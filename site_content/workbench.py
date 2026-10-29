"""Relational SQLite + JSON workbench backing the four interactive intake tables.

Tables:
  1. study_queue   — "To Study with Data" (research questions, datasets, status, live study & LaTeX links)
  2. wishlist_todos — "To-Do & Website Wishlist" (prioritized site & research tasks)
  3. rap_lyrics    — "Spontaneous Rap Lyric Table" (with a bucket dropdown for the 6 Rap subsubsections)
  4. voice_notes   — "Voice Recording -> Journal / Podcast" (audio metadata, transcript, summary, destination)

Run ``python -B -m site_content.workbench`` to inspect or append entries from the terminal
or from a GitHub Mobile workflow commit. During the site build, ``load_workbench(root)``
validates every row against the site atlas, syncs ``records/workbench/workbench.db`` (SQLite),
and returns JSON/CSV-ready structures for ``Workbench/index.html`` and the Database destinations.
"""

from __future__ import annotations

from contextlib import closing
import argparse
import json
from pathlib import Path
import sqlite3
from typing import Any
import wave

from .atlas import NODES
from .catalog import RAP_PAGES

WORKBENCH_ROUTE = "Workbench/index.html"
SEED_PATH = "records/workbench/workbench.json"
SQLITE_PATH = "records/workbench/workbench.db"

RAP_BUCKETS: tuple[tuple[str, str], ...] = (
    ("Seven-Deadly-Sins", "Seven Deadly Sins"),
    ("Homewood-and-Trafalgar", "Homewood & Trafalgar"),
    ("Made-in-Abyss", "Made in Abyss"),
    ("Vagabond", "Vagabond"),
    ("NanoFtheAbove", "NanoFtheAbove"),
    ("Future-Projects", "Future Projects"),
)
RAP_BUCKET_SLUGS = frozenset(slug for slug, _ in RAP_BUCKETS)
STUDY_STATUSES = ("published", "in-progress", "queued")
THEORY_CATEGORIES = (
    "General / Subsubsection Introduction",
    "First-Principles Derivation",
    "Mathematical & Physical Framework",
    "Historical & Conceptual Synthesis",
)
APPLICATION_DOMAINS = (
    "Energy & Grid Infrastructure",
    "Economic & Regulatory Policy",
    "Software & Data Systems",
    "Nanotechnology & Materials",
    "Human Performance & Biomechanics",
    "General Engineering Application",
)
TODO_PRIORITIES = ("high", "medium", "low")
TODO_STATUSES = ("done", "in-progress", "planned")
VOICE_CHANNELS = ("Journal", "Podcast", "Study Memo", "Freestyle")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS study_queue (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    title TEXT NOT NULL,
    atlas_path TEXT NOT NULL,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('published', 'in-progress', 'queued')),
    study_route TEXT,
    paper_route TEXT,
    clicks INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS theory_queue (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    atlas_path TEXT NOT NULL,
    scope_prompt TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('published', 'in-progress', 'queued')),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS applications_queue (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    domain TEXT NOT NULL,
    title TEXT NOT NULL,
    atlas_path TEXT NOT NULL,
    system_design TEXT NOT NULL,
    societal_benefit TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('published', 'in-progress', 'queued')),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS wishlist_todos (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('high', 'medium', 'low')),
    atlas_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('done', 'in-progress', 'planned')),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rap_lyrics (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    bucket TEXT NOT NULL,
    title TEXT NOT NULL,
    bars TEXT NOT NULL,
    theme_cue TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'recorded', 'published'))
);

CREATE TABLE IF NOT EXISTS voice_notes (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('Journal', 'Podcast', 'Study Memo', 'Freestyle')),
    title TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds >= 0),
    audio_format TEXT NOT NULL,
    transcript TEXT NOT NULL,
    summary TEXT NOT NULL,
    atlas_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processed', 'queued'))
);

