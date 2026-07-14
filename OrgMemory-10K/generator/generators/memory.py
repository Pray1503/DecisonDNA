import random
from datetime import datetime, timedelta
import pandas as pd

def compile_decision_memory(adrs: list, jira_tickets: list, pull_requests: list, deployments: list, incidents: list, metrics_list: list, output_dir_path):
    """
    Synthesizes Hindsight Decision Memory Objects by aggregating data from ADRs, 
    Jira tickets, PRs, deployments, incidents, and daily metrics.
    Writes each consolidated memory to its own markdown file in hindsight/.
    """
    memories = []
    
    # Convert metrics list to DataFrame for easy analytical queries
    metrics_df = pd.DataFrame(metrics_list)
    
    for adr in adrs:
        adr_id = adr["adr_id"]
        adr_dt = datetime.strptime(adr["date"], "%Y-%m-%d")
        
        # 1. Implementation details
        linked_jiras = adr["linked_jira_tickets"]
        linked_prs = adr["linked_pull_requests"]
        linked_deps = adr["linked_deployments"]
        linked_incs = adr["linked_incidents"]
        linked_fdb = adr["linked_feedback"]
        
        # Find related commits
        linked_commits = []
        for pr_id in linked_prs:
            pr_obj = next((pr for pr in pull_requests if pr["pr_id"] == pr_id), None)
            if pr_obj:
                linked_commits.extend(pr_obj["commits"])
                
        # 2. Before/After Metric Analysis
        proj_id = adr["related_project"]
        metric_name = adr["_impact_metric"]
        
        before_val = "N/A"
        after_val = "N/A"
        metric_diff_str = "No baseline data available."
        
        if not metrics_df.empty and proj_id in metrics_df["project_id"].values:
            proj_metrics = metrics_df[metrics_df["project_id"] == proj_id].copy()
            proj_metrics["date"] = pd.to_datetime(proj_metrics["date"])
            
            # 30-day window
            window_before = proj_metrics[(proj_metrics["date"] >= adr_dt - timedelta(days=30)) & (proj_metrics["date"] < adr_dt)]
            window_after = proj_metrics[(proj_metrics["date"] > adr_dt) & (proj_metrics["date"] <= adr_dt + timedelta(days=30))]
            
            # Map metric key to CSV columns
            column_map = {
                "latency": "latency_ms",
                "availability": "availability_pct",
                "cost": "daily_cost_usd",
                "error_rate": "error_rate_pct"
            }
            
            col = column_map.get(metric_name)
            if col and not window_before.empty and not window_after.empty:
                avg_before = window_before[col].mean()
                avg_after = window_after[col].mean()
                
                unit = "ms" if metric_name == "latency" else ("%" if "pct" in col else " USD/day")
                before_val = f"{avg_before:.2f}{unit}"
                after_val = f"{avg_after:.2f}{unit}"
                
                diff = avg_after - avg_before
                pct_change = (diff / avg_before) * 100 if avg_before != 0 else 0
                
                sign = "+" if diff > 0 else ""
                metric_diff_str = f"Average {metric_name} went from {before_val} to {after_val} ({sign}{diff:.2f} / {sign}{pct_change:.1f}%)."
                
        # 3. Calculate Operational Confidence Score
        # Starts at 100, drops for each failure
        confidence = 1.0
        incident_failures = 0
        rollback_failures = 0
        
        for inc_id in linked_incs:
            inc_obj = next((inc for inc in incidents if inc["incident_id"] == inc_id), None)
            if inc_obj:
                severity = inc_obj["severity"]
                if severity == "P0":
                    confidence -= 0.3
                elif severity == "P1":
                    confidence -= 0.2
                else:
                    confidence -= 0.1
                incident_failures += 1
                
        for dep_id in linked_deps:
            dep_obj = next((d for d in deployments if d["deployment_id"] == dep_id), None)
            if dep_obj and dep_obj["rollback"]:
                confidence -= 0.15
                rollback_failures += 1
                
        confidence = max(0.1, round(confidence, 2))
        
        # 4. Version & Evolution History
        version = 1
        evolution = [
            {"date": adr["date"], "event": f"Decision formulated and accepted as {adr_id}."}
        ]
        
        if linked_jiras:
            evolution.append({"date": adr["date"], "event": f"Jira ticket {linked_jiras[0]} created for tracking implementation."})
            
        if linked_deps:
            # Get first deployment date
            first_dep = deployments[0]
            for dep in deployments:
                if dep["deployment_id"] in linked_deps:
                    first_dep = dep
                    break
            evolution.append({"date": first_dep["timestamp"].split(" ")[0], "event": f"Deployed to production in run {first_dep['deployment_id']}."})
            
        for inc_id in linked_incs:
            inc_obj = next((inc for inc in incidents if inc["incident_id"] == inc_id), None)
            if inc_obj:
                evolution.append({"date": inc_obj["_detect_time"].strftime("%Y-%m-%d"), "event": f"Alert! Caused production incident {inc_id} ({inc_obj['cause']})."})
                
        if adr["status"] == "Superseded":
            version = 2
            evolution.append({"date": (adr_dt + timedelta(days=365)).strftime("%Y-%m-%d"), "event": "This decision was superseded by a newer architectural standard due to scalability requirements."})
        elif adr["status"] == "Deprecated":
            version = 2
            evolution.append({"date": (adr_dt + timedelta(days=365)).strftime("%Y-%m-%d"), "event": "This decision was deprecated and the technology was decommissioned."})
            
        memory_obj = {
            "adr_id": adr_id,
            "title": adr["title"],
            "problem": adr["problem"],
            "context": adr["context"],
            "decision": adr["decision"],
            "alternatives": adr["alternatives"],
            "implementation": {
                "jira_tickets": linked_jiras,
                "pull_requests": linked_prs,
                "commits_count": len(linked_commits)
            },
            "deployments": linked_deps,
            "metrics_before_after": metric_diff_str,
            "incidents": linked_incs,
            "lessons_learned": adr["consequences"] + " " + adr["outcome"],
            "confidence_score": confidence,
            "memory_version": f"v{version}.0.0",
            "historical_evolution": evolution
        }
        
        memories.append(memory_obj)
        
        # Write to Markdown file
        mem_filepath = output_dir_path / "hindsight" / f"MEM-{adr_id.split('-')[1]}.md"
        
        evolution_md = "\n".join([f"- **{evt['date']}**: {evt['event']}" for evt in evolution])
        
        md_content = f"""# Decision Memory Object: MEM-{adr_id.split('-')[1]} ({adr['title']})

* **Original ADR:** [{adr_id}](../architecture/{adr_id}.md)
* **Status:** {adr['status']}
* **Memory Version:** v{version}.0.0
* **Operational Confidence Score:** {confidence:.2f} (Scale: 0.0 - 1.0)

## 1. Context and Problem
{adr['context']}

* **Problem Statement:** {adr['problem']}

## 2. Alternatives Considered
{adr['alternatives']}

## 3. Decision & Technical Direction
{adr['decision']}

## 4. Implementation Details
* **Jira Tickets:** {', '.join([f"`{j}`" for j in linked_jiras]) if linked_jiras else 'None'}
* **Pull Requests:** {', '.join([f"`{p}`" for p in linked_prs]) if linked_prs else 'None'}
* **Total Git Commits:** {len(linked_commits)}

## 5. Operations and Deployments
* **Deployments:** {', '.join([f"`{d}`" for d in linked_deps]) if linked_deps else 'None'}
* **Incidents Triggered:** {', '.join([f"`{i}`" for i in linked_incs]) if linked_incs else 'None'}

## 6. Real-world Performance Impact
{metric_diff_str}

## 7. Lessons Learned & Retrospective
{adr['consequences']}
{adr['outcome']}

## 8. Historical Evolution Timeline
{evolution_md}
"""
        with open(mem_filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
    return memories
