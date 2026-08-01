# 🔒 Cyber Security Policy & Threat Defense - Uyanık Kal / Stay Awake

**Creator / Geliştirici**: Hasan Aras DEMİR  
**Copyright © 2026 Hasan Aras DEMİR. Tüm Hakları Saklıdır. / All Rights Reserved.**

## Supported Versions

Below are the versions of Uyanık Kal / Stay Awake currently supported with security updates.

| Version | Supported          | Security Model |
| ------- | ------------------ | -------------- |
| 1.1.x   | :white_check_mark: | Hardened Cyber Security & Anti-DDoS v1 |
| 1.0.x   | :white_check_mark: | Legacy Release |
| < 1.0   | :x:                | Deprecated |

---

## 🛡️ Enterprise Security & Threat Defense Architecture

Uyanık Kal / Stay Awake is built with a zero-trust, defense-in-depth security model designed to withstand malicious attacks, resource exhaustion, process flooding, and privilege escalation:

### 1. 🛡️ Anti-DDoS & Event Flood Protection
- **Token Bucket Rate Limiter**: All user interface events and engine actions pass through `AntiDDoSController`. Rapid clicking, automated GUI flood scripts, or event burst spamming are rate-limited to protect CPU and memory from Denial-of-Service.
- **Circuit Breaker**: Protects application threads against resource exhaustion under heavy event spikes.

### 2. 🔐 Process Isolation & Single Instance Protection (Local DoS Defense)
- **Windows Kernel Named Mutex**: Implements `Global\StayAwakePC_SingleInstance_Mutex_v1` using native Win32 `CreateMutexW`.
- Prevents malicious actors or rogue scripts from spawning thousands of concurrent process instances to exhaust RAM/CPU (Local Process Flooding DoS).

### 3. 💉 Win32 DLL Search Path Hardening (Anti-DLL Hijacking)
- **DLL Preload Mitigation**: Calls `SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32)` on process startup.
- Ensures all Windows API calls (`kernel32.dll`, `user32.dll`, `shell32.dll`) resolve strictly from `%SystemRoot%\System32`, blocking DLL Hijacking / DLL Sideloading exploits.

### 4. 🧹 Input Sanitization & WAF Inspection Engine
- **Payload Inspection**: `InputSanitizer` scans inputs using regex rules to block SQL Injection (SQLi), Cross-Site Scripting (XSS), Path Traversal (`../`), and Command Injection attempts.
- **Control Character Filtering**: Removes null bytes and control characters to prevent Log Injection (CWE-117).

### 5. 💣 Image Decompression Bomb Mitigation
- **Pillow Pixel Bounds**: Sets `Image.MAX_IMAGE_PIXELS = 10,000,000` via `ImageBombProtector`.
- Defeats memory exhaustion exploits caused by malicious, high-resolution pixel bomb images.

### 6. ⚙️ TOML Config Schema Validation & File Integrity
- **Strict Schema Enforcement**: `ConfigValidator` verifies TOML data types, bounds, and string values against config file tampering.
- **SHA-256 Hashing**: `IntegrityVerifier` computes cryptographic hashes to detect unauthorized asset or configuration modification.

### 7. 🌐 Zero External Network Surface
- **100% Local / Offline**: No telemetry, no external HTTP/DNS queries, zero network attack surface.
- **Least Privilege**: Runs strictly under standard user context; requires zero Administrator elevation.

---

## 📊 STRIDE Threat Matrix

| Threat Category | Potential Attack Vector | Protection Implemented |
| --------------- | ---------------------- | ---------------------- |
| **Spoofing** | Rogue Process Spawning | Single Instance Windows Mutex (`Global\StayAwakePC_SingleInstance_Mutex_v1`) |
| **Tampering** | Config File Injection | `ConfigValidator` + SHA-256 Checksum Verification |
| **Repudiation** | Log Injection | `InputSanitizer` Null-Byte & Control Character Redaction |
| **Information Disclosure** | Path Leakage | Exception Sanitization & Offline Operating Model |
| **Denial of Service (DDoS)** | GUI Spamming / Process Flooding | `AntiDDoSController` Token Bucket & Single Instance Lock |
| **Elevation of Privilege** | DLL Sideloading | `SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32)` |

---

## 🐛 Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

1. **Do NOT open a public issue** on GitHub for security vulnerabilities.
2. Open a **Private Security Advisory** via GitHub Security Tab.
3. Include:
   - Description of the issue / vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### Disclosure Policy

- We will acknowledge receipt of your vulnerability report within **48 hours**.
- We will provide a timeline for addressing the vulnerability.
- Once fixed, a security advisory and patch release will be published.

Thank you for helping keep **Uyanık Kal / Stay Awake** safe, hardened, and trustworthy!
