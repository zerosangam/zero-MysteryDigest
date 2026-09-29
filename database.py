"""
MysteryDigest v2 — Persistent JSON Database
Stores candidates, daily shortlists, weekly comparisons, and analytics.
Migrates existing sent_cache.json data forward.
"""

import json
import os
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path

DB_DIR = Path(__file__).parent / 'data'
CANDIDATES_FILE = DB_DIR / 'candidates.json'
SHORTLIST_FILE = DB_DIR / 'shortlist.json'
ANALYTICS_FILE = DB_DIR / 'analytics.json'
LEGACY_CACHE = Path(__file__).parent / 'sent_cache.json'


def _ensure_db():
    """Create database directory and files if they don't exist."""
    DB_DIR.mkdir(exist_ok=True)
    for f in [CANDIDATES_FILE, SHORTLIST_FILE, ANALYTICS_FILE]:
        if not f.exists():
            f.write_text('{}')


def _load(filepath):
    _ensure_db()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(filepath, data):
    _ensure_db()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def topic_hash(title):
    normalized = re.sub(r'[^a-z0-9]', '', title.lower())
    return hashlib.md5(normalized.encode()).hexdigest()


# ── Candidate Store ──────────────────────────────────────────

def get_candidates_db():
    """Get all candidates keyed by date."""
    return _load(CANDIDATES_FILE)


def store_candidates(topics, cycle_id=None):
    """Store discovered candidates from a 30-min cycle."""
    db = _load(CANDIDATES_FILE)
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in db:
        db[today] = []

    added = 0
    existing_hashes = {topic_hash(c['title']) for c in db[today]}

    for t in topics:
        h = topic_hash(t['title'])
        if h not in existing_hashes:
            t['discovered_at'] = datetime.now().isoformat()
            t['cycle_id'] = cycle_id or datetime.now().strftime('%H%M')
            t['topic_hash'] = h
            if 'viral_score' not in t:
                t['viral_score'] = 0.0
            if 'sources_list' not in t:
                t['sources_list'] = []
            if 'category' not in t:
                t['category'] = 'MYSTERY'
            if 'verified' not in t:
                t['verified'] = False
            if 'credible_source_count' not in t:
                t['credible_source_count'] = 0
            db[today].append(t)
            existing_hashes.add(h)
            added += 1

    _save(CANDIDATES_FILE, db)
    return added


def get_today_candidates():
    """Get all candidates discovered today."""
    db = _load(CANDIDATES_FILE)
    today = datetime.now().strftime('%Y-%m-%d')
    return db.get(today, [])


def get_week_candidates():
    """Get candidates from the last 6 days (Mon-Sat)."""
    db = _load(CANDIDATES_FILE)
    all_candidates = []
    for i in range(7):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        all_candidates.extend(db.get(day, []))
    return all_candidates


def update_candidate_score(date_str, topic_hash_val, viral_score, score_breakdown=None):
    """Update the viral score for a specific candidate."""
    db = _load(CANDIDATES_FILE)
    if date_str in db:
        for c in db[date_str]:
            if c.get('topic_hash') == topic_hash_val:
                c['viral_score'] = viral_score
                if score_breakdown:
                    c['score_breakdown'] = score_breakdown
                break
    _save(CANDIDATES_FILE, db)


def is_known_candidate(title):
    """Check if a topic already exists in today's candidates."""
    db = _load(CANDIDATES_FILE)
    today = datetime.now().strftime('%Y-%m-%d')
    h = topic_hash(title)
    return any(c.get('topic_hash') == h for c in db.get(today, []))


# ── Daily Shortlist ──────────────────────────────────────────

def get_shortlist_db():
    return _load(SHORTLIST_FILE)


