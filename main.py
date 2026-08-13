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
        myappid = 'uyanikkal.power.preventer.v1.2.0'
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
            'default_virtual_heartbeat': True,
            'default_session_minutes': 0,
            'default_always_on_top': False
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
        return format_duration(self.get_elapsed_seconds())

    def get_elapsed_seconds(self) -> int:
        if not self.is_active:
            return self.elapsed_seconds
        return max(0, int(time.time() - self.start_time))


def format_duration(total_seconds: int) -> str:
        hours, remainder = divmod(max(0, int(total_seconds)), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

LANGUAGES = {
    'TR': {
        'title': 'Uyanık Kal',
        'subtitle': 'Windows güç ve ekran oturum yöneticisi',
        'status_active': '● KORUMA ETKİN',
        'status_inactive': '○ HAZIR',
        'status_completed': '✓ PLANLANAN OTURUM TAMAMLANDI',
        'timer_title': 'Geçen süre',
        'btn_start': 'Korumayı başlat',
        'btn_stop': 'Oturumu durdur',
        'btn_reset': '↺ Süreyi Sıfırla',
        'config_header': 'Koruma kapsamı',
        'chk_display': 'Ekranın Kapanmasını Engelle',
        'chk_system': 'Sistemin Uykuya Girmesini Engelle',
        'chk_heartbeat': 'Sessiz Arka Plan Sinyali (İmleç Kıpırdamaz)',
        'chk_always_on_top': 'Pencereyi her zaman üstte tut',
        'duration_header': 'Oturum süresi',
        'duration_unlimited': 'Sınırsız',
        'duration_30': '30 dk',
        'duration_60': '1 saat',
        'duration_120': '2 saat',
        'remaining': 'Kalan {time} • Bitiş {end_time}',
        'unlimited_hint': 'Siz durdurana kadar etkin kalır',
        'last_session': 'Son oturum: {time}',
        'shortcut': 'F8 ile hızlı başlat / durdur',
        'select_protection': 'En az bir koruma seçeneği etkin olmalıdır.',
        'footer': 'Stay Awake v1.2.0 • Çevrimdışı çalışır • Hasan Aras DEMİR',
        'exit_title': 'Çıkış Onayı',
        'exit_msg': 'Uyanık Kal şu anda etkindir. Çıkarsanız bilgisayarınız varsayılan uyku moduna dönecektir.\n\nYine de çıkmak istiyor musunuz?',
        'already_running_title': 'Uyanık Kal Zaten Çalışıyor',
        'already_running_msg': 'Uyanık Kal zaten çalışıyor!\n\nKaynak koruması ve güvenlik gereği aynı anda yalnızca tek bir oturum çalıştırılabilir.'
    },
    'EN': {
        'title': 'Stay Awake',
        'subtitle': 'Windows power and display session manager',
        'status_active': '● PROTECTION ACTIVE',
        'status_inactive': '○ READY',
        'status_completed': '✓ SCHEDULED SESSION COMPLETED',
        'timer_title': 'Elapsed time',
        'btn_start': 'Start protection',
        'btn_stop': 'Stop session',
        'btn_reset': '↺ Reset Timer',
        'config_header': 'Protection scope',
        'chk_display': 'Prevent Display from Turning Off',
        'chk_system': 'Prevent System from Entering Sleep Mode',
        'chk_heartbeat': 'Silent Background Signal (Cursor Remains Still)',
        'chk_always_on_top': 'Keep this window always on top',
        'duration_header': 'Session duration',
        'duration_unlimited': 'Unlimited',
        'duration_30': '30 min',
        'duration_60': '1 hour',
        'duration_120': '2 hours',
        'remaining': '{time} remaining • Ends {end_time}',
        'unlimited_hint': 'Stays active until you stop it',
        'last_session': 'Last session: {time}',
        'shortcut': 'Press F8 to start / stop quickly',
        'select_protection': 'Select at least one protection option.',
        'footer': 'Stay Awake v1.2.0 • Works offline • Hasan Aras DEMİR',
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
        self.title(f"{app_title} v1.2.0")
        self.geometry("600x760")
        self.minsize(530, 700)
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
        self.var_always_on_top = tk.BooleanVar(value=prot_cfg.get('default_always_on_top', False))
        self.selected_duration_minutes = tk.IntVar(value=prot_cfg.get('default_session_minutes', 0))
        self.session_deadline = None
        self.last_session_seconds = 0
        self.duration_buttons = {}

        self.btn_reset = None

        self._build_ui()
        self._toggle_always_on_top()
        self.bind("<F8>", lambda _event: self._toggle_engine())

        self._bring_to_foreground()

        self._update_timer_loop()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _bring_to_foreground(self):
        try:
            self.deiconify()
            self.lift()
            self.attributes('-topmost', True)
            self.after_idle(self.attributes, '-topmost', bool(self.var_always_on_top.get()))
            self.focus_force()
        except Exception as err:
            print(f"Bring to foreground warning: {err}")

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
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        header_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        header_frame.pack(fill=tk.X, pady=(0, 10))

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
            text="TR" if self.current_lang == 'TR' else "EN",
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
            pady=14
        )
        self.status_card.pack(fill=tk.X, pady=8)

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

        progress_style = ttk.Style(self)
        progress_style.theme_use("clam")
        progress_style.configure(
            "StayAwake.Horizontal.TProgressbar",
            troughcolor=self.COLOR_BORDER,
            background=self.COLOR_CYAN,
            bordercolor=self.COLOR_CARD,
            lightcolor=self.COLOR_CYAN,
            darkcolor=self.COLOR_CYAN,
            thickness=7
        )
        self.session_progress = ttk.Progressbar(
            self.status_card,
            style="StayAwake.Horizontal.TProgressbar",
            maximum=100,
            value=0
        )
        self.session_progress.pack(fill=tk.X, pady=(7, 8))

        self.lbl_countdown = tk.Label(
            self.status_card,
            text=txt['unlimited_hint'],
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_CARD
        )
        self.lbl_countdown.pack(anchor="center")

        action_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        action_frame.pack(fill=tk.X, pady=10)

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

        duration_card = tk.Frame(
            main_container,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=16,
            pady=10
        )
        duration_card.pack(fill=tk.X, pady=(0, 10))

        self.lbl_duration_header = tk.Label(
            duration_card,
            text=txt['duration_header'],
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_TEXT_PRIMARY,
            bg=self.COLOR_CARD
        )
        self.lbl_duration_header.pack(anchor="w", pady=(0, 8))

        duration_button_frame = tk.Frame(duration_card, bg=self.COLOR_CARD)
        duration_button_frame.pack(fill=tk.X)
        duration_specs = (
            (0, 'duration_unlimited'),
            (30, 'duration_30'),
            (60, 'duration_60'),
            (120, 'duration_120'),
        )
        for column, (minutes, text_key) in enumerate(duration_specs):
            duration_button_frame.grid_columnconfigure(column, weight=1)
            button = tk.Button(
                duration_button_frame,
                text=txt[text_key],
                font=("Segoe UI", 9, "bold"),
                fg=self.COLOR_TEXT_PRIMARY,
                bg=self.COLOR_RESET_BTN,
                activebackground=self.COLOR_CYAN,
                activeforeground="#FFFFFF",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                pady=8,
                command=lambda value=minutes: self._select_duration(value)
            )
            button.grid(row=0, column=column, padx=(0 if column == 0 else 4, 0), sticky="ew")
            self.duration_buttons[minutes] = button
        self._refresh_duration_buttons()

        options_card = tk.Frame(
            main_container,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=20,
            pady=11
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
        self.chk_display.pack(anchor="w", pady=3)

        self.chk_system = self._create_checkbox(
            options_card, 
            txt['chk_system'], 
            self.var_keep_system
        )
        self.chk_system.pack(anchor="w", pady=3)

        self.chk_heartbeat = self._create_checkbox(
            options_card, 
            txt['chk_heartbeat'], 
            self.var_virtual_heartbeat
        )
        self.chk_heartbeat.pack(anchor="w", pady=3)

        self.chk_always_on_top = self._create_checkbox(
            options_card,
            txt['chk_always_on_top'],
            self.var_always_on_top
        )
        self.chk_always_on_top.config(command=self._toggle_always_on_top)
        self.chk_always_on_top.pack(anchor="w", pady=(8, 4))

        self.lbl_shortcut = tk.Label(
            main_container,
            text=txt['shortcut'],
            font=("Segoe UI", 9),
            fg=self.COLOR_TEXT_SECONDARY,
            bg=self.COLOR_BG
        )
        self.lbl_shortcut.pack(anchor="center", pady=(7, 0))

        footer_frame = tk.Frame(main_container, bg=self.COLOR_BG)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

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

    def _toggle_always_on_top(self):
        self.attributes('-topmost', bool(self.var_always_on_top.get()))

    def _select_duration(self, minutes: int):
        if self.engine.is_active:
            return
        self.selected_duration_minutes.set(minutes)
        self._refresh_duration_buttons()
        txt = LANGUAGES[self.current_lang]
        self.lbl_countdown.config(text=txt['unlimited_hint'] if minutes == 0 else txt[f'duration_{minutes}'])

    def _refresh_duration_buttons(self):
        active_value = self.selected_duration_minutes.get()
        for minutes, button in self.duration_buttons.items():
            is_selected = minutes == active_value
            button.config(
                bg=self.COLOR_CYAN if is_selected else self.COLOR_RESET_BTN,
                activebackground=self.COLOR_CYAN,
                state=tk.DISABLED if self.engine.is_active else tk.NORMAL,
                cursor="arrow" if self.engine.is_active else "hand2"
            )

    def _set_running_ui(self, running: bool, completed: bool = False):
        txt = LANGUAGES[self.current_lang]
        if running:
            self.btn_toggle.config(
                text=txt['btn_stop'],
                bg=self.COLOR_INACTIVE,
                activebackground=self.COLOR_INACTIVE_HOVER
            )
            self.lbl_status_badge.config(text=txt['status_active'], fg=self.COLOR_ACTIVE)
            self.status_card.config(highlightbackground=self.COLOR_ACTIVE)
        else:
            self.btn_toggle.config(
                text=txt['btn_start'],
                bg=self.COLOR_ACTIVE,
                activebackground=self.COLOR_ACTIVE_HOVER
            )
            self.lbl_status_badge.config(
                text=txt['status_completed'] if completed else txt['status_inactive'],
                fg=self.COLOR_CYAN if completed else self.COLOR_TEXT_SECONDARY
            )
            self.status_card.config(highlightbackground=self.COLOR_CYAN if completed else self.COLOR_BORDER)

        option_state = tk.DISABLED if running else tk.NORMAL
        option_cursor = "arrow" if running else "hand2"
        for checkbox in (self.chk_display, self.chk_system, self.chk_heartbeat):
            checkbox.config(state=option_state, cursor=option_cursor)
        if self.btn_reset:
            self.btn_reset.config(
                state=tk.DISABLED if running else tk.NORMAL,
                bg=self.COLOR_DISABLED if running else self.COLOR_RESET_BTN,
                cursor="arrow" if running else "hand2"
            )
        self._refresh_duration_buttons()

    def _stop_session(self, completed: bool = False):
        self.last_session_seconds = self.engine.get_elapsed_seconds()
        self.engine.stop()
        self.engine.elapsed_seconds = self.last_session_seconds
        self.session_deadline = None
        self.session_progress['value'] = 100 if completed else 0
        self.lbl_countdown.config(
            text=LANGUAGES[self.current_lang]['last_session'].format(
                time=format_duration(self.last_session_seconds)
            )
        )
        self._set_running_ui(False, completed=completed)
        if completed:
            self.bell()

    def _toggle_language(self):
        if not self.rate_limiter.is_allowed():
            return

        self.current_lang = 'EN' if self.current_lang == 'TR' else 'TR'
        txt = LANGUAGES[self.current_lang]

        self.title(f"{txt['title']} v1.2.0")
        self.btn_lang.config(text="TR" if self.current_lang == 'TR' else "EN")
        self.lbl_title.config(text=txt['title'])
        self.lbl_subtitle.config(text=txt['subtitle'])
        self.lbl_timer_title.config(text=txt['timer_title'])
        self.lbl_options_header.config(text=txt['config_header'])
        self.lbl_duration_header.config(text=txt['duration_header'])
        self.chk_display.config(text=txt['chk_display'])
        self.chk_system.config(text=txt['chk_system'])
        self.chk_heartbeat.config(text=txt['chk_heartbeat'])
        self.chk_always_on_top.config(text=txt['chk_always_on_top'])
        self.lbl_shortcut.config(text=txt['shortcut'])
        self.lbl_footer_info.config(text=txt['footer'])
        duration_keys = {0: 'duration_unlimited', 30: 'duration_30', 60: 'duration_60', 120: 'duration_120'}
        for minutes, key in duration_keys.items():
            self.duration_buttons[minutes].config(text=txt[key])

        if self.btn_reset:
            self.btn_reset.config(text=txt['btn_reset'])

        if self.engine.is_active:
            self.lbl_status_badge.config(text=txt['status_active'])
            self.btn_toggle.config(text=txt['btn_stop'])
        else:
            self.lbl_status_badge.config(text=txt['status_inactive'])
            self.btn_toggle.config(text=txt['btn_start'])
            if self.last_session_seconds:
                self.lbl_countdown.config(text=txt['last_session'].format(time=format_duration(self.last_session_seconds)))
            elif self.selected_duration_minutes.get() == 0:
                self.lbl_countdown.config(text=txt['unlimited_hint'])

    def _reset_timer(self):
        if not self.rate_limiter.is_allowed():
            return

        if not self.engine.is_active:
            self.engine.reset_timer()
            self.last_session_seconds = 0
            self.session_progress['value'] = 0
            self.lbl_timer.config(text="00:00:00")
            txt = LANGUAGES[self.current_lang]
            minutes = self.selected_duration_minutes.get()
            self.lbl_countdown.config(
                text=txt['unlimited_hint'] if minutes == 0 else txt[f'duration_{minutes}']
            )

    def _toggle_engine(self):
        if not self.rate_limiter.is_allowed():
            return

        txt = LANGUAGES[self.current_lang]

        if not self.engine.is_active:
            if not any((
                self.var_keep_display.get(),
                self.var_keep_system.get(),
                self.var_virtual_heartbeat.get()
            )):
                messagebox.showwarning(txt['title'], txt['select_protection'])
                return
            self.engine.start(
                keep_display=self.var_keep_display.get(),
                keep_system=self.var_keep_system.get(),
                virtual_heartbeat=self.var_virtual_heartbeat.get()
            )
            minutes = self.selected_duration_minutes.get()
            self.session_deadline = time.time() + (minutes * 60) if minutes else None
            self.session_progress['value'] = 0
            self._set_running_ui(True)
        else:
            self._stop_session()

    def _update_timer_loop(self):
        formatted_time = self.engine.get_formatted_runtime()
        self.lbl_timer.config(text=formatted_time)
        if self.engine.is_active:
            txt = LANGUAGES[self.current_lang]
            if self.session_deadline is None:
                self.session_progress['value'] = 0
                self.lbl_countdown.config(text=txt['unlimited_hint'])
            else:
                remaining = max(0, int(self.session_deadline - time.time()))
                if remaining <= 0:
                    self._stop_session(completed=True)
                else:
                    total = self.selected_duration_minutes.get() * 60
                    elapsed = total - remaining
                    self.session_progress['value'] = min(100, (elapsed / total) * 100)
                    end_time = time.strftime("%H:%M", time.localtime(self.session_deadline))
                    self.lbl_countdown.config(
                        text=txt['remaining'].format(time=format_duration(remaining), end_time=end_time)
                    )
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
