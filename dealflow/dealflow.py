from datetime import datetime
from pydantic import Field
from enrichmcp import EnrichMCP, EnrichModel
from typing import Optional, Dict

app = EnrichMCP(
    title="DealFlow Lead Management",
    description="Lead ingestion, enrichment, scoring, routing, and reporting"
)

@app.entity
class Lead(EnrichModel):
    """Lead entity representing a marketing or sales lead in the DealFlow system."""
    id: int = Field(description="Lead ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    name: str = Field(description="Lead name")
    email: str = Field(description="Lead email")
    source: str = Field(description="Lead source")
    extra: dict = Field(default_factory=dict, description="Extra metadata")
    status: str = Field(default="new", description="Lead status")
    score: Optional[str] = Field(default=None, description="Lead score")
    assigned_to: Optional[dict] = Field(default=None, description="Assigned sales rep")

LEADS: dict[int, Lead] = {}
SALES_REPS = [
    {"id": 1, "name": "Alice", "specialty": "Startup founders, corporate execs", "comment": "Great with high-value and target buyers"},
    {"id": 2, "name": "Bob", "specialty": "ML engineers, students, researchers", "comment": "Technical, connects with influencers and evangelists"},
    {"id": 3, "name": "Carol", "specialty": "Investors, VCs, referrals", "comment": "Understands investor mindset, builds relationships"},
]
route_counter = 0

@app.create
async def ingest_lead(name: str, email: str, source: str, extra: Optional[Dict] = None) -> Lead:
    """Ingest a new lead into the system with name, email, source, and optional extra metadata."""
    lid = len(LEADS) + 1
    lead = Lead(id=lid, name=name, email=email, source=source, extra=extra or {})
    LEADS[lid] = lead
    return lead

@app.update
async def enrich_lead(lead_id: int) -> Lead:
    """Enrich a lead with dummy metadata such as company, LinkedIn, industry, and location."""
    lead = LEADS[lead_id]
    enrichment = {
        "company": "Acme Corp",
        "linkedin": f"https://linkedin.com/in/{lead.name.replace(' ', '').lower()}",
        "industry": "Technology",
        "location": "San Francisco, CA"
    }
    lead.extra.update(enrichment)
    LEADS[lead_id] = lead
    return lead

@app.update
async def score_lead(lead_id: int) -> Lead:
    """Score a lead as SQL or MQL using rule-based logic based on company and source."""
    lead = LEADS[lead_id]
    company = lead.extra.get("company", "")
    if company == "Acme Corp" and lead.source == "web_form":
        lead.score = "SQL"
    else:
        lead.score = "MQL"
    LEADS[lead_id] = lead
    return lead

@app.update
async def route_lead(lead_id: int) -> Lead:
    """Assign a lead to a sales rep using round-robin logic and simulate a notification."""
    global route_counter
    lead = LEADS[lead_id]
    rep = SALES_REPS[route_counter % len(SALES_REPS)]
    route_counter += 1
    lead.assigned_to = rep
    lead.status = "assigned"
    print(f"[Notification] Lead {lead_id} assigned to {rep['name']} (email: {lead.email})")
    LEADS[lead_id] = lead
    return lead


@app.update
async def report_performance() -> dict:
    """Return dummy performance and attribution reporting metrics for all leads."""
    total_leads = len(LEADS)
    leads_by_source = {}
    leads_by_score = {"MQL": 0, "SQL": 0}
    leads_by_rep = {rep["name"]: 0 for rep in SALES_REPS}
    for lead in LEADS.values():
        leads_by_source[lead.source] = leads_by_source.get(lead.source, 0) + 1
        if lead.score in leads_by_score:
            leads_by_score[lead.score] += 1
        if lead.assigned_to:
            leads_by_rep[lead.assigned_to["name"]] += 1
    report = {
        "total_leads": total_leads,
        "leads_by_source": leads_by_source,
        "leads_by_score": leads_by_score,
        "leads_by_rep": leads_by_rep
    }
    return {
        "report_markdown": format_report_markdown(report),
        "report_data": report  # Optionally include raw data too
    }

def format_report_markdown(report: dict) -> str:
    md = f"""# DealFlow Report

**Total Leads:** {report['total_leads']}

## Leads by Source
| Source | Count |
|--------|-------|
"""
    for src, count in report['leads_by_source'].items():
        md += f"| {src} | {count} |\n"

    md += "\n## Leads by Score\n| Score | Count |\n|-------|-------|\n"
    for score, count in report['leads_by_score'].items():
        md += f"| {score} | {count} |\n"

    md += "\n## Leads by Rep\n| Rep | Count |\n|-----|-------|\n"
    for rep, count in report['leads_by_rep'].items():
        md += f"| {rep} | {count} |\n"

    return md

@app.create
async def process_lead_and_report(name: str, email: str, source: str) -> dict:
    """Process a lead through ingest, enrich, score, route, and return a markdown diagram and report."""
    # 1. Ingest
    lead = await ingest_lead(name, email, source)
    # 2. Enrich
    enriched = await enrich_lead(lead.id)
    # 3. Score
    scored = await score_lead(lead.id)
    # 4. Route
    routed = await route_lead(lead.id)
    # 5. Report
    report = await report_performance()
    # Diagram
    diagram = f'''
📩 Lead Source: {source}
        |
        V
📥 Ingest Lead ({name}, {email}, {source})
        |
        V
🧠 Enrich Lead (company: {enriched.extra.get('company')}, LinkedIn: {enriched.extra.get('linkedin')}, industry: {enriched.extra.get('industry')})
        |
        V
📈 Score Lead → {scored.score}
        |
        V
🔄 Route to Rep → {routed.assigned_to['name'] if routed.assigned_to else 'N/A'}
        |
        V
📊 Report → Source counts, score ratios, rep assignments
'''
    return {
        "process_diagram": diagram,
        "report_markdown": report["report_markdown"],
        "report_data": report["report_data"]
    }

def main():
    app.run()

if __name__ == "__main__":
    main()
