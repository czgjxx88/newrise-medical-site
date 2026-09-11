#!/usr/bin/env node
// Regenerate news pagination: 9 articles per page
const fs = require('fs');
const path = require('path');

const SITE = process.env.SITE_DIR || '/Users/lobster/workspace/lali';
const NEWS = path.join(SITE, 'news');
const PER_PAGE = 9;

// Get all article files, sorted newest first
const files = fs.readdirSync(NEWS)
  .filter(f => /^\d{4}-\d{2}-\d{2}-.*\.html$/.test(f) && f !== 'article-template.html')
  .sort((a, b) => b.localeCompare(a));

const totalPages = Math.ceil(files.length / PER_PAGE);
console.log(`📰 ${files.length} articles → ${totalPages} pages`);

function extractMeta(filename) {
  const html = fs.readFileSync(path.join(NEWS, filename), 'utf8');
  const title = (html.match(/<title>([^<]*)<\/title>/) || [])[1]?.replace(/\s*– Newrise Medical$/, '') || 'Newrise Medical Update';
  const desc = (html.match(/<meta name="description" content="([^"]*)"/) || [])[1] || '';
  const imgMatch = html.match(/src="([^"]*\.jpg)"/);
  const img = imgMatch ? path.basename(imgMatch[1]) : 'banner-hero.jpg';
  const dateMatch = filename.match(/^(\d{4}-\d{2}-\d{2})/);
  let cardDate = '';
  if (dateMatch) {
    const d = new Date(dateMatch[1] + 'T00:00:00+08:00');
    cardDate = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  }
  return { title, desc, img, cardDate };
}

function articleCard(slug, prefix) {
  const { title, desc, img, cardDate } = extractMeta(slug);
  return `        <article class="news-card">
          <div class="news-image">
            <img src="${prefix}assets/images/${img}" alt="${title}" loading="lazy">
          </div>
          <div class="news-content">
            <div class="news-date">${cardDate}</div>
            <h3><a href="${prefix}news/${slug}">${title}</a></h3>
            <p>${desc}</p>
            <a href="${prefix}news/${slug}" class="btn btn-sm btn-primary" style="margin-top:12px;">Read More &rarr;</a>
          </div>
        </article>`;
}

function pagination(pageNum, totalPages) {
  if (totalPages <= 1) return '';
  const parts = ['<nav class="pagination" style="display:flex;justify-content:center;align-items:center;gap:8px;margin-top:60px;">'];
  if (pageNum > 1) {
    const prev = pageNum - 1 === 1 ? 'news.html' : `news-page-${pageNum - 1}.html`;
    parts.push(`<a href="${prev}" class="btn btn-sm" style="background:var(--bg-light);color:var(--text-light);">← Prev</a>`);
  }
  for (let i = 1; i <= totalPages; i++) {
    if (i === pageNum) {
      parts.push(`<span class="btn btn-sm" style="background:var(--accent);color:#fff;pointer-events:none;">${i}</span>`);
    } else {
      const link = i === 1 ? 'news.html' : `news-page-${i}.html`;
      parts.push(`<a href="${link}" class="btn btn-sm" style="background:var(--bg-light);color:var(--text-light);">${i}</a>`);
    }
  }
  if (pageNum < totalPages) {
    const next = pageNum + 1 === 1 ? 'news.html' : `news-page-${pageNum + 1}.html`;
    parts.push(`<a href="${next}" class="btn btn-sm" style="background:var(--bg-light);color:var(--text-light);">Next →</a>`);
  }
  parts.push('</nav>');
  return parts.join('\n        ');
}

