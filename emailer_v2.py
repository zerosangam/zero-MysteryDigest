"""
MysteryDigest v2 — Sunday Viral Email Module
PRESERVES the original emailer.py (untouched for backward compat).
This new module handles the upgraded Sunday-only viral digest email.
Format: English + Hindi, viral scores, source lists, categories.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def _get_category_emoji(category):
    emojis = {
        'CRIME': '&#128248;',       # 🔪
        'HISTORY': '&#127963;',      # 🏛
        'MYSTERY': '&#128270;',      # 🔎
        'PARANORMAL': '&#128123;',   # 👻
        'DISAPPEARANCE': '&#128566;' # 😶
    }
    return emojis.get(category, '&#128270;')


def format_sunday_html(topics):
    """Format viral topics into the Sunday email HTML."""
    date_str = datetime.now().strftime('%B %d, %Y')
    count = len(topics)

    topics_html = ''
    for i, topic in enumerate(topics, 1):
        category = topic.get('category', 'MYSTERY')
        cat_emoji = _get_category_emoji(category)
        score = topic.get('viral_score', 0)
        breakdown = topic.get('score_breakdown', {})

        title_en = topic.get('title_en', topic.get('title', ''))
        title_hi = topic.get('title_hi', '')
        summary_en = topic.get('summary_en', topic.get('summary', ''))
        summary_hi = topic.get('summary_hi', '')

        # Score breakdown bar
        score_bar = f"""
        <div style="margin: 10px 0; font-size: 12px; color: #888;">
            <strong style="color: #ff6b6b;">Viral Score: {score:.1f}/10</strong>
            &nbsp;|&nbsp; YT: {breakdown.get('youtube_velocity', 0):.0f}
            &nbsp;|&nbsp; Reddit: {breakdown.get('reddit_engagement', 0):.0f}
            &nbsp;|&nbsp; Trends: {breakdown.get('google_trends', 0):.0f}
            &nbsp;|&nbsp; News: {breakdown.get('news_coverage', 0):.0f}
            &nbsp;|&nbsp; Intrigue: {breakdown.get('intrigue_factor', 0):.0f}
        </div>
        """

        # Sources list (clickable)
        sources_list = topic.get('sources_list', [])
        sources_html = ''
        if sources_list:
            sources_items = ''.join(
                f'<li><a href="{s.get("url", "#")}" style="color: #667eea; text-decoration: none;">'
                f'[{s.get("credibility", "?")}] {s.get("source_name", "Source")}</a>'
                f' — {s.get("finding", "")[:80]}</li>'
                for s in sources_list[:15]
            )
            sources_html = f'<ul style="font-size: 12px; color: #777; padding-left: 20px;">{sources_items}</ul>'

        # YouTube link if available
        yt_html = ''
        if topic.get('youtube_id'):
            yt_html = f'<a href="https://www.youtube.com/watch?v={topic["youtube_id"]}" style="color: #ff0000; text-decoration: none; font-size: 12px;">&#9654; Watch on YouTube</a><br>'

        topics_html += f"""
        <tr>
            <td style="padding: 25px; border-bottom: 2px solid #1a1a2e;">
                <div style="display: flex; align-items: start;">
                    <span style="display: inline-block; width: 36px; height: 36px;
                                 background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                                 color: white; border-radius: 50%; text-align: center;
                                 line-height: 36px; font-weight: bold; font-size: 16px;
                                 margin-right: 15px; flex-shrink: 0;">{i}</span>
                    <div style="flex: 1;">
                        <div style="font-size: 11px; color: #ff6b6b; font-weight: 600; margin-bottom: 4px;">
                            {cat_emoji} {category}
                        </div>
                        <h3 style="margin: 0 0 4px 0; color: #1a1a2e; font-size: 17px; font-weight: 700;">
                            {title_en}
                        </h3>
                        <p style="margin: 0 0 8px 0; color: #888; font-size: 13px; font-style: italic;">
                            {title_hi}
                        </p>
                        <p style="margin: 0 0 6px 0; color: #444; font-size: 14px; line-height: 1.5;">
                            {summary_en}
                        </p>
                        <p style="margin: 0 0 10px 0; color: #777; font-size: 13px; line-height: 1.5; font-style: italic;">
                            {summary_hi}
                        </p>
                        {score_bar}
                        {yt_html}
                        <details style="margin-top: 8px;">
                            <summary style="color: #667eea; cursor: pointer; font-size: 13px; font-weight: 500;">
                                &#128279; {len(sources_list)} Sources
                            </summary>
                            {sources_html}
                        </details>
                    </div>
                </div>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin: 0; padding: 0; background-color: #0f0f23; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f0f23; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="650" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 70%, #e94560 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: 1px;">
                                    &#128293; Sunday Viral Mysteries
                                </h1>
                                <p style="margin: 10px 0 0 0; color: #a8b2d1; font-size: 15px;">
                                    {count} Topics Worth Watching &bull; {date_str}
                                </p>
                                <p style="margin: 5px 0 0 0; color: #667eea; font-size: 13px;">
                                    Only verified incidents scoring 8.0+ on the viral scale
                                </p>
                            </td>
                        </tr>

                        <!-- Topics -->
                        <tr>
                            <td>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    {topics_html}
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 25px; text-align: center; background-color: #f8f9fa;">
                                <p style="margin: 0; color: #999; font-size: 12px;">
                                    MysteryDigest v2 &bull; Weekly Viral Research &bull; Powered by 50+ free sources
                                    <br>English + Hindi &bull; Verified with 3+ credible sources per topic
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def format_sunday_plain(topics):
    """Plain text version of Sunday email."""
    date_str = datetime.now().strftime('%B %d, %Y')
    count = len(topics)
    lines = [
        f'Sunday Viral Mysteries - {date_str}',
        f'{count} Topics Worth Watching',
        '=' * 50, ''
    ]

    for i, topic in enumerate(topics, 1):
        lines.append(f'{i}. [{topic.get("category", "?")}] {topic.get("title_en", topic.get("title", ""))}')
        if topic.get('title_hi'):
            lines.append(f'   Hindi: {topic["title_hi"]}')
        lines.append(f'   {topic.get("summary_en", topic.get("summary", ""))}')
        lines.append(f'   Viral Score: {topic.get("viral_score", 0):.1f}/10')
        lines.append(f'   Sources: {len(topic.get("sources_list", []))}')
        lines.append(f'   Primary: {topic.get("source", "")}')
        lines.append('')

    lines.extend(['---', 'MysteryDigest v2 — Weekly Viral Research'])
    return '\n'.join(lines)


