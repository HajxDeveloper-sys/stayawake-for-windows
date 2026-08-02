import sys
import os
import ctypes
import time
import threading
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "Python 3.11 öncesi sürümlerde 'tomli' paketi gereklidir. "
            "Lütfen 'pip install tomli' komutuyla yükleyin."
        )
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from security import (
    Win32SecurityManager,
    SingleInstanceGuard,
    AntiDDoSController,
    InputSanitizer,
    ImageBombProtector,
    ConfigValidator
)

Win32SecurityManager.apply_dll_security()

ImageBombProtector.apply_protection()

if sys.platform == 'win32':
    try:
        myappid = 'uyanikkal.power.preventer.v1.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as err:
        print(f"AppUserModelID initialization warning: {err}")

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

MOUSEEVENTF_MOVE = 0x0001

def load_config():
    default_config = {
        'ui': {
            'show_reset_button': True,
            'default_language': 'TR',
            'allow_resizable': True
        },
        'protection': {
            'default_keep_display': True,
            'default_keep_system': True,
            'default_virtual_heartbeat': True
        },
        'security': {
            'rate_limit_enabled': True,
            'max_burst_capacity': 10,
            'refill_rate_per_sec': 2.0,
            'single_instance_only': True
        }
    }
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'rb') as f:
                loaded = tomllib.load(f)
                validated = ConfigValidator.validate_config(loaded)
                return validated
        except Exception as err:
            print(f"Config read error: {err}")
    return default_config

