"""
MysteryDigest Researcher Module
Gathers unsolved mysteries, true crime, historical anomalies from free public sources.
Sources:
  1. Wikipedia API - articles from mystery/unsolved categories
  2. Reddit public JSON - r/UnresolvedMysteries, r/UnsolvedMysteries top posts
  3. RSS feeds from mystery/true-crime sites
  4. Wikipedia "On This Day" events
"""

import requests
import feedparser
import json
import random
import re
import hashlib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from pathlib import Path

HEADERS = {
    'User-Agent': 'MysteryDigest/1.0 (Educational Research Bot; +https://github.com/mysterydigest)'
}

CACHE_FILE = Path(__file__).parent / 'sent_cache.json'


def load_cache():
    """Load the deduplication cache."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {'sent_topics': []}
    return {'sent_topics': []}


def save_cache(cache):
    """Save the deduplication cache."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, default=str)


def get_topic_hash(title):
    """Generate a hash for deduplication."""
    normalized = re.sub(r'[^a-z0-9]', '', title.lower())
    return hashlib.md5(normalized.encode()).hexdigest()


def is_duplicate(title, cache):
    """Check if a topic was sent in the last 7 days."""
    topic_hash = get_topic_hash(title)
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    for entry in cache.get('sent_topics', []):
        if entry['hash'] == topic_hash and entry['date'] >= cutoff:
            return True
    return False


def mark_sent(titles, cache):
    """Mark topics as sent and clean old entries."""
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    # Clean old entries
    cache['sent_topics'] = [
        e for e in cache.get('sent_topics', [])
        if e['date'] >= cutoff
    ]
    # Add new entries
    for title in titles:
        cache['sent_topics'].append({
            'hash': get_topic_hash(title),
            'title': title,
            'date': datetime.now().isoformat()
        })
    save_cache(cache)


def fetch_wikipedia_mysteries():
    """Fetch mystery-related articles from Wikipedia API."""
    topics = []
    categories = [
        'Unsolved_murders', 'Unexplained_disappearances',
        'Conspiracy_theories', 'Historical_mysteries',
        'Paranormal_events', 'Unsolved_deaths',
        'Lost_places', 'Ancient_mysteries',
        'Unidentified_decedents', 'Cryptids'
    ]

    for category in categories[:6]:
        try:
            url = 'https://en.wikipedia.org/w/api.php'
            params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{category}',
                'cmlimit': '20',
                'cmtype': 'page',
                'format': 'json'
            }
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                members = data.get('query', {}).get('categorymembers', [])
                random.shuffle(members)
                for member in members[:3]:
                    page_title = member['title']
                    extract_params = {
                        'action': 'query',
                        'titles': page_title,
                        'prop': 'extracts',
                        'exintro': True,
                        'explaintext': True,
                        'exsentences': 3,
                        'format': 'json'
                    }
                    extract_resp = requests.get(
                        url, params=extract_params, headers=HEADERS, timeout=15
                    )
                    if extract_resp.status_code == 200:
                        pages = extract_resp.json().get('query', {}).get('pages', {})
                        for pid, pdata in pages.items():
                            extract = pdata.get('extract', '')
                            if extract and len(extract) > 50:
                                wiki_link = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                                topics.append({
                                    'title': page_title,
                                    'summary': extract[:200].strip(),
                                    'source': wiki_link,
                                    'source_name': 'Wikipedia'
                                })
        except Exception as e:
            print(f'Wikipedia error for {category}: {e}')
            continue

    return topics


