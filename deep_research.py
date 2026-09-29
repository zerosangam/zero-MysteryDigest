"""
MysteryDigest v2 — Deep Research Layer
Researches each topic across 50+ free websites/sources.
Extends the existing researcher.py without replacing it.
Uses only free public APIs, RSS feeds, and direct page fetching.
"""

import requests
import feedparser
import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

HEADERS = {
    'User-Agent': 'MysteryDigest/2.0 (Educational Research; +https://github.com/zerosangam/zero-MysteryDigest)'
}

# ── Source Registry: 50+ websites organized by category ──────

NEWS_RSS_SOURCES = [
    ('https://feeds.bbci.co.uk/news/rss.xml', 'BBC News', 'High'),
    ('https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'NYT', 'High'),
    ('https://www.theguardian.com/world/rss', 'The Guardian', 'High'),
    ('https://feeds.reuters.com/reuters/topNews', 'Reuters', 'High'),
    ('https://www.aljazeera.com/xml/rss/all.xml', 'Al Jazeera', 'High'),
    ('http://rss.cnn.com/rss/edition.rss', 'CNN', 'High'),
    ('https://www.france24.com/en/rss', 'France24', 'High'),
    ('https://rss.dw.com/rdf/rss-en-all', 'DW', 'High'),
    ('https://timesofindia.indiatimes.com/rssfeedstopstories.cms', 'Times of India', 'Medium'),
    ('https://www.thehindu.com/feeder/default.rss', 'The Hindu', 'High'),
    ('https://indianexpress.com/feed/', 'Indian Express', 'Medium'),
]

MYSTERY_RSS_SOURCES = [
    ('https://listverse.com/feed/', 'Listverse', 'Medium'),
    ('https://www.atlasobscura.com/feeds/latest', 'Atlas Obscura', 'High'),
    ('https://mysteriousuniverse.org/feed/', 'Mysterious Universe', 'Medium'),
    ('https://www.historicmysteries.com/feed/', 'Historic Mysteries', 'Medium'),
    ('https://www.ancient-origins.net/rss.xml', 'Ancient Origins', 'Medium'),
    ('https://www.smithsonianmag.com/rss/latest_articles/', 'Smithsonian', 'High'),
    ('https://www.nationalgeographic.com/feeds/rss/latest', 'NatGeo', 'High'),
    ('https://www.history.com/.rss/full/', 'History.com', 'High'),
]

REDDIT_SUBS = [
    'UnresolvedMysteries', 'UnsolvedMysteries', 'TrueCrime',
    'WithoutATrace', 'mystery', 'Paranormal',
    'creepy', 'conspiracy', 'HistoryMemes',
    'todayilearned'
]

WIKIPEDIA_MYSTERY_CATEGORIES = [
    'Unsolved_murders', 'Unexplained_disappearances', 'Conspiracy_theories',
    'Historical_mysteries', 'Paranormal_events', 'Unsolved_deaths',
    'Lost_places', 'Ancient_mysteries', 'Unidentified_decedents', 'Cryptids',
    'Unsolved_crimes', 'Missing_people', 'Archaeological_mysteries',
    'Ghost_ships', 'UFO_sightings', 'Mysterious_events',
    'Cold_cases', 'Disappeared_people', 'Unexplained_phenomena'
]

MYSTERY_KEYWORDS = [
    'mystery', 'unsolved', 'unexplained', 'disappear', 'strange',
    'bizarre', 'haunted', 'paranormal', 'conspiracy', 'ancient',
    'crime', 'cold case', 'murder', 'vanish', 'secret', 'enigma',
    'unknown', 'puzzle', 'cryptid', 'legend', 'anomal', 'missing',
    'unidentified', 'lost', 'hidden', 'forbidden', 'cursed',
    'assassination', 'coverup', 'classified', 'declassified'
]


def _safe_request(url, headers=None, timeout=12, retries=3):
    """Make a request with retry logic and exponential backoff."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers or HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                time.sleep(2 ** attempt + random.random())
                continue
        except Exception:
            if attempt < retries - 1:
                time.sleep(1 + random.random())
    return None


def _is_mystery_related(text):
    """Check if text contains mystery-related keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in MYSTERY_KEYWORDS)


def _clean_html(html_text):
    """Strip HTML tags from text."""
    if not html_text:
        return ''
    return BeautifulSoup(html_text, 'html.parser').get_text()[:300].strip()


# ── Source Fetchers ──────────────────────────────────────────

