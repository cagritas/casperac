from __future__ import annotations

import threading
import time

from casperac import sudo, tor
from casperac.globalvpn import get_active_network_services

_KILL_SWITCH_ACTIVE = False
_MONITOR_THREAD = None
_TRIGGERED = False


def _monitor_loop():
    global _KILL_SWITCH_ACTIVE, _TRIGGERED
    while _KILL_SWITCH_ACTIVE:
        if not tor.is_tor_listening():
            # Tor dropped! Trigger Kill-Switch
            _TRIGGERED = True
            services = get_active_network_services()
            for svc in services:
                # Bring down the network service immediately
                sudo.run_sudo_cmd(
                    ["networksetup", "-setnetworkserviceenabled", svc, "off"]
                )
            _KILL_SWITCH_ACTIVE = False
            break
        time.sleep(1.0)  # Check every second


def enable_killswitch():
    global _KILL_SWITCH_ACTIVE, _MONITOR_THREAD, _TRIGGERED
    _TRIGGERED = False
    if not _KILL_SWITCH_ACTIVE:
        _KILL_SWITCH_ACTIVE = True
        _MONITOR_THREAD = threading.Thread(target=_monitor_loop, daemon=True)
        _MONITOR_THREAD.start()


def disable_killswitch():
    global _KILL_SWITCH_ACTIVE
    _KILL_SWITCH_ACTIVE = False


def restore_network():
    """If the killswitch triggered, restores the network interfaces."""
    global _TRIGGERED
    services = [
        "Wi-Fi",
        "Ethernet",
    ]  # Fallback hardcoded if we can't fetch active ones when offline
    for svc in services:
        sudo.run_sudo_cmd(["networksetup", "-setnetworkserviceenabled", svc, "on"])
    _TRIGGERED = False


def is_triggered() -> bool:
    return _TRIGGERED


def is_active() -> bool:
    return _KILL_SWITCH_ACTIVE
