import random
from datetime import datetime, timedelta
from generator.config import DB_OPTIONS, MQ_OPTIONS, CACHE_OPTIONS

def generate_sprints(seed_date, num_sprints=130):
    """Generates bi-weekly sprint definitions."""
    sprints = []
    start_dt = seed_date
    for i in range(1, num_sprints + 1):
        end_dt = start_dt + timedelta(days=14)
        sprints.append({
            "name": f"Sprint-{start_dt.strftime('%Y')}-W{start_dt.strftime('%U')}",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d")
        })
        start_dt = end_dt
    return sprints

def generate_jira_tickets(num_tickets: int, projects: list, employees: list, adrs: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates Jira tickets (Epics, Stories, Tasks, Bugs, Spikes) with consistent relationships.
    """
    tickets = []
    sprints = generate_sprints(seed_date)
    
    # Track ticket counters per project key to generate keys like NCA-1, NCA-2
    project_counters = {p["jira_project"]["key"]: 1 for p in projects}
    
    # Group employees by department for assigning relevant tickets
    devs = [e for e in employees if e["department"] in ["Backend Engineering", "Frontend Engineering", "Platform Engineering", "AI Research", "DevOps", "Security"]]
    pms = [e for e in employees if e["department"] == "Product"]
    
    # 1. Allocate a portion of tickets specifically to ADR implementations
    # Each ADR gets 1 Spike (optional), 1 Epic (optional for high complexity), and 1-3 Stories/Tasks
    adr_tickets_count = 0
    adrs_handled = 0
    
    for adr in adrs:
        proj_id = adr["related_project"]
        proj = next((p for p in projects if p["project_id"] == proj_id), projects[0])
        p_key = proj["jira_project"]["key"]
        p_name = proj["name"]
        
        adr_date = datetime.strptime(adr["date"], "%Y-%m-%d")
        
        # Determine sprint based on ADR date
        sprint_name = "Backlog"
        for s in sprints:
            s_start = datetime.strptime(s["start_date"], "%Y-%m-%d")
            s_end = datetime.strptime(s["end_date"], "%Y-%m-%d")
            if s_start <= adr_date <= s_end:
                sprint_name = s["name"]
                break
                
        # Generate research Spike BEFORE ADR date
        if adr["complexity"] in ["Medium", "High"] and random.random() < 0.7:
            spike_id = f"{p_key}-{project_counters[p_key]}"
            project_counters[p_key] += 1
            
            # Owner: ADR author
            owner = adr["owner"]
            
            # Spike Date is slightly before ADR date
            spike_date = adr_date - timedelta(days=random.randint(5, 15))
            
            tickets.append({
                "ticket_id": spike_id,
                "type": "Spike",
                "title": f"Spike: Evaluate options for {adr['title'].split('for')[0].strip()}",
                "status": "Done",
                "description": f"Research spiked for {adr['title']}. Alternatives considered: {adr['alternatives']}",
                "project": proj_id,
                "owner": owner,
                "adr": adr["adr_id"],
                "sprint": sprint_name,
                "priority": adr["priority"],
                "dependencies": [],
                "created_date": spike_date.strftime("%Y-%m-%d"),
                "resolved_date": adr["date"]
            })
            adr["linked_jira_tickets"].append(spike_id)
            adr_tickets_count += 1
            
        # Generate Epic for the implementation
        epic_id = f"{p_key}-{project_counters[p_key]}"
        project_counters[p_key] += 1
        
        epic_owner = random.choice(pms)["employee_id"] if pms else adr["owner"]
        
        tickets.append({
            "ticket_id": epic_id,
            "type": "Epic",
            "title": f"Epic: {adr['title']}",
            "status": "Done" if adr["status"] in ["Accepted", "Superseded"] else "In Progress",
            "description": f"Implementation of decision in {adr['adr_id']}. Expected benefits: {adr['expected_benefits']}",
            "project": proj_id,
            "owner": epic_owner,
            "adr": adr["adr_id"],
            "sprint": sprint_name,
            "priority": adr["priority"],
            "dependencies": [],
            "created_date": adr["date"],
            "resolved_date": (adr_date + timedelta(days=30)).strftime("%Y-%m-%d")
        })
        adr["linked_jira_tickets"].append(epic_id)
        adr_tickets_count += 1
        
        # Generate Stories/Tasks implementing the Epic
        num_impl_tickets = random.randint(1, 3)
        for t_idx in range(num_impl_tickets):
            t_id = f"{p_key}-{project_counters[p_key]}"
            project_counters[p_key] += 1
            
            t_type = "Story" if t_idx == 0 else "Task"
            
            eligible_devs = [e["employee_id"] for e in devs if e["team"] == proj["team"]]
            if not eligible_devs:
                eligible_devs = [e["employee_id"] for e in devs]
            t_owner = random.choice(eligible_devs) if eligible_devs else adr["owner"]
                
            t_title = f"Implement {adr['_tech_selected']} backend service in {p_name}" if t_type == "Story" else f"Configure deployment pipelines for {adr['_tech_selected']} on {p_name}"
            
            created_dt = adr_date + timedelta(days=random.randint(1, 5))
            resolved_dt = created_dt + timedelta(days=random.randint(3, 14))
            
            tickets.append({
                "ticket_id": t_id,
                "type": t_type,
                "title": t_title,
                "status": "Done" if adr["status"] in ["Accepted", "Superseded"] else "Open",
                "description": f"Tasks to fulfill architectural decision {adr['adr_id']}. Focus on: {adr['decision']}",
                "project": proj_id,
                "owner": t_owner,
                "adr": adr["adr_id"],
                "sprint": sprint_name,
                "priority": adr["priority"],
                "dependencies": [epic_id],
                "created_date": created_dt.strftime("%Y-%m-%d"),
                "resolved_date": resolved_dt.strftime("%Y-%m-%d") if adr["status"] in ["Accepted", "Superseded"] else None
            })
            adr["linked_jira_tickets"].append(t_id)
            adr_tickets_count += 1
            
        adrs_handled += 1
        
    # 2. Generate generic tickets to fill the rest of the target count
    remaining_tickets = num_tickets - adr_tickets_count
    
    for i in range(max(10, remaining_tickets)):
        proj = random.choice(projects)
        p_key = proj["jira_project"]["key"]
        p_id = proj["project_id"]
        p_name = proj["name"]
        
        t_id = f"{p_key}-{project_counters[p_key]}"
        project_counters[p_key] += 1
        
        t_type = random.choices(["Story", "Task", "Bug"], weights=[0.5, 0.3, 0.2])[0]
        
        # Pick date
        days_offset = random.randint(0, 5 * 365)
        created_dt = seed_date + timedelta(days=days_offset)
        
        sprint_name = "Backlog"
        for s in sprints:
            s_start = datetime.strptime(s["start_date"], "%Y-%m-%d")
            s_end = datetime.strptime(s["end_date"], "%Y-%m-%d")
            if s_start <= created_dt <= s_end:
                sprint_name = s["name"]
                break
                
        # Owner
        # Find developer in matching team
        eligible_devs = [e for e in devs if e["team"] == proj["team"]]
        if not eligible_devs:
            eligible_devs = devs if devs else employees
        t_owner = random.choice(eligible_devs)["employee_id"]
        
        # Title/Description based on type
        priority = random.choice(["Low", "Medium", "High", "Critical"])
        status = random.choices(["Done", "In Progress", "Open", "Blocked"], weights=[0.75, 0.10, 0.10, 0.05])[0]
        
        if t_type == "Story":
            title = random.choice([
                f"Add feature request endpoint to {p_name}",
                f"Optimize user session timeouts in {p_name}",
                f"Refactor API request validation for {p_name}",
                f"Implement pagination for bulk queries in {p_name} controller",
                f"Integrate metrics reporting client in {p_name}"
            ])
            desc = f"As a developer, we need to implement {title.lower()} to support customer growth."
        elif t_type == "Task":
            title = random.choice([
                f"Upgrade dependency libraries in {p_name}",
                f"Write integration tests for {p_name} router",
                f"Configure Prometheus alert rules for {p_name}",
                f"Document API endpoints in OpenAPISchema for {p_name}",
                f"Security scanning of Docker base images for {p_name}"
            ])
            desc = f"Developer chore: {title.lower()}."
        else: # Bug
            title = random.choice([
                f"Fix memory leak in {p_name} concurrency routine",
                f"Resolve validation error on {p_name} post body parsing",
                f"Fix broken CSS styles in {p_name} dashboard view",
                f"Resolve NullPointerException in {p_name} client",
                f"Fix transaction rollback failure in {p_name} checkout flow"
            ])
            desc = f"Reported bug: {title.lower()} causing test failures in production environment."
            
        resolved_dt = None
        if status == "Done":
            resolved_dt = (created_dt + timedelta(days=random.randint(2, 14))).strftime("%Y-%m-%d")
            
        # Dependencies: occasionally reference another ticket of the same project
        deps = []
        if i > 10 and random.random() < 0.15:
            # Pick a previously generated ticket from this project
            prev_tickets = [t["ticket_id"] for t in tickets if t["project"] == p_id]
            if prev_tickets:
                deps.append(random.choice(prev_tickets))
                
        tickets.append({
            "ticket_id": t_id,
            "type": t_type,
            "title": title,
            "status": status,
            "description": desc,
            "project": p_id,
            "owner": t_owner,
            "adr": None, # Generic ticket
            "sprint": sprint_name,
            "priority": priority,
            "dependencies": deps,
            "created_date": created_dt.strftime("%Y-%m-%d"),
            "resolved_date": resolved_dt
        })
        
    return tickets
