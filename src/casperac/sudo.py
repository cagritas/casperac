from __future__ import annotations

import subprocess

_SUDO_PASSWORD: str | None = None


def set_password(pwd: str) -> None:
    global _SUDO_PASSWORD
    _SUDO_PASSWORD = pwd


def has_password() -> bool:
    return _SUDO_PASSWORD is not None


def run_sudo_cmd(cmd_list: list[str]) -> subprocess.CompletedProcess:
    """Runs a sudo command using the cached password via stdin."""
    if not _SUDO_PASSWORD:
        raise ValueError("Sudo password not set!")

    full_cmd = ["sudo", "-S"] + cmd_list
    # Note: subprocess.run with input passes the password and auto-adds newline
    return subprocess.run(
        full_cmd,
        input=f"{_SUDO_PASSWORD}\n",
        capture_output=True,
        text=True,
        check=False,
    )


def verify_password(pwd: str) -> bool:
    """Verifies if the provided sudo password is correct by running a simple dummy command."""
    result = subprocess.run(
        ["sudo", "-S", "true"],
        input=f"{pwd}\n",
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0
