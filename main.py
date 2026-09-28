"""
MysteryDigest - Daily Mystery Research & Email System
Main orchestrator that runs the full pipeline:
  1. Research mysteries from free public sources
  2. Score, deduplicate, and select top 10
  3. Format and send email digest

Usage:
  python main.py           # Run full pipeline
  python main.py --test    # Run research only (no email)
  python main.py --dry-run # Run everything but print instead of sending
"""

import sys
import io
import json

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from datetime import datetime
from researcher import research_mysteries
from emailer import send_digest, format_email_plain


def main():
    print(f'\n{"=" * 50}')
    print(f'MysteryDigest Pipeline')
    print(f'Started: {datetime.now().isoformat()}')
    print(f'{"=" * 50}')

    mode = 'full'
    if '--test' in sys.argv:
        mode = 'test'
    elif '--dry-run' in sys.argv:
        mode = 'dry-run'

    print(f'Mode: {mode}')

    # Step 1: Research
    print('\n>>> Step 1: Researching mysteries...')
    topics = research_mysteries(10)

    if not topics:
        print('ERROR: No topics found! Check internet connection and source availability.')
        sys.exit(1)

    print(f'\n>>> Found {len(topics)} topics')

    # Step 2: Display results
    print('\n>>> Step 2: Topics collected:')
    for i, t in enumerate(topics, 1):
        print(f'  {i}. {t["title"]}')
        summary_preview = t["summary"][:100]
        print(f'     {summary_preview}...')
        print(f'     Source: {t["source"]}')

    if mode == 'test':
        print('\n>>> Test mode: Skipping email send.')
        print(f'\n{"=" * 50}')
        print(f'Pipeline completed (test mode)')
        print(f'Finished: {datetime.now().isoformat()}')
        print(f'{"=" * 50}')
        return

    if mode == 'dry-run':
        print('\n>>> Dry run mode: Email content preview:')
        print(format_email_plain(topics))
        print(f'\n{"=" * 50}')
        print(f'Pipeline completed (dry run)')
        print(f'Finished: {datetime.now().isoformat()}')
        print(f'{"=" * 50}')
        return

    # Step 3: Send email
    print('\n>>> Step 3: Sending email digest...')
    success = send_digest(topics)

    if success:
        print(f'\n{"=" * 50}')
        print(f'Pipeline completed successfully!')
        print(f'Finished: {datetime.now().isoformat()}')
        print(f'{"=" * 50}')
    else:
        print(f'\n{"=" * 50}')
        print(f'Pipeline completed with email error')
        print(f'Finished: {datetime.now().isoformat()}')
        print(f'{"=" * 50}')
        sys.exit(1)


if __name__ == '__main__':
    main()
