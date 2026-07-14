import random
from datetime import datetime, timedelta
from generator.config import MEETING_TEMPLATES

def generate_meetings(num_meetings: int, projects: list, employees: list, adrs: list, jira_tickets: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates realistic meeting transcripts linked to ADRs, Jira tickets, and employees.
    """
    meetings = []
    
    # 1. Generate meetings discussing each ADR
    # We will generate one design review meeting per ADR, slightly before or on the ADR date
    adr_meetings_count = 0
    for adr in adrs:
        adr_id = adr["adr_id"]
        adr_dt = datetime.strptime(adr["date"], "%Y-%m-%d")
        meet_dt = adr_dt - timedelta(days=random.randint(0, 3))
        
        # Participants: Owner + 3-6 other developers from the project team or department
        proj_id = adr["related_project"]
        proj = next((p for p in projects if p["project_id"] == proj_id), projects[0])
        team = proj["team"]
        
        team_members = [e["employee_id"] for e in employees if e["team"] == team and e["employee_id"] != adr["owner"]]
        if not team_members:
            team_members = [e["employee_id"] for e in employees if e["department"] == proj["dept"] and e["employee_id"] != adr["owner"]]
        if not team_members:
            team_members = [employees[0]["employee_id"]] # CEO fallback
            
        participants = [adr["owner"]] + random.sample(team_members, min(len(team_members), random.randint(2, 5)))
        
        # Agenda and discussion based on ADR
        agenda = f"Design Review: {adr['title']}"
        discussion = f"The team discussed the problem: '{adr['problem']}'. Author {adr['owner']} presented the proposal to: '{adr['decision']}'. We reviewed alternatives: {adr['alternatives']}. Feedback was mostly positive regarding the expected benefits: '{adr['expected_benefits']}'. SRE raised concerns on potential risks: '{adr['potential_risks']}', which we decided to mitigate by scaling up monitoring."
        decision_summary = f"Approved implementation of decision. {adr['owner']} to publish official ADR and create Jira implementation tasks."
        
        # Action items map to Jira tickets of this ADR
        action_items = [f"Complete implementation details in {t}" for t in adr["linked_jira_tickets"][:3]]
        
        meet_id = f"MEET-{adr_meetings_count+1:04d}"
        adr_meetings_count += 1
        
        meetings.append({
            "meeting_id": meet_id,
            "date": meet_dt.strftime("%Y-%m-%d"),
            "time": f"{random.randint(9, 16):02d}:{random.choice([0, 15, 30, 45]):02d}",
            "participants": participants,
            "agenda": agenda,
            "discussion": discussion,
            "decision": decision_summary,
            "action_items": action_items,
            "linked_adr": adr_id,
            "linked_jira": adr["linked_jira_tickets"][0] if adr["linked_jira_tickets"] else None,
            "linked_incident": None
        })
        
    # 2. Generate remaining meetings (generic sprint retros, planning, incident syncs)
    remaining_meetings = num_meetings - adr_meetings_count
    
    for i in range(max(10, remaining_meetings)):
        meet_id = f"MEET-{adr_meetings_count+1:04d}"
        adr_meetings_count += 1
        
        # Pick date
        days_offset = random.randint(0, 5 * 365)
        meet_dt = seed_date + timedelta(days=days_offset)
        
        # Choose a template
        tmpl = random.choice(MEETING_TEMPLATES)
        
        # Setup template details
        agenda = tmpl["agenda"].format(inc_num=f"{i:03d}")
        discussion = tmpl["discussion"].format(service_name="various services", db_tech="Database", cache_tech="Cache", mq_tech="Message Queue", mem_limit="2Gi")
        
        # Pick 4-8 random employees
        participants = [e["employee_id"] for e in random.sample(employees, random.randint(4, 8))]
        
        meetings.append({
            "meeting_id": meet_id,
            "date": meet_dt.strftime("%Y-%m-%d"),
            "time": f"{random.randint(9, 16):02d}:{random.choice([0, 15, 30, 45]):02d}",
            "participants": participants,
            "agenda": agenda,
            "discussion": discussion,
            "decision": tmpl["decisions"],
            "action_items": tmpl["actions"],
            "linked_adr": None,
            "linked_jira": None,
            "linked_incident": None
        })
        
    # Sort chronologically
    meetings.sort(key=lambda x: x["date"])
    for idx, meet in enumerate(meetings):
        meet["meeting_id"] = f"MEET-{idx+1:04d}"
        
    return meetings

def write_meeting_markdown_files(meetings: list, output_dir_path):
    """
    Writes each meeting transcript to its own markdown file in the meetings/ folder.
    """
    for meet in meetings:
        meet_id = meet["meeting_id"]
        filepath = output_dir_path / "meetings" / f"{meet_id}.md"
        
        md_content = f"""# Meeting Minutes: {meet['agenda']}

* **Meeting ID:** {meet_id}
* **Date:** {meet['date']} at {meet['time']}
* **Linked ADR:** {meet['linked_adr'] if meet['linked_adr'] else 'None'}
* **Linked Jira:** {meet['linked_jira'] if meet['linked_jira'] else 'None'}
* **Linked Incident:** {meet['linked_incident'] if meet['linked_incident'] else 'None'}

## Participants
{', '.join(meet['participants'])}

## Agenda
{meet['agenda']}

## Discussion
{meet['discussion']}

## Decisions Made
{meet['decision']}

## Action Items
{chr(10).join([f"- [ ] {item}" for item in meet['action_items']]) if meet['action_items'] else 'None'}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
