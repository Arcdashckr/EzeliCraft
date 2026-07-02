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
CURRENT_UPDATER_VERSION = "2.1.0"

class IncrementalLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"EzeliCraft Smart Launcher v{CURRENT_UPDATER_VERSION}")
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
        
        # İlk açılışta klasördeki isim karmaşasını ve eski exe'leri temizleme/düzeltme kontrolü
        if self.sanitize_folder_on_startup():
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

    def sanitize_folder_on_startup(self):
        current_exe = sys.executable
        if not current_exe.endswith(".exe"):
            return True
            
        current_exe_name = os.path.basename(current_exe)
        final_exe_path = os.path.join(self.current_dir, "Modpack_Guncelleyici_v2.exe")
        
        for old_name in ["Modpack_Guncelleyici_MANUEL.exe", "Modpack_Guncelleyici_OTOMATİK.exe"]:
            old_path = os.path.join(self.current_dir, old_name)
            if os.path.exists(old_path) and current_exe_name != old_name:
                try: os.remove(old_path)
                except: pass

        if "_yeni.exe" in current_exe_name.lower() or "_temp_" in current_exe_name.lower():
            pid = os.getpid()
            ps_script = f"""
            Start-Sleep -Seconds 1
            $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
            if ($proc) {{ $proc | Wait-Process -Timeout 5 }}
            if (Test-Path "{final_exe_path}") {{ Remove-Item "{final_exe_path}" -Force }}
            Rename-Item "{current_exe}" "Modpack_Guncelleyici_v2.exe" -Force
            Start-Process "{final_exe_path}"
            """
            subprocess.Popen(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
            self.root.destroy()
            sys.exit(0)
            return False
            
        return True

    def check_launcher_update_and_load(self):
        try:
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                self.remote_data = json.loads(response.read().decode('utf-8'))
            
            # --- PROGRAMIN KENDİ KENDİNİ GÜNCELLEMESİ (AKILLI DOĞRULAMA) ---
            remote_updater_ver = self.remote_data.get("updater_version", "1.0.0")
            if remote_updater_ver != CURRENT_UPDATER_VERSION:
                self.status_label.config(text=f"Launcher yeni sürüme (v{remote_updater_ver}) yükseltiliyor...", fg=self.accent_color)
                self.root.update_idletasks()
                
                current_exe = sys.executable
                
                if current_exe.endswith(".exe"):
                    import time
                    timestamp = int(time.time())
                    temp_exe_name = f"Modpack_Guncelleyici_temp_{timestamp}.exe"
                    new_exe_path = os.path.join(self.current_dir, temp_exe_name)
                    
                    updater_urls = self.remote_data.get("updater_urls", self.remote_data.get("updater_url"))
                    if isinstance(updater_urls, str):
                        updater_urls = [updater_urls]
                        
                    download_success = False
                    for idx, url in enumerate(updater_urls):
                        try:
                            self.status_label.config(text=f"Launcher indiriliyor (Sunucu {idx+1}/{len(updater_urls)})...")
                            self.root.update_idletasks()
                            
                            opener = urllib.request.build_opener()
                            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                            urllib.request.install_opener(opener)
                            urllib.request.urlretrieve(url, new_exe_path)
                            
                            download_success = True
                            break
                        except Exception as e:
                            print(f"Kaynak {url} hata verdi: {e}")
                            if os.path.exists(new_exe_path): os.remove(new_exe_path)
                    
                    if not download_success:
                        raise Exception("Güncelleyici dosyası hiçbir indirme sunucusundan çekilemedi! Lütfen bir yetkiliye bildirin.")
                    
                    pid = os.getpid()
                    final_exe_name = os.path.join(self.current_dir, "Modpack_Guncelleyici_v2.exe")
                    
                    ps_script = f"""
                    Start-Sleep -Seconds 1
                    $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
                    if ($proc) {{ $proc | Wait-Process -Timeout 5 }}
                    if (Test-Path "{current_exe}") {{ Remove-Item "{current_exe}" -Force }}
                    if (Test-Path "{final_exe_name}") {{ Remove-Item "{final_exe_name}" -Force }}
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
            self.status_label.config(text=f"Değişiklik paketi indiriliyor: %{percent} (Sunucu: {self.current_server_info})", fg=self.text_color)
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

    def perform_incremental_update(self):
        temp_zip_name = "temp_patch.zip"
        zip_path = os.path.join(self.current_dir, temp_zip_name)
        remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
        
        modpack_urls = self.remote_data.get("modpack_urls", self.remote_data.get("modpack_url"))
        if isinstance(modpack_urls, str):
            modpack_urls = [modpack_urls]
            
        try:
            download_success = False
            for idx, url in enumerate(modpack_urls):
                try:
                    self.status_label.config(text=f"Sunucuya bağlanılıyor (Sunucu {idx+1}/{len(modpack_urls)})...")
                    self.current_server_info = f"{idx+1}/{len(modpack_urls)}"
                    self.root.update_idletasks()
                    
                    if os.path.exists(zip_path): os.remove(zip_path)
                    
                    opener = urllib.request.build_opener()
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
                    urllib.request.install_opener(opener)
                    
                    urllib.request.urlretrieve(url, zip_path, reporthook=self.download_progress)
                    
                    # 🔍 [KRİTİK DOĞRULAMA] İndirilen dosya geçerli bir ZIP mi kontrol et
                    if zipfile.is_zipfile(zip_path):
                        download_success = True
                        break # Geçerli bir zip ise döngüyü kır ve devam et
                    else:
                        print(f"Sunucu {url} dosya indirdi fakat dosya geçerli bir ZIP değil (Bozuk/Hatalı)!")
                        if os.path.exists(zip_path): os.remove(zip_path)
                        
                except Exception as e:
                    print(f"Sunucu {url} bağlantı hatası verdi: {e}")
                    if os.path.exists(zip_path): os.remove(zip_path)
            
            # Eğer tüm döngü bittiği halde geçerli bir dosya inmediyse tetiklenecek hata mesajı
            if not download_success:
                raise Exception("Mod paketi hiçbir indirme sunucusundan çekilemedi veya indirilen dosyalar bozuk! Lütfen durumu bir yetkiliye bildirin.")
            
            self.status_label.config(text="Akıllı dosya entegrasyonu yapılıyor...")
            self.progress['value'] = 60
            self.root.update_idletasks()
            
            protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list):
                    if file.endswith('/'):
                        continue
                        
                    parts = file.split('/')
                    if len(parts) > 1 and parts[0] == "minecraft":
                        folder_lower = parts[1].lower()
                        if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                            continue
                    
                    target_path = os.path.join(self.current_dir, file.replace('/', os.sep))
                    target_dir = os.path.dirname(target_path)
                    
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                        
                    with zip_ref.open(file) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    
                    if i % max(1, (total_files // 10)) == 0:
                        percent_extract = int((i / total_files) * 30)
                        self.progress['value'] = 60 + percent_extract
                        self.status_label.config(text=f"Dosyalar güncelleniyor: %{int((i / total_files) * 100)}")
                        self.root.update_idletasks()

            if os.path.exists(zip_path): os.remove(zip_path)

            self.update_options_txt()

            self.status_label.config(text="Eski ve kaldırılan dosyalar temizleniyor...")
            self.progress['value'] = 95
            self.root.update_idletasks()
            
            deleted_files = self.remote_data.get("deleted_files", [])
            for rel_path in deleted_files:
                fixed_path = rel_path
                if fixed_path.startswith(".minecraft/"):
                    fixed_path = fixed_path.replace(".minecraft/", "minecraft/", 1)
                    
                full_del_path = os.path.join(self.current_dir, fixed_path.replace('/', os.sep))
                if os.path.isfile(full_del_path):
                    os.remove(full_del_path)
                elif os.path.isdir(full_del_path):
                    shutil.rmtree(full_del_path)

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