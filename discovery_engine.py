import urllib.parse
import requests
from bs4 import BeautifulSoup
import central_core

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

DIRECTORY_BLACKLIST = {"justdial.com", "practo.com", "sulekha.com", "yelp.com", "tripadvisor.in", "facebook.com", "instagram.com"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def deep_discover_urls(category, city):
    query = f'{category} in {city} official website contact email -justdial -practo'
    candidates = set()
    if DDGS:
        try:
            ddgs = DDGS()
            for r in ddgs.text(query, max_results=10):
                if r.get("href"): candidates.add(r["href"])
        except Exception:
            pass
    
    final_urls = []
    for url in candidates:
        netloc = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        if netloc and not any(b in netloc for b in DIRECTORY_BLACKLIST):
            final_urls.append(url)
    return final_urls
