"""
MysteryDigest v2 — Viral Scoring Algorithm
Scores topics on a 1-10 scale based on multiple free signals.
Weights:
  - YouTube trending velocity: 25%
  - Google Trends growth: 20%
  - Reddit engagement velocity: 20%
  - Twitter/X mention signal: 15%
  - News coverage frequency: 10%
  - Intrigue / unsolved nature: 10%

A topic is "100% VIRAL" only if score >= 8.0
"""

import requests
import time
import re
from urllib.parse import quote_plus
from datetime import datetime

HEADERS = {
    'User-Agent': 'MysteryDigest/2.0 (Educational Research Bot)'
}


def _safe_get(url, timeout=8):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        return resp if resp.status_code == 200 else None
    except Exception:
        return None


# ── Individual Signal Scorers (0.0 - 10.0 each) ─────────────

def score_youtube_velocity(topic):
    """Score based on YouTube view count and recency. 0-10."""
    views = topic.get('youtube_views', 0)
    if views <= 0:
        # Try to find YouTube data via search
        try:
            instances = ['https://vid.puffyan.us', 'https://inv.nadeko.net']
            q = quote_plus(topic.get('title', '')[:60])
            for inst in instances:
                resp = _safe_get(f'{inst}/api/v1/search?q={q}&type=video&sort_by=relevance', timeout=6)
                if resp:
                    videos = resp.json() if isinstance(resp.json(), list) else []
                    if videos:
                        views = videos[0].get('viewCount', 0)
                        topic['youtube_views'] = views
                        topic['youtube_id'] = videos[0].get('videoId', '')
                    break
        except Exception:
            pass

    if views >= 1_000_000:
        return 10.0
    elif views >= 500_000:
        return 8.5
    elif views >= 100_000:
        return 7.0
    elif views >= 50_000:
        return 5.5
    elif views >= 10_000:
        return 4.0
    elif views >= 1_000:
        return 2.5
    elif views > 0:
        return 1.5
    return 1.0


def score_reddit_engagement(topic):
    """Score based on Reddit upvotes and comments. 0-10."""
    reddit_score = topic.get('reddit_score', 0)
    comments = topic.get('reddit_comments', 0)

    if reddit_score <= 0 and comments <= 0:
        # Try searching Reddit for this topic
        try:
            q = quote_plus(topic.get('title', '')[:50])
            url = f'https://www.reddit.com/search.json?q={q}&sort=relevance&limit=3'
            resp = _safe_get(url, timeout=8)
            if resp:
                posts = resp.json().get('data', {}).get('children', [])
                for p in posts:
                    pd = p.get('data', {})
                    reddit_score = max(reddit_score, pd.get('score', 0))
                    comments = max(comments, pd.get('num_comments', 0))
                topic['reddit_score'] = reddit_score
                topic['reddit_comments'] = comments
        except Exception:
            pass

    combined = reddit_score + (comments * 3)
    if combined >= 10000:
        return 10.0
    elif combined >= 5000:
        return 8.0
    elif combined >= 2000:
        return 6.5
    elif combined >= 500:
        return 5.0
    elif combined >= 100:
        return 3.5
    elif combined > 0:
        return 2.0
    return 1.0


def score_google_trends(topic):
    """Estimate Google Trends interest. Uses search result count as proxy. 0-10."""
    try:
        q = quote_plus(topic.get('title', '')[:50] + ' mystery')
        # Use DuckDuckGo instant answer as free proxy
        url = f'https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1'
        resp = _safe_get(url, timeout=6)
        if resp:
            data = resp.json()
            # Check if there's a significant response
            abstract = data.get('Abstract', '')
            related = data.get('RelatedTopics', [])
            results_count = len(related)

            if abstract and len(abstract) > 100:
                return min(8.0, 4.0 + results_count * 0.5)
            elif results_count > 5:
                return min(7.0, 3.0 + results_count * 0.4)
            elif results_count > 0:
                return 2.5
    except Exception:
        pass
    return 1.5


def score_twitter_signal(topic):
    """Estimate Twitter/X mentions. Uses Nitter instances as proxy. 0-10."""
    # Without Twitter API, we use a keyword-based heuristic
    title = topic.get('title', '').lower()

    # High-signal keywords that tend to go viral on Twitter
    viral_terms = ['breaking', 'update', 'new evidence', 'found', 'identified',
                   'solved', 'arrest', 'charged', 'dna', 'body found']
    trending_terms = ['missing', 'disappear', 'unsolved', 'cold case', 'mystery']

    score = 1.0
    for term in viral_terms:
        if term in title:
            score += 1.5
    for term in trending_terms:
        if term in title:
            score += 0.8

    return min(10.0, score)


def score_news_coverage(topic):
    """Score based on how many credible sources cover this topic. 0-10."""
    sources_list = topic.get('sources_list', [])
    credible_count = sum(1 for s in sources_list if s.get('credibility') == 'High')
    total = len(sources_list)

    if credible_count >= 5:
        return 9.0
    elif credible_count >= 3:
        return 7.0
    elif credible_count >= 1:
        return 5.0
    elif total >= 3:
        return 3.5
    elif total >= 1:
        return 2.0
    return 1.0


