"""
MysteryDigest v2 — Translator Module
Translates titles and summaries to Hindi using free translation APIs.
Falls back through multiple free services.
"""

import requests
import re
import time

HEADERS = {'User-Agent': 'MysteryDigest/2.0'}


def translate_to_hindi(text, retries=3):
    """Translate English text to Hindi using free APIs. Falls back through multiple services."""
    if not text or len(text.strip()) < 3:
        return text

    text = text[:500]  # Limit length

    # Method 1: MyMemory API (free, 5000 chars/day)
    for attempt in range(retries):
        try:
            url = 'https://api.mymemory.translated.net/get'
            params = {'q': text, 'langpair': 'en|hi'}
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get('responseData', {}).get('translatedText', '')
                if translated and 'MYMEMORY' not in translated.upper():
                    return translated
        except Exception:
            time.sleep(0.5)

    # Method 2: LibreTranslate (free public instances)
    libre_instances = [
        'https://libretranslate.com',
        'https://translate.argosopentech.com',
    ]
    for instance in libre_instances:
        try:
            resp = requests.post(f'{instance}/translate', json={
                'q': text, 'source': 'en', 'target': 'hi'
            }, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                translated = resp.json().get('translatedText', '')
                if translated:
                    return translated
        except Exception:
            continue

    # Method 3: Fallback - return original with note
    return f'[Hindi translation unavailable] {text}'


def translate_topic(topic):
    """Add Hindi translations to a topic dict."""
    title_en = topic.get('title', '')
    summary_en = topic.get('summary', '')

    topic['title_en'] = title_en
    topic['title_hi'] = translate_to_hindi(title_en)

    topic['summary_en'] = summary_en
    topic['summary_hi'] = translate_to_hindi(summary_en)

    return topic


def batch_translate(topics, delay=0.3):
    """Translate a batch of topics to Hindi."""
    print(f'\n=== Translating {len(topics)} topics to Hindi ===')
    for i, topic in enumerate(topics):
        translate_topic(topic)
        if (i + 1) % 5 == 0:
            print(f'  Translated {i+1}/{len(topics)}...')
        time.sleep(delay)  # Rate limiting
    print('=== Translation complete ===')
    return topics


if __name__ == '__main__':
    test_text = "The mysterious disappearance of a young woman in 1947 baffled investigators."
    print(f'English: {test_text}')
    print(f'Hindi: {translate_to_hindi(test_text)}')
