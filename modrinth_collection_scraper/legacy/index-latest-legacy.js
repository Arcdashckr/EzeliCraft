import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const COLLECTION_URL = 'https://modrinth.com/collection/K3ej09Af';

// Sadece senin istediğin 10 ana mod türü etiketleri (Küçük harf eşleşmesi için)
const ALLOWED_CATEGORIES = [
    'decoration', 'equipment', 'food', 'game mechanics',
    'library', 'mobs', 'optimization', 'storage',
    'transportation', 'utility'
];

// Başlıkların şık görünmesi için bir eşleme tablosu
const CATEGORY_TITLES = {
    'decoration': '🧱 Decoration (Dekorasyon)',
    'equipment': '🛡️ Equipment (Ekipman)',
    'food': '🍎 Food (Yiyecek)',
    'game mechanics': '⚙️ Game Mechanics (Oyun Mekanikleri)',
    'library': '📚 Library (Kütüphane / API)',
    'mobs': '🦁 Mobs (Yaratıklar / Canlılar)',
    'optimization': '⚡ Optimization (Performans / FPS)',
    'storage': '📦 Storage (Depolama)',
    'transportation': '🚇 Transportation (Ulaşım)',
    'utility': '🛠️ Utility (Yardımcı Araçlar)',
    'other': '🎮 Diğer / Sınıflandırılamayan Modlar'
};

// Gelen etiket dizisinden senin istediğin ilk geçerli kategoriyi bulan fonksiyon
function findValidCategory(tags) {
    for (const tag of tags) {
        const cleanTag = tag.toLowerCase().trim();
        if (ALLOWED_CATEGORIES.includes(cleanTag)) {
            return cleanTag;
        }
    }
    return 'other'; // Listede eşleşen yoksa buraya düşer
}

// Client/Server durumunu kontrol edip Obsidian uyumlu tag üreten fonksiyon
function parseSideTags(tags) {
    // Tekrarlayan elementleri temizlemek için benzersiz (unique) bir diziye çeviriyoruz
    const uniqueTags = [...new Set(tags.map(t => t.toLowerCase().trim()))];
    const sideTags = [];
    uniqueTags.forEach(tag => {
        if (tag.includes('istemci veya sunucu') || tag.includes('client or server')) {
            sideTags.push('#clientAndServer');
        } else if (tag === 'istemci' || tag === 'client') {
            sideTags.push('#clientSide');
        } else if (tag === 'sunucu' || tag === 'server') {
            sideTags.push('#serverSide');
        }
    });
    return [...new Set(sideTags)];
}

function cleanDescription(text) {
    if (!text) return "Açıklama bulunmuyor.";
    let clean = text.replace(/<\/?[^>]+(>|$)/g, "").trim();
    if (clean.length > 250) {
        clean = clean.substring(0, 247) + "...";
    }
    return clean;
}

