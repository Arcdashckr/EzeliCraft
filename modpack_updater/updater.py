import os
import re
import sys
import zipfile
import shutil
import urllib.request
import json
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from threading import Thread

# ⚠️ GITHUB'DAKİ version.json DOSYASININ "RAW" LİNKİ
JSON_URL = "https://raw.githubusercontent.com/Arcdashckr/EzeliCraft/main/modpack_updater/version.json"
CURRENT_UPDATER_VERSION = "2.2.1"
LOG_FILE_NAME = "guncelleyici.log"


def parse_version(version_value):
    match = re.search(r'(\d+)', str(version_value or '0'))
    if not match:
        return (0,)
    return tuple(int(part) for part in re.findall(r'\d+', str(version_value or '0')))


def should_require_launcher_update(current_version, remote_version):
    if not remote_version:
        return False
    return parse_version(remote_version) > parse_version(current_version)


def collect_pending_updates(local_version, remote_data):
    local_version = str(local_version or '0.0.0')

    chain = remote_data.get('update_chain') or remote_data.get('updates') or []
    if isinstance(chain, list) and chain:
        pending = []
        current_version = local_version

        if local_version in {'0.0.0', 'v0.0.0', '', 'None'}:
            bootstrap_version = remote_data.get('bootstrap_version') or remote_data.get('bootstrap_target_version')
            if bootstrap_version:
                current_version = str(bootstrap_version)
                pending.append({
                    'from_version': local_version,
                    'to_version': str(bootstrap_version),
                    'modpack_url': remote_data.get('modpack_url') or remote_data.get('modpack_urls'),
                    'modpack_urls': remote_data.get('modpack_urls') or remote_data.get('modpack_url'),
                    'changelog': remote_data.get('changelog', []),
                    'deleted_files': remote_data.get('deleted_files', []),
                    'options_updates': remote_data.get('options_updates', {})
                })

        while True:
            next_step = None
            for step in chain:
                if str(step.get('from_version', '')).strip() == current_version:
                    next_step = step
                    break
            if not next_step:
                break
            pending.append(next_step)
            current_version = str(next_step.get('to_version', current_version))

        if pending:
            return pending

    remote_modpack_ver = remote_data.get('modpack_version')
    if remote_modpack_ver and str(local_version) != str(remote_modpack_ver):
        return [{
            'from_version': local_version,
            'to_version': str(remote_modpack_ver),
            'modpack_url': remote_data.get('modpack_url') or remote_data.get('modpack_urls'),
            'modpack_urls': remote_data.get('modpack_urls') or remote_data.get('modpack_url'),
            'changelog': remote_data.get('changelog', []),
            'deleted_files': remote_data.get('deleted_files', []),
            'options_updates': remote_data.get('options_updates', {})
        }]

    return []


class IncrementalLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"EzeliCraft Smart Launcher v{CURRENT_UPDATER_VERSION}")
        self.root.geometry("760x650")
        self.root.resizable(False, False)

        self.bg_color = "#111827"
        self.card_color = "#1f2937"
        self.accent_color = "#60a5fa"
        self.text_color = "#f3f4f6"
        self.success_color = "#34d399"
        self.error_color = "#f87171"
        self.muted_color = "#9ca3af"

        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TProgressbar', thickness=16, troughcolor='#374151', background=self.accent_color)

        if getattr(sys, 'frozen', False):
            self.current_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.current_dir = os.path.dirname(os.path.abspath(__file__))

        self.remote_data = {}
        self.skipped_files = []
        self.current_server_info = ''
        self.log_file = os.path.join(self.current_dir, LOG_FILE_NAME)
        self.launcher_update_state_file = os.path.join(self.current_dir, 'launcher_update_state.json')
        self.changelog_expanded = False

        self.create_widgets()
        self.log('Launcher başlatıldı')

        if self.sanitize_folder_on_startup():
            Thread(target=self.check_launcher_update_and_load, daemon=True).start()

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{timestamp}] {message}'
        with open(self.log_file, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
        print(line)

    def load_launcher_update_state(self):
        if not os.path.exists(self.launcher_update_state_file):
            return {}
        try:
            with open(self.launcher_update_state_file, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return {}

    def save_launcher_update_state(self, state):
        try:
            with open(self.launcher_update_state_file, 'w', encoding='utf-8') as fh:
                json.dump(state, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f'Launcher güncelleme durumu kaydedilemedi: {e}')

    def should_prompt_for_launcher_update(self, remote_version):
        if not should_require_launcher_update(CURRENT_UPDATER_VERSION, remote_version):
            return False
        state = self.load_launcher_update_state()
        if state.get('dismissed_version') == str(remote_version):
            return False
        if state.get('accepted_version') == str(remote_version):
            return False
        return True

    def remember_launcher_update_decision(self, remote_version, accepted):
        state = self.load_launcher_update_state()
        state['last_prompted_version'] = str(remote_version)
        if accepted:
            state['accepted_version'] = str(remote_version)
        else:
            state['dismissed_version'] = str(remote_version)
        self.save_launcher_update_state(state)

    def prompt_for_launcher_update(self, remote_updater_version):
        self.root.after(0, lambda: self._prompt_for_launcher_update(remote_updater_version))

    def _prompt_for_launcher_update(self, remote_updater_version):
        if not self.root.winfo_exists():
            return
        decision = messagebox.askyesno(
            'Yeni güncelleyici sürümü bulundu',
            f'Yeni bir güncelleyici sürümü mevcut: v{CURRENT_UPDATER_VERSION} -> v{remote_updater_version}\n\n'
            'Yeni sürümü indirip kurmak ister misiniz?\n'
            'Hayır seçerseniz program mevcut sürümle çalışmaya devam eder.'
        )
        self.remember_launcher_update_decision(remote_updater_version, bool(decision))
        if decision:
            self.install_launcher_update(remote_updater_version)
        else:
            self.status_label.config(
                text=f'Yeni güncelleyici sürümü bulundu (v{remote_updater_version}), mevcut sürümle devam ediliyor.',
                fg=self.accent_color
            )

    def install_launcher_update(self, remote_updater_version):
        self.status_label.config(text=f'Yeni güncelleyici sürümü indiriliyor (v{remote_updater_version})...', fg=self.accent_color)
        self.root.update_idletasks()

        current_exe = sys.executable
        if not current_exe.endswith('.exe'):
            messagebox.showinfo('Bilgi', 'Bu çalışma ortamında güncelleyici kendini güncelleyemez; lütfen paketlenmiş .exe sürümünü kullanın.')
            self.status_label.config(text='Güncelleyici güncelleme işlemi için .exe ortamı bekliyor.', fg=self.muted_color)
            return

        import time
        timestamp = int(time.time())
        temp_exe_name = f'Modpack_Guncelleyici_temp_{timestamp}.exe'
        new_exe_path = os.path.join(self.current_dir, temp_exe_name)

        updater_urls = self.remote_data.get('updater_urls', self.remote_data.get('updater_url'))
        if isinstance(updater_urls, str):
            updater_urls = [updater_urls]

        download_success = False
        for idx, url in enumerate(updater_urls):
            try:
                self.status_label.config(text=f'Launcher indiriliyor (Sunucu {idx + 1}/{len(updater_urls)})...')
                self.root.update_idletasks()

                opener = urllib.request.build_opener()
                opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(url, new_exe_path)
                download_success = True
                break
            except Exception as e:
                self.log(f'Launcher indirme hatası: {url} -> {e}')
                if os.path.exists(new_exe_path):
                    os.remove(new_exe_path)

        if not download_success:
            messagebox.showerror('Hata', 'Güncelleyici dosyası hiçbir indirme sunucusundan çekilemedi!')
            self.status_label.config(text='Güncelleyici indirme başarısız oldu.', fg=self.error_color)
            return

        pid = os.getpid()
        final_exe_name = os.path.join(self.current_dir, 'Modpack_Guncelleyici_v2.exe')
        ps_script = f'''
        Start-Sleep -Seconds 1
        $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
        if ($proc) {{ $proc | Wait-Process -Timeout 5 }}
        if (Test-Path "{current_exe}") {{ Remove-Item "{current_exe}" -Force }}
        if (Test-Path "{final_exe_name}") {{ Remove-Item "{final_exe_name}" -Force }}
        Rename-Item "{new_exe_path}" "Modpack_Guncelleyici_v2.exe" -Force
        Start-Process "{final_exe_name}"
        '''
        subprocess.Popen(['powershell', '-Command', ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
        self.root.destroy()
        sys.exit(0)

    def create_widgets(self):
        self.title_frame = tk.Frame(self.root, bg=self.bg_color)
        self.title_frame.pack(pady=(16, 10), padx=24, fill='x')

        self.title_label = tk.Label(self.title_frame, text='EzeliCraft Akıllı Güncelleyici', font=('Segoe UI', 16, 'bold'), bg=self.bg_color, fg=self.accent_color)
        self.title_label.pack(side='left')

        self.launcher_version_label = tk.Label(self.title_frame, text=f'Launcher v{CURRENT_UPDATER_VERSION}', font=('Segoe UI', 9), bg=self.bg_color, fg=self.muted_color)
        self.launcher_version_label.pack(side='right', pady=4)

        self.info_card = tk.Frame(self.root, bg=self.card_color, bd=0, highlightbackground='#374151', highlightthickness=1)
        self.info_card.pack(pady=(0, 10), padx=24, fill='x')

        self.status_label = tk.Label(self.info_card, text='Bağlantı kuruluyor, sürüm denetleniyor...', font=('Segoe UI', 10, 'bold'), bg=self.card_color, fg=self.text_color, justify='center')
        self.status_label.pack(pady=(12, 8), padx=10)

        self.info_text = tk.Label(self.info_card, text='Bulunan sürüm: —\nSon sürüm: —\nBu güncelleme birden fazla adımda ilerleyebilir.', font=('Segoe UI', 9), bg=self.card_color, fg=self.muted_color, justify='left')
        self.info_text.pack(pady=(0, 10), padx=12, anchor='w')

        self.changelog_frame = tk.Frame(self.root, bg=self.bg_color)
        self.changelog_frame.pack(pady=(6, 8), padx=24, fill='x')

        self.changelog_header = tk.Frame(self.changelog_frame, bg=self.bg_color)
        self.changelog_header.pack(fill='x')

        self.changelog_title = tk.Label(self.changelog_header, text='Değişiklik Notları', font=('Segoe UI', 10, 'bold'), bg=self.bg_color, fg=self.text_color)
        self.changelog_title.pack(side='left')

        self.toggle_changelog_btn = tk.Button(self.changelog_header, text='Genişlet', command=self.toggle_changelog, font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=10, pady=4)
        self.toggle_changelog_btn.pack(side='right')

        self.changelog_container = tk.Frame(self.changelog_frame, bg=self.card_color, bd=0, highlightbackground='#374151', highlightthickness=1)
        self.changelog_container.pack(fill='x', pady=(6, 0))

        self.changelog_box = tk.Text(self.changelog_container, height=8, font=('Segoe UI', 9), bg=self.card_color, fg=self.text_color, bd=0, wrap='word')
        self.changelog_box.pack(side='left', fill='both', expand=True, padx=(0, 0), pady=0)

        self.changelog_scroll = ttk.Scrollbar(self.changelog_container, orient='vertical', command=self.changelog_box.yview)
        self.changelog_scroll.pack(side='right', fill='y')
        self.changelog_box.configure(yscrollcommand=self.changelog_scroll.set)
        self.changelog_box.insert('1.0', ' Güncelleme notları yükleniyor...')
        self.changelog_box.config(state='disabled')

        self.detail_label = tk.Label(self.root, text='İşlem detayı: Bekleniyor', font=('Segoe UI', 9), bg=self.bg_color, fg=self.muted_color, justify='left')
        self.detail_label.pack(pady=(10, 6), padx=24, anchor='w')

        self.progress = ttk.Progressbar(self.root, orient='horizontal', length=700, mode='determinate', style='TProgressbar')
        self.progress.pack(pady=(4, 10), padx=24, fill='x')

        self.btn_update = tk.Button(self.root, text='Güncellemeyi Denetle', font=('Segoe UI', 10, 'bold'), bg=self.accent_color, fg='#111827', activebackground='#93c5fd', activeforeground='#111827', bd=0, padx=22, pady=8, state='disabled')
        self.btn_update.pack(pady=(4, 20))

        # Additional action buttons
        self.actions_frame = tk.Frame(self.root, bg=self.bg_color)
        self.actions_frame.pack(pady=(0, 12))

        self.btn_fix_resourcepacks = tk.Button(self.actions_frame, text='ResourcePack Sırasını Düzelt', font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=12, pady=6, state='disabled', command=self.fix_resourcepack_order)
        self.btn_fix_resourcepacks.pack(side='left', padx=(0, 8))

        self.btn_versions = tk.Button(self.actions_frame, text='Sürüm Notları', font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=12, pady=6, state='disabled', command=self.open_version_changelogs_window)
        self.btn_versions.pack(side='left', padx=(0, 8))

        self.btn_repair = tk.Button(self.actions_frame, text='Onar', font=('Segoe UI', 9, 'bold'), bg='#f59e0b', fg='#111827', bd=0, padx=12, pady=6, state='disabled', command=self.repair_now)
        self.btn_repair.pack(side='left')

    def toggle_changelog(self):
        self.changelog_expanded = not self.changelog_expanded
        self.toggle_changelog_btn.config(text='Daralt' if self.changelog_expanded else 'Genişlet')
        self.changelog_box.configure(height=16 if self.changelog_expanded else 8)

    def set_info_text(self, local_version, remote_version, pending_updates):
        if pending_updates:
            first_step = pending_updates[0]
            next_version = first_step.get('to_version', remote_version)
            text = f'Bulunan sürüm: {local_version}\nSon sürüm: {remote_version}\nSonraki adım: {first_step.get("from_version")} -> {next_version}'
            if len(pending_updates) > 1:
                text += f'\nToplam adım: {len(pending_updates)}'
            self.info_text.config(text=text)
        else:
            self.info_text.config(text=f'Bulunan sürüm: {local_version}\nSon sürüm: {remote_version}\nGüncelleme yok.')

    def show_changelog_lines(self, lines):
        self.changelog_box.config(state='normal')
        self.changelog_box.delete('1.0', tk.END)
        if not lines:
            self.changelog_box.insert('1.0', 'Bu sürüm için değişiklik notu bulunmuyor.')
        else:
            for line in lines:
                self.changelog_box.insert(tk.END, f'{line}\n')
        self.changelog_box.config(state='disabled')

    def _find_options_for_latest(self):
        # Prefer options_updates tied to the latest to_version in update_chain
        opts = self.remote_data.get('options_updates', {}) or {}
        try:
            latest = self.remote_data.get('modpack_version')
            chain = self.remote_data.get('update_chain', []) or []
            for step in reversed(chain):
                if str(step.get('to_version')) == str(latest):
                    if step.get('options_updates'):
                        return step.get('options_updates', {})
        except Exception:
            pass
        return opts

    def fix_resourcepack_order(self):
        try:
            opts = self._find_options_for_latest() or {}
            rp = opts.get('resourcePacks') or opts.get('resourcePacks') or self.remote_data.get('options_updates', {}).get('resourcePacks')
            irp = opts.get('incompatibleResourcePacks') or self.remote_data.get('options_updates', {}).get('incompatibleResourcePacks')
            updates = {}
            if rp:
                updates['resourcePacks'] = rp
            if irp:
                updates['incompatibleResourcePacks'] = irp
            if not updates:
                messagebox.showinfo('Bilgi', 'version.json içinde resource pack sırası bulunamadı.')
                return
            self.update_options_txt(updates)
            messagebox.showinfo('Başarılı', 'Resource pack sırası uygulandı. Minecraft içinde kontrol edin ve gerekirse yeniden başlatın.')
        except Exception as e:
            self.log(f'Resource pack sırası düzeltilirken hata: {e}')
            messagebox.showerror('Hata', f'Resource pack sırası uygulanamadı:\n{e}')

    def open_version_changelogs_window(self):
        try:
            win = tk.Toplevel(self.root)
            win.title('Sürüm Notları')
            win.geometry('600x420')
            win.configure(bg=self.bg_color)

            left = tk.Frame(win, bg=self.card_color)
            left.pack(side='left', fill='y', padx=(12,6), pady=12)

            right = tk.Frame(win, bg=self.card_color)
            right.pack(side='right', fill='both', expand=True, padx=(6,12), pady=12)

            list_box = tk.Frame(left, bg=self.card_color)
            list_box.pack(fill='y')

            def show_lines(lines):
                txt.config(state='normal')
                txt.delete('1.0', tk.END)
                if not lines:
                    txt.insert('1.0', 'Bu sürüm için değişiklik notu bulunmuyor.')
                else:
                    for line in lines:
                        txt.insert(tk.END, f'{line}\n')
                txt.config(state='disabled')

            # Top-level changelog
            tk.Button(list_box, text=f'All Notes', font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=8, pady=6, command=lambda: show_lines(self.remote_data.get('changelog', []))).pack(fill='x', pady=4)

            # Per-step buttons
            for step in (self.remote_data.get('update_chain') or []):
                ver = step.get('to_version') or f"{step.get('from_version')} -> {step.get('to_version')}"
                tk.Button(list_box, text=f'v{ver}', font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=8, pady=6, command=lambda s=step: show_lines(s.get('changelog', []))).pack(fill='x', pady=2)

            # Pending updates (if any)
            pending = self.remote_data.get('pending_updates') or []
            if pending:
                sep = tk.Label(list_box, text='-- Bekleyen Güncellemeler --', bg=self.card_color, fg=self.text_color)
                sep.pack(fill='x', pady=(8,4))
                for idx, step in enumerate(pending, 1):
                    label = f'Adım {idx}: {step.get("from_version")} -> {step.get("to_version")}'
                    tk.Button(list_box, text=label, font=('Segoe UI', 9), bg='#374151', fg=self.text_color, bd=0, padx=8, pady=6, command=lambda s=step: show_lines(s.get('changelog', []))).pack(fill='x', pady=2)

            txt = tk.Text(right, font=('Segoe UI', 9), bg=self.card_color, fg=self.text_color, bd=0, wrap='word')
            txt.pack(fill='both', expand=True)
            txt.insert('1.0', 'Sürüm notlarından birini seçin.')
            txt.config(state='disabled')

            tk.Button(win, text='Kapat', command=win.destroy, bg=self.bg_color, fg=self.text_color, bd=0).pack(pady=(0,8))
        except Exception as e:
            self.log(f'Sürüm notları penceresi açılamadı: {e}')

    def repair_now(self):
        Thread(target=self._repair_background, daemon=True).start()

    def _repair_background(self):
        try:
            self.btn_repair.config(state='disabled')
            self.status_label.config(text='Onarım uygulanıyor...', fg=self.text_color)
            self.root.update_idletasks()

            zip_path = os.path.join(self.current_dir, 'temp_repair.zip')
            urls = self.remote_data.get('modpack_urls') or self.remote_data.get('modpack_url')
            if isinstance(urls, str):
                urls = [urls]
            if not urls:
                raise Exception('Onarım için modpack URLsi bulunamadı.')

            download_success = False
            for idx, url in enumerate(urls):
                try:
                    opener = urllib.request.build_opener()
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(url, zip_path, reporthook=self.download_progress)
                    if zipfile.is_zipfile(zip_path):
                        download_success = True
                        break
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except Exception as e:
                    self.log(f'Onarım indirilemedi ({url}): {e}')
                    if os.path.exists(zip_path):
                        os.remove(zip_path)

            if not download_success:
                raise Exception('Onarım indirilemedi.')

            # apply as a single step
            step = {'options_updates': self.remote_data.get('options_updates', {}), 'deleted_files': self.remote_data.get('deleted_files', [])}
            self.apply_patch_zip(zip_path, step, 1, 1)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            self.update_options_txt(step.get('options_updates', {}))
            self.remove_deleted_files(step.get('deleted_files', []))

            messagebox.showinfo('Başarılı', 'Onarım tamamlandı.')
            self.status_label.config(text='Onarım tamamlandı.', fg=self.success_color)
        except Exception as e:
            self.log(f'Onarım hatası: {e}')
            messagebox.showerror('Hata', f'Onarım başarısız:\n{e}')
            self.status_label.config(text=f'Onarım hatası: {e}', fg=self.error_color)
        finally:
            try:
                self.btn_repair.config(state='normal')
            except Exception:
                pass

    def sanitize_folder_on_startup(self):
        current_exe = sys.executable
        if not current_exe.endswith('.exe'):
            return True

        current_exe_name = os.path.basename(current_exe)
        final_exe_path = os.path.join(self.current_dir, 'Modpack_Guncelleyici_v2.exe')

        for old_name in ['Modpack_Guncelleyici_MANUEL.exe', 'Modpack_Guncelleyici_OTOMATİK.exe']:
            old_path = os.path.join(self.current_dir, old_name)
            if os.path.exists(old_path) and current_exe_name != old_name:
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        if '_yeni.exe' in current_exe_name.lower() or '_temp_' in current_exe_name.lower():
            pid = os.getpid()
            ps_script = f'''
            Start-Sleep -Seconds 1
            $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
            if ($proc) {{ $proc | Wait-Process -Timeout 5 }}
            if (Test-Path "{final_exe_path}") {{ Remove-Item "{final_exe_path}" -Force }}
            Rename-Item "{current_exe}" "Modpack_Guncelleyici_v2.exe" -Force
            Start-Process "{final_exe_path}"
            '''
            subprocess.Popen(['powershell', '-Command', ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
            self.root.destroy()
            sys.exit(0)
            return False

        return True

    def check_launcher_update_and_load(self):
        try:
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                self.remote_data = json.loads(response.read().decode('utf-8'))

            self.log(f'Remote manifest yüklendi: {JSON_URL}')

            remote_updater_ver = self.remote_data.get('updater_version', '1.0.0')
            if should_require_launcher_update(CURRENT_UPDATER_VERSION, remote_updater_ver):
                self.status_label.config(text=f'Yeni güncelleyici sürümü bulundu: v{remote_updater_ver}', fg=self.accent_color)
                self.root.update_idletasks()
                if self.should_prompt_for_launcher_update(remote_updater_ver):
                    self.prompt_for_launcher_update(remote_updater_ver)
                else:
                    self.log(f'Launcher güncelleme bildirimi atlandı: v{remote_updater_ver}')
                return

            local_version_path = os.path.join(self.current_dir, 'local_version.json')
            local_ver = '0.0.0'
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r', encoding='utf-8') as fh:
                        local_ver = json.load(fh).get('version', '0.0.0')
                except Exception as e:
                    self.log(f'local_version.json okunamadı: {e}')

            pending_updates = collect_pending_updates(local_ver, self.remote_data)
            latest_version = self.remote_data.get('modpack_version', '0.0.0')
            if isinstance(self.remote_data.get('update_chain', []), list) and self.remote_data.get('update_chain'):
                latest_version = self.remote_data['update_chain'][-1].get('to_version', latest_version)

            self.set_info_text(local_ver, latest_version, pending_updates)
            if pending_updates:
                # Save pending updates to remote_data so the 'Sürüm Notları' window can display them
                try:
                    self.remote_data['pending_updates'] = pending_updates
                except Exception:
                    pass
                # Don't show full changelog on main screen; direct user to the Sürüm Notları window
                self.show_changelog_lines(['Yeni güncelleme bulundu. Detaylı değişiklik notları için "Sürüm Notları" butonuna tıklayın.'])
                self.status_label.config(text=f'Yeni güncelleme bulundu: {local_ver} -> {latest_version}', fg=self.error_color)
                self.btn_update.config(text='Güncellemeyi Başlat', bg=self.accent_color, fg='#111827', state='normal', command=self.start_update_thread)
                self.btn_fix_resourcepacks.config(state='normal')
                self.btn_versions.config(state='normal')
                self.btn_repair.config(state='normal')
            else:
                # Main changelog hidden on main screen; instruct user to open version notes window
                self.show_changelog_lines(['Güncelleme notlarını görmek için "Sürüm Notları" butonuna tıklayın.'])
                self.status_label.config(text=f'Mod paketi tamamen güncel! (Sürüm: v{local_ver})', fg=self.success_color)
                self.btn_update.config(text='Zaten Güncel', bg=self.success_color, fg='#111827', state='disabled')
                self.btn_fix_resourcepacks.config(state='normal')
                self.btn_versions.config(state='normal')
                self.btn_repair.config(state='normal')

        except Exception as e:
            self.log(f'Manifest yüklenirken hata: {e}')
            self.status_label.config(text=f'Hata oluştu: {str(e)}', fg=self.error_color)

    def start_update_thread(self):
        self.btn_update.config(state='disabled')
        Thread(target=self.perform_incremental_update, daemon=True).start()

    def download_progress(self, block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, int((downloaded / total_size) * 100))
            self.progress['value'] = percent * 0.5
            self.status_label.config(text=f'İndiriliyor: %{percent} (Sunucu: {self.current_server_info})', fg=self.text_color)
            self.root.update_idletasks()

    def update_options_txt(self, options_updates=None):
        options_path = os.path.join(self.current_dir, 'minecraft', 'options.txt')
        if not options_updates:
            return
        if not os.path.exists(options_path):
            return

        try:
            self.status_label.config(text='options.txt ayarları optimize ediliyor...')
            self.root.update_idletasks()

            current_settings = {}
            with open(options_path, 'r', encoding='utf-8', errors='ignore') as fh:
                for line in fh:
                    if ':' in line:
                        key, val = line.strip().split(':', 1)
                        current_settings[key] = val

            for key, val in options_updates.items():
                current_settings[key] = val

            with open(options_path, 'w', encoding='utf-8') as fh:
                for key, val in current_settings.items():
                    fh.write(f'{key}:{val}\n')
        except Exception as e:
            self.log(f'options.txt güncellenirken hata: {e}')

    def remove_deleted_files(self, deleted_files=None):
        if not deleted_files:
            return
        for rel_path in deleted_files:
            fixed_path = rel_path
            if fixed_path.startswith('.minecraft/'):
                fixed_path = fixed_path.replace('.minecraft/', 'minecraft/', 1)

            full_del_path = os.path.join(self.current_dir, fixed_path.replace('/', os.sep))
            try:
                if os.path.isfile(full_del_path):
                    os.remove(full_del_path)
                elif os.path.isdir(full_del_path):
                    shutil.rmtree(full_del_path)
            except Exception as e:
                self.log(f'Kaldırılan dosya temizlenemedi: {rel_path} -> {e}')

    def apply_patch_zip(self, zip_path, step, step_index, total_steps):
        protected_folders = ['saves', 'screenshots', 'schematics', 'xaero']
        self.progress['value'] = 55 + ((step_index - 1) / max(1, total_steps) * 35)
        self.root.update_idletasks()

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            for i, file_name in enumerate(file_list):
                if file_name.endswith('/'):
                    continue

                parts = file_name.split('/')
                if len(parts) > 1 and parts[0] == 'minecraft':
                    folder_lower = parts[1].lower()
                    if folder_lower in protected_folders or folder_lower.startswith('xaerowaypoints'):
                        continue

                target_path = os.path.join(self.current_dir, file_name.replace('/', os.sep))
                target_dir = os.path.dirname(target_path)

                try:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                    with zip_ref.open(file_name) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                except Exception as e:
                    self.skipped_files.append(file_name)
                    self.log(f'Atlanan dosya: {file_name} -> {e}')
                    continue

                if i % max(1, (total_files // 10)) == 0:
                    percent_extract = int((i / total_files) * 100)
                    self.progress['value'] = 55 + ((step_index - 1) / max(1, total_steps) * 35) + (percent_extract / max(1, total_steps) * 0.35)
                    self.status_label.config(text=f'Adım {step_index}/{total_steps}: Dosyalar güncelleniyor... %{percent_extract}')
                    self.root.update_idletasks()

    def resolve_patch_urls(self, step):
        raw_urls = step.get('modpack_urls') or step.get('modpack_url') or self.remote_data.get('modpack_urls') or self.remote_data.get('modpack_url')
        if isinstance(raw_urls, str):
            return [raw_urls]
        if isinstance(raw_urls, list):
            return [url for url in raw_urls if isinstance(url, str) and url]
        return []

    def perform_incremental_update(self):
        temp_zip_name = 'temp_patch.zip'
        zip_path = os.path.join(self.current_dir, temp_zip_name)
        self.skipped_files = []

        try:
            local_version_path = os.path.join(self.current_dir, 'local_version.json')
            local_ver = '0.0.0'
            if os.path.exists(local_version_path):
                try:
                    with open(local_version_path, 'r', encoding='utf-8') as fh:
                        local_ver = json.load(fh).get('version', '0.0.0')
                except Exception as e:
                    self.log(f'local_version.json okunamadı: {e}')

            pending_updates = collect_pending_updates(local_ver, self.remote_data)
            if not pending_updates:
                self.status_label.config(text='Güncellenecek adım bulunamadı.', fg=self.success_color)
                self.btn_update.config(state='normal')
                return

            total_steps = len(pending_updates)
            for step_index, step in enumerate(pending_updates, 1):
                self.progress['value'] = (step_index - 1) / max(1, total_steps) * 100
                from_ver = step.get('from_version', local_ver)
                to_ver = step.get('to_version', 'unknown')
                self.status_label.config(text=f'Adım {step_index}/{total_steps}: {from_ver} -> {to_ver} güncelleniyor...', fg=self.text_color)
                self.detail_label.config(text=f'İşlem detayı: {from_ver} sürümünden {to_ver} sürümüne geçiliyor')
                self.root.update_idletasks()

                patch_urls = self.resolve_patch_urls(step)
                if not patch_urls:
                    raise Exception(f'{from_ver} -> {to_ver} için güncelleme URLsi bulunamadı.')

                download_success = False
                for idx, url in enumerate(patch_urls):
                    try:
                        self.current_server_info = f'{idx + 1}/{len(patch_urls)}'
                        self.status_label.config(text=f'Adım {step_index}/{total_steps}: İndiriliyor ({self.current_server_info})...', fg=self.text_color)
                        self.root.update_idletasks()

                        if os.path.exists(zip_path):
                            os.remove(zip_path)

                        opener = urllib.request.build_opener()
                        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
                        urllib.request.install_opener(opener)
                        urllib.request.urlretrieve(url, zip_path, reporthook=self.download_progress)

                        if zipfile.is_zipfile(zip_path):
                            download_success = True
                            break
                        self.log(f'İndirilen dosya geçerli ZIP değil: {url}')
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                    except Exception as e:
                        self.log(f'Patch indirme hatası ({url}): {e}')
                        if os.path.exists(zip_path):
                            os.remove(zip_path)

                if not download_success:
                    raise Exception(f'{from_ver} -> {to_ver} güncellemesi indirilemedi.')

                self.apply_patch_zip(zip_path, step, step_index, total_steps)

                if os.path.exists(zip_path):
                    os.remove(zip_path)

                self.update_options_txt(step.get('options_updates', {}))
                self.remove_deleted_files(step.get('deleted_files', []))

                with open(local_version_path, 'w', encoding='utf-8') as fh:
                    json.dump({'version': to_ver}, fh)

                self.log(f'Adım tamamlandı: {from_ver} -> {to_ver}')

            self.progress['value'] = 100
            self.status_label.config(text=f'Güncelleme tamamlandı! Son sürüm: v{pending_updates[-1].get("to_version", local_ver)}', fg=self.success_color)
            self.btn_update.config(text='Sürüm Güncel', bg=self.success_color, fg='#111827', state='disabled')
            if self.skipped_files:
                messagebox.showwarning('Uyarı', f'Güncelleme tamamlandı ancak {len(self.skipped_files)} dosya atlandı. Detaylar {self.log_file} dosyasında yazıyor.')
            else:
                messagebox.showinfo('Başarılı', f'Mod paketiniz {pending_updates[-1].get("to_version", local_ver)} sürümüne başarıyla güncellendi!')

        except Exception as e:
            self.log(f'Güncelleme hatası: {e}')
            self.status_label.config(text=f'Hata oluştu:\n{str(e)}', fg=self.error_color)
            messagebox.showerror('Hata', f'İşlem başarısız:\n{str(e)}')
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            self.btn_update.config(state='normal')


if __name__ == '__main__':
    root = tk.Tk()
    app = IncrementalLauncherApp(root)
    root.mainloop()