import typer
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from casperac import antidetect, autodeploy, core, globalvpn, tor, warp

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
err_console = Console(theme=custom_theme, stderr=True)

app = typer.Typer(
    help="CasperAC: A dual-layer network anonymization tool featuring Global VPN, Anti-Detect Engine, and Zero-Config Auto-Deploy.",
    add_completion=False,
)


def print_banner():
    console.print(BANNER)


@app.command()
def status():
    """Check the status of WARP and Tor connections."""
    print_banner()
    with console.status("[bold neon_green]Checking network status..."):
        tor_listening = tor.is_tor_listening()
        warp_active = warp.is_warp_active()

    if not tor_listening:
        # Trigger Auto-Deploy outside of spinner so sudo prompts work
        console.print(
            "\n[bold yellow]Tor service not detected. Attempting Auto-Deploy...[/bold yellow]"
        )
        success, msg = autodeploy.check_and_deploy_tor()
        if success:
            console.print(f"[bold green]✔ {msg}[/bold green]")
        else:
            console.print(f"[bold red]✖ Auto-Deploy failed:[/bold red] {msg}")

    if not warp_active:
        console.print(
            "\n[bold yellow]Cloudflare WARP not detected. Attempting Auto-Deploy for maximum privacy...[/bold yellow]"
        )
        console.print(
            "[bold cyan]Note: You may be prompted for your system password to install Cloudflare WARP system extensions.[/bold cyan]"
        )
        success, msg = autodeploy.check_and_deploy_warp()
        if success:
            console.print(f"[bold green]✔ {msg}[/bold green]")
        else:
            console.print(f"[bold red]✖ WARP Auto-Deploy failed:[/bold red] {msg}")

    with console.status("[bold neon_green]Verifying final status..."):
        tor_listening = tor.is_tor_listening()
        warp_active = warp.is_warp_active()
        tor_api_data = {}
        if tor_listening:
            tor_api_data = tor.get_tor_status()

        is_global_vpn = globalvpn.is_global_vpn_active()

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

    # Global VPN Status
    gvpn_status = (
        "[bold green]Active[/bold green]"
        if is_global_vpn
        else "[bold red]Inactive[/bold red]"
    )
    table.add_row(
        "Global VPN Mode", gvpn_status, "Routes entire OS traffic through Tor"
    )

    console.print(table)


@app.command()
def global_on():
    """Enables Global VPN Mode (routes all OS traffic through Tor)."""
    print_banner()
    if not tor.is_tor_listening():
        console.print(
            "[bold yellow]Tor is not running. Attempting Auto-Deploy...[/bold yellow]"
        )
        success, msg = autodeploy.check_and_deploy_tor()
        if not success:
            console.print(
                f"[bold red]Cannot enable Global VPN. Tor failed to start: {msg}[/bold red]"
            )
            raise typer.Exit(code=1)

    with console.status("[bold neon_green]Configuring OS-level SOCKS proxy..."):
        success, msg = globalvpn.enable_global_vpn()

    if success:
        console.print(f"[bold green]✔ {msg}[/bold green]")
        console.print(
            "[bold yellow]All system traffic (browsers, apps) is now routed through Tor.[/bold yellow]"
        )
    else:
        console.print(f"[bold red]✖ {msg}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def global_off():
    """Disables Global VPN Mode and restores normal OS routing."""
    print_banner()
    with console.status("[bold neon_green]Restoring OS-level proxy settings..."):
        success, msg = globalvpn.disable_global_vpn()

    if success:
        console.print(f"[bold green]✔ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✖ {msg}[/bold red]")
        raise typer.Exit(code=1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    mobile: bool = typer.Option(
        False, "--mobile", help="Spoof a mobile device identity."
    ),
    desktop: bool = typer.Option(
        False, "--desktop", help="Spoof a desktop device identity (Default)."
    ),
    browser: str = typer.Option(
        None,
        "--browser",
        help="Spoof a specific browser (e.g. chrome, firefox, safari).",
    ),
):
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
            "\n[bold yellow]Tor not detected, attempting Auto-Deploy...[/bold yellow]"
        )
        success, msg = autodeploy.check_and_deploy_tor()

        if success:
            console.print(f"[bold green]✔ {msg}[/bold green]")
        else:
            console.print(
                "[bold yellow]Warning:[/bold yellow] Tor SOCKS port (127.0.0.1:9050) is not listening and Auto-Deploy failed. The command might fail or leak real IP."
            )
            console.print(f"[dim]{msg}[/dim]")

    if not warp.is_warp_active():
        console.print(
            "[bold yellow]Privacy Warning:[/bold yellow] Cloudflare WARP is not active. Your ISP can see you are connecting to Tor. Run `casperac status` to auto-deploy WARP for maximum privacy."
        )

    device_type = "mobile" if mobile else "desktop"
    exit_code = core.run_command_with_proxy(
        ctx.args, device_type=device_type, browser=browser
    )
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
    # We should not print the banner to stdout if the user is evaluating this (eval $(casperac env-on))
    # It would cause bash syntax errors.

    headers = antidetect.get_random_identity("desktop")
    ua = headers.get("User-Agent", "Mozilla/5.0")

    print(f"export HTTP_PROXY={core.PROXY_URL}")
    print(f"export HTTPS_PROXY={core.PROXY_URL}")
    print(f"export ALL_PROXY={core.PROXY_URL}")
    print(f"export HTTP_USER_AGENT='{ua}'")

    # Send instructions to stderr so it doesn't break eval
    err_console.print("\n# To apply to your current shell, run:")
    err_console.print("# [bold cyan]eval $(casperac env-on)[/bold cyan]")


@app.command()
def env_off():
    """Outputs the shell commands to unset proxy variables from the current session."""
    print("unset HTTP_PROXY")
    print("unset HTTPS_PROXY")
    print("unset ALL_PROXY")
    print("unset HTTP_USER_AGENT")

    err_console.print("\n# To apply to your current shell, run:")
    err_console.print("# [bold cyan]eval $(casperac env-off)[/bold cyan]")


@app.command()
def ui():
    """Starts the CasperAC System Tray Icon and GUI."""
    print_banner()
    console.print("[bold green]Starting CasperAC UI in the background...[/bold green]")
    console.print("Check your system tray / menu bar for the CasperAC icon.")
    from casperac import ui as casper_ui
    casper_ui.start_tray()


@app.command(hidden=True)
def window():
    """Internal command to launch the GUI window process."""
    from casperac import ui as casper_ui
    casper_ui.start_window()


if __name__ == "__main__":
    app()

