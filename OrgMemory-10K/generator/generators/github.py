import random
import hashlib
from datetime import datetime, timedelta

def generate_sha(seed_str: str):
    """Generates a pseudo-random git SHA hash from a seed string."""
    return hashlib.sha1(seed_str.encode('utf-8')).hexdigest()[:40]

def generate_github_data(
    num_pr: int, num_commits: int, num_releases: int,
    repositories: list, projects: list, employees: list, jira_tickets: list, adrs: list,
    seed_date=datetime(2021, 1, 1)
):
    """
    Generates GitHub repositories, commits, PRs, and releases, 
    linking them consistently to Jira tickets and ADRs.
    """
    pull_requests = []
    commits = []
    releases = []
    
    # Organize employees
    devs = [e for e in employees if e["department"] in ["Backend Engineering", "Frontend Engineering", "Platform Engineering", "AI Research", "DevOps", "Security"]]
    if not devs:
        devs = employees
        
    # Group Jira tickets by project
    jira_by_proj = {}
    for t in jira_tickets:
        p_id = t["project"]
        if p_id not in jira_by_proj:
            jira_by_proj[p_id] = []
        jira_by_proj[p_id].append(t)
        
    # Counter for PRs per repo
    repo_pr_counters = {r: 1 for r in repositories}
    # Track releases per repo
    repo_release_counters = {r: 1 for r in repositories}
    
    # We will generate PRs by mapping them to Jira tickets that are resolved or in progress
    valid_tickets = [t for t in jira_tickets if t["status"] in ["Done", "In Progress"]]
    # Sort by created date so we process chronologically
    valid_tickets.sort(key=lambda x: x["created_date"])
    
    if not valid_tickets:
        valid_tickets = jira_tickets
        
    # 1. Generate Pull Requests
    num_pr_to_gen = min(num_pr, len(valid_tickets))
    
    # We want to make sure ADR-related Jira tickets definitely get PRs
    adr_tickets = [t for t in valid_tickets if t["adr"] is not None]
    generic_tickets = [t for t in valid_tickets if t["adr"] is None]
    
    # Prioritize ADR tickets, then fill with generic ones
    selected_tickets = random.sample(adr_tickets, min(len(adr_tickets), num_pr_to_gen)) + random.sample(generic_tickets, min(len(generic_tickets), max(0, num_pr_to_gen - len(adr_tickets))))
    
    # Ensure they are sorted chronologically by ticket creation date
    selected_tickets.sort(key=lambda x: x["created_date"])
    
    # Distribute commits to be generated across PRs
    # Average commits per PR = total_commits / total_prs
    avg_commits_per_pr = max(1, num_commits // len(selected_tickets))
    
    commit_idx = 1
    
    for idx, ticket in enumerate(selected_tickets):
        proj_id = ticket["project"]
        proj = next((p for p in projects if p["project_id"] == proj_id), projects[0])
        repo = proj["repository"]
        p_key = proj["jira_project"]["key"]
        
        pr_global_id = f"PR-{idx+1:04d}"
        pr_number = repo_pr_counters[repo]
        repo_pr_counters[repo] += 1
        
        # Dates based on ticket creation
        t_created = datetime.strptime(ticket["created_date"], "%Y-%m-%d")
        
        # Commit dates are slightly after ticket creation but before PR merge
        # PR is created 1-3 days after ticket creation
        pr_created_dt = t_created + timedelta(days=random.randint(1, 3))
        
        if ticket["resolved_date"]:
            pr_merged_dt = datetime.strptime(ticket["resolved_date"], "%Y-%m-%d")
            # Enforce merged_dt > created_dt
            if pr_merged_dt <= pr_created_dt:
                pr_merged_dt = pr_created_dt + timedelta(days=random.randint(1, 4))
            status = "Merged"
        else:
            pr_merged_dt = None
            status = random.choice(["Open", "Closed"])
            
        # Reviewer: Another dev from the same team or department
        eligible_reviewers = [e["employee_id"] for e in devs if e["employee_id"] != ticket["owner"] and (e["team"] == proj["team"] or e["department"] == proj["team"])]
        if not eligible_reviewers:
            eligible_reviewers = [e["employee_id"] for e in devs if e["employee_id"] != ticket["owner"]]
        if not eligible_reviewers:
            eligible_reviewers = [employees[0]["employee_id"]]
            
        reviewer = random.choice(eligible_reviewers)
        
        # Generate commits for this PR
        pr_commits = []
        num_pr_commits = random.randint(max(1, avg_commits_per_pr - 3), avg_commits_per_pr + 3)
        num_pr_commits = max(1, num_pr_commits)
        
        # Get author details
        author_emp = next((e for e in employees if e["employee_id"] == ticket["owner"]), employees[0])
        author_github = author_emp["github_username"]
        
        for c_num in range(num_pr_commits):
            sha = generate_sha(f"commit_{commit_idx}_{pr_global_id}")
            commit_idx += 1
            
            c_date = pr_created_dt - timedelta(hours=random.randint(0, 48))
            
            # Commit message
            if ticket["adr"]:
                c_msg = f"feat({proj['name']}): implement decision from {ticket['adr']} - step {c_num+1}"
            else:
                c_msg = f"{random.choice(['feat', 'fix', 'refactor', 'docs', 'chore'])}({proj['name']}): {ticket['title'].lower()}"
                
            commit_obj = {
                "commit_sha": sha,
                "author": author_github,
                "message": c_msg,
                "date": c_date.strftime("%Y-%m-%d %H:%M:%S"),
                "repository": repo,
                "pull_request": pr_global_id
            }
            commits.append(commit_obj)
            pr_commits.append(sha)
            
        # ADR ID
        adr_id = ticket["adr"]
        
        # Assemble PR
        pr = {
            "pr_id": pr_global_id,
            "pr_number": pr_number,
            "repository": repo,
            "title": f"Resolve {ticket['ticket_id']}: {ticket['title']}",
            "status": status,
            "author": author_github,
            "reviewer": next((e["github_username"] for e in employees if e["employee_id"] == reviewer), "reviewer-github"),
            "jira_ticket": ticket["ticket_id"],
            "adr": adr_id,
            "created_at": pr_created_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "merged_at": pr_merged_dt.strftime("%Y-%m-%d %H:%M:%S") if pr_merged_dt else None,
            "commits": pr_commits,
            "linked_deployment": None # Will link during deployment phase
        }
        
        pull_requests.append(pr)
        
        # Link back to ADR if it exists
        if adr_id:
            adr_obj = next((a for a in adrs if a["adr_id"] == adr_id), None)
            if adr_obj:
                adr_obj["linked_pull_requests"].append(pr_global_id)
                
    # 2. Generate remaining commits (some direct merges, docs, chores)
    while len(commits) < num_commits:
        repo = random.choice(repositories)
        sha = generate_sha(f"commit_direct_{commit_idx}")
        commit_idx += 1
        
        days_offset = random.randint(0, 5 * 365)
        c_date = seed_date + timedelta(days=days_offset)
        
        author = random.choice(devs)
        
        commits.append({
            "commit_sha": sha,
            "author": author["github_username"],
            "message": f"chore({repo}): sync repository and update CI scripts",
            "date": c_date.strftime("%Y-%m-%d %H:%M:%S"),
            "repository": repo,
            "pull_request": None
        })
        
    # 3. Generate Releases
    # Group PRs by repository
    prs_by_repo = {r: [] for r in repositories}
    for pr in pull_requests:
        if pr["status"] == "Merged":
            prs_by_repo[pr["repository"]].append(pr)
            
    # Generate releases per repository
    for repo, repo_prs in prs_by_repo.items():
        # Sort merged PRs by merge date
        repo_prs.sort(key=lambda x: x["merged_at"])
        
        # Pack PRs into releases
        # E.g. every 4 merged PRs make a release
        chunk_size = max(2, len(repo_prs) // (num_releases // len(repositories) + 1))
        
        for k in range(0, len(repo_prs), chunk_size):
            chunk = repo_prs[k:k+chunk_size]
            if not chunk:
                continue
                
            r_num = repo_release_counters[repo]
            repo_release_counters[repo] += 1
            
            # Release tag and date
            latest_pr_merge = max([datetime.strptime(pr["merged_at"], "%Y-%m-%d %H:%M:%S") for pr in chunk])
            release_dt = latest_pr_merge + timedelta(hours=random.randint(2, 24))
            
            tag = f"v{r_num // 5}.{r_num % 5}.0"
            r_id = f"REL-{repo.upper()}-{r_num:03d}"
            
            release_obj = {
                "release_id": r_id,
                "repository": repo,
                "tag_name": tag,
                "name": f"Release {tag} - stable build",
                "published_at": release_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "linked_prs": [pr["pr_id"] for pr in chunk],
                "description": f"Contains fixes and features for {repo}:\n" + "\n".join([f"- {pr['title']} ({pr['pr_id']})" for pr in chunk])
            }
            releases.append(release_obj)
            
    return pull_requests, commits, releases
