import random
from datetime import datetime, timedelta
from generator.config import FEEDBACK_TEMPLATES

def generate_developer_feedback(
    num_entries: int, projects: list, employees: list, adrs: list, jira_tickets: list,
    seed_date=datetime(2021, 1, 1)
):
    """
    Generates developer feedback logs representing retrospectives, surveys, and opinions.
    """
    feedback_entries = []
    
    # Filter developers
    devs = [e for e in employees if e["department"] in ["Backend Engineering", "Frontend Engineering", "Platform Engineering", "AI Research", "DevOps", "Security"]]
    if not devs:
        devs = employees
        
    # Get distinct sprints from jira tickets
    sprints = list(set([t["sprint"] for t in jira_tickets if t["sprint"] != "Backlog"]))
    if not sprints:
        sprints = ["Sprint-2021-W01", "Sprint-2021-W03", "Sprint-2021-W05"]
        
    for i in range(1, num_entries + 1):
        f_id = f"FDB-{i:05d}"
        
        # Pick developer
        dev = random.choice(devs)
        dev_id = dev["employee_id"]
        
        # Pick sprint
        sprint = random.choice(sprints)
        
        # Determine if this feedback is about a specific project or ADR
        proj = random.choice(projects)
        proj_id = proj["project_id"]
        proj_name = proj["name"]
        
        # Pick ADR related to project if available
        proj_adrs = [a for a in adrs if a["related_project"] == proj_id]
        adr_id = random.choice(proj_adrs)["adr_id"] if proj_adrs and random.random() < 0.3 else None
        
        # Choose difficulty rating (1: Easy, 5: Hard)
        difficulty = random.choices([1, 2, 3, 4, 5], weights=[0.1, 0.25, 0.4, 0.2, 0.05])[0]
        
        # Build feedback message
        if adr_id:
            adr_title = next(a["title"] for a in adrs if a["adr_id"] == adr_id)
            opinion = f"Regarding {adr_id} ({adr_title}): " + random.choice([
                f"Implementing this decision on {proj_name} was relatively straightforward, but testing took time.",
                f"We hit some performance hiccups under load on {proj_name} after applying this decision. We might need a follow-up architecture review.",
                f"The team found the design in {adr_id} clean. It helped decouple our database calls nicely.",
                f"There's still a learning curve for the team regarding the new tech stack. We need more pair programming sessions."
            ])
            suggestion = f"Write better onboarding docs for {adr_id}."
        else:
            opinion = random.choice(FEEDBACK_TEMPLATES).format(
                service=proj_name, 
                database="MongoDB", 
                message_queue="Kafka", 
                caching_layer="Redis", 
                container_orchestration="Kubernetes", 
                frontend_framework="Next.js"
            )
            suggestion = random.choice([
                f"Improve CI build times for {proj_name} repository. Currently taking > 15 minutes.",
                f"Enforce standard code linter rules globally.",
                f"Provide sandbox credentials for local database testing.",
                f"Refactor the billing module of {proj_name}; it has too much technical debt.",
                f"Set up an internal knowledge base detailing API interface contracts."
            ])
            
        feedback_entries.append({
            "feedback_id": f_id,
            "sprint": sprint,
            "project_id": proj_id,
            "adr_id": adr_id,
            "employee_id": dev_id,
            "difficulty_rating": difficulty,
            "opinion": opinion,
            "suggestion": suggestion
        })
        
        # Link back to ADR if it exists
        if adr_id:
            adr_obj = next((a for a in adrs if a["adr_id"] == adr_id), None)
            if adr_obj:
                adr_obj["linked_feedback"].append(f_id)
                
    return feedback_entries
