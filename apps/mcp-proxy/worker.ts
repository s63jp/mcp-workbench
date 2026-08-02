/**
 * MCP Proxy Worker
 *
 * A Cloudflare Worker that acts as a WebSocket-to-stdio proxy for MCP servers.
 * Uses Durable Objects to maintain stateful WebSocket connections and child
 * process handles across requests.
 *
 * Architecture:
 *   POST /connect    → creates a session (stores command+args in DO storage)
 *   GET  /rpc         → WebSocket upgrade; DO spawns the MCP server and bridges
 *   POST /disconnect  → destroys session and kills the child process
 *
 * Compatible with the Model Context Protocol JSON-RPC line-delimited format.
 */

import { Hono } from "hono";
import { cors } from "hono/cors";
import { z } from "zod";

// ─────────────────────────────────────────────
// Validation Schemas
// ─────────────────────────────────────────────

const ConnectBodySchema = z.object({
  command: z.string().min(1, { message: "Command is required" }),
  args: z.array(z.string()).default([]),
  env: z.record(z.string(), z.string()).optional(),
  cwd: z.string().optional(),
});

const DisconnectBodySchema = z.object({
  sessionId: z.string().uuid(),
});

// ─────────────────────────────────────────────
// JSON-RPC Types
// ─────────────────────────────────────────────

interface JSONRPCMessage {
  jsonrpc: "2.0";
  id?: string | number | null;
  method?: string;
  params?: unknown;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

// ─────────────────────────────────────────────
// ReadBuffer: parses newline-delimited JSON-RPC from stdio
// (Mirrors @modelcontextprotocol/sdk/shared/stdio logic)
// ─────────────────────────────────────────────

const STDIO_DEFAULT_MAX_BUFFER_SIZE = 10 * 1024 * 1024;

class ReadBuffer {
  private _buffer: Uint8Array | null = null;
  private _maxSize: number;

  constructor(options?: { maxBufferSize?: number }) {
    this._maxSize = options?.maxBufferSize ?? STDIO_DEFAULT_MAX_BUFFER_SIZE;
  }

  append(chunk: Uint8Array) {
    const newSize = (this._buffer?.length ?? 0) + chunk.length;
    if (newSize > this._maxSize) {
      this.clear();
      throw new Error(
        `ReadBuffer exceeded maximum size of ${this._maxSize} bytes`
      );
    }
    this._buffer = this._buffer ? concatUint8(this._buffer, chunk) : chunk;
  }

  readMessage(): JSONRPCMessage | null {
    if (!this._buffer) return null;

    const text = new TextDecoder().decode(this._buffer);
    const nl = text.indexOf("\n");
    if (nl === -1) return null;

    const line = text.slice(0, nl).replace(/\r$/, "");
    this._buffer = new TextEncoder().encode(text.slice(nl + 1));

    if (!line.trim()) return this.readMessage();

    try {
      const parsed = JSON.parse(line);
      if (parsed.jsonrpc !== "2.0") return null;
      return parsed as JSONRPCMessage;
    } catch {
      return null;
    }
  }

  clear() {
    this._buffer = null;
  }
}

function concatUint8(a: Uint8Array, b: Uint8Array): Uint8Array {
  const c = new Uint8Array(a.length + b.length);
  c.set(a, 0);
  c.set(b, a.length);
  return c;
}

function serializeMessage(msg: JSONRPCMessage): string {
  return JSON.stringify(msg) + "\n";
}

// ─────────────────────────────────────────────
// Session Types
// ─────────────────────────────────────────────

interface SessionConfig {
  command: string;
  args: string[];
  env?: Record<string, string>;
  cwd?: string;
}

interface ActiveSession {
  process: any; // Node.js ChildProcess
  ws: WebSocket;
  readBuffer: ReadBuffer;
}

// ─────────────────────────────────────────────
// Environment
// ─────────────────────────────────────────────

export interface Env {
  MCP_PROXY_SESSION: DurableObjectNamespace;
}

// ─────────────────────────────────────────────
// Durable Object: McpProxySession
// ─────────────────────────────────────────────
// Holds the active child process and WebSocket for each session.
// ─────────────────────────────────────────────

export class McpProxySession {
  private state: DurableObjectState;
  private activeSessions: Map<string, ActiveSession> = new Map();

  constructor(state: DurableObjectState, _env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/session" && request.method === "POST") {
      return this.createSession(request);
    }

