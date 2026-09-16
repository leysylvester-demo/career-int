# Career Intelligence System

An AI-powered job search and career strategy tool that helps you decide which jobs are worth pursuing, how to position yourself, and where your career opportunities are heading.

Built with Python, Streamlit, PostgreSQL, and the Anthropic Claude API.

## Why I Built This

I originally built Career Intelligence for myself after being laid off from Oracle. Job searching quickly became overwhelming. There were hundreds of postings, unclear job requirements, repeated applications, and the constant question:

**Is this job actually worth my time?**

I wanted something that went beyond keyword matching or a generic fit score. Career Intelligence evaluates opportunities against evidence from your actual experience. It can recommend that you apply, tell you to consider a role carefully, or tell you to skip it altogether.

This system is built around three core ideas:

1. **Evidence over assumptions** Skills are connected to things you have actually done, built, managed, or delivered.

2. **Honest job triage** Jobs are classified as **Apply, Consider, or Skip**, with reasoning, strengths, concerns, and potential gaps.

3. **Career intelligence, not just job matching** Over time, the system looks across job postings to identify recurring skills, market demand, and gaps that may influence your longer-term career strategy.

I built this for myself first. I am sharing it because many talented people are navigating layoffs and difficult job searches, and it may help someone else too.

## What It Does

- **Profile Builder**: Upload your resume and build a structured professional profile containing your experience, education, skills, accomplishments, and supporting evidence.
- **Job Feed**: Collect job postings matching your target roles using the JSearch API. Results are deduplicated and filtered before AI analysis.
- **AI Job Triage**: Recommends Apply, Consider, or Skip, including strengths, concerns, recruiter perspective, and potential gaps.
- **Application Tracker**: Track opportunities through: Saved, Applied, Interviewed, Offer, Rejected.
- **Application Assistant**: Generates tailored resume content, professional summaries, cover letters, and outreach messages grounded in your experience.
- **Career Strategy**: Identifies recurring skills, skill gaps, hiring patterns, salary signals, and remote versus onsite trends.
 
## How It Works

```text
Resume
   ↓
Evidence-Based Profile
   ↓
Target Roles + Preferences
   ↓
Job Collection
   ↓
Pre-Filtering
   ↓
AI Triage
   ↓
Apply | Consider | Skip
   ↓
Application Support + Career Insights
```

## Technology Stack

| Component | Technology |
|---|---|
| User Interface | Streamlit |
| Application | Python |
| Database | PostgreSQL + SQLAlchemy |
| AI | Anthropic Claude API |
| Job Data | JSearch API via RapidAPI |
| Resume Parsing | pdfplumber + python-docx |

## Architecture
```text
career-int/
├── app/
│   ├── config.py              # Environment configuration
│   ├── core/
│   │   ├── db.py               # Database connection (PostgreSQL + SQLAlchemy)
│   │   ├── models.py           # Profile and Job schemas
│   │   ├── profile_parser.py   # AI resume extraction
│   │   ├── job_collector.py    # JSearch API integration
│   │   ├── job_filters.py      # Quality and location pre-filtering
│   │   ├── triage_engine.py    # Core AI triage logic
│   │   ├── application_generator.py  # Tailored application content
│   │   ├── skill_gap_analyzer.py     # AI-powered skill gap extraction
│   │   └── market_analyzer.py        # Market data aggregation
│   └── pages/
├── pages/
│   ├── 01_profile.py
│   ├── 02_job_feed.py
│   ├── 03_dashboard.py
│   ├── 04_tracker.py
│   ├── 05_apply.py
│   └── 06_career_strategy.py
├── scripts/
├── main.py
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 16+
- An [Anthropic API key](https://console.anthropic.com)
- A [JSearch API key](https://rapidapi.com) (free tier via RapidAPI)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/leysylvester-demo/career-int.git
cd career-int
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a PostgreSQL database:
```sql
CREATE DATABASE career_intelligence;
```

5. Copy `.env.example` to `.env` in the project root:

```text
DATABASE_URL=postgresql://username:password@localhost:5432/career_intelligence
ANTHROPIC_API_KEY=your_anthropic_key_here
RAPIDAPI_KEY=your_jsearch_key_here
```

6. Initialize the database:
```bash
python -c "from app.core.db import init_db; init_db()"
```

7. Run the app:
```bash
streamlit run main.py
```

### Daily Use

1. **Build your profile** (Profile page): upload your resume, review and add evidence to every skill, add specific accomplishments. The more specific your evidence, the better your triage results.

2. **Set your target roles, locations, and deal breakers** carefully. These directly shape what jobs get collected and how they're triaged.

3. **Collect jobs**:
```bash
python scripts/collect_jobs.py
```

4. **Triage**:
```bash
python scripts/run_triage.py
```
Run repeatedly until it reports "No pending jobs to triage."

5. **Review your Dashboard**, work through Apply-tier jobs, generate application packages, and track your pipeline.

6. **Periodically run Career Strategy** analysis to see skill gaps and market trends.

### Automation (Optional)

Use your OS task scheduler to run `collect_jobs.py` and `run_triage.py` daily so new postings are triaged automatically.

> [!WARNING]
> Never commit your `.env` file or API keys to GitHub.

>[!NOTE]
> Resume content used for AI-powered features is sent to the configured AI provider as necessary to perform those features. Review the provider's data and privacy policies before use.

## License
Licensed under the MIT License. See the LICENSE file for details.

**Built after a layoff. Shared in the hope that it helps someone navigate theirs.**
