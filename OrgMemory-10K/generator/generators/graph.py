import random
import networkx as nx
from datetime import datetime

def build_relationship_graph(
    employees: list, projects: list, adrs: list, jira_tickets: list,
    pull_requests: list, commits: list, deployments: list, incidents: list,
    feedback: list, customers: list, memories: list
):
    """
    Assembles a NetworkX directed graph containing all generated entities and their relationships.
    This graph is used to verify consistency and programmatically generate solvable benchmark questions.
    """
    G = nx.DiGraph()
    
    # 1. Add Nodes
    for e in employees:
        G.add_node(e["employee_id"], type="employee", label=e["name"], data=e)
        
    for p in projects:
        G.add_node(p["project_id"], type="project", label=p["name"], data=p)
        
    for a in adrs:
        G.add_node(a["adr_id"], type="adr", label=a["title"], data=a)
        
    for t in jira_tickets:
        G.add_node(t["ticket_id"], type="jira", label=t["title"], data=t)
        
    for pr in pull_requests:
        G.add_node(pr["pr_id"], type="pr", label=pr["title"], data=pr)
        
    for c in commits:
        G.add_node(c["commit_sha"], type="commit", label=c["message"], data=c)
        
    for d in deployments:
        G.add_node(d["deployment_id"], type="deployment", label=d["pipeline_run"], data=d)
        
    for inc in incidents:
        G.add_node(inc["incident_id"], type="incident", label=inc["cause"], data=inc)
        
    for f in feedback:
        G.add_node(f["feedback_id"], type="feedback", label=f["opinion"][:30], data=f)
        
    for cust in customers:
        G.add_node(cust["customer_id"], type="customer", label=cust["name"], data=cust)
        # Add support tickets and feature requests as nodes
        for st in cust["support_tickets"]:
            G.add_node(st["ticket_id"], type="support_ticket", label=st["subject"], data=st)
        for fr in cust["feature_requests"]:
            G.add_node(fr["request_id"], type="feature_request", label=fr["title"], data=fr)
            
    for m in memories:
        G.add_node(f"MEM-{m['adr_id'].split('-')[1]}", type="memory", label=m["title"], data=m)

    # 2. Add Edges (Relationships)
    
    # Reporting lines
    for e in employees:
        if e["manager"] and e["manager"] != "CEO" and e["manager"] in G:
            G.add_edge(e["employee_id"], e["manager"], rel="reports_to")
            
    # Project owners
    for p in projects:
        if p["owner"] in G:
            G.add_edge(p["project_id"], p["owner"], rel="owned_by")
            
    # ADR relations
    for a in adrs:
        if a["related_project"] in G:
            G.add_edge(a["adr_id"], a["related_project"], rel="related_to")
        if a["owner"] in G:
            G.add_edge(a["adr_id"], a["owner"], rel="authored_by")
            
    # Jira tickets
    for t in jira_tickets:
        if t["project"] in G:
            G.add_edge(t["ticket_id"], t["project"], rel="belongs_to")
        if t["owner"] in G:
            G.add_edge(t["ticket_id"], t["owner"], rel="assigned_to")
        if t["adr"] and t["adr"] in G:
            G.add_edge(t["ticket_id"], t["adr"], rel="implements_adr")
        for dep in t["dependencies"]:
            if dep in G:
                G.add_edge(t["ticket_id"], dep, rel="blocks")
                
    # GitHub pull requests
    for pr in pull_requests:
        # PR to Jira ticket
        if pr["jira_ticket"] in G:
            G.add_edge(pr["pr_id"], pr["jira_ticket"], rel="resolves_ticket")
        # PR to ADR
        if pr["adr"] and pr["adr"] in G:
            G.add_edge(pr["pr_id"], pr["adr"], rel="implements_adr")
        # PR reviewer
        reviewer_emp = next((e for e in employees if e["github_username"] == pr["reviewer"]), None)
        if reviewer_emp:
            G.add_edge(pr["pr_id"], reviewer_emp["employee_id"], rel="reviewed_by")
        # PR commits
        for c in pr["commits"]:
            if c in G:
                G.add_edge(c, pr["pr_id"], rel="part_of_pr")
                
    # Direct commits to repo (mapped via project repos)
    for c in commits:
        if not c["pull_request"]:
            proj_obj = next((p for p in projects if p["repository"] == c["repository"]), None)
            if proj_obj:
                G.add_edge(c["commit_sha"], proj_obj["project_id"], rel="committed_to")
                
    # Deployments
    for d in deployments:
        if d["linked_pr"] and d["linked_pr"] in G:
            G.add_edge(d["deployment_id"], d["linked_pr"], rel="deploys_pr")
        if d["linked_adr"] and d["linked_adr"] in G:
            G.add_edge(d["deployment_id"], d["linked_adr"], rel="deploys_adr")
            
    # Incidents
    for inc in incidents:
        if inc["linked_deployment"] and inc["linked_deployment"] in G:
            G.add_edge(inc["incident_id"], inc["linked_deployment"], rel="triggered_by_deployment")
        if inc["linked_adr"] and inc["linked_adr"] in G:
            G.add_edge(inc["incident_id"], inc["linked_adr"], rel="linked_to_adr")
        if inc["linked_pr"] and inc["linked_pr"] in G:
            G.add_edge(inc["incident_id"], inc["linked_pr"], rel="triggered_by_pr")
            
    # Customer support and feature requests
    for cust in customers:
        for st in cust["support_tickets"]:
            G.add_edge(st["ticket_id"], cust["customer_id"], rel="filed_by")
            if st["linked_incident"] and st["linked_incident"] in G:
                G.add_edge(st["ticket_id"], st["linked_incident"], rel="triggered_by_outage")
        for fr in cust["feature_requests"]:
            G.add_edge(fr["request_id"], cust["customer_id"], rel="requested_by")
            if fr["linked_jira"] and fr["linked_jira"] in G:
                G.add_edge(fr["request_id"], fr["linked_jira"], rel="linked_to_backlog")
                
    # Developer feedback
    for f in feedback:
        G.add_edge(f["feedback_id"], f["employee_id"], rel="submitted_by")
        G.add_edge(f["feedback_id"], f["project_id"], rel="about_project")
        if f["adr_id"] and f["adr_id"] in G:
            G.add_edge(f["feedback_id"], f["adr_id"], rel="about_adr")
            
    # Memories
    for m in memories:
        mem_id = f"MEM-{m['adr_id'].split('-')[1]}"
        G.add_edge(mem_id, m["adr_id"], rel="summarizes")
        
    return G

