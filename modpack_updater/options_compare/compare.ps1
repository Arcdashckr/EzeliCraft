# Konsol ve dosya çıktılarını UTF-8 yapar
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$EskiDosya = "options_eski.txt"
$YeniDosya = "options.txt"
$RaporDosyasi = "changed_options.txt"
$JsonDosyasi = "options_updates.json"

if (-not (Test-Path $EskiDosya) -or -not (Test-Path $YeniDosya)) {
    Write-Host "Hata: Klasörde options_eski.txt ve options.txt bulunamadı!" -ForegroundColor Red
    Pause
    Exit
}

# Dosyaları UTF-8 olarak okuyan fonksiyon
function Oku-Options($Yol) {
    $Hash = @{}
    Get-Content $Yol -Encoding utf8 | ForEach-Object {
        if ($_ -match ":") {
            $Satir = $_.Split(":", 2)
            $Key = $Satir[0].Trim()
            $Val = $Satir[1].Trim()
            if ($Key -ne "") { $Hash[$Key] = $Val }
        }
    }
    return $Hash
}

$EskiAyarlar = Oku-Options $EskiDosya
$YeniAyarlar = Oku-Options $YeniDosya

# İnsanlar için okunabilir rapor listesi
$Rapor = @()
$Rapor += "=================================================="
$Rapor += "        OPTIONS.TXT KARŞILAŞTIRMA RAPORU        "
$Rapor += "=================================================="
$Rapor += ""

# version.json için sadece DEĞİŞEN ve YENİ EKLENEN tuş atamalarını tutacak obje
$JsonObjesi = [ordered]@{}

# Değişenleri ve Yeni Eklenenleri Bul
$YeniAyarlar.Keys | ForEach-Object {
    $Key = $_
    if (-not $EskiAyarlar.ContainsKey($Key)) {
        $Rapor += "[YENİ EKLENDİ] $Key : $($YeniAyarlar[$Key])"
        $JsonObjesi[$Key] = $YeniAyarlar[$Key] # JSON'a ekle
    } elseif ($EskiAyarlar[$Key] -ne $YeniAyarlar[$Key]) {
        $Rapor += "[DEĞİŞTİ] $Key : $($EskiAyarlar[$Key]) -> $($YeniAyarlar[$Key])"
        $JsonObjesi[$Key] = $YeniAyarlar[$Key] # JSON'a ekle (Yeni değeri gönderiyoruz)
    }
}

# Silinenleri Bul (Bunlar sadece raporda görünür, oyuncunun dosyasından bir şey silmeyiz)
$EskiAyarlar.Keys | ForEach-Object {
    $Key = $_
    if (-not $YeniAyarlar.ContainsKey($Key)) {
        $Rapor += "[SİLİNDİ] $Key : $($EskiAyarlar[$Key])"
    }
}

# 1. Metin Raporunu Kaydet
$Rapor | Out-File -FilePath $RaporDosyasi -Encoding utf8

# 2. JSON Dosyasını Kaydet (Süslü ve okunaklı formatta)
$JsonFormatli = ConvertTo-Json $JsonObjesi -Depth 10
$JsonFormatli | Out-File -FilePath $JsonDosyasi -Encoding utf8

# Ekrana başarı mesajı bas
Write-Host "İşlem tamamlandı!" -ForegroundColor Green
Write-Host "• İnsan raporu -> '$RaporDosyasi' dosyasına kaydedildi." -ForegroundColor Cyan
Write-Host "• JSON çıktısı -> '$JsonDosyasi' dosyasına kaydedildi." -ForegroundColor Yellow
Pause