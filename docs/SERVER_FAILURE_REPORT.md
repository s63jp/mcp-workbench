# MCP Workbench Server Failure Report

**Date:** 2026-08-02
**Incident:** Apparent server instability
**Status:** Misdiagnosed — server was stable

---

## Timeline

| Time | Event |
|------|-------|
| 19:25:01 | Server started via `terminal(background=true)` → pid 579682 |
| 19:27:27 | Supervisor script (`run_beta.sh start`) attempted fresh start |
| 19:27:30 | Supervisor's child process (pid 583061) crashed: `OSError: [Errno 98] address already in use` |
| 19:27:30 | Supervisor marked server "healthy" (curl to port 3460 succeeded because pid 579682 was still serving) |
| 19:27:38 | Cloudflare tunnel started by supervisor → new public URL |
| 19:28:08 | Investigation: original server pid 579682 confirmed alive |

---

## Root Cause

**The server never died.** The apparent instability was caused by:

1. **Test run** — `timeout 3 python3 server.py 3460` briefly started a server that printed "server.start" and exited after 3 seconds. This triggered the watch pattern and created a false "server dying" signal.

2. **Multiple background notifications** — accumulated watch-pattern matches from test runs and stopped processes made it appear the server was restarting.

3. **Premature diagnosis** — I jumped to "server is dying" without verifying with `ps` or `ss` first.

The supervisor's `start_server` function had a bug: it checked `curl` against the local port (which succeeded because pid 579682 was serving), then tried to spawn a new process on the same port (which crashed with EADDRINUSE). The supervisor recorded the dying child PID but the service was still healthy.

---

## Evidence

- `ss -tlnp | grep 3460` confirms pid 579682 has been listening on port 3460 since 19:25
- `ps -p 579682` shows the process is alive
- `curl http://localhost:3460/api/health` returns 200
- `curl https://series-forwarding-converted-juice.trycloudflare.com/api/health` returns 200

---

## Lessons

1. **Verify before diagnosing** — `ps`, `ss`, and `curl` are the ground truth. Watch patterns and accumulated notifications are signal noise.
2. **`terminal(background=true)` is correct** — the process is properly tracked and survives shell exit.
3. **Supervisor needs a port-check fix** — before starting, check if the port is already in use and skip if so.

---

## Action Items

- [ ] Fix `run_beta.sh` to detect port-in-use and skip restart if service is healthy
- [ ] Reduce noise: only send watch-pattern notifications for NEW server starts, not test runs
- [ ] Run 24-hour soak test before beta recruitment
- [ ] Do NOT introduce additional process management complexity until evidence demands it

---

## Current State

- **Server:** pid 579682, alive, port 3460, started 19:25:01
- **Tunnel:** pid 526609, alive, started 18:52
- **Local URL:** http://localhost:3460 (200 OK)
- **Public URL:** https://series-forwarding-converted-juice.trycloudflare.com (200 OK)
