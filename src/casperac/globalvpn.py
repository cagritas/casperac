from __future__ import annotations

import platform
import shutil
import subprocess


def get_os_type() -> str:
    """Returns the operating system type."""
    return platform.system().lower()


def get_active_network_services() -> list[str]:
    """
    Returns a list of active network services on macOS (e.g., 'Wi-Fi', 'Ethernet').
    """
    if get_os_type() != "darwin":
        return []

    try:
        result = subprocess.run(
            ["networksetup", "-listallnetworkservices"],
            capture_output=True,
            text=True,
            check=True,
        )
        services = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            # Ignore informational lines and disabled services (which start with '*')
            if not line or line.startswith(("*", "An asterisk")):
                continue
            services.append(line)
        return services
    except subprocess.CalledProcessError:
        return []


def is_global_vpn_active() -> bool:
    """
    Checks if the Global SOCKS proxy is active on any network service.
    """
    os_type = get_os_type()

    if os_type == "darwin":
        services = get_active_network_services()
        for service in services:
            try:
                result = subprocess.run(
                    ["networksetup", "-getsocksfirewallproxy", service],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if "Enabled: Yes" in result.stdout and "127.0.0.1" in result.stdout:
                    return True
            except subprocess.SubprocessError:
                continue
        return False

    elif os_type == "linux":
        if not shutil.which("gsettings"):
            return False
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.system.proxy", "mode"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "'manual'" in result.stdout:
                host_result = subprocess.run(
                    ["gsettings", "get", "org.gnome.system.proxy.socks", "host"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if "'127.0.0.1'" in host_result.stdout:
                    return True
        except subprocess.SubprocessError:
            return False
        return False

    return False


def enable_global_vpn(host: str = "127.0.0.1", port: int = 9050) -> tuple[bool, str]:
    """
    Enables Global VPN mode by configuring the OS-level SOCKS proxy.
    On macOS, this might prompt the user for their system password via a native GUI dialogue.
    On Linux (GNOME), it modifies gsettings.
    """
    os_type = get_os_type()

    if os_type == "darwin":
        services = get_active_network_services()
        if not services:
            return False, "No active network services found to configure."

        success = False
        for service in services:
            try:
                subprocess.run(
                    [
                        "networksetup",
                        "-setsocksfirewallproxy",
                        service,
                        host,
                        str(port),
                    ],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["networksetup", "-setsocksfirewallproxystate", service, "on"],
                    check=True,
                    capture_output=True,
                )
                # DNS Leak Protection: Force Cloudflare DNS
                subprocess.run(
                    ["networksetup", "-setdnsservers", service, "1.1.1.1", "1.0.0.1"],
                    check=False,
                    capture_output=True,
                )
                success = True
            except subprocess.CalledProcessError:
                pass

        if success:
            return True, "Global VPN Mode successfully enabled on active Mac networks."
        return (
            False,
            "Failed to enable Global VPN Mode. Ensure you allow the system prompt if it appears.",
        )

    elif os_type == "linux":
        if not shutil.which("gsettings"):
            return (
                False,
                "Linux Global VPN is currently only supported on Desktop Environments using 'gsettings' (e.g., GNOME/Ubuntu).",
            )

        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy.socks", "host", host],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy.socks", "port", str(port)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"],
                check=True,
                capture_output=True,
            )
            return (
                True,
                "Global VPN Mode successfully enabled for GNOME (Ubuntu/Fedora).",
            )
        except subprocess.CalledProcessError:
            return False, "Failed to configure gsettings for Linux Global VPN."

    return False, f"Global VPN Mode is not supported on OS: {os_type}"


def disable_global_vpn() -> tuple[bool, str]:
    """
    Disables the Global VPN mode by turning off the OS-level SOCKS proxy.
    """
    os_type = get_os_type()

    if os_type == "darwin":
        services = get_active_network_services()
        if not services:
            return False, "No active network services found to configure."

        success = False
        for service in services:
            try:
                subprocess.run(
                    ["networksetup", "-setsocksfirewallproxystate", service, "off"],
                    check=True,
                    capture_output=True,
                )
                # Remove custom DNS
                subprocess.run(
                    ["networksetup", "-setdnsservers", service, "Empty"],
                    check=False,
                    capture_output=True,
                )
                success = True
            except subprocess.CalledProcessError:
                pass

        if success:
            return (
                True,
                "Global VPN Mode successfully disabled on macOS. Direct internet restored.",
            )
        return False, "Failed to disable Global VPN Mode on macOS."

    elif os_type == "linux":
        if not shutil.which("gsettings"):
            return False, "gsettings not found on this Linux system."

        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy", "mode", "none"],
                check=True,
                capture_output=True,
            )
            return (
                True,
                "Global VPN Mode successfully disabled for Linux GNOME. Direct internet restored.",
            )
        except subprocess.CalledProcessError:
            return False, "Failed to disable Linux Global VPN via gsettings."

    return False, f"Global VPN Mode is not supported on OS: {os_type}"
