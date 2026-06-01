import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import readline from 'readline';

// Ana koleksiyon linkini buraya (sonunda /mods veya /resourcepacks olmadan) temizce yazıyoruz
const BASE_COLLECTION_URL = 'https://modrinth.com/collection/K3ej09Af';

// --- KOLAYCA DEĞİŞTİRİLEBİLİR SEÇENEK AYARLARI ---
// Buraya yeni seçenekler ekleyebilir, tetiklenecek endpoint'leri ve klasör isimlerini değiştirebilirsin
const SCRAPE_OPTIONS = {
    '1': {
        name: 'Mod Listesi',
        endpoint: '/mods',
        isResourcePack: false,
        folderName: 'mods'
    },
    '2': {
        name: 'Resource Pack (Doku Paketi) Listesi',
        endpoint: '/resourcepacks',
        isResourcePack: true,
        folderName: 'resourcepacks'
    },
    '3': {
        name: 'Shader Listesi',
        endpoint: '/shaders',
        isResourcePack: true,
        folderName: 'shaders'
    }
};

const ALLOWED_CATEGORIES = [
    'decoration', 'equipment', 'food', 'game mechanics', 
    'library', 'mobs', 'optimization', 'storage', 
    'transportation', 'utility'
];

const ALLOWED_RP_CATEGORIES = ['decoration', 'realistic', 'simplistic', 'tweaks', 'utility', 'modded'];

const ALLOWED_RP_FEATURES = [
    'audio', 'blocks', 'core', 'shaders', 'entities', 
    'environment', 'equipment', 'fonts', 'gui', 'items', 
    'locale', 'models'
];

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
    'resourcepack': '🎨 Resource Packs (Doku Paketleri)',
    'other': '🎮 Diğer / Sınıflandırılamayan Modlar'
};

function processTags(tags, isResourcePack) {
    const outputTags = [];
    let sideTag = '';
    const fullRawText = tags.join(' ').toLowerCase();

    if (isResourcePack) {
        ALLOWED_RP_FEATURES.forEach(feature => {
            if (fullRawText.includes(feature)) outputTags.push(feature);
        });
        ALLOWED_RP_CATEGORIES.forEach(category => {
            if (fullRawText.includes(category)) outputTags.push(category);
        });
        if (fullRawText.includes('vanilla') && fullRawText.includes('like')) {
            outputTags.push('vanilla-like');
        }
    } else {
        const cleanTags = [...new Set(tags.map(t => t.toLowerCase().trim()))];
        cleanTags.forEach(tag => {
            if (tag.includes('istemci veya sunucu') || tag.includes('client or server')) {
                sideTag = '#clientAndServer';
            } else if (tag === 'istemci' || tag === 'client') {
                if (!isResourcePack) sideTag = '#clientSide';
            } else if (tag === 'sunucu' || tag === 'server') {
                if (!isResourcePack) sideTag = '#serverSide';
            } else {
                const ignoredKeywords = ['fabric', 'forge', 'quilt', 'neoforge', 'client', 'server'];
                if (!ignoredKeywords.includes(tag) && ALLOWED_CATEGORIES.includes(tag)) {
                    outputTags.push(tag);
                }
            }
        });
    }

    let finalTypeTag = 'other';
    if (isResourcePack) {
        finalTypeTag = 'resourcepack';
    } else {
        for (const tag of outputTags) {
            if (ALLOWED_CATEGORIES.includes(tag)) {
                finalTypeTag = tag;
                break;
            }
        }
    }

    let mappedTags = [];
    if (isResourcePack) {
        mappedTags = [...new Set(outputTags)].map(t => `#${t}`);
    } else {
        mappedTags = [`#${finalTypeTag}`];
        if (sideTag) mappedTags.push(sideTag);
    }

    return {
        categoryKey: finalTypeTag,
        obsidianTags: mappedTags.join(' ')
    };
}

function cleanDescription(text) {
    if (!text) return "Açıklama bulunmuyor.";
    let clean = text.replace(/<\/?[^>]+(>|$)/g, "").trim();
    if (clean.length > 250) {
        clean = clean.substring(0, 247) + "...";
    }
    return clean;
}