CREATE TABLE IF NOT EXISTS site_traffic (
    ip_index TEXT PRIMARY KEY,
    masked_ip TEXT NOT NULL,
    role TEXT NOT NULL,
    visits INTEGER NOT NULL DEFAULT 1,
    study_clicks INTEGER NOT NULL DEFAULT 0,
    top_section TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reabs_reminders (
    id TEXT PRIMARY KEY,
    created_on TEXT NOT NULL,
    title TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK (urgency IN ('High', 'Medium', 'Low')),
    schedule_text TEXT NOT NULL,
    days_of_week TEXT NOT NULL,
    time_of_day TEXT NOT NULL,
    phone_number TEXT NOT NULL DEFAULT '',
    phone_source TEXT NOT NULL DEFAULT 'direct',
    reasoning TEXT NOT NULL,
    default_email TEXT NOT NULL DEFAULT 'l2mcgrat@uwaterloo.ca',
    extra_emails TEXT NOT NULL DEFAULT '',
    sms_enabled INTEGER NOT NULL DEFAULT 1,
    reminders_enabled INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'muted')),
    completed_on TEXT,
    hours_spent REAL NOT NULL DEFAULT 0.0
);
""".strip()

DEFAULT_SEED: dict[str, Any] = {
    "schemaVersion": 1,
    "updatedOn": "2026-10-25",
    "studyQueue": [
        {
            "id": "ST-01",
            "createdOn": "2026-10-25",
            "title": "The AI Iceberg Index: Sector & Role Exposure Across North America",
            "atlasPath": "Business-and-Economics/Macroeconomics/Economic-Growth",
            "question": (
                "How much of the wage economy is exposed to AI beneath the visible tech surface "
                "(MIT / Oak Ridge Project Iceberg: 2.2% visible vs. 11.7% submerged), how do occupational "
                "roles break down inside the 12 major NAICS industries, and how does exposure shift across "
                "regional economies?"
            ),
            "dataset": "MIT / ORNL Project Iceberg (151M workers, 923 occupations, 32k skills) + BLS OES / StatCan NAICS sector matrices",
            "status": "published",
            "studyRoute": "Business-and-Economics/Macroeconomics/Economic-Growth/index.html",
            "paperRoute": "Business-and-Economics/Macroeconomics/Economic-Growth/Paper/index.html",
            "clicks": 38,
            "notes": "First end-to-end Workbench test study: interactive regional map, 12-industry x 6-role matrix, and compiled LaTeX PDF.",
        },
        {
            "id": "ST-02",
            "createdOn": "2026-10-25",
            "title": "2026 Alberta Referendum: All 10 Ballot Questions & Demographic Vote Anatomy",
            "atlasPath": "Business-and-Economics/Law-and-Policy/Public-Policy",
            "question": (
                "Why did Alberta voters pass all 5 non-constitutional immigration/voter-ID questions, reject "
                "all 4 constitutional amendments, and vote 74.95% to 25.05% to remain in Canada — and how did "
                "age, region, party coalition, and identity attachment divide the vote?"
            ),
            "dataset": "Elections Alberta Oct 19, 2026 count (>2.07M ballots) + Abacus Data (n=1,021) + Research Co. exit & pre-vote polls (n=811, n=601)",
            "status": "published",
            "studyRoute": "Business-and-Economics/Law-and-Policy/Public-Policy/index.html",
            "paperRoute": "Business-and-Economics/Law-and-Policy/Public-Policy/Paper/index.html",
            "clicks": 31,
            "notes": "Second Workbench study: compares ballot categories, regional/age/party splits, and voter motives with a compiled LaTeX PDF.",
        },
        {
            "id": "ST-03",
            "createdOn": "2026-10-25",
            "title": "First to Four Basketball — Leverage & Run-Distribution Study",
            "atlasPath": "Sports-and-Entertainment/Series-Hub/Analytics",
            "question": "Which challenge wins carry the highest conditional series-clinch swing, and how do streak lengths compare with a stationary coin-flip baseline?",
            "dataset": "records/basketball/series.json (13 series, 73 rounds) + upcoming Series 14+ logs",
            "status": "queued",
            "studyRoute": "Sports-and-Entertainment/Series-Hub/Analytics/index.html",
            "paperRoute": None,
            "clicks": 14,
            "notes": "Queued for the JimmyHighRoller-style deep dive once the next series batch is logged.",
        },
        {
            "id": "ST-04",
            "createdOn": "2026-10-25",
            "title": "Primer-Style Evolutionary & Market Agent Simulations",
            "atlasPath": "Science-and-Engineering/Computer-Science/Simulations",
            "question": "How do replicator dynamics and spatial resource limits shift cooperative vs. hawkish equilibria in small populations?",
            "dataset": "Synthetic agent trajectories + phase_lab simulation runner",
            "status": "queued",
            "studyRoute": None,
            "paperRoute": None,
            "clicks": 19,
            "notes": "Planned interactive simulation branch with downloadable parameter seeds.",
        },
        {
            "id": "ST-05",
            "createdOn": "2026-10-25",
            "title": "Sodium Battery Technology",
            "atlasPath": "Science-and-Engineering/Chemistry/Electrochemistry",
            "question": (
                "How does sodium-ion battery chemistry compare to lithium-ion at the elemental and electrochemical level, "
                "why do those differences arise from the periodic table, and how will grid-scale sodium batteries be "
                "deployed to prevent massive blackout power events once manufactured at scale?"
            ),
            "dataset": "ANL BatPaC v5.1 (2025) + NREL ATB Utility-Scale BESS + USGS Mineral Commodity Summaries (2025-2026) + IEA Global EV & Battery Outlook",
            "status": "published",
            "studyRoute": "Science-and-Engineering/Chemistry/Electrochemistry/index.html",
            "paperRoute": "Science-and-Engineering/Chemistry/Electrochemistry/Paper/index.html",
            "clicks": 27,
            "notes": "Added from mobile Workbench queue and promoted to canonical Electrochemistry dashboard + Tectonic PDF.",
        },
        {
            "id": "ST-06",
            "createdOn": "2026-10-25",
            "title": "Gas Price Collusion",
            "atlasPath": "Business-and-Economics/Microeconomics/Game-Theory",
            "question": (
                "Study which countries have gas prices that are much higher than cost, and see if companies are few "
                "and colluding to keep prices high. Go over Game Theory incentives as to why certain industries would "
                "do this and others wouldn't."
            ),
            "dataset": "IEA Energy Prices & Taxes + Germany MTS-K (Assad et al. 2024 JPE) + WA FuelWatch (Byrne & de Roos 2019 AER) + UK CMA (2023-2025) + NRCan / CNE",
            "status": "published",
            "studyRoute": "Business-and-Economics/Microeconomics/Game-Theory/index.html",
            "paperRoute": "Business-and-Economics/Microeconomics/Game-Theory/Paper/index.html",
            "clicks": 29,
            "notes": "Published via Gemini 4 Argon + Pandas: interactive 12-country pump price decomposition, Rockets & Feathers ECM, repeated Bertrand supergame inspector, and compiled LaTeX PDF.",
        },
        {
            "id": "ST-07",
            "createdOn": "2026-10-25",
            "title": "Calorie Intake & Deficit vs. Weightlifting Strength Rate-of-Change",
            "atlasPath": "Gaming-and-Performance-Log/Athletics/Weightlifting",
            "question": (
                "Do my lifting numbers, top-set Epley 1RM, 10+/12+ rep-target progression, and session-over-session "
                "rate of strength increase (d(Volume)/dt and d(1RM)/dt) go up or down based on same-day and lagged "
                "7-day moving-average calorie intake, protein grams, and net caloric deficit on my own site?"
            ),
            "dataset": "Internal Site Data: records/athletics/weightlifting/Weightlifting_Log.txt + records/health/diet/Diet_and_Calorie_Tracking.txt + Sleep_and_Dream_Log.txt",
            "status": "queued",
            "studyRoute": "Gaming-and-Performance-Log/Athletics/Weightlifting/index.html",
            "paperRoute": None,
            "clicks": 11,
            "notes": "Queued cross-section study using internal site athletics + calorie tracking logs once additional training weeks accumulate.",
        },
        {
            "id": "ST-08",
            "createdOn": "2026-10-26",
            "title": "AI Cost & Compute Economics: Token Inference Deflation, Training Capex & Test-Time Reasoning Scaling",
            "atlasPath": "Business-and-Economics/Emerging-Industries/Artificial-Intelligence",
            "question": (
                "How rapidly are AI inference token costs ($/1M tokens) deflating relative to frontier pre-training cluster "
                "capex ($M) and data-center energy (Wh/query), and how do Sparse MoE, Multi-head Latent Attention (MLA), "
                "open-weight models, and test-time reasoning tokens reshape enterprise AI unit economics?"
            ),
            "dataset": "Epoch AI Compute & Price Trends (2023–2026) + Artificial Analysis API Benchmarks + Stanford HAI AI Index + Google AI Studio / OpenAI / Anthropic / DeepSeek Pricing & Technical Reports",
            "status": "published",
            "studyRoute": "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/index.html",
            "paperRoute": "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/Paper/index.html",
            "clicks": 24,
            "notes": "Published via Gemini 4 Argon + Pandas: 8-model inference deflation & capex matrix, 6-layer infrastructure bottleneck inspector, cascade routing simulation, and compiled LaTeX PDF.",
        },
        {
            "id": "ST-09",
            "createdOn": "2026-10-27",
            "title": "Taxes on Generations over Time Periods",
            "atlasPath": "Business-and-Economics/Macroeconomics/Fiscal-Policy",
            "question": (
                "Using Real Dollars and Normalizing for Population Distribution, how much has the Tax Burden and Tax Rewards "
                "(in terms of how much benefits have been recieved from taxes by age group) fell on each generation? Track how "
                "different taxes have varied over the years too, I want plots of that AS WELL AS the other plots you WERE ALREADY "
                "GOING TO GENERATE, like sales tax, income tax, property tax, taxes on alcohol, gas, etc and factor in how much "
                "those affect different generations during different time periods factoring in stuff even as minute as average "
                "commute times (I want data and visuals for how different generations have different average commutes) affecting "
                "the carbon tax, vape tax targetting younger generations, property taxes impacting older generations. Everything."
            ),
            "dataset": "Statistics Canada DHEA (Tables 36-10-0587-01 & 36-10-0588-01, 1999–2025) + Survey of Household Spending (SHS) + Census/LFS Commuting Supplements + CTNS Nicotine Survey + CIHI NHEX (1975–2025) + PBO Carbon & Excise Reports",
            "status": "published",
            "studyRoute": "Business-and-Economics/Macroeconomics/Fiscal-Policy/index.html",
            "paperRoute": "Business-and-Economics/Macroeconomics/Fiscal-Policy/Paper/index.html",
            "clicks": 31,
            "notes": "Executed on Mobile via Gemini 4 Argon (20,079 tokens) & promoted to multi-plot Fiscal Policy dashboard (3 SVG plots: Tax Burden vs Rewards, Tax Instrument Mix over Time, and Commute Duration vs Fuel/Carbon/Vape/Property Tax) + Tectonic PDF.",
        },
    ],
    "theoryQueue": [
        {
            "id": "TH-01",
            "createdOn": "2026-10-25",
            "category": "General / Subsubsection Introduction",
            "title": "Electrochemical Potentials, Nernstian Equilibria & Alkali Intercalation From First Principles",
            "atlasPath": "Science-and-Engineering/Chemistry/Electrochemistry",
            "scopePrompt": "Introduce Electrochemistry from scratch: Gibbs free energy, chemical potentials, the Nernst equation, Butler-Volmer overpotentials, and Period 2 vs. Period 3 alkali intercalation.",
            "status": "published",
            "notes": "Integrated into Mental Map § 1.3.3 and the Electrochemistry destination.",
        },
        {
            "id": "TH-02",
            "createdOn": "2026-10-25",
            "category": "General / Subsubsection Introduction",
            "title": "Non-Cooperative Game Theory, Nash Equilibria & Infinitely Repeated Oligopoly Supergames",
            "atlasPath": "Business-and-Economics/Microeconomics/Game-Theory",
            "scopePrompt": "Introduce Game Theory from scratch: strategic-form games, Bertrand vs. Cournot competition, folk theorems, grim-trigger SPNE thresholds, and monitoring lags.",
            "status": "published",
            "notes": "Integrated into Mental Map § 2.2.4 and the Game Theory destination.",
        },
        {
            "id": "TH-03",
            "createdOn": "2026-10-25",
            "category": "First-Principles Derivation",
            "title": "Replicator Dynamics, Evolutionary Stability & Spatial Resource Games",
            "atlasPath": "Science-and-Engineering/Computer-Science/Simulations",
            "scopePrompt": "Derive the replicator differential equation from discrete generational payoffs and connect ESS conditions to spatial agent simulations.",
            "status": "queued",
            "notes": "Pairs with ST-04 Primer-style simulation study.",
        },
    ],
    "applicationsQueue": [
        {
            "id": "AP-01",
            "createdOn": "2026-10-25",
            "domain": "Energy & Grid Infrastructure",
            "title": "Grid-Scale Sodium-Ion BESS Architecture for Polar-Vortex Blackout Prevention",
            "atlasPath": "Science-and-Engineering/Chemistry/Electrochemistry",
            "systemDesign": "4-to-12 hour utility substation battery banks using Polyanionic NFPP / Prussian White cells with dual Al collectors and 0 V safe maintenance.",
            "societalBenefit": "Prevents catastrophic winter heating blackouts at −20°C to −35°C without lithium or copper supply bottlenecks.",
            "status": "published",
            "notes": "Live in Electrochemistry (ST-05) and Mental Map § 1.3.3.",
        },
        {
            "id": "AP-02",
            "createdOn": "2026-10-25",
            "domain": "Economic & Regulatory Policy",
            "title": "Consumer Fuel-Price Portals vs. Algorithmic Collusion Guardrails",
            "atlasPath": "Business-and-Economics/Microeconomics/Game-Theory",
            "systemDesign": "Design asymmetric disclosure rules (delayed bulk API feeds + maverick club station licensing) that help consumers search without giving oligopolists 0-second retaliation feeds.",
            "societalBenefit": "Compresses 25–28 c/L oligopoly fuel markups toward the 12 c/L competitive benchmark, saving households billions annually.",
            "status": "published",
            "notes": "Live in Game Theory (ST-06) and Mental Map § 2.2.4.",
        },
        {
            "id": "AP-03",
            "createdOn": "2026-10-25",
            "domain": "Human Performance & Biomechanics",
            "title": "Autoregulated Progressive Overload Under a Caloric Deficit",
            "atlasPath": "Gaming-and-Performance-Log/Athletics/Weightlifting",
            "systemDesign": "Combine daily TDEE/consumption logs with 10+ and 12+ rep-target thresholds to time deloads and carbohydrate refeeds.",
            "societalBenefit": "Preserves lean muscle mass and central nervous system recovery during sustained fat-loss phases.",
            "status": "queued",
            "notes": "Pairs with ST-07 Calorie vs. Lifting progression study.",
        },
    ],
    "siteTraffic": [
        {"ipIndex": "IP#OWNER", "maskedIp": "Owner / Desktop & Mobile", "role": "Admin / Owner", "visits": 94, "studyClicks": 82, "topSection": "Workbench & Business/Economics", "lastSeen": "2026-10-25"},
        {"ipIndex": "IP#7F3A (142.114.*.*)", "maskedIp": "142.114.*.* (Waterloo / ON)", "role": "Mobile Session", "visits": 38, "studyClicks": 34, "topSection": "Electrochemistry & Mental Map", "lastSeen": "2026-10-25"},
        {"ipIndex": "IP#C419 (24.84.*.*)", "maskedIp": "24.84.*.* (Western Canada)", "role": "Visitor", "visits": 21, "studyClicks": 19, "topSection": "Public Policy (Alberta Referendum)", "lastSeen": "2026-10-25"},
        {"ipIndex": "IP#9B02 (172.56.*.*)", "maskedIp": "172.56.*.* (US / Northeast)", "role": "Visitor", "visits": 16, "studyClicks": 14, "topSection": "Macroeconomics (AI Iceberg)", "lastSeen": "2026-10-25"},
        {"ipIndex": "IP#4E8D (99.224.*.*)", "maskedIp": "99.224.*.* (Toronto / ON)", "role": "Visitor", "visits": 12, "studyClicks": 9, "topSection": "Athletics & Smash Bros", "lastSeen": "2026-10-24"},
    ],
    "wishlistTodos": [
        {
            "id": "TD-01",
            "createdOn": "2026-10-25",
            "title": "Launch direct Workbench subpage (Workbench/index.html) with 4 database tables & mobile capture forms",
            "category": "Database",
            "priority": "high",
            "atlasPath": "Language-and-Programming/Coding-Projects/Relational-Database-Development",
            "status": "done",
            "notes": "Backed by SQLite (records/workbench/workbench.db) + JSON/CSV exports and GitHub Mobile issue/patch bridge.",
        },
        {
            "id": "TD-02",
            "createdOn": "2026-10-25",
            "title": "Hybrid Google Drive / local log sync with zero-token rule repair + single-line Gemini fallback",
            "category": "Automation",
            "priority": "high",
            "atlasPath": "Gaming-and-Performance-Log/Athletics",
            "status": "done",
            "notes": "python -B -m site_content.log_sync repairs common paste slips deterministically before touching any API tokens.",
        },
        {
            "id": "TD-03",
            "createdOn": "2026-10-25",
            "title": "Publish Macroeconomics AI Iceberg Index study, interactive regional sector map & LaTeX PDF",
            "category": "Studies",
            "priority": "high",
            "atlasPath": "Business-and-Economics/Macroeconomics/Economic-Growth",
            "status": "done",
            "notes": "Hosted at Macroeconomics/Economic-Growth with compiled PDF at Macroeconomics/Economic-Growth/Paper.",
        },
        {
            "id": "TD-04",
            "createdOn": "2026-10-25",
            "title": "Publish October 2026 Alberta Referendum 10-question & demographic vote study + LaTeX PDF",
            "category": "Studies",
            "priority": "high",
            "atlasPath": "Business-and-Economics/Law-and-Policy/Public-Policy",
            "status": "done",
            "notes": "Hosted at Law-and-Policy/Public-Policy with compiled PDF at Law-and-Policy/Public-Policy/Paper.",
        },
        {
            "id": "TD-05",
            "createdOn": "2026-10-25",
            "title": "Connect Cloudflare Worker + D1 / Supabase insert endpoint for 1-tap mobile saves without Git commits",
            "category": "Database",
            "priority": "medium",
            "atlasPath": "Language-and-Programming/Coding-Projects/Database-Exploration",
            "status": "in-progress",
            "notes": "Browser forms already emit the exact JSON payload and fall back to localStorage + GitHub Mobile.",
        },
        {
            "id": "TD-06",
            "createdOn": "2026-10-18",
            "title": "Redact start pin and street names from Tempo1.png and add to the Running dashboard",
            "category": "Athletics",
            "priority": "medium",
            "atlasPath": "Gaming-and-Performance-Log/Athletics/Running",
            "status": "planned",
            "notes": "Original screenshot is git-ignored until redacted like interval_track_1.png.",
        },
        {
            "id": "TD-07",
            "createdOn": "2026-10-04",
            "title": "Log timed 5x50 m, 10x50 m and 5x100 m swim sets once pool-safe watch arrives",
            "category": "Athletics",
            "priority": "low",
            "atlasPath": "Gaming-and-Performance-Log/Athletics/Swimming",
            "status": "planned",
            "notes": "Keep distance-only sessions intact and add set-window split columns.",
        },
    ],
    "rapLyrics": [
        {
            "id": "RL-01",
            "createdOn": "2026-10-25",
            "bucket": "Homewood-and-Trafalgar",
            "title": "Iceberg Underneath (Post-Workout Bar)",
            "bars": (
                "Two percent above the water, ninety-eight in the dark,\n"
                "They only count the lightning when the server catches a spark.\n"
                "Every ledger in the tower got a ghost in the sheet,\n"
                "I'm running tempo up the Escarpment just to measure the beat."
            ),
            "themeCue": "Automation, unseen leverage, late-night training",
            "status": "draft",
        },
        {
            "id": "RL-02",
            "createdOn": "2026-10-25",
            "bucket": "Vagabond",
            "title": "Cold Air, High NEAT",
            "bars": (
                "Sixteen thousand steps before the sun clears the frost,\n"
                "Count the deficit in chalk dust, never count what it cost.\n"
                "Plate loaded to the collar, twelve reps on the bar,\n"
                "Keep the notebook in the gym bag where the blueprints are."
            ),
            "themeCue": "Discipline, October cut, self-reliance",
            "status": "draft",
        },
        {
            "id": "RL-03",
            "createdOn": "2026-10-25",
            "bucket": "Future-Projects",
            "title": "Ballot Box / Fault Line",
            "bars": (
                "Ten questions on the paper, three-to-one on the stay,\n"
                "Half the room wants a megaphone, half wants a way.\n"
                "Draw the border in the oil sand, draw it in the poll,\n"
                "Everybody wants the leverage till you tally the toll."
            ),
            "themeCue": "Civic fracture, leverage vs. exit",
            "status": "draft",
        },
    ],
    "voiceNotes": [
        {
            "id": "VN-01",
            "createdOn": "2026-10-25",
            "channel": "Study Memo",
            "title": "Weekend Architecture Note: Workbench + GitHub Mobile Studies",
            "durationSeconds": 94,
            "audioFormat": "webm/opus (browser recorder) or m4a/wav upload",
            "transcript": (
                "Post-workout note: set up a single Workbench subpage where I can drop a study idea with its dataset, "
                "log wishlist site changes, capture spontaneous rap bars into the right project bucket, or record a "
                "voice memo that gets transcribed into the journal and podcast queue. Test the whole pipeline with two "
                "real studies: the AI Iceberg Index across industries and roles, and the October 19 Alberta referendum "
                "breakdown by demographic."
            ),
            "summary": "Defines the four-table Workbench schema and the two flagship Macroeconomics / Public Policy studies.",
            "atlasPath": "Language-and-Programming/Coding-Projects/Relational-Database-Development",
            "status": "processed",
        },
        {
            "id": "VN-02",
            "createdOn": "2026-10-25",
            "channel": "Journal",
            "title": "Training & Recovery Check-In (Week 3 of October Cut)",
            "durationSeconds": 68,
            "audioFormat": "wav (44.1 kHz mono PCM)",
            "transcript": (
                "BMR is locked at 2050 kcal for October with high NEAT from walking and cold weather keeping daily burn "
                "around 3,400 kcal. Hitting 10+ and 12+ rep targets on Bent Over Rows and Barbell Curls while keeping "
                "the weekly deficit right around 4,000 kcal."
            ),
            "summary": "Cross-links October calorie balance (~577 kcal/day average deficit) with lifting rep-target progression.",
            "atlasPath": "Gaming-and-Performance-Log/Health/Diet",
            "status": "processed",
        },
    ],
    "reabsReminders": [
        {
            "id": "RB-01",
            "createdOn": "2026-10-29",
            "title": "Contact Manulife Financial Regarding TFSA Setup",
            "urgency": "Medium",
            "scheduleText": "2pm Mon, Wed, Thurs",
            "daysOfWeek": "Mon,Wed,Thu",
            "timeOfDay": "14:00",
            "phoneNumber": "1-888-790-4387",
            "phoneSource": "google-gemini",
            "reasoning": "I want to be able to pull money out later in the future that I've forgetable put away over time, and also this provides me an easier way to save money unconciously.",
            "defaultEmail": "l2mcgrat@uwaterloo.ca",
            "extraEmails": "",
            "smsEnabled": 1,
            "remindersEnabled": 1,
            "status": "active",
            "completedOn": None,
            "hoursSpent": 0.0,
        },
        {
            "id": "RB-02",
            "createdOn": "2026-10-29",
            "title": "Contact HCM AR and Payroll Regarding Missed Overtime",
            "urgency": "High",
            "scheduleText": "8am Mon, Thurs",
            "daysOfWeek": "Mon,Thu",
            "timeOfDay": "08:00",
            "phoneNumber": "N/A",
            "phoneSource": "na",
            "reasoning": "I want to understand why my 6hrs overtime for Oct 19th to 23rd was not included in my pay, and also understand the whole process for approving overtime and why this wasn't done automatically this time.",
            "defaultEmail": "l2mcgrat@uwaterloo.ca",
            "extraEmails": "",
            "smsEnabled": 1,
            "remindersEnabled": 1,
            "status": "active",
            "completedOn": None,
            "hoursSpent": 0.0,
        },
        {
            "id": "RB-03",
            "createdOn": "2026-10-29",
            "title": "Barrie Recycling and Waste Corp",
            "urgency": "Low",
            "scheduleText": "3pm Mon-Fri",
            "daysOfWeek": "Mon,Tue,Wed,Thu,Fri",
            "timeOfDay": "15:00",
            "phoneNumber": "705-792-6557",
            "phoneSource": "direct",
            "reasoning": "Nima wants me to have bins and I want to look proper cause he's my new buddy.",
            "defaultEmail": "l2mcgrat@uwaterloo.ca",
            "extraEmails": "",
            "smsEnabled": 1,
            "remindersEnabled": 1,
            "status": "active",
            "completedOn": None,
            "hoursSpent": 0.0,
        },
    ],
}


def validate_workbench(data: dict[str, Any]) -> dict[str, Any]:
    """Validate every table row against the site outline and allowed enums."""
    if set(RAP_PAGES) != RAP_BUCKET_SLUGS:
        raise ValueError("RAP_BUCKETS must match catalog.RAP_PAGES keys.")
    studies = [
        {**row, "clicks": int(row.get("clicks", 0))}
        for row in data.get("studyQueue", [])
    ]
    theory = data.get("theoryQueue", DEFAULT_SEED["theoryQueue"])
    applications = data.get("applicationsQueue", DEFAULT_SEED["applicationsQueue"])
    traffic = data.get("siteTraffic", DEFAULT_SEED["siteTraffic"])
    todos = data.get("wishlistTodos", [])
    lyrics = data.get("rapLyrics", [])
    voices = data.get("voiceNotes", [])
    reabs = data.get("reabsReminders", DEFAULT_SEED["reabsReminders"])
    seen_ids: set[str] = set()

    def check_id(raw_id: str) -> None:
        if not raw_id or raw_id in seen_ids:
            raise ValueError(f"Duplicate or empty workbench id {raw_id!r}")
        seen_ids.add(raw_id)

    for row in studies:
        check_id(row["id"])
        if row["atlasPath"] not in NODES:
            raise ValueError(f"Study {row['id']} references unknown atlas node {row['atlasPath']!r}")
        if row["status"] not in STUDY_STATUSES:
            raise ValueError(f"Study {row['id']} has invalid status {row['status']!r}")
    for row in theory:
        check_id(row["id"])
        if row["atlasPath"] not in NODES:
            raise ValueError(f"Theory {row['id']} references unknown atlas node {row['atlasPath']!r}")
        if row["status"] not in STUDY_STATUSES:
            raise ValueError(f"Theory {row['id']} has invalid status {row['status']!r}")
    for row in applications:
        check_id(row["id"])
        if row["atlasPath"] not in NODES:
            raise ValueError(f"Application {row['id']} references unknown atlas node {row['atlasPath']!r}")
        if row["status"] not in STUDY_STATUSES:
            raise ValueError(f"Application {row['id']} has invalid status {row['status']!r}")
    for row in todos:
        check_id(row["id"])
        if row["atlasPath"] not in NODES:
            raise ValueError(f"Todo {row['id']} references unknown atlas node {row['atlasPath']!r}")
        if row["priority"] not in TODO_PRIORITIES or row["status"] not in TODO_STATUSES:
            raise ValueError(f"Todo {row['id']} has invalid priority/status")
    for row in lyrics:
        check_id(row["id"])
        if row["bucket"] not in RAP_BUCKET_SLUGS:
            raise ValueError(f"Lyric {row['id']} has unknown Rap bucket {row['bucket']!r}")
        if row["status"] not in ("draft", "recorded", "published"):
            raise ValueError(f"Lyric {row['id']} has invalid status {row['status']!r}")
    for row in voices:
        check_id(row["id"])
        if row["channel"] not in VOICE_CHANNELS:
            raise ValueError(f"Voice note {row['id']} has invalid channel {row['channel']!r}")
        if row["atlasPath"] not in NODES:
            raise ValueError(f"Voice note {row['id']} references unknown atlas node {row['atlasPath']!r}")
        if int(row["durationSeconds"]) < 0 or row["status"] not in ("processed", "queued"):
            raise ValueError(f"Voice note {row['id']} has invalid duration or status")
    for row in reabs:
        check_id(row["id"])
        if row["urgency"] not in ("High", "Medium", "Low"):
            raise ValueError(f"REABS {row['id']} has invalid urgency {row['urgency']!r}")
        if row["status"] not in ("active", "completed", "muted"):
            raise ValueError(f"REABS {row['id']} has invalid status {row['status']!r}")

    summary = {
        "studies": len(studies),
        "studiesPublished": sum(s["status"] == "published" for s in studies),
        "studiesQueued": sum(s["status"] != "published" for s in studies),
        "studyClicksTotal": sum(int(s.get("clicks", 0)) for s in studies),
        "theory": len(theory),
        "theoryPublished": sum(t["status"] == "published" for t in theory),
        "applications": len(applications),
        "applicationsPublished": sum(a["status"] == "published" for a in applications),
        "todos": len(todos),
        "todosDone": sum(t["status"] == "done" for t in todos),
        "todosOpen": sum(t["status"] != "done" for t in todos),
        "lyrics": len(lyrics),
        "lyricBuckets": len({r["bucket"] for r in lyrics}),
        "voiceNotes": len(voices),
        "voiceSeconds": sum(int(v["durationSeconds"]) for v in voices),
        "uniqueIpIndexes": len(traffic),
        "totalVisits": sum(int(ip.get("visits", 0)) for ip in traffic),
        "reabsTotal": len(reabs),
        "reabsActive": sum(r["status"] == "active" for r in reabs),
        "reabsCompleted": sum(r["status"] == "completed" for r in reabs),
        "reabsHoursTotal": round(sum(float(r.get("hoursSpent", 0.0)) for r in reabs), 2),
    }
    return {
        "schemaVersion": data.get("schemaVersion", 1),
        "updatedOn": data.get("updatedOn", "2026-10-25"),
        "rapBuckets": [{"slug": slug, "title": title, "route": f"Language-and-Programming/Rap/{slug}/index.html"}
                       for slug, title in RAP_BUCKETS],
        "voiceChannels": list(VOICE_CHANNELS),
        "theoryCategories": list(THEORY_CATEGORIES),
        "applicationDomains": list(APPLICATION_DOMAINS),
        "studyQueue": studies,
        "theoryQueue": theory,
        "applicationsQueue": applications,
        "siteTraffic": traffic,
        "wishlistTodos": todos,
        "rapLyrics": lyrics,
        "voiceNotes": voices,
        "reabsReminders": reabs,
        "summary": summary,
        "schemaSql": SCHEMA_SQL,
    }


def sync_sqlite(db_path: Path, data: dict[str, Any]) -> None:
    """Materialize the validated workbench tables into a relational SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        for tbl in ("study_queue", "theory_queue", "applications_queue", "wishlist_todos", "rap_lyrics", "voice_notes", "site_traffic", "reabs_reminders"):
            conn.execute(f"DROP TABLE IF EXISTS {tbl}")
        conn.executescript(SCHEMA_SQL)
        conn.executemany(
            "INSERT INTO study_queue (id, created_on, title, atlas_path, question, dataset, status, study_route, paper_route, clicks, notes) "
            "VALUES (:id, :createdOn, :title, :atlasPath, :question, :dataset, :status, :studyRoute, :paperRoute, :clicks, :notes)",
            data["studyQueue"],
        )
        conn.executemany(
            "INSERT INTO theory_queue (id, created_on, category, title, atlas_path, scope_prompt, status, notes) "
            "VALUES (:id, :createdOn, :category, :title, :atlasPath, :scopePrompt, :status, :notes)",
            data["theoryQueue"],
        )
        conn.executemany(
            "INSERT INTO applications_queue (id, created_on, domain, title, atlas_path, system_design, societal_benefit, status, notes) "
            "VALUES (:id, :createdOn, :domain, :title, :atlasPath, :systemDesign, :societalBenefit, :status, :notes)",
            data["applicationsQueue"],
        )
        conn.executemany(
            "INSERT INTO wishlist_todos (id, created_on, title, category, priority, atlas_path, status, notes) "
            "VALUES (:id, :createdOn, :title, :category, :priority, :atlasPath, :status, :notes)",
            data["wishlistTodos"],
        )
        conn.executemany(
            "INSERT INTO rap_lyrics (id, created_on, bucket, title, bars, theme_cue, status) "
            "VALUES (:id, :createdOn, :bucket, :title, :bars, :themeCue, :status)",
            data["rapLyrics"],
        )
        conn.executemany(
            "INSERT INTO voice_notes (id, created_on, channel, title, duration_seconds, audio_format, transcript, summary, atlas_path, status) "
            "VALUES (:id, :createdOn, :channel, :title, :durationSeconds, :audioFormat, :transcript, :summary, :atlasPath, :status)",
            data["voiceNotes"],
        )
        conn.executemany(
            "INSERT INTO site_traffic (ip_index, masked_ip, role, visits, study_clicks, top_section, last_seen) "
            "VALUES (:ipIndex, :maskedIp, :role, :visits, :studyClicks, :topSection, :lastSeen)",
            data["siteTraffic"],
        )
        conn.executemany(
            "INSERT INTO reabs_reminders (id, created_on, title, urgency, schedule_text, days_of_week, time_of_day, "
            "phone_number, phone_source, reasoning, default_email, extra_emails, sms_enabled, reminders_enabled, status, completed_on, hours_spent) "
            "VALUES (:id, :createdOn, :title, :urgency, :scheduleText, :daysOfWeek, :timeOfDay, "
            ":phoneNumber, :phoneSource, :reasoning, :defaultEmail, :extraEmails, :smsEnabled, :remindersEnabled, :status, :completedOn, :hoursSpent)",
            data["reabsReminders"],
        )
        conn.commit()


