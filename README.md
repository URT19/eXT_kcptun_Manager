# kcptun-rs Manager

**نسخه پایدار و تست‌شده: `2.7.2`**

مدیر تونل kcptun با تجمیع HAProxy و رابط تعاملی (TUI).  
طراحی‌شده برای لینک **ایران ⇄ خارج (Kharej)**؛ سرور ایران به‌عنوان رله عمل می‌کند و ترافیک را از چند تونل kcptun به سرور خارج می‌فرستد.

[📥 نصب](#-نصب) · [🚀 راه‌اندازی سریع](#-راه‌اندازی-سریع) · [✨ قابلیت‌ها](#-قابلیت‌ها) · [⌨️ منو](#️-منو) · [🧠 معماری](#-معماری) · [📁 ساختار](#-ساختار-فایل‌ها)

> راهنمای تصویری و گام‌به‌گام تست‌شده: **[Setup_Help.md](Setup_Help.md)**

---

## 📥 نصب

### پیش‌نیازها

- Ubuntu 22.04 / 24.04 (یا Debian-based)
- دسترسی root
- `python3` 3.10+

### نصب سریع (پکیج رسمی)

**با curl:**

```bash
curl -fsSL -o kcptun-manager-pkg.tar.gz \
  https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh
sudo kcptun-manager
```

**با wget:**

```bash
wget https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh
sudo kcptun-manager
```

### نصب از گیت

```bash
git clone https://github.com/URT19/eXT_kcptun_Manager.git
cd eXT_kcptun_Manager
sudo bash install.sh
sudo kcptun-manager
```

### دستورات بعد از نصب

```bash
sudo kcptun-manager    # منوی تعاملی (TUI)
sudo kcptun            # میانبر همان منو
kcptun-manager version
kcptun-manager export [--name NAME] [--out DIR]
```

---

## 🚀 راه‌اندازی سریع

این خلاصهٔ همان جریان تست‌شده در [Setup_Help.md](Setup_Help.md) است. روی **هر دو سرور** (ایران و خارج) نصب را انجام دهید.

### ۱) انتخاب نقش

در اولین اجرا:

```text
1) IRAN   (relay + HAProxy + kcptun-client)
2) KHAREJ (exit + kcptun-server)
```

### ۲) Initialize (روی هر دو سرور)

منو → **`[1] Nasb / Initialize`**  
باینری‌های kcptun و قالب‌های systemd نصب می‌شوند.

### ۳) ساخت اتصال روی ایران

منو ایران → **`[2] Sakht connection jadid`**

نمونه ورودی‌ها:

| سؤال | مثال / پیش‌فرض |
|------|----------------|
| اسم connection | `arvan21-hetzner56` |
| IP سرور خارج | `x.x.x.x` |
| Port target روی خارج | `443` |
| Port ورودی ایران (HAProxy) | `443` |
| تعداد تونل‌ها | `4` (۱ تا ۲۰) |
| crypt / mode / mtu / ... | Enter = پیش‌فرض |

بعد از ساخت، منو → **`[3] Export baraye KHAREJ`** و blob را کپی کنید.

### ۴) Import روی خارج

منو خارج → **`[2] Import data az IRAN`**  
blob را paste کنید → Enter. سرویس‌های `kcptun-server` ساخته و بالا می‌آیند.

### ۵) استفاده

در کانفیگ کلاینت/پنل، به‌جای IP سرور خارج، **IP سرور ایران** و همان پورت frontend را بگذارید.

### ۶) تست سرعت (اختیاری)

1. **خارج** → `[10] Speedtest` → `1) Start server` → اتصال مورد نظر  
2. **ایران** → `[11] Speedtest` → `1) Run test` → تست HAProxy یا تک‌کانال  

جزئیات و اسکرین‌شات‌ها در [Setup_Help.md](Setup_Help.md).

---

## ✨ قابلیت‌ها

- **TUI تعاملی** با لوگو رنگی و منوی دوستونه
- **HAProxy** جلوی چند تونل kcptun (round-robin)
- **سرویس systemd جدا** برای هر کانال (main + test)
- **Speedtest** سه‌حالته: HAProxy تجمیعی / تک‌تونل / پورت دلخواه
- **Export / Import** متادیتای اتصال بین ایران و خارج
- **Backup نسخه‌بندی‌شده** (حداکثر ۲۰ نسخه برای هر فایل)
- **Export امن برنامه** بدون کلید، IP و state

---

## ⌨️ منو

### ایران (رله + HAProxy)

| #  | آیتم                    | بخش        |
|----|-------------------------|------------|
| 1  | Nasb / Initialize       | Setup      |
| 2  | Sakht connection jadid  | Setup      |
| 3  | Export baraye KHAREJ    | Setup      |
| 4  | List connection-ha      | Management |
| 5  | Edit connection         | Management |
| 6  | Namayesh config-ha      | Management |
| 7  | Hazf connection         | Management |
| 8  | kcptun-client services  | Services   |
| 9  | HAProxy                 | Services   |
| 10 | Firewall                | Services   |
| 11 | Speedtest               | Tools      |
| 12 | Migrate connection-ha   | Tools      |
| 13 | Backup / Restore        | Tools      |
| 14 | Taghir-e Role be KHAREJ | Tools      |

### خارج / Kharej (خروجی)

| #  | آیتم                    | بخش        |
|----|-------------------------|------------|
| 1  | Nasb / Initialize       | Setup      |
| 2  | Import data az IRAN     | Management |
| 3  | List connection-ha      | Management |
| 4  | Edit connection         | Management |
| 5  | Hazf connection         | Management |
| 6  | Namayesh config-ha      | Management |
| 7  | kcptun-server services  | Services   |
| 8  | Firewall                | Tools      |
| 9  | Backup / Restore        | Tools      |
| 10 | Speedtest               | Tools      |
| 11 | Taghir-e Role be IRAN   | Tools      |

---

## 🧠 معماری

```text
      users
        │
        ▼
   ┌─────────────┐     HAProxy (round-robin)    ┌──────────────────────┐
   │  :443       │ ──────► ch1 ──┐              │  kcptun-server@...   │
   │  HAProxy    │ ──────► ch2 ──┼── kcptun ──► │  127.0.0.1:443       │
   │  (IRAN)     │ ──────► ch3 ──┘   (KCP)      │  (target / Xray)     │
   └─────────────┘                              └──────────────────────┘
        Iran (relay)                               Kharej (exit)
```

هر connection شامل **N کانال** است:

- **تونل main** — ترافیک واقعی کاربران  
- **تونل test** — مخصوص Speedtest (iperf3)

---

## 📁 ساختار فایل‌ها

```text
/opt/kcptun-manager/              برنامه (پایتون + helper)
/opt/kcptun-manager/bin/          kcptun-client / kcptun-server
/opt/kcptun-manager/VERSION       نسخه (2.7.2)

/etc/kcptun-manager/              role + connections.json
/etc/kcptun-manager/instances/    فایل‌های .env هر تونل
/etc/haproxy/haproxy.cfg          کانفیگ تولیدشده HAProxy

/etc/systemd/system/kcptun-client@.service
/etc/systemd/system/kcptun-server@.service

/var/backups/kcptun-manager/      بک‌آپ‌های نسخه‌بندی‌شده
/var/lock/kcptun-manager.lock

/usr/local/bin/kcptun-manager
/usr/local/bin/kcptun
```

---

## 🔒 حریم خصوصی

دستور `kcptun-manager export` این موارد را **هرگز** داخل آرشیو نمی‌گذارد:

- `connections.json` و role  
- `instances/*.env`  
- `haproxy.cfg`  
- بک‌آپ‌ها، لاگ‌ها و فایل‌های `.b64`

آرشیو برنامه برای انتشار عمومی امن است.

---

## 📜 مجوز

MIT

---

**مخزن:** [github.com/URT19/eXT_kcptun_Manager](https://github.com/URT19/eXT_kcptun_Manager)  
**راهنمای تست‌شده:** [Setup_Help.md](Setup_Help.md)
