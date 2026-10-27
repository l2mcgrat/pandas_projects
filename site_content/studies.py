"""Data models and CSV/JSON exporters for the Macroeconomics AI Iceberg and 2026 Alberta Referendum studies."""

from __future__ import annotations

from typing import Any

MACRO_STUDY_ROUTE = "Business-and-Economics/Macroeconomics/Economic-Growth/index.html"
MACRO_PAPER_ROUTE = "Business-and-Economics/Macroeconomics/Economic-Growth/Paper/index.html"
ALBERTA_STUDY_ROUTE = "Business-and-Economics/Law-and-Policy/Public-Policy/index.html"
ALBERTA_PAPER_ROUTE = "Business-and-Economics/Law-and-Policy/Public-Policy/Paper/index.html"
GAS_STUDY_ROUTE = "Business-and-Economics/Microeconomics/Game-Theory/index.html"
GAS_TAB_ROUTE = "Business-and-Economics/Microeconomics/Game-Theory/Gas-Price-Collusion/index.html"
GAS_PAPER_ROUTE = "Business-and-Economics/Microeconomics/Game-Theory/Paper/index.html"
SODIUM_STUDY_ROUTE = "Science-and-Engineering/Chemistry/Electrochemistry/index.html"
SODIUM_TAB_ROUTE = "Science-and-Engineering/Chemistry/Electrochemistry/Sodium-Battery-Technology/index.html"
SODIUM_PAPER_ROUTE = "Science-and-Engineering/Chemistry/Electrochemistry/Paper/index.html"
AI_COST_STUDY_ROUTE = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/index.html"
AI_COST_TAB_ROUTE = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/AI-Cost-Study/index.html"
AI_COST_PAPER_ROUTE = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/Paper/index.html"
GEN_TAX_STUDY_ROUTE = "Business-and-Economics/Macroeconomics/Fiscal-Policy/index.html"
GEN_TAX_TAB_ROUTE = "Business-and-Economics/Macroeconomics/Fiscal-Policy/Taxes-on-Generations/index.html"
GEN_TAX_PAPER_ROUTE = "Business-and-Economics/Macroeconomics/Fiscal-Policy/Paper/index.html"

ROLE_FAMILIES: tuple[tuple[str, str, float, float], ...] = (
    # (key, label, surface_ai_pct, submerged_ai_pct)
    ("analytical", "Analytical, Engineering & Tech", 14.0, 34.0),
    ("admin", "Administrative, Clerical & Ops Support", 2.5, 46.0),
    ("management", "Management, Finance & Strategy", 2.0, 24.0),
    ("sales", "Sales, Intake & Client Service", 2.2, 22.0),
    ("trades", "Skilled Trades, Plant & Transport", 0.4, 4.5),
    ("care", "Hands-On Clinical, Site & Hospitality", 0.3, 3.5),
)

# 12 major NAICS sectors: employment share (% of workforce), GDP share (%), median wage ($ USD),
# surface AI exposure (% of sector wage bill), submerged Iceberg exposure (% of sector wage bill),
# and role-share percentages summing to 100 across the 6 ROLE_FAMILIES.
INDUSTRY_SECTORS: tuple[dict[str, Any], ...] = (
    {
        "code": "51", "name": "Information, Software & Media",
        "employmentShare": 2.1, "gdpShare": 5.5, "medianWage": 104000,
        "surfacePct": 16.8, "submergedPct": 26.4,
        "roles": {"analytical": 44, "admin": 12, "management": 16, "sales": 16, "trades": 8, "care": 4},
        "aiWipeoutRisk": "Routine coding, QA boilerplate, localization, tier-1 support, and ad-ops scheduling.",
        "humanMoat": "Systems architecture, novel product direction, proprietary data negotiation, and security accountability.",
    },
    {
        "code": "52", "name": "Finance, Insurance & Real Estate",
        "employmentShare": 6.0, "gdpShare": 20.7, "medianWage": 84000,
        "surfacePct": 4.2, "submergedPct": 28.6,
        "roles": {"analytical": 26, "admin": 28, "management": 18, "sales": 22, "trades": 2, "care": 4},
        "aiWipeoutRisk": "Underwriting packets, claims triage, KYC/AML document review, routine financial modeling, and reconciliation.",
        "humanMoat": "Fiduciary sign-off, complex deal structuring, regulatory relationship management, and physical asset appraisal.",
    },
    {
        "code": "54", "name": "Professional, Scientific & Technical",
        "employmentShare": 7.4, "gdpShare": 8.1, "medianWage": 96000,
        "surfacePct": 6.9, "submergedPct": 27.1,
        "roles": {"analytical": 46, "admin": 18, "management": 16, "sales": 10, "trades": 5, "care": 5},
        "aiWipeoutRisk": "Junior legal discovery, contract redlining, standard CAD drafting, tax prep, and market-research synthesis.",
        "humanMoat": "Wet-lab experimentation, courtroom advocacy, P.Eng. stamp liability, and ambiguous client problem-framing.",
    },
    {
        "code": "31-33", "name": "Manufacturing (Advanced & Process)",
        "employmentShare": 8.3, "gdpShare": 10.3, "medianWage": 61000,
        "surfacePct": 1.4, "submergedPct": 11.8,
        "roles": {"analytical": 14, "admin": 11, "management": 10, "sales": 6, "trades": 54, "care": 5},
        "aiWipeoutRisk": "ERP supply-chain scheduling, quality-log reporting, vendor invoicing, and routine BOM procurement.",
        "humanMoat": "Line maintenance, die/tooling setup, physical process troubleshooting on the shop floor, and safety lockouts.",
    },
    {
        "code": "62", "name": "Healthcare & Social Assistance",
        "employmentShare": 14.1, "gdpShare": 8.6, "medianWage": 63000,
        "surfacePct": 0.9, "submergedPct": 10.4,
        "roles": {"analytical": 10, "admin": 18, "management": 8, "sales": 4, "trades": 4, "care": 56},
        "aiWipeoutRisk": "Medical coding (ICD-10), prior-authorization paperwork, intake transcription, and shift rostering.",
        "humanMoat": "Bedside nursing, surgical & emergency intervention, physical therapy, and high-trust patient care.",
    },
    {
        "code": "92", "name": "Public Administration & Government",
        "employmentShare": 4.8, "gdpShare": 11.4, "medianWage": 72000,
        "surfacePct": 1.1, "submergedPct": 15.9,
        "roles": {"analytical": 20, "admin": 30, "management": 14, "sales": 6, "trades": 10, "care": 20},
        "aiWipeoutRisk": "Permit intake verification, benefits eligibility screening, freedom-of-information redaction, and case summaries.",
        "humanMoat": "First-responder policing/fire, statutory adjudication, public hearings, and field inspections.",
    },
    {
        "code": "61", "name": "Educational Services",
        "employmentShare": 8.9, "gdpShare": 5.2, "medianWage": 59000,
        "surfacePct": 1.3, "submergedPct": 12.6,
        "roles": {"analytical": 16, "admin": 16, "management": 10, "sales": 4, "trades": 6, "care": 48},
        "aiWipeoutRisk": "Standardized grading, syllabus/worksheet drafting, admissions paperwork, and registrar scheduling.",
        "humanMoat": "In-room classroom management, childhood socialization, hands-on lab instruction, and mentorship.",
    },
    {
        "code": "42-45", "name": "Retail & Wholesale Trade",
        "employmentShare": 12.8, "gdpShare": 11.9, "medianWage": 44000,
        "surfacePct": 1.2, "submergedPct": 10.9,
        "roles": {"analytical": 6, "admin": 14, "management": 10, "sales": 42, "trades": 18, "care": 10},
        "aiWipeoutRisk": "Call-center order tracking, catalog copywriting, demand forecasting sheets, and automated checkout.",
        "humanMoat": "Floor merchandising, complex B2B technical sales, loss prevention, and last-yard stocking.",
    },
    {
        "code": "48-49", "name": "Transportation, Warehousing & Utilities",
        "employmentShare": 5.1, "gdpShare": 4.9, "medianWage": 58000,
        "surfacePct": 0.8, "submergedPct": 8.7,
        "roles": {"analytical": 8, "admin": 14, "management": 8, "sales": 5, "trades": 58, "care": 7},
        "aiWipeoutRisk": "Freight brokerage matching, customs manifest filing, dispatch routing, and billing audit.",
        "humanMoat": "Heavy-haul driving in adverse weather, high-voltage line repair, marine/rail operations, and physical loading.",
    },
    {
        "code": "21", "name": "Energy, Mining & Oil/Gas Extraction",
        "employmentShare": 1.6, "gdpShare": 3.4, "medianWage": 89000,
        "surfacePct": 1.5, "submergedPct": 9.8,
        "roles": {"analytical": 22, "admin": 10, "management": 10, "sales": 4, "trades": 48, "care": 6},
        "aiWipeoutRisk": "Seismic log pre-screening, reservoir simulation setup, land-lease clerical compliance, and SCADA reporting.",
        "humanMoat": "Rig/wellhead operations, pipeline maintenance, field geology, and hazardous-environment turnaround crews.",
    },
    {
        "code": "23", "name": "Construction & Civil Infrastructure",
        "employmentShare": 6.1, "gdpShare": 4.4, "medianWage": 62000,
        "surfacePct": 0.5, "submergedPct": 5.4,
        "roles": {"analytical": 8, "admin": 9, "management": 11, "sales": 4, "trades": 64, "care": 4},
        "aiWipeoutRisk": "Quantity takeoffs, routine bid estimation, RFIs, and progress-billing paperwork.",
        "humanMoat": "Unstructured job-site carpentry, electrical, plumbing, ironwork, crane operation, and municipal inspection.",
    },
    {
        "code": "72", "name": "Accommodation, Food & Recreation",
        "employmentShare": 9.4, "gdpShare": 3.6, "medianWage": 34000,
        "surfacePct": 0.4, "submergedPct": 4.8,
        "roles": {"analytical": 2, "admin": 7, "management": 9, "sales": 14, "trades": 8, "care": 60},
        "aiWipeoutRisk": "Reservation bots, drive-thru voice ordering, and multi-property revenue pricing.",
        "humanMoat": "Line cooking, table hospitality, housekeeping, live events, and culinary craft.",
    },
)

