import os
import sys
import zipfile
import shutil
import urllib.request
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

# ⚠️ GITHUB'DAKİ version.json DOSYASININ "RAW" LİNKİ
JSON_URL = "https://raw.githubusercontent.com/Arcdashckr/EzeliCraft/main/modpack_updater/version.json"
CURRENT_UPDATER_VERSION = "2.0.6"

class IncrementalLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EzeliCraft Smart Launcher v2.0.6")
        self.root.geometry("550x450")
        self.root.resizable(False, False)
        
        # Modern Koyu Tema (Catppuccin Mocha)
        self.bg_color = "#1e1e2e"
        self.card_color = "#252538"
        self.accent_color = "#89b4fa"
        self.text_color = "#cdd6f4"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TProgressbar", thickness=18, troughcolor=self.card_color, background=self.accent_color)
        
        self.current_dir = os.getcwd()
        self.remote_data = {}
        
        self.create_widgets()
        Thread(target=self.check_launcher_update_and_load, daemon=True).start()

    def create_widgets(self):
        self.title_frame = tk.Frame(self.root, bg=self.bg_color)
        self.title_frame.pack(pady=10, padx=20, fill="x")
        
        self.title_label = tk.Label(self.title_frame, text="EzeliCraft Akıllı Güncelleyici", font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.accent_color)
        self.title_label.pack(side="left")
        
        self.version_label = tk.Label(self.title_frame, text=f"Launcher v{CURRENT_UPDATER_VERSION}", font=("Helvetica", 9), bg=self.bg_color, fg="#6c7086")
        self.version_label.pack(side="right", pady=4)
        
        self.status_card = tk.Frame(self.root, bg=self.card_color, bd=0, highlightbackground="#45475a", highlightthickness=1)
        self.status_card.pack(pady=5, padx=20, fill="x")
        
        self.status_label = tk.Label(self.status_card, text="Bağlantı kuruluyor, sürüm denetleniyor...", font=("Helvetica", 10, "bold"), bg=self.card_color, fg=self.text_color, justify="center")
        self.status_label.pack(pady=12, padx=10)
        
        changelog_title = tk.Label(self.root, text="Yenilikler ve Değişiklik Notları:", font=("Helvetica", 10, "bold"), bg=self.bg_color, fg=self.text_color)
        changelog_title.pack(anchor="w", padx=25, pady=(10, 2))
        
        self.changelog_box = tk.Text(self.root, font=("Helvetica", 9), bg=self.card_color, fg=self.text_color, bd=0, highlightbackground="#45475a", highlightthickness=1, wrap="word", height=8)
        self.changelog_box.pack(pady=5, padx=20, fill="x")
        self.changelog_box.insert("1.0", " Güncelleme notları yükleniyor...")
        self.changelog_box.config(state="disabled")
        
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=510, mode="determinate", style="TProgressbar")
        self.progress.pack(pady=10)
        
        self.btn_update = tk.Button(self.root, text="Güncellemeyi Denetle", font=("Helvetica", 11, "bold"), bg="#45475a", fg=self.bg_color, activebackground=self.accent_color, activeforeground=self.bg_color, bd=0, padx=25, pady=8, state="disabled")
        self.btn_update.pack(pady=10)

    def check_launcher_update_and_load(self):
        try:
            # 1. GitHub üzerindeki sürüm JSON dosyasını çekiyoruz (Tarayıcı taklidi ile)
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                self.remote_data = json.loads(response.read().decode('utf-8'))
            
            # --- PROGRAMIN KENDİ KENDİNİ GÜNCELLEMESİ (ZAMAN DAMGALI & ESKİLERİ TEMİZLEYEN V4) ---
            remote_updater_ver = self.remote_data.get("updater_version", "1.0.0")
            if remote_updater_ver != CURRENT_UPDATER_VERSION:
                self.status_label.config(text="Launcher yeni sürüme yükseltiliyor, lütfen bekleyin...", fg=self.accent_color)
                self.root.update_idletasks()
                
                current_exe = sys.executable
                
                # Eğer .py formatında çalışıyorsa güncellemeyi atla (geliştirici modu)
                if current_exe.endswith(".exe"):
                    import time
                    # Kullanıcı kazara eski bir '_yeni.exe' açsa bile indirme çakışmasını önlemek için benzersiz isim
                    timestamp = int(time.time())
                    temp_exe_name = f"Modpack_Guncelleyici_temp_{timestamp}.exe"
                    new_exe_path = os.path.join(self.current_dir, temp_exe_name)
                    
                    updater_url = self.remote_data.get("updater_url")
                    
                    # Yeni .exe'yi benzersiz geçici ismiyle indir
                    opener = urllib.request.build_opener()
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(updater_url, new_exe_path)
                    
                    pid = os.getpid()
                    final_exe_name = os.path.join(self.current_dir, "Modpack_Guncelleyici_v2.exe")
                    
                    # Eski manuel ve otomatik güncelleyicilerin yolları
                    old_manuel = os.path.join(self.current_dir, "Modpack_Guncelleyici_MANUEL.exe")
                    old_otomatik = os.path.join(self.current_dir, "Modpack_Guncelleyici_OTOMATİK.exe")
                    
                    # Güçlendirilmiş Görünmez PowerShell Betiği:
                    # 1. PID üzerinden mevcut programın tamamen kapanmasını bekler.
                    # 2. Şu an çalışan dosyayı diskten siler.
                    # 3. Klasörde önceden kalma v2, MANUEL veya OTOMATİK güncelleyiciler varsa hepsini temizler.
                    # 4. Yeni indirilen benzersiz temp dosyasını "Modpack_Guncelleyici_v2.exe" yapar ve başlatır.
                    ps_script = f"""
                    Start-Sleep -Seconds 1
                    $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
                    if ($proc) {{ $proc | Wait-Process -Timeout 5 }}
                    if (Test-Path "{current_exe}") {{ Remove-Item "{current_exe}" -Force }}
                    if (Test-Path "{final_exe_name}") {{ Remove-Item "{final_exe_name}" -Force }}
                    if (Test-Path "{old_manuel}") {{ Remove-Item "{old_manuel}" -Force }}
                    if (Test-Path "{old_otomatik}") {{ Remove-Item "{old_otomatik}" -Force }}
                    Rename-Item "{new_exe_path}" "Modpack_Guncelleyici_v2.exe" -Force
                    Start-Process "{final_exe_name}"
                    """
                    
                    subprocess.Popen(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
                    self.root.destroy()
                    sys.exit(0)
                    return

            # --- NORMAL MODPACK SÜRÜM KONTROLÜ ---
            local_version_path = os.path.join(self.current_dir, "local_version.json")
            local_ver = "0.0.0"
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r') as f:
                        local_ver = json.load(f).get("version", "0.0.0")
                except: pass
                
            remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
            
            # Değişiklik notlarını listeleme
            self.changelog_box.config(state="normal")
            self.changelog_box.delete("1.0", tk.END)
            for line in self.remote_data.get("changelog", ["• Değişiklik notu yok."]):
                self.changelog_box.insert(tk.END, f"{line}\n")
            self.changelog_box.config(state="disabled")
            
            if local_ver == remote_modpack_ver:
                self.status_label.config(text=f"Mod paketi tamamen güncel! (Sürüm: v{local_ver})", fg=self.success_color)
                self.btn_update.config(text="Dosyaları Kontrol Et / Onar", bg="#a6e3a1", state="normal", command=self.start_update_thread)
            else:
                self.status_label.config(text=f"Yeni Akıllı Güncelleme Hazır!\nv{local_ver} -> v{remote_modpack_ver}", fg=self.error_color)
                self.btn_update.config(text="Değişiklikleri Uygula", bg=self.accent_color, state="normal", command=self.start_update_thread)
                
        except Exception as e:
            self.status_label.config(text=f"Hata oluştu: {str(e)}", fg=self.error_color)

    def start_update_thread(self):
        self.btn_update.config(state="disabled")
        Thread(target=self.perform_incremental_update, daemon=True).start()

    def download_progress(self, block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            percent = int((downloaded / total_size) * 100)
            percent = min(100, percent)
            self.progress['value'] = percent * 0.5
            self.status_label.config(text=f"Değişiklik paketi indiriliyor: %{percent}", fg=self.text_color)
            self.root.update_idletasks()

    def update_options_txt(self):
        options_path = os.path.join(self.current_dir, "minecraft", "options.txt")
        options_updates = self.remote_data.get("options_updates", {})
        
        if not options_updates or not os.path.exists(options_path):
            return
            
        try:
            self.status_label.config(text="options.txt ayarları optimize ediliyor...")
            self.root.update_idletasks()
            
            current_settings = {}
            with open(options_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if ":" in line:
                        key, val = line.strip().split(":", 1)
                        current_settings[key] = val
            
            for key, val in options_updates.items():
                current_settings[key] = val
                
            with open(options_path, 'w', encoding='utf-8') as f:
                for key, val in current_settings.items():
                    f.write(f"{key}:{val}\n")
                    
        except Exception as e:
            print(f"options.txt güncellenirken hata: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = IncrementalLauncherApp(root)
    root.mainloop()