// Yardımcı Klasör Oluşturma Fonksiyonu
function ensureDirExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}

async function runScraper(selectedConfig) {
    const isResourcePack = selectedConfig.isResourcePack;
    const targetUrl = `${BASE_COLLECTION_URL}${selectedConfig.endpoint}`;
    
    // Klasör Yapısını Tanımlıyoruz
    const obsidianTargetDir = path.join(process.cwd(), 'obsidian_output', selectedConfig.folderName);
    const discordTargetDir = path.join(process.cwd(), 'discord_output', selectedConfig.folderName);

    // Gerekli klasörleri güvenli bir şekilde açalım
    ensureDirExists(obsidianTargetDir);
    ensureDirExists(discordTargetDir);

    console.log(`\n🚀 Tarayıcı başlatılıyor...`);
    console.log(`🔗 Hedef Link: ${targetUrl}`);
    
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.goto(targetUrl, { waitUntil: 'networkidle2' });

        console.log("📥 Modrinth üzerinden veriler çekiliyor, lütfen bekleyin...");
        await page.waitForSelector('.project-card-container', { timeout: 10000 });

        const items = await page.evaluate(() => {
            const cardElements = document.querySelectorAll('.project-card-container');
            const data = [];

            cardElements.forEach(card => {
                const titleEl = card.querySelector('.project-card-title');
                const summaryEl = card.querySelector('.project-card-summary');
                const imgEl = card.querySelector('.project-card__icon');
                
                let realUrl = 'https://modrinth.com';
                const parentLink = card.closest('a');
                const siblingLink = card.parentElement ? card.parentElement.querySelector('a[href*="/mod/"], a[href*="/resourcepack/"]') : null;
                const finalLinkElement = parentLink || siblingLink || card.querySelector('a');

                if (finalLinkElement && finalLinkElement.href) {
                    realUrl = finalLinkElement.href;
                } else if (finalLinkElement && finalLinkElement.getAttribute('href')) {
                    const href = finalLinkElement.getAttribute('href');
                    realUrl = href.startsWith('http') ? href : `https://modrinth.com${href}`;
                }

                const tagElements = card.querySelectorAll('.grid-project-card-list__tags div, .grid-project-card-list__tags span');
                const tags = [];
                tagElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && text.length > 1) tags.push(text);
                });

                if (titleEl) {
                    const title = titleEl.textContent.trim();
                    const description = summaryEl ? summaryEl.textContent.trim() : '';
                    
                    let imgUrl = 'https://modrinth.com/favicon.ico';
                    if (imgEl) {
                        const srcValue = imgEl.getAttribute('src');
                        if (srcValue && srcValue !== 'null' && srcValue !== 'undefined' && srcValue.trim() !== '') {
                            imgUrl = srcValue;
                        }
                    }

                    data.push({ title, description, url: realUrl, imgUrl, tags });
                }
            });
            return data;
        });

        await browser.close();

        if (items.length === 0) {
            console.log(`❌ Koleksiyonda herhangi bir öğe bulunamadı.`);
            return;
        }

        console.log(`✅ ${items.length} adet veri işleniyor...`);

        // --- KATEGORİLERE GÖRE GRUPLAMA ---
        const groupedItems = {};
        items.forEach(item => {
            const { categoryKey, obsidianTags } = processTags(item.tags, isResourcePack);
            if (!groupedItems[categoryKey]) groupedItems[categoryKey] = [];
            groupedItems[categoryKey].push({ ...item, obsidianTags });
        });

        // --- 1. OBSIDIAN YAZMA İŞLEMİ ---
        const obsidianFileName = isResourcePack ? 'resourcepacks.md' : 'mods.md';
        const obsidianFullPath = path.join(obsidianTargetDir, obsidianFileName);

        let obsidianContent = `---\ntags:\n  - minecraft\n  - ${isResourcePack ? 'resource-pack-koleksiyonu' : 'mod-koleksiyonu'}\ntoplam_oge: ${items.length}\n---\n\n# 🛠️ Modrinth Koleksiyon Listesi (${selectedConfig.name})\n\n`;

        for (const [catKey, categoryItems] of Object.entries(groupedItems)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES['other'];
            obsidianContent += `## ${displayTitle}\n\n`;

            categoryItems.forEach(item => {
                obsidianContent += `> [!info] **[${item.title}](${item.url})**\n`;
                obsidianContent += `> <table style="width: 100%; border-collapse: collapse; border: none; background: transparent;"><tr style="background: transparent; border: none;"><td width="110" valign="top" style="border: none; padding: 5px;"><img src="${item.imgUrl}" width="100" height="100" style="border-radius:12px; min-width:100px; max-width:100px;"></td><td valign="top" style="padding-left:15px; border: none; padding-top: 5px;">${cleanDescription(item.description)}</td></tr></table>\n`;
                obsidianContent += `> \n`;
                obsidianContent += `> **Tags:** ${item.obsidianTags}\n\n`;
            });
        }
        fs.writeFileSync(obsidianFullPath, obsidianContent, 'utf-8');
        console.log(`\n📂 Obsidian Dosyası Hazır: ${obsidianFullPath}`);


        // --- 2. DISCORD YAZMA İŞLEMİ ---
        // Klasörün içindeki eski partları temizle
        fs.readdirSync(discordTargetDir).forEach(file => fs.unlinkSync(path.join(discordTargetDir, file)));

        let fileIndex = 1;
        const filePrefix = isResourcePack ? 'rp_part_' : 'mod_part_';
        let currentDiscordText = `## 🎮 MINECRAFT ${selectedConfig.name.toUpperCase()} (Parça ${fileIndex}) 🎮\n\n`;
        let isFirstItem = true;

        for (const [catKey, categoryItems] of Object.entries(groupedItems)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES['other'];
            let categoryText = `### ${displayTitle}\n`;
            
            categoryItems.forEach(item => {
                const itemLine = `🔹 **[${item.title}](${item.url})**\n> 📝 ${cleanDescription(item.description)}\n\n`;
                categoryText += itemLine;
            });

            if (!isFirstItem && (currentDiscordText.length + categoryText.length > 1800)) {
                const fileName = path.join(discordTargetDir, `${filePrefix}${fileIndex.toString().padStart(2, '0')}.md`);
                fs.writeFileSync(fileName, currentDiscordText, 'utf-8');
                fileIndex++;
                
                currentDiscordText = `## 🎮 MINECRAFT ${selectedConfig.name.toUpperCase()} (Parça ${fileIndex}) 🎮\n\n` + categoryText;
            } else {
                currentDiscordText += categoryText + `\n`;
                isFirstItem = false;
            }
        }

        if (currentDiscordText.trim().length > 0) {
            const fileName = path.join(discordTargetDir, `${filePrefix}${fileIndex.toString().padStart(2, '0')}.md`);
            fs.writeFileSync(fileName, currentDiscordText, 'utf-8');
        }

        console.log(`📂 Discord Partları Hazır (${fileIndex} adet): ${discordTargetDir}\\`);
        console.log(`\n🎉 Tüm işlemler başarıyla tamamlandı!`);

    } catch (error) {
        console.error("❌ Bir hata oluştu:", error.message);
        await browser.close();
    }
}

// --- INTERAKTIF SORU PANELİ ---
function askQuestion() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    console.log('===================================================');
    console.log('   🤖 MODRINTH KOLEKSİYON AYIKLAYICI BAŞLADI 🤖');
    console.log('===================================================');
    console.log('Lütfen işlem yapmak istediğiniz türü seçin:\n');
    
    // Dinamik seçenek listesini terminale basıyoruz
    Object.keys(SCRAPE_OPTIONS).forEach(key => {
        console.log(`  [${key}] -> ${SCRAPE_OPTIONS[key].name}`);
    });
    console.log('===================================================');

    rl.question('\nSeçiminiz (Sayı girin): ', (answer) => {
        const selection = answer.trim();
        
        if (SCRAPE_OPTIONS[selection]) {
            rl.close();
            runScraper(SCRAPE_OPTIONS[selection]);
        } else {
            console.log('❌ Geçersiz seçim yaptınız. Lütfen tekrar deneyin.\n');
            rl.close();
            askQuestion(); // Hatalı seçimde soruyu tekrar sorar
        }
    });
}

askQuestion();