# Cursor project config

## Stitch MCP

[`mcp.json`](mcp.json) reads the Stitch API key from the environment:

```text
X-Goog-Api-Key: ${env:STITCH_API_KEY}
```

1. See the dummy name in [`web/.env.example`](../web/.env.example). Set the real key in your shell (not in the repo), for example in `~/.zshrc`:

   ```bash
   export STITCH_API_KEY="your-real-key"
   ```

2. Fully quit and reopen Cursor so MCP picks up the new environment.
3. Do not commit a real API key into `mcp.json` or any tracked file.
