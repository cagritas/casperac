import typer
from rich.console import Console
from rich.table import Table

from casperac import core
from casperac import warp
from casperac import tor
from rich.theme import Theme

BANNER = r"""
[bold neon_green]
   ____                           _    ____ 
  / ___|__ _ ___ _ __   ___ _ __ / \  / ___|
 | |   / _` / __| '_ \ / _ \ '__/ _ \| |    
 | |__| (_| \__ \ |_) |  __/ | / ___ \ |___ 
  \____\__,_|___/ .__/ \___|_|/_/   \_\____|
                |_|                         
[/bold neon_green]
[bold purple]Advanced Dual-Layer Network Anonymization[/bold purple]
"""


custom_theme = Theme({"neon_green": "color(46)", "purple": "color(135)"})
console = Console(theme=custom_theme)

app = typer.Typer(
    help="casperac: A dual-layer network anonymization wrapper.", add_completion=False
)


def print_banner():
    console.print(BANNER)


@app.command()
def status():
    """Check the status of WARP and Tor connections."""
    print_banner()
    with console.status("[bold neon_green]Checking network status..."):
        warp_active = warp.is_warp_active()
        tor_listening = tor.is_tor_listening()

        tor_api_data = {}
        if tor_listening:
            tor_api_data = tor.get_tor_status()

    table = Table(
        title="CasperAC Status", show_header=True, header_style="bold magenta"
    )
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="green")

    # WARP Status
    warp_status = (
        "[bold green]Active[/bold green]"
        if warp_active
        else "[bold red]Inactive / Not Installed[/bold red]"
    )
    table.add_row(
        "Cloudflare WARP", warp_status, "Secures local link to Cloudflare edge"
    )

    # Tor Status
    tor_status = (
        "[bold green]Listening (9050)[/bold green]"
        if tor_listening
        else "[bold red]Not Listening[/bold red]"
    )

    if tor_listening and tor_api_data.get("IsTor"):
        ip_info = f"IP: {tor_api_data.get('IP', 'Unknown')}"
        tor_details = f"[bold green]Routed via Tor[/bold green] - {ip_info}"
    else:
        error_msg = tor_api_data.get("error", "Not routed via Tor")
        tor_details = (
            f"[bold red]Traffic not Torified[/bold red] - {error_msg}"
            if tor_listening
            else "Service offline"
        )

    table.add_row("Tor Network", tor_status, tor_details)

    console.print(table)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(ctx: typer.Context):
    """
    Run a command with Tor proxy environment variables injected.
    Example: casperac run -- curl -I https://api.github.com/user
    """
    print_banner()
    if not ctx.args:
        console.print(
            "[bold red]Error:[/bold red] No command provided. Use [cyan]casperac run -- <command>[/cyan]"
        )
        raise typer.Exit(code=1)

    if not tor.is_tor_listening():
        console.print(
            "[bold yellow]Warning:[/bold yellow] Tor SOCKS port (127.0.0.1:9050) is not listening. The command might fail or leak real IP."
        )

    exit_code = core.run_command_with_proxy(ctx.args)
    raise typer.Exit(code=exit_code)


@app.command()
def renew():
    """Renew the Tor circuit (SIGNAL NEWNYM) to acquire a new exit node IP."""
    print_banner()
    with console.status("[bold neon_green]Requesting new Tor circuit..."):
        success = tor.renew_tor_circuit()

    if success:
        console.print(
            "[bold green]Successfully signaled Tor to renew circuit![/bold green]"
        )

        with console.status("[bold blue]Verifying new exit IP..."):
            data = tor.get_tor_status()
            if data.get("IsTor"):
                console.print(f"New Exit IP: [bold cyan]{data.get('IP')}[/bold cyan]")
            else:
                console.print(
                    "[bold yellow]Tor API check failed or returned negative after renewal.[/bold yellow]"
                )
    else:
        console.print(
            "[bold red]Failed to renew Tor circuit.[/bold red] Ensure the Tor Control Port (9051) is active and does not require a password, or configure authentication."
        )


@app.command()
def env_on():
    """Outputs the shell commands to export proxy variables to the current session."""
    print_banner()
    print(f"export HTTP_PROXY={core.PROXY_URL}")
    print(f"export HTTPS_PROXY={core.PROXY_URL}")
    print(f"export ALL_PROXY={core.PROXY_URL}")
    print(f"export HTTP_USER_AGENT='{core.USER_AGENT}'")
    console.print("\n# To apply to your current shell, run:")
    console.print("# [bold cyan]eval $(casperac env-on)[/bold cyan]")


@app.command()
def env_off():
    """Outputs the shell commands to unset proxy variables from the current session."""
    print_banner()
    print("unset HTTP_PROXY")
    print("unset HTTPS_PROXY")
    print("unset ALL_PROXY")
    print("unset HTTP_USER_AGENT")
    console.print("\n# To apply to your current shell, run:")
    console.print("# [bold cyan]eval $(casperac env-off)[/bold cyan]")


if __name__ == "__main__":
    app()
