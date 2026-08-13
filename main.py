"""Stay Awake's desktop interface.

Protection remains entirely local.  The interface intentionally describes the
scope of Windows' ``SetThreadExecutionState`` API accurately: it prevents idle
sleep/display timeout while this app is running; it cannot override a manual
lock, administrator policy, a closed laptop lid, or critical battery actions.
"""

from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from preferences import PreferencesStore
from security import (
    AntiDDoSController,
    ConfigValidator,
    ImageBombProtector,
    SingleInstanceGuard,
    Win32SecurityManager,
)
from session_engine import SleepPreventerEngine


Win32SecurityManager.apply_dll_security()
ImageBombProtector.apply_protection()

if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "stayawake.windows.v1.2.0"
        )
    except Exception:
        pass


def load_config() -> dict:
    """Read bundled defaults without ever writing to the install directory."""
    default_config = {
        "ui": {
            "show_reset_button": True,
            "default_language": "TR",
            "allow_resizable": True,
        },
        "protection": {
            "default_keep_display": True,
            "default_keep_system": True,
            "default_virtual_heartbeat": False,
        },
        "security": {
            "rate_limit_enabled": True,
            "max_burst_capacity": 10,
            "refill_rate_per_sec": 2.0,
            "single_instance_only": True,
        },
    }
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    if not os.path.exists(config_path):
        return default_config
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
        with open(config_path, "rb") as handle:
            return ConfigValidator.validate_config(tomllib.load(handle))
    except Exception:
        return default_config