# 12 North American regional economies for the interactive sector map (x, y in 900x460 SVG).
REGIONAL_ECONOMIES: tuple[dict[str, Any], ...] = (
    {
        "id": "ON", "name": "Ontario (Toronto–Waterloo–Auto Corridor)", "country": "Canada",
        "x": 635, "y": 195, "gdpBillions": 830, "workersMillions": 8.0,
        "surfacePct": 2.6, "submergedPct": 13.1,
        "sectors": {"Finance & Insurance": 22, "Manufacturing": 13, "Prof. & Tech": 11, "Healthcare & Ed": 15, "Trade & Logistics": 16, "Construction & Energy": 9},
        "signature": "High submerged exposure in Bay Street back-office finance alongside protected auto/process manufacturing in southwestern Ontario.",
    },
    {
        "id": "AB", "name": "Alberta (Calgary–Edmonton–Oil Sands)", "country": "Canada",
        "x": 285, "y": 135, "gdpBillions": 345, "workersMillions": 2.5,
        "surfacePct": 1.6, "submergedPct": 9.9,
        "sectors": {"Energy & Mining": 26, "Construction & Engineering": 13, "Finance & Corporate HQ": 12, "Trade & Logistics": 14, "Healthcare & Ed": 13, "Manufacturing & Ag": 11},
        "signature": "Field extraction and skilled trades anchor a high physical moat, while Calgary corporate/engineering headquarters carry the submerged AI exposure.",
    },
    {
        "id": "BC", "name": "British Columbia (Pacific Gateway)", "country": "Canada",
        "x": 195, "y": 145, "gdpBillions": 310, "workersMillions": 2.9,
        "surfacePct": 2.5, "submergedPct": 11.4,
        "sectors": {"Real Estate & Finance": 21, "Trade, Port & Logistics": 16, "Prof., Tech & Film": 12, "Forestry, Mining & Energy": 11, "Healthcare & Ed": 15, "Hospitality": 9},
        "signature": "Port logistics, natural resources, and construction balance urban software/VFX exposure in Vancouver.",
    },
    {
        "id": "QC", "name": "Quebec (Montreal–Aerospace & Hydro)", "country": "Canada",
        "x": 705, "y": 165, "gdpBillions": 440, "workersMillions": 4.5,
        "surfacePct": 2.4, "submergedPct": 12.0,
        "sectors": {"Manufacturing & Aerospace": 15, "Finance & Admin": 16, "Prof., AI & Tech": 11, "Healthcare & Public": 19, "Trade & Logistics": 15, "Hydro & Resources": 8},
        "signature": "Strong AI research hub (Mila) paired with heavy aerospace/industrial manufacturing and public-sector services.",
    },
    {
        "id": "CA", "name": "California (Bay Area–SoCal–Central Valley)", "country": "USA",
        "x": 165, "y": 315, "gdpBillions": 4100, "workersMillions": 18.6,
        "surfacePct": 4.8, "submergedPct": 13.6,
        "sectors": {"Info, Software & Media": 15, "Finance & Real Estate": 20, "Prof. & Biotech": 13, "Trade & Ports": 14, "Healthcare & Ed": 14, "Manufacturing & Ag": 11},
        "signature": "Highest visible 'tip of the iceberg' (4.8%) due to Silicon Valley, plus large submerged exposure in entertainment, legal, and financial ops.",
    },
    {
        "id": "TX", "name": "Texas (Houston–DFW–Austin Triangle)", "country": "USA",
        "x": 430, "y": 375, "gdpBillions": 2650, "workersMillions": 14.2,
        "surfacePct": 2.3, "submergedPct": 11.2,
        "sectors": {"Energy, Refining &_Chem": 17, "Manufacturing & Semis": 12, "Trade & Logistics": 16, "Finance & Corporate": 16, "Prof. & Tech": 11, "Construction": 9},
        "signature": "DFW/Austin corporate & tech hubs create mid-tier cognitive exposure, buffered by Gulf Coast energy, refining, and construction.",
    },
    {
        "id": "NY", "name": "New York & Tri-State Corridor", "country": "USA",
        "x": 745, "y": 240, "gdpBillions": 2250, "workersMillions": 9.8,
        "surfacePct": 3.4, "submergedPct": 15.8,
        "sectors": {"Finance & Insurance": 29, "Prof., Legal & Media": 16, "Healthcare & Ed": 17, "Public Admin": 10, "Trade & Real Estate": 14, "Manufacturing": 5},
        "signature": "Highest submerged Iceberg exposure (15.8%): dense concentration of financial analysis, compliance, legal, and administrative roles.",
    },
    {
        "id": "GL", "name": "Great Lakes Manufacturing Belt (MI/OH/IL/IN)", "country": "USA",
        "x": 580, "y": 260, "gdpBillions": 3150, "workersMillions": 19.4,
        "surfacePct": 1.6, "submergedPct": 11.9,
        "sectors": {"Manufacturing & Auto": 19, "Finance, Insurance & HQ": 17, "Trade, Rail & Logistics": 16, "Healthcare & Ed": 15, "Prof. & Engineering": 10, "Agriculture": 6},
        "signature": "The classic Iceberg case highlighted by ORNL: low visible tech-sector share (1.6%), but 7.4x larger submerged exposure in plant administration, supply chain, and insurance.",
    },
    {
        "id": "NE", "name": "New England (Boston Biotech & Hartford Finance)", "country": "USA",
        "x": 790, "y": 210, "gdpBillions": 1420, "workersMillions": 7.5,
        "surfacePct": 3.5, "submergedPct": 14.4,
        "sectors": {"Prof., Biotech & R&D": 17, "Finance & Insurance": 21, "Higher Ed & Healthcare": 20, "Info & Software": 9, "Precision Manufacturing": 10, "Trade": 11},
        "signature": "High white-collar density in insurance, asset management, and university administration alongside protected wet-lab R&D.",
    },
    {
        "id": "PNW", "name": "Pacific Northwest (Seattle–Portland)", "country": "USA",
        "x": 190, "y": 215, "gdpBillions": 1180, "workersMillions": 6.1,
        "surfacePct": 4.4, "submergedPct": 12.5,
        "sectors": {"Cloud, Software & Retail HQ": 18, "Aerospace & Manufacturing": 13, "Trade, Ports & Timber": 15, "Finance & Real Estate": 17, "Healthcare & Ed": 14, "Construction": 8},
        "signature": "Second-highest visible tech exposure (4.4%) from hyperscale cloud & software HQs, contrasted with aerospace machining and maritime trade.",
    },
    {
        "id": "SE", "name": "US Southeast (Atlanta–Charlotte–Florida)", "country": "USA",
        "x": 665, "y": 355, "gdpBillions": 3800, "workersMillions": 24.5,
        "surfacePct": 1.9, "submergedPct": 11.6,
        "sectors": {"Trade, Ports & Aviation": 18, "Banking & Back-Office": 18, "Hospitality & Tourism": 14, "Healthcare": 15, "Construction": 10, "Auto & Aero Mfg": 9},
        "signature": "Charlotte banking and Atlanta corporate back-offices drive submerged clerical exposure; hospitality and construction remain physical.",
    },
    {
        "id": "MW", "name": "Mountain & Plains (CO/UT/NM/KS)", "country": "USA",
        "x": 345, "y": 285, "gdpBillions": 1650, "workersMillions": 9.2,
        "surfacePct": 2.4, "submergedPct": 11.1,
        "sectors": {"Energy, Mining & Ag": 15, "Aerospace, Defense & Labs": 14, "Prof. & Tech": 13, "Finance & Real Estate": 16, "Healthcare & Ed": 14, "Tourism & Trade": 14},
        "signature": "National laboratories, aerospace engineering, and resource extraction balance mid-level administrative exposure.",
    },
)


# ---- Study 2: October 19, 2026 Alberta Referendum ------------------------------------

