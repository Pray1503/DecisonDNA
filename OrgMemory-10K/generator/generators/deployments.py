import random
from datetime import datetime, timedelta

def generate_deployments(num_deployments: int, pull_requests: list, adrs: list, seed_date=datetime(2021, 1, 1)):
    """
    Generates CI/CD deployment history linked to GitHub PRs and ADRs.
    """
    deployments = []
    
    # Filter merged PRs
    merged_prs = [pr for pr in pull_requests if pr["status"] == "Merged"]
    if not merged_prs:
        merged_prs = pull_requests  # Fallback
        
    # Sort merged PRs by merge time
    # (Handling formats like '2021-01-02 12:30:15' vs '2021-01-02')
    def get_pr_date(x):
        date_str = x["merged_at"] if x["merged_at"] else x["created_at"]
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.strptime(date_str, "%Y-%m-%d")
            
    merged_prs.sort(key=get_pr_date)
    
    # Generate deployments. We want to distribute them across the simulation window.
    # To reach the target count, we can deploy some PRs to Staging first, and then to Production.
    # This naturally doubles the deployment count for successful PRs.
    dep_counter = 1
    
    for pr in merged_prs:
        if dep_counter > num_deployments:
            break
            
        repo = pr["repository"]
        pr_id = pr["pr_id"]
        adr_id = pr["adr"]
        
        pr_merged_dt = get_pr_date(pr)
        
        # 1. Staging Deployment
        stage_dt = pr_merged_dt + timedelta(minutes=random.randint(5, 30))
        stage_status = random.choices(["Success", "Failed"], weights=[0.92, 0.08])[0]
        stage_duration = random.randint(60, 240)
        
        stage_dep_id = f"DEP-{dep_counter:04d}"
        dep_counter += 1
        
        stage_run = f"https://github.com/novatech-solutions/{repo}/actions/runs/{random.randint(10000, 99999)}"
        
        deployments.append({
            "deployment_id": stage_dep_id,
            "environment": "staging",
            "timestamp": stage_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline_run": stage_run,
            "duration_seconds": stage_duration,
            "status": stage_status,
            "rollback": False,
            "linked_pr": pr_id,
            "linked_adr": adr_id
        })
        
        # If staging failed, developer usually fixes it and redeploys
        if stage_status == "Failed":
            if dep_counter > num_deployments:
                break
            # Redeploy after 30-90 minutes
            stage_dt = stage_dt + timedelta(minutes=random.randint(30, 90))
            stage_status = "Success"
            stage_dep_id = f"DEP-{dep_counter:04d}"
            dep_counter += 1
            
            deployments.append({
                "deployment_id": stage_dep_id,
                "environment": "staging",
                "timestamp": stage_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "pipeline_run": stage_run,
                "duration_seconds": stage_duration + random.randint(-20, 20),
                "status": stage_status,
                "rollback": False,
                "linked_pr": pr_id,
                "linked_adr": adr_id
            })
            
        # 2. Production Deployment (only if staging succeeded)
        if stage_status == "Success":
            if dep_counter > num_deployments:
                break
                
            prod_dt = stage_dt + timedelta(hours=random.randint(1, 24))
            
            # Occasionally production deployments fail, leading to rollbacks
            prod_status = random.choices(["Success", "Failed"], weights=[0.95, 0.05])[0]
            prod_duration = random.randint(90, 360)
            rollback = True if prod_status == "Failed" else False
            
            prod_dep_id = f"DEP-{dep_counter:04d}"
            dep_counter += 1
            
            prod_run = f"https://github.com/novatech-solutions/{repo}/actions/runs/{random.randint(10000, 99999)}"
            
            prod_dep = {
                "deployment_id": prod_dep_id,
                "environment": "production",
                "timestamp": prod_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "pipeline_run": prod_run,
                "duration_seconds": prod_duration,
                "status": prod_status,
                "rollback": rollback,
                "linked_pr": pr_id,
                "linked_adr": adr_id
            }
            deployments.append(prod_dep)
            
            # Link back to PR
            pr["linked_deployment"] = prod_dep_id
            if adr_id:
                # Link to ADR
                adr_obj = next((a for a in adrs if a["adr_id"] == adr_id), None)
                if adr_obj:
                    adr_obj["linked_deployments"].append(prod_dep_id)
                    
    # Fill remaining deployments with generic dev environment/sandbox runs if counts are short
    while dep_counter <= num_deployments:
        days_offset = random.randint(0, 5 * 365)
        run_dt = seed_date + timedelta(days=days_offset)
        
        repo = random.choice(pull_requests)["repository"]
        
        deployments.append({
            "deployment_id": f"DEP-{dep_counter:04d}",
            "environment": "sandbox",
            "timestamp": run_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline_run": f"https://github.com/novatech-solutions/{repo}/actions/runs/{random.randint(10000, 99999)}",
            "duration_seconds": random.randint(30, 150),
            "status": random.choice(["Success", "Failed"]),
            "rollback": False,
            "linked_pr": None,
            "linked_adr": None
        })
        dep_counter += 1
        
    return deployments