def score_intrigue(topic):
    """Score based on how mysterious/unsolved the topic is. 0-10."""
    text = (topic.get('title', '') + ' ' + topic.get('summary', '')).lower()

    score = 1.0
    high_intrigue = ['unsolved', 'unexplained', 'vanished', 'mysterious disappearance',
                     'without trace', 'no body', 'cold case', 'never found',
                     'unidentified', 'unknown killer', 'baffling']
    medium_intrigue = ['mystery', 'strange', 'bizarre', 'haunted', 'paranormal',
                       'conspiracy', 'cover up', 'classified', 'forbidden']

    for kw in high_intrigue:
        if kw in text:
            score += 1.5
    for kw in medium_intrigue:
        if kw in text:
            score += 0.8

    return min(10.0, score)


# ── Category Classifier ─────────────────────────────────────

def classify_category(topic):
    """Classify topic into: CRIME / HISTORY / MYSTERY / PARANORMAL / DISAPPEARANCE."""
    text = (topic.get('title', '') + ' ' + topic.get('summary', '')).lower()

    crime_kw = ['murder', 'killer', 'crime', 'homicide', 'assault', 'robbery', 'arrest',
                'forensic', 'suspect', 'victim', 'serial', 'manslaughter']
    disappear_kw = ['disappear', 'missing', 'vanish', 'without trace', 'lost', 'abducted',
                    'kidnap', 'not found']
    paranormal_kw = ['ghost', 'haunted', 'paranormal', 'ufo', 'alien', 'supernatural',
                     'poltergeist', 'cryptid', 'bigfoot', 'mothman']
    history_kw = ['ancient', 'historical', 'century', 'medieval', 'archaeological',
                  'civilization', 'empire', 'dynasty', 'war', 'battle']

    scores = {
        'CRIME': sum(1 for kw in crime_kw if kw in text),
        'DISAPPEARANCE': sum(1 for kw in disappear_kw if kw in text),
        'PARANORMAL': sum(1 for kw in paranormal_kw if kw in text),
        'HISTORY': sum(1 for kw in history_kw if kw in text),
        'MYSTERY': 1  # Default
    }

    return max(scores, key=scores.get)


# ── Master Viral Score Calculator ────────────────────────────

def calculate_viral_score(topic):
    """
    Calculate the final viral score (1-10) with weighted breakdown.
    Returns (score, breakdown_dict).
    """
    yt = score_youtube_velocity(topic)
    gt = score_google_trends(topic)
    rd = score_reddit_engagement(topic)
    tw = score_twitter_signal(topic)
    nc = score_news_coverage(topic)
    intr = score_intrigue(topic)

    # Weighted average
    final = (
        yt * 0.25 +
        gt * 0.20 +
        rd * 0.20 +
        tw * 0.15 +
        nc * 0.10 +
        intr * 0.10
    )

    breakdown = {
        'youtube_velocity': round(yt, 1),
        'google_trends': round(gt, 1),
        'reddit_engagement': round(rd, 1),
        'twitter_signal': round(tw, 1),
        'news_coverage': round(nc, 1),
        'intrigue_factor': round(intr, 1),
        'final_score': round(final, 2)
    }

    # Classify category
    category = classify_category(topic)
    topic['category'] = category
    topic['viral_score'] = round(final, 2)
    topic['score_breakdown'] = breakdown

    return round(final, 2), breakdown


def is_viral(topic, threshold=8.0):
    """Check if a topic qualifies as viral (score >= threshold)."""
    score = topic.get('viral_score', 0)
    if score == 0:
        score, _ = calculate_viral_score(topic)
    return score >= threshold


def batch_score(topics):
    """Score a batch of topics and return sorted by viral score."""
    print(f'\n=== Scoring {len(topics)} topics ===')
    for i, t in enumerate(topics):
        score, breakdown = calculate_viral_score(t)
        if (i + 1) % 10 == 0:
            print(f'  Scored {i+1}/{len(topics)}...')

    topics.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    print(f'=== Scoring complete ===')

    viral_count = sum(1 for t in topics if t.get('viral_score', 0) >= 8.0)
    print(f'  Viral (8.0+): {viral_count}')
    print(f'  Top score: {topics[0].get("viral_score", 0) if topics else 0}')

    return topics


if __name__ == '__main__':
    test = {
        'title': 'The Disappearance of Madeleine McCann',
        'summary': 'A three-year-old British girl disappeared from a holiday apartment in Portugal in 2007. Despite massive investigations, she has never been found.',
        'source': 'https://en.wikipedia.org/wiki/Disappearance_of_Madeleine_McCann',
        'source_name': 'Wikipedia',
        'sources_list': [
            {'url': 'https://bbc.co.uk', 'credibility': 'High'},
            {'url': 'https://theguardian.com', 'credibility': 'High'},
            {'url': 'https://cnn.com', 'credibility': 'High'},
        ]
    }
    score, breakdown = calculate_viral_score(test)
    print(f'Score: {score}')
    print(f'Breakdown: {breakdown}')
    print(f'Category: {test["category"]}')