    if (url.pathname === "/session" && request.method === "DELETE") {
      return this.destroySession(request);
    }

    if (url.pathname === "/ws") {
      return this.handleWebSocket(request);
    }

    return new Response("Not Found", { status: 404 });
  }

  // ── Session lifecycle ──

  private async createSession(request: Request): Promise<Response> {
    const body = (await request.json()) as {
      sessionId: string;
      config: SessionConfig;
    };
    await this.state.storage.put<SessionConfig>(
      `session:${body.sessionId}`,
      body.config
    );
    return jsonResponse({ status: "created" });
  }

  private async destroySession(request: Request): Promise<Response> {
    const body = (await request.json()) as { sessionId: string };
    const sessionId = body.sessionId;

    await this.state.storage.delete(`session:${sessionId}`);
    const active = this.activeSessions.get(sessionId);

    if (active) {
      if (!active.process.killed) {
        try {
          active.process.stdin?.end();
        } catch {
          /* ignore */
        }
        try {
          active.process.kill("SIGTERM");
        } catch {
          /* ignore */
        }

        setTimeout(() => {
          try {
            if (!active.process.killed) {
              active.process.kill("SIGKILL");
            }
          } catch {
            /* ignore */
          }
        }, 2000);
      }

      try {
        active.ws.close(1000, "Session destroyed");
      } catch {
        /* ignore */
      }

      this.activeSessions.delete(sessionId);
    }

    return jsonResponse({ status: "disconnected", sessionId });
  }

  // ── WebSocket + stdio bridge ──

