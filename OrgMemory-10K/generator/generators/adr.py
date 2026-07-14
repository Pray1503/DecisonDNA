import random
from datetime import datetime, timedelta
from generator.config import (
    ADR_TEMPLATES, DB_OPTIONS, MQ_OPTIONS, CACHE_OPTIONS, 
    ORCHESTRATION_OPTIONS, FRONTEND_OPTIONS
)

def generate_adrs(num_adrs: int, projects: list, employees: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates realistic Architecture Decision Records (ADRs) linked to projects and employees.
    """
    adrs = []
    
    # Filter employees to find engineers/architects who can author ADRs
    authors = [
        e for e in employees 
        if "Engineer" in e["role"] or "Architect" in e["role"] or "Scientist" in e["role"] or "Lead" in e["role"]
    ]
    if not authors:
        authors = employees  # Fallback
        
    for i in range(1, num_adrs + 1):
        adr_id = f"ADR-{i:04d}"
        
        # Pick a random template
        tmpl = random.choice(ADR_TEMPLATES)
        
        # Pick a random project
        proj = random.choice(projects)
        service_name = proj["name"]
        
        # Select choices matching project tech or configuration
        db_choice = random.choice(DB_OPTIONS)
        mq_choice = random.choice(MQ_OPTIONS)
        cache_choice = random.choice(CACHE_OPTIONS)
        orch_choice = random.choice(ORCHESTRATION_OPTIONS)
        fe_choice = random.choice(FRONTEND_OPTIONS)
        
        # Formatting fields
        fields = {
            "service": service_name,
            "database": db_choice,
            "message_queue": mq_choice,
            "caching_layer": cache_choice,
            "container_orchestration": orch_choice,
            "frontend_framework": fe_choice
        }
        
        title = tmpl["title_template"].format(**fields)
        context = tmpl["context"].format(**fields)
        problem = tmpl["problem"].format(**fields)
        alternatives = tmpl["alternatives"].format(**fields)
        decision = tmpl["decision"].format(**fields)
        reason = tmpl["reason"].format(**fields)
        consequences = tmpl["consequences"].format(**fields)
        expected_benefits = tmpl["expected_benefits"].format(**fields)
        potential_risks = tmpl["potential_risks"].format(**fields)
        
        # Date: distributed across the 5 years
        days_offset = random.randint(0, 5 * 365)
        adr_date = seed_date + timedelta(days=days_offset)
        
        # Complexity and Priority
        complexity = random.choices(["Low", "Medium", "High"], weights=[0.3, 0.5, 0.2])[0]
        priority = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.2, 0.5, 0.2, 0.1])[0]
        
        # Status
        # Newer ADRs are proposed, older are accepted/superseded
        if adr_date.year == 2025 and random.random() < 0.3:
            status = "Proposed"
        elif random.random() < 0.1:
            status = "Superseded"
        elif random.random() < 0.05:
            status = "Deprecated"
        else:
            status = "Accepted"
            
        # Owner
        owner_emp = random.choice(authors)
        owner_id = owner_emp["employee_id"]
        
        # Metric impacts (we store these to use in metrics and hindsight memory)
        impact_metric = tmpl["impact_metric"]
        impact_direction = tmpl["impact_direction"]
        impact_val = tmpl["impact_val"]
        
        # Keep track of database/caching technology selected
        tech_selected = ""
        if "database" in tmpl["title_template"]:
            tech_selected = db_choice
        elif "caching" in tmpl["title_template"]:
            tech_selected = cache_choice
        elif "queue" in tmpl["title_template"]:
            tech_selected = mq_choice
        elif "orchestration" in tmpl["title_template"]:
            tech_selected = orch_choice
        elif "framework" in tmpl["title_template"]:
            tech_selected = fe_choice
            
        adr = {
            "adr_id": adr_id,
            "title": title,
            "status": status,
            "date": adr_date.strftime("%Y-%m-%d"),
            "context": context,
            "problem": problem,
            "alternatives": alternatives,
            "decision": decision,
            "reason": reason,
            "consequences": consequences,
            "expected_benefits": expected_benefits,
            "potential_risks": potential_risks,
            "related_project": proj["project_id"],
            "owner": owner_id,
            "tags": tmpl["tags"],
            "complexity": complexity,
            "priority": priority,
            
            # Placeholders for links (will be filled later during graph linkage)
            "linked_jira_tickets": [],
            "linked_pull_requests": [],
            "linked_deployments": [],
            "linked_incidents": [],
            "linked_feedback": [],
            "outcome": "Pending deployment and operations feedback.",
            
            # Internal helpers for simulation consistency
            "_impact_metric": impact_metric,
            "_impact_direction": impact_direction,
            "_impact_val": impact_val,
            "_tech_selected": tech_selected
        }
        
        adrs.append(adr)
        
    # Sort ADRs by date so ID ordering matches temporal order
    adrs.sort(key=lambda x: x["date"])
    for idx, adr in enumerate(adrs):
        adr["adr_id"] = f"ADR-{idx+1:04d}"
        
    return adrs

def write_adr_markdown_files(adrs: list, output_dir_path):
    """
    Writes each ADR to its own markdown file in the architecture/ folder.
    """
    for adr in adrs:
        adr_id = adr["adr_id"]
        filepath = output_dir_path / "architecture" / f"{adr_id}.md"
        
        md_content = f"""# {adr_id}: {adr['title']}

* **Status:** {adr['status']}
* **Date:** {adr['date']}
* **Related Project:** {adr['related_project']}
* **Owner:** {adr['owner']}
* **Complexity:** {adr['complexity']}
* **Priority:** {adr['priority']}
* **Tags:** {', '.join(adr['tags'])}

## Context
{adr['context']}

## Problem
{adr['problem']}

## Alternatives Considered
{adr['alternatives']}

## Decision
{adr['decision']}

## Rationale
{adr['reason']}

## Consequences
{adr['consequences']}

## Expected Benefits
{adr['expected_benefits']}

## Potential Risks
{adr['potential_risks']}

## Operations and Outcomes
* **Jira Tickets:** {', '.join(adr['linked_jira_tickets']) if adr['linked_jira_tickets'] else 'None'}
* **GitHub PRs:** {', '.join(adr['linked_pull_requests']) if adr['linked_pull_requests'] else 'None'}
* **Deployments:** {', '.join(adr['linked_deployments']) if adr['linked_deployments'] else 'None'}
* **Incidents:** {', '.join(adr['linked_incidents']) if adr['linked_incidents'] else 'None'}
* **Developer Feedback:** {', '.join(adr['linked_feedback']) if adr['linked_feedback'] else 'None'}
* **Outcome Summary:** {adr['outcome']}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
