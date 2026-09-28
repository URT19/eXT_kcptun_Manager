# راهنمای نصب و راه‌اندازی eXT_kcptun_Manager

## مرحله ۱: نصب اسکریپت روی هر دو سرور

روی **هر دو سرور** (ایران و خارج) دستورات زیر را اجرا کنید:

```bash
curl -fsSL -o kcptun-manager-pkg.tar.gz https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh
```

سپس برنامه را اجرا کنید:

```bash
sudo kcptun-manager
```

در اولین اجرا از شما نقش سرور را می‌پرسد (ایران یا خارج).

**مثال برای سرور ایران:**

```
1) IRAN   (relay + HAProxy + kcptun-client)
```

بعد از انتخاب، منو نمایش داده می‌شود و نقش مشخص می‌شود:

```
Role: IRAN
```

همین کار را برای سرور خارج انجام دهید:

```
Role: KHAREJ
```

---

## مرحله ۲: نصب و راه‌اندازی فایل‌ها

از منوی اصلی گزینه زیر را انتخاب کنید:

```
[ 1] Nasb / Initialize
```

این گزینه فایل‌های لازم را نصب می‌کند.

---

## مرحله ۳: پیکربندی روی سرور ایران

گزینه زیر را انتخاب کنید:

```
[ 2] Sakht connection jadid
```

### اطلاعات مورد نیاز

1. **اسم کانکشن**  
   مثال: `arvan21-hetzner56` (هر نامی می‌توانید بگذارید)

2. **آی‌پی سرور خارج**

   ```
   IP server kharej:
   ```

3. **پورت کانفیگ VPN روی سرور خارج** (پیش‌فرض `443`)

   ```
   Port target rooye kharej (mesl 443) [443]:
   ```

4. **پورت ورودی روی سرور ایران** (frontend HAProxy)  
   اگر می‌خواهید پورت متفاوتی باشد، عدد دیگری وارد کنید؛ در غیر این صورت همان پورت سرور خارج را بزنید.

   ```
   Port voroodi rooye IRAN (frontend HAProxy) [443]:
   ```

5. **تعداد تانل‌ها** (پیش‌فرض `4` – بین ۱ تا ۲۰)

   ```
   Tedad tunnel-ha [4]:
   ```

### تنظیمات kcptun

مقادیر پیش‌فرض را می‌توانید نگه دارید. برای پیدا کردن مقادیر بهینه می‌توانید از اسکریپت زیر استفاده کنید:  
[KCP_Tunnel_Benchmark](https://github.com/URT19/MyLinuxTools/tree/main/KCP_Tunnel_Benchmark)

نمونه مقادیر وارد شده:

```
Esme connection (a-z 0-9 _ -): arvan21-hetzner56
IP server kharej: 18.161.148.56
Port target rooye kharej (mesl 443) [443]:
Port voroodi rooye IRAN (frontend HAProxy) [443]:
Tedad tunnel-ha [4]:

[INFO] Tanzimate kcptun (Enter = default):
    crypt [aes-128]:
    mode [fast3]:
    mtu [1350]:
    sndwnd [1024]:
    rcvwnd [1024]:
    sockbuf [16777216]:
    nocomp (on/off) [on]:
    smuxver (1/2) [2]:
    fec (datashard/parityshard) [0/0]:
```

در انتها تأیید کنید:

```
Taeed mishe? (y/n) [y]:
```

کلید `Y` را بزنید.

پس از ساخت تانل‌ها این پیام نمایش داده می‌شود:

```
[INFO] Baraye enteghal be KHAREJ, az menu gozine 'Export' ra bezanid.
```

سپس گزینه زیر را انتخاب کنید:

```
[ 3] Export baraye KHAREJ
```

شماره اتصال مورد نظر را وارد کنید (مثلاً `1`). یک متن Base64 نمایش داده می‌شود که باید کپی کنید.

---

## مرحله ۴: پیکربندی روی سرور خارج

گزینه زیر را انتخاب کنید:

```
[ 2] Import data az IRAN
```

متن Base64 کپی‌شده را Paste کنید و Enter بزنید:

```
Base64 blob ra paste konid va Enter bezanid:
```

پس از اتمام، پیام موفقیت نمایش داده می‌شود. Enter بزنید.

**تانل آماده است.**  
در کانفیگ VPN خود به جای آی‌پی سرور خارج، **آی‌پی سرور ایران** را قرار دهید.

---

## تست سرعت تانل

### روی سرور خارج

1. گزینه `[10] Speedtest` را انتخاب کنید.
2. گزینه `1) Start server` را بزنید.
3. اتصال مورد نظر را انتخاب کنید.
4. حالت پورت را انتخاب کنید (معمولاً گزینه ۱):

```
Mode-e server:
  1) Port hamoon target (443)
  2) Port custom
  0) Cancel
Entekhab [1]: 1
```

### روی سرور ایران

1. گزینه `[11] Speedtest` را انتخاب کنید.
2. گزینه `1) Run test` را بزنید.
3. تأیید کنید که روی سرور خارج سرور تست را راه‌اندازی کرده‌اید (`Y`).
4. شماره اتصال را وارد کنید.
5. نوع تست را انتخاب کنید:

```
Noe-e test:
  1) Test-e HAProxy   (hame channel-ha az tarigh 127.0.0.1:443)
  2) Test-e channel-e tak (yek channel-e entekhabi)
  0) Cancel
Entekhab [1]:
```

6. مدت تست را وارد کنید (پیش‌فرض ۱۰ ثانیه).
7. تعداد استریم همزمان را وارد کنید (برای تست تجمیعی، حداقل برابر تعداد تانل‌ها بگذارید).

نمونه نتیجه:

```
Result   :    321.00 Mbit/s
```
```

render_file<file_path>/home/workdir/artifacts/README.md</file_path>