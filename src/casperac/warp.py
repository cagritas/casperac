import subprocess


def is_warp_active() -> bool:
    """Checks if Cloudflare warp-cli is active."""
    try:
        result = subprocess.run(
            ["warp-cli", "status"], capture_output=True, text=True, check=False
        )
        return (
            "Connected" in result.stdout or "Status update: Connected" in result.stdout
        )
    except FileNotFoundError:
        return False