class SleepPreventerEngine:

    def __init__(self):
        self.is_active = False
        self.start_time = 0.0
        self.elapsed_seconds = 0
        self._thread = None
        self._stop_event = threading.Event()
        self.keep_display = True
        self.keep_system = True

    def _compute_flags(self) -> int:
        flags = ES_CONTINUOUS
        if self.keep_system:
            flags |= ES_SYSTEM_REQUIRED
        if self.keep_display:
            flags |= ES_DISPLAY_REQUIRED
        return flags

    def start(self, keep_display=True, keep_system=True, virtual_heartbeat=True):
        if self.is_active:
            return
        
        self.keep_display = keep_display
        self.keep_system = keep_system
        self.is_active = True
        self.start_time = time.time()
        self._stop_event.clear()

        flags = self._compute_flags()
        if sys.platform == 'win32':
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(flags)
            except Exception as err:
                print(f"Win32 API execution error: {err}")

        self._thread = threading.Thread(
            target=self._run_heartbeat_daemon, 
            args=(virtual_heartbeat,), 
            daemon=True
        )
        self._thread.start()

    def stop(self):
        if not self.is_active:
            return
        
        self.is_active = False
        self._stop_event.set()
        
        if sys.platform == 'win32':
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            except Exception as err:
                print(f"Win32 API reset error: {err}")

    def reset_timer(self):
        if not self.is_active:
            self.start_time = 0.0
            self.elapsed_seconds = 0

    def _run_heartbeat_daemon(self, virtual_heartbeat):
        last_mouse_time = 0.0
        last_reassert_time = time.time()

        while not self._stop_event.is_set():
            now = time.time()
            self.elapsed_seconds = int(now - self.start_time)

            if now - last_reassert_time >= 15.0:
                if sys.platform == 'win32':
                    try:
                        flags = self._compute_flags()
                        ctypes.windll.kernel32.SetThreadExecutionState(flags)
                    except Exception:
                        pass
                last_reassert_time = now
            
            if virtual_heartbeat and (now - last_mouse_time >= 45.0):
                if sys.platform == 'win32':
                    try:
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, 0)
                    except Exception:
                        pass
                last_mouse_time = now
                
            time.sleep(1.0)

    def get_formatted_runtime(self):
        if not self.is_active:
            hours, remainder = divmod(self.elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        current_elapsed = int(time.time() - self.start_time)
        hours, remainder = divmod(current_elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

LANGUAGES = {
    'TR': {
        'title': 'Uyanık Kal',
        'subtitle': 'Windows Güç ve Ekran Yönetimi Asistanı',
        'status_active': '[ETKİN] Ekran ve Sistem Uyanık Tutuluyor',
        'status_inactive': '[DEVRE DIŞI] Varsayılan Windows Güç Modu',
        'timer_title': 'Kesintisiz Çalışma Süresi',
        'btn_start': 'Uykuyu Engelle (Etkinleştir)',
        'btn_stop': 'Korumayı Durdur (Devre Dışı Bırak)',
        'btn_reset': '↺ Süreyi Sıfırla',
        'config_header': 'Koruma Ayarları',
        'chk_display': 'Ekranın Kapanmasını Engelle',
        'chk_system': 'Sistemin Uykuya Girmesini Engelle',
        'chk_heartbeat': 'Sessiz Arka Plan Sinyali (İmleç Kıpırdamaz)',
        'footer': 'Uyanık Kal v1.1.0 • Tüm Hakları Saklıdır • Geliştirici: Hasan Aras DEMİR',
        'exit_title': 'Çıkış Onayı',
        'exit_msg': 'Uyanık Kal şu anda etkindir. Çıkarsanız bilgisayarınız varsayılan uyku moduna dönecektir.\n\nYine de çıkmak istiyor musunuz?',
        'already_running_title': 'Uyanık Kal Zaten Çalışıyor',
        'already_running_msg': 'Uyanık Kal zaten çalışıyor!\n\nKaynak koruması ve güvenlik gereği aynı anda yalnızca tek bir oturum çalıştırılabilir.'
    },
    'EN': {
        'title': 'Stay Awake',
        'subtitle': 'Windows Power & Display Management Assistant',
        'status_active': '[ACTIVE] Display & System Kept Awake',
        'status_inactive': '[INACTIVE] Default Windows Power Mode',
        'timer_title': 'Continuous Elapsed Runtime',
        'btn_start': 'Prevent Sleep (Enable)',
        'btn_stop': 'Stop Protection (Disable)',
        'btn_reset': '↺ Reset Timer',
        'config_header': 'Protection Settings',
        'chk_display': 'Prevent Display from Turning Off',
        'chk_system': 'Prevent System from Entering Sleep Mode',
        'chk_heartbeat': 'Silent Background Signal (Cursor Remains Still)',
        'footer': 'Stay Awake v1.1.0 • All Rights Reserved • Creator: Hasan Aras DEMİR',
        'exit_title': 'Confirm Exit',
        'exit_msg': 'Stay Awake is currently active! Exiting will restore your computer to default sleep mode.\n\nDo you still want to exit?',
        'already_running_title': 'Stay Awake Already Running',
        'already_running_msg': 'Stay Awake is already running!\n\nFor resource protection and security, only a single instance can run at a time.'
    }
}

class StayAwakeApp(tk.Tk):
    def __init__(self, single_instance_guard: SingleInstanceGuard = None):
        super().__init__()

        self.single_instance_guard = single_instance_guard
        self.config_data = load_config()

        ui_cfg = self.config_data['ui']
        prot_cfg = self.config_data['protection']
        sec_cfg = self.config_data.get('security', {})

        max_burst = sec_cfg.get('max_burst_capacity', 10)
        refill_rate = sec_cfg.get('refill_rate_per_sec', 2.0)
        self.rate_limiter = AntiDDoSController(max_tokens=max_burst, refill_rate=refill_rate)

        self.current_lang = ui_cfg.get('default_language', 'TR')

        app_title = LANGUAGES[self.current_lang]['title']
        self.title(f"{app_title} v1.1.0")
        self.geometry("520x640")
        self.minsize(460, 580)
        self.resizable(ui_cfg.get('allow_resizable', True), ui_cfg.get('allow_resizable', True))

        self.engine = SleepPreventerEngine()

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.icon_ico_path = os.path.join(self.assets_dir, "icon.ico")
        self.icon_png_path = os.path.join(self.assets_dir, "icon.png")

        self._load_app_icon()

        self.COLOR_BG = "#0B0F19"
        self.COLOR_CARD = "#111827"
        self.COLOR_BORDER = "#1F2937"
        self.COLOR_TEXT_PRIMARY = "#F9FAFB"
        self.COLOR_TEXT_SECONDARY = "#9CA3AF"
        
        self.COLOR_ACTIVE = "#10B981"
        self.COLOR_ACTIVE_HOVER = "#059669"
        self.COLOR_INACTIVE = "#DC2626"
        self.COLOR_INACTIVE_HOVER = "#B91C1C"
        self.COLOR_RESET_BTN = "#374151"
        self.COLOR_RESET_HOVER = "#4B5563"
        self.COLOR_DISABLED = "#1F2937"
        self.COLOR_CYAN = "#06B6D4"

        self.configure(bg=self.COLOR_BG)

        self.var_keep_display = tk.BooleanVar(value=prot_cfg.get('default_keep_display', True))
        self.var_keep_system = tk.BooleanVar(value=prot_cfg.get('default_keep_system', True))
        self.var_virtual_heartbeat = tk.BooleanVar(value=prot_cfg.get('default_virtual_heartbeat', True))

        self.btn_reset = None

        self._build_ui()

        self._update_timer_loop()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_app_icon(self):
        try:
            if os.path.exists(self.icon_ico_path):
                self.iconbitmap(self.icon_ico_path)
                self.wm_iconbitmap(self.icon_ico_path)
            if os.path.exists(self.icon_png_path):
                img = Image.open(self.icon_png_path)
                photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, photo)
                self.app_icon_img = photo
        except Exception as err:
            print(f"Icon loading warning: {err}")

    def _build_ui(self):
        txt = LANGUAGES[self.current_lang]
        show_reset = self.config_data['ui'].get('show_reset_button', True)

        main_container = tk.Frame(self, bg=self.COLOR_BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        header_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        try:
            if os.path.exists(self.icon_png_path):
                pil_icon = Image.open(self.icon_png_path).resize((44, 44), Image.Resampling.LANCZOS)
                self.header_icon_tk = ImageTk.PhotoImage(pil_icon)
                icon_label = tk.Label(header_frame, image=self.header_icon_tk, bg=self.COLOR_BG)
                icon_label.pack(side=tk.LEFT, padx=(0, 14))
        except Exception:
            pass

        title_container = tk.Frame(header_frame, bg=self.COLOR_BG)
        title_container.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_title = tk.Label(
            title_container,
            text=txt['title'],
            font=("Segoe UI", 18, "bold"),
            fg=self.COLOR_CYAN,
            bg=self.COLOR_BG
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = tk.Label(
            title_container,
            text=txt['subtitle'],
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG
        )
        self.lbl_subtitle.pack(anchor="w")

        self.btn_lang = tk.Button(
            header_frame,
            text="🇹🇷 TR" if self.current_lang == 'TR' else "🇬🇧 EN",
            font=("Segoe UI", 9, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_CARD,
            activebackground=self.COLOR_BORDER,
            activeforeground=self.COLOR_TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._toggle_language
        )
        self.btn_lang.pack(side=tk.RIGHT, anchor="n")

        self.status_card = tk.Frame(
            main_container,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        self.status_card.pack(fill=tk.X, pady=10)

        self.lbl_status_badge = tk.Label(
            self.status_card,
            text=txt['status_inactive'],
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_CARD
        )
        self.lbl_status_badge.pack(anchor="center", pady=(0, 10))

        self.lbl_timer_title = tk.Label(
            self.status_card,
            text=txt['timer_title'],
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_CARD
        )
        self.lbl_timer_title.pack(anchor="center")

        self.lbl_timer = tk.Label(
            self.status_card,
            text="00:00:00",
            font=("Consolas", 36, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_CARD
        )
        self.lbl_timer.pack(anchor="center", pady=5)

        action_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        action_frame.pack(fill=tk.X, pady=15)

        self.btn_toggle = tk.Button(
            action_frame,
            text=txt['btn_start'],
            font=("Segoe UI", 12, "bold"),
            fg="#FFFFFF",
            bg=self.COLOR_ACTIVE,
            activebackground=self.COLOR_ACTIVE_HOVER,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=14,
            command=self._toggle_engine
        )
        
        if show_reset:
            self.btn_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

            self.btn_reset = tk.Button(
                action_frame,
                text=txt['btn_reset'],
                font=("Segoe UI", 10, "bold"),
                fg=self.COLOR_TEXT_PRIMARY,
                bg=self.COLOR_RESET_BTN,
                activebackground=self.COLOR_RESET_HOVER,
                activeforeground=self.COLOR_TEXT_PRIMARY,
                disabledforeground=self.COLOR_TEXT_SECONDARY,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                padx=15,
                pady=14,
                state=tk.NORMAL,
                command=self._reset_timer
            )
            self.btn_reset.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.btn_toggle.pack(fill=tk.X)

        options_card = tk.Frame(
            main_container,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=20,
            pady=15
        )
        options_card.pack(fill=tk.X, pady=5)

        self.lbl_options_header = tk.Label(
            options_card,
            text=txt['config_header'],
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_CARD
        )
        self.lbl_options_header.pack(anchor="w", pady=(0, 8))

        self.chk_display = self._create_checkbox(
            options_card, 
            txt['chk_display'], 
            self.var_keep_display
        )
        self.chk_display.pack(anchor="w", pady=4)

        self.chk_system = self._create_checkbox(
            options_card, 
            txt['chk_system'], 
            self.var_keep_system
        )
        self.chk_system.pack(anchor="w", pady=4)

        self.chk_heartbeat = self._create_checkbox(
            options_card, 
            txt['chk_heartbeat'], 
            self.var_virtual_heartbeat
        )
        self.chk_heartbeat.pack(anchor="w", pady=4)

        footer_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))

        self.lbl_footer_info = tk.Label(
            footer_frame,
            text=txt['footer'],
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG,
            justify=tk.CENTER
        )
        self.lbl_footer_info.pack(anchor="center")

    def _create_checkbox(self, parent, text, variable):
        chk = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_CARD,
            activebackground=self.COLOR_CARD,
            activeforeground=self.COLOR_TEXT_PRIMARY,
            disabledforeground=self.COLOR_TEXT_SECONDARY,
            selectcolor=self.COLOR_BG,
            bd=0,
            cursor="hand2"
        )
        return chk

    def _toggle_language(self):
        if not self.rate_limiter.is_allowed():
            return

        self.current_lang = 'EN' if self.current_lang == 'TR' else 'TR'
        txt = LANGUAGES[self.current_lang]

        self.title(f"{txt['title']} v1.1.0")
        self.btn_lang.config(text="🇹🇷 TR" if self.current_lang == 'TR' else "🇬🇧 EN")
        self.lbl_title.config(text=txt['title'])
        self.lbl_subtitle.config(text=txt['subtitle'])
        self.lbl_timer_title.config(text=txt['timer_title'])
        self.lbl_options_header.config(text=txt['config_header'])
        self.chk_display.config(text=txt['chk_display'])
        self.chk_system.config(text=txt['chk_system'])
        self.chk_heartbeat.config(text=txt['chk_heartbeat'])
        self.lbl_footer_info.config(text=txt['footer'])

        if self.btn_reset:
            self.btn_reset.config(text=txt['btn_reset'])

        if self.engine.is_active:
            self.lbl_status_badge.config(text=txt['status_active'])
            self.btn_toggle.config(text=txt['btn_stop'])
        else:
            self.lbl_status_badge.config(text=txt['status_inactive'])
            self.btn_toggle.config(text=txt['btn_start'])

    def _reset_timer(self):
        if not self.rate_limiter.is_allowed():
            return

        if not self.engine.is_active:
            self.engine.reset_timer()
            self.lbl_timer.config(text="00:00:00")

    def _toggle_engine(self):
        if not self.rate_limiter.is_allowed():
            return

        txt = LANGUAGES[self.current_lang]

        if not self.engine.is_active:
            self.engine.start(
                keep_display=self.var_keep_display.get(),
                keep_system=self.var_keep_system.get(),
                virtual_heartbeat=self.var_virtual_heartbeat.get()
            )
            self.btn_toggle.config(
                text=txt['btn_stop'],
                bg=self.COLOR_INACTIVE,
                activebackground=self.COLOR_INACTIVE_HOVER
            )
            self.lbl_status_badge.config(
                text=txt['status_active'],
                fg=self.COLOR_ACTIVE
            )
            self.status_card.config(highlightbackground=self.COLOR_ACTIVE)

            self.chk_display.config(state=tk.DISABLED, cursor="arrow")
            self.chk_system.config(state=tk.DISABLED, cursor="arrow")
            self.chk_heartbeat.config(state=tk.DISABLED, cursor="arrow")

            if self.btn_reset:
                self.btn_reset.config(
                    state=tk.DISABLED,
                    bg=self.COLOR_DISABLED,
                    cursor="arrow"
                )
        else:
            self.engine.stop()
            self.btn_toggle.config(
                text=txt['btn_start'],
                bg=self.COLOR_ACTIVE,
                activebackground=self.COLOR_ACTIVE_HOVER
            )
            self.lbl_status_badge.config(
                text=txt['status_inactive'],
                fg=self.COLOR_TEXT_SECONDARY
            )
            self.status_card.config(highlightbackground=self.COLOR_BORDER)

            self.chk_display.config(state=tk.NORMAL, cursor="hand2")
            self.chk_system.config(state=tk.NORMAL, cursor="hand2")
            self.chk_heartbeat.config(state=tk.NORMAL, cursor="hand2")

            if self.btn_reset:
                self.btn_reset.config(
                    state=tk.NORMAL,
                    bg=self.COLOR_RESET_BTN,
                    cursor="hand2"
                )

    def _update_timer_loop(self):
        formatted_time = self.engine.get_formatted_runtime()
        self.lbl_timer.config(text=formatted_time)
        self.after(500, self._update_timer_loop)

    def _on_closing(self):
        txt = LANGUAGES[self.current_lang]
        if self.engine.is_active:
            ans = messagebox.askyesno(
                txt['exit_title'],
                txt['exit_msg']
            )
            if not ans:
                return
        
        self.engine.stop()
        if self.single_instance_guard:
            self.single_instance_guard.release()
        self.destroy()

if __name__ == "__main__":
    guard = SingleInstanceGuard()
    if not guard.acquire():
        root = tk.Tk()
        root.withdraw()
        cfg = load_config()
        lang = cfg.get('ui', {}).get('default_language', 'TR')
        txt = LANGUAGES.get(lang, LANGUAGES['TR'])
        messagebox.showwarning(txt['already_running_title'], txt['already_running_msg'])
        root.destroy()
        sys.exit(0)

    app = StayAwakeApp(single_instance_guard=guard)
    app.mainloop()
