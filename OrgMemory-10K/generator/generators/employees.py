import random
from datetime import datetime, timedelta
from faker import Faker
from generator.config import DEPARTMENTS, TEAMS, ROLES, SKILLS_BY_DEPT

fake = Faker()

def generate_employees(num_employees: int, seed_date=datetime(2021, 1, 1)):
    """
    Generates a list of employees with realistic details and reporting hierarchy.
    """
    employees = []
    
    # 1. Generate CEO (the ultimate manager)
    ceo_id = "EMP-001"
    ceo_name = fake.name()
    ceo_email = f"{ceo_name.lower().replace(' ', '.')}@novatech.com"
    ceo_joining = seed_date - timedelta(days=random.randint(1000, 2000))  # Joined long ago
    
    ceo = {
        "employee_id": ceo_id,
        "name": ceo_name,
        "email": ceo_email,
        "department": "Management",
        "team": "Executive",
        "manager": "CEO",  # Reports to board
        "joining_date": ceo_joining.strftime("%Y-%m-%d"),
        "experience": f"{random.randint(15, 25)} years",
        "skills": ["Leadership", "Business Strategy", "Enterprise SaaS", "Public Speaking"],
        "role": "Chief Executive Officer",
        "salary_band": "L5 ($400k-$600k)",
        "github_username": f"{ceo_name.lower().replace(' ', '')}-ceo",
        "jira_username": f"{ceo_name.lower().replace(' ', '')}",
        "meeting_attendance": 0.95,
        "performance_rating": "Outstanding"
    }
    employees.append(ceo)
    
    # 2. Generate Department Heads (VPs / Directors)
    dept_heads = {}
    emp_counter = 2
    
    for dept in DEPARTMENTS:
        head_id = f"EMP-{emp_counter:03d}"
        emp_counter += 1
        head_name = fake.name()
        head_joining = seed_date - timedelta(days=random.randint(500, 1000))
        
        # Choose role details
        role_info = ROLES[dept][-1]  # Highest level role for head
        
        head = {
            "employee_id": head_id,
            "name": head_name,
            "email": f"{head_name.lower().replace(' ', '.')}@novatech.com",
            "department": dept,
            "team": "Leadership",
            "manager": ceo_id,
            "joining_date": head_joining.strftime("%Y-%m-%d"),
            "experience": f"{random.randint(10, 15)} years",
            "skills": random.sample(SKILLS_BY_DEPT[dept], min(4, len(SKILLS_BY_DEPT[dept]))) + ["Management", "Agile"],
            "role": f"Director of {dept}" if dept != "Product" else "VP of Product",
            "salary_band": role_info["salary_band"],
            "github_username": f"{head_name.lower().replace(' ', '')}-nt",
            "jira_username": f"{head_name.lower().replace(' ', '')}",
            "meeting_attendance": round(random.uniform(0.90, 0.98), 2),
            "performance_rating": random.choice(["Exceeds Expectations", "Meets Expectations"])
        }
        employees.append(head)
        dept_heads[dept] = head_id
        
    # 3. Generate Managers/Leads for each team
    managers_by_team = {}
    for dept, teams in TEAMS.items():
        managers_by_team[dept] = {}
        for team in teams:
            lead_id = f"EMP-{emp_counter:03d}"
            emp_counter += 1
            lead_name = fake.name()
            lead_joining = seed_date - timedelta(days=random.randint(200, 600))
            
            # Select role details (usually Level 3 or Senior)
            role_info = ROLES[dept][min(2, len(ROLES[dept])-1)]
            
            lead = {
                "employee_id": lead_id,
                "name": lead_name,
                "email": f"{lead_name.lower().replace(' ', '.')}@novatech.com",
                "department": dept,
                "team": team,
                "manager": dept_heads[dept],
                "joining_date": lead_joining.strftime("%Y-%m-%d"),
                "experience": f"{random.randint(6, 10)} years",
                "skills": random.sample(SKILLS_BY_DEPT[dept], min(6, len(SKILLS_BY_DEPT[dept]))),
                "role": f"{team} Lead",
                "salary_band": role_info["salary_band"],
                "github_username": f"{lead_name.lower().replace(' ', '')}-dev",
                "jira_username": f"{lead_name.lower().replace(' ', '')}",
                "meeting_attendance": round(random.uniform(0.85, 0.95), 2),
                "performance_rating": random.choice(["Exceeds Expectations", "Meets Expectations", "Needs Improvement"])
            }
            employees.append(lead)
            managers_by_team[dept][team] = lead_id
            
    # 4. Generate Individual Contributors (ICs)
    while len(employees) < num_employees:
        dept = random.choice(DEPARTMENTS)
        team = random.choice(TEAMS[dept])
        
        emp_id = f"EMP-{emp_counter:03d}"
        emp_counter += 1
        emp_name = fake.name()
        
        # Joined during the simulation period (2021-2025)
        days_offset = random.randint(0, 5 * 365)
        emp_joining = seed_date + timedelta(days=days_offset)
        
        # Select role level (mostly L1-L2, occasionally L3)
        role_weight = random.choices([0, 1, 2], weights=[0.40, 0.50, 0.10])[0]
        role_info = ROLES[dept][min(role_weight, len(ROLES[dept])-1)]
        
        # Experience
        exp_range = role_info["experience"].split(" ")[0]
        if "-" in exp_range:
            min_exp, max_exp = map(int, exp_range.split("-"))
            exp_yrs = random.randint(min_exp, max_exp)
        else:
            exp_yrs = random.randint(10, 15)
            
        # Manager is the team lead
        mgr_id = managers_by_team[dept].get(team, dept_heads[dept])
        
        ic = {
            "employee_id": emp_id,
            "name": emp_name,
            "email": f"{emp_name.lower().replace(' ', '.')}@novatech.com",
            "department": dept,
            "team": team,
            "manager": mgr_id,
            "joining_date": emp_joining.strftime("%Y-%m-%d"),
            "experience": f"{exp_yrs} years",
            "skills": random.sample(SKILLS_BY_DEPT[dept], min(5, len(SKILLS_BY_DEPT[dept]))),
            "role": role_info["role"],
            "salary_band": role_info["salary_band"],
            "github_username": f"{emp_name.lower().replace(' ', '')}-nt",
            "jira_username": f"{emp_name.lower().replace(' ', '')}",
            "meeting_attendance": round(random.uniform(0.75, 0.95), 2),
            "performance_rating": random.choice(["Exceeds Expectations", "Meets Expectations", "Meets Expectations", "Needs Improvement"])
        }
        employees.append(ic)
        
    return employees
