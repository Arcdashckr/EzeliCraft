$EskiDosya = "options_eski.txt"
$YeniDosya = "options_yeni.txt"
$RaporDosyasi = "changed_options.txt"
$JsonDosyasi = "options_updates.json"

if (-not (Test-Path $EskiDosya) -or -not (Test-Path $YeniDosya)) {
    Write-Host "Hata: options_eski.txt veya options_yeni.txt bulunamadi!" -ForegroundColor Red
    Pause
    Exit
}

function Oku-Options($Yol) {
    $Hash = @{}
    Get-Content $Yol | ForEach-Object {
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

$Rapor = @()
$Rapor += "=================================================="
$Rapor += "         OPTIONS.TXT COMPARISON REPORT            "
$Rapor += "=================================================="
$Rapor += ""

$JsonObjesi = [ordered]@{}

# Yeni eklenenler ve degisenler
$YeniAyarlar.Keys | ForEach-Object {
    $Key = $_
    if (-not $EskiAyarlar.ContainsKey($Key)) {
        $Rapor += "[+] NEW -> $Key : $($YeniAyarlar[$Key])"
        $JsonObjesi[$Key] = $YeniAyarlar[$Key]
    } elseif ($EskiAyarlar[$Key] -ne $YeniAyarlar[$Key]) {
        $Rapor += "[~] CHANGED -> $Key : $($EskiAyarlar[$Key]) -> $($YeniAyarlar[$Key])"
        $JsonObjesi[$Key] = $YeniAyarlar[$Key]
    }
}

# Silinenler
$EskiAyarlar.Keys | ForEach-Object {
    $Key = $_
    if (-not $YeniAyarlar.ContainsKey($Key)) {
        $Rapor += "[-] DELETED -> $Key : $($EskiAyarlar[$Key])"
    }
}

# Raporlari kaydet
$Rapor | Out-File -FilePath $RaporDosyasi -Encoding ascii
$JsonFormatli = ConvertTo-Json $JsonObjesi -Depth 10
$JsonFormatli | Out-File -FilePath $JsonDosyasi -Encoding ascii

Write-Host "Islem tamamlandi!" -ForegroundColor Green
Write-Host "-> Rapor: $RaporDosyasi" -ForegroundColor Cyan
Write-Host "-> JSON: $JsonDosyasi" -ForegroundColor Yellow
Pause