ALBERTA_QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "number": 1, "category": "Non-constitutional · Immigration & employment",
        "shortTitle": "Provincial control of immigration & job priority",
        "prompt": "Support Alberta taking increased control over immigration to decrease levels, prioritize economic migration, and give Albertans first priority on new jobs?",
        "forVotes": 1093541, "againstVotes": 907731, "forPct": 54.64, "againstPct": 45.36,
        "outcome": "Passed (non-binding)",
    },
    {
        "number": 2, "category": "Non-constitutional · Social program eligibility",
        "shortTitle": "Restrict provincial programs to citizens/PR/approved status",
        "prompt": "Mandate that only Canadian citizens, permanent residents, and individuals with Alberta-approved status qualify for provincially funded health, education, and social services?",
        "forVotes": 1032950, "againstVotes": 941379, "forPct": 52.32, "againstPct": 47.68,
        "outcome": "Passed (non-binding)",
    },
    {
        "number": 3, "category": "Non-constitutional · Residency waiting period",
        "shortTitle": "12-month residency wait for non-permanent residents",
        "prompt": "Require individuals with non-permanent legal immigration status to reside in Alberta at least 12 months before qualifying for provincially funded social support?",
        "forVotes": 1053247, "againstVotes": 932163, "forPct": 53.05, "againstPct": 46.95,
        "outcome": "Passed (non-binding)",
    },
    {
        "number": 4, "category": "Non-constitutional · Healthcare & school fees",
        "shortTitle": "Healthcare & education fee/premium for non-permanent status",
        "prompt": "Charge a reasonable fee or premium to individuals with non-permanent immigration status for their and their family's use of healthcare and education?",
        "forVotes": 1007376, "againstVotes": 919120, "forPct": 52.29, "againstPct": 47.71,
        "outcome": "Passed (non-binding)",
    },
    {
        "number": 5, "category": "Non-constitutional · Election law",
        "shortTitle": "Proof of citizenship required to vote",
        "prompt": "Require individuals to provide proof of citizenship (passport, birth certificate, or citizenship card) to vote in an Alberta provincial election?",
        "forVotes": 1083647, "againstVotes": 730033, "forPct": 59.75, "againstPct": 40.25,
        "outcome": "Passed (non-binding)",
    },
    {
        "number": 6, "category": "Constitutional amendment · Judiciary",
        "shortTitle": "Provincial selection of King's Bench & Appeal judges",
        "prompt": "Work with willing provinces to amend the Constitution so provincial governments, not Ottawa, select King's Bench and Appeal court justices?",
        "forVotes": 832386, "againstVotes": 918241, "forPct": 47.55, "againstPct": 52.45,
        "outcome": "Rejected",
    },
    {
        "number": 7, "category": "Constitutional amendment · Parliament",
        "shortTitle": "Abolish the unelected federal Senate",
        "prompt": "Work with willing provinces to amend the Canadian Constitution to abolish the unelected federal Senate?",
        "forVotes": 898093, "againstVotes": 926950, "forPct": 49.21, "againstPct": 50.79,
        "outcome": "Rejected",
    },
    {
        "number": 8, "category": "Constitutional amendment · Fiscal federalism",
        "shortTitle": "Opt out of federal social programs with full funding",
        "prompt": "Amend the Constitution to allow provinces to opt out of federal programs in health, education, and social services without losing associated federal funding?",
        "forVotes": 752760, "againstVotes": 855376, "forPct": 46.81, "againstPct": 53.19,
        "outcome": "Rejected",
    },
    {
        "number": 9, "category": "Constitutional amendment · Paramountcy",
        "shortTitle": "Provincial law priority over conflicting federal law",
        "prompt": "Amend the Constitution to give provincial laws in provincial or shared jurisdiction priority over conflicting federal laws?",
        "forVotes": 785995, "againstVotes": 792812, "forPct": 49.78, "againstPct": 50.22,
        "outcome": "Rejected",
    },
    {
        "number": 10, "category": "Independence / Sovereignty process",
        "shortTitle": "Remain in Canada vs. commence binding separation referendum",
        "prompt": "Should Alberta remain a province of Canada (Option 1), or should the Government of Alberta commence the legal process to hold a binding referendum on separating from Canada (Option 2)?",
        "forVotes": 1551868, "againstVotes": 518766, "forPct": 74.95, "againstPct": 25.05,
        "outcome": "Remain won 74.95% – 25.05%",
    },
)

# Demographic breakdown on Question 10 (Abacus Data Oct 7-13, 2026 n=1,021; Research Co. Oct 16-18 n=811 & Oct 19-20 Exit Poll n=601).
ALBERTA_DEMOGRAPHICS: tuple[dict[str, Any], ...] = (
    {"dimension": "Official Count", "group": "All Alberta Ballots (Oct 19)", "remainPct": 75.0, "option2Pct": 25.0, "otherPct": 0.0, "turnoutOrShare": "2,070,634 ballots (99.98% rpt)", "source": "Elections Alberta"},
    {"dimension": "Region", "group": "Edmonton Metro", "remainPct": 77.0, "option2Pct": 17.0, "otherPct": 6.0, "turnoutOrShare": "41% say best days ahead", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "Region", "group": "Calgary Metro", "remainPct": 75.0, "option2Pct": 19.0, "otherPct": 6.0, "turnoutOrShare": "48% say best days ahead", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "Region", "group": "Small Cities & Suburbs", "remainPct": 62.0, "option2Pct": 29.0, "otherPct": 9.0, "turnoutOrShare": "Red Deer / Lethbridge / Airdrie", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "Region", "group": "Rural Alberta", "remainPct": 57.0, "option2Pct": 35.0, "otherPct": 8.0, "turnoutOrShare": "52% say best days ahead", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "Provincial Party", "group": "Alberta NDP Voters", "remainPct": 93.0, "option2Pct": 4.0, "otherPct": 3.0, "turnoutOrShare": "84% strong attachment to Canada", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "Provincial Party", "group": "United Conservative (UCP) Voters", "remainPct": 44.0, "option2Pct": 52.0, "otherPct": 4.0, "turnoutOrShare": "77% of Option 2 pool is UCP", "source": "Abacus Data (Oct 2026)"},
    {"dimension": "2025 Federal Vote", "group": "Federal Liberal Voters", "remainPct": 95.0, "option2Pct": 5.0, "otherPct": 0.0, "turnoutOrShare": "Likely voters", "source": "Research Co. (Oct 18, 2026)"},
    {"dimension": "2025 Federal Vote", "group": "Federal NDP Voters", "remainPct": 82.0, "option2Pct": 18.0, "otherPct": 0.0, "turnoutOrShare": "Likely voters", "source": "Research Co. (Oct 18, 2026)"},
    {"dimension": "2025 Federal Vote", "group": "Federal Conservative Voters", "remainPct": 65.0, "option2Pct": 35.0, "otherPct": 0.0, "turnoutOrShare": "Likely voters", "source": "Research Co. (Oct 18, 2026)"},
    {"dimension": "Age & Turnout", "group": "Ages 18–34 (Under 30 turnout 38%)", "remainPct": 64.0, "option2Pct": 24.0, "otherPct": 12.0, "turnoutOrShare": "21% open to US statehood", "source": "Abacus / Research Co."},
    {"dimension": "Age & Turnout", "group": "Ages 35–54", "remainPct": 67.0, "option2Pct": 25.0, "otherPct": 8.0, "turnoutOrShare": "15% open to US statehood", "source": "Abacus / Research Co."},
    {"dimension": "Age & Turnout", "group": "Ages 55+ (60+ definite turnout 85%)", "remainPct": 73.0, "option2Pct": 23.0, "otherPct": 4.0, "turnoutOrShare": "6% open to US statehood; 71% dual attachment", "source": "Abacus / Research Co."},
    {"dimension": "Voting Channel", "group": "Early Mail-In Ballots (11% of electorate)", "remainPct": 93.0, "option2Pct": 7.0, "otherPct": 0.0, "turnoutOrShare": "84% of Remain voters 100% certain", "source": "Abacus Data (Oct 2026)"},
)

ALBERTA_MOTIVES: dict[str, tuple[tuple[str, int], ...]] = {
    "remain": (
        ("Proud to be Canadian & want Alberta to stay", 39),
        ("Object to the referendum happening at all", 29),
        ("Separation is too economically risky or costly", 16),
        ("Frustrated with Ottawa, but separation goes too far", 13),
        ("Other / unsure", 3),
    ),
    "option2": (
        ("Want Alberta to become an independent country", 32),
        ("Negotiate a better deal within Canada", 23),
        ("Believe Albertans deserve a direct binding vote", 22),
        ("Send Ottawa a message without leaving", 19),
        ("Other / unsure", 4),
    ),
}


