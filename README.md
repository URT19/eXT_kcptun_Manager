# 🚀 eXtreme KCPTun Manager v4.0

**مدیر پیشرفته تونل KCPTun با تجمیع HAProxy**

## نصب

```bash
sudo bash install.sh
sudo frp-cli



ویژگی‌ها
پشتیبانی از kcptun-rs (Rust)

Auto-Tuner (پورت Python از kcptun-rs-optimizer-v4.1.sh)

تجمیع HAProxy

معماری Route/Channel

دو زبانه (فینگلیش / انگلیسی)

Pre-flight UDP check

CPU diagnostic

معماری
text
Client → Iran:Entry → HAProxy → N × kcptun-client → Kharej:kcptun-server → Xray
لایسنس
MIT

text

---

## 📋 مرحله ۱۰: چک‌لیست اجرا

1. **ساختار پوشه‌ها را بسازید:**
```bash
mkdir -p kcptun_manager/{kcptun,haproxy,system,i18n,ui}
فایل‌ها را به ترتیب زیر کپی کنید:

__init__.py, __main__.py, constants.py, config.py, models.py, state.py

kcptun/__init__.py, kcptun/builder.py, kcptun/installer.py, kcptun/deployer.py, kcptun/systemd.py, kcptun/tuner.py

haproxy/__init__.py, haproxy/builder.py, haproxy/service.py

system/__init__.py, system/net.py, system/ssh.py, system/optimize.py

i18n/__init__.py, i18n/en.py, i18n/fa.py

ui/__init__.py, ui/prompts.py, ui/tables.py, ui/wizard.py, ui/tuner_ui.py, ui/uninstall.py

cli.py

install.sh, pyproject.toml, README.md

نصب:

bash
sudo bash install.sh
sudo frp-cli
✅ مرحله ۱۱: تست
bash
# بررسی نسخه
frp-cli --version

# بررسی state
cat /opt/kcptun-manager/data/state.json

# بررسی سرویس‌ها
systemctl status 'kcptun-client-*' 'kcptun-server-*' haproxy-kcptun-agg

# بررسی لاگ‌ها
journalctl -u 'kcptun-client-*' -f