  private async handleWebSocket(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get("sessionId");

    if (!sessionId) {
      return new Response("Missing sessionId query parameter", { status: 400 });
    }

    const config = await this.state.storage.get<SessionConfig>(
      `session:${sessionId}`
    );
    if (!config) {
      return new Response("Session not found", { status: 404 });
    }

    let spawn: (...args: any[]) => any;
    try {
      // @ts-ignore child_process is available only in nodejs_compat runtimes
      const cp = await import("node:child_process");
      spawn = cp.spawn;
    } catch (e) {
      return new Response(
        `child_process is not available in this runtime. ` +
          `MCP proxy requires a Node.js-compatible environment ` +
          `(e.g. local \`wrangler dev\`). Error: ${e}`,
        { status: 501 }
      );
    }

    const child = spawn(config.command, config.args, {
      env: { ...getDefaultEnv(), ...config.env },
      cwd: config.cwd,
      stdio: ["pipe", "pipe", "pipe"],
      shell: false,
    });

    const pair = new WebSocketPair();
    const clientWs = pair[0];
    const serverWs = pair[1];

    (serverWs as any).accept();

    const readBuffer = new ReadBuffer();
    const active: ActiveSession = { process: child, ws: serverWs, readBuffer };

    // stdout -> WebSocket
    child.stdout?.on("data", (chunk: Uint8Array) => {
      readBuffer.append(chunk);
      while (true) {
        const msg = readBuffer.readMessage();
        if (!msg) break;
        try {
          serverWs.send(JSON.stringify(msg));
        } catch {
          break;
        }
      }
    });

    // stderr -> console.error
    child.stderr?.on("data", (chunk: Uint8Array) => {
      const text = new TextDecoder().decode(chunk).trim();
      if (text) {
        console.error(`[${sessionId}] stderr: ${text}`);
      }
    });

    // WebSocket -> stdin
    serverWs.addEventListener("message", (event: MessageEvent) => {
      let data: string;
      if (typeof event.data === "string") {
        data = event.data;
      } else {
        data = new TextDecoder().decode(event.data);
      }

      try {
        const msg = JSON.parse(data) as JSONRPCMessage;
        const serialized = serializeMessage(msg);
        if (child.stdin?.write) {
          child.stdin.write(serialized);
        }
      } catch (err) {
        serverWs.send(
          JSON.stringify({
            jsonrpc: "2.0",
            error: {
              code: -32700,
              message: `Parse error: ${(err as Error).message}`,
            },
            id: null,
          })
        );
      }
    });

    // Process exit
    child.on("close", (code: number | null, signal: string | null) => {
      console.log(
        `[${sessionId}] Process exited (code: ${code}, signal: ${signal})`
      );
      try {
        serverWs.close(1000, "Process exited");
      } catch {
        /* ignore */
      }
      this.activeSessions.delete(sessionId);
    });

    child.on("error", (err: Error) => {
      console.error(`[${sessionId}] Process error:`, err);
      try {
        serverWs.send(
          JSON.stringify({
            jsonrpc: "2.0",
            error: {
              code: -32000,
              message: `Process error: ${err.message}`,
            },
            id: null,
          })
        );
      } catch {
        /* ignore */
      }
    });

    // WebSocket close -> kill process
    serverWs.addEventListener("close", () => {
      if (!child.killed) {
        try {
          child.stdin?.end();
        } catch {
          /* ignore */
        }
        try {
          child.kill("SIGTERM");
        } catch {
          /* ignore */
        }

        setTimeout(() => {
          try {
            if (!child.killed) {
              child.kill("SIGKILL");
            }
          } catch {
            /* ignore */
          }
        }, 2000);
      }
      this.activeSessions.delete(sessionId);
    });

    this.activeSessions.set(sessionId, active);
    return new Response(null, { status: 101, webSocket: clientWs });
  }
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * Returns a default environment object with safe-to-inherit vars.
 * Matches the SDK's getDefaultEnvironment() behaviour.
 */
function getDefaultEnv(): Record<string, string> {
  const keys = ["HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER"];
  const env: Record<string, string> = {};
  try {
    const procEnv = (globalThis as any).process?.env;
    if (procEnv) {
      for (const key of keys) {
        const value = procEnv[key];
        if (value !== undefined) env[key] = value;
      }
    }
  } catch {
    // Workers without process global
  }
  return env;
}

// ─────────────────────────────────────────────
// Hono App
// ─────────────────────────────────────────────

const app = new Hono<{ Bindings: Env }>();

app.use(
  "*",
  cors({
    origin: "*",
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Upgrade"],
  })
);

// Health check
app.get("/health", (c) =>
  c.json({ status: "ok", service: "mcp-proxy", version: "0.1.0" })
);

// POST /connect — start a new MCP server session
app.post("/connect", async (c) => {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const parsed = ConnectBodySchema.safeParse(body);
  if (!parsed.success) {
    return c.json(
      { error: "Invalid parameters", details: parsed.error.issues },
      400
    );
  }

  const sessionId = crypto.randomUUID();
  const config: SessionConfig = {
    command: parsed.data.command,
    args: parsed.data.args,
    env: parsed.data.env,
    cwd: parsed.data.cwd,
  };

  const durableObjectId = c.env.MCP_PROXY_SESSION.idFromName(sessionId);
  const durableObject = c.env.MCP_PROXY_SESSION.get(durableObjectId);

  const res = await durableObject.fetch(
    new Request("http://internal/session", {
      method: "POST",
      body: JSON.stringify({ sessionId, config }),
    })
  );

  if (!res.ok) {
    const text = await res.text();
    return c.json({ error: `Failed to create session: ${text}` }, 500);
  }

  return c.json({
    sessionId,
    wsUrl: `/rpc?sessionId=${sessionId}`,
  });
});

// GET /rpc — WebSocket upgrade for JSON-RPC bridge
app.get("/rpc", async (c) => {
  const sessionId = c.req.query("sessionId");
  if (!sessionId) {
    return c.json({ error: "Missing sessionId query parameter" }, 400);
  }

  const durableObjectId = c.env.MCP_PROXY_SESSION.idFromName(sessionId);
  const durableObject = c.env.MCP_PROXY_SESSION.get(durableObjectId);

  return durableObject.fetch(
    new Request(`http://internal/ws?sessionId=${sessionId}`, {
      headers: c.req.raw.headers,
    })
  );
});

// POST /disconnect — terminate a session
app.post("/disconnect", async (c) => {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const parsed = DisconnectBodySchema.safeParse(body);
  if (!parsed.success) {
    return c.json(
      { error: "Invalid parameters", details: parsed.error.issues },
      400
    );
  }

  const sessionId = parsed.data.sessionId;
  const durableObjectId = c.env.MCP_PROXY_SESSION.idFromName(sessionId);
  const durableObject = c.env.MCP_PROXY_SESSION.get(durableObjectId);

  const res = await durableObject.fetch(
    new Request("http://internal/session", {
      method: "DELETE",
      body: JSON.stringify({ sessionId }),
    })
  );

  if (!res.ok) {
    const text = await res.text();
    return c.json({ error: `Failed to destroy session: ${text}` }, 500);
  }

  return c.json({ status: "disconnected", sessionId });
});

export default app;
