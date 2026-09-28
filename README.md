# 🚀 eXtreme KCPTun Manager v4.0

**مدیر پیشرفته تونل KCPTun با تجمیع HAProxy**

[![Version](https://img.shields.io/badge/version-4.0.0-blue?style=for-the-badge)](https://github.com/URT19/eXT_kcptun_Manager)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ubuntu](https://img.shields.io/badge/ubuntu-22.04%20%7C%2024.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

مدیر تونل **KCPTun** مبتنی بر **kcptun-rs** (Rust) با **تجمیع HAProxy**  
و معماری **مسیر / کانال (Route / Channel)** — طراحی‌شده برای مسیریابی ترافیک **ایران ← خارج**.

[📥 نصب](#-نصب) · [✨ ویژگی‌ها](#-ویژگی‌ها) · [🧠 معماری](#-معماری) · [⌨️ منو](#️-منو) · [📁 ساختار](#-ساختار-فایل‌ها)

---

## 📥 نصب

### پیش‌نیازها

- اوبونتو ۲۲.۰۴ / ۲۴.۰۴ (یا دبیان ۱۲+)
- دسترسی root
- پایتون ۳.۱۰+

### نصب سریع (پکیج)

**با wget:**

```bash
wget https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh
sudo kcptun-manager
```

**با curl:**

```bash
curl -fsSL -o kcptun-manager-pkg.tar.gz https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh
sudo kcptun-manager
```

----


### پس از نصب

در اولین اجرا نقش را انتخاب کنید (**IRAN** یا **KHAREJ**)، سپس گزینه **۱ (Initialize)** را بزنید تا باینری‌های kcptun دریافت شوند.

```bash
# میانبر TUI
sudo kcptun

# نسخه
kcptun-manager version
```

---

## ✨ ویژگی‌ها

| ⚡ موتور تونل | ⚖️ تجمیع HAProxy | 🎯 تجربه کاربری |
|---|---|---|
| پشتیبانی کامل از **kcptun-rs** (Rust) | توزیع ترافیک روی چند کانال موازی | ویزارد سریع Node + Route |
| Auto-Tuner (بهینه‌ساز mode / mtu / window / sockbuf) | تجمیع پهنای‌باند از چند سرور خارج | دو زبانه (فینگلیش / انگلیسی) |
| پارامترها: mode, mtu, sndwnd, rcvwnd, sockbuf, FEC, SMUX v2 | Failover خودکار | Export/Import فشرده بین ایران و خارج |
| Pre-flight UDP check | Round-robin / leastconn / source | Backup وضعیت و Reset |
| CPU diagnostic | مسیر ساده و مسیر متوازن (Balanced) | بهینه‌سازی sysctl سیستم |

---

## 🧠 معماری

```text
Client → Iran:Entry → HAProxy → N × kcptun-client → Kharej:kcptun-server → Xray / Target
```

| اصطلاح      | معنی                                                              |
|-------------|-------------------------------------------------------------------|
| **Hub**     | سرور ایران — اینجا `kcptun-client` و HAProxy اجرا می‌شود         |
| **Node**    | سرور خارج — اینجا `kcptun-server` گوش می‌دهد                     |
| **Route**   | یک پورت عمومی روی Hub که به یک یا چند کانال نگاشت می‌شود         |
| **Channel** | یک تونل kcptun تکی بین Hub و یک Node                             |

- **Simple Route**: یک کانال به یک Node  
- **Balanced Route**: چند کانال موازی (تجمیع با HAProxy)

---

## ⌨️ منو

```
  [ 1] نصب باینری‌ها              [10] Auto-Tuner
  [ 2] ویزارد                     [11] Speedtest
  [ 3] مدیریت Nodeها              [12] بهینه‌سازی سیستم
  [ 4] مسیر ساده (Simple)         [13] Backup
  [ 5] مسیر متوازن (Balanced)     [14] Reset
  [ 6] لیست Routeها               [15] زبان (fa/en)
  [ 7] Export (برای خارج)         [16] راهنما
  [ 8] Import (از ایران)          [17] Uninstall
  [ 9] مدیریت Channelها           [ 0] خروج
```

### جریان پیشنهادی

1. روی **ایران (Hub)**: گزینه `1` → نصب باینری‌ها  
2. گزینه `2` (ویزارد) یا دستی: Node + Route بسازید  
3. گزینه `7` → Export فشرده را کپی کنید  
4. روی **خارج (Node)**: گزینه `8` → Import و راه‌اندازی سرور  
5. در صورت نیاز گزینه `10` (Auto-Tuner) برای یافتن بهترین پارامترها  

---

## 📁 ساختار فایل‌ها

```text
/opt/kcptun-manager/
├── bin/                    # باینری‌های kcptun-client / kcptun-server
├── data/
│   ├── state.json          # وضعیت (nodes, routes, channels)
│   ├── configs/
│   ├── haproxy/
│   ├── exports/
│   ├── backups/
│   ├── logs/
│   └── env/
├── venv/                   # محیط مجازی پایتون
└── kcptun_manager/         # کد برنامه

/usr/local/bin/
├── kcptun-manager          # نقطه ورود اصلی
├── frp-cli                 # نام مستعار
├── kcptun-tuner            # اجرای مستقیم Tuner
└── kcptun-uninstall        # حذف نصب
```

---

## 🔧 دستورات مفید

```bash
# وضعیت سرویس‌ها
systemctl status 'kcptun-client-*' 'kcptun-server-*' haproxy-kcptun-agg

# لاگ زنده
journalctl -u 'kcptun-client-*' -f

# فایل وضعیت
cat /opt/kcptun-manager/data/state.json

# بک‌آپ دستی (از داخل منو هم موجود است)
ls /opt/kcptun-manager/data/backups/
```

---

## 🔒 حریم خصوصی

- کلیدها و آدرس Nodeها فقط در `state.json` و فایل‌های env محلی ذخیره می‌شوند.
- Export فشرده فقط متادیتای لازم برای راه‌اندازی سمت خارج را منتقل می‌کند.
- کد منبع و آرشیو انتشار عمومی نباید شامل `data/` یا فایل‌های `.env` واقعی باشد.

---

## ⚠️ نکات و ایرادهای فعلی مخزن

مواردی که در کد/README فعلی گیت‌هاب دیده می‌شود و بهتر است قبل از انتشار عمومی رفع شوند:

1. **نام `frp-cli`** — از پروژه FRP کپی شده؛ بهتر است فقط `kcptun-manager` رسمی باشد (نام مستعار اختیاری بماند).
2. **منوهای ۴، ۵ و ۱۱** در `HANDLERS` هنوز handler ندارند (`simple_route`, `balanced_route`, `speedtest`).
3. **README قبلی** ناقص بود و چک‌لیست ساخت پروژه داخلش مانده بود — با این نسخه جایگزین شود.
4. وابستگی به toolchain راست برای ساخت باینری در گزینه ۱ باید در مستندات شفاف باشد.

---

## 📜 مجوز

MIT

---

**مخزن:** [github.com/URT19/eXT_kcptun_Manager](https://github.com/URT19/eXT_kcptun_Manager)