# ---- Study 3: Gas Price Collusion & Oligopoly Supergames (ST-06) ---------------------
# Decomposes retail pump price (USD/L) into Wholesale Terminal Gate Price (TGP), Sovereign Tax Wedge
# (excise + carbon + VAT), and Ex-Tax Retail & Distribution Markup Spread, paired with Top-4 firm
# concentration (CR4 %), Herfindahl-Hirschman Index (HHI), and empirical collusion regime findings.
GAS_COUNTRIES: tuple[dict[str, Any], ...] = (
    {
        "code": "DE", "country": "Germany (MTS-K / Algorithmic Oligopoly)",
        "pumpUsdL": 1.98, "wholesaleUsdL": 0.64, "taxUsdL": 1.06, "markupUsdL": 0.28,
        "cr4Pct": 68, "hhi": 2640, "dominantFirms": "Aral (BP), Shell, Jet, Esso, TotalEnergies",
        "regime": "Algorithmic tacit collusion (+28% duopoly margin, Assad et al. 2024 JPE)",
        "lernerExTaxPct": 30.4,
    },
    {
        "code": "UK", "country": "United Kingdom (CMA Supermarket Quadropoly)",
        "pumpUsdL": 1.94, "wholesaleUsdL": 0.63, "taxUsdL": 1.04, "markupUsdL": 0.27,
        "cr4Pct": 64, "hhi": 2480, "dominantFirms": "Asda, Tesco, Sainsbury's, Morrisons + BP/Shell",
        "regime": "Rocket-and-feather margin expansion (+6 p/L CMA 2023–2025 finding)",
        "lernerExTaxPct": 30.0,
    },
    {
        "code": "AU", "country": "Australia (Perth FuelWatch / 4-Pillar Refiners)",
        "pumpUsdL": 1.38, "wholesaleUsdL": 0.62, "taxUsdL": 0.49, "markupUsdL": 0.27,
        "cr4Pct": 74, "hhi": 2890, "dominantFirms": "BP, Ampol/Caltex, Viva (Shell), Coles/7-Eleven",
        "regime": "BP focal-point signaling ended Edgeworth wars (+75% margin, Byrne & de Roos 2019 AER)",
        "lernerExTaxPct": 30.3,
    },
    {
        "code": "CL", "country": "Chile (COPEC–Shell–Petrobras Triopoly)",
        "pumpUsdL": 1.44, "wholesaleUsdL": 0.65, "taxUsdL": 0.53, "markupUsdL": 0.26,
        "cr4Pct": 89, "hhi": 3620, "dominantFirms": "COPEC (~55%), Shell (Enex), Esmax (Petrobras)",
        "regime": "Mandatory price-disclosure portal increased local margins (+7%–11%, Luco 2019 AEJ)",
        "lernerExTaxPct": 28.6,
    },
    {
        "code": "CA", "country": "Canada (Regional Refiner-Marketers & Cartel Clusters)",
        "pumpUsdL": 1.32, "wholesaleUsdL": 0.61, "taxUsdL": 0.46, "markupUsdL": 0.25,
        "cr4Pct": 71, "hhi": 2580, "dominantFirms": "Petro-Canada (Suncor), Esso (Imperial), Shell, Couche-Tard",
        "regime": "Phone-tree & asymmetric pass-through coordination (Clark & Houde 2013/2014)",
        "lernerExTaxPct": 29.1,
    },
    {
        "code": "NL", "country": "Netherlands (Highway Concession Oligopoly)",
        "pumpUsdL": 2.26, "wholesaleUsdL": 0.64, "taxUsdL": 1.37, "markupUsdL": 0.25,
        "cr4Pct": 67, "hhi": 2510, "dominantFirms": "Shell, BP, Esso, TotalEnergies",
        "regime": "High tax wedge + concentrated highway auction leases",
        "lernerExTaxPct": 28.1,
    },
    {
        "code": "DK", "country": "Denmark (Nordic Retail Consolidation)",
        "pumpUsdL": 2.35, "wholesaleUsdL": 0.65, "taxUsdL": 1.46, "markupUsdL": 0.24,
        "cr4Pct": 76, "hhi": 2790, "dominantFirms": "Circle K, OK, Q8, Shell",
        "regime": "Highest OECD pump price (62% sovereign tax + 24 c/L synchronized list price)",
        "lernerExTaxPct": 27.0,
    },
    {
        "code": "IT", "country": "Italy (Integrated Eni–IP–Q8 Network)",
        "pumpUsdL": 2.04, "wholesaleUsdL": 0.64, "taxUsdL": 1.18, "markupUsdL": 0.22,
        "cr4Pct": 62, "hhi": 2290, "dominantFirms": "Eni, IP (Gruppo API), Q8, Tamoil",
        "regime": "Parallel recommended price lists with regional sticky spreads",
        "lernerExTaxPct": 25.6,
    },
    {
        "code": "FR", "country": "France (Hypermarket vs. Highway Split)",
        "pumpUsdL": 1.99, "wholesaleUsdL": 0.64, "taxUsdL": 1.17, "markupUsdL": 0.18,
        "cr4Pct": 54, "hhi": 1920, "dominantFirms": "TotalEnergies, E.Leclerc, Carrefour, Intermarche",
        "regime": "Loss-leader hypermarkets compress urban margins; highway corridors stay oligopolistic",
        "lernerExTaxPct": 22.0,
    },
    {
        "code": "JP", "country": "Japan (ENEOS–Idemitsu–Cosmo Triopoly)",
        "pumpUsdL": 1.24, "wholesaleUsdL": 0.62, "taxUsdL": 0.43, "markupUsdL": 0.19,
        "cr4Pct": 82, "hhi": 3180, "dominantFirms": "ENEOS (~50%), Idemitsu Showa Shell, Cosmo Oil",
        "regime": "3-refiner wholesale consolidation + government subsidy smoothing",
        "lernerExTaxPct": 23.5,
    },
    {
        "code": "US", "country": "United States (Unconcentrated Independent & Big-Box Benchmark)",
        "pumpUsdL": 0.96, "wholesaleUsdL": 0.59, "taxUsdL": 0.15, "markupUsdL": 0.12,
        "cr4Pct": 31, "hhi": 1120, "dominantFirms": "Costco, QuikTrip, Wawa, Sheetz, Buc-ee's, 60%+ independents",
        "regime": "Competitive high-volume discounters break focal-point coordination (12 c/L spread)",
        "lernerExTaxPct": 16.9,
    },
    {
        "code": "DZ", "country": "Algeria (State-Subsidized Producer Benchmark)",
        "pumpUsdL": 0.34, "wholesaleUsdL": 0.22, "taxUsdL": 0.05, "markupUsdL": 0.07,
        "cr4Pct": 95, "hhi": 8200, "dominantFirms": "Naftal (Sonatrach state monopoly)",
        "regime": "Administratively capped domestic fuel price below export parity",
        "lernerExTaxPct": 24.1,
    },
)

# 28-day trajectory for Chart 2: Asymmetric Pass-Through ("Rockets & Feathers" ECM) + Edgeworth Cycle vs. Sticky Collusion
GAS_PASS_THROUGH_DAYS: tuple[dict[str, Any], ...] = (
    {"day": 0, "rocketPassPct": 0.0, "featherPassPct": 0.0, "edgeworthMarginCpl": 8.0, "collusiveMarginCpl": 19.5},
    {"day": 1, "rocketPassPct": 54.0, "featherPassPct": 8.0, "edgeworthMarginCpl": 18.5, "collusiveMarginCpl": 20.0},
    {"day": 2, "rocketPassPct": 82.0, "featherPassPct": 15.0, "edgeworthMarginCpl": 16.2, "collusiveMarginCpl": 20.4},
    {"day": 3, "rocketPassPct": 93.0, "featherPassPct": 22.0, "edgeworthMarginCpl": 13.8, "collusiveMarginCpl": 20.6},
    {"day": 5, "rocketPassPct": 98.0, "featherPassPct": 33.0, "edgeworthMarginCpl": 10.4, "collusiveMarginCpl": 20.8},
    {"day": 7, "rocketPassPct": 100.0, "featherPassPct": 44.0, "edgeworthMarginCpl": 7.2, "collusiveMarginCpl": 21.0},
    {"day": 8, "rocketPassPct": 100.0, "featherPassPct": 49.0, "edgeworthMarginCpl": 18.8, "collusiveMarginCpl": 21.1},
    {"day": 10, "rocketPassPct": 100.0, "featherPassPct": 58.0, "edgeworthMarginCpl": 14.5, "collusiveMarginCpl": 21.2},
    {"day": 12, "rocketPassPct": 100.0, "featherPassPct": 67.0, "edgeworthMarginCpl": 10.9, "collusiveMarginCpl": 21.0},
    {"day": 14, "rocketPassPct": 100.0, "featherPassPct": 74.0, "edgeworthMarginCpl": 7.5, "collusiveMarginCpl": 21.3},
    {"day": 15, "rocketPassPct": 100.0, "featherPassPct": 78.0, "edgeworthMarginCpl": 19.0, "collusiveMarginCpl": 21.4},
    {"day": 18, "rocketPassPct": 100.0, "featherPassPct": 85.0, "edgeworthMarginCpl": 13.2, "collusiveMarginCpl": 21.2},
    {"day": 21, "rocketPassPct": 100.0, "featherPassPct": 91.0, "edgeworthMarginCpl": 7.8, "collusiveMarginCpl": 21.5},
    {"day": 22, "rocketPassPct": 100.0, "featherPassPct": 93.0, "edgeworthMarginCpl": 18.6, "collusiveMarginCpl": 21.5},
    {"day": 25, "rocketPassPct": 100.0, "featherPassPct": 97.0, "edgeworthMarginCpl": 11.8, "collusiveMarginCpl": 21.4},
    {"day": 28, "rocketPassPct": 100.0, "featherPassPct": 100.0, "edgeworthMarginCpl": 8.1, "collusiveMarginCpl": 21.6},
)

# Chart 3 & Inspector: Repeated Bertrand Supergame Incentive-Compatibility across 10 Industries
# delta_star = 1 - 1/N (critical discount factor required for tacit collusion SPNE)
# delta_eff = exp(-r * T_lag) adjusted for price transparency, homogeneity, and multi-market contact
GAS_INDUSTRY_INCENTIVES: tuple[dict[str, Any], ...] = (
    {
        "id": "GAS-AI", "industry": "Retail Gasoline (Local Duopoly + AI Pricing)",
        "firmsN": 2.5, "detectionLagHours": 0.1, "deltaStar": 0.60, "deltaEff": 0.98,
        "slack": 0.38, "equilibrium": "Tacit Collusion SPNE",
        "homogeneity": "Identical (87/91 octane)", "priceVisibility": "Real-time API & street signs",
        "whyMechanism": "AI repricing detects rival cuts in seconds (T -> 0), eliminating deviation windfall and expanding duopoly margins +28% (Assad et al. 2024).",
    },
    {
        "id": "GAS-OLIG", "industry": "Retail Gasoline (4-Firm National Oligopoly)",
        "firmsN": 4.0, "detectionLagHours": 1.0, "deltaStar": 0.75, "deltaEff": 0.95,
        "slack": 0.20, "equilibrium": "Tacit Collusion SPNE",
        "homogeneity": "Identical commodity", "priceVisibility": "Mandatory gov't portals & signs",
        "whyMechanism": "Inelastic aggregate demand (-0.15) maximizes joint collusive profit, while hyper-elastic station switching (-36% per 2 c/L) makes punishment devastating.",
    },
    {
        "id": "CEM", "industry": "Ready-Mix Cement & Aggregates",
        "firmsN": 3.5, "detectionLagHours": 12.0, "deltaStar": 0.71, "deltaEff": 0.89,
        "slack": 0.18, "equilibrium": "Tacit Collusion SPNE",
        "homogeneity": "Standardized ASTM grade", "priceVisibility": "Published zone haulage tariffs",
        "whyMechanism": "High weight-to-value creates tight 50 km geographic oligopolies with high multi-market contact and symmetric kiln capacities.",
    },
    {
        "id": "TEL", "industry": "Canadian / OECD Wireless Telecom (3-Carrier)",
        "firmsN": 3.0, "detectionLagHours": 6.0, "deltaStar": 0.67, "deltaEff": 0.91,
        "slack": 0.24, "equilibrium": "Tacit Collusion SPNE",
        "homogeneity": "Standardized GB tier plans", "priceVisibility": "Public web plan cards",
        "whyMechanism": "Spectrum auction barriers lock N=3; public rate cards allow instant matching of promotional discounts across flanker brands.",
    },
    {
        "id": "GROC", "industry": "Concentrated Supermarket / Bread Retail",
        "firmsN": 4.5, "detectionLagHours": 24.0, "deltaStar": 0.78, "deltaEff": 0.86,
        "slack": 0.08, "equilibrium": "Tacit Collusion SPNE",
        "homogeneity": "Staple SKUs homogeneous", "priceVisibility": "Weekly flyers & shelf scrapers",
        "whyMechanism": "Multi-market contact across thousands of SKUs and shared wholesale suppliers sustains focal-point retail price floors.",
    },
    {
        "id": "AIR", "industry": "Hub-and-Spoke Domestic Airlines",
        "firmsN": 4.0, "detectionLagHours": 2.0, "deltaStar": 0.75, "deltaEff": 0.79,
        "slack": 0.04, "equilibrium": " Knife-Edge / Cyclical",
        "homogeneity": "Perishable seat inventory", "priceVisibility": "GDS / Sabre instant fares",
        "whyMechanism": "Instant fare visibility aids coordination, but perishable empty seats at departure create strong temptations to dump last-minute fares.",
    },
    {
        "id": "GAS-US", "industry": "Retail Gasoline (10+ Firms + Costco/Big-Box)",
        "firmsN": 10.0, "detectionLagHours": 1.0, "deltaStar": 0.90, "deltaEff": 0.81,
        "slack": -0.09, "equilibrium": "Competitive Bertrand",
        "homogeneity": "Identical commodity", "priceVisibility": "Public street signs",
        "whyMechanism": "Maverick big-box clubs optimize store membership/foot-traffic rather than fuel margin, refusing to join focal-point price jumps (delta < delta*).",
    },
    {
        "id": "SAAS", "industry": "Enterprise B2B SaaS & Cloud Contracts",
        "firmsN": 5.0, "detectionLagHours": 720.0, "deltaStar": 0.80, "deltaEff": 0.52,
        "slack": -0.28, "equilibrium": "Competitive / Differentiated",
        "homogeneity": "High feature differentiation", "priceVisibility": "Secret NDA enterprise discounts",
        "whyMechanism": "Secret off-list discounting (Stigler 1964) means rivals cannot tell if a lost deal was due to price undercutting or product fit (large T, low delta).",
    },
    {
        "id": "MFG", "industry": "Custom B2B Precision Manufacturing & Job Shops",
        "firmsN": 8.0, "detectionLagHours": 1440.0, "deltaStar": 0.88, "deltaEff": 0.41,
        "slack": -0.47, "equilibrium": "Competitive Bidding",
        "homogeneity": "Bespoke CAD specifications", "priceVisibility": "Sealed-bid private RFQs",
        "whyMechanism": "Every RFQ has custom engineering specs and sealed bids; no common focal price exists and cheating cannot be monitored.",
    },
    {
        "id": "AERO", "industry": "Commercial Widebody Aircraft Procurement",
        "firmsN": 2.0, "detectionLagHours": 4320.0, "deltaStar": 0.50, "deltaEff": 0.34,
        "slack": -0.16, "equilibrium": "Aggressive Bidding Wars",
        "homogeneity": "High switching costs", "priceVisibility": "Confidential multi-year concessions",
        "whyMechanism": "Even with N=2, orders are huge, lumpy, and infrequent ($10B fleet deals): a single deviation locks in 20 years of fleet aftermarket revenue.",
    },
)