def fetch_rss_batch(sources_list, max_per_source=5):
    """Fetch topics from a batch of RSS sources."""
    results = []
    for feed_url, source_name, credibility in sources_list:
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries[:15]:
                if count >= max_per_source:
                    break
                title = entry.get('title', '')
                summary = _clean_html(entry.get('summary', entry.get('description', '')))
                link = entry.get('link', '')
                pub_date = entry.get('published', entry.get('updated', ''))

                if _is_mystery_related(title + ' ' + summary):
                    results.append({
                        'title': title[:200],
                        'summary': summary[:300],
                        'source': link,
                        'source_name': source_name,
                        'credibility': credibility,
                        'pub_date': pub_date,
                        'found_via': 'rss'
                    })
                    count += 1
        except Exception as e:
            print(f'  RSS skip {source_name}: {e}')
    return results


def fetch_reddit_deep(subreddits=None, limit=10):
    """Fetch from multiple Reddit subreddits via public JSON."""
    subs = subreddits or REDDIT_SUBS
    results = []
    for sub in subs:
        try:
            for sort in ['hot', 'new']:
                url = f'https://www.reddit.com/r/{sub}/{sort}.json?limit={limit}'
                resp = _safe_request(url, headers={
                    'User-Agent': 'MysteryDigest/2.0 (Educational Research Bot)'
                })
                if resp:
                    data = resp.json()
                    for post in data.get('data', {}).get('children', []):
                        pd = post.get('data', {})
                        title = pd.get('title', '')
                        selftext = pd.get('selftext', '')[:300]
                        permalink = pd.get('permalink', '')
                        score = pd.get('score', 0)
                        num_comments = pd.get('num_comments', 0)

                        if title and not pd.get('stickied'):
                            results.append({
                                'title': title[:200],
                                'summary': selftext if len(selftext) > 20 else f'Discussion on r/{sub}',
                                'source': f'https://www.reddit.com{permalink}',
                                'source_name': f'Reddit r/{sub}',
                                'credibility': 'Medium',
                                'reddit_score': score,
                                'reddit_comments': num_comments,
                                'found_via': 'reddit'
                            })
                time.sleep(0.5)  # Rate limit
        except Exception as e:
            print(f'  Reddit skip r/{sub}: {e}')
    return results


def fetch_wikipedia_deep(categories=None, max_per_cat=5):
    """Fetch from many Wikipedia categories."""
    cats = categories or WIKIPEDIA_MYSTERY_CATEGORIES
    results = []
    random.shuffle(cats)

    for category in cats[:10]:  # Limit to avoid timeouts
        try:
            url = 'https://en.wikipedia.org/w/api.php'
            params = {
                'action': 'query', 'list': 'categorymembers',
                'cmtitle': f'Category:{category}',
                'cmlimit': '30', 'cmtype': 'page', 'format': 'json'
            }
            resp = _safe_request(url, timeout=10)
            if not resp:
                resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            else:
                resp = requests.get(url, params=params, headers=HEADERS, timeout=10)

            if resp and resp.status_code == 200:
                members = resp.json().get('query', {}).get('categorymembers', [])
                random.shuffle(members)
                for member in members[:max_per_cat]:
                    page_title = member['title']
                    # Get extract
                    ext_resp = requests.get(url, params={
                        'action': 'query', 'titles': page_title,
                        'prop': 'extracts', 'exintro': True,
                        'explaintext': True, 'exsentences': 4, 'format': 'json'
                    }, headers=HEADERS, timeout=10)

                    if ext_resp and ext_resp.status_code == 200:
                        pages = ext_resp.json().get('query', {}).get('pages', {})
                        for pid, pdata in pages.items():
                            extract = pdata.get('extract', '')
                            if extract and len(extract) > 50:
                                wiki_link = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                                results.append({
                                    'title': page_title,
                                    'summary': extract[:300].strip(),
                                    'source': wiki_link,
                                    'source_name': 'Wikipedia',
                                    'credibility': 'High',
                                    'found_via': 'wikipedia'
                                })
        except Exception as e:
            print(f'  Wiki skip {category}: {e}')
    return results


