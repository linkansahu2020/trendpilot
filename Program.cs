var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<InstagramOptions>(builder.Configuration.GetSection("Instagram"));
builder.Services.AddHttpClient("instagram");
builder.Services.AddSingleton<InstagramSessionStore>();
builder.Services.AddSingleton<InstagramClient>();

var app = builder.Build();

app.MapGet("/", () => "Hello World!");

app.MapGet("/instagram/login", (InstagramSessionStore sessions, InstagramClient instagram) =>
{
    var missing = instagram.MissingConfigurationMessage();
    if (missing is not null)
    {
        return Results.Json(new { error = missing }, statusCode: StatusCodes.Status500InternalServerError);
    }

    var state = sessions.CreateState();
    return Results.Redirect(instagram.BuildAuthorizeUrl(state));
});

app.MapGet("/instagram/callback", async (
    string? code,
    string? state,
    string? error,
    string? error_description,
    InstagramSessionStore sessions,
    InstagramClient instagram,
    CancellationToken cancellationToken) =>
{
    if (!string.IsNullOrWhiteSpace(error))
    {
        var message = string.IsNullOrWhiteSpace(error_description) ? error : error_description;
        return Results.Json(new { error = message }, statusCode: StatusCodes.Status400BadRequest);
    }

    var missing = instagram.MissingConfigurationMessage();
    if (missing is not null)
    {
        return Results.Json(new { error = missing }, statusCode: StatusCodes.Status500InternalServerError);
    }

    if (string.IsNullOrWhiteSpace(state) || !sessions.TryConsumeState(state))
    {
        return Results.Json(
            new { error = "The Instagram login state is missing or expired. Start again at /instagram/login." },
            statusCode: StatusCodes.Status400BadRequest);
    }

    if (string.IsNullOrWhiteSpace(code))
    {
        return Results.Json(
            new { error = "Instagram did not return an authorization code." },
            statusCode: StatusCodes.Status400BadRequest);
    }

    var login = await instagram.ExchangeCodeAsync(code, cancellationToken);
    if (!login.IsSuccess || login.Value is null)
    {
        return Results.Json(new { error = login.Error }, statusCode: login.StatusCode);
    }

    sessions.Set(login.Value);
    return Results.Ok(new { signedIn = true, userId = login.Value.UserId });
});

app.MapGet("/instagram/me", async (InstagramSessionStore sessions, InstagramClient instagram, CancellationToken cancellationToken) =>
{
    var session = sessions.GetValid();
    if (session is null)
    {
        return Results.Json(
            new { error = "Sign in at /instagram/login." },
            statusCode: StatusCodes.Status401Unauthorized);
    }

    var account = await instagram.GetAccountAsync(session.UserId, session.AccessToken, cancellationToken);
    if (!account.IsSuccess || account.Value is null)
    {
        return Results.Json(new { error = account.Error }, statusCode: account.StatusCode);
    }

    return Results.Ok(account.Value);
});

app.Run();
