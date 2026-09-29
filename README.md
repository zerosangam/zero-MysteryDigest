<div align="center">

<!-- HERO BANNER -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:1e293b,100:0ea5e9&height=200&section=header&text=MysteryDigest&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Unravel%20the%20Unknown%20%E2%80%94%20Daily&descAlignY=58&descSize=18" width="100%"/>

<!-- TAGLINE BADGES -->
<a href="#-features"><img src="https://img.shields.io/badge/Status-Active-00C853?style=for-the-badge&logo=statuspage&logoColor=white" /></a>
<a href="#-cost"><img src="https://img.shields.io/badge/Cost-%240%20Forever-0EA5E9?style=for-the-badge&logo=opensourceinitiative&logoColor=white" /></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-FFD700?style=for-the-badge&logo=opensourceinitiative&logoColor=black" /></a>
<a href="https://github.com/YOUR_USERNAME/MysteryDigest/actions"><img src="https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/MysteryDigest/mystery-digest.yml?style=for-the-badge&logo=githubactions&logoColor=white&label=Workflow" /></a>

<br/>

<!-- TECH STACK -->
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/Gmail_SMTP-EA4335?style=flat-square&logo=gmail&logoColor=white" />
<img src="https://img.shields.io/badge/Wikipedia_API-000000?style=flat-square&logo=wikipedia&logoColor=white" />
<img src="https://img.shields.io/badge/Reddit_API-FF4500?style=flat-square&logo=reddit&logoColor=white" />
<img src="https://img.shields.io/badge/RSS-FFA500?style=flat-square&logo=rss&logoColor=white" />

<br/><br/>

> **🕵️ Every morning at 6:00 AM IST — the world's most mysterious unsolved cases,  
> true crimes, and unexplained events — delivered to your inbox.**

</div>

---

## 🎯 Overview

**MysteryDigest** is a fully automated, zero-cost email digest system that curates the **top 10 most intriguing mysteries** from across the internet and delivers them straight to your inbox — every single day.

Built to be **set-and-forget**: fork it, add 3 secrets, and let GitHub Actions handle the rest.

---

## ⚡ Features

| | Feature | Description |
|---|---------|-------------|
| 🔍 | **Multi-Source Research** | Wikipedia, Reddit, RSS feeds, and historical events |
| 🧠 | **Smart Scoring** | Ranks topics by intrigue, novelty, and engagement |
| 🗂️ | **7-Day Dedup Cache** | Never receive the same mystery twice in a week |
| 📧 | **Beautiful HTML Email** | Responsive, dark-mode friendly, mobile-optimized |
| ⏰ | **Daily Cron Automation** | Fires at 06:00 AM IST without any manual work |
| 💸 | **100% Free Stack** | GitHub Actions + Gmail SMTP + Public APIs |
| 🧪 | **Local Testing Modes** | `--test` and `--dry-run` for safe iteration |

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    MYSTERYDIGEST PIPELINE               │
└─────────────────────────────────────────────────────────┘

   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  Wikipedia   │   │   Reddit     │   │  RSS Feeds   │
   │   + On This  │   │   JSON API   │   │  Listverse,  │
   │     Day      │   │              │   │  Atlas, etc. │
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                 ┌──────────────────────┐
                 │   researcher.py      │
                 │  (Gather + Score)    │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │  sent_cache.json     │
                 │  (7-Day Dedup)       │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │    emailer.py        │
                 │  (HTML + SMTP Send)  │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │    📬 Your Inbox     │
                 └──────────────────────┘

                 ⏰ Triggered by GitHub Actions (cron: 06:00 IST)
```

---

## 🚀 Quick Start

### 1️⃣ Clone & Initialize

```bash
git clone https://github.com/YOUR_USERNAME/MysteryDigest.git
cd MysteryDigest
git init && git add . && git commit -m "✨ Initial commit: MysteryDigest"
git remote add origin https://github.com/YOUR_USERNAME/MysteryDigest.git
git push -u origin main
```

### 2️⃣ Configure Secrets

Navigate to **Settings → Secrets and variables → Actions → New repository secret**

| 🔑 Secret Name | 📝 Value |
|---|---|
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | [Generate App Password](https://myaccount.google.com/apppasswords) |
| `RECIPIENT_EMAIL` | Where the digest lands |

> ⚠️ **Note:** Regular Gmail passwords won't work. You **must** generate an App Password.

### 3️⃣ Enable Workflow

Go to **Actions** tab → **MysteryDigest Daily** → **Run workflow** to test immediately.

---

## 🧪 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Research only — no email
python main.py --test

# Preview email without sending
python main.py --dry-run

# Full run
export GMAIL_USER=your@gmail.com
export GMAIL_APP_PASSWORD=your-app-password
export RECIPIENT_EMAIL=recipient@gmail.com
python main.py
```

---

## 📚 Data Sources

<div align="center">

| Source | Type | Categories |
|--------|------|------------|
| 📖 **Wikipedia API** | REST | Unsolved murders, disappearances, conspiracies, cryptids |
| 🕰️ **On This Day** | REST | Historical mysterious events |
| 👽 **Reddit JSON** | JSON | r/UnresolvedMysteries, r/UnsolvedMysteries, r/mystery, r/TrueCrime |
| 📰 **RSS Feeds** | XML | Listverse, Atlas Obscura, Mysterious Universe, Historic Mysteries |

</div>

---

## 💰 Cost Breakdown

<div align="center">

| Service | Tier | Cost |
|---------|------|------|
| 🐙 GitHub Actions | Free (unlimited on public repos) | **$0** |
| 📧 Gmail SMTP | Free w/ App Password | **$0** |
| 🌐 Public APIs & RSS | Open | **$0** |
| **TOTAL** | | **$0 / month** |

</div>

---

## 📁 Project Structure

```text
MysteryDigest/
├── 🔧 main.py                 # Pipeline orchestrator
├── 🔍 researcher.py           # Multi-source topic gatherer
├── 📧 emailer.py              # HTML formatter + SMTP sender
├── 💾 sent_cache.json         # 7-day dedup cache (auto-managed)
├── 📋 requirements.txt        # Python dependencies
├── 📜 LICENSE                 # MIT
└── .github/
    └── workflows/
        └── ⏰ mystery-digest.yml  # Daily cron schedule
```

---

## 🗺️ Roadmap

- [x] Multi-source research engine
- [x] 7-day deduplication
- [x] Beautiful HTML email
- [ ] 🎨 Custom email themes (dark/light)
- [ ] 📊 Topic preference learning
- [ ] 🔔 Telegram / Discord notifications
- [ ] 🌍 Multi-language support
- [ ] 🖼️ Auto-fetch topic images

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repo 🍴
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m '✨ Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 🎉

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">

### 🌟 If you found this useful, give it a star!

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,100:0f172a&height=120&section=footer&text=Stay%20Curious%20%F0%9F%95%B5%EF%B8%8F&fontSize=24&fontColor=ffffff&animation=fadeIn" width="100%"/>

<sub>Built with 🖤 for mystery lovers everywhere.</sub>

</div>