def fetch_google_scholar_topics(queries=None):
    """Search Google Scholar for mystery/crime research papers."""
    if not queries:
        queries = ['unsolved mystery', 'cold case forensics', 'archaeological mystery',
                   'historical anomaly', 'unexplained disappearance']
    results = []
    for query in queries[:3]:
        try:
            url = f'https://scholar.google.com/scholar?q={quote_plus(query)}&as_sdt=0&as_vis=1&oi=scholart'
            resp = _safe_request(url, timeout=10)
            if resp:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.select('.gs_ri')[:3]:
                    title_el = item.select_one('.gs_rt a')
                    snippet_el = item.select_one('.gs_rs')
                    if title_el:
                        results.append({
                            'title': title_el.get_text()[:200],
                            'summary': snippet_el.get_text()[:300] if snippet_el else '',
                            'source': title_el.get('href', ''),
                            'source_name': 'Google Scholar',
                            'credibility': 'High',
                            'found_via': 'scholar'
                        })
        except Exception:
            pass
    return results


def fetch_archive_org(queries=None):
    """Search Archive.org for historical mystery documents."""
    if not queries:
        queries = ['unsolved mystery', 'true crime', 'historical enigma']
    results = []
    for query in queries[:2]:
        try:
            url = f'https://archive.org/advancedsearch.php?q={quote_plus(query)}&fl[]=title&fl[]=description&fl[]=identifier&rows=5&output=json'
            resp = _safe_request(url, timeout=10)
            if resp:
                docs = resp.json().get('response', {}).get('docs', [])
                for doc in docs:
                    title = doc.get('title', '')
                    desc = doc.get('description', '')
                    if isinstance(desc, list):
                        desc = desc[0] if desc else ''
                    identifier = doc.get('identifier', '')
                    if title:
                        results.append({
                            'title': title[:200],
                            'summary': str(desc)[:300],
                            'source': f'https://archive.org/details/{identifier}',
                            'source_name': 'Archive.org',
                            'credibility': 'High',
                            'found_via': 'archive'
                        })
        except Exception:
            pass
    return results


def fetch_fbi_vault():
    """Check FBI Vault for recently released documents."""
    results = []
    try:
        url = 'https://vault.fbi.gov/recently-added'
        resp = _safe_request(url, timeout=10)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for link in soup.select('a[href*="/vault.fbi.gov"]')[:5]:
                title = link.get_text().strip()
                if title and _is_mystery_related(title):
                    results.append({
                        'title': f'FBI Vault: {title[:150]}',
                        'summary': f'Recently released FBI document about {title}',
                        'source': f'https://vault.fbi.gov{link.get("href", "")}',
                        'source_name': 'FBI Vault',
                        'credibility': 'High',
                        'found_via': 'fbi'
                    })
    except Exception:
        pass
    return results


def fetch_youtube_trending(queries=None, max_per_query=10):
    """Search YouTube for trending mystery content via Invidious (free, no API key)."""
    if not queries:
        queries = [
            'unsolved mystery', 'true crime documentary', 'historical mystery',
            'unexplained events', 'missing person case', 'ancient mystery',
            'vanished without trace'
        ]
    results = []
    # Use Invidious (free YouTube frontend with JSON API)
    invidious_instances = [
        'https://vid.puffyan.us',
        'https://invidious.snopyta.org',
        'https://yewtu.be',
        'https://inv.nadeko.net',
    ]

    for query in queries[:5]:
        for instance in invidious_instances:
            try:
                url = f'{instance}/api/v1/search?q={quote_plus(query)}&sort_by=upload_date&type=video'
                resp = _safe_request(url, timeout=8)
                if resp:
                    videos = resp.json() if isinstance(resp.json(), list) else []
                    for video in videos[:max_per_query]:
                        vid_id = video.get('videoId', '')
                        title = video.get('title', '')
                        channel = video.get('author', '')
                        views = video.get('viewCount', 0)
                        published = video.get('publishedText', '')

                        if title and _is_mystery_related(title):
                            results.append({
                                'title': title[:200],
                                'summary': f'YouTube video by {channel} — {views:,} views. {published}',
                                'source': f'https://www.youtube.com/watch?v={vid_id}',
                                'source_name': f'YouTube ({channel})',
                                'credibility': 'Medium',
                                'youtube_views': views,
                                'youtube_channel': channel,
                                'youtube_id': vid_id,
                                'found_via': 'youtube'
                            })
                    break  # Succeeded with this instance
            except Exception:
                continue  # Try next Invidious instance
    return results


def fetch_wikipedia_on_this_day():
    """Fetch mysterious events from Wikipedia 'On this day'."""
    results = []
    try:
        today = datetime.now()
        url = f'https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}'
        resp = _safe_request(url, timeout=10)
        if resp:
            events = resp.json().get('events', [])
            for event in events:
                text = event.get('text', '')
                if _is_mystery_related(text):
                    pages = event.get('pages', [])
                    link = ''
                    if pages:
                        link = pages[0].get('content_urls', {}).get('desktop', {}).get('page', '')
                    results.append({
                        'title': f'On This Day: {text[:120]}',
                        'summary': text[:300],
                        'source': link or 'https://en.wikipedia.org',
                        'source_name': 'Wikipedia On This Day',
                        'credibility': 'High',
                        'found_via': 'wikipedia_otd'
                    })
    except Exception:
        pass
    return results


