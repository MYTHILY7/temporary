from newspaper import Article, build
from datetime import datetime, timedelta
from db_setup import ScrapedArticle, Session
from config import RSS_URLS

def fetch_articles(category):
    session = Session()
    new_count = 0
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)

    urls = RSS_URLS.get(category, [])
    if not urls:
        print(f"❌ No URLs found for category: {category}")
        return

    for site_url in urls:
        try:
            # Use newspaper3k to get all article links from the website
            paper = build(site_url, memoize_articles=False)
            print(f"🔍 Found {len(paper.articles)} articles at {site_url}")

            for content in paper.articles:
                try:
                    content.download()
                    content.parse()

                    # Skip if no publish date and fallback to current time
                    published = content.publish_date or now
                    
                    # Filter articles older than 1 week
                    if published < one_week_ago:
                        print(f"⏳ Skipped old article: {content.url}")
                        continue

                    # Check for duplicates
                    if session.query(ScrapedArticle).filter_by(url=content.url).first():
                        print(f"⚠️ Already exists: {content.url}")
                        continue

                    # Add article to DB
                    new_article = ScrapedArticle(
                        category=category,
                        title=content.title or "No Title",
                        url=content.url,
                        summary=(content.text[:1000] if content.text else "No Content"),
                        published_at=published
                    )

                    session.add(new_article)
                    new_count += 1
                    print(f"✅ Added: {content.url}")

                except Exception as e:
                    print(f"❌ Error scraping article: {content.url}\n{e}")

        except Exception as e:
            print(f"❌ Failed to load site: {site_url}\n{e}")

    session.commit()
    session.close()
    print(f"✅ {category}: {new_count} new articles scraped.")

# Example usage
if __name__ == "__main__":
    fetch_articles("CurrentTrends")
