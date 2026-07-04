# Modrinth Collection Scraper

Bu klasör, Modrinth koleksiyonlarından mod, resource pack veya shader listelerini çekip düzenli Markdown dosyaları halinde üretir.

## Bu klasör ne işe yarar?

- Birden fazla Modrinth koleksiyonunu tek seferde işler.
- Her koleksiyon için ayrı bir çıktı klasörü oluşturur.
- Obsidian için düzenli bir bilgi sayfası üretir.
- Discord paylaşımı için parçalı Markdown dosyaları hazırlar.
- Aynı koleksiyon adıyla tekrar çalıştırıldığında mevcut çıktıları günceller.

## Hızlı başlangıç

### 1) Gereksinimler

- Node.js kurulu olmalı.
- npm kurulu olmalı.

### 2) Bağımlılıkları yükleyin

Bu klasörde terminal açın:

```powershell
npm install
```

### 3) Koleksiyonları tanımlayın

[collections.txt](collections.txt) dosyasına alt alta sadece koleksiyon URL'lerini yazın.

Desteklenen format:

```text
https://modrinth.com/collection/SLUG
```

Örnek:

```text
https://modrinth.com/collection/K3ej09Af
https://modrinth.com/collection/ABC123
```

### 4) Çalıştırın

Windows'ta en kolay yöntem:

```powershell
start.bat
```

Alternatif olarak:

```powershell
npm start
```

veya

```powershell
node index.js
```

## Çıktı yapısı

Her koleksiyon için şu klasör yapısı oluşturulur:

```text
output/
  <koleksiyon-adi>/
    obsidian/
      mods.md veya resourcepacks.md veya shaders.md
    discord/
      kategori bazlı .md dosyaları
    github/
      mods.md / resourcepacks.md / shaders.md
```

Aynı koleksiyon adıyla tekrar çalıştırıldığında, ilgili klasörlerin içeriği güncellenir.

## Seçenekler

Scraper çalıştırıldığında konsolda bir seçim ekranı görünür. Buradan şu seçenekleri belirleyebilirsiniz:

- mods
- resourcepacks
- shaders
- all

`all` seçildiğinde koleksiyon linki doğrudan kullanılır ve karışık bir liste oluşturulur. Diğer seçeneklerde ise URL sonuna ilgili suffix eklenir ve o şekilde scrape edilir.

Ayrıca çıktı klasörlerinde hangi scrape modu kullanıldığı da belirtilir.

## Sorun yaşarsanız

- Node.js sürümünün güncel olduğundan emin olun.
- npm install komutunun başarıyla tamamlandığını kontrol edin.
- Modrinth sitesine erişiminizin olduğunu doğrulayın.
- Puppeteer ilk çalıştırmada tarayıcı dosyalarını yükleyebilir; bu işlem birkaç dakika sürebilir.
