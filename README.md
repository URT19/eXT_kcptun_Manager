<div align="center">

# 🚀 eXtreme KCPTun Manager v4.0

**مدیر پیشرفته تونل KCPTun با تجمیع HAProxy**

[![Version](https://img.shields.io/badge/version-4.0.0-blue?style=for-the-badge)](https://github.com/URT19/eXT_kcptun_Manager)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ubuntu](https://img.shields.io/badge/ubuntu-22.04%20%7C%2024.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

مدیر تونل **KCPTun** مبتنی بر **kcptun-rs** (Rust) با **تجمیع HAProxy**  
و معماری **مسیر/کانال (Route/Channel)** — طراحی‌شده برای مسیریابی ترافیک ایران ← خارج.

[📥 نصب](#-نصب) · [ویژگی‌ها](#-ویژگی‌ها) · [معماری](#-معماری) · [استفاده](#-استفاده)

</div>

---

## 📥 نصب

### پیش‌نیازها
- اوبونتو ۲۲.۰۴ / ۲۴.۰۴ (یا دبیان ۱۲+)
- دسترسی root
- پایتون ۳.۱۰+
- حداقل ۱ گیگابایت رم

### نصب سریع

```bash
git clone https://github.com/URT19/eXT_kcptun_Manager.git
cd eXT_kcptun_Manager
sudo bash install.sh
```

پس از نصب:

```bash
sudo frp-cli          # یا sudo kcptun-manager
```

دستورات نصب‌شده:
| دستور | توضیح |
|-------|--------|
| `frp-cli` / `kcptun-manager` | منوی اصلی |
| `kcptun-tuner` | رابط Auto-Tuner |
| `kcptun-uninstall` | حذف کامل |

---

## ✨ ویژگی‌ها

<table>
<tr>
<td width="50%">

### ⚡ موتور تونل
- پشتیبانی کامل از **kcptun-rs** (Rust — تا ۵× سریع‌تر از نسخه Go)
- Auto-Tuner پیشرفته (پورت پایتون از `kcptun-rs-optimizer`)
- پارامترهای قابل تنظیم: mode, mtu, sndwnd, rcvwnd, sockbuf, FEC, SMUX v2
- Pre-flight UDP check
- CPU diagnostic

### ⚖️ تجمیع HAProxy
- توزیع ترافیک روی چند کانال موازی
- تجمیع پهنای‌باند از چند سرور خارج
- Failover خودکار
- الگوریتم‌های Round-robin / leastconn / source

</td>
<td width="50%">

### 🎯 معماری Route/Channel
- **Simple Route**: یک کانال مستقیم
- **Balanced Route**: چند کانال + HAProxy
- ساخت Node + Route با ویزارد یکپارچه
- Export/Import فشرده (Compact) بین ایران و خارج

### 🎨 رابط کاربری
- دو زبانه (فینگلیش / انگلیسی)
- منوی رنگی و جداول وضعیت زنده
- پشتیبان‌گیری و ریست آسان
- بهینه‌سازی sysctl یک‌کلیکی

</td>
</tr>
</table>

---

## 🧠 معماری

```text
Client → Iran:Entry → HAProxy → N × kcptun-client → Kharej:kcptun-server → Xray/Target
```

| اصطلاح     | معنی                                                      |
|------------|-----------------------------------------------------------|
| **Hub**    | سرور ایران (kcptun-client + HAProxy اینجا اجرا می‌شود)   |
| **Node**   | سرور خارج (kcptun-server اینجا گوش می‌دهد)               |
| **Route**  | یک پورت عمومی روی Hub که به یک یا چند کانال نگاشت می‌شود |
| **Channel**| یک تونل kcptun تکی بین Hub و یک Node                     |

### حالت‌های Route

| حالت      | تعداد کانال | HAProxy | کاربرد                              |
|-----------|-------------|---------|-------------------------------------|
| Simple    | ۱           | ✗       | ترافیک سبک، راه‌اندازی سریع         |
| Balanced  | N (۲+)      | ✓       | پهنای‌باند بالا، HA، چند نود        |

---

## 🚀 شروع سریع

```bash
# ۱. نصب
sudo bash install.sh

# ۲. اجرا
sudo frp-cli

# ۳. استفاده از ویزارد (پیشنهادی)
# منوی [2] → پاسخ به سؤالات
```

جریان پیشنهادی:
1. `[1]` نصب باینری‌های kcptun-rs
2. `[2]` ویزارد → ساخت Node + Route
3. `[7]` خروجی Compact از ایران
4. روی سرور خارج: `[8]` وارد کردن Compact
5. `[9]` مدیریت کانال‌ها (Start/Stop)
6. `[10]` Auto-Tuner برای بهینه‌سازی پارامترها

---

## 📋 چیدمان منو

```text
  [ 1]  نصب KCPTun (kcptun-rs)
  [ 2]  ویزارد (سریع)                  ← پیشنهادی
  [ 3]  مدیریت Node-ها
  [ 4]  ساخت Simple Route
  [ 5]  ساخت Balanced Route
  [ 6]  مدیریت Route-ها
  [ 7]  خروجی برای Node (Compact)
  [ 8]  ورودی روی Node
  [ 9]  مدیریت Channel-ها
  [10]  Auto-Tuner
  [11]  تست سرعت
  [12]  بهینه‌سازی سیستم (sysctl)
  [13]  پشتیبان‌گیری
  [14]  ریست
  [15]  زبان (فینگلیش / انگلیسی)
  [16]  راهنما
  [17]  حذف نصب
  [ 0]  خروج
```

---

## 🎮 استفاده

```bash
sudo frp-cli              # منوی اصلی
sudo kcptun-manager       # همان منوی اصلی
sudo kcptun-tuner         # رابط Auto-Tuner مستقیم
sudo kcptun-uninstall     # حذف کامل
```

### خروجی و استقرار (Export / Import)

**روی Hub (ایران):**
```bash
sudo frp-cli
# منوی [7] → انتخاب نود → کپی خروجی Compact
```

**روی Node (خارج):**
```bash
sudo frp-cli
# منوی [8] → چسباندن Compact → خط خالی برای پایان
```

---

## 🔧 Auto-Tuner

ابزار هوشمند برای پیدا کردن بهترین ترکیب پارامترهای KCP:

- mode (fast3 / fast2 / fast / normal)
- MTU
- Send/Receive Window
- Socket Buffer
- FEC Data/Parity Shards
- SMUX version
- Compression

```bash
sudo kcptun-tuner
# یا از منوی [10]
```

---

## 📦 ساختار پروژه

```text
eXT_kcptun_Manager/
├── install.sh
├── pyproject.toml
├── README.md
└── kcptun_manager/
    ├── cli.py                 # منوی اصلی
    ├── models.py              # مدل‌های Node / Channel / Route
    ├── kcptun/                # منطق اصلی kcptun
    │   ├── builder.py
    │   ├── installer.py
    │   ├── deployer.py
    │   ├── systemd.py
    │   └── tuner.py           # Auto-Tuner
    ├── haproxy/               # ساخت و مدیریت HAProxy
    ├── system/                # شبکه، SSH، بهینه‌سازی
    ├── i18n/                  # ترجمه‌ها (fa / en)
    └── ui/                    # ویزارد، جداول، prompts
```

---

## 🛠️ عیب‌یابی

```bash
# نسخه
frp-cli --version

# وضعیت state
cat /opt/kcptun-manager/data/state.json

# سرویس‌ها
systemctl status 'kcptun-client-*' 'kcptun-server-*' haproxy-kcptun-agg

# لاگ زنده
journalctl -u 'kcptun-client-*' -f
journalctl -u 'kcptun-server-*' -f
```

---

## 📄 لایسنس

MIT

---

<div align="center">

ساخته‌شده با ❤️ برای جامعه ایرانی

</div>