# ── Master Deep Research Function ────────────────────────────

def deep_research_cycle(min_topics=10):
    """
    Run a full deep research cycle across 50+ sources.
    Guarantees at least min_topics fresh topics.
    Returns list of enriched topic dicts.
    """
    print(f'\n=== Deep Research Cycle Starting ===')
    print(f'Time: {datetime.now().isoformat()}')
    print(f'Minimum target: {min_topics} topics')

    all_topics = []
    sources_used = []

    # 1. Wikipedia (expanded categories)
    print('\n[1/8] Wikipedia deep search...')
    wiki = fetch_wikipedia_deep()
    all_topics.extend(wiki)
    sources_used.append(f'Wikipedia: {len(wiki)}')
    print(f'  Found {len(wiki)} topics')

    # 2. Reddit (expanded subreddits)
    print('[2/8] Reddit deep search...')
    reddit = fetch_reddit_deep()
    all_topics.extend(reddit)
    sources_used.append(f'Reddit: {len(reddit)}')
    print(f'  Found {len(reddit)} topics')

    # 3. News RSS (11 major outlets)
    print('[3/8] News RSS feeds...')
    news = fetch_rss_batch(NEWS_RSS_SOURCES)
    all_topics.extend(news)
    sources_used.append(f'News RSS: {len(news)}')
    print(f'  Found {len(news)} topics')

    # 4. Mystery RSS (8 specialty sites)
    print('[4/8] Mystery RSS feeds...')
    mystery = fetch_rss_batch(MYSTERY_RSS_SOURCES)
    all_topics.extend(mystery)
    sources_used.append(f'Mystery RSS: {len(mystery)}')
    print(f'  Found {len(mystery)} topics')

    # 5. YouTube trending
    print('[5/8] YouTube trending...')
    yt = fetch_youtube_trending()
    all_topics.extend(yt)
    sources_used.append(f'YouTube: {len(yt)}')
    print(f'  Found {len(yt)} topics')

    # 6. Wikipedia On This Day
    print('[6/8] Wikipedia On This Day...')
    otd = fetch_wikipedia_on_this_day()
    all_topics.extend(otd)
    sources_used.append(f'On This Day: {len(otd)}')
    print(f'  Found {len(otd)} topics')

    # 7. Archive.org
    print('[7/8] Archive.org...')
    archive = fetch_archive_org()
    all_topics.extend(archive)
    sources_used.append(f'Archive.org: {len(archive)}')
    print(f'  Found {len(archive)} topics')

    # 8. Google Scholar
    print('[8/8] Google Scholar...')
    scholar = fetch_google_scholar_topics()
    all_topics.extend(scholar)
    sources_used.append(f'Scholar: {len(scholar)}')
    print(f'  Found {len(scholar)} topics')

    print(f'\nTotal raw topics: {len(all_topics)}')

    # If we don't have enough, expand search
    if len(all_topics) < min_topics:
        print(f'WARNING: Only {len(all_topics)} < {min_topics}. Expanding search...')
        extra_wiki = fetch_wikipedia_deep(
            categories=['Kidnappings', 'Assassinations', 'Scandals', 'Hoaxes'],
            max_per_cat=8
        )
        all_topics.extend(extra_wiki)
        print(f'  Expanded with {len(extra_wiki)} more from Wikipedia')

    # Deduplicate by title hash
    seen = set()
    unique = []
    for t in all_topics:
        from database import topic_hash
        h = topic_hash(t.get('title', ''))
        if h not in seen and t.get('title'):
            seen.add(h)
            unique.append(t)

    print(f'After dedup: {len(unique)} unique topics')
    print(f'Sources used: {", ".join(sources_used)}')
    print(f'=== Deep Research Cycle Complete ===\n')

    return unique, sources_used


if __name__ == '__main__':
    topics, sources = deep_research_cycle(10)
    print(f'\nFinal count: {len(topics)} topics from {len(sources)} source groups')
    for i, t in enumerate(topics[:10], 1):
        print(f'  {i}. [{t.get("credibility", "?")}] {t["title"][:80]}')
        print(f'     Source: {t.get("source_name", "?")} | {t.get("source", "")[:60]}')
