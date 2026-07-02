import os
import sys
import zipfile
import shutil
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

# ⚠️ BURAYA DOSYANIN DOĞRUDAN (DIRECT) İNDİRME LİNKİNİ YAPIŞTIR!
MODPACK_URL = "https://download1503.mediafire.com/8rvjgscoyalgXmnWmxuQBmJiTdZxyrSEveu19Yvg5aYMlbQHgt5-DMYEhbfroUg-2YdcVTn2V71OOB3UO4QybotDW-5xZplV-xezSAn2U35Q-U09_-8QqEfitvXVB1TfdbPgur2abHMmjC1M_fh8lNeJhD57jrlz3JjrNo20Iis/qvu8q2d19xsygph/EC+Ascend+Modpack+v2.3.1.zip" 

class AutoModpackUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EzeliCraft Otomatik Güncelleyici v2.0")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Modern Koyu Tema Renk Paleti
        self.bg_color = "#1e1e2e"
        self.card_color = "#252538"
        self.accent_color = "#a6e3a1" # İndirme odaklı yeşil/mavi tonu
        self.text_color = "#cdd6f4"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        
        self.root.configure(bg=self.bg_color)
        
        # Stil Ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TProgressbar", thickness=20, troughcolor=self.card_color, background="#89b4fa")
        
        self.create_widgets()
        self.current_dir = os.getcwd()

    def create_widgets(self):
        # Başlık
        title_label = tk.Label(self.root, text="EzeliCraft Modpack Güncelleyici", font=("Helvetica", 15, "bold"), bg=self.bg_color, fg="#89b4fa")
        title_label.pack(pady=15)
        
        # Bilgi Kutusu
        self.card = tk.Frame(self.root, bg=self.card_color, bd=0, highlightbackground="#89b4fa", highlightthickness=1)
        self.card.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.status_label = tk.Label(self.card, text="Butona tıkladığınızda en güncel mod paketi internetten otomatik olarak indirilecek ve kurulacaktır.\n\nDünyalarınız, waypointleriniz ve ekran görüntüleriniz güvendedir.", font=("Helvetica", 10), bg=self.card_color, fg=self.text_color, wraplength=440, justify="center")
        self.status_label.pack(expand=True, pady=10, padx=10)
        
        # İlerleme Çubuğu
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=440, mode="determinate", style="TProgressbar")
        self.progress.pack(pady=5)
        
        # Güncelle Butonu
        self.btn_update = tk.Button(self.root, text="İndir ve Güncelle", font=("Helvetica", 11, "bold"), bg="#89b4fa", fg=self.bg_color, activebackground="#74c7ec", activeforeground=self.bg_color, bd=0, padx=20, pady=8, command=self.start_update_thread)
        self.btn_update.pack(pady=15)

    def start_update_thread(self):
        self.btn_update.config(state="disabled")
        Thread(target=self.perform_full_update, daemon=True).start()

    def download_progress(self, block_num, block_size, total_size):
        # İndirme yüzdesini hesaplar ve progress bar'ı günceller
        if total_size > 0:
            downloaded = block_num * block_size
            percent = int((downloaded / total_size) * 100)
            percent = min(100, percent) # 100'ü geçmesini engelle
            self.progress['value'] = percent * 0.5 # İlk %50'lik kısmı indirmeye ayırdık
            self.status_label.config(text=f"Mod paketi indiriliyor: %{percent}")
            self.root.update_idletasks()

    def perform_full_update(self):
        temp_zip_name = "temp_modpack.zip"
        zip_path = os.path.join(self.current_dir, temp_zip_name)
        
        try:
            # 1. AŞAMA: İndirme işlemi
            self.status_label.config(text="Sunucuya bağlanılıyor, lütfen bekleyin...")
            self.root.update_idletasks()
            
            # Eski geçici dosya kalmışsa sil
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
            # Dosyayı indir
            urllib.request.urlretrieve(MODPACK_URL, zip_path, reporthook=self.download_progress)
            
            # 2. AŞAMA: Kurulum/Ayıklama İşlemi
            protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
            
            self.status_label.config(text="Paket açılıyor ve analiz ediliyor...")
            self.progress['value'] = 55
            self.root.update_idletasks()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # Temizlik aşaması
                top_level_dirs_in_zip = set()
                for file in file_list:
                    parts = file.split('/')
                    if parts[0]:
                        top_level_dirs_in_zip.add(parts[0])
                
                self.status_label.config(text="Eski modlar ve çakışan dosyalar temizleniyor...")
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
                
                # Dosyaları çıkartma aşaması
                for i, file in enumerate(file_list):
                    parts = file.split('/')
                    if parts[0]:
                        folder_lower = parts[0].lower()
                        if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                            continue
                    
                    zip_ref.extract(file, self.current_dir)
                    
                    if i % max(1, (total_files // 10)) == 0:
                        percent_extract = int((i / total_files) * 30) # Kalan %30'u çıkartmaya ayırdık
                        self.progress['value'] = 70 + percent_extract
                        self.status_label.config(text=f"Yeni dosyalar yükleniyor: %{int((i / total_files) * 100)}")
                        self.root.update_idletasks()

            # Geçici dosyayı temizle
            if os.path.exists(zip_path):
                os.remove(zip_path)

            self.progress['value'] = 100
            self.status_label.config(text="Güncelleme BAŞARIYLA Tamamlandı!\n\nArtık bu pencereyi kapatıp oyuna giriş yapabilirsiniz.", fg=self.success_color)
            messagebox.showinfo("Başarılı", "Mod paketiniz otomatik olarak indirildi ve güncellendi!\nİyi oyunlar dileriz.")
            
        except Exception as e:
            self.status_label.config(text=f"HATA OLUŞTU:\n{str(e)}", fg=self.error_color)
            messagebox.showerror("Hata", f"Güncelleme indirilirken veya kurulurken bir hata oluştu:\n{str(e)}")
            # Hata durumunda geçici zip kalırsa temizle
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
        finally:
            self.btn_update.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoModpackUpdaterApp(root)
    root.mainloop()