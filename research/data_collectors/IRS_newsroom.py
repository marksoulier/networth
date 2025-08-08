import feedparser

def fetch_irs_newsroom():
    feed_url = "https://www.irs.gov/rss/irsnewsreleases.xml"
    feed = feedparser.parse(feed_url)
    print("feed.feed contents:")
    print(feed.feed)

if __name__ == "__main__":
    fetch_irs_newsroom() 