function buildPage(pageNum) {
  const prefix = pageNum === 1 ? '' : '../';
  const title = pageNum === 1
    ? 'News & Insights – Newrise Medical'
    : `News & Insights – Page ${pageNum} – Newrise Medical`;
  const desc = pageNum === 1
    ? 'Stay updated with the latest industry trends, product updates, and company news from Newrise Medical.'
    : `Page ${pageNum} of industry trends, product updates, and company news from Newrise Medical.`;
  const canonical = pageNum === 1
    ? 'https://www.newrisemedical.com/news.html'
    : `https://www.newrisemedical.com/news-page-${pageNum}.html`;
  const breadcrumb = pageNum === 1
    ? '<span>News</span>'
    : `<a href="../news.html">News</a> &raquo; <span>Page ${pageNum}</span>`;

  const start = (pageNum - 1) * PER_PAGE;
  const pageFiles = files.slice(start, start + PER_PAGE);
  const cards = pageFiles.map(f => articleCard(f, prefix)).join('\n\n');
  const pag = pagination(pageNum, totalPages);

  const filename = pageNum === 1 ? 'news.html' : `news-page-${pageNum}.html`;
  const outPath = path.join(SITE, filename);

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-C3LER7FFRQ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-C3LER7FFRQ');
</script>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" sizes="64x64" href="${prefix}assets/images/favicon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="${prefix}assets/images/favicon-32.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <meta name="description" content="${desc}">
  <link rel="canonical" href="${canonical}">
  <meta property="og:title" content="${title}">
  <meta property="og:description" content="${desc}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://www.newrisemedical.com/assets/images/banner-hero.jpg">
  <meta property="og:site_name" content="Newrise Medical">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${prefix}assets/css/styles.css?v=15">
</head>
<body>
  <header class="header" id="header">
    <div class="container">
      <nav class="navbar">
        <a href="${prefix}index.html" class="logo">
          <img src="${prefix}assets/images/logo.png" alt="Newrise Medical" style="height:44px;width:auto;">
        </a>
        <button class="menu-toggle" id="menuToggle" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
        <div class="nav-links" id="navLinks">
          <a href="${prefix}index.html">Home</a>
          <a href="${prefix}about.html">About Us</a>
          <div class="nav-dropdown">
            <a href="${prefix}products.html" class="nav-dropdown-toggle">Products <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M2 4l4 4 4-4z"/></svg></a>
            <div class="dropdown-menu">
              <a href="${prefix}landing-pages/landing-incontinence-care.html">Incontinence Care</a>
              <a href="${prefix}landing-pages/landing-medical-blankets.html">Medical Blankets</a>
              <a href="${prefix}landing-pages/landing-infection-control.html">Infection Control</a>
              <a href="${prefix}landing-pages/landing-patient-transfer.html">Patient Transfer</a>
              <a href="${prefix}landing-pages/landing-oem-odm.html">OEM / ODM</a>
            </div>
          </div>
          <a href="${prefix}news.html" class="active">News</a>
          <a href="${prefix}faq.html">FAQ</a>
          <a href="${prefix}contact.html">Contact</a>
        </div>
        <button class="search-btn" id="searchBtn" aria-label="Search">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </button>
        <div class="nav-cta">
          <a href="${prefix}contact.html" class="btn btn-primary btn-sm">Get Quote</a>
        </div>
      </nav>
    </div>
    <div class="search-overlay" id="searchOverlay" style="display:none;">
      <div class="search-container">
        <form class="search-form" action="#" method="get">
          <input type="search" placeholder="Search products, news, pages..." class="search-input">
          <button type="submit" class="search-submit">Search</button>
          <button type="button" class="search-close" id="searchClose">&times;</button>
        </form>
      </div>
    </div>
  </header>
  <section class="page-header">
    <div class="container">
      <h1>News & Insights</h1>
      <p>Stay updated with the latest industry trends, product updates, and company news from Newrise Medical.</p>
      <div class="breadcrumb">
        <a href="${prefix}index.html">Home</a> &raquo; ${breadcrumb}
      </div>
    </div>
  </section>
  <section class="section" id="page-${pageNum}">
    <div class="container">
      <div class="news-grid">
${cards}
      </div>
      ${pag}
    </div>
  </section>
  <section class="cta-banner">
    <div class="container">
      <h2>Need a Reliable Medical Supply Partner?</h2>
      <p>Contact us for a free quote. We respond within 24 hours.</p>
      <div class="hero-buttons">
        <a href="${prefix}contact.html" class="btn btn-white">Get Free Quote</a>
        <a href="${prefix}products.html" class="btn btn-outline">View Products</a>
      </div>
    </div>
  </section>
  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-about">
          <div class="logo">
            <img src="${prefix}assets/images/logo.png" alt="Newrise Medical" style="height:44px;width:auto;">
          </div>
          <p>Changzhou Newrise Medical & Hygiene Products Co., Ltd. — Professional manufacturer of disposable medical and healthcare supplies since 2004.</p>
        </div>
        <div>
          <h4>Quick Links</h4>
          <ul class="footer-links">
            <li><a href="${prefix}index.html">Home</a></li>
            <li><a href="${prefix}about.html">About Us</a></li>
            <li><a href="${prefix}products.html">Products</a></li>
            <li><a href="${prefix}news.html">News</a></li>
            <li><a href="${prefix}faq.html">FAQ</a></li>
            <li><a href="${prefix}contact.html">Contact</a></li>
          </ul>
        </div>
        <div>
          <h4>Products</h4>
          <ul class="footer-links">
            <li><a href="${prefix}landing-pages/landing-incontinence-care.html">Incontinence Care</a></li>
            <li><a href="${prefix}landing-pages/landing-medical-blankets.html">Medical Blankets</a></li>
            <li><a href="${prefix}landing-pages/landing-infection-control.html">Infection Control</a></li>
            <li><a href="${prefix}landing-pages/landing-patient-transfer.html">Patient Transfer</a></li>
            <li><a href="${prefix}landing-pages/landing-oem-odm.html">OEM / ODM</a></li>
          </ul>
        </div>
        <div>
          <h4>Contact Us</h4>
          <ul class="footer-contact">
            <li><span class="icon">📞</span><div>+86 519 86580890</div></li>
            <li><span class="icon">✉️</span><div>info@cznewrise.com</div></li>
            <li><span class="icon">👤</span><div>Rachel — Sales Manager</div></li>
            <li><span class="icon">📍</span><div>Changzhou, Jiangsu, China</div></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">&copy; 2026 Changzhou Newrise Medical & Hygiene Products Co., Ltd. All rights reserved.</div>
    </div>
  </footer>
  <script src="${prefix}assets/js/main.js?v=15"></script>
</body>
</html>
`;

  fs.writeFileSync(outPath, html, 'utf8');
  console.log(`  ✅ ${filename} (${pageFiles.length} articles)`);
}

// Generate all pages
for (let p = 1; p <= totalPages; p++) {
  buildPage(p);
}

// Remove stale page files
const existing = fs.readdirSync(SITE).filter(f => /^news-page-\d+\.html$/.test(f));
for (const f of existing) {
  const n = parseInt(f.match(/\d+/)[0]);
  if (n > totalPages) {
    fs.unlinkSync(path.join(SITE, f));
    console.log(`  🗑️ Removed: ${f}`);
  }
}

console.log(`✅ Done! ${files.length} articles across ${totalPages} pages.`);