PANDAS_GAS_SCRIPT = '''"""Reproducible Pandas analysis for ST-06: Gas Price Collusion & Oligopoly Supergames."""
import numpy as np
import pandas as pd

# 1. Load the cross-country pump price decomposition & concentration table
countries = pd.read_csv("studies-gas-countries.csv")
countries["ex_tax_price_usd_l"] = countries["wholesaleUsdL"] + countries["markupUsdL"]
countries["tax_share_pct"] = (countries["taxUsdL"] / countries["pumpUsdL"] * 100).round(1)
countries["lerner_ex_tax_pct"] = (countries["markupUsdL"] / countries["ex_tax_price_usd_l"] * 100).round(1)
countries["excess_markup_vs_us_cpl"] = ((countries["markupUsdL"] - 0.12) * 100).round(1)

# Exclude state-capped producer monopoly (DZ) when estimating market oligopoly HHI gradient
market_oecd = countries[countries["code"] != "DZ"].copy()
corr_cr4 = market_oecd["cr4Pct"].corr(market_oecd["markupUsdL"])
corr_hhi = market_oecd["hhi"].corr(market_oecd["markupUsdL"])
slope_cpl_per_10pct_cr4 = np.polyfit(market_oecd["cr4Pct"], market_oecd["markupUsdL"] * 100, 1)[0] * 10

print("=== Cross-Country Oligopoly Markup Summary (Pandas) ===")
print(market_oecd[["code", "pumpUsdL", "wholesaleUsdL", "taxUsdL", "markupUsdL", "cr4Pct", "hhi", "lerner_ex_tax_pct"]])
print(f"Correlation(CR4, Ex-Tax Markup): r = {corr_cr4:.3f} | Correlation(HHI, Markup): r = {corr_hhi:.3f}")
print(f"OLS Gradient: +{slope_cpl_per_10pct_cr4:.2f} cents/L markup per +10 percentage points in CR4 concentration\\n")

# 2. Asymmetric Pass-Through ("Rockets & Feathers" Error Correction Model)
pt = pd.read_csv("studies-gas-pass-through.csv")
rocket_half_life = pt.loc[pt["rocketPassPct"] >= 50, "day"].min()
feather_half_life = pt.loc[pt["featherPassPct"] >= 50, "day"].min()
cumulative_wedge_cpl_days = np.trapezoid(pt["rocketPassPct"] - pt["featherPassPct"], pt["day"]) / 10.0
print(f"Rocket 50% pass-through lag: {rocket_half_life} day(s) vs. Feather 50% decay lag: {feather_half_life} days")
print(f"Asymmetric tacit rent per 10 c/L wholesale cycle: +{cumulative_wedge_cpl_days:.1f} cent-days/L\\n")

# 3. Repeated Bertrand Supergame Incentive-Compatibility (delta >= delta* = 1 - 1/N)
ind = pd.read_csv("studies-gas-industries.csv")
ind["collusive_spne"] = ind["deltaEff"] >= ind["deltaStar"]
print("=== Supergame Incentive-Compatibility (delta_eff vs. delta_star) ===")
print(ind[["id", "industry", "firmsN", "deltaStar", "deltaEff", "slack", "collusive_spne"]])
'''


# ---- Study 4: ST-05 Sodium Battery Technology vs. Lithium-Ion (Electrochemistry) -----
SODIUM_CHEMISTRIES: tuple[dict[str, Any], ...] = (
    {
        "id": "SIB-PBW", "chemistry": "Na-Ion Prussian White (CATL Gen-2 / Natron)",
        "ion": "Na+ (r = 1.02 Å)", "cathode": "Na2Fe[Fe(CN)6] (Prussian White)", "anode": "Hard Carbon (Al foil)",
        "gravWhKg": 165, "volWhL": 340, "cellCostUsdKwh": 44, "cycleLife": 8000,
        "tempRetMinus20Pct": 92, "crustalPpm": 23600, "zeroVoltSafe": "Yes (Al collector both sides)",
    },
    {
        "id": "SIB-NFM", "chemistry": "Na-Ion Layered Oxide (HiNa NaNi1/3Fe1/3Mn1/3O2)",
        "ion": "Na+ (r = 1.02 Å)", "cathode": "O3/P2 Layered Transition Metal Oxide", "anode": "Hard Carbon (Al foil)",
        "gravWhKg": 155, "volWhL": 330, "cellCostUsdKwh": 49, "cycleLife": 4500,
        "tempRetMinus20Pct": 88, "crustalPpm": 23600, "zeroVoltSafe": "Yes (0 V short-circuit transport)",
    },
    {
        "id": "SIB-POLY", "chemistry": "Na-Ion Polyanionic NFPP (Na4Fe3(PO4)2P2O7 Grid)",
        "ion": "Na+ (r = 1.02 Å)", "cathode": "Polyanionic Iron Pyrophosphate", "anode": "Hard Carbon (Al foil)",
        "gravWhKg": 135, "volWhL": 295, "cellCostUsdKwh": 41, "cycleLife": 10000,
        "tempRetMinus20Pct": 90, "crustalPpm": 23600, "zeroVoltSafe": "Yes (ultra-stable 3D framework)",
    },
    {
        "id": "LIB-LFP", "chemistry": "Li-Ion LFP (LiFePO4 Prismatic BESS Benchmark)",
        "ion": "Li+ (r = 0.76 Å)", "cathode": "Olivine LiFePO4", "anode": "Graphite (Cu foil required)",
        "gravWhKg": 190, "volWhL": 410, "cellCostUsdKwh": 68, "cycleLife": 6500,
        "tempRetMinus20Pct": 64, "crustalPpm": 20, "zeroVoltSafe": "No (Cu dissolution < 1.5 V)",
    },
    {
        "id": "LIB-LMFP", "chemistry": "Li-Ion LMFP (Manganese-Doped LiMn0.6Fe0.4PO4)",
        "ion": "Li+ (r = 0.76 Å)", "cathode": "Olivine LMFP (4.0 V plateau)", "anode": "Graphite / SiOx (Cu foil)",
        "gravWhKg": 225, "volWhL": 490, "cellCostUsdKwh": 74, "cycleLife": 4500,
        "tempRetMinus20Pct": 68, "crustalPpm": 20, "zeroVoltSafe": "No (Cu collector corrosion)",
    },
    {
        "id": "LIB-NMC811", "chemistry": "Li-Ion NMC-811 (High-Nickel Long-Range EV)",
        "ion": "Li+ (r = 0.76 Å)", "cathode": "LiNi0.8Mn0.1Co0.1O2", "anode": "Graphite + Si (Cu foil)",
        "gravWhKg": 275, "volWhL": 670, "cellCostUsdKwh": 98, "cycleLife": 2200,
        "tempRetMinus20Pct": 72, "crustalPpm": 20, "zeroVoltSafe": "No (thermal runaway O2 release)",
    },
)

