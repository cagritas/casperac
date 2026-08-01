from __future__ import annotations

import random

# Pre-defined realistic User-Agents to rotate through
DESKTOP_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Linux Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
]

MOBILE_USER_AGENTS = [
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# Customizable Injection Rules Structure
# Maps a CLI tool (e.g. 'curl') to how its headers and user-agent should be injected.
# Users can theoretically extend this by overriding this dictionary.
INJECTION_RULES = {
    "curl": {
        "user_agent_flag": "-A",  # curl -A "User Agent String"
        "header_flag": "-H",  # curl -H "Header: Value"
        "header_format": "{key}: {value}",
    },
    "wget": {
        "user_agent_flag": "--user-agent=",  # wget --user-agent="User Agent"
        "header_flag": "--header=",  # wget --header="Header: Value"
        "header_format": "{key}: {value}",
    },
    "http": {  # HTTPie
        "user_agent_flag": None,  # HTTPie handles User-Agent as a normal header
        "header_flag": "",  # http Header:Value
        "header_format": "{key}:{value}",
    },
    "aria2c": {
        "user_agent_flag": "-U",
        "header_flag": "--header=",
        "header_format": "{key}: {value}",
    },
}


def get_random_identity(
    device_type: str = "desktop", browser: str | None = None
) -> dict[str, str]:
    """
    Generates a realistic set of HTTP headers based on device type and requested browser.
    Returns a dictionary of headers (e.g., {'User-Agent': '...', 'Accept-Language': '...'})
    """
    headers = {}

    # 1. Determine User Agent
    pool = (
        MOBILE_USER_AGENTS if device_type.lower() == "mobile" else DESKTOP_USER_AGENTS
    )

    if browser:
        b = browser.lower()
        filtered = [ua for ua in pool if b in ua.lower()]
        if filtered:
            pool = filtered

    ua = random.choice(pool)
    headers["User-Agent"] = ua

    # 2. Add realistic Accept-Language
    langs = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9,en-US;q=0.8",
        "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    ]
    headers["Accept-Language"] = random.choice(langs)

    # 3. Add Sec-Ch-Ua headers for Chromium based browsers to bypass advanced bot protection
    if "Chrome" in ua:
        version = ua.split("Chrome/")[1].split(".")[0]
        platform = (
            "Windows"
            if "Windows" in ua
            else (
                "macOS"
                if "Macintosh" in ua
                else "Android" if "Android" in ua else "Linux"
            )
        )
        mobile = "?1" if "Mobile" in ua else "?0"

        headers["sec-ch-ua"] = (
            f'"Not_A Brand";v="8", "Chromium";v="{version}", "Google Chrome";v="{version}"'
        )
        headers["sec-ch-ua-mobile"] = mobile
        headers["sec-ch-ua-platform"] = f'"{platform}"'

    return headers


def inject_cli_arguments(command: list[str], headers: dict[str, str]) -> list[str]:
    """
    Looks up the command in INJECTION_RULES and dynamically injects the arguments.
    If the command is not in the rules, returns the original command unmodified.
    """
    if not command:
        return command

    base_cmd = command[0].split("/")[-1]  # Extract 'curl' from '/usr/bin/curl'

    if base_cmd not in INJECTION_RULES:
        return (
            command  # Not a supported CLI tool for arg injection, fallback to Env Vars.
        )

    rule = INJECTION_RULES[base_cmd]
    injected_cmd = [command[0]]

    # Extract User-Agent early since it modifies headers dict
    ua_value = headers.get("User-Agent")

    # Inject User Agent specifically if rule dictates
    if ua_value and rule.get("user_agent_flag"):
        flag = rule["user_agent_flag"]
        if flag.endswith("="):
            injected_cmd.append(f"{flag}{ua_value}")
        else:
            injected_cmd.extend([flag, ua_value])

    # Inject remaining headers
    for key, value in headers.items():
        if key == "User-Agent" and rule.get("user_agent_flag"):
            continue  # Already handled above

        if rule.get("header_flag") is not None:
            flag = rule["header_flag"]
            formatted_header = rule["header_format"].format(key=key, value=value)
            if flag == "":  # e.g. HTTPie
                injected_cmd.append(formatted_header)
            elif flag.endswith("="):
                injected_cmd.append(f"{flag}{formatted_header}")
            else:
                injected_cmd.extend([flag, formatted_header])

    # Append the rest of the original command arguments
    injected_cmd.extend(command[1:])
    return injected_cmd
