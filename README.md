# kcptun-rs Manager

مدیر تونل چندپروتکلی با تجمیع HAProxy، تونل kcptun و رابط تعاملی (TUI).

طراحی‌شده برای استقرار لینک **ایران ⇄ خارج (Kharej)**؛ جایی که سرور ایران به‌عنوان رله عمل می‌کند و ترافیک کاربران را از طریق چند تونل kcptun به سرور خارج (خروجی / exit) می‌فرستد.

**نسخه فعلی:** `2.7.2`

---

## قابلیت‌ها

- **رابط تعاملی (TUI)** با لوگو رنگی، منوی دوستونه و تأیید تک‌کلیدی
- **HAProxy** در جلوی چند تونل kcptun برای توزیع بار (round-robin)
- **سرویس‌های systemd جداگانه** برای هر تونل (کانال اصلی + کانال تست)
- **منوی Speedtest** با سه حالت:
  - تست نود از طریق HAProxy (همه کانال‌ها با هم)
  - تست تک‌تونل (اصلی یا تست)
  - تست پورت دلخواه
- **بک‌آپ نسخه‌بندی‌شده** از هر فایلی که تغییر می‌کند (حداکثر ۲۰ نسخه برای هر فایل)
- **Export / Import** متادیتای اتصال بین ایران و خارج
- **CLI مستقل** (`kcptun-manager export`) برای بسته‌بندی ابزار روی سرور جدید
- **بدون داده خصوصی در export** — کلیدها، IPها و وضعیت اتصالات حذف می‌شوند

---

## پیش‌نیازها

- Ubuntu 22.04 / 24.04 (یا هر توزیع مبتنی بر Debian)
- `python3` (۳.۱۰ به بالا)، `curl`، `wget`، `unzip`، `iperf3`، `iproute2`
- برای نقش ایران: `haproxy`
- دسترسی root

نصب‌کننده این وابستگی‌ها را به‌صورت خودکار نصب می‌کند.

---

## نصب

### روش ۱ — با اسکریپت `install.sh` (پیشنهادی)

فایل `install.sh` را همراه با آرشیو روی سرور جدید قرار دهید و اجرا کنید:

```bash
# آرشیو و install.sh را در /root کپی کنید، سپس:
chmod +x install.sh
sudo ./install.sh /root/kcptun-manager-export-v2.7.2-*.tar.gz
```

اسکریپت خودش extract، نصب وابستگی‌ها، ساخت پوشه‌ها، reload سرویس‌ها و ساخت دستور سراسری را انجام می‌دهد.

### روش ۲ — دستی از روی tar.gz

**روی سرور مبدأ (اختیاری — برای ساخت آرشیو):**

```bash
kcptun-manager export
# خروجی: /root/kcptun-manager-export-vX.Y.Z-YYYYMMDD-HHMMSS.tar.gz
```

**کپی به سرور جدید:**

```bash
scp /root/kcptun-manager-export-*.tar.gz root@NEW_SERVER:/root/
```

**روی سرور جدید:**

```bash
# (الف) استخراج
cd / && tar -xzf /root/kcptun-manager-export-*.tar.gz

# (ب) نصب وابستگی‌ها
apt-get update
apt-get install -y python3 curl wget unzip iperf3 haproxy iproute2

# (ج) ساخت پوشه‌های اجرایی
mkdir -p /etc/kcptun-manager/instances
mkdir -p /etc/kcptun-manager/haproxy
mkdir -p /opt/kcptun-manager/bin
mkdir -p /var/lock /var/backups/kcptun-manager

# (د) بارگذاری مجدد systemd
systemctl daemon-reload

# (ه) اجرای مدیر
python3 -u /opt/kcptun-manager/kcptun_manager.py
```

در اولین اجرا نقش را انتخاب کنید (**IRAN** یا **KHAREJ**)، سپس از گزینه **۱) نصب / Initialize** برای دریافت باینری‌های kcptun استفاده کنید.

### دستور سراسری (اختیاری)

```bash
cat > /usr/local/bin/kcptun << 'EOF'
#!/usr/bin/env bash
exec python3 -u /opt/kcptun-manager/kcptun_manager.py "$@"
EOF
chmod +x /usr/local/bin/kcptun

# بعد فقط بنویسید:
kcptun
```

برای CLI کامل‌تر:

```bash
cat > /usr/local/bin/kcptun-manager << 'EOF'
#!/usr/bin/env bash
exec python3 -u /opt/kcptun-manager/cli.py "$@"
EOF
chmod +x /usr/local/bin/kcptun-manager
```

---

## CLI