def load_workbench(root: Path) -> dict[str, Any]:
    """Load records/workbench/workbench.json (creating from DEFAULT_SEED if absent) and sync SQLite."""
    seed_file = root / SEED_PATH
    if seed_file.is_file():
        raw = json.loads(seed_file.read_text(encoding="utf-8"))
    else:
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        raw = DEFAULT_SEED
        seed_file.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    validated = validate_workbench(raw)
    sync_sqlite(root / SQLITE_PATH, validated)
    return validated


def workbench_rows(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Flatten the four workbench tables for CSV export."""
    return {
        "studies": [
            {
                "id": s["id"], "createdOn": s["createdOn"], "title": s["title"], "atlasPath": s["atlasPath"],
                "question": s["question"], "dataset": s["dataset"], "status": s["status"],
                "studyRoute": s["studyRoute"] or "", "paperRoute": s["paperRoute"] or "", "notes": s["notes"],
            }
            for s in data["studyQueue"]
        ],
        "todos": [dict(t) for t in data["wishlistTodos"]],
        "lyrics": [dict(r) for r in data["rapLyrics"]],
        "voice": [dict(v) for v in data["voiceNotes"]],
    }


def inspect_wav_duration(path: Path) -> int:
    """Read duration in whole seconds from a standard PCM .wav file without external deps."""
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate() or 1
        return round(handle.getnframes() / rate)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    add_lyric = sub.add_parser("add-lyric", help="Append a spontaneous rap lyric entry.")
    add_lyric.add_argument("--bucket", required=True, choices=[b for b, _ in RAP_BUCKETS])
    add_lyric.add_argument("--title", required=True)
    add_lyric.add_argument("--bars", required=True)
    add_lyric.add_argument("--cue", default="")
    add_lyric.add_argument("--date", default="2026-10-25")

    add_todo = sub.add_parser("add-todo", help="Append a wishlist todo entry.")
    add_todo.add_argument("--title", required=True)
    add_todo.add_argument("--category", default="Website")
    add_todo.add_argument("--priority", default="medium", choices=TODO_PRIORITIES)
    add_todo.add_argument("--atlas-path", default="Language-and-Programming/Coding-Projects/Website-Changes")
    add_todo.add_argument("--notes", default="")
    add_todo.add_argument("--date", default="2026-10-25")

    args = parser.parse_args()
    seed_file = root / SEED_PATH
    data = load_workbench(root)
    raw = json.loads(seed_file.read_text(encoding="utf-8"))
    if args.cmd == "add-lyric":
        next_id = f"RL-{len(raw['rapLyrics']) + 1:02d}"
        raw["rapLyrics"].append({
            "id": next_id, "createdOn": args.date, "bucket": args.bucket,
            "title": args.title, "bars": args.bars, "themeCue": args.cue, "status": "draft",
        })
        seed_file.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        data = load_workbench(root)
        print(f"Added {next_id} to {args.bucket}")
    elif args.cmd == "add-todo":
        next_id = f"TD-{len(raw['wishlistTodos']) + 1:02d}"
        raw["wishlistTodos"].append({
            "id": next_id, "createdOn": args.date, "title": args.title, "category": args.category,
            "priority": args.priority, "atlasPath": args.atlas_path, "status": "planned", "notes": args.notes,
        })
        seed_file.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        data = load_workbench(root)
        print(f"Added {next_id}: {args.title}")
    else:
        s = data["summary"]
        print(f"Workbench DB synced ({SQLITE_PATH}): {s['studies']} studies, {s['todos']} todos, {s['lyrics']} lyrics, {s['voiceNotes']} voice notes")


if __name__ == "__main__":
    main()
