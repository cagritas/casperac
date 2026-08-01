from __future__ import annotations

import platform
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
    if get_os_type() != "darwin":
        return False

    services = get_active_network_services()
    for service in services:
        try:
            result = subprocess.run(
                ["networksetup", "-getsocksfirewallproxy", service],
                capture_output=True,
                text=True,
                check=False,
            )
            # If enabled is yes and proxy is 127.0.0.1:9050, it is active
            if "Enabled: Yes" in result.stdout and "127.0.0.1" in result.stdout:
                return True
        except subprocess.SubprocessError:
            continue
    return False


def enable_global_vpn(host: str = "127.0.0.1", port: int = 9050) -> tuple[bool, str]:
    """
    Enables Global VPN mode by configuring the OS-level SOCKS proxy.
    On macOS, this might prompt the user for their system password via a native GUI dialogue.
    """
    os_type = get_os_type()
    if os_type != "darwin":
        return False, "Global VPN Mode is currently only supported on macOS."

    services = get_active_network_services()
    if not services:
        return False, "No active network services found to configure."

    success = False
    for service in services:
        try:
            # Set the SOCKS proxy details
            subprocess.run(
                ["networksetup", "-setsocksfirewallproxy", service, host, str(port)],
                check=True,
                capture_output=True,
            )
            # Enable the SOCKS proxy state
            subprocess.run(
                ["networksetup", "-setsocksfirewallproxystate", service, "on"],
                check=True,
                capture_output=True,
            )
            success = True
        except subprocess.CalledProcessError:
            # Continue trying other services even if one fails
            pass

    if success:
        return (
            True,
            "Global VPN Mode (OS-level SOCKS Proxy) successfully enabled on active networks.",
        )
    else:
        return (
            False,
            "Failed to enable Global VPN Mode. Ensure you allow the system prompt if it appears.",
        )


def disable_global_vpn() -> tuple[bool, str]:
    """
    Disables the Global VPN mode by turning off the OS-level SOCKS proxy.
    """
    os_type = get_os_type()
    if os_type != "darwin":
        return False, "Global VPN Mode is currently only supported on macOS."

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
            success = True
        except subprocess.CalledProcessError:
            pass

    if success:
        return True, "Global VPN Mode successfully disabled. Direct internet restored."
    else:
        return False, "Failed to disable Global VPN Mode."
