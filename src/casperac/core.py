import os
import subprocess
from typing import Dict, List

PROXY_URL = "socks5h://127.0.0.1:9050"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_proxy_env() -> Dict[str, str]:
    """Returns the environment variables for proxying."""
    env = os.environ.copy()
    env["HTTP_PROXY"] = PROXY_URL
    env["HTTPS_PROXY"] = PROXY_URL
    env["ALL_PROXY"] = PROXY_URL
    env["http_proxy"] = PROXY_URL
    env["https_proxy"] = PROXY_URL
    env["all_proxy"] = PROXY_URL

    # Inject generic browser User-Agent to mitigate standard CLI fingerprints
    env["HTTP_USER_AGENT"] = USER_AGENT
    env["USER_AGENT"] = USER_AGENT

    return env


def run_command_with_proxy(command: List[str]) -> int:
    """Runs a command with proxy environment variables injected."""
    env = get_proxy_env()
    try:
        result = subprocess.run(command, env=env)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found.")
        return 127