SODIUM_TEMP_CURVE: tuple[dict[str, Any], ...] = (
    {"tempC": -40, "sibRetentionPct": 76.0, "lfpRetentionPct": 28.0, "nmcRetentionPct": 41.0},
    {"tempC": -30, "sibRetentionPct": 85.0, "lfpRetentionPct": 45.0, "nmcRetentionPct": 56.0},
    {"tempC": -20, "sibRetentionPct": 92.0, "lfpRetentionPct": 64.0, "nmcRetentionPct": 72.0},
    {"tempC": -10, "sibRetentionPct": 96.0, "lfpRetentionPct": 79.0, "nmcRetentionPct": 85.0},
    {"tempC": 0,   "sibRetentionPct": 98.5, "lfpRetentionPct": 91.0, "nmcRetentionPct": 94.0},
    {"tempC": 25,  "sibRetentionPct": 100.0, "lfpRetentionPct": 100.0, "nmcRetentionPct": 100.0},
    {"tempC": 45,  "sibRetentionPct": 99.0, "lfpRetentionPct": 98.0, "nmcRetentionPct": 95.0},
)

PANDAS_SODIUM_SCRIPT = '''"""Reproducible Pandas analysis for ST-05: Sodium Battery Technology vs. Lithium-Ion."""
import numpy as np
import pandas as pd

# 1. Periodic Table & Faraday Law Fundamental Ratios
F = 96485.3321  # C/mol
M_Li, M_Na = 6.94, 22.99  # g/mol
r_Li, r_Na = 0.76, 1.02   # Shannon 6-coord octahedral ionic radius (Angstroms)
E0_Li, E0_Na = -3.04, -2.71  # V vs SHE

q_Li = F / (3.6 * M_Li)  # 3861 mAh/g
q_Na = F / (3.6 * M_Na)  # 1166 mAh/g
vol_ratio = (r_Na / r_Li) ** 3

print(f"Theoretical metal specific capacity: Li = {q_Li:.0f} mAh/g vs. Na = {q_Na:.0f} mAh/g")
print(f"Shannon ionic volume expansion (Na+/Li+)^3: {vol_ratio:.2f}x | Potential shift: +{E0_Na - E0_Li:.2f} V")

# 2. Load 6-chemistry benchmark table & compute Levelized Cost of Storage (LCOS $/MWh-cycle)
df = pd.read_csv("studies-sodium-chemistries.csv")
df["cost_per_1000_cycles_usd_kwh"] = (df["cellCostUsdKwh"] / (df["cycleLife"] / 1000.0)).round(2)
df["winter_effective_wh_kg_minus20C"] = (df["gravWhKg"] * df["tempRetMinus20Pct"] / 100.0).round(1)

print("\\n=== Sodium-Ion vs. Lithium-Ion Chemistry Matrix (Pandas) ===")
print(df[["id", "gravWhKg", "cellCostUsdKwh", "cycleLife", "tempRetMinus20Pct", "cost_per_1000_cycles_usd_kwh", "winter_effective_wh_kg_minus20C"]])
'''


# ---- Study 5: ST-08 AI Cost & Compute Economics (Emerging Industries / AI) -----
AI_COST_MODELS: tuple[dict[str, Any], ...] = (
    {
        "id": "GPT4-2023", "model": "GPT-4 Original (Mar 2023 Baseline)",
        "architecture": "Early MoE (~1.76T total)", "inputUsdM": 30.00, "outputUsdM": 60.00,
        "blendedUsdM": 36.00, "trainFlopsE24": 21.0, "trainCapexUsdM": 78.0,
        "energyWhQuery": 2.90, "benchmarkPct": 68.0,
        "regime": "2023 Frontier Reference (1.0× cost baseline)",
    },
    {
        "id": "CLAUDE-OPUS", "model": "Claude 4.5 Opus (Dense Frontier)",
        "architecture": "Frontier High-Capacity Dense", "inputUsdM": 15.00, "outputUsdM": 75.00,
        "blendedUsdM": 27.00, "trainFlopsE24": 45.0, "trainCapexUsdM": 145.0,
        "energyWhQuery": 2.40, "benchmarkPct": 86.4,
        "regime": "High-Capex Deep Synthesis Tier",
    },
    {
        "id": "GPT4O-STD", "model": "GPT-4o (Omni Production Frontier)",
        "architecture": "Multimodal Sparse MoE", "inputUsdM": 2.50, "outputUsdM": 10.00,
        "blendedUsdM": 4.38, "trainFlopsE24": 32.0, "trainCapexUsdM": 95.0,
        "energyWhQuery": 0.95, "benchmarkPct": 81.5,
        "regime": "8.2× cheaper than 2023 GPT-4 (+13.5 pp score)",
    },
    {
        "id": "ARGON-HIGH", "model": "Gemini 4 Argon (High Thinking)",
        "architecture": "Sparse MoE + Test-Time Reasoning", "inputUsdM": 1.25, "outputUsdM": 10.00,
        "blendedUsdM": 3.50, "trainFlopsE24": 52.0, "trainCapexUsdM": 130.0,
        "energyWhQuery": 0.85, "benchmarkPct": 89.2,
        "regime": "10.3× cheaper than 2023 GPT-4 (+21.2 pp score)",
    },
    {
        "id": "LLAMA4-405B", "model": "Llama-4 405B FP8 (Open-Weight Cloud)",
        "architecture": "405B Dense FP8 Quantized", "inputUsdM": 0.80, "outputUsdM": 1.20,
        "blendedUsdM": 0.90, "trainFlopsE24": 38.0, "trainCapexUsdM": 64.0,
        "energyWhQuery": 0.62, "benchmarkPct": 82.1,
        "regime": "40× cheaper via open-weight inference competition",
    },
    {
        "id": "DEEPSEEK-R1", "model": "DeepSeek-V3 / R1 (MLA + Aux-Free MoE)",
        "architecture": "671B Total / 37B Active MoE + MLA", "inputUsdM": 0.14, "outputUsdM": 2.19,
        "blendedUsdM": 0.48, "trainFlopsE24": 2.79, "trainCapexUsdM": 5.58,
        "energyWhQuery": 0.38, "benchmarkPct": 87.5,
        "regime": "75× cheaper · Multi-head Latent Attention cuts KV-cache 75%",
    },
    {
        "id": "FLASH-38", "model": "Gemini 3.8 Flash (High-Throughput)",
        "architecture": "Distilled Hardware-Aware MoE", "inputUsdM": 0.075, "outputUsdM": 0.30,
        "blendedUsdM": 0.18, "trainFlopsE24": 9.5, "trainCapexUsdM": 22.0,
        "energyWhQuery": 0.14, "benchmarkPct": 79.8,
        "regime": "200× cheaper than 2023 GPT-4 at higher accuracy",
    },
    {
        "id": "LOCAL-Q4", "model": "Local Quantized 32B–70B (4-Bit Consumer GPU)",
        "architecture": "32B Q4_K_M Local VRAM", "inputUsdM": 0.03, "outputUsdM": 0.06,
        "blendedUsdM": 0.04, "trainFlopsE24": 4.2, "trainCapexUsdM": 8.0,
        "energyWhQuery": 0.09, "benchmarkPct": 76.4,
        "regime": "900× cheaper marginal electricity · zero API rent",
    },
)

AI_COST_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "id": "INF-DEFL", "layer": "Algorithmic & Hardware Inference Deflation",
        "metricVal": "−68%/yr (10× / 2 yrs)", "costSharePct": 88, "bottleneckScore": 84,
        "deflationRate": "3.2×/yr", "hardwareDriver": "MoE Sparsity + FP8/INT4 + MLA KV-Cache",
        "mechanism": "Active parameter sparsity (37B active of 671B), Multi-head Latent Attention (MLA), and FP8 quantization compress memory bandwidth per token by 10× every 18–24 months.",
    },
    {
        "id": "SILICON", "layer": "Accelerator Silicon & HBM3e Memory Wall",
        "metricVal": "54% of server capex", "costSharePct": 54, "bottleneckScore": 94,
        "deflationRate": "1.4×/yr", "hardwareDriver": "HBM3e Stacks + CoWoS Packaging",
        "mechanism": "Autoregressive token decoding is memory-bandwidth bound (bytes moved per FLOP), making HBM3e wafer allocation and NVIDIA/TPU interconnect margins the dominant hardware bottleneck.",
    },
    {
        "id": "THINKING", "layer": "Test-Time Reasoning & Jevons Token Multiplier",
        "metricVal": "5×–15× tokens/query", "costSharePct": 64, "bottleneckScore": 78,
        "deflationRate": "1.8×/yr", "hardwareDriver": "Chain-of-Thought / RL Search Trees",
        "mechanism": "As unit token prices fall 99%, reasoning models (Gemini 4 Argon, o3, R1) spend 5,000–32,000 internal thinking tokens per complex task—confirming Jevons Paradox in total compute spend.",
    },
    {
        "id": "CAPEX", "layer": "Frontier Pre-Training Cluster Capex",
        "metricVal": "$100M–$1B+ / run", "costSharePct": 72, "bottleneckScore": 91,
        "deflationRate": "0.7×/yr (Rising)", "hardwareDriver": "100,000+ Accelerator Fabrics",
        "mechanism": "While marginal inference approaches electricity cost, frontier pre-training cluster capex grows ~2.4× per generation, concentrating base foundation model ownership into 4–6 firms.",
    },
    {
        "id": "ENERGY", "layer": "Data-Center Baseload Power & Thermal Cooling",
        "metricVal": "0.14–2.90 Wh/query", "costSharePct": 24, "bottleneckScore": 89,
        "deflationRate": "1.2×/yr", "hardwareDriver": "Direct-to-Chip Liquid Cooling (PUE 1.12)",
        "mechanism": "Single queries consume 0.14–0.95 Wh (less than 10 seconds of an LED bulb), but aggregate gigawatt data centers face 4-to-7 year transformer and grid-interconnect queues.",
    },
    {
        "id": "ROUTING", "layer": "Cascade Routing & Prompt Prefix Caching",
        "metricVal": "78% TCO reduction", "costSharePct": 42, "bottleneckScore": 65,
        "deflationRate": "2.6×/yr", "hardwareDriver": "KV-Cache Prefix Reuse + Flash Cascade",
        "mechanism": "Routing 85% of routine tasks to distilled Flash/Mini models ($0.18/1M) and reserving High-Thinking Argon ($3.50/1M) for hard proofs cuts enterprise billings by 78% with zero accuracy loss.",
    },
)

