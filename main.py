"""
MysteryDigest v2 — Main Orchestrator
UPGRADED from v1. Preserves all existing modes (--test, --dry-run, full).
Adds new modes:
  --cycle       : 30-minute research cycle (Mon-Sat)
  --daily-lock  : Lock top 10 for today's shortlist (runs at 11:59 PM IST)
  --sunday      : Sunday comparison + viral email (runs Sunday 06:00 AM IST)
  --dashboard   : Regenerate analytics dashboard
  --test        : (PRESERVED) Research only, no email
  --dry-run     : (PRESERVED) Show email content without sending

Usage:
  python main.py --cycle        # 30-min research cycle
  python main.py --daily-lock   # Lock daily top 10
  python main.py --sunday       # Sunday viral email
  python main.py --dashboard    # Regenerate dashboard
  python main.py --test         # Legacy test mode
  python main.py --dry-run      # Legacy dry run
  python main.py                # Legacy full pipeline (backward compat)
"""

import sys
import io
import json
import os
from datetime import datetime

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

from database import (
    store_candidates, get_today_candidates, get_week_candidates,
    lock_daily_top10, get_viral_topics, log_cycle, log_daily_lockin,
    log_sunday_email, migrate_legacy_cache, get_analytics_summary
)
from deep_research import deep_research_cycle
from viral_scorer import batch_score, calculate_viral_score
from verifier import batch_verify
from translator import batch_translate
from emailer_v2 import send_sunday_digest, send_no_viral_email
from analytics import generate_dashboard_html

# Also import legacy researcher for backward compatibility
from researcher import research_mysteries


def run_30min_cycle():
    """
    30-minute research cycle (Mon-Sat).
    Discovers 10+ fresh topics, scores them, stores in database.
    """
    print(f'\n{"=" * 60}')
    print(f'MysteryDigest v2 — 30-Minute Research Cycle')
    print(f'Time: {datetime.now().isoformat()}')
    print(f'{"=" * 60}')

    # Step 1: Deep research across 50+ sources
    topics, sources_used = deep_research_cycle(min_topics=10)

    if len(topics) < 10:
        print(f'WARNING: Only {len(topics)} topics found. Running legacy researcher as backup...')
        legacy = research_mysteries(15)
        for lt in legacy:
            lt['found_via'] = 'legacy_v1'
            lt['credibility'] = 'Medium'
        topics.extend(legacy)

    # Step 2: Verify (filter out fiction)
    print('\n>>> Verifying topics...')
    # Use lighter verification for cycles (1 credible source minimum)
    verified = batch_verify(topics, min_credible=1)

    # Step 3: Score all topics
    print('\n>>> Scoring topics...')
    scored = batch_score(verified)

    # Step 4: Store in database
    print('\n>>> Storing candidates...')
    added = store_candidates(scored)
    print(f'  Added {added} new candidates to database')

    # Step 5: Log analytics
    log_cycle(
        candidates_found=added,
        sources_used=sources_used if isinstance(sources_used, list) else [str(sources_used)],
        cycle_type='30min_research'
    )

    # Step 6: Update dashboard
    try:
        generate_dashboard_html()
    except Exception as e:
        print(f'Dashboard update skipped: {e}')

    total_today = len(get_today_candidates())
    print(f'\n{"=" * 60}')
    print(f'Cycle complete: +{added} new | {total_today} total today')
    print(f'Finished: {datetime.now().isoformat()}')
    print(f'{"=" * 60}')


def run_daily_lockin():
    """
    Daily lock-in at 11:59 PM IST (Mon-Sat).
    Ranks today's candidates and locks top 10 into Weekend Shortlist.
    """
    print(f'\n{"=" * 60}')
    print(f'MysteryDigest v2 — Daily Top-10 Lock-In')
    print(f'Time: {datetime.now().isoformat()}')
    print(f'{"=" * 60}')

    today = datetime.now().strftime('%Y-%m-%d')
    candidates = get_today_candidates()
    print(f'Today\'s candidates: {len(candidates)}')

    if not candidates:
        print('No candidates to lock in.')
        return

    # Re-score all candidates
    batch_score(candidates)

    # Lock top 10
    top10 = lock_daily_top10(today)
    print(f'\nLocked top {len(top10)} topics:')
    for i, t in enumerate(top10, 1):
        print(f'  {i}. [{t.get("viral_score", 0):.1f}] {t.get("title", "")[:70]}')

    log_daily_lockin(today, top10)

    print(f'\n{"=" * 60}')
    print(f'Lock-in complete for {today}')
    print(f'{"=" * 60}')


