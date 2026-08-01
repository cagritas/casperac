from __future__ import annotations

import os
import subprocess

from casperac import antidetect

PROXY_URL = "socks5h://127.0.0.1:9050"


def get_proxy_env(identity_headers: dict[str, str] | None = None) -> dict[str, str]:
    """Returns the environment variables for proxying."""
    env = os.environ.copy()
    env["HTTP_PROXY"] = PROXY_URL
    env["HTTPS_PROXY"] = PROXY_URL
    env["ALL_PROXY"] = PROXY_URL
    env["http_proxy"] = PROXY_URL
    env["https_proxy"] = PROXY_URL
    env["all_proxy"] = PROXY_URL

    if identity_headers:
        for k, v in identity_headers.items():
            env_key = f"HTTP_{k.upper().replace('-', '_')}"
            env[env_key] = v
            # Also inject without HTTP_ prefix for some tools
            env[k.upper().replace("-", "_")] = v

    return env


def run_command_with_proxy(
    command: list[str], device_type: str = "desktop", browser: str | None = None
) -> int:
    """Runs a command with proxy environment variables and dynamic CLI argument injection."""
    headers = antidetect.get_random_identity(device_type, browser)

    # 1. Inject generic OS Environment Variables
    env = get_proxy_env(headers)

    # 2. Inject specific CLI arguments (Smart Wrapper)
    injected_cmd = antidetect.inject_cli_arguments(command, headers.copy())

    try:
        result = subprocess.run(injected_cmd, env=env, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command '{injected_cmd[0]}' not found.")
        return 127
