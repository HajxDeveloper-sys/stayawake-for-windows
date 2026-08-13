# 📜 Changelog - StayAwake PC

All notable changes to the **StayAwake PC** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-13

### Added

- Added 30-minute, 1-hour, 2-hour and unlimited protection sessions.
- Added automatic session completion with Windows power-state restoration.
- Added live remaining time, exact end time and session progress feedback.
- Added an always-on-top preference and an `F8` start/stop shortcut.
- Added validated session defaults to `config.toml`.

### Changed

- Refined the dark interface hierarchy, labels, controls and active/completed states.
- Isolated mutex tests from a real running application instance for reliable local and CI runs.

---

## [1.1.1] - 2026-08-02

### 🔧 Bug Fixes & Improvements

#### Fixed
- **Version Consistency**: All in-code version strings (`AppUserModelID`, window title, footer) updated from `v1.0.0` to `v1.1.0` to match CHANGELOG and release tag.
- **README.md**: Fixed incorrect root directory name (`The VS Code/` → `stayawake-for-pc/`) and placeholder `git clone` URL updated to actual repository URL.

#### Added
- **Python < 3.11 Compatibility**: Added `tomli` fallback for `tomllib` module (standard library since Python 3.11) with descriptive error message for missing dependency.
- **Cross-Platform Guards**: All `ctypes.windll` calls in `main.py` wrapped with `sys.platform == 'win32'` checks to prevent `AttributeError` on non-Windows platforms.
- **`requirements-dev.txt`**: Separated development/CI dependencies (`bandit`, `pip-audit`) from runtime dependencies (`Pillow`, `tomli`).

#### Changed
- **`requirements.txt`**: Now contains only runtime dependencies. Added conditional `tomli` dependency for Python < 3.11.
- **`security-scan.yml`**: CI workflow updated to install from both `requirements.txt` and `requirements-dev.txt`.

---

## [1.1.0] - 2026-08-01

### 🛡️ Cyber Security & Anti-DDoS Enterprise Hardening

#### Added
- **Core Security Engine (`security.py`)**:
  - **Anti-DDoS Rate Limiter (`AntiDDoSController`)**: Token Bucket algorithm (10 token capacity, 2.0 refill rate/sec) protecting against UI event spamming, burst flooding, and DoS attacks.
  - **Single Instance Process Isolation (`SingleInstanceGuard`)**: Windows Kernel Named Mutex (`Global\StayAwakePC_SingleInstance_Mutex_v1`) to prevent Local DoS / Process Flooding attacks.
  - **Win32 DLL Search Hardening (`Win32SecurityManager`)**: Calls `SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32)` on startup to defeat DLL Hijacking / Preloading exploits (CWE-427).
  - **WAF & Payload Inspection Engine (`InputSanitizer`)**: Regex inspection blocking SQL Injection (SQLi), Cross-Site Scripting (XSS), Path Traversal (`../`), and Command Injection.
  - **Image Decompression Bomb Defense (`ImageBombProtector`)**: Pillow `MAX_IMAGE_PIXELS` set to 10,000,000 to prevent RAM exhaustion image bomb DoS attacks.
  - **TOML Config Schema Validator (`ConfigValidator`)**: Enforces strict schema, boolean type checks, string whitelists, and numeric bound clamps.
  - **File Checksum Integrity (`IntegrityVerifier`)**: SHA-256 file hashing module for asset/config tampering detection.
- **Automated CI/CD Security Workflows (`.github/workflows/`)**:
  - `codeql.yml`: GitHub CodeQL Static Application Security Testing (SAST) workflow.
  - `security-scan.yml`: Automated `bandit` SAST scanner and `pip-audit` dependency vulnerability scanner.
  - `dependabot.yml`: Daily automated dependency security update scanner.
- **Security Documentation**:
  - `SECURITY_ARCHITECTURE.md`: Detailed documentation of 7-Layer Defense-in-Depth architecture.
  - Updated `SECURITY.md` with STRIDE Threat Matrix and Anti-DDoS specifications.
- **Automated Security Verification Suite**:
  - `test_security.py`: Unit test suite testing all 7 security layers (passes 6/6 tests).

#### Changed
- `main.py`: Full integration of single-instance mutex guard, Win32 DLL search hardening, Anti-DDoS rate limiting, and config validation.
- `config.toml`: Added `[security]` section for configurable rate limits and single instance toggle.
- `requirements.txt`: Updated Pillow to `>=10.3.0` (fixing CVE-2023-4863 / CVE-2024-28219) and added `bandit` & `pip-audit`.

---

## [1.0.0] - 2026-08-01

### 🎉 Initial Release

#### Added
- **Core Engine (`SleepPreventer`)**:
  - Windows `SetThreadExecutionState` API integration via `ctypes`.
  - Continuous system and display keep-awake flags (`ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED`).
  - Daemon thread for background heartbeat & timer tracking.
  - Virtual heartbeat mouse movement simulation (`dx=0, dy=0`) every 45 seconds without stealing focus.
- **GUI Application (`StayAwakeApp`)**:
  - Modern Cyber Dark theme (`#0B0F19` background, `#111827` cards, `#06B6D4` cyan accents).
  - Prominent Toggle Switch Button with live color transitions.
  - Live HH:MM:SS timer counter updated every 500ms.
  - Dynamic status badge (`● AKTİF - UYKU MODU ENGELLENDİ` vs `○ PASİF - DORMANT MOD`).
  - Individual checkboxes for Display Protection, System Sleep Protection, and Virtual Heartbeat.
  - Window icon integration (PNG & ICO formats).
  - Safe exit confirmation prompt when application is active.
- **Automated Installer & Launchers**:
  - `install.bat`: Batch installer creating `venv` and installing dependencies.
  - `install.ps1`: PowerShell installer for virtual environment setup.
  - `run.bat`: One-click Batch launcher using `pythonw.exe`.
  - `run.ps1`: One-click PowerShell launcher.
- **Repository Documentation**:
  - `README.md` with badges, installation, architecture overview, and usage guide.
  - `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `ARCHITECTURE.md`, `FAQ.md`.
  - Enterprise-grade `.gitignore` and MIT `LICENSE`.
  - GitHub issue and pull request templates under `.github/`.
