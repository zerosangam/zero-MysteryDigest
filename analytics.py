"""
MysteryDigest v2 — Analytics & Dashboard Generator
Generates a static HTML analytics dashboard.
Logs all cycles, shortlists, and emails.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from database import get_analytics_summary, _load, ANALYTICS_FILE, CANDIDATES_FILE, SHORTLIST_FILE


def generate_dashboard_html():
    """Generate a static HTML analytics dashboard."""
    summary = get_analytics_summary()
    candidates_db = _load(CANDIDATES_FILE)
    shortlist_db = _load(SHORTLIST_FILE)

    # Weekly stats
    weekly_data = []
    for i in range(7):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_candidates = len(candidates_db.get(day, []))
        day_shortlist = len(shortlist_db.get(day, []))
        weekly_data.append({
            'date': day,
            'candidates': day_candidates,
            'shortlisted': day_shortlist
        })
    weekly_data.reverse()

    # Build chart data
    dates_json = json.dumps([d['date'][-5:] for d in weekly_data])
    candidates_json = json.dumps([d['candidates'] for d in weekly_data])
    shortlist_json = json.dumps([d['shortlisted'] for d in weekly_data])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MysteryDigest Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #0f0f23; color: #e0e0e0; padding: 20px; }}
        .header {{ text-align: center; padding: 30px; }}
        .header h1 {{ font-size: 2em; color: #fff; }}
        .header p {{ color: #888; margin-top: 8px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                       gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #1a1a2e; border-radius: 12px; padding: 25px;
                      text-align: center; border: 1px solid #333; }}
        .stat-card .value {{ font-size: 2.5em; font-weight: 700; color: #667eea; }}
        .stat-card .label {{ color: #888; margin-top: 8px; font-size: 0.9em; }}
        .chart-container {{ background: #1a1a2e; border-radius: 12px; padding: 25px;
                            margin: 20px 0; border: 1px solid #333; }}
        .chart-container h2 {{ margin-bottom: 15px; color: #fff; }}
        canvas {{ max-height: 300px; }}
        .log-section {{ background: #1a1a2e; border-radius: 12px; padding: 25px;
                        margin: 20px 0; border: 1px solid #333; }}
        .log-section h2 {{ margin-bottom: 15px; color: #fff; }}
        .log-entry {{ padding: 8px 12px; border-bottom: 1px solid #222; font-size: 0.85em; }}
        .log-entry .time {{ color: #667eea; }}
        .log-entry .count {{ color: #4ecdc4; font-weight: 600; }}
        .footer {{ text-align: center; padding: 30px; color: #555; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>&#128269; MysteryDigest Analytics</h1>
        <p>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="value">{summary['total_cycles']}</div>
            <div class="label">Total Research Cycles</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary['total_candidates_found']}</div>
            <div class="label">Total Candidates Found</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary['days_with_lockins']}</div>
            <div class="label">Days with Shortlists</div>
        </div>
        <div class="stat-card">
            <div class="value">{summary['sunday_emails_sent']}</div>
            <div class="label">Sunday Emails Sent</div>
        </div>
    </div>

    <div class="chart-container">
        <h2>Weekly Research Activity</h2>
        <canvas id="weeklyChart"></canvas>
    </div>

    <div class="log-section">
        <h2>Recent Cycles</h2>
        {''.join(f'<div class="log-entry"><span class="time">{c.get("timestamp", "")[:16]}</span> &mdash; <span class="count">{c.get("candidates_found", 0)} candidates</span> found ({c.get("type", "research")})</div>' for c in summary.get('recent_cycles', [])[-10:])}
    </div>

    <div class="footer">
        MysteryDigest v2 &bull; Automated Analytics &bull; Updated every cycle
    </div>

    <script>
        const ctx = document.getElementById('weeklyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {dates_json},
                datasets: [
                    {{
                        label: 'Candidates Found',
                        data: {candidates_json},
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: '#667eea',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Shortlisted (Top 10)',
                        data: {shortlist_json},
                        backgroundColor: 'rgba(78, 205, 196, 0.6)',
                        borderColor: '#4ecdc4',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: '#333' }},
                        ticks: {{ color: '#888' }}
                    }},
                    x: {{
                        grid: {{ color: '#333' }},
                        ticks: {{ color: '#888' }}
                    }}
                }},
                plugins: {{
                    legend: {{ labels: {{ color: '#ccc' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    # Save dashboard
    dashboard_path = Path(__file__).parent / 'docs' / 'index.html'
    dashboard_path.parent.mkdir(exist_ok=True)
    dashboard_path.write_text(html, encoding='utf-8')
    print(f'Dashboard generated: {dashboard_path}')
    return str(dashboard_path)


if __name__ == '__main__':
    path = generate_dashboard_html()
    print(f'Dashboard at: {path}')
