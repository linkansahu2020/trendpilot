using System.Collections.Concurrent;
using System.Net;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.WebUtilities;
using Microsoft.Extensions.Options;

public sealed class InstagramOptions
{
    public string GraphVersion { get; set; } = "v25.0";
    public string RedirectUri { get; set; } = "";
    public string AppId { get; set; } = "";
    public string AppSecret { get; set; } = "";
}

public sealed record InstagramLogin(string UserId, string AccessToken, DateTimeOffset ExpiresAt);

public sealed record InstagramProfile(
    string Id,
    string? Username,
    string? Name,
    string? Biography,
    string? Website,
    int? FollowersCount,
    int? FollowsCount,
    int? MediaCount,
    string? ProfilePictureUrl);

public sealed record InstagramMedia(
    string Id,
    string? Caption,
    string? MediaType,
    string? MediaUrl,
    string? Permalink,
    DateTimeOffset? Timestamp,
    int? LikeCount,
    int? CommentsCount);

public sealed record InstagramAccount(
    InstagramProfile Profile,
    IReadOnlyList<InstagramMedia> Media,
    string? NextCursor);

public sealed class InstagramResult<T>
{
    private InstagramResult(T value)
    {
        Value = value;
    }

    private InstagramResult(int statusCode, string message)
    {
        StatusCode = statusCode;
        Error = message;
    }

    public T? Value { get; }
    public int StatusCode { get; }
    public string? Error { get; }
    public bool IsSuccess => Error is null;

    public static InstagramResult<T> Ok(T value) => new(value);

    public static InstagramResult<T> Fail(int statusCode, string message) => new(statusCode, message);
}

public sealed class InstagramSessionStore
{
    private readonly ConcurrentDictionary<string, DateTimeOffset> _states = new();
    private readonly object _sessionGate = new();
    private InstagramLogin? _session;

    public string CreateState()
    {
        var now = DateTimeOffset.UtcNow;
        foreach (var entry in _states)
        {
            if (entry.Value <= now)
            {
                _states.TryRemove(entry.Key, out _);
            }
        }

        var state = Guid.NewGuid().ToString("N");
        _states[state] = now.AddMinutes(10);
        return state;
    }

    public bool TryConsumeState(string state)
    {
        if (!_states.TryRemove(state, out var expiresAt))
        {
            return false;
        }

        return expiresAt > DateTimeOffset.UtcNow;
    }

    public void Set(InstagramLogin login)
    {
        lock (_sessionGate)
        {
            _session = login;
        }
    }

    public InstagramLogin? GetValid()
    {
        lock (_sessionGate)
        {
            if (_session is null || _session.ExpiresAt <= DateTimeOffset.UtcNow)
            {
                _session = null;
                return null;
            }

            return _session;
        }
    }
}

public sealed class InstagramClient
{
    private const string ProfileFields = "id,username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url";
    private const string MediaFields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count";

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly InstagramOptions _options;

    public InstagramClient(IHttpClientFactory httpClientFactory, IOptions<InstagramOptions> options)
    {
        _httpClientFactory = httpClientFactory;
        _options = options.Value;
    }

    public string? MissingConfigurationMessage()
    {
        if (string.IsNullOrWhiteSpace(_options.AppId) || string.IsNullOrWhiteSpace(_options.AppSecret))
        {
            return "Instagram app id and app secret are not configured. Set Instagram__AppId and Instagram__AppSecret.";
        }

        if (string.IsNullOrWhiteSpace(_options.RedirectUri))
        {
            return "Instagram:RedirectUri is not configured.";
        }

        return null;
    }

    public string BuildAuthorizeUrl(string state)
    {
        return QueryHelpers.AddQueryString(
            "https://www.instagram.com/oauth/authorize",
            new Dictionary<string, string?>
            {
                ["client_id"] = _options.AppId,
                ["redirect_uri"] = _options.RedirectUri,
                ["response_type"] = "code",
                ["scope"] = "instagram_business_basic",
                ["state"] = state
            });
    }

