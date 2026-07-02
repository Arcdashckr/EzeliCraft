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

# PROGRAMIN KENDİ SÜRÜMÜ (GitHub'daki updater_version ile kıyaslanır)
CURRENT_UPDATER_VERSION = "2.0.0"

class AdvancedLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EzeliCraft Advanced Launcher v3.5")
        self.root.geometry("550x450")
        self.root.resizable(False, False)
        
        # Modern Koyu Tema Renkleri
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
        
        # Program açılır açılmaz kendi güncellemesini kontrol etmek için arka plan thread'i başlat
        self.create_widgets()
        Thread(target=self.check_launcher_update_and_load, daemon=True).start()

    def create_widgets(self):
        # Üst Başlık ve Sürüm Bilgisi
        self.title_frame = tk.Frame(self.root, bg=self.bg_color)
        self.title_frame.pack(pady=10, padx=20, fill="x")
        
        self.title_label = tk.Label(self.title_frame, text="EzeliCraft Modpack Güncelleyici", font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.accent_color)
        self.title_label.pack(side="left")
        
        self.version_label = tk.Label(self.title_frame, text=f"Launcher v{CURRENT_UPDATER_VERSION}", font=("Helvetica", 9), bg=self.bg_color, fg="#6c7086")
        self.version_label.pack(side="right", pady=4)
        
        # Durum ve Sürüm Karşılaştırma Kartı
        self.status_card = tk.Frame(self.root, bg=self.card_color, bd=0, highlightbackground="#45475a", highlightthickness=1)
        self.status_card.pack(pady=5, padx=20, fill="x")
        
        self.status_label = tk.Label(self.status_card, text="Sunucuya bağlanılıyor, güncellemeler denetleniyor...", font=("Helvetica", 10, "bold"), bg=self.card_color, fg=self.text_color, justify="center")
        self.status_label.pack(pady=12, padx=10)
        
        # Değişiklik Notları (Changelog) Başlığı
        changelog_title = tk.Label(self.root, text="Son Yapılan Değişiklikler ve Güncelleme Notları:", font=("Helvetica", 10, "bold"), bg=self.bg_color, fg=self.text_color)
        changelog_title.pack(anchor="w", padx=25, pady=(10, 2))
        
        # Değişiklik Notları Listbox (Metin Alanı)
        self.changelog_box = tk.Text(self.root, font=("Helvetica", 9), bg=self.card_color, fg=self.text_color, bd=0, highlightbackground="#45475a", highlightthickness=1, wrap="word", height=8)
        self.changelog_box.pack(pady=5, padx=20, fill="x")
        self.changelog_box.insert("1.0", " Güncelleme notları yükleniyor...")
        self.changelog_box.config(state="disabled")
        
        # İlerleme Çubuğu
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=510, mode="determinate", style="TProgressbar")
        self.progress.pack(pady=10)
        
        # Güncelle Butonu
        self.btn_update = tk.Button(self.root, text="Güncellemeyi Denetle", font=("Helvetica", 11, "bold"), bg="#45475a", fg=self.bg_color, activebackground=self.accent_color, activeforeground=self.bg_color, bd=0, padx=25, pady=8, state="disabled")
        self.btn_update.pack(pady=10)

    def check_launcher_update_and_load(self):
        try:
            # 1. ADIM: JSON dosyasını oku
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                self.remote_data = json.loads(response.read().decode('utf-8'))
            
            # --- SELF-UPDATE (PROGRAMIN KENDİNİ GÜNCELLEMESİ) ---
            remote_updater_ver = self.remote_data.get("updater_version", "1.0.0")
            if remote_updater_ver != CURRENT_UPDATER_VERSION:
                self.status_label.config(text="Launcher için yeni bir güncelleme var! Kendi kendini güncelliyor...", fg=self.accent_color)
                updater_url = self.remote_data.get("updater_url")
                
                # Yeni exe'yi geçici isimle indir
                current_exe = sys.argv[0]
                new_exe = current_exe.replace(".exe", "_yeni.exe")
                if not new_exe.endswith("_yeni.exe"): 
                    new_exe = "Modpack_Guncelleyici_yeni.exe"
                
                urllib.request.urlretrieve(updater_url, new_exe)
                
                # Eski exe'yi silip yenisini başlatan bir CMD betiği tetikle ve uygulamayı kapat
                batch_cmd = f'timeout /t 1 && del "{current_exe}" && move "{new_exe}" "{current_exe}" && start "" "{current_exe}" && del "%~f0"'
                subprocess.Popen(f'cmd.exe /c {batch_cmd}', shell=True)
                self.root.quit()
                return

            # --- SÜRÜM KONTROLÜ VE CHANGELOG YÜKLEME ---
            # Yerel sürümü oku (yoksa 0.0.0 kabul et)
            local_version_path = os.path.join(self.current_dir, "local_version.json")
            local_ver = "0.0.0"
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r') as f:
                        local_ver = json.load(f).get("version", "0.0.0")
                except: pass
                
            remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
            
            # Güncelleme notlarını yazdır
            self.changelog_box.config(state="normal")
            self.changelog_box.delete("1.0", tk.END)
            changelog_lines = self.remote_data.get("changelog", ["• Herhangi bir değişiklik notu belirtilmedi."])
            for line in changelog_lines:
                self.changelog_box.insert(tk.END, f"{line}\n")
            self.changelog_box.config(state="disabled")
            
            # Sürümleri kıyasla ve butonu ayarla
            if local_ver == remote_modpack_ver:
                self.status_label.config(text=f"Zaten En Güncel Sürümdesiniz! (v{local_ver})\nOynamaya hazırsınız.", fg=self.success_color)
                self.btn_update.config(text="Tekrar Kur / Onar", bg="#a6e3a1", state="normal", command=self.start_update_thread)
            else:
                self.status_label.config(text=f"Yeni Güncelleme Mevcut!\nYerel Sürüm: v{local_ver} -> Güncel Sürüm: v{remote_modpack_ver}", fg=self.error_color)
                self.btn_update.config(text="Şimdi Güncelle", bg=self.accent_color, state="normal", command=self.start_update_thread)
                
        except Exception as e:
            self.status_label.config(text=f"Veriler alınırken hata oluştu:\n{str(e)}", fg=self.error_color)

    def start_update_thread(self):
        self.btn_update.config(state="disabled")
        Thread(target=self.perform_full_update, daemon=True).start()

    def download_progress(self, block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            percent = int((downloaded / total_size) * 100)
            percent = min(100, percent)
            self.progress['value'] = percent * 0.5
            self.status_label.config(text=f"Mod paketi indiriliyor: %{percent}", fg=self.text_color)
            self.root.update_idletasks()

    def perform_full_update(self):
        temp_zip_name = "temp_modpack.zip"
        zip_path = os.path.join(self.current_dir, temp_zip_name)
        modpack_url = self.remote_data.get("modpack_url")
        remote_modpack_ver = self.remote_data.get("modpack_version", "1.0.0")
        
        try:
            self.status_label.config(text="Dosya indirme sunucusuna bağlanılıyor...")
            self.root.update_idletasks()
            
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
            urllib.request.urlretrieve(modpack_url, zip_path, reporthook=self.download_progress)
            
            protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
            self.status_label.config(text="Paket açılıyor ve çakışan dosyalar temizleniyor...")
            self.progress['value'] = 55
            self.root.update_idletasks()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                top_level_dirs_in_zip = set()
                for file in file_list:
                    parts = file.split('/')
                    if parts[0]:
                        top_level_dirs_in_zip.add(parts[0])
                
                for folder in top_level_dirs_in_zip:
                    folder_lower = folder.lower()
                    is_protected = False
                    if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                        is_protected = True
                        
                    if not is_protected:
                        target_folder_path = os.path.join(self.current_dir, folder)
                        if os.path.isdir(target_folder_path):
                            shutil.rmtree(target_folder_path)
                
                self.progress['value'] = 70
                self.root.update_idletasks()
                
                for i, file in enumerate(file_list):
                    parts = file.split('/')
                    if parts[0]:
                        folder_lower = parts[0].lower()
                        if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                            continue
                    
                    zip_ref.extract(file, self.current_dir)
                    
                    if i % max(1, (total_files // 10)) == 0:
                        percent_extract = int((i / total_files) * 30)
                        self.progress['value'] = 70 + percent_extract
                        self.status_label.config(text=f"Yeni dosyalar yükleniyor: %{int((i / total_files) * 100)}")
                        self.root.update_idletasks()

            if os.path.exists(zip_path):
                os.remove(zip_path)

            # --- BAŞARILI KURULUM SONRASI SÜRÜM DOSYASINI YAZDIRMA ---
            local_version_path = os.path.join(self.current_dir, "local_version.json")
            with open(local_version_path, 'w') as f:
                json.dump({"version": remote_modpack_ver}, f)

            self.progress['value'] = 100
            self.status_label.config(text=f"Güncelleme Başarıyla Tamamlandı! Mevcut Sürüm: v{remote_modpack_ver}", fg=self.success_color)
            self.btn_update.config(text="Sürüm Güncel", bg="#a6e3a1", state="disabled")
            messagebox.showinfo("Başarılı", f"Mod paketiniz v{remote_modpack_ver} sürümüne başarıyla güncellendi!")
            
        except Exception as e:
            self.status_label.config(text=f"Güncelleme sırasında hata oluştu:\n{str(e)}", fg=self.error_color)
            messagebox.showerror("Hata", f"İşlem başarısız:\n{str(e)}")
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            self.btn_update.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedLauncherApp(root)
    root.mainloop()