# Building the Hermes Verification Engine: How We Validate MCP Servers at Scale

At MCP Workbench, we run hundreds of MCP server validation tests every day. Each one checks protocol compliance, schema integrity, error handling, and cross-client compatibility. Doing this manually would be impossible — so we built the **Hermes Verification Engine**, an automated system that validates MCP servers against a growing suite of tests.

This post is a deep dive into how it works, why we built it this way, and what we've learned about the MCP ecosystem from running thousands of validations.

## The Problem: MCP Is a Protocol, Not a Guarantee

MCP defines the wire format (JSON-RPC), the lifecycle (initialize → list tools → call tools → shutdown), and the schema format (JSON Schema for tool definitions). What it *doesn't* guarantee is that a server actually follows these rules consistently.

We've seen servers that:

- Return `initialize` responses with invalid protocol versions
- Claim to support `tools/list` but throw unhandled exceptions when called
- Publish JSON Schemas with circular `$ref` pointers that crash clients
- Send raw HTML error pages instead of JSON-RPC error objects
- Close the transport stream mid-response, orphaning pending requests

These aren't edge cases. In our testing, **roughly 30% of community MCP servers fail at least one critical verification test**.

## The Hermes Architecture

Hermes is built on three core principles:

1. **Hermetic isolation**: Every test runs in a fresh, isolated process with no shared state
2. **Deterministic replay**: Every test produces a traceable JSON-RPC log that can be inspected and replayed
3. **Client emulation**: Tests simulate real AI clients (Claude, Cursor, Cline, VS Code) to catch compatibility issues

### Test Runner

The runner launches an MCP server as a subprocess, establishes stdio or WebSocket transport, and executes a sequence of JSON-RPC requests. Each request/response pair is logged with timestamps and categorized by test phase.

```
Phase 1: Transport Connection
Phase 2: Initialize Handshake
Phase 3: Tool Discovery (tools/list)
Phase 4: Schema Validation
Phase 5: Tool Invocation (tools/call)
Phase 6: Error Injection
Phase 7: Graceful Shutdown
```

### Emulated Clients

Instead of requiring actual Claude Desktop or Cursor installations, Hermes emulates their behavior. For example:

- **Claude Desktop emulator**: Sends specific capability flags, expects `content` arrays in tool responses, validates `Content` block structure
- **Cursor emulator**: Expects tool names in a specific format, handles partial streaming differently
- **VS Code emulator**: Validates against the VS Code MCP extension's stricter schema requirements

Each emulator runs the same server through a client-specific test path, then flags divergences.

### Schema Validator

Hermes includes a custom JSON Schema validator tuned for MCP's specific patterns:

- Detects circular `$ref` chains before they blow up client parsers
- Validates that `required` fields actually exist in `properties`
- Checks that `additionalProperties` behavior is consistent with the implementation
- Flags schema sizes that might exceed client context windows

### Error Injector

One of the most powerful features is deliberate error injection. Hermes sends malformed requests to test how the server handles:

- Missing required parameters
- Wrong parameter types
- Invalid JSON-RPC `id` fields
- Requests sent before `initialize` completes
- Simultaneous concurrent tool calls

A well-behaved server returns proper JSON-RPC errors with clear messages. A fragile server crashes, hangs, or returns raw stack traces.

## What We've Learned

After running thousands of validations, here are the most common failure patterns:

| Failure Pattern | Frequency | Impact |
|-----------------|-----------|--------|
| Invalid JSON Schema | ~18% | Client can't parse tool definitions |
| Initialize handshake errors | ~12% | Server incompatible with some clients |
| Missing error handling | ~22% | Silent failures or transport crashes |
| Schema/implementation mismatch | ~15% | Tool call fails despite "valid" schema |
| Timeout on long operations | ~8% | Client assumes server is dead |

The good news: these are all detectable before the server reaches users. The bad news: most server authors don't know they're shipping broken code because they've never run a structured validation.

## Running Hermes Yourself

Hermes is integrated into MCP Workbench, so every server you connect gets automatically validated. You can also trigger validation runs via CI/CD webhooks for automated regression testing.

🔗 [Try MCP Workbench live](https://mcp-workbench.uk)

🔗 [Join the beta for CI/CD integration](https://mcp-workbench.uk/beta.html)

---

*Hermes is named after the Greek messenger god — because in the MCP ecosystem, reliable message passing is everything.*