```bash
kcptun-manager export [--name NAME] [--out DIR] [--quiet]
kcptun-manager version
kcptun-manager help
kcptun-manager                # اجرای منوی تعاملی
```

دستور `export` فایل  
`/root/kcptun-manager-<name>-v<version>-<ts>.tar.gz`  
می‌سازد که فقط برنامه را شامل می‌شود — بدون کلید، بدون IP و بدون وضعیت اتصالات. دستورات نصب روی سرور جدید هم چاپ می‌شود.

---

## نمای کلی منو

### ایران (رله / سمت HAProxy)

| #  | آیتم                      | بخش        |
|----|---------------------------|------------|
| 1  | نصب / Initialize          | Setup      |
| 2  | ساخت connection جدید      | Setup      |
| 3  | Export برای KHAREJ        | Setup      |
| 4  | لیست connectionها         | Management |
| 5  | ویرایش connection         | Management |
| 6  | نمایش configها            | Management |
| 7  | حذف connection            | Management |
| 8  | سرویس‌های kcptun-client   | Services   |
| 9  | HAProxy                   | Services   |
| 10 | Firewall                  | Services   |
| 11 | Speedtest                 | Tools      |
| 12 | مهاجرت connectionها       | Tools      |
| 13 | Backup / Restore          | Tools      |
| 14 | تغییر نقش به KHAREJ       | Tools      |

### خارج / Kharej (سمت خروجی)

| #  | آیتم                      | بخش        |
|----|---------------------------|------------|
| 1  | نصب / Initialize          | Setup      |
| 2  | Import داده از IRAN       | Management |
| 3  | لیست connectionها         | Management |
| 4  | ویرایش connection         | Management |
| 5  | حذف connection            | Management |
| 6  | نمایش configها            | Management |
| 7  | سرویس‌های kcptun-server   | Services   |
| 8  | Firewall                  | Tools      |
| 9  | Backup / Restore          | Tools      |
| 10 | Speedtest                 | Tools      |
| 11 | تغییر نقش به IRAN         | Tools      |

---

## ساختار فایل‌ها

```
/opt/kcptun-manager/              برنامه (کد پایتون + helperها)
/opt/kcptun-manager/bin/          باینری‌های kcptun-client و kcptun-server
/opt/kcptun-manager/VERSION       نسخه فعلی

/etc/kcptun-manager/              داده‌های زمان اجرا (نقش، connections.json)
/etc/kcptun-manager/instances/    فایل‌های .env هر تونل
/etc/haproxy/haproxy.cfg          کانفیگ تولیدشده HAProxy

/etc/systemd/system/kcptun-client@.service
/etc/systemd/system/kcptun-server@.service

/var/backups/kcptun-manager/      بک‌آپ‌های نسخه‌بندی‌شده
/var/lock/kcptun-manager.lock     قفل انحصاری

/usr/local/bin/kcptun-manager     نقطه ورود CLI
/usr/local/bin/kcptun             میانبر → TUI
```

---

## معماری

```
      کاربران
        │
        ▼
   ┌─────────────┐     HAProxy (round-robin)    ┌──────────────────────┐
   │  :443       │ ──────► 31000 ──┐            │  kcptun-server@...   │
   │  HAProxy    │ ──────► 31001 ──┼── kcptun ─►│  127.0.0.1:443       │
   │             │ ──────► 31002 ──┘   (KCP)    │  (سرویس مقصد)        │
   │             │ ──────► 31003 ──┐            └──────────────────────┘
   └─────────────┘                │
   ایران (رله)                 تونل‌های kcptun    خارج (خروجی)
```

هر connection شامل **N کانال** است. هر کانال دو تونل دارد:

- **تونل اصلی (main)** — ترافیک واقعی کاربران (معمولاً به Xray)
- **تونل تست (test)** — مخصوص speedtest (به iperf3)

---

## امنیت و حریم خصوصی

دستور `export` هرگز این موارد را شامل نمی‌شود:

- `connections.json`
- فایل نقش (role)
- `instances/*.env`
- `haproxy.cfg`
- بک‌آپ‌ها، لاگ‌های موقت یا فایل‌های `.b64`

بنابراین آرشیو برای انتشار عمومی امن است.

---

## نسخه‌بندی

برای تغییر نسخه:

```bash
python3 -c "
import sys; sys.path.insert(0,'/opt/kcptun-manager')
from lib.backup import set_version, get_version
set_version('2.8.0')
print(get_version())
"
```

- **patch** — رفع باگ
- **minor** — قابلیت جدید
- **major** — تغییر ساختاری

---

## مجوز

MIT
