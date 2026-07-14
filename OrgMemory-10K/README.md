# OrgMemory-10K: Enterprise Memory Benchmark Dataset

OrgMemory-10K is a synthetically generated, fully relational, internally consistent enterprise software company's historical record spanning 5 years (2021–2025).

This dataset is designed specifically for benchmarking AI agents with persistent organizational memory (e.g., Hindsight) on tasks involving temporal, causal, structural, and factual reasoning over long-horizon corporate activities.

## Company Profile
- **Company Name:** NovaTech Solutions
- **Industry:** Enterprise SaaS
- **Products:** NovaCommerce, AtlasPay, InsightCRM, CloudSync, VisionAI, FusionERP
- **Repositories:** novacommerce-core, novacommerce-web, atlaspay-backend, atlaspay-frontend, insightcrm-core, insightcrm-web, cloudsync-core, cloudsync-apps, visionai-engine, fusionerp-monolith, platform-infra, security-tools

## Dataset Statistics
- **Scale Run:** LARGE
- **Employees:** 250
- **Projects:** 25
- **ADRs:** 500
- **Jira Tickets:** 5000
- **Commits:** 20028
- **PRs:** 2000
- **Deployments:** 750
- **Incidents:** 360
- **Meetings:** 510
- **Customers:** 200
- **Benchmark Questions:** 1000

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
python main.py --scale large --seed 42
```
