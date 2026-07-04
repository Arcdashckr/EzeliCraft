# EzeliCraft Modpack Updater

Bu klasör, EzeliCraft mod paketi için kullanılan akıllı güncelleyici arayüzünü ve ilgili yapılandırma dosyalarını içerir.

## Bu klasör ne işe yarar?

- Modpack güncelleme işlemini kullanıcı dostu bir GUI üzerinden yürütür.
- Uzak sunucudaki sürüm bilgilerini kontrol eder.
- Yeni modpack sürümü geldiğinde sadece değişen dosyaları indirip uygular.
- Eski veya kaldırılan dosyaları temizler.
- Oyuncunun kendi kaydettiği alanları koruyacak şekilde bazı klasörleri korur.

## Ana dosyalar

- updater.py: Ana güncelleyici arayüzü ve güncelleme mantığı.
- version.json: Uzak sürüm bilgileri, güncelleme linkleri, changelog ve silinecek dosyaların listesi.
- start.bat: PyInstaller ile .exe haline getirmek için hazırlanmış yardımcı betik.
- build/: Derlenmiş çıktıların saklandığı klasör.
- legacy/: Eski güncelleme scriptlerinin saklandığı klasör.

## Nasıl çalışır?

1. Program açılır.
2. GitHub üzerinden uzak sürüm bilgileri alınır.
3. Eğer güncelleyici sürümü eskiyse, yeni güncelleyici kendini indirip yenisiyle açılır.
4. Eğer modpack sürümü eskiyse, uzak sunucudan yeni patch dosyası indirilir.
5. Dosyalar güncellenir.
6. options.txt ayarları güncellenir.
7. Kaldırılan dosyalar temizlenir.
8. local_version.json dosyasına mevcut sürüm yazılır.

## Kurulum

### Python ile çalıştırma

Windows'ta şu şekilde başlatabilirsiniz:

- updater.py dosyasına çift tıklayabilirsiniz.
- Veya terminalde:

```powershell
python updater.py
```

Bu yöntem için ekstra paket kurmaya gerek yoktur; script standart Python kütüphanelerini kullanır.

### .exe haline getirme

Eğer kendi çalıştırılabilir dosyanızı oluşturmak istiyorsanız:

```powershell
pip install pyinstaller
start.bat
```

Bu işlem sonunda dist klasörü içinde çalıştırılabilir dosya oluşturulur.

## Önemli notlar

- version.json dosyası güncelleme mantığının kalbidir.
- local_version.json dosyası, bilgisayarda hangi sürümün yüklü olduğunu takip eder.
- Bazı klasörler koruma altına alınır. Bunlar arasında saves, screenshots, schematics ve xaero bulunur.
- Güncelleme sırasında oyuncu verileri kaybolmaması için bu klasörler değiştirilmez.

## options_compare klasörü ne işe yarar?

[options_compare](options_compare) klasörü, modpack güncellemesi sırasında `options.txt` dosyasında değişen anahtarları incelemek için kullanılır.

- [options_compare/compare.ps1](options_compare/compare.ps1): Eski ve yeni `options.txt` dosyalarını karşılaştırır.
- [options_compare/options_eski.txt](options_compare/options_eski.txt): Önceki ayarların kaydı.
- [options_compare/options_yeni.txt](options_compare/options_yeni.txt): Yeni ayarların kaydı.
- [options_compare/options_updates.json](options_compare/options_updates.json): Güncelleme sırasında uygulanacak ayar değişikliklerini içerir.
- [options_compare/changed_options.txt](options_compare/changed_options.txt): Karşılaştırma sonucunda fark edilen seçenekleri listeler.

Bu klasör sayesinde güncelleme sonrası hangi tuş atamalarının veya ayarların değiştiğini hızlıca görebilirsiniz.

## Hata alırsanız

- İnternet bağlantınızı kontrol edin.
- version.json dosyasının erişilebilir olduğundan emin olun.
- Python kurulumunun PATH'e ekli olduğundan emin olun.
- PyInstaller yoksa, önce kurulum adımını uygulayın.
