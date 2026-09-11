#!/bin/bash
# Daily article publish & deploy script
# Usage: ./publish.sh <article-file>
#   article-file: path to an article HTML file (from news/drafts/ or news/)
# If no file given, publishes the most recent untracked .html in news/
set -euo pipefail
cd /Users/lobster/workspace/lali

ARTICLE="$1"

if [ -n "$ARTICLE" ]; then
  if [ ! -f "$ARTICLE" ]; then
    echo "Error: file not found: $ARTICLE"
    exit 1
  fi
else
  # Find the most recent untracked .html in news/ (excluding template)
  LATEST=$(git status --porcelain news/ | grep '?? ' | grep -v 'article-template.html' | grep '\.html$' | head -1 | awk '{print $2}')
  if [ -z "$LATEST" ]; then
    echo "No new articles found."
    exit 0
  fi
  ARTICLE="$LATEST"
  echo "Auto-selected: $ARTICLE"
fi

# Check if article page already exists in repo
BASENAME=$(basename "$ARTICLE")
if [ -f "news/$BASENAME" ] && git ls-files --error-unmatch "news/$BASENAME" >/dev/null 2>&1; then
  echo "Article already tracked: news/$BASENAME"
else
  # Move to news/ if not already there
  if [[ "$ARTICLE" != news/* ]]; then
    mv "$ARTICLE" "news/$BASENAME"
  fi
  git add "news/$BASENAME"
  echo "Added news/$BASENAME"
fi

# Extract metadata from the article file
TITLE=$(sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' "news/$BASENAME" | sed 's/ – Newrise Medical$//')
DATE_LINE=$(sed -n 's/.*📅 \([A-Za-z]* [A-Za-z]* [0-9]*, [0-9]\{4\}\).*/\1/p' "news/$BASENAME" | head -1 || echo "")
TAG=$(sed -n 's/.*🏷️ \([^<]*\)<.*/\1/p' "news/$BASENAME" | head -1 || echo "Industry News")
IMG_SRC=$(sed -n 's/.*src="\([^"]*\.jpg\)".*/\1/p' "news/$BASENAME" | head -1 || echo "banner-hero.jpg")
IMG_SRC=$(basename "$IMG_SRC")
DESCRIPTION=$(grep -oP '<meta name="description" content="\K[^"]+' "news/$BASENAME" | head -1 || echo "")

# Parse date for slug sorting
DATE_PART=$(echo "$BASENAME" | sed -n 's/^\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p' || echo "")
if [ -n "$DATE_LINE" ]; then
  CARD_DATE="$DATE_LINE"
elif [ -n "$DATE_PART" ]; then
  # Convert YYYY-MM-DD to "Month Day, YYYY"
  CARD_DATE=$(date -d "$DATE_PART" "+%B %e, %Y" 2>/dev/null || echo "$DATE_PART")
  # Remove leading zero from day (macOS compatible)
  CARD_DATE=$(echo "$CARD_DATE" | sed 's/ 0/ /g')
else
  CARD_DATE=$(date "+%B %e, %Y" | sed 's/ 0/ /g')
fi

# Update news.html - insert new card after the first <div class="news-grid"> or after <main>
CARD_HTML="<article class=\"news-card\">
          <div class=\"news-image\">
            <img src=\"assets/images/$IMG_SRC\" alt=\"$TITLE\" loading=\"lazy\">
          </div>
          <div class=\"news-content\">
            <div class=\"news-date\">$CARD_DATE</div>
            <h3><a href=\"news/$BASENAME\">$TITLE</a></h3>
            <p>$DESCRIPTION</p>
            <a href=\"news/$BASENAME\" class=\"btn btn-sm btn-primary\" style=\"margin-top:12px;\">Read More &rarr;</a>
          </div>
        </article>"

# Check if card already exists
if grep -q "$BASENAME" news.html; then
  echo "Card already exists in news.html"
else
  # Insert after <div class="news-grid">
  if grep -q 'class="news-grid"' news.html; then
    sed -i '' "/<div class=\"news-grid\">/a\\
$CARD_HTML
" news.html
  else
    echo "Warning: could not find news-grid in news.html"
  fi
  echo "Added card to news.html"
fi

# Update sitemap.xml
if ! grep -q "$BASENAME" sitemap.xml; then
  # Get today's date for lastmod
  TODAY=$(date "+%Y-%m-%d")
  # Insert after the news.html url block
  NEWS_ENTRY="  <url>
    <loc>https://www.newrisemedical.com/news/$BASENAME</loc>
    <lastmod>$TODAY</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>"
  # Insert after news.html block
  sed -i '' "/<loc>https:\/\/www.newrisemedical.com\/news.html<\/loc>/,/<\/url>/{
    /<\/url>/a\\
$NEWS_ENTRY
  }" sitemap.xml
  echo "Added $BASENAME to sitemap.xml"
else
  echo "Already in sitemap.xml"
fi

# Commit and push
git add news.html sitemap.xml "news/$BASENAME"
git -c user.name='NewriseBot' -c user.email='bot@newrisemedical.com' commit -m "New article: $TITLE" 2>/dev/null || echo "Nothing to commit"
git push 2>&1
echo "✅ Published: $BASENAME"
