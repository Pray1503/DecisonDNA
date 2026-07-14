import random
from datetime import datetime, timedelta
from generator.config import PROJECTS_CONFIG

def generate_projects(num_projects: int, employees: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates software projects mapped to repositories, tech stacks, and team owners.
    """
    projects = []
    
    # Filter config based on scale
    active_configs = PROJECTS_CONFIG[:num_projects]
    
    for i, cfg in enumerate(active_configs):
        p_name = cfg["name"]
        p_id = cfg["project_id"]
        team = cfg["team"]
        dept = cfg["dept"]
        
        # Find potential owners: Managers or PMs in the matching team/department
        potential_owners = [
            e["employee_id"] for e in employees 
            if (e["department"] == dept and e["team"] == team) or
               (e["department"] == "Product" and team.split(" ")[0] in e["team"])
        ]
        
        # Fallback if no matching employees are found (e.g., in small scale)
        if not potential_owners:
            potential_owners = [
                e["employee_id"] for e in employees 
                if e["department"] in [dept, "Product"]
            ]
        if not potential_owners:
            potential_owners = [employees[0]["employee_id"]] # Fallback to CEO
            
        owner = random.choice(potential_owners)
        
        # Jira project key from name
        words = p_name.replace("-", " ").split(" ")
        jira_key = "".join([w[0].upper() for w in words])
        if len(jira_key) < 2:
            jira_key = p_name[:3].upper()
        # Ensure key is unique
        jira_key = f"{jira_key}{i}" if len(jira_key) < 3 else jira_key
        
        jira_project = {
            "key": jira_key,
            "name": p_name.replace("-", " ").title()
        }
        
        # Timeline
        # Project start: between 1 year before simulation and 2 years into simulation
        start_offset = random.randint(-365, 365 * 2)
        start_dt = seed_date + timedelta(days=start_offset)
        
        status = random.choices(["Active", "Completed", "Archived"], weights=[0.8, 0.15, 0.05])[0]
        
        if status in ["Completed", "Archived"]:
            end_dt = start_dt + timedelta(days=random.randint(180, 500))
            end_str = end_dt.strftime("%Y-%m-%d")
        else:
            end_str = "Ongoing"
            
        timeline = {
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_str
        }
        
        projects.append({
            "project_id": p_id,
            "name": p_name,
            "owner": owner,
            "repository": cfg["repo"],
            "jira_project": jira_project,
            "technology_stack": cfg["tech"],
            "team": team,
            "timeline": timeline,
            "status": status
        })
        
    return projects
