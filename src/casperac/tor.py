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
    global _ROTATOR_ACTIVE, _ROTATOR_INTERVAL
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
