# CasperAC Architecture Specification

## Overview
CasperAC provides an opinionated framework to route terminal processes through a dual-layer anonymity chain. It is built natively in Python leveraging modern CLI frameworks.

## Proxy Chain 
**[Command / Subprocess] -> [Local Tor SOCKS5 Proxy 127.0.0.1:9050] -> [Cloudflare WARP Interface] -> [Tor Network] -> [Destination]**

1. **Tor**: Local daemon receives traffic from subprocess via `socks5h` environment variables. The `h` forces remote DNS resolution.
2. **WARP**: Assuming WARP is running natively on the host interface, the Tor daemon's encrypted packets are encapsulated by WARP before they leave the physical machine.

## Module Breakdown
- `casperac.core`: Handles environment mutation and subprocess execution. Uses `os.environ` copy to safely inject proxies and generic User-Agents.
- `casperac.warp`: Subprocess wrapper that executes `warp-cli status` to report on the state of the Cloudflare tunnel.
- `casperac.tor`: Interfaces with the Tor daemon. Utilizes sockets to check for port 9050 liveness, `requests[socks]` to query Tor's API endpoint, and socket communication with the control port (9051) to send `SIGNAL NEWNYM`.
- `casperac.main`: The Typer application providing the `run`, `status`, `renew`, `env-on`, and `env-off` commands. Uses `rich` to format output.

## Environment Injections
- `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`
- `http_proxy`, `https_proxy`, `all_proxy` (lowercase variants)
- `HTTP_USER_AGENT`, `USER_AGENT`

## Limitations
- User-Agent injection relies on the underlying application respecting the environment variable. It will not override hardcoded client headers in advanced network tools without specific flags (e.g., `curl -A`).
