# 🤝 Contributing to Uyanık Kal / Stay Awake

**Creator / Geliştirici**: Hasan Aras DEMİR  
**Copyright © 2026 Hasan Aras DEMİR. Tüm Hakları Saklıdır. / All Rights Reserved.**

Thank you for your interest in contributing to **Uyanık Kal / Stay Awake**! We welcome contributions from developers of all skill levels.

---

## 📜 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

---

## 🛠️ How to Contribute

### 1. Reporting Bugs

Before creating a bug report, please check the [FAQ](FAQ.md) and open issues. If you find a new bug:
- Use the **Bug Report Template** (`.github/ISSUE_TEMPLATE/bug_report.md`).
- Provide clear steps to reproduce the issue, your Windows version, and Python version.

### 2. Suggesting Features

We welcome ideas for improving Uyanık Kal / Stay Awake!
- Use the **Feature Request Template** (`.github/ISSUE_TEMPLATE/feature_request.md`).
- Describe the feature, why it would be useful, and how you imagine it working.

### 3. Submitting Pull Requests (PRs)

1. **Fork the Repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/stayawake-pc.git
   cd stayawake-pc
   ```
3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Setup Environment**:
   Run `install.bat` or `install.ps1` to setup `venv` and dependencies.
5. **Make your changes**:
   - Follow PEP 8 guidelines for Python code.
   - Ensure GUI responsiveness and low CPU usage.
6. **Test your changes**:
   Run `python main.py` and verify all features (toggle, timer, status badge, checkbox options).
7. **Commit & Push**:
   ```bash
   git commit -m "feat: add amazing feature"
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request** against the `main` branch.

---

## 🎨 Code Style & Standards

- **Python**: PEP 8 compliance, clear function docstrings in Turkish/English.
- **Threading**: Always run non-UI long tasks in background daemon threads to prevent GUI freezing.
- **Win32 API**: Ensure all `ctypes` calls handle exceptions gracefully.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE) (Copyright © 2026 Hasan Aras DEMİR).