PANDAS_AI_COST_SCRIPT = '''"""Reproducible Pandas analysis for ST-08: AI Compute, Token Inference & Training Cost Economics."""
import numpy as np
import pandas as pd

# 1. Load Frontier vs. Open-Weight AI Model Cost & Capability Benchmark Table
df = pd.read_csv("studies-ai-cost-models.csv")
baseline_cost = df.loc[df["id"] == "GPT4-2023", "blendedUsdM"].iloc[0]
df["deflation_multiple_vs_2023"] = (baseline_cost / df["blendedUsdM"]).round(1)
df["accuracy_points_per_dollar"] = (df["benchmarkPct"] / df["blendedUsdM"]).round(2)
df["queries_per_kwh"] = (1000.0 / df["energyWhQuery"]).round(0)

print("=== ST-08: AI Inference Deflation & Training Capex Matrix (Pandas) ===")
print(df[["id", "blendedUsdM", "deflation_multiple_vs_2023", "trainCapexUsdM", "energyWhQuery", "benchmarkPct", "accuracy_points_per_dollar"]])

# 2. Enterprise Cascade Routing Simulation (100M monthly tokens: 85% Flash + 15% Argon High)
flash_cost = df.loc[df["id"] == "FLASH-38", "blendedUsdM"].iloc[0]
argon_cost = df.loc[df["id"] == "ARGON-HIGH", "blendedUsdM"].iloc[0]
all_argon_monthly = 100.0 * argon_cost
cascade_monthly = 100.0 * (0.85 * flash_cost + 0.15 * argon_cost)
savings_pct = (1.0 - cascade_monthly / all_argon_monthly) * 100.0
print(f"\\n100M Token/Month Enterprise Workload: All-Frontier = ${all_argon_monthly:,.2f} vs. Cascade = ${cascade_monthly:,.2f} ({savings_pct:.1f}% savings)")
'''


# ---- Study 6: ST-09 Taxes on Generations Over Time Periods (Macroeconomics / Fiscal Policy) -----
GEN_TAX_COHORTS: tuple[dict[str, Any], ...] = (
    {
        "id": "GENZ-2025", "cohort": "Gen Z (Ages 15–28, 2025)",
        "era": "2025 Current", "totalTaxCad": 8640, "totalRewardCad": 11920,
        "netIncidenceCad": 3280, "rewardRatio": 1.38,
        "incomePayrollCad": 4120, "salesTaxCad": 1980, "propertyTaxCad": 410,
        "fuelCarbonCad": 340, "alcoholTaxCad": 142, "vapeTaxCad": 168,
        "commuteMins": 21.2, "autoSharePct": 61.5, "vapePrevPct": 19.7, "homeownerPct": 18.4,
        "driverNote": "Net Reward +$3,280/cap; peak vaping excise ($168/cap, 64.2% national share) & education STiK ($6,850/cap)",
    },
    {
        "id": "MILL-2025", "cohort": "Millennials (Ages 29–44, 2025)",
        "era": "2025 Current", "totalTaxCad": 26890, "totalRewardCad": 13450,
        "netIncidenceCad": -13440, "rewardRatio": 0.50,
        "incomePayrollCad": 15420, "salesTaxCad": 3410, "propertyTaxCad": 2120,
        "fuelCarbonCad": 780, "alcoholTaxCad": 248, "vapeTaxCad": 74,
        "commuteMins": 28.4, "autoSharePct": 81.6, "vapePrevPct": 9.4, "homeownerPct": 52.6,
        "driverNote": "Net Burden −$13,440/cap; longest exurban commute (28.4 min, $780 fuel/CO2 tax) + 11.9% CPP payroll rate",
    },
    {
        "id": "GENX-2025", "cohort": "Gen X (Ages 45–60, 2025)",
        "era": "2025 Current", "totalTaxCad": 31420, "totalRewardCad": 12840,
        "netIncidenceCad": -18580, "rewardRatio": 0.41,
        "incomePayrollCad": 18350, "salesTaxCad": 3890, "propertyTaxCad": 2490,
        "fuelCarbonCad": 815, "alcoholTaxCad": 245, "vapeTaxCad": 32,
        "commuteMins": 27.6, "autoSharePct": 84.8, "vapePrevPct": 4.2, "homeownerPct": 71.2,
        "driverNote": "Peak Net Burden −$18,580/cap; highest income ($18,350), sales ($3,890) & fuel/carbon tax ($815/cap)",
    },
    {
        "id": "BOOM-2025", "cohort": "Baby Boomers (Ages 61–79, 2025)",
        "era": "2025 Current", "totalTaxCad": 14180, "totalRewardCad": 27510,
        "netIncidenceCad": 13330, "rewardRatio": 1.94,
        "incomePayrollCad": 7650, "salesTaxCad": 2920, "propertyTaxCad": 2640,
        "fuelCarbonCad": 410, "alcoholTaxCad": 165, "vapeTaxCad": 8,
        "commuteMins": 19.8, "autoSharePct": 22.0, "vapePrevPct": 1.4, "homeownerPct": 76.0,
        "driverNote": "Net Reward +$13,330/cap; peak property tax ($2,640/cap) offset by $13,120 OAS/CPP & $14,042 CIHI health STiK",
    },
    {
        "id": "SILENT-2025", "cohort": "Silent Gen (Ages 80+, 2025)",
        "era": "2025 Current", "totalTaxCad": 9120, "totalRewardCad": 33560,
        "netIncidenceCad": 24440, "rewardRatio": 3.68,
        "incomePayrollCad": 4680, "salesTaxCad": 1850, "propertyTaxCad": 2180,
        "fuelCarbonCad": 185, "alcoholTaxCad": 72, "vapeTaxCad": 2,
        "commuteMins": 4.2, "autoSharePct": 3.0, "vapePrevPct": 0.4, "homeownerPct": 68.5,
        "driverNote": "Net Reward +$24,440/cap; $24,800/cap CIHI healthcare STiK + $8,760 OAS/GIS pensions",
    },
    {
        "id": "BOOM-1990", "cohort": "Boomers at Ages 26–44 (1990 Baseline)",
        "era": "1990 Historical", "totalTaxCad": 19850, "totalRewardCad": 13040,
        "netIncidenceCad": -6810, "rewardRatio": 0.66,
        "incomePayrollCad": 11840, "salesTaxCad": 2890, "propertyTaxCad": 1680,
        "fuelCarbonCad": 460, "alcoholTaxCad": 295, "vapeTaxCad": 0,
        "commuteMins": 21.8, "autoSharePct": 79.2, "vapePrevPct": 0.0, "homeownerPct": 64.0,
        "driverNote": "1990 Real 2024$: 4.4% CPP rate, 5.8:1 worker support ratio, $0 carbon/vape tax, 21.8 min commute",
    },
    {
        "id": "GENX-2005", "cohort": "Gen X at Ages 25–40 (2005 Baseline)",
        "era": "2005 Historical", "totalTaxCad": 23410, "totalRewardCad": 12180,
        "netIncidenceCad": -11230, "rewardRatio": 0.52,
        "incomePayrollCad": 13680, "salesTaxCad": 3250, "propertyTaxCad": 1890,
        "fuelCarbonCad": 540, "alcoholTaxCad": 265, "vapeTaxCad": 0,
        "commuteMins": 25.1, "autoSharePct": 81.0, "vapePrevPct": 0.0, "homeownerPct": 58.5,
        "driverNote": "2005 Real 2024$: 7% GST era, 9.9% CPP reform rate, 25.1 min suburban commute, moderate property tax",
    },
    {
        "id": "SILENT-1990", "cohort": "Silent Gen at Ages 45–60 (1990 Baseline)",
        "era": "1990 Historical", "totalTaxCad": 24680, "totalRewardCad": 11420,
        "netIncidenceCad": -13260, "rewardRatio": 0.46,
        "incomePayrollCad": 14920, "salesTaxCad": 3140, "propertyTaxCad": 1950,
        "fuelCarbonCad": 490, "alcoholTaxCad": 310, "vapeTaxCad": 0,
        "commuteMins": 20.4, "autoSharePct": 82.5, "vapePrevPct": 0.0, "homeownerPct": 74.0,
        "driverNote": "1990 Real 2024$: Peak manufacturing/income tax era before 1991 GST & 1997 CPP payroll expansion",
    },
)

PANDAS_GEN_TAX_SCRIPT = '''"""Reproducible Pandas analysis for ST-09: Taxes on Generations Over Time Periods (Real 2024 CAD/Capita)."""
import numpy as np
import pandas as pd

# 1. Load Population-Normalized Generational Fiscal Accounting Table (StatCan DHEA, SHS, Census, CTNS & CIHI)
df = pd.read_csv("studies-gen-tax-cohorts.csv")
df["net_fiscal_reward_cad"] = df["totalRewardCad"] - df["totalTaxCad"]
df["reward_to_tax_ratio"] = (df["totalRewardCad"] / df["totalTaxCad"]).round(2)
df["indirect_excise_share_pct"] = (
    (df["salesTaxCad"] + df["propertyTaxCad"] + df["fuelCarbonCad"] + df["alcoholTaxCad"] + df["vapeTaxCad"])
    / df["totalTaxCad"] * 100
).round(1)

print("=== ST-09: Population-Normalized Generational Tax Burden vs. Fiscal Rewards (2024 CAD/Capita) ===")
print(df[["id", "totalTaxCad", "totalRewardCad", "net_fiscal_reward_cad", "reward_to_tax_ratio", "commuteMins", "fuelCarbonCad", "vapeTaxCad", "propertyTaxCad"]])

# 2. Age-Matched Life-Cycle Comparison: Millennials (2025, Ages 29-44) vs. Boomers (1990, Ages 26-44)
mill_2025 = df.loc[df["id"] == "MILL-2025"].iloc[0]
boom_1990 = df.loc[df["id"] == "BOOM-1990"].iloc[0]
burden_delta = mill_2025["totalTaxCad"] - boom_1990["totalTaxCad"]
commute_delta = mill_2025["commuteMins"] - boom_1990["commuteMins"]
print(f"\\nYoung-Adult Life-Cycle Shift (2025 Millennials vs. 1990 Boomers at Same Age):")
print(f"  Real Gross Tax Delta: +${burden_delta:,.0f}/capita (+{burden_delta / boom_1990['totalTaxCad'] * 100:.1f}%)")
print(f"  One-Way Commute Delta: +{commute_delta:.1f} mins ({mill_2025['commuteMins']}m vs {boom_1990['commuteMins']}m) -> Fuel/Carbon Tax ${mill_2025['fuelCarbonCad']}/cap")
'''