def fetch_reddit_mysteries():
    """Fetch top posts from mystery subreddits via public JSON API."""
    topics = []
    subreddits = ['UnresolvedMysteries', 'UnsolvedMysteries', 'mystery', 'TrueCrime']

    for sub in subreddits:
        try:
            url = f'https://www.reddit.com/r/{sub}/hot.json?limit=15'
            resp = requests.get(url, headers={
                'User-Agent': 'MysteryDigest/1.0 (Educational Research Bot)'
            }, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get('data', {}).get('children', [])
                for post in posts:
                    pdata = post.get('data', {})
                    title = pdata.get('title', '')
                    selftext = pdata.get('selftext', '')
                    permalink = pdata.get('permalink', '')
                    if title and not pdata.get('stickied', False):
                        summary = selftext[:200].strip() if selftext else (
                            f"Discussion from r/{sub} about this mysterious topic."
                        )
                        link = (
                            f"https://www.reddit.com{permalink}"
                            if permalink
                            else f"https://www.reddit.com/r/{sub}"
                        )
                        topics.append({
                            'title': title[:150],
                            'summary': summary if len(summary) > 20 else (
                                f"An intriguing discussion from r/{sub} exploring this unsolved case."
                            ),
                            'source': link,
                            'source_name': f'Reddit r/{sub}'
                        })
        except Exception as e:
            print(f'Reddit error for r/{sub}: {e}')
            continue

    return topics


def fetch_rss_mysteries():
    """Fetch mystery articles from RSS feeds."""
    topics = []
    feeds = [
        ('https://listverse.com/feed/', 'Listverse'),
        ('https://www.atlasobscura.com/feeds/latest', 'Atlas Obscura'),
        ('https://mysteriousuniverse.org/feed/', 'Mysterious Universe'),
        ('https://www.historicmysteries.com/feed/', 'Historic Mysteries'),
    ]

    mystery_keywords = [
        'mystery', 'unsolved', 'unexplained', 'disappear', 'strange',
        'bizarre', 'haunted', 'paranormal', 'conspiracy', 'ancient',
        'crime', 'cold case', 'murder', 'vanish', 'secret', 'enigma',
        'unknown', 'puzzle', 'cryptid', 'legend', 'anomal'
    ]

    for feed_url, source_name in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')

                # Clean HTML from summary
                if summary:
                    summary = BeautifulSoup(summary, 'html.parser').get_text()
                    summary = summary[:200].strip()

                # Filter for mystery-related content
                text_to_check = (title + ' ' + summary).lower()
                if any(kw in text_to_check for kw in mystery_keywords):
                    if title and summary and len(summary) > 20:
                        topics.append({
                            'title': title[:150],
                            'summary': summary,
                            'source': link,
                            'source_name': source_name
                        })
        except Exception as e:
            print(f'RSS error for {source_name}: {e}')
            continue

    return topics


def fetch_wikipedia_on_this_day():
    """Fetch 'On this day' events from Wikipedia that are mysterious."""
    topics = []
    try:
        today = datetime.now()
        url = (
            f'https://en.wikipedia.org/api/rest_v1/feed/onthisday/events'
            f'/{today.month}/{today.day}'
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get('events', [])

            mystery_keywords = [
                'mystery', 'disappear', 'murder', 'unsolved', 'unknown',
                'strange', 'unexplained', 'conspiracy', 'assassination',
                'disaster', 'crash', 'vanish', 'lost', 'incident'
            ]

            for event in events:
                text = event.get('text', '')
                if any(kw in text.lower() for kw in mystery_keywords):
                    pages = event.get('pages', [])
                    link = ''
                    if pages:
                        page = pages[0]
                        link = (
                            page.get('content_urls', {})
                            .get('desktop', {})
                            .get('page', '')
                        )

                    topics.append({
                        'title': f"On This Day: {text[:100]}",
                        'summary': text[:200],
                        'source': link or 'https://en.wikipedia.org',
                        'source_name': 'Wikipedia On This Day'
                    })
    except Exception as e:
        print(f'Wikipedia On This Day error: {e}')

    return topics


def score_topic(topic):
    """Score a topic for mystery/interest value."""
    score = 0
    title_lower = topic['title'].lower()
    summary_lower = topic.get('summary', '').lower()
    combined = title_lower + ' ' + summary_lower

    high_value = ['unsolved', 'mystery', 'disappear', 'unexplained', 'cold case', 'vanish']
    medium_value = ['murder', 'strange', 'bizarre', 'haunted', 'conspiracy', 'enigma', 'cryptid']
    low_value = ['crime', 'ancient', 'secret', 'legend', 'anomal', 'paranormal']

    for kw in high_value:
        if kw in combined:
            score += 3
    for kw in medium_value:
        if kw in combined:
            score += 2
    for kw in low_value:
        if kw in combined:
            score += 1

    # Bonus for having a good summary
    if len(topic.get('summary', '')) > 80:
        score += 2

    # Bonus for having a direct source link
    if topic.get('source', '').startswith('http'):
        score += 1

    return score


def research_mysteries(count=10):
    """Main research function. Returns top N mysteries."""
    print('\n=== MysteryDigest Research Starting ===')
    print(f'Target: {count} topics')
    print(f'Time: {datetime.now().isoformat()}')

    cache = load_cache()
    all_topics = []

    # Gather from all sources
    print('\n[1/4] Fetching from Wikipedia categories...')
    wiki_topics = fetch_wikipedia_mysteries()
    print(f'  Found {len(wiki_topics)} topics from Wikipedia')
    all_topics.extend(wiki_topics)

    print('\n[2/4] Fetching from Reddit...')
    reddit_topics = fetch_reddit_mysteries()
    print(f'  Found {len(reddit_topics)} topics from Reddit')
    all_topics.extend(reddit_topics)

    print('\n[3/4] Fetching from RSS feeds...')
    rss_topics = fetch_rss_mysteries()
    print(f'  Found {len(rss_topics)} topics from RSS')
    all_topics.extend(rss_topics)

    print('\n[4/4] Fetching Wikipedia On This Day...')
    otd_topics = fetch_wikipedia_on_this_day()
    print(f'  Found {len(otd_topics)} topics from On This Day')
    all_topics.extend(otd_topics)

    print(f'\nTotal raw topics: {len(all_topics)}')

    # Deduplicate against cache
    fresh_topics = [t for t in all_topics if not is_duplicate(t['title'], cache)]
    print(f'After dedup: {len(fresh_topics)} fresh topics')

    # Score and sort
    scored = [(score_topic(t), t) for t in fresh_topics]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top N
    top_topics = [t for _, t in scored[:count]]

    # If we don't have enough, warn
    if len(top_topics) < count:
        print(f'Warning: Only found {len(top_topics)} unique topics (target: {count})')

    # Mark as sent
    mark_sent([t['title'] for t in top_topics], cache)

    print(f'\n=== Research Complete: {len(top_topics)} topics selected ===')
    return top_topics


if __name__ == '__main__':
    topics = research_mysteries(10)
    for i, t in enumerate(topics, 1):
        print(f"\n--- Topic {i} ---")
        print(f"Title: {t['title']}")
        print(f"Summary: {t['summary']}")
        print(f"Source: {t['source']}")
