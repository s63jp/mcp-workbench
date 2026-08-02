# How to Debug MCP Server Connection Issues in 60 Seconds

You've spun up a shiny new MCP server, pointed your client at it, and… silence. No tools appear. No error message. Just a vague sense that something went wrong somewhere in the JSON-RPC void.

Connection debugging is the most common pain point for MCP developers, and it's unnecessarily painful because most of us do it inside a chat client where observability is near zero. Here's a 60-second workflow to isolate and fix the problem using MCP Workbench.

## Step 1: Verify the Server Starts at All (10 seconds)

Before testing the client, confirm the server process itself launches cleanly. In MCP Workbench, paste your server command into the connection form and click **Connect**.

If the server fails to start, Workbench surfaces the stderr output immediately. Common culprits:

- **Missing dependencies**: The server binary or npx package isn't installed.
- **Permission errors**: The server can't read a file or bind to a port.
- **Wrong arguments**: A missing `--base-dir` or incorrect API key flag.

Fix the startup error before moving on.

## Step 2: Check Tool Discovery (15 seconds)

Once connected, Workbench automatically sends an `initialize` request followed by `tools/list`. If discovery fails, you'll see the exact JSON-RPC error:

- **`initialize` rejected**: Your server isn't negotiating protocol versions correctly. Ensure you're responding with supported protocol versions and capability flags.
- **`tools/list` empty or errors**: The server claims to support tools but can't enumerate them. Check for unhandled exceptions in your tool listing logic.
- **Schema validation failures**: A tool is returned, but its JSON Schema is malformed (e.g., a `$ref` pointing nowhere, or an invalid type). Workbench flags the exact field.

## Step 3: Invoke a Tool with Test Parameters (20 seconds)

Discovery passing doesn't mean execution works. Pick a tool from the list, fill in the required parameters using Workbench's form builder, and run it.

If the tool call fails, the raw JSON-RPC response tells you exactly why:

- **`InvalidParams`**: The arguments you sent don't match the tool's JSON Schema. Check the `errors` array for the mismatch.
- **`InternalError`**: Your server threw an exception during execution. Look at the server-side logs (Workbench shows stderr alongside RPC traffic).
- **Timeout**: The tool ran but never responded. Common with long-running operations or deadlocks.
- **Transport closed**: The server crashed mid-request. Usually an unhandled error in your tool handler.

## Step 4: Compare Against Known-Good Servers (15 seconds)

Still stuck? Connect to an official MCP server (like `@modelcontextprotocol/server-filesystem`) in a second tab and compare the JSON-RPC traffic side-by-side.

Look for differences in:
- The `initialize` request/response shape
- How `content` arrays are structured in tool responses
- Whether you're using the correct JSON-RPC `id` correlation

This single technique has resolved more "mysterious" client compatibility issues than any documentation reading.

## The Golden Rule

**Never debug an MCP server inside a chat client.** The client abstracts away the protocol, caches capabilities, and gives you zero visibility into the wire format. MCP Workbench (and any raw JSON-RPC inspector) shows you exactly what's sent and received, which is the only way to fix issues in seconds instead of hours.

## Quick Reference: Common Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Client shows no tools | Discovery failed / `tools/list` errors | Check JSON-RPC response in Workbench |
| Tool call silently fails | `InternalError` not surfaced by client | Inspect raw response for error payload |
| Schema complaints | Invalid JSON Schema in tool definition | Validate schema with Workbench validator |
| Works in Claude but not Cursor | Capability mismatch | Compare `initialize` negotiation |
| Works locally but not in CI | Environment / env var differences | Use saved configs to lock down setup |

## Try It Yourself

Next time an MCP server misbehaves, open MCP Workbench, connect it, and read the actual JSON-RPC. You'll be surprised how fast the problem becomes obvious.

🔗 [Launch MCP Workbench](https://depth-plenty-mia-similarly.trycloudflare.com)

---

*Have a debugging tip that saved you hours? Share it — the best ones get added to the docs.*