def send_sunday_digest(topics):
    """Send the Sunday viral digest email."""
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not all([gmail_user, gmail_password, recipient]):
        print('ERROR: Missing email credentials in environment.')
        return False

    count = len(topics)
    date_str = datetime.now().strftime('%B %d, %Y')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Sunday Viral Mysteries - {count} Topics Worth Watching - {date_str}'
    msg['From'] = f'MysteryDigest <{gmail_user}>'
    msg['To'] = recipient

    msg.attach(MIMEText(format_sunday_plain(topics), 'plain', 'utf-8'))
    msg.attach(MIMEText(format_sunday_html(topics), 'html', 'utf-8'))

    print(f'\nSending Sunday email to {recipient}...')
    for attempt in range(3):
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, recipient, msg.as_string())
            print('Sunday email sent successfully!')
            return True
        except Exception as e:
            print(f'Attempt {attempt + 1} failed: {e}')
            if attempt < 2:
                import time
                time.sleep(5)
    print('ERROR: All email attempts failed.')
    return False


def send_no_viral_email():
    """Send a 'no viral topics' notification."""
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not all([gmail_user, gmail_password, recipient]):
        print('No credentials for no-viral email.')
        return False

    date_str = datetime.now().strftime('%B %d, %Y')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'MysteryDigest — No Truly Viral Mysteries This Week — {date_str}'
    msg['From'] = f'MysteryDigest <{gmail_user}>'
    msg['To'] = recipient

    plain = f'MysteryDigest - {date_str}\n\nNo truly viral mysteries this week.\nAll candidates scored below 8.0 on the viral scale.\nThe system will continue monitoring next week.'
    html = f"""<html><body style="background:#0f0f23;padding:40px;font-family:sans-serif;">
    <div style="max-width:500px;margin:auto;background:#1a1a2e;border-radius:12px;padding:40px;text-align:center;">
        <h1 style="color:#fff;">&#128270; MysteryDigest</h1>
        <p style="color:#888;font-size:18px;">No truly viral mysteries this week.</p>
        <p style="color:#667eea;font-size:14px;">All candidates scored below 8.0/10.</p>
        <p style="color:#555;font-size:12px;margin-top:20px;">{date_str}</p>
    </div></body></html>"""

    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        print('No-viral notification sent.')
        return True
    except Exception as e:
        print(f'Failed to send no-viral email: {e}')
        return False
