import subprocess
import sys
import threading
from PIL import Image, ImageDraw
import pystray
import customtkinter as ctk

from casperac import globalvpn, tor, warp, autodeploy
from casperac import sudo, killswitch

# --- THEME & SETUP ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class SudoDialog(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("380x250")
        self.title("Security Authorization")
        self.attributes("-topmost", True)
        self.password = None
        
        self.label = ctk.CTkLabel(self, text="⚠️ Yetkilendirme Gerekiyor", font=ctk.CTkFont(size=16, weight="bold"), text_color="yellow")
        self.label.pack(pady=(20, 5))
        
        self.info = ctk.CTkLabel(self, text="Kill-Switch gibi sistem ağını koruyan derin\nmüdahaleler için Mac/Linux yönetici şifreniz gereklidir.", justify="center")
        self.info.pack(pady=5)
        
        self.pwd_entry = ctk.CTkEntry(self, show="*", width=200, placeholder_text="Yönetici Şifresi (Sudo)")
        self.pwd_entry.pack(pady=15)
        self.pwd_entry.bind("<Return>", lambda event: self.submit())
        
        self.submit_btn = ctk.CTkButton(self, text="Yetki Ver", command=self.submit, fg_color="#8a2be2", hover_color="#5a189a")
        self.submit_btn.pack(pady=5)
        
    def submit(self):
        self.password = self.pwd_entry.get()
        self.destroy()
        
    def get_password(self):
        self.wait_window()
        return self.password

class CasperWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CasperAC - Ghost Console")
        self.geometry("340x550")
        self.resizable(False, False)
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        
        # Title Label
        self.title_label = ctk.CTkLabel(
            self, text="CASPER AC", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(15, 10))
        
        # Status Frame
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, pady=5)
        
        self.tor_status = ctk.CTkLabel(self.status_frame, text="Tor: Checking...", text_color="yellow")
        self.tor_status.grid(row=0, column=0, padx=10)
        
        self.vpn_status = ctk.CTkLabel(self.status_frame, text="VPN: Checking...", text_color="yellow")
        self.vpn_status.grid(row=1, column=0, padx=10)

        # Global VPN Toggle
        self.vpn_switch = ctk.CTkSwitch(
            self, text="Global VPN Mode", command=self.toggle_vpn,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.vpn_switch.grid(row=2, column=0, pady=(15, 5))
        
        # Kill-Switch Toggle
        self.ks_switch = ctk.CTkSwitch(
            self, text="Kill-Switch (Ağ Kesici)", command=self.toggle_killswitch,
            font=ctk.CTkFont(size=14, weight="bold"), button_color="red", button_hover_color="darkred"
        )
        self.ks_switch.grid(row=3, column=0, pady=5)
        
        # Restore Network Button (Hidden by default)
        self.restore_btn = ctk.CTkButton(
            self, text="Ağı Geri Yükle (Restore)", command=self.restore_network,
            fg_color="red", hover_color="darkred"
        )
        self.restore_btn.grid(row=4, column=0, pady=5)
        self.restore_btn.grid_remove() # Hide initially
        
        # Auto-Rotate Toggle
        self.rotate_switch = ctk.CTkSwitch(
            self, text="Auto-Rotate IP (5 dk)", command=self.toggle_rotate,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.rotate_switch.grid(row=5, column=0, pady=5)
        
        # Renew IP Button
        self.renew_btn = ctk.CTkButton(
            self, text="Renew IP Identity", command=self.renew_ip,
            fg_color="#8a2be2", hover_color="#5a189a" # Purple colors
        )
        self.renew_btn.grid(row=6, column=0, pady=10)
        
        # Logs / Info Box
        self.log_box = ctk.CTkTextbox(self, width=300, height=130, state="disabled")
        self.log_box.grid(row=7, column=0, pady=15)
        
        self.log("CasperAC GUI Initialized.")
        
        # Check if killswitch triggered
        self.check_killswitch_trigger()
        
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
            
        if killswitch.is_active():
            self.ks_switch.select()
        else:
            self.ks_switch.deselect()
            
    def check_killswitch_trigger(self):
        if killswitch.is_triggered():
            self.log("⚠️ KILL-SWITCH TETİKLENDİ! Ağ Koptu.")
            self.ks_switch.deselect()
            self.restore_btn.grid() # Show restore button
        
        self.after(2000, self.check_killswitch_trigger)

    def request_sudo(self):
        """Asks for sudo password if not already cached."""
        if sudo.has_password():
            return True
            
        dialog = SudoDialog(self)
        pwd = dialog.get_password()
        
        if pwd:
            if sudo.verify_password(pwd):
                sudo.set_password(pwd)
                self.log("Sudo yetkisi doğrulandı.")
                return True
            else:
                self.log("Hata: Sudo şifresi yanlış!")
                return False
        return False

    def toggle_killswitch(self):
        if self.ks_switch.get() == 1:
            if not self.request_sudo():
                self.ks_switch.deselect()
                return
            
            self.log("Kill-Switch Aktif Edildi. Tor düşerse ağ anında kesilecek.")
            killswitch.enable_killswitch()
        else:
            self.log("Kill-Switch Kapatıldı.")
            killswitch.disable_killswitch()
            
    def restore_network(self):
        if not self.request_sudo():
            return
        
        self.log("Ağ bağlantıları geri yükleniyor...")
        threading.Thread(target=self._restore_network, daemon=True).start()
        
    def _restore_network(self):
        killswitch.restore_network()
        self.log("Ağ başarıyla geri yüklendi.")
        # Hide button in main thread
        self.after(0, self.restore_btn.grid_remove)
        
    def toggle_rotate(self):
        if self.rotate_switch.get() == 1:
            self.log("Auto-Rotate Aktif (5 dakikada bir yenilenecek).")
            tor.start_auto_rotate(5, self._on_auto_rotate)
        else:
            self.log("Auto-Rotate Kapatıldı.")
            tor.stop_auto_rotate()
            
    def _on_auto_rotate(self, success):
        if success:
            self.log("🔄 Otomatik IP rotasyonu başarılı!")
            # Delay fetch slightly
            self.after(2000, self._fetch_ip_background)
        else:
            self.log("🔄 Otomatik IP yenileme başarısız.")
            
    def _fetch_ip_background(self):
        threading.Thread(target=self._do_fetch_ip, daemon=True).start()
        
    def _do_fetch_ip(self):
        data = tor.get_tor_status()
        if data.get("IsTor"):
            self.log(f"Yeni IP: {data.get('IP')}")

    def toggle_vpn(self):
        if self.vpn_switch.get() == 1:
            self.log("Enabling Global VPN...")
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
    image = Image.new('RGB', (64, 64), color=(30, 0, 50))
    d = ImageDraw.Draw(image)
    d.arc([10, 10, 54, 54], start=45, end=315, fill=(0, 255, 0), width=8)
    return image


def start_window():
    app = CasperWindow()
    app.mainloop()


def on_open_clicked(icon, item):
    subprocess.Popen(["casperac", "window"])


def on_quit_clicked(icon, item):
    icon.stop()


def start_tray():
    image = create_tray_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem('Open CasperAC', on_open_clicked, default=True),
        pystray.MenuItem('Quit', on_quit_clicked)
    )
    icon = pystray.Icon("CasperAC", image, "CasperAC", menu)
    icon.run()