def generate_benchmark_questions(G: nx.DiGraph, num_questions: int):
    """
    Queries the NetworkX graph G to generate structured, solvable benchmark questions.
    """
    questions = []
    
    # Collect nodes of different types
    adrs = [n for n, attr in G.nodes(data=True) if attr.get("type") == "adr"]
    incidents = [n for n, attr in G.nodes(data=True) if attr.get("type") == "incident"]
    deployments = [n for n, attr in G.nodes(data=True) if attr.get("type") == "deployment"]
    prs = [n for n, attr in G.nodes(data=True) if attr.get("type") == "pr"]
    projects = [n for n, attr in G.nodes(data=True) if attr.get("type") == "project"]
    support_tickets = [n for n, attr in G.nodes(data=True) if attr.get("type") == "support_ticket"]
    memories = [n for n, attr in G.nodes(data=True) if attr.get("type") == "memory"]
    
    q_counter = 1
    
    # Helper to generate unique options
    def build_choices(correct_ans, distractor_pool, count=3):
        choices = [correct_ans]
        clean_distractors = [d for d in distractor_pool if d != correct_ans]
        choices.extend(random.sample(clean_distractors, min(len(clean_distractors), count)))
        random.shuffle(choices)
        
        letters = ["A", "B", "C", "D"]
        choice_dict = {letters[idx]: val for idx, val in enumerate(choices)}
        ans_letter = [k for k, v in choice_dict.items() if v == correct_ans][0]
        return choice_dict, ans_letter
        
    # We will loop and generate questions from templates
    while len(questions) < num_questions:
        q_type = random.randint(1, 6)
        
        if q_type == 1 and adrs:
            # 1. Rationale Lookup (factual)
            adr_node = random.choice(adrs)
            adr_data = G.nodes[adr_node]["data"]
            
            # Find the technology selected
            tech = adr_data.get("_tech_selected", "")
            if not tech:
                continue
                
            q_text = f"According to {adr_node}, why was {tech} selected?"
            correct_reason = adr_data["reason"]
            
            # Distractors from other ADR reasons
            other_reasons = [G.nodes[a]["data"]["reason"] for a in adrs if a != adr_node]
            if len(other_reasons) < 3:
                continue
                
            choices, ans = build_choices(correct_reason, other_reasons)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "factual",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": correct_reason,
                "ground_truth_path": {
                    "adr_id": adr_node
                }
            })
            q_counter += 1
            
        elif q_type == 2 and incidents:
            # 2. Causal Trace (causal): Which ADR is linked to the deployment that caused production incident INC-XXXX?
            inc_node = random.choice(incidents)
            inc_data = G.nodes[inc_node]["data"]
            
            dep_id = inc_data["linked_deployment"]
            if not dep_id or dep_id not in G:
                continue
                
            dep_data = G.nodes[dep_id]["data"]
            adr_id = dep_data["linked_adr"]
            
            if not adr_id:
                continue
                
            q_text = f"Which Architectural Decision Record (ADR) is linked to the production deployment ({dep_id}) that triggered incident {inc_node}?"
            
            # Distractors
            other_adrs = [a for a in adrs if a != adr_id]
            if len(other_adrs) < 3:
                continue
                
            choices, ans = build_choices(adr_id, other_adrs)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "causal",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": adr_id,
                "ground_truth_path": {
                    "incident_id": inc_node,
                    "deployment_id": dep_id,
                    "adr_id": adr_id
                }
            })
            q_counter += 1
            
        elif q_type == 3 and incidents:
            # 3. Fault Attribution (causal): Which Pull Request (PR) introduced the change that triggered incident INC-XXXX?
            inc_node = random.choice(incidents)
            inc_data = G.nodes[inc_node]["data"]
            
            pr_id = inc_data["linked_pr"]
            if not pr_id:
                continue
                
            q_text = f"Which GitHub Pull Request (PR) was merged, introducing the change that triggered production incident {inc_node}?"
            
            other_prs = [p for p in prs if p != pr_id]
            if len(other_prs) < 3:
                continue
                
            choices, ans = build_choices(pr_id, other_prs)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "causal",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": pr_id,
                "ground_truth_path": {
                    "incident_id": inc_node,
                    "pr_id": pr_id
                }
            })
            q_counter += 1
            
        elif q_type == 4 and projects:
            # 4. Performance Analytics (analytics): Which decision (ADR) reduced latency the most for a project?
            proj_node = random.choice(projects)
            proj_name = G.nodes[proj_node]["data"]["name"]
            
            # Find ADRs for this project that had latency reduction impact
            proj_adrs = [
                a for a in adrs 
                if G.nodes[a]["data"]["related_project"] == proj_node and
                   G.nodes[a]["data"]["_impact_metric"] == "latency" and
                   G.nodes[a]["data"]["_impact_direction"] == "decrease"
            ]
            
            if not proj_adrs:
                continue
                
            # Select the one with the maximum percentage impact value
            best_adr = max(proj_adrs, key=lambda a: G.nodes[a]["data"]["_impact_val"])
            best_val = G.nodes[best_adr]["data"]["_impact_val"]
            
            q_text = f"Which architectural decision (ADR) resulted in the largest planned latency reduction ({best_val}%) for the project {proj_name}?"
            
            other_adrs = [a for a in adrs if a != best_adr]
            if len(other_adrs) < 3:
                continue
                
            choices, ans = build_choices(best_adr, other_adrs)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "analytics",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": best_adr,
                "ground_truth_path": {
                    "project_id": proj_node,
                    "adr_id": best_adr
                }
            })
            q_counter += 1
            
        elif q_type == 5 and adrs:
            # 5. Structural Evolution (factual): Which decision later failed/was superseded?
            superseded = [a for a in adrs if G.nodes[a]["data"]["status"] in ["Superseded", "Deprecated"]]
            if not superseded:
                continue
                
            fail_adr = random.choice(superseded)
            status = G.nodes[fail_adr]["data"]["status"].lower()
            
            q_text = f"Which architectural decision (ADR) was later {status} due to scaling issues or technological transitions?"
            
            other_adrs = [a for a in adrs if G.nodes[a]["data"]["status"] == "Accepted"]
            if len(other_adrs) < 3:
                continue
                
            choices, ans = build_choices(fail_adr, other_adrs)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "factual",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": fail_adr,
                "ground_truth_path": {
                    "adr_id": fail_adr
                }
            })
            q_counter += 1
            
        elif q_type == 6 and support_tickets:
            # 6. Support Escalation (causal): Which support ticket was escalated due to outage INC-XXXX?
            st_node = random.choice(support_tickets)
            st_data = G.nodes[st_node]["data"]
            
            inc_id = st_data.get("linked_incident")
            if not inc_id:
                continue
                
            q_text = f"Which customer support ticket was created in response to the system outage identified as {inc_id}?"
            
            other_st = [s for s in support_tickets if s != st_node]
            if len(other_st) < 3:
                continue
                
            choices, ans = build_choices(st_node, other_st)
            
            questions.append({
                "question_id": f"Q-{q_counter:04d}",
                "category": "causal",
                "question": q_text,
                "choices": choices,
                "answer": ans,
                "answer_text": st_node,
                "ground_truth_path": {
                    "support_ticket_id": st_node,
                    "incident_id": inc_id
                }
            })
            q_counter += 1
            
    # Sort questions by ID
    questions.sort(key=lambda x: x["question_id"])
    return questions
