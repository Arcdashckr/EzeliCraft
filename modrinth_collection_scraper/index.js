import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { createInterface } from 'readline/promises';
import { stdin as input, stdout as output } from 'process';

const CONFIG_FILE = path.join(process.cwd(), 'collections.txt');
const OUTPUT_ROOT = path.join(process.cwd(), 'output');

const SCRAPE_MODE_OPTIONS = {
    mods: {
        name: 'Mods',
        endpoint: '/mods',
        isResourcePack: false,
        folderName: 'mods'
    },
    resourcepacks: {
        name: 'Resource Packs',
        endpoint: '/resourcepacks',
        isResourcePack: true,
        folderName: 'resourcepacks'
    },
    shaders: {
        name: 'Shaders',
        endpoint: '/shaders',
        isResourcePack: true,
        folderName: 'shaders'
    },
    all: {
        name: 'All',
        endpoint: '',
        isResourcePack: false,
        folderName: 'all'
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

const MAX_DISCORD_FILE_CHARS = 1900;

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
                sideTag = '#clientSide';
            } else if (tag === 'sunucu' || tag === 'server') {
                sideTag = '#serverSide';
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

    const mappedTags = isResourcePack
        ? [...new Set(outputTags)].map(t => `#${t}`)
        : [`#${finalTypeTag}`, ...(sideTag ? [sideTag] : [])];

    return {
        categoryKey: finalTypeTag,
        obsidianTags: mappedTags.join(' ')
    };
}

function cleanDescription(text) {
    if (!text) return 'Açıklama bulunmuyor.';
    let clean = text.replace(/<\/?[^>]+(>|$)/g, '').trim();
    if (clean.length > 250) {
        clean = clean.substring(0, 247) + '...';
    }
    return clean;
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function writeSimpleGithubMarkdown(outputFilePath, collectionName, collectionMeta, groupedItems) {
    const lines = [];
    lines.push(`# ${collectionName}`);
    lines.push('');

    if (collectionMeta.imageUrl) {
        lines.push(`![${collectionName}](${collectionMeta.imageUrl})`);
        lines.push('');
    }

    lines.push(`- Koleksiyon adı: **${collectionName}**`);
    lines.push(`- Proje sayısı: **${collectionMeta.projectCount || 'Bilinmiyor'}**`);
    lines.push(`- Scrape modu: **${collectionMeta.scrapeLabel || collectionMeta.scrapeMode || 'Bilinmiyor'}**`);
    lines.push(`- Toplam öğe: **${Object.values(groupedItems).reduce((sum, items) => sum + items.length, 0)}**`);
    lines.push('');

    for (const [catKey, categoryItems] of Object.entries(groupedItems)) {
        const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES.other;
        lines.push(`## ${displayTitle}`);
        lines.push('');

        categoryItems.forEach((item, index) => {
            const description = cleanDescription(item.description);
            const descriptionMarkup = description && description !== 'Açıklama bulunmuyor.'
                ? `<div style="margin-top: 4px; color: #f3f4f6; line-height: 1.4;">${escapeHtml(description)}</div>`
                : '';
            const spacing = Math.max(12, Math.min(28, Math.ceil((description.length || 0) / 70) * 4));
            const imgMarkup = item.imgUrl
                ? `<div style="flex-shrink: 0;"><img src="${escapeHtml(item.imgUrl)}" alt="${escapeHtml(item.title)}" width="72" height="72" style="border-radius: 8px; margin-top: 2px;"></div>`
                : '';
            const positionLabel = `<span style="display: inline-block; min-width: 28px; padding: 2px 7px; margin-right: 8px; border-radius: 999px; background: #4b5563; color: #f9fafb; font-weight: 700; font-size: 12px; text-align: center;">${index + 1}</span>`;

            lines.push(`<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: ${spacing}px; padding: 12px 14px; border: 1px solid #4b5563; border-radius: 10px; background: #2f343a; color: #f9fafb;">${imgMarkup}<div style="flex: 1;"><div style="display: flex; align-items: center; flex-wrap: wrap;">${positionLabel}<a href="${escapeHtml(item.url)}">${escapeHtml(item.title)}</a></div>${descriptionMarkup}</div></div>`);
        });

        lines.push('');
    }

    fs.writeFileSync(outputFilePath, lines.join('\n'), 'utf-8');
}

function writeDiscordCategoryFiles(baseDir, collectionName, categoryKey, displayTitle, items) {
    const categoryDir = path.join(baseDir, categoryKey);
    ensureDirExists(categoryDir);

    const header = `## 🎮 MINECRAFT ${collectionName.toUpperCase()}\n\n### ${displayTitle}\n\n`;
    const itemBlocks = items.map(item => `🔹 **[${item.title}](${item.url})**\n> 📝 ${cleanDescription(item.description)}\n\n`);

    const files = [];
    let currentContent = header;
    let fileIndex = 1;

    itemBlocks.forEach(block => {
        const candidate = currentContent + block;
        if (candidate.length > MAX_DISCORD_FILE_CHARS && currentContent !== header) {
            files.push(currentContent);
            currentContent = header;
            fileIndex += 1;
        }

        if (block.length > MAX_DISCORD_FILE_CHARS) {
            const safeBlock = `${block.substring(0, MAX_DISCORD_FILE_CHARS - header.length - 40)}\n\n> ...`;
            currentContent += safeBlock;
            return;
        }

        currentContent += block;
    });

    if (currentContent.trim() && currentContent !== header) {
        files.push(currentContent);
    }

    files.forEach((content, index) => {
        const fileName = path.join(categoryDir, `${sanitizeFolderName(displayTitle)}_${String(index + 1).padStart(2, '0')}.md`);
        fs.writeFileSync(fileName, content, 'utf-8');
    });
}

function ensureDirExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}

function clearDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
        return;
    }

    for (const entry of fs.readdirSync(dirPath)) {
        const fullPath = path.join(dirPath, entry);
        fs.rmSync(fullPath, { recursive: true, force: true });
    }
}

