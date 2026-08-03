import subprocess
import sys
import threading
from PIL import Image, ImageDraw
import pystray
import customtkinter as ctk

from casperac import globalvpn, tor, warp, autodeploy

# --- THEME & SETUP ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class CasperWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CasperAC - Ghost Console")
        self.geometry("320x450")
        self.resizable(False, False)
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        
        # Title Label
        self.title_label = ctk.CTkLabel(
            self, text="CASPER AC", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(20, 10))
        
        # Status Frame
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, pady=10)
        
        self.tor_status = ctk.CTkLabel(self.status_frame, text="Tor: Checking...", text_color="yellow")
        self.tor_status.grid(row=0, column=0, padx=10)
        
        self.vpn_status = ctk.CTkLabel(self.status_frame, text="VPN: Checking...", text_color="yellow")
        self.vpn_status.grid(row=1, column=0, padx=10)

        # Global VPN Toggle
        self.vpn_switch = ctk.CTkSwitch(
            self, text="Global VPN Mode", command=self.toggle_vpn,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.vpn_switch.grid(row=2, column=0, pady=(20, 10))
        
        # Renew IP Button
        self.renew_btn = ctk.CTkButton(
            self, text="Renew IP Identity", command=self.renew_ip,
            fg_color="#8a2be2", hover_color="#5a189a" # Purple colors
        )
        self.renew_btn.grid(row=3, column=0, pady=10)
        
        # Logs / Info Box
        self.log_box = ctk.CTkTextbox(self, width=280, height=120, state="disabled")
        self.log_box.grid(row=4, column=0, pady=20)
        
        self.log("CasperAC GUI Initialized.")
        
        # Initial Status Update
        self.update_status()

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"> {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_status(self):
        # Update Tor
        if tor.is_tor_listening():
            self.tor_status.configure(text="Tor: Active (9050)", text_color="#00ff00")
        else:
            self.tor_status.configure(text="Tor: Offline", text_color="red")
            
        # Update VPN
        if globalvpn.is_global_vpn_active():
            self.vpn_status.configure(text="Global VPN: Active", text_color="#00ff00")
            self.vpn_switch.select()
        else:
            self.vpn_status.configure(text="Global VPN: Offline", text_color="red")
            self.vpn_switch.deselect()

    def toggle_vpn(self):
        if self.vpn_switch.get() == 1:
            self.log("Enabling Global VPN...")
            # Run in thread to not freeze GUI
            threading.Thread(target=self._enable_vpn, daemon=True).start()
        else:
            self.log("Disabling Global VPN...")
            threading.Thread(target=self._disable_vpn, daemon=True).start()

    def _enable_vpn(self):
        if not tor.is_tor_listening():
            self.log("Starting Tor via AutoDeploy...")
            autodeploy.check_and_deploy_tor()
        success, msg = globalvpn.enable_global_vpn()
        if success:
            self.log("VPN Enabled Successfully.")
        else:
            self.log(f"Error: {msg}")
        self.after(500, self.update_status)

    def _disable_vpn(self):
        success, msg = globalvpn.disable_global_vpn()
        if success:
            self.log("VPN Disabled.")
        else:
            self.log(f"Error: {msg}")
        self.after(500, self.update_status)

    def renew_ip(self):
        self.log("Renewing Tor IP...")
        threading.Thread(target=self._renew_ip, daemon=True).start()
        
    def _renew_ip(self):
        success = tor.renew_tor_circuit()
        if success:
            self.log("Circuit renewed! Fetching new IP...")
            data = tor.get_tor_status()
            if data.get("IsTor"):
                self.log(f"New IP: {data.get('IP')}")
            else:
                self.log("Failed to fetch new IP.")
        else:
            self.log("Failed to renew circuit.")


def create_tray_icon_image():
    # Create a 64x64 image with a dark purple background and neon green 'C'
    image = Image.new('RGB', (64, 64), color=(30, 0, 50))
    d = ImageDraw.Draw(image)
    d.arc([10, 10, 54, 54], start=45, end=315, fill=(0, 255, 0), width=8)
    return image


def start_window():
    """Starts the CustomTkinter GUI. Called as a separate process."""
    app = CasperWindow()
    app.mainloop()


def on_open_clicked(icon, item):
    # Launch the GUI in a new process to avoid macOS thread blocking issues
    subprocess.Popen(["casperac", "window"])


def on_quit_clicked(icon, item):
    icon.stop()


def start_tray():
    """Starts the pystray system tray icon."""
    image = create_tray_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem('Open CasperAC', on_open_clicked, default=True),
        pystray.MenuItem('Quit', on_quit_clicked)
    )
    icon = pystray.Icon("CasperAC", image, "CasperAC", menu)
    icon.run()