def lock_daily_top10(day_str=None):
    """Lock today's top 10 candidates into the Weekend Shortlist."""
    if not day_str:
        day_str = datetime.now().strftime('%Y-%m-%d')

    db_candidates = _load(CANDIDATES_FILE)
    candidates = db_candidates.get(day_str, [])

    # Sort by viral_score descending
    candidates.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    top10 = candidates[:10]

    shortlist_db = _load(SHORTLIST_FILE)
    shortlist_db[day_str] = top10
    _save(SHORTLIST_FILE, shortlist_db)

    return top10


def get_weekend_shortlist():
    """Get the full 6-day shortlist (up to 60 topics)."""
    shortlist_db = _load(SHORTLIST_FILE)
    all_topics = []
    for i in range(7):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        all_topics.extend(shortlist_db.get(day, []))
    return all_topics


def get_viral_topics(min_score=8.0):
    """Get only topics scoring 8.0+ from the weekend shortlist."""
    shortlist = get_weekend_shortlist()
    viral = [t for t in shortlist if t.get('viral_score', 0) >= min_score]
    viral.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    return viral


# ── Analytics ────────────────────────────────────────────────

def log_cycle(candidates_found, sources_used, cycle_type='research'):
    """Log a research cycle."""
    db = _load(ANALYTICS_FILE)
    if 'cycles' not in db:
        db['cycles'] = []
    db['cycles'].append({
        'timestamp': datetime.now().isoformat(),
        'type': cycle_type,
        'candidates_found': candidates_found,
        'sources_used': sources_used
    })
    # Keep last 500 entries
    db['cycles'] = db['cycles'][-500:]
    _save(ANALYTICS_FILE, db)


def log_daily_lockin(day_str, topics):
    """Log which topics made the daily shortlist."""
    db = _load(ANALYTICS_FILE)
    if 'daily_lockins' not in db:
        db['daily_lockins'] = {}
    db['daily_lockins'][day_str] = [
        {'title': t.get('title', ''), 'score': t.get('viral_score', 0)}
        for t in topics
    ]
    _save(ANALYTICS_FILE, db)


def log_sunday_email(topics_sent, scores):
    """Log the Sunday email."""
    db = _load(ANALYTICS_FILE)
    if 'sunday_emails' not in db:
        db['sunday_emails'] = []
    db['sunday_emails'].append({
        'date': datetime.now().isoformat(),
        'count': len(topics_sent),
        'topics': [{'title': t.get('title', ''), 'score': s}
                   for t, s in zip(topics_sent, scores)]
    })
    _save(ANALYTICS_FILE, db)


def get_analytics_summary():
    """Get analytics summary for dashboard."""
    db = _load(ANALYTICS_FILE)
    cycles = db.get('cycles', [])
    lockins = db.get('daily_lockins', {})
    emails = db.get('sunday_emails', [])

    return {
        'total_cycles': len(cycles),
        'total_candidates_found': sum(c.get('candidates_found', 0) for c in cycles),
        'days_with_lockins': len(lockins),
        'sunday_emails_sent': len(emails),
        'last_cycle': cycles[-1] if cycles else None,
        'recent_cycles': cycles[-10:]
    }


# ── Migration ────────────────────────────────────────────────

def migrate_legacy_cache():
    """Migrate old sent_cache.json into the new database."""
    if LEGACY_CACHE.exists():
        try:
            with open(LEGACY_CACHE, 'r') as f:
                old = json.load(f)
            sent = old.get('sent_topics', [])
            if sent:
                print(f'Migrating {len(sent)} legacy cache entries...')
                for entry in sent:
                    store_candidates([{
                        'title': entry.get('title', 'Unknown'),
                        'summary': 'Migrated from v1 cache',
                        'source': '',
                        'source_name': 'Legacy',
                        'viral_score': 0,
                        'category': 'MYSTERY'
                    }])
                print('Migration complete.')
        except Exception as e:
            print(f'Migration warning: {e}')


if __name__ == '__main__':
    _ensure_db()
    migrate_legacy_cache()
    print(f'Candidates today: {len(get_today_candidates())}')
    print(f'Week candidates: {len(get_week_candidates())}')
    print(f'Analytics: {get_analytics_summary()}')
