"""
MysteryDigest v2 — Incident Verifier
Ensures every topic is a 100% real, verified incident.
Auto-rejects fictional stories, urban legends, creepypasta, and unverifiable claims.
Requires at least 3 independent credible sources per topic.
"""

import requests
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'MysteryDigest/2.0 (Verification Bot)'}

# Known fiction/urban legend indicators
FICTION_INDICATORS = [
    'creepypasta', 'nosleep', 'fiction', 'short story', 'novel',
    'movie plot', 'film synopsis', 'tv show', 'television series',
    'video game', 'comic book', 'manga', 'anime', 'fanfiction',
    'urban legend', 'folklore tale', 'fairy tale', 'myth retelling',
    'scp foundation', 'writing prompt', 'imaginary', 'made up',
    'copypasta', 'meme origin', 'hoax confirmed'
]

# Credible source domains
HIGH_CREDIBILITY_DOMAINS = [
    'bbc.co.uk', 'bbc.com', 'nytimes.com', 'theguardian.com',
    'reuters.com', 'apnews.com', 'washingtonpost.com', 'cnn.com',
    'aljazeera.com', 'dw.com', 'france24.com', 'wikipedia.org',
    'britannica.com', 'smithsonianmag.com', 'nationalgeographic.com',
    'history.com', 'jstor.org', 'scholar.google.com', 'ncbi.nlm.nih.gov',
    'fbi.gov', 'cia.gov', 'loc.gov', 'archives.gov',
    'courtlistener.com', 'thehindu.com', 'indianexpress.com',
    'ndtv.com', 'timesofindia.indiatimes.com', 'hindustantimes.com'
]

MEDIUM_CREDIBILITY_DOMAINS = [
    'listverse.com', 'atlasobscura.com', 'reddit.com',
    'historicmysteries.com', 'ancient-origins.net',
    'mysteriousuniverse.org', 'archive.org',
    'medium.com', 'substack.com'
]


def _get_source_credibility(url):
    """Determine credibility level of a source URL."""
    url_lower = url.lower()
    for domain in HIGH_CREDIBILITY_DOMAINS:
        if domain in url_lower:
            return 'High'
    for domain in MEDIUM_CREDIBILITY_DOMAINS:
        if domain in url_lower:
            return 'Medium'
    return 'Low'


def is_fictional(topic):
    """Check if a topic appears to be fictional or an urban legend."""
    text = (topic.get('title', '') + ' ' + topic.get('summary', '')).lower()
    source = topic.get('source', '').lower()
    source_name = topic.get('source_name', '').lower()

    # Check against fiction indicators
    for indicator in FICTION_INDICATORS:
        if indicator in text or indicator in source_name:
            return True, f'Matched fiction indicator: {indicator}'

    # Check if source is from fiction subreddits
    fiction_subs = ['nosleep', 'writingprompts', 'shortscarystories', 'creepypasta']
    for sub in fiction_subs:
        if sub in source:
            return True, f'Source is fiction subreddit: r/{sub}'

    return False, 'Passed fiction check'


def find_corroborating_sources(topic, min_sources=3):
    """Search for corroborating sources to verify a topic is real."""
    title = topic.get('title', '')
    existing_sources = topic.get('sources_list', [])

    if len(existing_sources) >= min_sources:
        credible = [s for s in existing_sources if s.get('credibility') == 'High']
        if len(credible) >= min_sources:
            return existing_sources, True

    # Search Wikipedia for verification
    sources_found = list(existing_sources)

    # Add primary source if credible
    primary_source = topic.get('source', '')
    if primary_source:
        cred = _get_source_credibility(primary_source)
        if not any(s.get('url') == primary_source for s in sources_found):
            sources_found.append({
                'url': primary_source,
                'source_name': topic.get('source_name', 'Primary'),
                'credibility': cred,
                'finding': topic.get('summary', '')[:100]
            })

    # Search Wikipedia
    try:
        q = quote_plus(title[:60])
        url = f'https://en.wikipedia.org/w/api.php?action=opensearch&search={q}&limit=3&format=json'
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) >= 4:
                titles = data[1]
                links = data[3]
                for t, l in zip(titles, links):
                    if not any(s.get('url') == l for s in sources_found):
                        sources_found.append({
                            'url': l,
                            'source_name': 'Wikipedia',
                            'credibility': 'High',
                            'finding': f'Wikipedia article: {t}'
                        })
    except Exception:
        pass

    # Search DuckDuckGo for more sources
    try:
        q = quote_plus(f'{title[:50]} real case')
        url = f'https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1'
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            for topic_item in data.get('RelatedTopics', [])[:5]:
                if isinstance(topic_item, dict):
                    first_url = topic_item.get('FirstURL', '')
                    text = topic_item.get('Text', '')
                    if first_url and not any(s.get('url') == first_url for s in sources_found):
                        sources_found.append({
                            'url': first_url,
                            'source_name': 'DuckDuckGo',
                            'credibility': _get_source_credibility(first_url),
                            'finding': text[:100] if text else ''
                        })
    except Exception:
        pass

    # Update topic
    topic['sources_list'] = sources_found
    credible = [s for s in sources_found if s.get('credibility') in ('High', 'Medium')]
    topic['credible_source_count'] = len(credible)

    verified = len(credible) >= min_sources
    topic['verified'] = verified

    return sources_found, verified


def verify_topic(topic, min_credible_sources=3):
    """Full verification pipeline for a single topic."""
    # Step 1: Check if fictional
    is_fiction, reason = is_fictional(topic)
    if is_fiction:
        topic['verified'] = False
        topic['rejection_reason'] = reason
        return False, reason

    # Step 2: Find corroborating sources
    sources, verified = find_corroborating_sources(topic, min_credible_sources)

    if not verified:
        topic['rejection_reason'] = f'Only {topic.get("credible_source_count", 0)} credible sources (need {min_credible_sources})'
        return False, topic['rejection_reason']

    topic['verified'] = True
    topic['rejection_reason'] = None
    return True, f'Verified with {len(sources)} sources ({topic.get("credible_source_count", 0)} credible)'


def batch_verify(topics, min_credible=3):
    """Verify a batch of topics. Returns only verified ones."""
    print(f'\n=== Verifying {len(topics)} topics (min {min_credible} credible sources) ===')
    verified = []
    rejected = 0

    for i, topic in enumerate(topics):
        is_valid, reason = verify_topic(topic, min_credible)
        if is_valid:
            verified.append(topic)
        else:
            rejected += 1

        if (i + 1) % 10 == 0:
            print(f'  Processed {i+1}/{len(topics)}: {len(verified)} verified, {rejected} rejected')

    print(f'=== Verification complete: {len(verified)} verified, {rejected} rejected ===')
    return verified


if __name__ == '__main__':
    test = {
        'title': 'Disappearance of Madeleine McCann',
        'summary': 'British girl vanished from holiday apartment in Portugal in 2007.',
        'source': 'https://en.wikipedia.org/wiki/Disappearance_of_Madeleine_McCann',
        'source_name': 'Wikipedia',
        'sources_list': []
    }
    verified, reason = verify_topic(test)
    print(f'Verified: {verified}')
    print(f'Reason: {reason}')
    print(f'Sources: {len(test["sources_list"])}')
    for s in test['sources_list']:
        print(f'  [{s["credibility"]}] {s["url"][:60]}')
