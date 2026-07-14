import random
from datetime import datetime, timedelta
from faker import Faker
from generator.config import PRODUCTS, CUSTOMER_TICKETS

fake = Faker()

def generate_customers(num_customers: int, projects: list, incidents: list, jira_tickets: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates enterprise customers with support tickets, feature requests, NPS, and renewals.
    Consistently links support tickets to production incidents and feature requests to Jira tickets.
    """
    customers = []
    
    # Industries list
    industries = ["Fintech", "Healthcare", "E-commerce", "Logistics", "Automotive", "Cybersecurity", "GovTech", "EduTech"]
    
    # Filter Jira stories/epics to link to customer feature requests
    stories_and_epics = [t for t in jira_tickets if t["type"] in ["Story", "Epic"]]
    
    sup_counter = 1
    feat_counter = 1
    
    for i in range(1, num_customers + 1):
        c_id = f"CST-{i:04d}"
        c_name = fake.company()
        industry = random.choice(industries)
        
        # Products subscribed (1 to 3 products)
        subscribed_products = random.sample(PRODUCTS, random.randint(1, 3))
        
        # NPS score (biased positive, but occasionally low)
        nps = random.choices(
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            weights=[0.3, 0.3, 0.15, 0.1, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01]
        )[0]
        
        # Renewals history (annual renewals over 5 years)
        renewals = []
        contract_value = random.randint(15000, 250000) # USD per year
        
        for yr in range(2021, 2026):
            # Biased towards renewal, but low NPS increases churn probability
            churn_prob = 0.05 if nps >= 8 else (0.2 if nps >= 6 else 0.6)
            status = "Renewed" if random.random() > churn_prob else "Churned"
            
            renewals.append({
                "year": yr,
                "status": status,
                "contract_value_usd": contract_value
            })
            
            # If churned, stop renewals history
            if status == "Churned":
                break
                
        # Support tickets
        support_tickets = []
        num_support = random.randint(1, 5)
        for _ in range(num_support):
            sup_id = f"SUP-{sup_counter:04d}"
            sup_counter += 1
            
            days_offset = random.randint(0, 5 * 365)
            ticket_dt = seed_date + timedelta(days=days_offset)
            
            prod = random.choice(subscribed_products)
            subject = random.choice(CUSTOMER_TICKETS)
            
            # Link support tickets to production incidents if they fall in the incident window
            linked_incident_id = None
            
            # Find if there was an incident for a project that matches this product/time
            for inc in incidents:
                inc_start = inc["_detect_time"]
                inc_end = inc["_resolve_time"]
                
                # Check if ticket was created on the day of the incident
                if inc_start.strftime("%Y-%m-%d") == ticket_dt.strftime("%Y-%m-%d"):
                    # Check if project matches product (e.g. AtlasPay maps to atlaspay-gateway)
                    proj_obj = next((p for p in projects if p["project_id"] == inc["linked_deployment"].split("-")[0]), None) # dummy check
                    # Better: check if product name is inside the incident cause or project name
                    if prod.lower() in inc["cause"].lower() or prod.lower() in inc["_project_name"].lower():
                        linked_incident_id = inc["incident_id"]
                        subject = f"System Error: {inc['cause']} affecting our operations."
                        break
                        
            support_tickets.append({
                "ticket_id": sup_id,
                "subject": subject,
                "status": "Closed" if linked_incident_id or random.random() < 0.9 else "Open",
                "product": prod,
                "created_date": ticket_dt.strftime("%Y-%m-%d"),
                "linked_incident": linked_incident_id
            })
            
        # Feature requests
        feature_requests = []
        num_features = random.randint(1, 3)
        for _ in range(num_features):
            feat_id = f"FTR-{feat_counter:04d}"
            feat_counter += 1
            
            days_offset = random.randint(0, 5 * 365)
            feat_dt = seed_date + timedelta(days=days_offset)
            
            prod = random.choice(subscribed_products)
            
            # Link to a Jira story or epic from a project that matches this product
            linked_jira_id = None
            
            # Find a project matching this product
            prod_projects = [p for p in projects if prod.lower() in p["name"].lower()]
            if prod_projects:
                target_proj = random.choice(prod_projects)
                proj_jira_stories = [t for t in stories_and_epics if t["project"] == target_proj["project_id"]]
                if proj_jira_stories:
                    linked_jira = random.choice(proj_jira_stories)
                    linked_jira_id = linked_jira["ticket_id"]
                    title = f"Request: {linked_jira['title']}"
                else:
                    title = f"Request: Add advanced custom report parameters for {prod}"
            else:
                title = f"Request: Integrate dashboard widgets in {prod}"
                
            feature_requests.append({
                "request_id": feat_id,
                "title": title,
                "status": "Implemented" if linked_jira_id and any(t["status"] == "Done" for t in jira_tickets if t["ticket_id"] == linked_jira_id) else "Under Review",
                "product": prod,
                "created_date": feat_dt.strftime("%Y-%m-%d"),
                "linked_jira": linked_jira_id
            })
            
        customers.append({
            "customer_id": c_id,
            "name": c_name,
            "industry": industry,
            "subscribed_products": subscribed_products,
            "nps_rating": nps,
            "renewals_history": renewals,
            "support_tickets": support_tickets,
            "feature_requests": feature_requests
        })
        
    return customers
