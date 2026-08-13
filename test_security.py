import sys
import unittest
import uuid
from PIL import Image

from security import (
    Win32SecurityManager,
    SingleInstanceGuard,
    AntiDDoSController,
    InputSanitizer,
    ImageBombProtector,
    ConfigValidator
)
from main import format_duration

class TestStayAwakeSecurity(unittest.TestCase):

    def test_win32_dll_security(self):
        res = Win32SecurityManager.apply_dll_security()
        self.assertTrue(res or sys.platform != "win32")

    def test_image_bomb_protection(self):
        ImageBombProtector.apply_protection()
        self.assertEqual(Image.MAX_IMAGE_PIXELS, 10_000_000)

    def test_anti_ddos_rate_limiter(self):
        limiter = AntiDDoSController(max_tokens=5, refill_rate=1.0)
        allowed = [limiter.is_allowed() for _ in range(5)]
        self.assertTrue(all(allowed))
        
        self.assertFalse(limiter.is_allowed())

    def test_input_sanitizer_waf(self):
        safe_sqli, reason = InputSanitizer.is_payload_safe("SELECT * FROM users WHERE 1=1; DROP TABLE data;")
        self.assertFalse(safe_sqli)
        self.assertIn("SQL", reason)

        safe_xss, reason = InputSanitizer.is_payload_safe("<script>alert('pwned')</script>")
        self.assertFalse(safe_xss)
        self.assertIn("XSS", reason)

        safe_path, reason = InputSanitizer.is_payload_safe("../../etc/passwd")
        self.assertFalse(safe_path)
        self.assertIn("Path Traversal", reason)

        safe_cmd, reason = InputSanitizer.is_payload_safe("test; powershell -Command Start-Process mal.exe")
        self.assertFalse(safe_cmd)
        self.assertIn("Command Injection", reason)

        safe_normal, _ = InputSanitizer.is_payload_safe("Uyanık Kal Normal Configuration String")
        self.assertTrue(safe_normal)

    def test_config_validator(self):
        malicious_raw_config = {
            'ui': {
                'show_reset_button': "invalid_type",
                'default_language': 'HACKED_LANG'
            },
            'security': {
                'max_burst_capacity': 999999,
                'refill_rate_per_sec': -50.0
            }
        }
        validated = ConfigValidator.validate_config(malicious_raw_config)
        self.assertEqual(validated['ui']['show_reset_button'], True)
        self.assertEqual(validated['ui']['default_language'], 'TR')
        self.assertEqual(validated['security']['max_burst_capacity'], 100)
        self.assertEqual(validated['security']['refill_rate_per_sec'], 0.1)

    def test_session_preferences_are_validated(self):
        validated = ConfigValidator.validate_config({
            'protection': {
                'default_session_minutes': 60,
                'default_always_on_top': True
            }
        })
        self.assertEqual(validated['protection']['default_session_minutes'], 60)
        self.assertTrue(validated['protection']['default_always_on_top'])

        fallback = ConfigValidator.validate_config({
            'protection': {'default_session_minutes': 999}
        })
        self.assertEqual(fallback['protection']['default_session_minutes'], 0)

    def test_duration_formatting(self):
        self.assertEqual(format_duration(0), "00:00:00")
        self.assertEqual(format_duration(3661), "01:01:01")

    def test_single_instance_guard(self):
        mutex_name = f"Local\\StayAwakePC_Test_{uuid.uuid4()}"
        guard1 = SingleInstanceGuard(mutex_name=mutex_name)
        self.assertTrue(guard1.acquire())

        guard2 = SingleInstanceGuard(mutex_name=mutex_name)
        self.assertFalse(guard2.acquire())

        guard1.release()

if __name__ == '__main__':
    unittest.main()
