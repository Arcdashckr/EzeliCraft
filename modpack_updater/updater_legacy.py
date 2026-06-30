import os
import sys
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

class ModpackUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Modpack Güncelleyici v1.0")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        if os.path.exists("logo.ico"):
            self.root.iconbitmap("logo.ico")
        
        # Modern Koyu Tema Renk Paleti
        self.bg_color = "#1e1e2e"
        self.card_color = "#252538"
        self.accent_color = "#89b4fa"
        self.text_color = "#cdd6f4"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        
        self.root.configure(bg=self.bg_color)
        
        # Stil Ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TProgressbar", thickness=20, troughcolor=self.card_color, background=self.accent_color)
        
        self.create_widgets()
        self.check_environment()

    def create_widgets(self):
        # Başlık
        title_label = tk.Label(self.root, text="Modpack Güncelleyici", font=("Helvetica", 16, "bold"), bg=self.bg_color, fg=self.accent_color)
        title_label.pack(pady=15)
        
        # Bilgi Kutusu
        self.card = tk.Frame(self.root, bg=self.card_color, bd=0, highlightbackground=self.accent_color, highlightthickness=1)
        self.card.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.status_label = tk.Label(self.card, text="Sistem kontrol ediliyor...", font=("Helvetica", 10), bg=self.card_color, fg=self.text_color, wraplength=440, justify="center")
        self.status_label.pack(expand=True, pady=10, padx=10)
        
        # İlerleme Çubuğu
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=440, mode="determinate", style="TProgressbar")
        
        # Güncelle Butonu (Bu satır tek başına durmalı)
        self.btn_update = tk.Button(self.root, text="Güncellemeyi Başlat", font=("Helvetica", 11, "bold"), bg=self.accent_color, fg=self.bg_color, activebackground="#74c7ec", activeforeground=self.bg_color, bd=0, padx=10, pady=5, command=self.start_update_thread, state="disabled")
        
        # Bu satır bir alt satırda ve başında 8 boşluk (veya 2 tab) olacak şekilde durmalı
        self.btn_update.pack(pady=15)
        
    def check_environment(self):
        self.current_dir = os.getcwd()
        
        # Klasördeki .zip dosyalarını bul
        self.zip_files = [f for f in os.listdir(self.current_dir) if f.endswith('.zip')]
        
        if not self.zip_files:
            self.status_label.config(text="HATA: Klasörde güncellenecek .zip paketi bulunamadı!\n\nLütfen indirdiğiniz güncel .zip dosyasını ve bu uygulamayı modpackın klasörünün içine (.minecraft içine) taşıyın ve programı yeniden başlatın.", fg=self.error_color)
            return
            
        self.target_zip = self.zip_files[0]
        self.status_label.config(text=f"Güncelleme paketi algılandı:\n{self.target_zip}\n\nButona tıkladığınızda dünyalarınız, harita işaretleriniz (waypoint) ve ekran görüntüleriniz KORUNARAK paketiniz güncellenecektir.")
        self.btn_update.config(state="normal")

    def start_update_thread(self):
        self.btn_update.config(state="disabled")
        self.progress.pack(pady=5)
        # GUI donmasın diye işlemi arka planda çalıştırıyoruz
        Thread(target=self.perform_update, daemon=True).start()

    def perform_update(self):
        try:
            zip_path = os.path.join(self.current_dir, self.target_zip)
            
            # Tamamen korunacak klasör adları (küçük harfle kontrol edilir)
            protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
            
            self.status_label.config(text="Paket açılıyor ve analiz ediliyor...", fg=self.text_color)
            self.progress['value'] = 10
            self.root.update_idletasks()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # 1. Aşama: Eski mod/config çakışmalarını önlemek için zip içinde gelen klasörleri (korunanlar hariç) temizleme
                top_level_dirs_in_zip = set()
                for file in file_list:
                    parts = file.split('/')
                    if parts[0]:
                        top_level_dirs_in_zip.add(parts[0])
                
                self.status_label.config(text="Eski dosyalar temizleniyor...", fg=self.text_color)
                for folder in top_level_dirs_in_zip:
                    folder_lower = folder.lower()
                    
                    # Koruma kriteri check
                    is_protected = False
                    if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                        is_protected = True
                        
                    if not is_protected:
                        target_folder_path = os.path.join(self.current_dir, folder)
                        if os.path.isdir(target_folder_path):
                            shutil.rmtree(target_folder_path) # Eski mods, config vb. klasörleri siler.
                
                self.progress['value'] = 30
                self.root.update_idletasks()
                
                # 2. Aşama: Dosyaları Üzerine Yazma (Extract)
                for i, file in enumerate(file_list):
                    parts = file.split('/')
                    if parts[0]:
                        folder_lower = parts[0].lower()
                        # Zip içinde yanlışlıkla korunan klasör verisi varsa çıkartma, atla.
                        if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                            continue
                    
                    # Dosyayı o anki dizine çıkartır (options.txt buraya dahildir, otomatik üstüne yazar)
                    zip_ref.extract(file, self.current_dir)
                    
                    if i % max(1, (total_files // 10)) == 0:
                        percent = 30 + int((i / total_files) * 60)
                        self.progress['value'] = percent
                        self.status_label.config(text=f"Dosyalar yükleniyor: %{int((i / total_files) * 100)}")
                        self.root.update_idletasks()

            self.progress['value'] = 100
            self.status_label.config(text="Güncelleme BAŞARIYLA Tamamlandı!\n\nBu pencereyi kapatıp Prism Launcher üzerinden oyuna girebilirsiniz.", fg=self.success_color)
            messagebox.showinfo("Başarılı", "Mod paketiniz başarıyla güncellendi!\nKeyifli oyunlar dileriz.")
            
        except Exception as e:
            self.status_label.config(text=f"HATA OLUŞTU:\n{str(e)}", fg=self.error_color)
            messagebox.showerror("Hata", f"Güncelleme yapılırken bir hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModpackUpdaterApp(root)
    root.mainloop()