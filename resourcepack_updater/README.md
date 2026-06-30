# DynamicPack Resource Pack Updater

Bu klasör, mevcut resource pack zip dosyalarına DynamicPack desteği ekler ve bunları bir DynamicPack repo yapısına dönüştürür.

## Ne yapar?

- packs klasöründeki .zip paketlerine `dynamicmcpack.json` ekler
- paketleri `dynamic_repo/` klasörü altında bir repo yapısına hazırlar
- gerekli repo dosyalarını (`dynamicmcpack.repo.json`, `dynamicmcpack.repo.build` ve içerik dosyaları) üretir

## Kullanım

1. Paketinizi [resourcepack_updater/packs](packs) klasörüne yerleştirin.
2. Aşağıdaki komutu çalıştırın:

```bash
python add_dynamicpack.py
```

3. Üretilen dosyalar `resourcepack_updater/dynamic_repo/` klasöründe bulunur.

## Notlar

- `REPO_URL` değerini kendi sunucunuza veya GitHub Pages URL'nize göre güncelleyin.
- `dynamic_repo/` klasörü, DynamicPack modunun repo olarak kullanabileceği yapıyı içerir.
- Varsayılan ayar, imzalı doğrulama gerektirmeden çalışan bir repo yapısı üretir.