function sanitizeFolderName(name) {
    return (name || 'collection')
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9._-]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

function parseCollectionsConfig(filePath) {
    if (!fs.existsSync(filePath)) {
        return [];
    }

    const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/);
    const collections = [];

    lines.forEach((line, index) => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) {
            return;
        }

        const parts = trimmed.split('|').map(part => part.trim());
        let name = '';
        let url = '';

        if (parts.length === 1) {
            url = parts[0];
        } else if (parts.length >= 2) {
            if (parts[0].startsWith('http')) {
                url = parts[0];
            } else {
                name = parts[0];
                url = parts[1];
            }
        }

        if (!url) {
            console.warn(`⚠️ Satır ${index + 1} geçersiz atlandı: ${line}`);
            return;
        }

        collections.push({ name, url });
    });

    return collections;
}

function resolveCollectionFolderName(entry) {
    const baseName = entry.name ? sanitizeFolderName(entry.name) : sanitizeFolderName(entry.url.match(/\/collection\/([^/?#]+)/i)?.[1] || 'collection');
    return baseName || 'collection';
}

function normalizeSelection(value) {
    const normalized = (value || '').trim().toLowerCase();
    if (normalized === '1' || normalized === 'mods' || normalized === 'mod') {
        return 'mods';
    }
    if (normalized === '2' || normalized === 'resourcepacks' || normalized === 'resourcepack' || normalized === 'resource' || normalized === 'rp') {
        return 'resourcepacks';
    }
    if (normalized === '3' || normalized === 'shaders' || normalized === 'shader') {
        return 'shaders';
    }
    if (normalized === '4' || normalized === 'all' || normalized === 'tum' || normalized === 'tümü') {
        return 'all';
    }
    return null;
}

async function promptScrapeMode() {
    const rl = createInterface({ input, output });

    try {
        console.log('\n🧭 Scrape edilecek içerik türünü seçin:');
        console.log('1) mods');
        console.log('2) resourcepacks');
        console.log('3) shaders');
        console.log('4) all');

        let answer = '';
        while (!normalizeSelection(answer)) {
            answer = (await rl.question('Seçim (1/2/3/4): ')).trim();
        }

        return normalizeSelection(answer);
    } finally {
        rl.close();
    }
}

function resolveSelectedConfig(mode) {
    return SCRAPE_MODE_OPTIONS[mode] || SCRAPE_MODE_OPTIONS.mods;
}

async function runScraperForCollection(entry, index, selectedMode) {
    const selectedConfig = resolveSelectedConfig(selectedMode);
    const fallbackName = entry.name || entry.url.match(/\/collection\/([^/?#]+)/i)?.[1] || `collection-${index + 1}`;
    const targetUrl = selectedMode === 'all'
        ? entry.url.replace(/\/$/, '')
        : `${entry.url.replace(/\/$/, '')}${selectedConfig.endpoint}`;

    console.log(`\n🚀 [${index + 1}/${entry.total}] ${fallbackName} işleniyor...`);
    console.log(`🔗 Hedef Link: ${targetUrl}`);

    let browser;
    try {
        browser = await puppeteer.launch({ headless: true });
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.goto(targetUrl, { waitUntil: 'networkidle2' });

        console.log('📥 Modrinth üzerinden veriler çekiliyor, lütfen bekleyin...');
        await page.waitForSelector('h1.heading-2xl, h1, .project-card-container', { timeout: 10000 });

        const collectionMeta = await page.evaluate(() => {
            const titleEl = document.querySelector('h1.heading-2xl') || document.querySelector('main h1');
            const title = titleEl ? titleEl.textContent.trim() : '';

            const avatarEl = document.querySelector('img.avatar, img[class*="avatar"]') || document.querySelector('main img');
            const imageUrl = avatarEl ? (avatarEl.getAttribute('src') || avatarEl.getAttribute('data-src') || '') : '';

            let projectCount = '';
            const projectNode = Array.from(document.querySelectorAll('span, div, p, li')).find(el => {
                const text = (el.textContent || '').trim();
                return /\bprojects?\b/i.test(text) && /\d+/.test(text);
            });

            if (projectNode) {
                const match = projectNode.textContent.match(/(\d+)/);
                if (match) {
                    projectCount = match[1];
                }
            }

            return { title, imageUrl, projectCount };
        });

        const collectionName = collectionMeta.title || fallbackName;
        const folderName = resolveCollectionFolderName({ ...entry, name: collectionName });
        const outputBaseDir = path.join(OUTPUT_ROOT, folderName);
        const obsidianTargetDir = path.join(outputBaseDir, 'obsidian');
        const discordTargetDir = path.join(outputBaseDir, 'discord');
        const githubTargetDir = path.join(outputBaseDir, 'github');

        ensureDirExists(outputBaseDir);
        ensureDirExists(obsidianTargetDir);
        ensureDirExists(discordTargetDir);
        ensureDirExists(githubTargetDir);

        clearDirectory(obsidianTargetDir);
        clearDirectory(discordTargetDir);
        clearDirectory(githubTargetDir);

        const metadataFilePath = path.join(outputBaseDir, 'collection-meta.json');
        fs.writeFileSync(metadataFilePath, JSON.stringify({
            collectionName,
            collectionUrl: entry.url,
            imageUrl: collectionMeta.imageUrl || '',
            projectCount: collectionMeta.projectCount || '',
            scrapeMode: selectedMode,
            scrapeLabel: selectedConfig.name,
            type: selectedConfig.folderName
        }, null, 2), 'utf-8');

        fs.writeFileSync(path.join(outputBaseDir, 'scrape-mode.txt'), `${selectedConfig.name}\n`, 'utf-8');

        const items = await page.evaluate(() => {
            const cardElements = document.querySelectorAll('.project-card-container');
            const data = [];

            cardElements.forEach(card => {
                const titleEl = card.querySelector('.project-card-title');
                const summaryEl = card.querySelector('.project-card-summary');
                const imgEl = card.querySelector('.project-card__icon');

                let realUrl = 'https://modrinth.com';
                const parentLink = card.closest('a');
                const siblingLink = card.parentElement ? card.parentElement.querySelector('a[href*="/mod/"], a[href*="/resourcepack/"], a[href*="/shader/"]') : null;
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

        if (items.length === 0) {
            console.log(`❌ ${collectionName} koleksiyonunda öğe bulunamadı.`);
            return;
        }

        console.log(`✅ ${items.length} adet veri işleniyor...`);

        const groupedItems = {};
        items.forEach(item => {
            const { categoryKey, obsidianTags } = processTags(item.tags, selectedConfig.isResourcePack);
            if (!groupedItems[categoryKey]) groupedItems[categoryKey] = [];
            groupedItems[categoryKey].push({ ...item, obsidianTags });
        });

        const obsidianFileName = selectedMode === 'resourcepacks' ? 'resourcepacks.md' : selectedMode === 'shaders' ? 'shaders.md' : selectedMode === 'all' ? 'all.md' : 'mods.md';
        const obsidianFullPath = path.join(obsidianTargetDir, obsidianFileName);

        let obsidianContent = `---\ntags:\n  - minecraft\n  - ${selectedConfig.isResourcePack ? 'resource-pack-koleksiyonu' : 'mod-koleksiyonu'}\ntoplam_oge: ${items.length}\ncollection_name: ${collectionName}\ncollection_image: ${collectionMeta.imageUrl || ''}\nproject_count: ${collectionMeta.projectCount || ''}\nscrape_mode: ${selectedMode}\n---\n\n# 🛠️ Modrinth Koleksiyon Listesi (${collectionName})\n\n`;

        if (collectionMeta.imageUrl) {
            obsidianContent += `![${collectionName}](${collectionMeta.imageUrl})\n\n`;
        }

        obsidianContent += `- Koleksiyon adı: **${collectionName}**\n`;
        obsidianContent += `- Proje sayısı: **${collectionMeta.projectCount || 'Bilinmiyor'}**\n\n`;

        for (const [catKey, categoryItems] of Object.entries(groupedItems)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES.other;
            obsidianContent += `## ${displayTitle}\n\n`;

            categoryItems.forEach(item => {
                obsidianContent += `> [!info] **[${item.title}](${item.url})**\n`;
                obsidianContent += `> <table style="width: 100%; border-collapse: collapse; border: none; background: transparent;"><tr style="background: transparent; border: none;"><td width="110" valign="top" style="border: none; padding: 5px;"><img src="${item.imgUrl}" width="100" height="100" style="border-radius:12px; min-width:100px; max-width:100px;"></td><td valign="top" style="padding-left:15px; border: none; padding-top: 5px;">${cleanDescription(item.description)}</td></tr></table>\n`;
                obsidianContent += `> \n`;
                obsidianContent += `> **Tags:** ${item.obsidianTags}\n\n`;
            });
        }

        fs.writeFileSync(obsidianFullPath, obsidianContent, 'utf-8');
        console.log(`📂 Obsidian çıktı: ${obsidianFullPath}`);

        const githubFileName = selectedMode === 'resourcepacks'
            ? 'resourcepacks.md'
            : selectedMode === 'shaders'
                ? 'shaders.md'
                : selectedMode === 'all'
                    ? 'all.md'
                    : 'mods.md';
        const githubFullPath = path.join(githubTargetDir, githubFileName);
        writeSimpleGithubMarkdown(githubFullPath, collectionName, {
            imageUrl: collectionMeta.imageUrl || '',
            projectCount: collectionMeta.projectCount || '',
            scrapeMode: selectedMode,
            scrapeLabel: selectedConfig.name
        }, groupedItems);
        console.log(`📄 GitHub çıktısı: ${githubFullPath}`);

        for (const [catKey, categoryItems] of Object.entries(groupedItems)) {
            const displayTitle = CATEGORY_TITLES[catKey] || CATEGORY_TITLES.other;
            writeDiscordCategoryFiles(discordTargetDir, collectionName, catKey, displayTitle, categoryItems);
        }

        console.log(`📂 Discord çıktı: ${discordTargetDir}`);
        console.log(`🎉 ${collectionName} başarıyla işlendi.`);
    } catch (error) {
        console.error(`❌ ${collectionName} işlenirken hata oluştu:`, error.message);
    } finally {
        if (browser) {
            await browser.close().catch(() => {});
        }
    }
}

async function main() {
    const collections = parseCollectionsConfig(CONFIG_FILE);

    if (collections.length === 0) {
        console.log('📋 collections.txt içinde işlenecek koleksiyon bulunamadı.');
        console.log('Örnek format:');
        console.log('https://modrinth.com/collection/SLUG');
        console.log('İsim|https://modrinth.com/collection/SLUG|mods');
        return;
    }

    ensureDirExists(OUTPUT_ROOT);
    const selectedMode = await promptScrapeMode();
    console.log(`📌 Seçilen scrape modu: ${selectedMode}`);

    collections.forEach((entry, index) => {
        entry.total = collections.length;
    });

    for (const [index, entry] of collections.entries()) {
        await runScraperForCollection(entry, index, selectedMode);
    }

    console.log(`\n✅ Tüm koleksiyonlar işlendi. Çıktılar: ${OUTPUT_ROOT}`);
}

main();