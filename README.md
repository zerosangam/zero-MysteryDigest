# 🔍 MysteryDigest

Automated daily email digest of the world's most mysterious unsolved cases, true crimes, historical anomalies, and unexplained events.

## How It Works

Every day at **06:00 AM IST**, the system:
1. Researches mysteries from Wikipedia, Reddit, RSS feeds, and more
2. Scores and deduplicates topics (7-day rolling window)
3. Selects the top 10 most interesting mysteries
4. Sends a beautifully formatted HTML email digest

## Setup

### 1. Create a new GitHub repository
```bash
cd MysteryDigest
git init
git add .
git commit -m "Initial commit: MysteryDigest automation"
git remote add origin https://github.com/YOUR_USERNAME/MysteryDigest.git
git push -u origin main
```

### 2. Add GitHub Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
| Secret Name | Value |
|---|---|
| `GMAIL_USER` | Your Gmail address (e.g., `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Your Gmail App Password ([Generate here](https://myaccount.google.com/apppasswords)) |
| `RECIPIENT_EMAIL` | Email address to receive the digest |

### 3. Enable GitHub Actions
The workflow runs automatically via cron. You can also trigger it manually from the **Actions** tab → **MysteryDigest Daily** → **Run workflow**.

## Local Testing

```bash
pip install -r requirements.txt

# Test research only (no email)
python main.py --test

# Dry run (shows email content without sending)
python main.py --dry-run

# Full run (requires env vars)
export GMAIL_USER=your@gmail.com
export GMAIL_APP_PASSWORD=your-app-password
export RECIPIENT_EMAIL=recipient@gmail.com
python main.py
```

## Data Sources (All Free)
- **Wikipedia API** — Categories: unsolved murders, disappearances, conspiracies, cryptids, etc.
- **Wikipedia On This Day** — Historical mysterious events that happened today
- **Reddit JSON API** — r/UnresolvedMysteries, r/UnsolvedMysteries, r/mystery, r/TrueCrime
- **RSS Feeds** — Listverse, Atlas Obscura, Mysterious Universe, Historic Mysteries

## Cost
**$0** — Uses only free services:
- GitHub Actions free tier (2,000 min/month for private, unlimited for public repos)
- Gmail SMTP (free with App Password)
- Public APIs and RSS feeds

## Architecture
```
main.py          → Orchestrator (runs pipeline)
researcher.py    → Gathers topics from 4 source types
emailer.py       → Formats HTML email, sends via Gmail SMTP
sent_cache.json  → 7-day dedup cache (auto-managed)
.github/workflows/mystery-digest.yml → Daily cron schedule
```

## License
MIT
