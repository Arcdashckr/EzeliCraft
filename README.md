# EzeliCraft Repository

EzeliCraft SMP serisi ile alakalı teknik yazılımları içerir.</br>
SMP için hazırlanan modpack ve bunun güncellenmesini kolaylaştıran yardımcı araçlardan oluşan bir projedir.</br>
Bu repo, hem kullanıcıların modpack'i kurup güncellemesini sağlayan bir güncelleyici hem de Modrinth koleksiyonundan içerik listesi çıkarmak için bir scraper içerir.

## Proje yapısı

### 1. Modpack Updater

Klasör: [modpack_updater](modpack_updater)

Bu klasör, kullanıcıların modpack sürümünü güncellemesine yardımcı olur.

- [modpack_updater/updater.py](modpack_updater/updater.py): Ana güncelleme arayüzü ve mantığı.
- [modpack_updater/version.json](modpack_updater/version.json): Uzak sürüm bilgileri, güncelleme linkleri ve değişiklik notlarını tutar.
- [modpack_updater/start.bat](modpack_updater/start.bat): PyInstaller ile çalıştırılabilir dosya üretmek için kullanılan yardımcı betik.
- [modpack_updater/README.md](modpack_updater/README.md): Modpack updater kullanım rehberi ve açıklamaları.

Kullanıcılar bu klasördeki araç sayesinde yeni sürüm geldiğinde sadece gerekli dosyaları indirip güncelleyebilir.

### 2. Modrinth Collection Scraper

Klasör: [modrinth_collection_scraper](modrinth_collection_scraper)

Bu klasör, Modrinth üzerinden bir koleksiyon tarayıp içerikleri özetleyen Markdown dosyaları üretir.

- [modrinth_collection_scraper/index.js](modrinth_collection_scraper/index.js): Ana tarama mantığı.
- [modrinth_collection_scraper/package.json](modrinth_collection_scraper/package.json): Node.js bağımlılıkları ve çalıştırma komutları.
- [modrinth_collection_scraper/README.md](modrinth_collection_scraper/README.md): Collection Scraper kullanım rehberi ve açıklamaları.

Bu araç sayesinde mod, resource pack ve shader listeleri Obsidian, Discord veya GitHub paylaşımı için hazırlanabilir.

### Çıktı yapısı

Her koleksiyon artık aşağıdaki gibi bir klasör yapısı üretir:

```text
output/
  <koleksiyon-adi>/
    obsidian/
      mods.md / resourcepacks.md / shaders.md
    discord/
      kategori bazlı 2bin karakteri aşmayan .md dosyaları
    github/
      mods.md / resourcepacks.md / shaders.md
```

## İlk kez nasıl başlanır?

### A) Modpack güncelleyiciyi kullanmak istiyorsanız

1. [modpack_updater](modpack_updater) klasörüne gidin.
2. [modpack_updater/updater.py](modpack_updater/updater.py) dosyasını çalıştırın.
3. Arayüz açıldığında güncellemeleri kontrol edin.
4. Yeni sürüm varsa güncelleme düğmesine basın.

### B) Modrinth scraper'ı kullanmak istiyorsanız

1. [modrinth_collection_scraper](modrinth_collection_scraper) klasörüne gidin.
2. Klasörde Powershell ile bağımlılıkları yükleyin:

```powershell
npm install
```

3. Klasörün içindeki [start.bat](modrinth_collection_scraper/start.bat) çalıştırın.

    yada Powershell ile başlatın:

    ```powershell
    npm start
    ```

4. Ekrandaki seçeneklerden birini seçin:
   - 1 = Mod listesi
   - 2 = Resource pack listesi
   - 3 = Shader listesi

5. Çıktılar otomatik olarak ilgili klasörlere yazılır.

## Hangi dosyalar ne işe yarar?

- [modpack_updater/README.md](modpack_updater/README.md): Modpack güncelleyici işleyişini açıklar.
- [modrinth_collection_scraper/README.md](modrinth_collection_scraper/README.md): Scraper kullanım rehberini açıklar.
- [README.md](README.md): Repo genel giriş dokümantasyonu.

## Not

Bu repo iki farklı amaç için hazırlanmıştır:

- Minecraft oyuncularına güncel modpack deneyimi sunmak.
- Modrinth koleksiyonlarını düzenli ve paylaşılabilir dokümanlara dönüştürmek.
