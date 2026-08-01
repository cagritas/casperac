from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time


def is_tor_installed() -> bool:
    """Checks if the 'tor' executable is available in the system PATH or standard Homebrew paths."""
    if shutil.which("tor"):
        return True
    return os.path.exists("/opt/homebrew/bin/tor") or os.path.exists(
        "/usr/local/bin/tor"
    )


def get_os_type() -> str:
    """Returns the operating system type."""
    return platform.system().lower()


def install_tor_macos() -> tuple[bool, str]:
    """Installs Tor on macOS using Homebrew."""
    if not shutil.which("brew"):
        return (
            False,
            "Homebrew (brew) is not installed on this Mac. Cannot auto-install Tor.",
        )

    try:
        # Install tor
        subprocess.run(["brew", "install", "tor"], check=True, capture_output=True)
        # Start tor service
        subprocess.run(
            ["brew", "services", "start", "tor"], check=True, capture_output=True
        )
        return True, "Tor successfully installed and started via Homebrew."
    except subprocess.CalledProcessError as e:
        return (
            False,
            f"Brew installation failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}",
        )


def install_tor_linux() -> tuple[bool, str]:
    """Installs Tor on Linux using apt-get (requires sudo)."""
    if not shutil.which("apt-get"):
        return (
            False,
            "apt-get is not found. Only Debian/Ubuntu based Linux is currently supported for auto-install.",
        )

    try:
        # Note: This will prompt for sudo password in the terminal if not running as root
        subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "tor"], check=True, capture_output=True
        )
        subprocess.run(
            ["sudo", "systemctl", "start", "tor"], check=False, capture_output=True
        )
        return True, "Tor successfully installed and started via apt."
    except subprocess.CalledProcessError as e:
        return (
            False,
            f"Apt installation failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}",
        )


def check_and_deploy_tor() -> tuple[bool, str]:
    """
    Main entry point for autodeploy.
    Returns (Success, Message).
    """
    if is_tor_installed():
        # If it is installed but not listening, try to start it based on OS
        os_type = get_os_type()
        try:
            if os_type == "darwin" and shutil.which("brew"):
                subprocess.run(
                    ["brew", "services", "start", "tor"],
                    check=False,
                    capture_output=True,
                )
                time.sleep(2)  # Give it a moment to bind to 9050
                return True, "Tor was already installed. Restarted service via brew."
            elif os_type == "linux":
                subprocess.run(
                    ["sudo", "systemctl", "start", "tor"],
                    check=False,
                    capture_output=True,
                )
                time.sleep(2)
                return (
                    True,
                    "Tor was already installed. Restarted service via systemctl.",
                )
            else:
                # Generic fallback, just try to run it in background
                subprocess.Popen(
                    ["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                time.sleep(2)
                return (
                    True,
                    "Tor was already installed. Launched generic daemon process.",
                )
        except OSError as e:
            return False, f"Tor is installed but failed to start: {e!s}"

    # Not installed, need to install
    os_type = get_os_type()
    if os_type == "darwin":
        success, msg = install_tor_macos()
    elif os_type == "linux":
        success, msg = install_tor_linux()
    elif os_type == "windows":
        return (
            False,
            "Auto-install on Windows is not supported yet. Please download Tor Expert Bundle or install Tor Browser.",
        )
    else:
        return False, f"Unsupported operating system for auto-install: {os_type}"

    if not success:
        return False, msg

    # Wait up to 10 seconds for Tor to become available
    for _ in range(10):
        if _is_tor_listening_local():
            return True, msg
        time.sleep(1)

    return True, msg + " (Tor was started but hasn't bound to port 9050 yet)"


def _is_tor_listening_local() -> bool:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", 9050))
        return True
    except OSError:
        return False
    finally:
        s.close()
