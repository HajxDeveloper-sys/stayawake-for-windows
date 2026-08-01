
import sys
import os
import re
import time
import ctypes
import hashlib
from typing import Dict, Any, Tuple, Optional
from PIL import Image

class Win32SecurityManager:
    
    @staticmethod
    def apply_dll_security() -> bool:
        if sys.platform != "win32":
            return True
        try:
            LOAD_LIBRARY_SEARCH_SYSTEM32 = 0x00000800
            result = ctypes.windll.kernel32.SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32)
            return bool(result)
        except Exception:
            return False

class SingleInstanceGuard:
    
    MUTEX_NAME = "Global\\StayAwakePC_SingleInstance_Mutex_v1"

    def __init__(self):
        self.mutex_handle = None
        self.is_already_running = False

    def acquire(self) -> bool:
        if sys.platform == "win32":
            try:
                ERROR_ALREADY_EXISTS = 183
                self.mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, self.MUTEX_NAME)
                last_error = ctypes.windll.kernel32.GetLastError()
                if last_error == ERROR_ALREADY_EXISTS:
                    self.is_already_running = True
                    return False
                return True
            except Exception:
                return True
        return True

    def release(self):
        if sys.platform == "win32" and self.mutex_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
            except Exception:
                pass

class AntiDDoSController:

    def __init__(self, max_tokens: int = 10, refill_rate: float = 2.0):
        self.max_tokens = float(max_tokens)
        self.refill_rate = float(refill_rate)
        self.tokens = float(max_tokens)
        self.last_refill = time.monotonic()

        self._client_buckets: Dict[str, Dict[str, Any]] = {}

    def is_allowed(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + (elapsed * self.refill_rate))
        self.last_refill = now

        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def is_client_allowed(self, client_ip: str, max_burst: int = 20, refill_per_sec: float = 5.0) -> bool:
        now = time.monotonic()
        if client_ip not in self._client_buckets:
            self._client_buckets[client_ip] = {
                'tokens': float(max_burst),
                'last_refill': now
            }

        bucket = self._client_buckets[client_ip]
        elapsed = now - bucket['last_refill']
        bucket['tokens'] = min(float(max_burst), bucket['tokens'] + (elapsed * refill_per_sec))
        bucket['last_refill'] = now

        if bucket['tokens'] >= 1.0:
            bucket['tokens'] -= 1.0
            return True
        return False

class InputSanitizer:

    XSS_PATTERN = re.compile(r"(<script.*?>|javascript:|onload=|onerror=|<iframe|<object|<embed)", re.IGNORECASE)
    SQLI_PATTERN = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|EXEC|TRUNCATE)\b|' OR '|' AND '|--|/\*)", re.IGNORECASE)
    PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\./|\.\.\\|/etc/passwd|c:\\windows)", re.IGNORECASE)
    CMD_INJECTION_PATTERN = re.compile(r"(&&|\|\||;|\$\(|`|powershell|cmd\.exe)", re.IGNORECASE)

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return ""
        clean_text = "".join(ch for ch in text if ord(ch) >= 32 or ch in ("\n", "\r", "\t"))
        return clean_text.strip()

    @classmethod
    def is_payload_safe(cls, payload: str) -> Tuple[bool, str]:
        if not isinstance(payload, str):
            return True, ""

        if cls.XSS_PATTERN.search(payload):
            return False, "XSS Script Injection pattern detected"
        if cls.SQLI_PATTERN.search(payload):
            return False, "SQL Injection pattern detected"
        if cls.PATH_TRAVERSAL_PATTERN.search(payload):
            return False, "Path Traversal pattern detected"
        if cls.CMD_INJECTION_PATTERN.search(payload):
            return False, "Command Injection pattern detected"

        return True, ""

class ImageBombProtector:

    MAX_PIXELS = 10_000_000

    @classmethod
    def apply_protection(cls):
        Image.MAX_IMAGE_PIXELS = cls.MAX_PIXELS

class ConfigValidator:

    ALLOWED_LANGUAGES = {"TR", "EN"}

    @classmethod
    def validate_config(cls, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        validated = {
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

        if not isinstance(raw_config, dict):
            return validated

        ui = raw_config.get('ui', {})
        if isinstance(ui, dict):
            if 'show_reset_button' in ui and isinstance(ui['show_reset_button'], bool):
                validated['ui']['show_reset_button'] = ui['show_reset_button']
            if 'default_language' in ui and isinstance(ui['default_language'], str):
                lang = ui['default_language'].upper().strip()
                if lang in cls.ALLOWED_LANGUAGES:
                    validated['ui']['default_language'] = lang
            if 'allow_resizable' in ui and isinstance(ui['allow_resizable'], bool):
                validated['ui']['allow_resizable'] = ui['allow_resizable']

        prot = raw_config.get('protection', {})
        if isinstance(prot, dict):
            if 'default_keep_display' in prot and isinstance(prot['default_keep_display'], bool):
                validated['protection']['default_keep_display'] = prot['default_keep_display']
            if 'default_keep_system' in prot and isinstance(prot['default_keep_system'], bool):
                validated['protection']['default_keep_system'] = prot['default_keep_system']
            if 'default_virtual_heartbeat' in prot and isinstance(prot['default_virtual_heartbeat'], bool):
                validated['protection']['default_virtual_heartbeat'] = prot['default_virtual_heartbeat']

        sec = raw_config.get('security', {})
        if isinstance(sec, dict):
            if 'rate_limit_enabled' in sec and isinstance(sec['rate_limit_enabled'], bool):
                validated['security']['rate_limit_enabled'] = sec['rate_limit_enabled']
            if 'max_burst_capacity' in sec and isinstance(sec['max_burst_capacity'], (int, float)):
                validated['security']['max_burst_capacity'] = max(1, min(100, int(sec['max_burst_capacity'])))
            if 'refill_rate_per_sec' in sec and isinstance(sec['refill_rate_per_sec'], (int, float)):
                validated['security']['refill_rate_per_sec'] = max(0.1, min(50.0, float(sec['refill_rate_per_sec'])))
            if 'single_instance_only' in sec and isinstance(sec['single_instance_only'], bool):
                validated['security']['single_instance_only'] = sec['single_instance_only']

        return validated

class IntegrityVerifier:

    @staticmethod
    def calculate_sha256(file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            return None
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None