async function startScraper() {
    console.log("Tarayıcı arka planda başlatılıyor...");
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.goto(COLLECTION_URL, { waitUntil: 'networkidle2' });

        console.log("Mod listesi yükleniyor...");
        await page.waitForSelector('.project-card-container', { timeout: 10000 });

        const mods = await page.evaluate(() => {
            const cardElements = document.querySelectorAll('.project-card-container');
            const data = [];

            cardElements.forEach(card => {
                const titleEl = card.querySelector('.project-card-title');
                const summaryEl = card.querySelector('.project-card-summary');
                const imgEl = card.querySelector('.project-card__icon');

                // Div veya span fark etmeksizin tüm etiket metinlerini topla
                const tagElements = card.querySelectorAll('.grid-project-card-list__tags div, .grid-project-card-list__tags span');
                const tags = [];
                tagElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && text.length > 1) tags.push(text);
                });

                if (titleEl) {
                    const title = titleEl.textContent.trim();
                    const description = summaryEl ? summaryEl.textContent.trim() : '';
                    const imgUrl = imgEl ? imgEl.getAttribute('src') : 'https://modrinth.com/favicon.ico';
                    if (imgEl == null) {
                        imgUrl = 'https://modrinth.com/favicon.ico';
                    }
                    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
                    const url = `https://modrinth.com/project/${slug}`;

                    data.push({ title, description, url, imgUrl, tags });
                }
            });
            return data;
        });

        await browser.close();

        if (mods.length === 0) {
            console.log("❌ Sayfadan mod verisi çekilemedi.");
            return;
        }

        console.log(`\n✅ ${mods.length} mod tespit edildi. Kategoriler ayrıştırılıyor...`);

        // --- KATEGORİLERE GÖRE GRUPLAMA ---
        const groupedMods = {};
        mods.forEach(mod => {
            const chosenCategory = findValidCategory(mod.tags);
            if (!groupedMods[chosenCategory]) groupedMods[chosenCategory] = [];
            groupedMods[chosenCategory].push(mod);
        });

        // --- 1. OBSIDIAN MARKDOWN ÇIKTISI ---
        let obsidianContent = `---\ntoplam_mod: ${mods.length}\n---\n\n# [🛠️ Modrinth Koleksiyon Listesi](${COLLECTION_URL})\n\n`;

        for (const [catKey, categoryMods] of Object.entries(groupedMods)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES['other'];
            obsidianContent += `## ${displayTitle}\n\n`;

            categoryMods.forEach(mod => {
                const sideTags = parseSideTags(mod.tags);
                const obsidianTagLine = sideTags.length > 0 ? `#${catKey} ${sideTags.join(' ')}` : `#${catKey}`;

                obsidianContent += `> [!info] **[${mod.title}](${mod.url})**\n`;
                obsidianContent += `> <table style="width: 100%; border-collapse: collapse; border: none; background: transparent;"><tr style="background: transparent; border: none;"><td width="110" valign="top" style="border: none; padding: 5px;"><img src="${mod.imgUrl}" width="100" height="100" style="border-radius:12px; min-width:100px; max-width:100px;"></td><td valign="top" style="padding-left:15px; border: none; padding-top: 5px;">${cleanDescription(mod.description)}</td></tr></table>\n`;
                obsidianContent += `> \n`;
                obsidianContent += `> **Tags:** ${obsidianTagLine}\n\n`;
            });
        }
        fs.writeFileSync('mods_obsidian.md', obsidianContent, 'utf-8');
        console.log("📂 Obsidian için 'mods_obsidian.md' tek satır HTML tasarımıyla güncellendi.");


        // --- 2. DISCORD KLASÖRÜ VE PARÇALANMIŞ MARKDOWN ÇIKTILARI ---
        const discordDir = path.join(process.cwd(), 'discord_output');
        if (!fs.existsSync(discordDir)) {
            fs.mkdirSync(discordDir);
        } else {
            fs.readdirSync(discordDir).forEach(file => fs.unlinkSync(path.join(discordDir, file)));
        }

        let fileIndex = 1;
        let currentDiscordText = `## 🎮 MINECRAFT MOD LİSTESİ (Parça ${fileIndex}) 🎮\n\n`;
        let isFirstItem = true;

        for (const [catKey, categoryMods] of Object.entries(groupedMods)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES['other'];
            let categoryText = `### ${displayTitle}\n`;

            categoryMods.forEach(mod => {
                const modLine = `🔹 **[${mod.title}](${mod.url})**\n> 📝 ${cleanDescription(mod.description)}\n\n`;
                categoryText += modLine;
            });

            // Karakter sınırı kontrolü (İlk parçanın boş kalmasını engellemek için koşul güncellendi)
            if (!isFirstItem && (currentDiscordText.length + categoryText.length > 1800)) {
                const fileName = path.join(discordDir, `part_${fileIndex.toString().padStart(2, '0')}.md`);
                fs.writeFileSync(fileName, currentDiscordText, 'utf-8');
                fileIndex++;

                currentDiscordText = `## 🎮 MINECRAFT MOD LİSTESİ (Parça ${fileIndex}) 🎮\n\n` + categoryText;
            } else {
                currentDiscordText += categoryText + `\n`;
                isFirstItem = false;
            }
        }

        // Kalan son metni de yazdırıyoruz
        if (currentDiscordText.trim().length > 0) {
            const fileName = path.join(discordDir, `part_${fileIndex.toString().padStart(2, '0')}.md`);
            fs.writeFileSync(fileName, currentDiscordText, 'utf-8');
        }

        console.log(`📂 Discord için 'discord_output/' klasörüne ${fileIndex} adet dosya üretildi.`);
        console.log(`\n🎉 Tüm süreç başarıyla optimize edildi!`);

    } catch (error) {
        console.error("❌ Hata:", error.message);
        await browser.close();
    }
}

startScraper();