def run_sunday_comparison():
    """
    Sunday 06:00 AM IST — Compare all 60 topics from the week.
    Select only those scoring 8.0+. Send ONE email.
    """
    print(f'\n{"=" * 60}')
    print(f'MysteryDigest v2 — Sunday Viral Comparison')
    print(f'Time: {datetime.now().isoformat()}')
    print(f'{"=" * 60}')

    # Get all week candidates
    all_candidates = get_week_candidates()
    print(f'Total week candidates: {len(all_candidates)}')

    if not all_candidates:
        print('No candidates this week.')
        send_no_viral_email()
        return

    # Re-score everything
    print('\n>>> Re-scoring all candidates...')
    batch_score(all_candidates)

    # Get viral topics (8.0+)
    viral = [t for t in all_candidates if t.get('viral_score', 0) >= 8.0]
    viral.sort(key=lambda x: x.get('viral_score', 0), reverse=True)

    print(f'\nViral topics (8.0+): {len(viral)}')

    if not viral:
        print('No truly viral topics this week.')
        send_no_viral_email()
        log_sunday_email([], [])
        return

    # Full verification (3+ credible sources)
    print('\n>>> Full verification...')
    verified_viral = batch_verify(viral, min_credible=3)

    if not verified_viral:
        print('No topics passed full verification.')
        send_no_viral_email()
        log_sunday_email([], [])
        return

    # Translate to Hindi
    print('\n>>> Translating to Hindi...')
    batch_translate(verified_viral)

    # Send Sunday email
    print(f'\n>>> Sending Sunday email with {len(verified_viral)} viral topics...')
    success = send_sunday_digest(verified_viral)

    scores = [t.get('viral_score', 0) for t in verified_viral]
    log_sunday_email(verified_viral, scores)

    # Update dashboard
    try:
        generate_dashboard_html()
    except Exception as e:
        print(f'Dashboard update skipped: {e}')

    print(f'\n{"=" * 60}')
    print(f'Sunday email {"sent!" if success else "FAILED"}')
    print(f'Topics: {len(verified_viral)} | Top score: {max(scores):.1f}')
    print(f'{"=" * 60}')


def run_legacy_mode(mode):
    """Backward-compatible legacy modes from v1."""
    print(f'\n{"=" * 50}')
    print(f'MysteryDigest Pipeline (Legacy v1 mode)')
    print(f'Started: {datetime.now().isoformat()}')
    print(f'{"=" * 50}')

    topics = research_mysteries(10)

    if not topics:
        print('ERROR: No topics found!')
        sys.exit(1)

    print(f'\n>>> Found {len(topics)} topics')
    for i, t in enumerate(topics, 1):
        print(f'  {i}. {t["title"]}')
        print(f'     {t["summary"][:100]}...')
        print(f'     Source: {t["source"]}')

    if mode == 'test':
        print('\n>>> Test mode: Skipping email send.')
    elif mode == 'dry-run':
        from emailer import format_email_plain
        print('\n>>> Dry run mode: Email content preview:')
        print(format_email_plain(topics))
    else:
        from emailer import send_digest
        print('\n>>> Sending email digest...')
        send_digest(topics)

    print(f'\n{"=" * 50}')
    print(f'Pipeline completed ({mode})')
    print(f'Finished: {datetime.now().isoformat()}')
    print(f'{"=" * 50}')


def main():
    # Migrate legacy data on first run
    migrate_legacy_cache()

    if '--cycle' in sys.argv:
        run_30min_cycle()
    elif '--daily-lock' in sys.argv:
        run_daily_lockin()
    elif '--sunday' in sys.argv:
        run_sunday_comparison()
    elif '--dashboard' in sys.argv:
        generate_dashboard_html()
        print('Dashboard regenerated.')
    elif '--test' in sys.argv:
        run_legacy_mode('test')
    elif '--dry-run' in sys.argv:
        run_legacy_mode('dry-run')
    else:
        # Default: run legacy full mode for backward compatibility
        run_legacy_mode('full')


if __name__ == '__main__':
    main()