def load_studies() -> dict[str, Any]:
    """Return validated study datasets for Macroeconomics AI Iceberg, Alberta 2026 Referendum, and Gas Price Collusion."""
    for sector in INDUSTRY_SECTORS:
        total_roles = sum(sector["roles"].values())
        if total_roles != 100:
            raise ValueError(f"Industry {sector['name']} role shares sum to {total_roles}, expected 100")

    return {
        "macro": {
            "title": "The AI Iceberg Index: Sector & Role Exposure Across North America",
            "route": MACRO_STUDY_ROUTE,
            "paperRoute": MACRO_PAPER_ROUTE,
            "summary": {
                "workersMillions": 151,
                "occupations": 923,
                "skills": 32000,
                "surfacePct": 2.2,
                "surfaceBillions": 211,
                "submergedPct": 11.7,
                "submergedBillions": 1200,
                "combinedPct": 13.9,
                "submergedToSurfaceRatio": round(11.7 / 2.2, 2),
                "industries": len(INDUSTRY_SECTORS),
                "regions": len(REGIONAL_ECONOMIES),
            },
            "roleFamilies": [
                {"key": key, "label": label, "surfacePct": surf, "submergedPct": sub}
                for key, label, surf, sub in ROLE_FAMILIES
            ],
            "industries": list(INDUSTRY_SECTORS),
            "regions": list(REGIONAL_ECONOMIES),
        },
        "alberta": {
            "title": "2026 Alberta Referendum: All 10 Questions & Demographic Vote Anatomy",
            "route": ALBERTA_STUDY_ROUTE,
            "paperRoute": ALBERTA_PAPER_ROUTE,
            "date": "2026-10-19",
            "summary": {
                "questions": 10,
                "nonConstitutionalPassed": 5,
                "constitutionalPassed": 0,
                "q10RemainVotes": 1551868,
                "q10Option2Votes": 518766,
                "q10TotalVotes": 2070634,
                "q10RemainPct": 74.95,
                "q10Option2Pct": 25.05,
                "directIndependencePct": 18.0,
            },
            "questions": list(ALBERTA_QUESTIONS),
            "demographics": list(ALBERTA_DEMOGRAPHICS),
            "motives": {k: [{"reason": r, "pct": p} for r, p in v] for k, v in ALBERTA_MOTIVES.items()},
        },
        "gas": {
            "id": "ST-06",
            "title": "Gas Price Collusion: Cross-Country Markups, Rockets & Feathers, and Repeated Oligopoly Supergames",
            "route": GAS_STUDY_ROUTE,
            "tabRoute": GAS_TAB_ROUTE,
            "paperRoute": GAS_PAPER_ROUTE,
            "date": "2026-10-25",
            "model": "Gemini 4 Argon (gemini-4-argon · High Thinking + Google Search + Pandas)",
            "summary": {
                "countriesAnalyzed": len(GAS_COUNTRIES),
                "industriesAnalyzed": len(GAS_INDUSTRY_INCENTIVES),
                "oligopolyMarkupCpl": "24–28 c/L",
                "competitiveMarkupCpl": "12 c/L",
                "aiDuopolyMarginBoostPct": 28,
                "focalSignalingBoostPct": 75,
                "rocketHalfLifeDays": 1,
                "featherHalfLifeDays": 9,
                "stationSwitchElasticityPct": 36,
                "cr4MarkupCorrelation": 0.91,
            },
            "countries": list(GAS_COUNTRIES),
            "passThrough": list(GAS_PASS_THROUGH_DAYS),
            "industries": list(GAS_INDUSTRY_INCENTIVES),
            "pandasScript": PANDAS_GAS_SCRIPT,
        },
        "sodium": {
            "id": "ST-05",
            "title": "Sodium Battery Technology: Periodic Table Electrochemistry, Hard Carbon Intercalation & Grid Blackout Resilience",
            "route": SODIUM_STUDY_ROUTE,
            "tabRoute": SODIUM_TAB_ROUTE,
            "paperRoute": SODIUM_PAPER_ROUTE,
            "date": "2026-10-25",
            "model": "Gemini 4 Argon (gemini-4-argon · High Thinking + Google Search + Pandas)",
            "summary": {
                "crustalAbundanceRatio": "1,180×",
                "naPpm": 23600,
                "liPpm": 20,
                "ionicRadiusNa": 1.02,
                "ionicRadiusLi": 0.76,
                "ionicVolumeRatio": 2.42,
                "sibCellCostUsdKwh": "41–49 $/kWh",
                "lfpCellCostUsdKwh": "68 $/kWh",
                "minus20CRetentionSibPct": 92,
                "minus20CRetentionLfpPct": 64,
                "maxCycleLife": "10,000 cycles",
            },
            "chemistries": list(SODIUM_CHEMISTRIES),
            "tempCurve": list(SODIUM_TEMP_CURVE),
            "pandasScript": PANDAS_SODIUM_SCRIPT,
        },
        "ai_cost": {
            "id": "ST-08",
            "title": "AI Cost & Compute Economics: Token Inference Deflation, Training Capex & Test-Time Reasoning Scaling",
            "route": AI_COST_STUDY_ROUTE,
            "tabRoute": AI_COST_TAB_ROUTE,
            "paperRoute": AI_COST_PAPER_ROUTE,
            "date": "2026-10-26",
            "model": "Gemini 4 Argon (gemini-4-argon · High Thinking + Google Search + Pandas)",
            "summary": {
                "inferenceDeflationMultiple": "200×",
                "gpt4BaselineUsdM": "$36.00 / 1M",
                "argonBlendedUsdM": "$3.50 / 1M",
                "flashBlendedUsdM": "$0.18 / 1M",
                "deepseekBlendedUsdM": "$0.48 / 1M",
                "energyPerQueryWh": "0.14–0.95 Wh",
                "cascadeSavingsPct": 80.6,
                "modelsAnalyzed": len(AI_COST_MODELS),
                "layersAnalyzed": len(AI_COST_LAYERS),
            },
            "models": list(AI_COST_MODELS),
            "layers": list(AI_COST_LAYERS),
            "pandasScript": PANDAS_AI_COST_SCRIPT,
        },
        "gen_tax": {
            "id": "ST-09",
            "title": "Taxes on Generations Over Time Periods: Real Tax Burden, Fiscal Rewards, Commute Carbon Incidence & Excise Asymmetry",
            "route": GEN_TAX_STUDY_ROUTE,
            "tabRoute": GEN_TAX_TAB_ROUTE,
            "paperRoute": GEN_TAX_PAPER_ROUTE,
            "date": "2026-10-27",
            "model": "Gemini 4 Argon (gemini-4-argon · High Thinking + Google Search + Pandas · 20,079 tokens)",
            "summary": {
                "peakTaxCohort": "$31,420 / yr",
                "seniorRewardRatio": "2.31× Taxes",
                "millennialCommuteTax": "28.4 mins / $780",
                "genZVapeShare": "64.2% ($168/cap)",
                "cohortsAnalyzed": len(GEN_TAX_COHORTS),
            },
            "cohorts": list(GEN_TAX_COHORTS),
            "pandasScript": PANDAS_GEN_TAX_SCRIPT,
        },
    }


def studies_rows(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Flatten study tables for CSV downloads."""
    macro, alberta, gas, sodium, ai_cost, gen_tax = (
        data["macro"], data["alberta"], data["gas"], data["sodium"], data["ai_cost"], data["gen_tax"]
    )
    return {
        "macro-industries": [
            {
                "naics": s["code"], "industry": s["name"], "employmentSharePct": s["employmentShare"],
                "gdpSharePct": s["gdpShare"], "medianWageUsd": s["medianWage"],
                "surfaceAiPct": s["surfacePct"], "submergedAiPct": s["submergedPct"],
                "combinedAiPct": round(s["surfacePct"] + s["submergedPct"], 1),
                **{f"role_{k}_pct": v for k, v in s["roles"].items()},
            }
            for s in macro["industries"]
        ],
        "macro-regions": [
            {
                "id": r["id"], "name": r["name"], "country": r["country"],
                "gdpBillionsUsd": r["gdpBillions"], "workersMillions": r["workersMillions"],
                "surfaceAiPct": r["surfacePct"], "submergedAiPct": r["submergedPct"],
                "combinedAiPct": round(r["surfacePct"] + r["submergedPct"], 1),
                "signature": r["signature"],
            }
            for r in macro["regions"]
        ],
        "alberta-questions": [dict(q) for q in alberta["questions"]],
        "alberta-demographics": [dict(d) for d in alberta["demographics"]],
        "gas-countries": [dict(c) for c in gas["countries"]],
        "gas-pass-through": [dict(p) for p in gas["passThrough"]],
        "gas-industries": [dict(i) for i in gas["industries"]],
        "sodium-chemistries": [dict(c) for c in sodium["chemistries"]],
        "sodium-temp-curve": [dict(t) for t in sodium["tempCurve"]],
        "ai-cost-models": [dict(m) for m in ai_cost["models"]],
        "ai-cost-layers": [dict(l) for l in ai_cost["layers"]],
        "gen-tax-cohorts": [dict(g) for g in gen_tax["cohorts"]],
    }