LANGUAGES = {
    "TR": {
        "title": "Uyanık Kal",
        "subtitle": "Windows uyku ve ekran zaman aşımı yardımcısı",
        "active": "ETKİN",
        "inactive": "DEVRE DIŞI",
        "completed": "Oturum tamamlandı",
        "error": "Koruma uygulanamadı",
        "status_scope": "Koruma kapsamı: {scope}",
        "scope_both": "sistem uykusu ve ekran kapanması",
        "scope_system": "sistem uykusu",
        "scope_display": "ekran kapanması",
        "timer_title": "Koruma süresi",
        "session_continuous": "Süresiz oturum",
        "session_remaining": "Bitiş: {end}  •  Kalan: {remaining}",
        "session_ends": "Koruma siz durdurana kadar etkin kalır",
        "session_header": "Oturum süresi",
        "preset_continuous": "Süresiz",
        "preset_30": "30 dakika",
        "preset_60": "1 saat",
        "preset_120": "2 saat",
        "preset_custom": "Özel süre",
        "custom_minutes": "Dakika",
        "custom_hint": "1–1440 dakika arasında bir süre girin.",
        "btn_start": "Korumayı Başlat",
        "btn_stop": "Korumayı Durdur",
        "btn_retry_restore": "Normal Güç Davranışını Yeniden Dene",
        "btn_reset": "Süreyi Sıfırla",
        "settings_header": "Koruma ayarları",
        "chk_display": "Ekranın otomatik kapanmasını engelle",
        "chk_system": "Sistemin uykuya geçmesini engelle",
        "chk_heartbeat": "Uyumluluk için sessiz arka plan sinyali",
        "heartbeat_hint": "Bu seçenek yalnızca gerektiğinde kullanılmalıdır; imleci görünür biçimde hareket ettirmez.",
        "settings_locked": "Ayarları değiştirmek için korumayı durdurun.",
        "settings_ready": "En az bir koruma seçeneği etkin olmalıdır.",
        "api_limit": "Lütfen bir an bekleyip yeniden deneyin.",
        "no_protection": "Ekran, sistem veya her ikisi için korumayı seçin.",
        "duration_invalid": "Özel süre 1 ile 1440 dakika arasında bir tam sayı olmalıdır.",
        "start_failed": "Windows istenen güç korumasını uygulayamadı. Uygulamayı yeniden başlatın veya izinleri kontrol edin.",
        "restore_failed": "Windows'un normal güç davranışının geri yüklendiği doğrulanamadı. Uygulamayı açık bırakın ve yeniden deneme düğmesini kullanın.",
        "completed_title": "Oturum tamamlandı",
        "completed_message": "Süreli koruma sona erdi. Windows'un varsayılan güç davranışı geri yüklendi.",
        "exit_title": "Korumayı durdur?",
        "exit_message": "Uygulamadan çıkmak korumayı durdurur ve Windows'un varsayılan güç davranışını geri yükler. Çıkmak istiyor musunuz?",
        "already_running_title": "Uyanık Kal zaten açık",
        "already_running_message": "Uygulama zaten çalışıyor. Mevcut pencereden korumayı yönetebilirsiniz.",
        "footer": "Stay Awake v1.2.0 • Yerel çalışır, veri toplamaz",
        "shortcut": "Kısayol: Ctrl+Enter ile başlat/durdur",
    },
    "EN": {
        "title": "Stay Awake",
        "subtitle": "Windows sleep and display timeout helper",
        "active": "ACTIVE",
        "inactive": "INACTIVE",
        "completed": "Session complete",
        "error": "Protection could not be applied",
        "status_scope": "Protection scope: {scope}",
        "scope_both": "system sleep and display timeout",
        "scope_system": "system sleep",
        "scope_display": "display timeout",
        "timer_title": "Protection runtime",
        "session_continuous": "Continuous session",
        "session_remaining": "Ends: {end}  •  Remaining: {remaining}",
        "session_ends": "Protection stays enabled until you stop it",
        "session_header": "Session duration",
        "preset_continuous": "Continuous",
        "preset_30": "30 minutes",
        "preset_60": "1 hour",
        "preset_120": "2 hours",
        "preset_custom": "Custom duration",
        "custom_minutes": "Minutes",
        "custom_hint": "Enter a duration between 1 and 1,440 minutes.",
        "btn_start": "Start protection",
        "btn_stop": "Stop protection",
        "btn_retry_restore": "Retry restoring normal power",
        "btn_reset": "Reset timer",
        "settings_header": "Protection settings",
        "chk_display": "Prevent the display from timing out",
        "chk_system": "Prevent the system from sleeping",
        "chk_heartbeat": "Silent background signal for compatibility",
        "heartbeat_hint": "Use this only when needed; it does not visibly move your cursor.",
        "settings_locked": "Stop protection to edit these settings.",
        "settings_ready": "Keep at least one protection option enabled.",
        "api_limit": "Please wait a moment and try again.",
        "no_protection": "Choose display protection, sleep protection, or both.",
        "duration_invalid": "Custom duration must be a whole number from 1 to 1,440 minutes.",
        "start_failed": "Windows could not apply the requested power protection. Restart the app or check permissions.",
        "restore_failed": "Windows' normal power behavior could not be confirmed as restored. Keep the app open and use the retry button.",
        "completed_title": "Session complete",
        "completed_message": "Timed protection has ended and Windows' normal power behavior was restored.",
        "exit_title": "Stop protection?",
        "exit_message": "Exiting stops protection and restores Windows' normal power behavior. Do you want to exit?",
        "already_running_title": "Stay Awake is already open",
        "already_running_message": "The app is already running. Manage protection from the existing window.",
        "footer": "Stay Awake v1.2.0 • Runs locally, collects no data",
        "shortcut": "Shortcut: Ctrl+Enter starts/stops protection",
    },
}

PRESET_SECONDS = {"continuous": None, "30": 30 * 60, "60": 60 * 60, "120": 120 * 60}


