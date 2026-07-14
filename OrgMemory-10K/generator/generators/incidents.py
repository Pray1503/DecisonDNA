import random
from datetime import datetime, timedelta
from generator.config import INCIDENT_TEMPLATES

def generate_incidents(num_incidents: int, deployments: list, projects: list, adrs: list, pull_requests: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates production incidents triggered by deployments and links them to ADRs and PRs.
    """
    incidents = []
    
    # Filter production deployments to trigger incidents
    prod_deps = [d for d in deployments if d["environment"] == "production"]
    if not prod_deps:
        prod_deps = deployments  # Fallback
        
    # We want to make sure that a reasonable number of incidents are directly tied to ADRs
    # so we can benchmark AI capabilities in finding ADR-related failures.
    adr_deps = [d for d in prod_deps if d["linked_adr"] is not None]
    generic_deps = [d for d in prod_deps if d["linked_adr"] is None]
    
    # Mix of ADR-triggered and generic deployments
    target_count = min(num_incidents, len(prod_deps))
    selected_deps = adr_deps + random.sample(generic_deps, min(len(generic_deps), max(0, target_count - len(adr_deps))))
    
    # Sort selected deployments chronologically
    def get_dep_date(x):
        try:
            return datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.strptime(x["timestamp"], "%Y-%m-%d")
            
    selected_deps.sort(key=get_dep_date)
    
    for idx, dep in enumerate(selected_deps):
        inc_id = f"INC-{idx+1:04d}"
        dep_dt = get_dep_date(dep)
        
        # Link PR & ADR
        pr_id = dep["linked_pr"]
        adr_id = dep["linked_adr"]
        
        # Find project and tech details
        pr_obj = next((pr for pr in pull_requests if pr["pr_id"] == pr_id), None)
        proj_id = None
        if pr_obj:
            # Look up project by PR's Jira ticket
            jira_t_id = pr_obj["jira_ticket"]
            # Extract project key (e.g. NCA from NCA-12)
            p_key = jira_t_id.split("-")[0]
            proj_obj = next((p for p in projects if p["jira_project"]["key"] == p_key), None)
            if proj_obj:
                proj_id = proj_obj["project_id"]
                
        if not proj_id:
            # Fallback to random project
            proj_obj = random.choice(projects)
            proj_id = proj_obj["project_id"]
            
        proj_name = proj_obj["name"]
        
        # Select tech details for templates
        db_tech = next((t for t in proj_obj["technology_stack"] if t in ["PostgreSQL", "MongoDB", "Cassandra", "Oracle"]), "database")
        cache_tech = next((t for t in proj_obj["technology_stack"] if t in ["Redis", "Memcached"]), "Redis")
        mq_tech = next((t for t in proj_obj["technology_stack"] if t in ["Kafka", "RabbitMQ"]), "Kafka")
        
        # Pick template
        tmpl = random.choice(INCIDENT_TEMPLATES)
        
        # Fill details
        format_args = {
            "service_name": proj_name,
            "db_tech": db_tech,
            "cache_tech": cache_tech,
            "mq_tech": mq_tech,
            "mem_limit": random.choice(["1Gi", "2Gi", "512Mi"])
        }
        
        cause = tmpl["cause"].format(**format_args)
        root_cause = tmpl["root_cause"].format(**format_args)
        lessons = tmpl["lessons"].format(**format_args)
        severity = tmpl["severity"]
        
        # Timeline generation (Starts 5m to 2h after deployment)
        start_delay = random.randint(5, 120)
        detect_dt = dep_dt + timedelta(minutes=start_delay)
        ack_dt = detect_dt + timedelta(minutes=random.randint(2, 15))
        mitigate_dt = ack_dt + timedelta(minutes=random.randint(15, 90))
        resolve_dt = mitigate_dt + timedelta(minutes=random.randint(30, 240))
        
        timeline = [
            {"event": "System Alert - Anomalous Metrics Detected", "timestamp": detect_dt.strftime("%Y-%m-%d %H:%M:%S")},
            {"event": "On-call Engineer Acknowledged Alert", "timestamp": ack_dt.strftime("%Y-%m-%d %H:%M:%S")},
            {"event": f"Mitigation Applied - {random.choice(['Rolled back deployment', 'Increased pod count', 'Flushed cache'])}", "timestamp": mitigate_dt.strftime("%Y-%m-%d %H:%M:%S")},
            {"event": "Incident Resolved - System metrics stabilized", "timestamp": resolve_dt.strftime("%Y-%m-%d %H:%M:%S")}
        ]
        
        resolution = f"Applied mitigation at {mitigate_dt.strftime('%H:%M:%S')} by rolling back production deployment {dep['deployment_id']} or applying hotfix. Monitored CPU and error rates until they returned to baseline levels."
        
        incident = {
            "incident_id": inc_id,
            "cause": cause,
            "root_cause": root_cause,
            "severity": severity,
            "timeline": timeline,
            "resolution": resolution,
            "linked_deployment": dep["deployment_id"],
            "linked_pr": pr_id,
            "linked_adr": adr_id,
            "lessons_learned": lessons,
            
            # Internal helpers for metrics overlays
            "_detect_time": detect_dt,
            "_resolve_time": resolve_dt,
            "_project_name": proj_name
        }
        incidents.append(incident)
        
        # Link back to ADR
        if adr_id:
            adr_obj = next((a for a in adrs if a["adr_id"] == adr_id), None)
            if adr_obj:
                adr_obj["linked_incidents"].append(inc_id)
                # Update ADR outcome
                adr_obj["outcome"] = f"Deployed in {dep['deployment_id']}. Caused incident {inc_id} due to: {cause}. Rolled back or mitigated."
                
    # Sort by detection time
    incidents.sort(key=lambda x: x["_detect_time"])
    for idx, inc in enumerate(incidents):
        inc["incident_id"] = f"INC-{idx+1:04d}"
        
    return incidents

def write_incident_markdown_files(incidents: list, output_dir_path):
    """
    Writes each incident to its own markdown file in the incidents/ folder.
    """
    for inc in incidents:
        inc_id = inc["incident_id"]
        filepath = output_dir_path / "incidents" / f"{inc_id}.md"
        
        timeline_str = "\n".join([f"- **{evt['timestamp']}**: {evt['event']}" for evt in inc['timeline']])
        
        md_content = f"""# Incident Report: {inc_id} - {inc['cause']}

* **Severity:** {inc['severity']}
* **Linked Deployment:** {inc['linked_deployment']}
* **Linked PR:** {inc['linked_pr'] if inc['linked_pr'] else 'None'}
* **Linked ADR:** {inc['linked_adr'] if inc['linked_adr'] else 'None'}

## Root Cause Summary
{inc['root_cause']}

## Incident Timeline
{timeline_str}

## Resolution Details
{inc['resolution']}

## Lessons Learned
{inc['lessons_learned']}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
