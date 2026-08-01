import socket
import requests
from typing import Dict


def is_tor_listening(host: str = "127.0.0.1", port: int = 9050) -> bool:
    """Checks if the Tor SOCKS port is listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, TimeoutError, OSError):
            return False


def get_tor_status() -> Dict:
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


def renew_tor_circuit(
    host: str = "127.0.0.1", port: int = 9051, password: str = ""
) -> bool:
    """Sends SIGNAL NEWNYM to Tor control port to renew circuit."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, port))

            # Authenticate
            if password:
                s.sendall(f'AUTHENTICATE "{password}"\r\n'.encode("utf-8"))
            else:
                s.sendall(b'AUTHENTICATE ""\r\n')

            response = s.recv(1024).decode("utf-8")
            if not response.startswith("250"):
                return False

            # Send NewNym signal
            s.sendall(b"SIGNAL NEWNYM\r\n")
            response = s.recv(1024).decode("utf-8")
            return response.startswith("250")
    except Exception:
        return False
