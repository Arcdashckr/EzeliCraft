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
CURRENT_UPDATER_VERSION = "2.0.1"  # Bu sürüm numarasını güncel tutun

class IncrementalLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EzeliCraft Smart Launcher v4.1")
        self.root.geometry("550x450")
        self.root.resizable(False, False)
        
        # Modern Koyu Tema
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
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                self.remote_data = json.loads(response.read().decode('utf-8'))
            
            # Kendi Kendini Güncelleme (Self-Update)
            remote_updater_ver = self.remote_data.get("updater_version", "1.0.0")
            if remote_updater_ver != CURRENT_UPDATER_VERSION:
                self.status_label.config(text="Launcher güncelleniyor, lütfen bekleyin...", fg=self.accent_color)
                updater_url = self.remote_data.get("updater_url")
                current_exe = sys.argv[0]
                new_exe = current_exe.replace(".exe", "_yeni.exe")
                if not new_exe.endswith("_yeni.exe"): new_exe = "Modpack_Guncelleyici_yeni.exe"
                
                urllib.request.urlretrieve(updater_url, new_exe)
                batch_cmd = f'timeout /t 1 && del "{current_exe}" && move "{new_exe}" "{current_exe}" && start "" "{current_exe}" && del "%~f0"'
                subprocess.Popen(f'cmd.exe /c {batch_cmd}', shell=True)
                self.root.quit()
                return

            # Sürüm Karşılaştırma
            local_version_path = os.path.join(self.current_dir, "local_version.json")
            local_ver = "0.0.0"
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r') as f:
                        local_ver = json.load(f).get("version", "0.0.0")
                except: pass
                
            remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
            
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

    def perform_incremental_update(self):
        temp_zip_name = "temp_patch.zip"
        zip_path = os.path.join(self.current_dir, temp_zip_name)
        modpack_url = self.remote_data.get("remote_url" if "remote_url" in self.remote_data else "modpack_url")
        remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
        
        try:
            self.status_label.config(text="Sunucuya bağlanılıyor...")
            if os.path.exists(zip_path): os.remove(zip_path)
            urllib.request.urlretrieve(modpack_url, zip_path, reporthook=self.download_progress)
            
            self.status_label.config(text="Akıllı dosya entegrasyonu yapılıyor...")
            self.progress['value'] = 60
            self.root.update_idletasks()
            
            protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list):
                    parts = file.split('/')
                    # Yapı artık 'minecraft' klasörü ile başlıyor
                    if len(parts) > 1 and parts[0] == "minecraft":
                        folder_lower = parts[1].lower()
                        # Eğer korunan bir klasörse ayıklama, pas geç
                        if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                            continue
                    
                    # Dosyayı hedef klasöre çıkart
                    zip_ref.extract(file, self.current_dir)
                    
                    if i % max(1, (total_files // 10)) == 0:
                        percent_extract = int((i / total_files) * 30)
                        self.progress['value'] = 60 + percent_extract
                        self.status_label.config(text=f"Dosyalar güncelleniyor: %{int((i / total_files) * 100)}")
                        self.root.update_idletasks()

            if os.path.exists(zip_path): os.remove(zip_path)

            # Eski ve kaldırılan dosyaları temizleme aşaması
            self.status_label.config(text="Eski ve kaldırılan dosyalar temizleniyor...")
            self.progress['value'] = 95
            self.root.update_idletasks()
            
            deleted_files = self.remote_data.get("deleted_files", [])
            for rel_path in deleted_files:
                # Eğer silinecek dosya eski koddan dolayı .minecraft/ ile kalmışsa otomatik minecraft/ yap
                fixed_path = rel_path
                if fixed_path.startswith(".minecraft/"):
                    fixed_path = fixed_path.replace(".minecraft/", "minecraft/", 1)
                    
                full_del_path = os.path.join(self.current_dir, fixed_path.replace('/', os.sep))
                if os.path.isfile(full_del_path):
                    os.remove(full_del_path)
                elif os.path.isdir(full_del_path):
                    shutil.rmtree(full_del_path)

            # Sürümü yerel dosyaya yaz
            local_version_path = os.path.join(self.current_dir, "local_version.json")
            with open(local_version_path, 'w') as f:
                json.dump({"version": remote_modpack_ver}, f)

            self.progress['value'] = 100
            self.status_label.config(text=f"Güncelleme Tamamlandı! Mevcut Sürüm: v{remote_modpack_ver}", fg=self.success_color)
            self.btn_update.config(text="Sürüm Güncel", bg="#a6e3a1", state="disabled")
            messagebox.showinfo("Başarılı", f"Mod paketiniz v{remote_modpack_ver} sürümüne başarıyla güncellendi!")
            
        except Exception as e:
            self.status_label.config(text=f"Hata oluştu:\n{str(e)}", fg=self.error_color)
            messagebox.showerror("Hata", f"İşlem başarısız:\n{str(e)}")
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            self.btn_update.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = IncrementalLauncherApp(root)
    root.mainloop()