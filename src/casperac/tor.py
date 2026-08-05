from __future__ import annotations

import socket
import threading
import time

import requests


def is_tor_listening(host: str = "127.0.0.1", port: int = 9050) -> bool:
    """Checks if the Tor SOCKS port is listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, TimeoutError, OSError):
            return False

def get_tor_status() -> dict:
    """Checks the Tor status using the check.torproject.org API."""
    proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
    try:
        response = requests.get(
            "https://check.torproject.org/api/ip", proxies=proxies, timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"IsTor": False, "IP": "Unknown", "error": str(e)}

def renew_tor_circuit(host: str = "127.0.0.1", port: int = 9051, password: str = "") -> bool:
    """Sends SIGNAL NEWNYM to Tor control port to renew circuit."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, port))

            if password:
                s.sendall(f'AUTHENTICATE "{password}"\r\n'.encode())
            else:
                s.sendall(b'AUTHENTICATE ""\r\n')

            response = s.recv(1024).decode("utf-8")
            if not response.startswith("250"):
                return False

            s.sendall(b"SIGNAL NEWNYM\r\n")
            response = s.recv(1024).decode("utf-8")
            return response.startswith("250")
    except OSError:
        return False

# --- AUTO ROTATION ---
_ROTATOR_ACTIVE = False
_ROTATOR_THREAD = None
_ROTATOR_INTERVAL = 300 # seconds

def _rotation_loop(callback):
    while _ROTATOR_ACTIVE:
        # Sleep in small chunks to allow quick cancellation
        for _ in range(_ROTATOR_INTERVAL):
            if not _ROTATOR_ACTIVE:
                break
            time.sleep(1)
            
        if _ROTATOR_ACTIVE:
            success = renew_tor_circuit()
            if callback:
                callback(success)

def start_auto_rotate(interval_minutes: int, callback=None):
    global _ROTATOR_ACTIVE, _ROTATOR_THREAD, _ROTATOR_INTERVAL
    _ROTATOR_INTERVAL = interval_minutes * 60
    if not _ROTATOR_ACTIVE:
        _ROTATOR_ACTIVE = True
        _ROTATOR_THREAD = threading.Thread(target=_rotation_loop, args=(callback,), daemon=True)
        _ROTATOR_THREAD.start()

def stop_auto_rotate():
    global _ROTATOR_ACTIVE
    _ROTATOR_ACTIVE = False
    
def is_auto_rotate_active() -> bool:
    return _ROTATOR_ACTIVE

# --- EXIT NODE COUNTRY SELECTION ---
def set_exit_country(country_code: str = "Random") -> tuple[bool, str]:
    """Updates torrc with a specific country code for ExitNodes and restarts Tor."""
    import os
    import platform
    import subprocess
    
    os_type = platform.system().lower()
    if os_type == "darwin":
        torrc_path = "/opt/homebrew/etc/tor/torrc"
        if not os.path.exists(torrc_path):
            torrc_path = "/usr/local/etc/tor/torrc"
        restart_cmd = ["brew", "services", "restart", "tor"]
    elif os_type == "linux":
        torrc_path = "/etc/tor/torrc"
        restart_cmd = ["sudo", "systemctl", "restart", "tor"]
    else:
        return False, "Unsupported OS for country selection."

    if not os.path.exists(torrc_path):
        return False, f"torrc file not found at {torrc_path}"

    try:
        # We need to read, remove old ExitNodes, append new
        # Due to permissions, we'll try direct file access, fallback to sudo is complex, 
        # but on mac it's usually user-owned. On Linux, we might need sudo.
        from casperac import sudo
        
        # Read contents
        if os.access(torrc_path, os.R_OK):
            with open(torrc_path, 'r') as f:
                lines = f.readlines()
        else:
            res = sudo.run_sudo_cmd(["cat", torrc_path])
            if res.returncode != 0:
                return False, "Failed to read torrc (Permission denied)."
            lines = res.stdout.splitlines(True)
            
        # Filter out old ExitNodes
        new_lines = [l for l in lines if not l.startswith("ExitNodes") and not l.startswith("StrictNodes")]
        
        if country_code != "Random":
            new_lines.append(f"\nExitNodes {{{country_code}}}\n")
            new_lines.append("StrictNodes 1\n")
            
        new_content = "".join(new_lines)
        
        # Write back
        if os.access(torrc_path, os.W_OK):
            with open(torrc_path, 'w') as f:
                f.write(new_content)
        else:
            # Create a temp file and sudo mv it
            import tempfile
            fd, tmp_path = tempfile.mkstemp()
            with open(fd, 'w') as f:
                f.write(new_content)
            sudo.run_sudo_cmd(["mv", tmp_path, torrc_path])
            
        # Restart Tor
        if restart_cmd[0] == "sudo":
            sudo.run_sudo_cmd(restart_cmd[1:])
        else:
            subprocess.run(restart_cmd, check=False, capture_output=True)
            
        return True, f"Country set to {country_code}. Tor restarted."
    except Exception as e:  # noqa: BLE001
        return False, str(e)

