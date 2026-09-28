"""
MysteryDigest Email Module
Formats and sends the daily mystery digest via Gmail SMTP.
Reads credentials from environment variables:
  - GMAIL_USER: sender Gmail address
  - GMAIL_APP_PASSWORD: Gmail app password
  - RECIPIENT_EMAIL: recipient email address
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def format_email_html(topics):
    """Format topics into a beautiful HTML email."""
    date_str = datetime.now().strftime('%B %d, %Y')

    topics_html = ''
    for i, topic in enumerate(topics, 1):
        source_name = topic.get('source_name', 'Source')
        topics_html += f"""
        <tr>
            <td style="padding: 20px 25px; border-bottom: 1px solid #eee;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="width: 40px; vertical-align: top;">
                            <span style="display: inline-block; width: 32px; height: 32px;
                                         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                         color: white; border-radius: 50%; text-align: center;
                                         line-height: 32px; font-weight: bold; font-size: 14px;">{i}</span>
                        </td>
                        <td style="padding-left: 15px;">
                            <h3 style="margin: 0 0 8px 0; color: #1a1a2e; font-size: 16px;
                                       font-weight: 600; line-height: 1.3;">
                                {topic['title']}
                            </h3>
                            <p style="margin: 0 0 10px 0; color: #555; font-size: 14px;
                                      line-height: 1.5;">
                                {topic['summary']}
                            </p>
                            <a href="{topic['source']}"
                               style="color: #667eea; text-decoration: none; font-size: 13px;
                                      font-weight: 500;">
                                &#128279; Read more ({source_name})
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 30px 25px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: 1px;">
                                    &#128269; MysteryDigest
                                </h1>
                                <p style="margin: 8px 0 0 0; color: #a8b2d1; font-size: 14px;">
                                    Your Daily Dose of the Unknown &bull; {date_str}
                                </p>
                            </td>
                        </tr>

                        <!-- Intro -->
                        <tr>
                            <td style="padding: 25px 25px 10px 25px;">
                                <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.6;">
                                    Here are today's <strong>top 10 mysteries</strong> from around the world &mdash;
                                    unsolved cases, historical anomalies, and unexplained events that will
                                    keep you thinking all day.
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
                            <td style="padding: 25px; text-align: center; background-color: #f8f9fa; border-top: 1px solid #eee;">
                                <p style="margin: 0; color: #999; font-size: 12px;">
                                    MysteryDigest &bull; Automated daily research &bull; Powered by open data
                                    <br>Sources: Wikipedia, Reddit, RSS Feeds, and more
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


def format_email_plain(topics):
    """Format topics as plain text fallback."""
    date_str = datetime.now().strftime('%B %d, %Y')
    lines = [f'MysteryDigest - {date_str}', '=' * 40, '']
    lines.append('Top 10 Mysteries of the Day:')
    lines.append('')

    for i, topic in enumerate(topics, 1):
        lines.append(f'{i}. {topic["title"]}')
        lines.append(f'   {topic["summary"]}')
        lines.append(f'   Source: {topic["source"]}')
        lines.append('')

    lines.append('---')
    lines.append('MysteryDigest - Automated daily research')
    return '\n'.join(lines)


def send_digest(topics):
    """Send the mystery digest email via Gmail SMTP."""
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not gmail_user:
        raise ValueError('GMAIL_USER environment variable not set')
    if not gmail_password:
        raise ValueError('GMAIL_APP_PASSWORD environment variable not set')
    if not recipient:
        raise ValueError('RECIPIENT_EMAIL environment variable not set')

    date_str = datetime.now().strftime('%B %d, %Y')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'MysteryDigest: Top 10 Mysteries - {date_str}'
    msg['From'] = f'MysteryDigest <{gmail_user}>'
    msg['To'] = recipient

    # Attach plain text and HTML versions
    plain_text = format_email_plain(topics)
    html_text = format_email_html(topics)

    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_text, 'html'))

    print(f'\nSending email to {recipient} via {gmail_user}...')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        print('Email sent successfully!')
        return True
    except smtplib.SMTPAuthenticationError:
        print('ERROR: Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.')
        print('Make sure you are using a Gmail App Password, not your regular password.')
        print('Generate one at: https://myaccount.google.com/apppasswords')
        return False
    except Exception as e:
        print(f'ERROR sending email: {e}')
        return False


if __name__ == '__main__':
    # Test with dummy data
    test_topics = [
        {
            'title': 'Test Mystery',
            'summary': 'This is a test topic to verify email formatting works correctly.',
            'source': 'https://example.com',
            'source_name': 'Test'
        }
    ]
    print(format_email_plain(test_topics))
