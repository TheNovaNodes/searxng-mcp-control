## 2024-08-31 - Redact sensitive settings in MCP server
**Vulnerability:** The MCP control server for SearXNG exposed the secret_key from the server configuration in plaintext to external agents/users when querying inspect_settings.
**Learning:** Returning parsed settings/configuration dictionaries from MCP endpoints can leak secrets that were originally stored securely in config files. We need to actively sanitize and redact sensitive keys before returning them to an MCP caller.
**Prevention:** Always implement an active redaction pass over parsed configuration objects before sending them over the wire via MCP.
