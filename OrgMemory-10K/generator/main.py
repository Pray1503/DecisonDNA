import os
import argparse
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add current directory to path to ensure relative imports work when executed directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.config import SCALES_CONFIG, COMPANY_NAME, INDUSTRY, DEPARTMENTS, PRODUCTS, REPOSITORIES
from generator.utils import (
    setup_seeds, create_output_directories, write_json, write_csv, write_yaml,
    write_markdown, copy_generator_code
)
from generator.generators.employees import generate_employees
from generator.generators.projects import generate_projects
from generator.generators.adr import generate_adrs, write_adr_markdown_files
from generator.generators.jira import generate_jira_tickets
from generator.generators.github import generate_github_data
from generator.generators.meetings import generate_meetings, write_meeting_markdown_files
from generator.generators.deployments import generate_deployments
from generator.generators.incidents import generate_incidents, write_incident_markdown_files
from generator.generators.monitoring import generate_system_metrics, write_incident_high_res_metrics
from generator.generators.feedback import generate_developer_feedback
from generator.generators.customers import generate_customers
from generator.generators.memory import compile_decision_memory
from generator.generators.graph import build_relationship_graph, generate_benchmark_questions

console = Console()

def main():
    parser = argparse.ArgumentParser(description="OrgMemory-10K: Synthetic Enterprise Dataset Generator")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="medium", help="Dataset size scale")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="OrgMemory-10K", help="Output directory path")
    args = parser.parse_args()
    
    # 1. Setup seeds
    setup_seeds(args.seed)
    
    # 2. Get scale config
    scale_cfg = SCALES_CONFIG[args.scale]
    
    console.print(f"[bold green]Starting OrgMemory-10K Generation Pipeline[/bold green]")
    console.print(f"Scale: [cyan]{args.scale.upper()}[/cyan] | Seed: [cyan]{args.seed}[/cyan]")
    console.print(f"Target Output Directory: [yellow]{args.output_dir}[/yellow]")
    
    # 3. Create folders
    out_dir = Path(args.output_dir)
    create_output_directories(out_dir)
    
    start_time = datetime.now()
    seed_date = datetime(2021, 1, 1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # --- Employees ---
        progress.add_task(description=f"Generating {scale_cfg['employees']} employees...", total=None)
        employees = generate_employees(scale_cfg["employees"], seed_date)
        write_json(employees, out_dir / "employees" / "employees.json")
        write_csv(employees, list(employees[0].keys()), out_dir / "employees" / "employees.csv")
        
        # --- Projects ---
        progress.add_task(description=f"Generating {scale_cfg['projects']} software projects...", total=None)
        projects = generate_projects(scale_cfg["projects"], employees, seed_date)
        write_json(projects, out_dir / "employees" / "projects.json") # Save projects metadata
        # Flat list for CSV
        proj_csv_data = []
        for p in projects:
            row = p.copy()
            row["jira_project_key"] = p["jira_project"]["key"]
            row["jira_project_name"] = p["jira_project"]["name"]
            row["start_date"] = p["timeline"]["start_date"]
            row["end_date"] = p["timeline"]["end_date"]
            del row["jira_project"]
            del row["timeline"]
            proj_csv_data.append(row)
        write_csv(proj_csv_data, list(proj_csv_data[0].keys()), out_dir / "employees" / "projects.csv")

        # --- Architecture Decision Records (ADRs) ---
        progress.add_task(description=f"Generating {scale_cfg['adrs']} ADRs...", total=None)
        adrs = generate_adrs(scale_cfg["adrs"], projects, employees, seed_date)
        
        # --- Jira Tickets ---
        progress.add_task(description=f"Generating {scale_cfg['jira_tickets']} Jira tickets...", total=None)
        jira_tickets = generate_jira_tickets(scale_cfg["jira_tickets"], projects, employees, adrs, seed_date)
        write_json(jira_tickets, out_dir / "jira" / "jira_tickets.json")
        write_csv(jira_tickets, list(jira_tickets[0].keys()), out_dir / "jira" / "jira_tickets.csv")
        
        # --- GitHub Data ---
        progress.add_task(description="Simulating GitHub repositories, commits, PRs, and releases...", total=None)
        pull_requests, commits, releases = generate_github_data(
            scale_cfg["pull_requests"], scale_cfg["commits"], scale_cfg["releases"],
            REPOSITORIES, projects, employees, jira_tickets, adrs, seed_date
        )
        write_json(pull_requests, out_dir / "github" / "pull_requests.json")
        write_json(commits, out_dir / "github" / "commits.json")
        write_json(releases, out_dir / "github" / "releases.json")
        write_csv(pull_requests, list(pull_requests[0].keys()), out_dir / "github" / "pull_requests.csv")
        write_csv(commits, list(commits[0].keys()), out_dir / "github" / "commits.csv")
        
        # --- Deployments ---
        progress.add_task(description=f"Generating {scale_cfg['deployments']} deployments...", total=None)
        deployments = generate_deployments(scale_cfg["deployments"], pull_requests, adrs, seed_date)
        write_json(deployments, out_dir / "deployments" / "deployments.json")
        write_csv(deployments, list(deployments[0].keys()), out_dir / "deployments" / "deployments.csv")
        
        # --- Incidents ---
        progress.add_task(description=f"Generating incidents...", total=None)
        # Note: incident count scales dynamically based on deployment volume, bounded by scale config
        incidents = generate_incidents(scale_cfg["incidents"], deployments, projects, adrs, pull_requests, seed_date)
        write_json(incidents, out_dir / "incidents" / "incidents.json")
        write_csv(incidents, [k for k in incidents[0].keys() if not k.startswith("_")], out_dir / "incidents" / "incidents.csv")
        write_incident_markdown_files(incidents, out_dir)
        
        # Write ADRs with all links resolved after generating Jiras/PRs/Incidents
        write_json(adrs, out_dir / "architecture" / "adrs.json")
        write_adr_markdown_files(adrs, out_dir)
        
        # --- Meetings ---
        progress.add_task(description=f"Generating {scale_cfg['meetings']} meetings...", total=None)
        # Link some meetings to incidents
        meetings = generate_meetings(scale_cfg["meetings"], projects, employees, adrs, jira_tickets, seed_date)
        # Randomly link incidents to non-ADR meetings as post-mortems
        non_adr_meets = [m for m in meetings if not m["linked_adr"]]
        for idx, inc in enumerate(incidents):
            if idx < len(non_adr_meets):
                non_adr_meets[idx]["linked_incident"] = inc["incident_id"]
                non_adr_meets[idx]["agenda"] = f"Post-Mortem: Outage {inc['incident_id']} - {inc['cause']}"
                non_adr_meets[idx]["discussion"] = f"Reviewing outage incident {inc['incident_id']} on {inc['_project_name']}. Root Cause: {inc['root_cause']}. Lessons learned: {inc['lessons_learned']}"
                non_adr_meets[idx]["decision"] = f"Resolve post-mortem tasks. Approved mitigation and preventative actions: {inc['lessons_learned']}"
                non_adr_meets[idx]["action_items"] = [f"Fix root cause in Jira task related to {inc['linked_pr']}", "Perform resilience testing on deployment pipelines"]
                
        write_json(meetings, out_dir / "meetings" / "meetings.json")
        write_meeting_markdown_files(meetings, out_dir)
        
        # --- Developer Feedback ---
        progress.add_task(description=f"Generating {scale_cfg['feedback']} developer feedback entries...", total=None)
        feedback = generate_developer_feedback(scale_cfg["feedback"], projects, employees, adrs, jira_tickets, seed_date)
        write_json(feedback, out_dir / "feedback" / "developer_feedback.json")
        write_csv(feedback, list(feedback[0].keys()), out_dir / "feedback" / "developer_feedback.csv")
        
        # --- Customers ---
        progress.add_task(description=f"Generating {scale_cfg['customers']} customers...", total=None)
        customers = generate_customers(scale_cfg["customers"], projects, incidents, jira_tickets, seed_date)
        write_json(customers, out_dir / "customers" / "customers.json")
        # Flat support tickets and feature requests CSVs
        sup_rows = []
        feat_rows = []
        for c in customers:
            for st in c["support_tickets"]:
                row = st.copy()
                row["customer_id"] = c["customer_id"]
                sup_rows.append(row)
            for fr in c["feature_requests"]:
                row = fr.copy()
                row["customer_id"] = c["customer_id"]
                feat_rows.append(row)
        if sup_rows:
            write_csv(sup_rows, list(sup_rows[0].keys()), out_dir / "customers" / "support_tickets.csv")
        if feat_rows:
            write_csv(feat_rows, list(feat_rows[0].keys()), out_dir / "customers" / "feature_requests.csv")
            
        # --- Metrics (Time-series) ---
        progress.add_task(description="Generating time-series system metrics and overlaying incident anomalies...", total=None)
        metrics = generate_system_metrics(projects, deployments, incidents, adrs, seed_date)
        write_json(metrics, out_dir / "monitoring" / "daily_system_metrics.json")
        write_csv(metrics, list(metrics[0].keys()), out_dir / "monitoring" / "daily_system_metrics.csv")
        write_incident_high_res_metrics(incidents, out_dir)
        
        # --- Hindsight Decision Memory ---
        progress.add_task(description="Compiling Decision Memory Objects (Hindsight)...", total=None)
        memories = compile_decision_memory(adrs, jira_tickets, pull_requests, deployments, incidents, metrics, out_dir)
        write_json(memories, out_dir / "hindsight" / "hindsight_memory.json")
        
        # --- Unified Graph & Benchmarks ---
        progress.add_task(description="Constructing graph and generating benchmark questions...", total=None)
        graph = build_relationship_graph(
            employees, projects, adrs, jira_tickets, pull_requests, commits,
            deployments, incidents, feedback, customers, memories
        )
        questions = generate_benchmark_questions(graph, scale_cfg["benchmark_questions"])
        write_json(questions, out_dir / "benchmark" / "questions.json")
        
        # Write metadata & config files
        progress.add_task(description="Writing final metadata and config configs...", total=None)
        
        # company_profile.json
        company_profile = {
            "company_name": COMPANY_NAME,
            "industry": INDUSTRY,
            "departments": DEPARTMENTS,
            "products": PRODUCTS,
            "repositories": REPOSITORIES,
            "simulation_period": "January 2021 - December 2025"
        }
        write_json(company_profile, out_dir / "company_profile.json")
        
        # generation_config.yaml
        gen_config = {
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scale": args.scale,
            "seed": args.seed,
            "parameters": scale_cfg
        }
        write_yaml(gen_config, out_dir / "generation_config.yaml")
        
        # dataset_info.json
        dataset_info = {
            "dataset_name": "OrgMemory-10K",
            "description": "Synthetic enterprise dataset representing a software company history over 5 years",
            "statistics": {
                "employees": len(employees),
                "projects": len(projects),
                "adrs": len(adrs),
                "jira_tickets": len(jira_tickets),
                "commits": len(commits),
                "pull_requests": len(pull_requests),
                "releases": len(releases),
                "deployments": len(deployments),
                "incidents": len(incidents),
                "meetings": len(meetings),
                "feedback_entries": len(feedback),
                "customers": len(customers),
                "support_tickets": len(sup_rows),
                "feature_requests": len(feat_rows),
                "benchmark_questions": len(questions)
            },
            "graph_metrics": {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges()
            }
        }
        write_json(dataset_info, out_dir / "dataset_info.json")
        
        # Copy generator code into the outputs
        copy_generator_code(Path(__file__).parent, out_dir)
        
        # Generate README.md
        readme_content = f"""# OrgMemory-10K: Enterprise Memory Benchmark Dataset

OrgMemory-10K is a synthetically generated, fully relational, internally consistent enterprise software company's historical record spanning 5 years (2021–2025).

This dataset is designed specifically for benchmarking AI agents with persistent organizational memory (e.g., Hindsight) on tasks involving temporal, causal, structural, and factual reasoning over long-horizon corporate activities.

## Company Profile
- **Company Name:** {COMPANY_NAME}
- **Industry:** {INDUSTRY}
- **Products:** {', '.join(PRODUCTS)}
- **Repositories:** {', '.join(REPOSITORIES)}

## Dataset Statistics
- **Scale Run:** {args.scale.upper()}
- **Employees:** {len(employees)}
- **Projects:** {len(projects)}
- **ADRs:** {len(adrs)}
- **Jira Tickets:** {len(jira_tickets)}
- **Commits:** {len(commits)}
- **PRs:** {len(pull_requests)}
- **Deployments:** {len(deployments)}
- **Incidents:** {len(incidents)}
- **Meetings:** {len(meetings)}
- **Customers:** {len(customers)}
- **Benchmark Questions:** {len(questions)}

## Repository Structure
- `/employees/`: Core staff list and organizational reporting hierarchy (JSON/CSV)
- `/architecture/`: Architecture Decision Records (ADRs) detailing decisions (Markdown/JSON)
- `/jira/`: Epics, Stories, Tasks, Spikes, and Bugs (JSON/CSV)
- `/github/`: Repository logs, commits, pull requests, and releases (JSON/CSV)
- `/meetings/`: Transcripts, decisions, and action items (Markdown/JSON)
- `/deployments/`: CI/CD logs, run statuses, and rollback flags (JSON/CSV)
- `/monitoring/`: Time-series performance metrics and incident-day hourly breakdowns (CSV)
- `/incidents/`: Outage root-cause analysis, timelines, and post-mortems (Markdown/JSON)
- `/feedback/`: Sprint retrospectives and survey opinions (JSON/CSV)
- `/customers/`: Support tickets, NPS scores, contract renewals, and feature requests (JSON)
- `/hindsight/`: Decision Memory Objects summarizing decision outcomes (Markdown/JSON)
- `/benchmark/`: Solvable multiple-choice question logs (JSON)
- `/generator/`: Self-contained generator Python scripts to re-generate the dataset

## Re-generating the Dataset
You can re-generate this dataset using the self-contained generator inside this folder:
```bash
cd generator
pip install -r requirements.txt
python main.py --scale {args.scale} --seed {args.seed}
```
"""
        write_markdown(readme_content, out_dir / "README.md")
        
    duration = datetime.now() - start_time
    console.print(f"[bold green]Dataset generation completed in {duration.total_seconds():.2f} seconds![/bold green]")
    console.print(f"Nodes in Unified Graph: [yellow]{graph.number_of_nodes()}[/yellow]")
    console.print(f"Edges in Unified Graph: [yellow]{graph.number_of_edges()}[/yellow]")
    console.print(f"Outputs written to: [blue]{out_dir.absolute()}[/blue]")

if __name__ == "__main__":
    main()
