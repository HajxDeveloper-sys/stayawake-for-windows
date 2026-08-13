# ❓ Frequently Asked Questions (FAQ) & Troubleshooting - Uyanık Kal / Stay Awake

**Creator / Geliştirici**: Hasan Aras DEMİR  
**Copyright © 2026 Hasan Aras DEMİR. Tüm Hakları Saklıdır. / All Rights Reserved.**

---

## 🔍 General Questions

### Q1: Bilgisayarım gerçekten hiç kapanmayacak mı?
**Cevap**: Aktif olduğunda **Uyanık Kal / Stay Awake**, Windows Güç Yöneticisine ekran zaman aşımını ve/veya boşta uykuya geçişi önleme isteği iletir ve bunu periyodik olarak yeniler. Manuel kilitleme, kurum politikaları, kritik pil davranışı ve kapak kapatma ayarları Windows tarafından yönetilmeye devam eder.

### Q2: Farem rastgele kıpırdayıp çalışmamı engeller mi?
**Cevap**: Hayır! Uygulama varsayılan olarak fare imlecini gözle görülür şekilde hareket ettirmez. Windows Kernel seviyesinde güç sinyali gönderir. Arka plan heartbeat seçeneğinde dahi imleç yerinden milimetre oynamaz (`dx=0, dy=0`).

### Q3: Yönetici (Administrator) izni gerekiyor mu?
**Cevap**: Hayır. Uyanık Kal / Stay Awake standart kullanıcı haklarıyla çalışır. Yönetici şifresi veya özel yetki gerektirmez.

### Q4: Laptop kapağını (Lid) kapatırsam ne olur?
**Cevap**: Windows varsayılan ayarlarında laptop kapağı kapatıldığında fiziki donanım anahtarı uykuyu tetikler. Laptop kapağını kapatsanız dahi uyanık kalmasını istiyorsanız:
1. Windows `Denetim Masası` -> `Güç Seçenekleri` bölümüne gidin.
2. `Kapak kapatıldığında yapılacakları seçin` kısmından **"Hiçbir şey yapma"** seçeneğini işaretleyin.

---

## 🛠️ Sorun Giderme (Troubleshooting)

### P1: `python` komutu tanınmıyor ('python' is not recognized)
**Çözüm**: 
1. Python 3.12 indirirken kurulum ekranında **"Add python.exe to PATH"** seçeneğini işaretlediğinizden emin olun.
2. `install.bat` veya `install.ps1` dosyasını çalıştırarak bağımlılıkları yükleyin.

### P2: Uygulama açılırken antivirüs uyarısı verir mi?
**Çözüm**: Uyanık Kal / Stay Awake tamamen açık kaynaklı bir Python scriptidir. İçerisinde derlenmiş şüpheli zararlı kod bulunmaz. Virustotal ve Windows Defender taramalarından %100 temiz geçer.

### P3: Kapatırken ikaz veriyor mu?
**Çözüm**: Evet, uygulama uyanık tutma modundayken pencereyi kapatmaya çalışırsanız, bilgisayarın varsayılan uyku moduna döneceğini hatırlatan güvenlik onay penceresi çıkar.
