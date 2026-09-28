### روی 2 تا سرور دستورات زیر رو اجرا میکنیم تا اسکریپت نصب بشه


```
curl -fsSL -o kcptun-manager-pkg.tar.gz https://github.com/user-attachments/files/32732219/kcptun-manager-pkg.tar.gz
tar -xzf kcptun-manager-pkg.tar.gz
cd kcptun-pkg
sudo bash install.sh

```


```
sudo kcptun-manager
```

برای اولین بار اجرا از ما میخواد نقش سرور رو مشخص کنیم، سرور ایران هست یا خارج؟





<img width="578" height="215" alt="image" src="https://github.com/user-attachments/assets/7bd1de36-16b0-4915-9ae8-07306009516b" />

مثلا توی این مثال سرور ایران رو انتخاب میکنیم


```
1) IRAN   (relay + HAProxy + kcptun-client)
```

منو نشون داده میشه و مشخص شده که ایران هست

```
Role: IRAN
```

<img width="697" height="669" alt="image" src="https://github.com/user-attachments/assets/676c18bc-9990-47b1-a439-e09fcb9380de" />

همین کار رو هم برای سرور خارج انجام میدیم

```
Role: KHAREJ
```


----

### مرحله دوم، نصب و راه اندازی فایل ها

```
 [ 1] Nasb / Initialize
```

گزینه 1 رو وارد میکنیم تا فایل ها رو نصب کنه

<img width="707" height="239" alt="image" src="https://github.com/user-attachments/assets/984f4ec5-89af-4c0f-b672-9023ff47cfeb" />


----
### مرحله سوم، سرور ایران: 

گزینه 2 رو وارد میکنیم

```
[ 2] Sakht connection jadid
```

از ما اسم کانکشن رو میخواد، مثلا سرور ایران من اروان هست و سرور خارج من هتزنر، میذارم arvan21-hetzner56 ، هر اسمی میتونیید بذارید

بعد ازمون آی پی سرور خارج رو میخواد، وارد میکنیم

```
 IP server kharej:
```


مرحله بعد پورت کانفیگ vpn رو روی سرور خارج میپرسه، پیش فرض 443 هست، میتونید تغییر بدید به پورت کانفیگ خودتون
```
 Port target rooye kharej (mesl 443) [443]:
```

بعد پورت ورودی به سرور ایران رو میپرسه، اگر میخواید سرور ایران با پورت دیگری ترافیک رو رد کنه ، یه پورت دیگه ای متفاوت با سرور خارجتون بذارید ولی اگه نمیخواید پورت کانفیگ روی سرور ایران رو تغییر بدید، همون پورت مشابه کانفیگ روی سرور خارج رو وارد کنید

```
 Port voroodi rooye IRAN (frontend HAProxy) [443]:
```

بعد میپرسه، قراره ترافیک رو از چند تانل رد کنیم، پیش فرض 4 هست، میتونید از بین 1 تا 20 انتخاب کنید، بستگی به سرورتون داره

```
Tedad tunnel-ha [4]:
```

بعدی ها دیگه تنظیمات تامل هست، من همه مقادیر رو پیش فرض وارد میکنم، اگه مقادیر بهتری براتون جواب میده، خودتون تغییر بدید

در نهایت من اینا رو وارد کردم

```
····························································
  Sakht connection jadid (IRAN)
····························································
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
····························································

```
آخر سر ازتون میپرسه تایید میکنید؟
```
Taeed mishe? (y/n) [y]:
```

کلید Y رو بزنید میره برای ساخت تانل ها

پس از اتمام ساخت تانل ها و تنظیمات پیام زیر رو بهتون نشون میده

```
[INFO] Baraye enteghal be KHAREJ, az menu gozine 'Export' ra bezanid.
```

اینتر رو بزنید و بعدش وارد منوی شماره 3 بشید

```
[ 3] Export baraye KHAREJ
```

این منو برای گرفتن تنظیمات ساخته شده و وارد کردن اون توی سرور خارج هست

ازتون میخواد که با شماره مشخص کنید که کدوم اتصال رو میخواید وارد سرور خارج کنید؟

برای من شماره 1 هست و شماره 1 رو وارد میکنم
یه متن کد شده رو بهتون نشون میده که باید کپی کنید

<img width="905" height="419" alt="image" src="https://github.com/user-attachments/assets/444257e2-6e6f-45fa-8d1e-9f0bba310171" />


حالا به سرور خارج میریم

-----

### مرحله 4: سرور خارج



```
[ 2] Import data az IRAN
```

بعد ازتون میخواد اون متن کپی شده رو وارد کنید

```

  Entekhab: 2
····························································
  Import data az IRAN
····························································
  Base64 blob ra paste konid va Enter bezanid:

```


متن رو paste کنید و Enter بزنید
بعد از اون شروع میکنه به ساخت تانل ها و سرویس ها

اخر سر پیام موفقیت آمیز بودن رو نشون میده
<img width="726" height="463" alt="image" src="https://github.com/user-attachments/assets/466091f8-53b2-4f1f-a69e-efd4855e6346" />

Enter رو میزنید و تمام.

تانل ما ساخته شد، حالا اگر در کانفیگ بجای آی پی سرور خارج آی پی سرور ایران رو بذارید باید کار بده.


----


### تست سرعت تانل

از سرور خارج منوی 10 رو انتخاب کنید

```
[10] Speedtest
```
بعد

 ```
1) Start server            (vared shodan be halat server)
```

بعد میپرسه برای کدوم اتصال؟ اتصال مورد نظرتون رو انتخاب میکنید

```
2) arvan21-hetzner56       tunnels=4  target=-:443
```







```
 Mode-e server:
   1) Port hamoon target (443)
   2) Port custom
   0) Cancel
  Entekhab [1]: 1
```
گزینه 1 رو انتخاب میکنم


حالا میگه بر روی سرور ایران و بقیه کارا رو انجام بده



<img width="756" height="384" alt="image" src="https://github.com/user-attachments/assets/fd1e97df-a748-4cc1-bbcf-37cacf9de91b" />


به سرور ایران میریم و گزینه [11] Speedtest رو انتخاب میکنم

```
[11] Speedtest
```

بعد 
```
1) Run test

```

تاییدیه میخواد که آیا روی سرور خارج اوکی کردم یا نه؟ که میزنم Y

بعد ازت شماره اتصال رو میخواد ، وارد میکنیم
بعد ازت میپرسه تست رو بصورت تکی میخوای یا تجمیعی؟

```
  Noe-e test:
    1) Test-e HAProxy   (hame channel-ha az tarigh 127.0.0.1:443)
    2) Test-e channel-e tak (yek channel-e entekhabi)
    0) Cancel
  Entekhab [1]:
```
من گزینه 1 رو میزنم بصورت تجمیعی



بعدش مدت تست رو میخواد ، پیش فرض 10 ثاینه هست

```
Moddat (saniye) [10]:
```

بعد تعداد کانال های همزمان رو میخواد، پیشفرض 1 هست، ولی چون میخوام از همه کانال ها رد بشه ، حداقل تعداد خود کانال ها رو میذارم که برای اتصال من 4 تا کانال بود

```
Tedad stream (-P) [1]:
```

در نهایت نتیجه سرعت رو میزنه

<img width="639" height="645" alt="image" src="https://github.com/user-attachments/assets/a57a1c1a-5a35-496d-9f18-dd576a68d1e8" />



```
 Result   :    321.00 Mbit/s
```