    public async Task<InstagramResult<InstagramLogin>> ExchangeCodeAsync(string code, CancellationToken cancellationToken)
    {
        if (code.EndsWith("#_", StringComparison.Ordinal))
        {
            code = code[..^2];
        }

        var client = _httpClientFactory.CreateClient("instagram");
        using var content = new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["client_id"] = _options.AppId,
            ["client_secret"] = _options.AppSecret,
            ["grant_type"] = "authorization_code",
            ["redirect_uri"] = _options.RedirectUri,
            ["code"] = code
        });

        using var tokenResponse = await client.PostAsync("https://api.instagram.com/oauth/access_token", content, cancellationToken);
        var tokenBody = await tokenResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!tokenResponse.IsSuccessStatusCode)
        {
            var (message, graphCode) = ReadError(tokenBody, tokenResponse.StatusCode);
            return InstagramResult<InstagramLogin>.Fail(MapStatus(tokenResponse.StatusCode, graphCode), message);
        }

        if (!TryReadShortLivedToken(tokenBody, out var userId, out var shortLivedToken))
        {
            return InstagramResult<InstagramLogin>.Fail(StatusCodes.Status502BadGateway, "Instagram token response did not include a user.");
        }

        var longLivedUrl = QueryHelpers.AddQueryString(
            "https://graph.instagram.com/access_token",
            new Dictionary<string, string?>
            {
                ["grant_type"] = "ig_exchange_token",
                ["client_secret"] = _options.AppSecret,
                ["access_token"] = shortLivedToken
            });

        using var longLivedResponse = await client.GetAsync(longLivedUrl, cancellationToken);
        var longLivedBody = await longLivedResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!longLivedResponse.IsSuccessStatusCode)
        {
            var (message, graphCode) = ReadError(longLivedBody, longLivedResponse.StatusCode);
            return InstagramResult<InstagramLogin>.Fail(MapStatus(longLivedResponse.StatusCode, graphCode), message);
        }

        if (!TryReadLongLivedToken(longLivedBody, out var accessToken, out var expiresIn))
        {
            return InstagramResult<InstagramLogin>.Fail(StatusCodes.Status502BadGateway, "Instagram did not return a long-lived token.");
        }

        return InstagramResult<InstagramLogin>.Ok(new InstagramLogin(userId, accessToken, DateTimeOffset.UtcNow.AddSeconds(expiresIn)));
    }

    public async Task<InstagramResult<InstagramAccount>> GetAccountAsync(
        string userId,
        string accessToken,
        CancellationToken cancellationToken)
    {
        var version = string.IsNullOrWhiteSpace(_options.GraphVersion) ? "v25.0" : _options.GraphVersion.Trim('/');
        var escapedUserId = Uri.EscapeDataString(userId);
        var escapedToken = Uri.EscapeDataString(accessToken);
        var client = _httpClientFactory.CreateClient("instagram");

        var profileUrl = $"https://graph.instagram.com/{version}/{escapedUserId}?fields={ProfileFields}&access_token={escapedToken}";
        using var profileResponse = await client.GetAsync(profileUrl, cancellationToken);
        var profileBody = await profileResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!profileResponse.IsSuccessStatusCode)
        {
            var (message, graphCode) = ReadError(profileBody, profileResponse.StatusCode);
            return InstagramResult<InstagramAccount>.Fail(MapStatus(profileResponse.StatusCode, graphCode), message);
        }

        var mediaUrl = $"https://graph.instagram.com/{version}/{escapedUserId}/media?fields={MediaFields}&limit=25&access_token={escapedToken}";
        using var mediaResponse = await client.GetAsync(mediaUrl, cancellationToken);
        var mediaBody = await mediaResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!mediaResponse.IsSuccessStatusCode)
        {
            var (message, graphCode) = ReadError(mediaBody, mediaResponse.StatusCode);
            return InstagramResult<InstagramAccount>.Fail(MapStatus(mediaResponse.StatusCode, graphCode), message);
        }

        var profile = ReadProfile(profileBody, userId);
        var (media, nextCursor) = ReadMedia(mediaBody);
        return InstagramResult<InstagramAccount>.Ok(new InstagramAccount(profile, media, nextCursor));
    }

    private static bool TryReadShortLivedToken(string body, out string userId, out string accessToken)
    {
        userId = "";
        accessToken = "";
        try
        {
            using var doc = JsonDocument.Parse(body);
            var root = doc.RootElement;
            if (root.TryGetProperty("data", out var data))
            {
                if (data.ValueKind != JsonValueKind.Array || data.GetArrayLength() == 0)
                {
                    return false;
                }

                return TryReadTokenFields(data[0], out userId, out accessToken);
            }

            return TryReadTokenFields(root, out userId, out accessToken);
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static bool TryReadTokenFields(JsonElement item, out string userId, out string accessToken)
    {
        userId = "";
        accessToken = "";
        if (!item.TryGetProperty("access_token", out var tokenElement) || tokenElement.ValueKind != JsonValueKind.String)
        {
            return false;
        }

        if (!item.TryGetProperty("user_id", out var userElement))
        {
            return false;
        }

        accessToken = tokenElement.GetString() ?? "";
        userId = ReadId(userElement);
        return accessToken.Length > 0 && userId.Length > 0;
    }

    private static bool TryReadLongLivedToken(string body, out string accessToken, out int expiresIn)
    {
        accessToken = "";
        expiresIn = 0;
        try
        {
            using var doc = JsonDocument.Parse(body);
            var root = doc.RootElement;
            if (!root.TryGetProperty("access_token", out var tokenElement) || tokenElement.ValueKind != JsonValueKind.String)
            {
                return false;
            }

            if (!root.TryGetProperty("expires_in", out var expiresElement) || !expiresElement.TryGetInt32(out expiresIn) || expiresIn <= 0)
            {
                return false;
            }

            accessToken = tokenElement.GetString() ?? "";
            return accessToken.Length > 0;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static InstagramProfile ReadProfile(string body, string fallbackUserId)
    {
        using var doc = JsonDocument.Parse(body);
        var root = doc.RootElement;
        var id = root.TryGetProperty("id", out var idElement) ? ReadId(idElement) : fallbackUserId;
        return new InstagramProfile(
            id,
            ReadString(root, "username"),
            ReadString(root, "name"),
            ReadString(root, "biography"),
            ReadString(root, "website"),
            ReadInt(root, "followers_count"),
            ReadInt(root, "follows_count"),
            ReadInt(root, "media_count"),
            ReadString(root, "profile_picture_url"));
    }

    private static (IReadOnlyList<InstagramMedia> Media, string? NextCursor) ReadMedia(string body)
    {
        using var doc = JsonDocument.Parse(body);
        var root = doc.RootElement;
        var media = new List<InstagramMedia>();
        if (root.TryGetProperty("data", out var data) && data.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in data.EnumerateArray())
            {
                var id = item.TryGetProperty("id", out var idElement) ? ReadId(idElement) : "";
                if (id.Length == 0)
                {
                    continue;
                }

                DateTimeOffset? timestamp = null;
                if (item.TryGetProperty("timestamp", out var timestampElement)
                    && timestampElement.ValueKind == JsonValueKind.String
                    && DateTimeOffset.TryParse(timestampElement.GetString(), out var parsed))
                {
                    timestamp = parsed;
                }

                media.Add(new InstagramMedia(
                    id,
                    ReadString(item, "caption"),
                    ReadString(item, "media_type"),
                    ReadString(item, "media_url"),
                    ReadString(item, "permalink"),
                    timestamp,
                    ReadInt(item, "like_count"),
                    ReadInt(item, "comments_count")));
            }
        }

        string? nextCursor = null;
        if (root.TryGetProperty("paging", out var paging)
            && paging.TryGetProperty("cursors", out var cursors)
            && cursors.TryGetProperty("after", out var after)
            && after.ValueKind == JsonValueKind.String)
        {
            nextCursor = after.GetString();
        }

        return (media, nextCursor);
    }

    private static (string Message, int? Code) ReadError(string body, HttpStatusCode status)
    {
        try
        {
            using var doc = JsonDocument.Parse(body);
            var root = doc.RootElement;
            if (root.TryGetProperty("error", out var error))
            {
                if (error.ValueKind == JsonValueKind.Object)
                {
                    var message = error.TryGetProperty("message", out var messageElement) ? messageElement.GetString() : null;
                    int? code = error.TryGetProperty("code", out var codeElement) && codeElement.TryGetInt32(out var graphCode)
                        ? graphCode
                        : null;
                    return (Redact(message), code);
                }

                if (error.ValueKind == JsonValueKind.String)
                {
                    var description = root.TryGetProperty("error_description", out var descriptionElement)
                        ? descriptionElement.GetString()
                        : error.GetString();
                    return (Redact(description), null);
                }
            }

            if (root.TryGetProperty("error_message", out var errorMessage))
            {
                return (Redact(errorMessage.GetString()), null);
            }
        }
        catch (JsonException)
        {
        }

        return ($"Instagram request failed with status {(int)status}.", null);
    }

    private static int MapStatus(HttpStatusCode status, int? graphCode)
    {
        if (status is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
        {
            return StatusCodes.Status403Forbidden;
        }

        if (graphCode is 10 or 102 or 190 or 200)
        {
            return StatusCodes.Status403Forbidden;
        }

        var code = (int)status;
        return code is >= 400 and <= 499 ? code : StatusCodes.Status502BadGateway;
    }

    private static string ReadId(JsonElement element)
    {
        return element.ValueKind switch
        {
            JsonValueKind.String => element.GetString() ?? "",
            JsonValueKind.Number => element.GetRawText(),
            _ => ""
        };
    }

    private static string? ReadString(JsonElement element, string name)
    {
        if (!element.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.String)
        {
            return null;
        }

        return value.GetString();
    }

    private static int? ReadInt(JsonElement element, string name)
    {
        if (!element.TryGetProperty(name, out var value) || !value.TryGetInt32(out var number))
        {
            return null;
        }

        return number;
    }

    private static string Redact(string? message)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return "Instagram request failed.";
        }

        return Regex.Replace(message, "(access_token|client_secret)=[^&\\s\"]+", "$1=REDACTED", RegexOptions.IgnoreCase);
    }
}