def format_seconds(total_seconds: int) -> str:
    hours, remainder = divmod(max(0, total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class StayAwakeApp(tk.Tk):
    def __init__(self, single_instance_guard: SingleInstanceGuard | None = None):
        super().__init__()
        self.single_instance_guard = single_instance_guard
        self.config_data = load_config()
        self.preferences_store = PreferencesStore()
        self.preferences = self.preferences_store.load()

        ui_cfg = self.config_data["ui"]
        protection_cfg = self.config_data["protection"]
        security_cfg = self.config_data["security"]
        self.current_lang = self.preferences.get(
            "language", ui_cfg.get("default_language", "TR")
        )
        self.current_lang = self.current_lang if self.current_lang in LANGUAGES else "TR"
        self.engine = SleepPreventerEngine()
        self.rate_limiter = (
            AntiDDoSController(
                max_tokens=security_cfg.get("max_burst_capacity", 10),
                refill_rate=security_cfg.get("refill_rate_per_sec", 2.0),
            )
            if security_cfg.get("rate_limit_enabled", True)
            else None
        )

        self.COLOR_BG = "#0B1020"
        self.COLOR_CARD = "#121A2B"
        self.COLOR_BORDER = "#263247"
        self.COLOR_TEXT = "#F8FAFC"
        self.COLOR_MUTED = "#A5B4C8"
        self.COLOR_PRIMARY = "#2563EB"
        self.COLOR_PRIMARY_HOVER = "#1D4ED8"
        self.COLOR_ACTIVE = "#059669"
        self.COLOR_STOP = "#DC2626"
        self.COLOR_STOP_HOVER = "#B91C1C"
        self.COLOR_WARNING = "#F59E0B"
        self.COLOR_ERROR = "#F87171"

        self.var_keep_display = tk.BooleanVar(
            value=self.preferences.get(
                "keep_display", protection_cfg.get("default_keep_display", True)
            )
        )
        self.var_keep_system = tk.BooleanVar(
            value=self.preferences.get(
                "keep_system", protection_cfg.get("default_keep_system", True)
            )
        )
        self.var_virtual_heartbeat = tk.BooleanVar(
            value=self.preferences.get(
                "virtual_heartbeat",
                protection_cfg.get("default_virtual_heartbeat", False),
            )
        )
        preset = self.preferences.get("session_preset", "continuous")
        self.session_preset_key = (
            preset if preset in (set(PRESET_SECONDS) | {"custom"}) else "continuous"
        )
        self.custom_duration_var = tk.StringVar(
            value=str(self.preferences.get("custom_duration_minutes", 30))
        )
        self.session_display_var = tk.StringVar()
        self._completion_notice_session = -1
        self._last_active_state = False

        self.title(self._txt("title") + " v1.2.0")
        self.geometry(self.preferences.get("geometry", "520x700"))
        self.minsize(480, 650)
        can_resize = ui_cfg.get("allow_resizable", True)
        self.resizable(can_resize, can_resize)
        self.configure(bg=self.COLOR_BG)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self._load_app_icon()
        self._build_ui()
        self.bind("<Control-Return>", lambda _event: self._toggle_engine())
        self.bind("<Configure>", self._on_window_configure)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(100, self._bring_to_foreground)
        self._update_timer_loop()

    def _txt(self, key: str) -> str:
        return LANGUAGES[self.current_lang][key]

    def _load_app_icon(self) -> None:
        ico_path = os.path.join(self.assets_dir, "icon.ico")
        png_path = os.path.join(self.assets_dir, "icon.png")
        try:
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            if os.path.exists(png_path):
                image = Image.open(png_path)
                self.app_icon_image = ImageTk.PhotoImage(image)
                self.iconphoto(True, self.app_icon_image)
        except Exception:
            pass

    def _bring_to_foreground(self) -> None:
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after_idle(lambda: self.attributes("-topmost", False))
            self.focus_force()
        except Exception:
            pass

    def _build_ui(self) -> None:
        if hasattr(self, "main_container"):
            self.main_container.destroy()

        self.main_container = tk.Frame(self, bg=self.COLOR_BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        header = tk.Frame(self.main_container, bg=self.COLOR_BG)
        header.pack(fill=tk.X, pady=(0, 14))
        self._build_header(header)
        self._build_status_card()
        self._build_action_row()
        self._build_session_card()
        self._build_settings_card()
        self._build_footer()
        self._render_state()

    def _build_header(self, parent: tk.Widget) -> None:
        icon_path = os.path.join(self.assets_dir, "icon.png")
        try:
            if os.path.exists(icon_path):
                image = Image.open(icon_path).resize((46, 46), Image.Resampling.LANCZOS)
                self.header_icon = ImageTk.PhotoImage(image)
                tk.Label(parent, image=self.header_icon, bg=self.COLOR_BG).pack(
                    side=tk.LEFT, padx=(0, 12)
                )
        except Exception:
            pass

        text_frame = tk.Frame(parent, bg=self.COLOR_BG)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            text_frame,
            text=self._txt("title"),
            font=("Segoe UI", 19, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_BG,
        ).pack(anchor="w")
        tk.Label(
            text_frame,
            text=self._txt("subtitle"),
            font=("Segoe UI", 10),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_BG,
        ).pack(anchor="w")

        tk.Button(
            parent,
            text="EN" if self.current_lang == "TR" else "TR",
            command=self._toggle_language,
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD,
            activeforeground=self.COLOR_TEXT,
            activebackground=self.COLOR_BORDER,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side=tk.RIGHT, anchor="n")

    def _card(self, parent: tk.Widget, padding: int = 18) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=padding,
            pady=padding,
        )

    def _build_status_card(self) -> None:
        self.status_card = self._card(self.main_container, 20)
        self.status_card.pack(fill=tk.X, pady=(0, 12))
        self.lbl_status = tk.Label(
            self.status_card,
            font=("Segoe UI", 11, "bold"),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
        )
        self.lbl_status.pack(anchor="center")
        self.lbl_status_detail = tk.Label(
            self.status_card,
            font=("Segoe UI", 10),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
            wraplength=430,
            justify=tk.CENTER,
        )
        self.lbl_status_detail.pack(anchor="center", pady=(5, 12))
        tk.Label(
            self.status_card,
            text=self._txt("timer_title"),
            font=("Segoe UI", 10),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
        ).pack(anchor="center")
        self.lbl_timer = tk.Label(
            self.status_card,
            text="00:00:00",
            font=("Consolas", 36, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD,
        )
        self.lbl_timer.pack(anchor="center", pady=(2, 4))
        self.lbl_session_countdown = tk.Label(
            self.status_card,
            font=("Segoe UI", 10),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
        )
        self.lbl_session_countdown.pack(anchor="center")

    def _build_action_row(self) -> None:
        row = tk.Frame(self.main_container, bg=self.COLOR_BG)
        row.pack(fill=tk.X, pady=(0, 12))
        self.btn_toggle = tk.Button(
            row,
            command=self._toggle_engine,
            font=("Segoe UI", 12, "bold"),
            fg="#FFFFFF",
            bg=self.COLOR_ACTIVE,
            activeforeground="#FFFFFF",
            activebackground="#047857",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=13,
            takefocus=True,
        )
        self.btn_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        if self.config_data["ui"].get("show_reset_button", True):
            self.btn_reset = tk.Button(
                row,
                text=self._txt("btn_reset"),
                command=self._reset_timer,
                font=("Segoe UI", 10, "bold"),
                fg=self.COLOR_TEXT,
                bg="#374151",
                activeforeground=self.COLOR_TEXT,
                activebackground="#4B5563",
                relief=tk.FLAT,
                bd=0,
                padx=14,
                cursor="hand2",
                takefocus=True,
            )
            self.btn_reset.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.btn_reset = None

    def _build_session_card(self) -> None:
        self.session_card = self._card(self.main_container)
        self.session_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            self.session_card,
            text=self._txt("session_header"),
            font=("Segoe UI", 11, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD,
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self._set_session_display_value()
        self.session_menu = tk.OptionMenu(
            self.session_card,
            self.session_display_var,
            *self._preset_labels(),
            command=self._on_preset_selected,
        )
        self.session_menu.config(
            font=("Segoe UI", 10),
            fg=self.COLOR_TEXT,
            bg="#1E3A5F",
            activeforeground=self.COLOR_TEXT,
            activebackground="#1D4ED8",
            highlightthickness=0,
            relief=tk.FLAT,
            cursor="hand2",
            width=18,
        )
        self.session_menu["menu"].config(
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_PRIMARY,
            activeforeground="#FFFFFF",
        )
        self.session_menu.grid(row=1, column=0, sticky="ew", pady=(10, 4))

        self.custom_duration_entry = tk.Spinbox(
            self.session_card,
            from_=1,
            to=1440,
            textvariable=self.custom_duration_var,
            width=8,
            font=("Segoe UI", 10),
            fg=self.COLOR_TEXT,
            bg="#0F172A",
            insertbackground=self.COLOR_TEXT,
            buttonbackground="#334155",
            relief=tk.FLAT,
        )
        self.custom_duration_label = tk.Label(
            self.session_card,
            text=self._txt("custom_minutes"),
            font=("Segoe UI", 10),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
        )
        self.session_hint = tk.Label(
            self.session_card,
            text=self._txt("session_ends"),
            font=("Segoe UI", 9),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
            wraplength=410,
            justify=tk.LEFT,
        )
        self.session_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.session_card.grid_columnconfigure(0, weight=1)
        self._sync_custom_duration_visibility()

    def _build_settings_card(self) -> None:
        self.settings_card = self._card(self.main_container)
        self.settings_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            self.settings_card,
            text=self._txt("settings_header"),
            font=("Segoe UI", 11, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD,
        ).pack(anchor="w", pady=(0, 5))
        self.chk_display = self._checkbox(
            self.settings_card, self._txt("chk_display"), self.var_keep_display
        )
        self.chk_display.pack(anchor="w", pady=3)
        self.chk_system = self._checkbox(
            self.settings_card, self._txt("chk_system"), self.var_keep_system
        )
        self.chk_system.pack(anchor="w", pady=3)
        self.chk_heartbeat = self._checkbox(
            self.settings_card, self._txt("chk_heartbeat"), self.var_virtual_heartbeat
        )
        self.chk_heartbeat.pack(anchor="w", pady=3)
        self.heartbeat_hint = tk.Label(
            self.settings_card,
            text=self._txt("heartbeat_hint"),
            font=("Segoe UI", 9),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_CARD,
            justify=tk.LEFT,
            wraplength=410,
        )
        self.heartbeat_hint.pack(anchor="w", padx=(24, 0), pady=(0, 4))
        self.settings_hint = tk.Label(
            self.settings_card,
            font=("Segoe UI", 9, "italic"),
            fg=self.COLOR_WARNING,
            bg=self.COLOR_CARD,
            justify=tk.LEFT,
            wraplength=410,
        )
        self.settings_hint.pack(anchor="w", pady=(5, 0))

    def _checkbox(self, parent: tk.Widget, text: str, variable: tk.BooleanVar) -> tk.Checkbutton:
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=self._on_setting_changed,
            font=("Segoe UI", 10),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_CARD,
            activebackground=self.COLOR_CARD,
            activeforeground=self.COLOR_TEXT,
            selectcolor="#0F172A",
            disabledforeground="#64748B",
            bd=0,
            cursor="hand2",
            takefocus=True,
        )

    def _build_footer(self) -> None:
        footer = tk.Frame(self.main_container, bg=self.COLOR_BG)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(3, 0))
        tk.Label(
            footer,
            text=self._txt("shortcut"),
            font=("Segoe UI", 9),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_BG,
        ).pack(anchor="center")
        tk.Label(
            footer,
            text=self._txt("footer"),
            font=("Segoe UI", 9),
            fg=self.COLOR_MUTED,
            bg=self.COLOR_BG,
        ).pack(anchor="center", pady=(2, 0))

    def _preset_labels(self) -> list[str]:
        return [
            self._txt("preset_continuous"),
            self._txt("preset_30"),
            self._txt("preset_60"),
            self._txt("preset_120"),
            self._txt("preset_custom"),
        ]

    def _preset_label(self, key: str) -> str:
        return self._txt(f"preset_{key}")

    def _set_session_display_value(self) -> None:
        self.session_display_var.set(self._preset_label(self.session_preset_key))

    def _on_preset_selected(self, selected: str) -> None:
        key_by_label = {self._preset_label(key): key for key in (*PRESET_SECONDS.keys(), "custom")}
        self.session_preset_key = key_by_label.get(selected, "continuous")
        self._sync_custom_duration_visibility()
        self._on_setting_changed()

    def _sync_custom_duration_visibility(self) -> None:
        custom = self.session_preset_key == "custom"
        if custom:
            self.custom_duration_entry.grid(row=1, column=1, sticky="e", pady=(10, 4))
            self.custom_duration_label.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=(10, 4))
            self.session_hint.configure(text=self._txt("custom_hint"))
        else:
            self.custom_duration_entry.grid_remove()
            self.custom_duration_label.grid_remove()
            self.session_hint.configure(text=self._txt("session_ends"))

    def _toggle_language(self) -> None:
        if not self._event_allowed():
            return
        self.current_lang = "EN" if self.current_lang == "TR" else "TR"
        self.title(self._txt("title") + " v1.2.0")
        self._build_ui()
        self._persist_preferences()

    def _event_allowed(self) -> bool:
        if self.rate_limiter is None or self.rate_limiter.is_allowed():
            return True
        self.settings_hint.configure(text=self._txt("api_limit"), fg=self.COLOR_WARNING)
        return False

    def _get_duration_seconds(self) -> int | None:
        if self.session_preset_key in PRESET_SECONDS:
            return PRESET_SECONDS[self.session_preset_key]
        try:
            minutes = int(self.custom_duration_var.get().strip())
        except ValueError:
            return -1
        if 1 <= minutes <= 1440:
            return minutes * 60
        return -1

    def _toggle_engine(self) -> None:
        if not self._event_allowed():
            return
        if self.engine.is_active:
            self.engine.stop()
            self._persist_preferences()
            self._render_state()
            return
        if self.engine.needs_restore:
            self.engine.stop()
            self._render_state()
            return

        if not self.var_keep_display.get() and not self.var_keep_system.get():
            self._show_start_error(self._txt("no_protection"))
            return
        duration = self._get_duration_seconds()
        if duration == -1:
            self._show_start_error(self._txt("duration_invalid"))
            return
        result = self.engine.start(
            keep_display=self.var_keep_display.get(),
            keep_system=self.var_keep_system.get(),
            virtual_heartbeat=self.var_virtual_heartbeat.get(),
            duration_seconds=duration,
        )
        if not result.started:
            self._show_start_error(self._txt("start_failed"))
            return
        self._persist_preferences()
        self._render_state()

    def _show_start_error(self, message: str) -> None:
        self.lbl_status.configure(text=self._txt("error"), fg=self.COLOR_ERROR)
        self.lbl_status_detail.configure(text=message)
        self.status_card.configure(highlightbackground=self.COLOR_ERROR)
        messagebox.showwarning(self._txt("error"), message, parent=self)

    def _reset_timer(self) -> None:
        if self._event_allowed() and not self.engine.is_active:
            self.engine.reset_timer()
            self.lbl_timer.configure(text="00:00:00")

    def _scope_label(self) -> str:
        if self.engine.keep_display and self.engine.keep_system:
            return self._txt("scope_both")
        if self.engine.keep_system:
            return self._txt("scope_system")
        return self._txt("scope_display")

    def _render_state(self) -> None:
        active = self.engine.is_active
        if active:
            self.lbl_status.configure(text=f"● {self._txt('active')}", fg="#34D399")
            self.lbl_status_detail.configure(
                text=self._txt("status_scope").format(scope=self._scope_label())
            )
            self.status_card.configure(highlightbackground="#059669")
            self.btn_toggle.configure(
                text=self._txt("btn_stop"), bg=self.COLOR_STOP, activebackground=self.COLOR_STOP_HOVER
            )
            countdown = self.engine.remaining_seconds()
            if countdown is None:
                self.lbl_session_countdown.configure(text=self._txt("session_continuous"))
            else:
                end_time = self.engine.end_time.strftime("%H:%M") if self.engine.end_time else "—"
                self.lbl_session_countdown.configure(
                    text=self._txt("session_remaining").format(
                        end=end_time, remaining=format_seconds(countdown)
                    )
                )
        else:
            if self.engine.last_error:
                status = self._txt("error")
                detail = (
                    self._txt("restore_failed")
                    if self.engine.last_stop_reason
                    else self._txt("start_failed")
                )
                color = self.COLOR_ERROR
            elif self.engine.last_stop_reason == "completed":
                status = self._txt("completed")
                detail = self._txt("completed_message")
                color = self.COLOR_PRIMARY
            else:
                status = self._txt("inactive")
                detail = self._txt("settings_ready")
                color = self.COLOR_MUTED
            self.lbl_status.configure(text=f"○ {status}", fg=color)
            self.lbl_status_detail.configure(text=detail)
            self.status_card.configure(highlightbackground=self.COLOR_BORDER)
            if self.engine.needs_restore:
                self.btn_toggle.configure(
                    text=self._txt("btn_retry_restore"),
                    bg="#D97706",
                    activebackground="#B45309",
                )
            else:
                self.btn_toggle.configure(
                    text=self._txt("btn_start"), bg=self.COLOR_ACTIVE, activebackground="#047857"
                )
            self.lbl_session_countdown.configure(text=self._txt("session_ends"))

        state = tk.DISABLED if active or self.engine.needs_restore else tk.NORMAL
        cursor = "arrow" if state == tk.DISABLED else "hand2"
        for control in (self.chk_display, self.chk_system, self.chk_heartbeat, self.session_menu):
            control.configure(state=state, cursor=cursor)
        self.custom_duration_entry.configure(state=state)
        if self.btn_reset:
            self.btn_reset.configure(state=tk.DISABLED if active or self.engine.needs_restore else tk.NORMAL)
        self.settings_hint.configure(
            text=(
                self._txt("restore_failed")
                if self.engine.needs_restore
                else self._txt("settings_locked") if active else self._txt("settings_ready")
            ),
            fg=self.COLOR_WARNING if active or self.engine.needs_restore else self.COLOR_MUTED,
        )
        self._last_active_state = active

    def _update_timer_loop(self) -> None:
        self.engine.check_expiry()
        self.lbl_timer.configure(text=format_seconds(self.engine.elapsed_seconds()))
        if self.engine.is_active:
            countdown = self.engine.remaining_seconds()
            if countdown is not None:
                end_time = self.engine.end_time.strftime("%H:%M") if self.engine.end_time else "—"
                self.lbl_session_countdown.configure(
                    text=self._txt("session_remaining").format(
                        end=end_time, remaining=format_seconds(countdown)
                    )
                )
        if self.engine.is_active != self._last_active_state:
            self._render_state()
        if (
            self.engine.last_stop_reason == "completed"
            and not self.engine.last_error
            and self._completion_notice_session != self.engine.session_id
        ):
            self._completion_notice_session = self.engine.session_id
            self._render_state()
            messagebox.showinfo(
                self._txt("completed_title"), self._txt("completed_message"), parent=self
            )
        self.after(500, self._update_timer_loop)

    def _on_setting_changed(self) -> None:
        if not self.engine.is_active:
            self._persist_preferences()

    def _persist_preferences(self) -> None:
        geometry = self.geometry().split("+")[0]
        self.preferences_store.save(
            {
                "language": self.current_lang,
                "keep_display": self.var_keep_display.get(),
                "keep_system": self.var_keep_system.get(),
                "virtual_heartbeat": self.var_virtual_heartbeat.get(),
                "session_preset": self.session_preset_key,
                "custom_duration_minutes": self._safe_custom_minutes(),
                "geometry": geometry,
            }
        )

    def _safe_custom_minutes(self) -> int:
        try:
            return max(1, min(1440, int(self.custom_duration_var.get())))
        except ValueError:
            return 30

    def _on_window_configure(self, event: tk.Event) -> None:
        if event.widget is self and not self.engine.is_active:
            # Do not write on every pixel change; closing and setting changes save it.
            self.preferences["geometry"] = self.geometry().split("+")[0]

    def _on_closing(self) -> None:
        if self.engine.is_active and not messagebox.askyesno(
            self._txt("exit_title"), self._txt("exit_message"), parent=self
        ):
            return
        self.engine.stop()
        if self.engine.last_error:
            self._render_state()
            messagebox.showerror(self._txt("error"), self._txt("restore_failed"), parent=self)
            return
        self._persist_preferences()
        if self.single_instance_guard:
            self.single_instance_guard.release()
        self.destroy()


def main() -> None:
    config = load_config()
    guard = None
    if config.get("security", {}).get("single_instance_only", True):
        guard = SingleInstanceGuard()
        if not guard.acquire():
            root = tk.Tk()
            root.withdraw()
            language = config.get("ui", {}).get("default_language", "TR")
            text = LANGUAGES.get(language, LANGUAGES["TR"])
            messagebox.showwarning(text["already_running_title"], text["already_running_message"])
            root.destroy()
            guard.release()
            return

    app = StayAwakeApp(single_instance_guard=guard)
    app.mainloop()


if __name__ == "__main__":
    main()
