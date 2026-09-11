#!/bin/bash
# Regenerate news.html + news-page-N.html from /news/*.html article files
# Each page shows 9 articles. Auto-creates/removes pages as needed.
set -euo pipefail

SITE_DIR="/Users/lobster/workspace/lali"
NEWS_DIR="$SITE_DIR/news"
PER_PAGE=9
GA_ID="G-C3LER7FFRQ"
CSS_V="15"

cd "$SITE_DIR"

# Get sorted article list (newest first, excluding template)
mapfile -t ARTICLES < <(
  ls -1 news/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-' | grep -v 'article-template' | sort -r
)

TOTAL=${#ARTICLES[@]}
PAGES=$(( (TOTAL + PER_PAGE - 1) / PER_PAGE ))
echo "📰 $TOTAL articles → $PAGES pages ($PER_PAGE/page)"

# Extract metadata from a single article file
get_meta() {
  local f="$NEWS_DIR/$1"
  local key="$2"
  case "$key" in
    title)
      sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' "$f" | head -1 | sed 's/ – Newrise Medical$//'
      ;;
    desc)
      sed -n 's/.*<meta name="description" content="\([^"]*\)".*/\1/p' "$f" | head -1
      ;;
    img)
      local raw
      raw=$(sed -n 's/.*src="\([^"]*\.jpg\)".*/\1/p' "$f" | head -1)
      basename "$raw"
      ;;
    date)
      local dp
      dp=$(echo "$1" | sed -n 's/^\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p')
      if [ -n "$dp" ]; then
        date -j -f "%Y-%m-%d" "$dp" "+%B %e, %Y" 2>/dev/null | sed 's/  / /g'
      fi
      ;;
  esac
}

# Build one article card HTML
card() {
  local slug="$1" prefix="$2"
  local t d i
  t=$(get_meta "$slug" title)
  d=$(get_meta "$slug" date)
  i=$(get_meta "$slug" img)
  local desc
  desc=$(get_meta "$slug" desc)
  [ -z "$t" ] && t="Newrise Medical Update"
  [ -z "$d" ] && d="Recent"
  [ -z "$i" ] && i="banner-hero.jpg"
  [ -z "$desc" ] && desc="Latest updates from Newrise Medical."

  cat <<EOF
        <article class="news-card">
          <div class="news-image">
            <img src="${prefix}assets/images/$i" alt="$t" loading="lazy">
          </div>
          <div class="news-content">
            <div class="news-date">$d</div>
            <h3><a href="${prefix}news/$slug">$t</a></h3>
            <p>$desc</p>
            <a href="${prefix}news/$slug" class="btn btn-sm btn-primary" style="margin-top:12px;">Read More &rarr;</a>
          </div>
        </article>
EOF
}

# Generate a complete news page HTML
gen_page() {
  local p="$1"
  local prefix="" title="News & Insights – Newrise Medical"
  local desc="Stay updated with the latest industry trends, product updates, and company news from Newrise Medical."
  local canonical="https://www.newrisemedical.com/news.html"
  local bc='<span>News</span>'

  if [ "$p" -gt 1 ]; then
    prefix="../"
    title="News & Insights – Page $p – Newrise Medical"
    desc="Page $p of industry trends, product updates, and company news from Newrise Medical."
    canonical="https://www.newrisemedical.com/news-page-$p.html"
    bc="<a href=\"../news.html\">News</a> &raquo; <span>Page $p</span>"
  fi

  # Article cards
  local start=$(( (p - 1) * PER_PAGE ))
  local body=""
  for ((i=start; i<start+PER_PAGE && i<TOTAL; i++)); do
    body+="$(card "${ARTICLES[$i]}" "$prefix")"$'\n'
  done

  # Pagination
  local pag=""
  if [ "$PAGES" -gt 1 ]; then
    pag='<nav class="pagination" style="display:flex;justify-content:center;align-items:center;gap:8px;margin-top:60px;">'
    if [ "$p" -gt 1 ]; then
      local pp=$((p-1))
      [ "$pp" -eq 1 ] && pag+="<a href=\"../news.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">← Prev</a>" || \
        pag+="<a href=\"../news-page-$pp.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">← Prev</a>"
    fi
    for ((n=1; n<=PAGES; n++)); do
      if [ "$n" -eq "$p" ]; then
        pag+="<span class=\"btn btn-sm\" style=\"background:var(--accent);color:#fff;pointer-events:none;\">$n</span>"
      else
        [ "$n" -eq 1 ] && pag+="<a href=\"../news.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">$n</a>" || \
          pag+="<a href=\"../news-page-$n.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">$n</a>"
      fi
    done
    if [ "$p" -lt "$PAGES" ]; then
      local np=$((p+1))
      [ "$np" -eq 1 ] && pag+="<a href=\"../news.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">Next →</a>" || \
        pag+="<a href=\"../news-page-$np.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">Next →</a>"
    fi
    pag+='</nav>'
  fi

  # Page 1 pagination uses local links (no ../)
  if [ "$p" -eq 1 ] && [ "$PAGES" -gt 1 ]; then
    pag='<nav class="pagination" style="display:flex;justify-content:center;align-items:center;gap:8px;margin-top:60px;">'
    pag+="<span class=\"btn btn-sm\" style=\"background:var(--accent);color:#fff;pointer-events:none;\">1</span>"
    pag+="<a href=\"news-page-2.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">2</a>"
    pag+="<a href=\"news-page-2.html\" class=\"btn btn-sm\" style=\"background:var(--bg-light);color:var(--text-light);\">Next →</a>"
    pag+='</nav>'
  fi

  local outfile
  [ "$p" -eq 1 ] && outfile="$SITE_DIR/news.html" || outfile="$SITE_DIR/news-page-$p.html"

  cat > "$outfile" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=$GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '$GA_ID');
</script>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" sizes="64x64" href="${prefix}assets/images/favicon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="${prefix}assets/images/favicon-32.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title</title>
  <meta name="description" content="$desc">
  <link rel="canonical" href="$canonical">
  <meta property="og:title" content="$title">
  <meta property="og:description" content="$desc">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://www.newrisemedical.com/assets/images/banner-hero.jpg">
  <meta property="og:site_name" content="Newrise Medical">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${prefix}assets/css/styles.css?v=$CSS_V">
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
        <a href="${prefix}index.html">Home</a> &raquo; $bc
      </div>
    </div>
  </section>
  <section class="section" id="page-$p">
    <div class="container">
      <div class="news-grid">
$body
      </div>
      $pag
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
  <script src="${prefix}assets/js/main.js?v=$CSS_V"></script>
</body>
</html>
EOF

  echo "  ✅ $outfile"
}

# Generate all pages
for ((p=1; p<=PAGES; p++)); do
  echo "📄 Page $p..."
  gen_page "$p"
done

# Remove stale page files
for old in "$SITE_DIR"/news-page-*.html; do
  [ -f "$old" ] || continue
  n=$(echo "$old" | sed -n 's/.*news-page-\([0-9]*\)\.html/\1/p')
  if [ -n "$n" ] && [ "$n" -gt "$PAGES" ]; then
    rm -f "$old"
    echo "  🗑️ Removed: $old"
  fi
done

echo "✅ Done! $TOTAL articles across $PAGES pages."