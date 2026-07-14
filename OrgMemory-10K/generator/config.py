import os

# Company Profile
COMPANY_NAME = "NovaTech Solutions"
INDUSTRY = "Enterprise SaaS"

DEPARTMENTS = [
    "Backend Engineering",
    "Frontend Engineering",
    "Platform Engineering",
    "AI Research",
    "DevOps",
    "Security",
    "Product",
    "Customer Success"
]

PRODUCTS = [
    "NovaCommerce",
    "AtlasPay",
    "InsightCRM",
    "CloudSync",
    "VisionAI",
    "FusionERP"
]

TEAMS = {
    "Backend Engineering": ["Core Commerce", "Payments Platform", "CRM Backend", "Storage Engine", "ERP Core"],
    "Frontend Engineering": ["Commerce Frontend", "Portal Frontend", "CRM Web", "Desktop Sync Frontend", "ERP UI"],
    "Platform Engineering": ["Infra Foundations", "Database Reliability", "Network Mesh"],
    "AI Research": ["Vision Intelligence", "Training Pipelines"],
    "DevOps": ["Developer Platform", "Observability Operations"],
    "Security": ["SecOps", "Identity & Access Management"],
    "Product": ["Commerce Product", "FinTech Product", "SaaS Analytics Product"],
    "Customer Success": ["Enterprise Support Team A", "Enterprise Support Team B"]
}

# 12 GitHub Repositories
REPOSITORIES = [
    "novacommerce-core",
    "novacommerce-web",
    "atlaspay-backend",
    "atlaspay-frontend",
    "insightcrm-core",
    "insightcrm-web",
    "cloudsync-core",
    "cloudsync-apps",
    "visionai-engine",
    "fusionerp-monolith",
    "platform-infra",
    "security-tools"
]

# 25 Software Projects and their mapping
PROJECTS_CONFIG = [
    {"project_id": "PRJ-001", "name": "novacommerce-api", "repo": "novacommerce-core", "tech": ["Go", "PostgreSQL", "Redis"], "dept": "Backend Engineering", "team": "Core Commerce"},
    {"project_id": "PRJ-002", "name": "novacommerce-ui", "repo": "novacommerce-web", "tech": ["React", "Next.js", "TailwindCSS"], "dept": "Frontend Engineering", "team": "Commerce Frontend"},
    {"project_id": "PRJ-003", "name": "novacommerce-cart", "repo": "novacommerce-core", "tech": ["Node.js", "Redis"], "dept": "Backend Engineering", "team": "Core Commerce"},
    {"project_id": "PRJ-004", "name": "novacommerce-checkout", "repo": "novacommerce-core", "tech": ["Go", "Kafka"], "dept": "Backend Engineering", "team": "Core Commerce"},
    {"project_id": "PRJ-005", "name": "atlaspay-gateway", "repo": "atlaspay-backend", "tech": ["Go", "PostgreSQL", "Kafka"], "dept": "Backend Engineering", "team": "Payments Platform"},
    {"project_id": "PRJ-006", "name": "atlaspay-ledger", "repo": "atlaspay-backend", "tech": ["Go", "PostgreSQL", "Cassandra"], "dept": "Backend Engineering", "team": "Payments Platform"},
    {"project_id": "PRJ-007", "name": "atlaspay-portal", "repo": "atlaspay-frontend", "tech": ["React", "TypeScript", "Vite"], "dept": "Frontend Engineering", "team": "Portal Frontend"},
    {"project_id": "PRJ-008", "name": "insightcrm-api", "repo": "insightcrm-core", "tech": ["Python", "FastAPI", "MongoDB"], "dept": "Backend Engineering", "team": "CRM Backend"},
    {"project_id": "PRJ-009", "name": "insightcrm-ui", "repo": "insightcrm-web", "tech": ["React", "Vite"], "dept": "Frontend Engineering", "team": "CRM Web"},
    {"project_id": "PRJ-010", "name": "insightcrm-analytics", "repo": "insightcrm-core", "tech": ["Python", "Spark", "Redis"], "dept": "Backend Engineering", "team": "CRM Backend"},
    {"project_id": "PRJ-011", "name": "cloudsync-daemon", "repo": "cloudsync-core", "tech": ["Go", "gRPC"], "dept": "Platform Engineering", "team": "Storage Engine"},
    {"project_id": "PRJ-012", "name": "cloudsync-storage", "repo": "cloudsync-core", "tech": ["Go", "S3", "Cassandra"], "dept": "Platform Engineering", "team": "Storage Engine"},
    {"project_id": "PRJ-013", "name": "cloudsync-desktop", "repo": "cloudsync-apps", "tech": ["Electron", "React", "TypeScript"], "dept": "Frontend Engineering", "team": "Desktop Sync Frontend"},
    {"project_id": "PRJ-014", "name": "visionai-inference", "repo": "visionai-engine", "tech": ["Python", "PyTorch", "C++", "gRPC"], "dept": "AI Research", "team": "Vision Intelligence"},
    {"project_id": "PRJ-015", "name": "visionai-training", "repo": "visionai-engine", "tech": ["Python", "PyTorch", "CUDA"], "dept": "AI Research", "team": "Training Pipelines"},
    {"project_id": "PRJ-016", "name": "visionai-pipeline", "repo": "visionai-engine", "tech": ["Go", "Kafka", "S3"], "dept": "Platform Engineering", "team": "Infra Foundations"},
    {"project_id": "PRJ-017", "name": "fusionerp-core", "repo": "fusionerp-monolith", "tech": ["Java", "Spring Boot", "Oracle"], "dept": "Backend Engineering", "team": "ERP Core"},
    {"project_id": "PRJ-018", "name": "fusionerp-payroll", "repo": "fusionerp-monolith", "tech": ["Java", "Spring Boot", "PostgreSQL"], "dept": "Backend Engineering", "team": "ERP Core"},
    {"project_id": "PRJ-019", "name": "fusionerp-frontend", "repo": "fusionerp-monolith", "tech": ["Angular", "TypeScript"], "dept": "Frontend Engineering", "team": "ERP UI"},
    {"project_id": "PRJ-020", "name": "platform-k8s-mesh", "repo": "platform-infra", "tech": ["Terraform", "Kubernetes", "Istio", "AWS"], "dept": "Platform Engineering", "team": "Network Mesh"},
    {"project_id": "PRJ-021", "name": "platform-logging", "repo": "platform-infra", "tech": ["Elasticsearch", "Logstash", "Kibana", "AWS"], "dept": "DevOps", "team": "Observability Operations"},
    {"project_id": "PRJ-022", "name": "platform-monitoring", "repo": "platform-infra", "tech": ["Prometheus", "Grafana", "AWS"], "dept": "DevOps", "team": "Observability Operations"},
    {"project_id": "PRJ-023", "name": "security-auth-proxy", "repo": "security-tools", "tech": ["Go", "OAuth2", "Redis", "OIDC"], "dept": "Security", "team": "Identity & Access Management"},
    {"project_id": "PRJ-024", "name": "security-scanner", "repo": "security-tools", "tech": ["Python", "Static Analysis", "Docker"], "dept": "Security", "team": "SecOps"},
    {"project_id": "PRJ-025", "name": "devops-ci-cd", "repo": "platform-infra", "tech": ["GitHub Actions", "Python", "Docker"], "dept": "DevOps", "team": "Developer Platform"}
]

# Scale Settings Mapping
SCALES_CONFIG = {
    "small": {
        "employees": 25,
        "projects": 5,
        "adrs": 50,
        "jira_tickets": 500,
        "commits": 2000,
        "pull_requests": 200,
        "releases": 50,
        "meetings": 50,
        "deployments": 75,
        "incidents": 20,
        "feedback": 500,
        "customers": 20,
        "benchmark_questions": 100
    },
    "medium": {
        "employees": 100,
        "projects": 12,
        "adrs": 200,
        "jira_tickets": 2000,
        "commits": 8000,
        "pull_requests": 800,
        "releases": 200,
        "meetings": 200,
        "deployments": 300,
        "incidents": 50,
        "feedback": 2000,
        "customers": 80,
        "benchmark_questions": 400
    },
    "large": {
        "employees": 250,
        "projects": 25,
        "adrs": 500,
        "jira_tickets": 5000,
        "commits": 20000,
        "pull_requests": 2000,
        "releases": 500,
        "meetings": 500,
        "deployments": 750,
        "incidents": 1000,
        "feedback": 5000,
        "customers": 200,
        "benchmark_questions": 1000
    }
}

# Roles and Salaries
ROLES = {
    "Backend Engineering": [
        {"role": "Junior Backend Engineer", "salary_band": "L1 ($80k-$100k)", "experience": "1-3 years"},
        {"role": "Backend Engineer", "salary_band": "L2 ($110k-$140k)", "experience": "3-6 years"},
        {"role": "Senior Backend Engineer", "salary_band": "L3 ($150k-$190k)", "experience": "6-10 years"},
        {"role": "Staff Backend Engineer", "salary_band": "L4 ($200k-$250k)", "experience": "10+ years"}
    ],
    "Frontend Engineering": [
        {"role": "Junior Frontend Engineer", "salary_band": "L1 ($75k-$95k)", "experience": "1-3 years"},
        {"role": "Frontend Engineer", "salary_band": "L2 ($105k-$135k)", "experience": "3-6 years"},
        {"role": "Senior Frontend Engineer", "salary_band": "L3 ($145k-$180k)", "experience": "6-10 years"},
        {"role": "Staff Frontend Engineer", "salary_band": "L4 ($190k-$240k)", "experience": "10+ years"}
    ],
    "Platform Engineering": [
        {"role": "Site Reliability Engineer", "salary_band": "L2 ($115k-$145k)", "experience": "3-6 years"},
        {"role": "Senior SRE", "salary_band": "L3 ($155k-$195k)", "experience": "6-10 years"},
        {"role": "Staff SRE", "salary_band": "L4 ($210k-$260k)", "experience": "10+ years"}
    ],
    "AI Research": [
        {"role": "AI Researcher", "salary_band": "L2 ($120k-$150k)", "experience": "3-6 years"},
        {"role": "Senior AI Researcher", "salary_band": "L3 ($165k-$210k)", "experience": "6-10 years"},
        {"role": "Principal AI Scientist", "salary_band": "L4 ($230k-$300k)", "experience": "10+ years"}
    ],
    "DevOps": [
        {"role": "DevOps Engineer", "salary_band": "L2 ($110k-$140k)", "experience": "3-6 years"},
        {"role": "Senior DevOps Engineer", "salary_band": "L3 ($150k-$190k)", "experience": "6-10 years"},
        {"role": "Principal DevOps Architect", "salary_band": "L4 ($200k-$250k)", "experience": "10+ years"}
    ],
    "Security": [
        {"role": "Security Analyst", "salary_band": "L1 ($85k-$105k)", "experience": "1-3 years"},
        {"role": "Security Engineer", "salary_band": "L2 ($115k-$145k)", "experience": "3-6 years"},
        {"role": "Senior Security Engineer", "salary_band": "L3 ($160k-$200k)", "experience": "6-10 years"},
        {"role": "Staff Security Architect", "salary_band": "L4 ($215k-$265k)", "experience": "10+ years"}
    ],
    "Product": [
        {"role": "Associate Product Manager", "salary_band": "L1 ($80k-$100k)", "experience": "1-3 years"},
        {"role": "Product Manager", "salary_band": "L2 ($115k-$145k)", "experience": "3-6 years"},
        {"role": "Senior Product Manager", "salary_band": "L3 ($155k-$195k)", "experience": "6-10 years"},
        {"role": "Director of Product", "salary_band": "L4 ($220k-$280k)", "experience": "10+ years"}
    ],
    "Customer Success": [
        {"role": "CS Associate", "salary_band": "L1 ($55k-$75k)", "experience": "1-3 years"},
        {"role": "CS Manager", "salary_band": "L2 ($80k-$105k)", "experience": "3-6 years"},
        {"role": "Senior CS Manager", "salary_band": "L3 ($110k-$140k)", "experience": "6-10 years"}
    ]
}

SKILLS_BY_DEPT = {
    "Backend Engineering": ["Go", "Python", "Java", "PostgreSQL", "Redis", "Kafka", "Docker", "gRPC", "Microservices", "REST APIs", "Cassandra", "SQL", "Elasticsearch"],
    "Frontend Engineering": ["React", "TypeScript", "JavaScript", "HTML", "CSS", "Vite", "Next.js", "Angular", "Electron", "TailwindCSS", "Redux", "GraphQL"],
    "Platform Engineering": ["Kubernetes", "Terraform", "AWS", "Docker", "Istio", "Networking", "Linux", "CI/CD", "Cassandra", "Cloud Security", "S3"],
    "AI Research": ["Python", "PyTorch", "TensorFlow", "CUDA", "LLMs", "Machine Learning", "Neural Networks", "NLP", "Computer Vision", "scikit-learn", "NumPy"],
    "DevOps": ["Docker", "Kubernetes", "Prometheus", "Grafana", "Kibana", "Elasticsearch", "GitHub Actions", "Jenkins", "Ansible", "Linux", "Python", "Shell Scripting"],
    "Security": ["Cryptography", "OAuth2", "OIDC", "Penetration Testing", "Security Compliance", "Vulnerability Auditing", "IAM", "TLS/SSL", "Docker Security"],
    "Product": ["Product Strategy", "User Research", "Agile", "Scrum", "Data Analytics", "Roadmapping", "A/B Testing", "Customer Feedback Analysis"],
    "Customer Success": ["Customer Relations", "Technical Troubleshooting", "Salesforce", "Communication", "Conflict Resolution", "SLA Management", "SQL"]
}

# Template data for ADR categories, problems, templates
ADR_TEMPLATES = [
    {
        "title_template": "Adopt {database} for {service} database storage",
        "tags": ["database", "storage", "backend"],
        "context": "Our current database strategy for {service} is experiencing scalability limitations under peak loads. We need a solution that can handle high throughput, support strong consistency, and scale horizontally.",
        "problem": "High read/write latency during peak traffic periods resulting in database connection pools exhausting, causing intermittent errors in downstream services.",
        "alternatives": "1. Scale vertical resources on existing systems.\n2. Implement a distributed cache layer (e.g. Redis) as a buffer.\n3. Migrate to a multi-master distributed DB like {database}.",
        "decision": "Migrate the primary storage of {service} to {database} to leverage its native scaling and high availability features.",
        "reason": "We chose {database} because of its robust clustering capabilities, low latency reads, and strong developer familiarity. It provides the required performance profile and matches our tech stack.",
        "consequences": "Developers must learn {database}-specific query optimization. We must set up migration scripts and operational monitoring for the new clusters.",
        "expected_benefits": "Reduced query latency by 50%, elimination of connection pool exhaustion incidents, and support for 5x current transaction volume.",
        "potential_risks": "Complexity of live migration, operational overhead of maintaining clusters, and potential data format conversion issues during the transition.",
        "impact_metric": "latency",
        "impact_direction": "decrease",
        "impact_val": 45
    },
    {
        "title_template": "Introduce {message_queue} for decoupled communications in {service}",
        "tags": ["message-queue", "architecture", "decoupling"],
        "context": "Direct HTTP calls between {service} and other services create hard dependencies. When downstream systems are down, transactions fail immediately, causing poor customer experience.",
        "problem": "Tight coupling leads to cascading failures across the backend. We need asynchronous messaging to guarantee eventual consistency and fault tolerance.",
        "alternatives": "1. Keep synchronous REST APIs but increase timeouts and retry limits.\n2. Introduce an HTTP webhook callback system.\n3. Deploy {message_queue} as a centralized event broker.",
        "decision": "Integrate {message_queue} to enable asynchronous, event-driven communication between {service} and downstream microservices.",
        "reason": "By utilizing {message_queue}, we can queue tasks and process them asynchronously, absorbing sudden traffic spikes without affecting the main API transaction loop.",
        "consequences": "Requires handling out-of-order execution, ensuring message idempotency in processors, and setting up telemetry for queue lags.",
        "expected_benefits": "Cascading failures are avoided; service availability increases to 99.99%; peak traffic load is smoothed.",
        "potential_risks": "Introducing a single point of failure (event broker), message duplication, and increased complexity in tracing requests end-to-end.",
        "impact_metric": "availability",
        "impact_direction": "increase",
        "impact_val": 0.05
    },
    {
        "title_template": "Implement {caching_layer} cache layer for {service}",
        "tags": ["cache", "performance", "scaling"],
        "context": "{service} performs heavy database reads for static or slow-moving configurations, putting unnecessary read load on our primary databases and increasing endpoint latency.",
        "problem": "High load on databases and slow API responses due to repeated queries for the same static configuration and user profile data.",
        "alternatives": "1. Add read replicas to the primary database.\n2. Use in-memory application caching.\n3. Deploy a centralized {caching_layer} caching cluster.",
        "decision": "Implement {caching_layer} as a distributed caching layer for {service} endpoints.",
        "reason": "A centralized {caching_layer} cluster allows shared cache across all horizontal pods of the service, keeping memory usage clean and providing sub-millisecond lookups.",
        "consequences": "Cache invalidation logic must be added to all update operations. Cache eviction policies (LRU) must be configured.",
        "expected_benefits": "Endpoint latency reduced by up to 80%; database read IOPS reduced by 60%.",
        "potential_risks": "Stale cache read anomalies, cache stampede during cold start, and additional cluster infrastructure costs.",
        "impact_metric": "latency",
        "impact_direction": "decrease",
        "impact_val": 60
    },
    {
        "title_template": "Use {container_orchestration} to deploy {service} to AWS",
        "tags": ["deployment", "infrastructure", "devops"],
        "context": "Our current deployment model using manual VM provisioning is slow, error-prone, and makes scaling applications dynamically very difficult during high load.",
        "problem": "Deployment takes over 40 minutes, and we lack auto-scaling. Small configuration drift on VMs makes debugging environments difficult.",
        "alternatives": "1. Script VM creation using custom Ansible and AMI images.\n2. Deploy directly to AWS ECS.\n3. Implement a complete {container_orchestration} container orchestration architecture.",
        "decision": "Standardize all microservice deployments, starting with {service}, on {container_orchestration} hosted on AWS.",
        "reason": "{container_orchestration} provides declarative configuration, auto-healing, and dynamic horizontal pod autoscaling (HPA) natively.",
        "consequences": "All services must be containerized (Dockerfiles written). Helm charts must be created, and CI/CD pipelines updated.",
        "expected_benefits": "Deployment time down from 40m to under 5m; auto-scaling responds to traffic load in under 2m.",
        "potential_risks": "Steep learning curve for the team, complex networking policies, and increased infrastructure cost for the control plane.",
        "impact_metric": "cost",
        "impact_direction": "increase",
        "impact_val": 15
    },
    {
        "title_template": "Migrate {service} frontend architecture to {frontend_framework}",
        "tags": ["frontend", "framework", "performance"],
        "context": "The legacy user interface of {service} is written in a monolithic, unmaintained framework. It leads to slow page loads, poor SEO, and difficulty in writing modern components.",
        "problem": "Bundle size is too large (5MB+), page interactive time (TTI) is over 6 seconds, and developers find it slow to build features.",
        "alternatives": "1. Refactor the existing legacy code and optimize bundle sizes.\n2. Migrate to Vanilla JS and web components.\n3. Rebuild the frontend using {frontend_framework}.",
        "decision": "Rebuild and migrate the UI for {service} to {frontend_framework}.",
        "reason": "{frontend_framework} offers Server-Side Rendering (SSR) / Static Site Generation (SSG), excellent component ecosystem, and faster developer onboarding.",
        "consequences": "Full frontend rewrite is needed. Existing component libraries must be recreated or migrated.",
        "expected_benefits": "First Contentful Paint (FCP) improved from 4s to 1.2s; developer velocity increased.",
        "potential_risks": "Delays in feature parity during migration, state management refactoring challenges, and framework updates overhead.",
        "impact_metric": "latency",
        "impact_direction": "decrease",
        "impact_val": 35
    }
]

DB_OPTIONS = ["PostgreSQL", "MongoDB", "Cassandra", "DynamoDB", "MySQL"]
MQ_OPTIONS = ["Kafka", "RabbitMQ", "AWS SQS", "NATS"]
CACHE_OPTIONS = ["Redis", "Memcached"]
ORCHESTRATION_OPTIONS = ["Kubernetes", "AWS ECS", "Nomad"]
FRONTEND_OPTIONS = ["React / Next.js", "Vue.js", "Angular", "Svelte"]

# Incident Templates
INCIDENT_TEMPLATES = [
    {
        "cause": "Database connection pool exhaustion on {service_name}",
        "root_cause": "The service connection pool size was set to 20, but under heavy concurrent traffic, queries blocked on {db_tech}, causing requests to queue up and exhaust all worker threads. The health check endpoint also blocked, leading Kubernetes to restart pods in a loop.",
        "lessons": "We must decoupled health check endpoints from primary database checks (make them shallow), increase connection pool limits, and implement rate limiting on expensive endpoints.",
        "severity": "P0"
    },
    {
        "cause": "Cache stampede in {service_name} for metadata queries",
        "root_cause": "An eviction of high-frequency metadata cache keys in {cache_tech} occurred concurrently with a traffic spike. Thousands of pods hit the underlying database at once to re-fetch the metadata, locking tables.",
        "lessons": "Implement cache key locking/mutexes (single-flight pattern) so only one request updates the cache while others wait. Add jitter to cache TTLs.",
        "severity": "P1"
    },
    {
        "cause": "Out of memory (OOM) crash in {service_name} pod during batch processing",
        "root_cause": "A memory leak in the Go/Python worker loop processing batch uploads. The worker accumulated pointers in a global slice and did not trigger garbage collection timely. Pod reached K8s limit ({mem_limit}) and got OOMKilled.",
        "lessons": "Profile heap usage during batch tasks, reuse object buffers, and add strict memory limits to K8s configs with warnings at 80% usage.",
        "severity": "P1"
    },
    {
        "cause": "Routing loop in Istio service mesh for {service_name}",
        "root_cause": "A misconfigured VirtualService manifest in Terraform caused traffic to cycle between the canary deployment and the main service. Latency spiked and error rates reached 100% due to maximum hop recursion.",
        "lessons": "Add deployment linting checks for mesh configurations. Implement dry-run verification steps in CI/CD pipeline before applying mesh routes.",
        "severity": "P0"
    },
    {
        "cause": "Unoptimized query on {service_name} database after release",
        "root_cause": "A new feature did a sequential scan on a table containing 10M+ rows because the foreign key index was omitted in the migration script. CPU spiked to 100% and query latency went from 5ms to 8000ms.",
        "lessons": "Require explain-plan checks in CI/CD pipelines for any new migration files. Enforce indexing guidelines for foreign keys.",
        "severity": "P2"
    },
    {
        "cause": "Message lag spike on {mq_tech} partition for {service_name}",
        "root_cause": "A slow consumer thread due to synchronous downstream HTTP calls. As partition size grew, processing fell behind by over 50,000 messages, delaying order processing in NovaCommerce.",
        "lessons": "Implement worker pool concurrency in consumer code, wrap calls in circuit breakers, and monitor consumer lag metrics to trigger auto-scaling.",
        "severity": "P1"
    }
]

# Meeting Agenda templates
MEETING_TEMPLATES = [
    {
        "agenda": "Reviewing system bottleneck and proposed cache integration",
        "discussion": "The team reviewed the latest performance profiles showing high read amplification on PostgreSQL. Senior engineers discussed alternatives like Redis and Memcached. PM emphasized the urgency due to upcoming holiday sales. The decision was made to implement Redis.",
        "decisions": "Proceed with deploying Redis caching cluster. Target next sprint for API integration.",
        "actions": ["Create JIRA ticket to provision AWS ElastiCache cluster", "Write draft ADR for Redis integration", "Implement Redis client wrapper in Go"]
    },
    {
        "agenda": "Post-Mortem: Incident INC-{inc_num} Service Outage",
        "discussion": "We analyzed the OOMKilled event on the production api pods. DevOps explained that batch uploads of CSV files loaded entire payloads into memory. SRE suggested streaming files. Platform proposed adjusting pod limits. Security approved the streaming proposal.",
        "decisions": "Rewrite CSV parser to use stream-processing. Increase container memory limit from 1Gi to 2Gi.",
        "actions": ["Refactor CSV upload endpoint to stream to disk", "Update Kubernetes deployment templates in Terraform", "Add Prometheus alert for pod memory usage > 85%"]
    },
    {
        "agenda": "Architecture Alignment: Microservices vs Monolith for FusionERP",
        "discussion": "Debated whether to split the payroll module out of the FusionERP monolith. Product is worried about data consistency. Engineers pointed out that scaling payroll is currently blocked by the Oracle database cost. Decided to keep it inside the monolith for now but wrap payroll in clean module boundaries.",
        "decisions": "Postpone microservices separation for 6 months. Begin domain-driven refactoring of modular boundaries.",
        "actions": ["Document payroll module dependencies", "Set up static analysis rules to prevent illegal imports across ERP modules"]
    },
    {
        "agenda": "Sprint Planning and Dev Velocity retro",
        "discussion": "Velocity fell short in the last sprint. Developers reported spending too much time debugging configuration drift. SRE team showcased the new dev environment based on docker-compose matching local environments. Team agreed to switch.",
        "decisions": "Adopt Docker-compose for all local development, deprecating local setup scripts.",
        "actions": ["Write docker-compose configurations for all core services", "Update README.md onboarding guides"]
    }
]

# Feedback Opinions
FEEDBACK_TEMPLATES = [
    "The transition to Kubernetes makes deployments smoother, but debugging network policies in development is painful.",
    "Using Kafka was a massive overkill for AtlasPay. We could have achieved the same results with PostgreSQL queues or simple SQS.",
    "Redis caching solved our immediate API bottlenecks. Highly recommend rolling it out to other services.",
    "The lack of documentation on our gRPC interfaces makes it difficult for new hires to build features.",
    "We need to enforce code formatting and ESLint rules in the CI pipeline; local configuration drifts are annoying.",
    "The database migration to Cassandra was complex, but it solved our write throughput issues on CloudSync.",
    "Meetings are taking too much coding time. We should have fewer syncs and write more asynchronous updates.",
    "Terraform configurations are clean, but applying them in dev environment is slow.",
    "FastAPI is amazing. It self-documents our CRM endpoints and cuts down API response development time significantly."
]

# Support tickets and complaints
CUSTOMER_TICKETS = [
    "Cannot process payments due to gateway timeout errors. This is blocking our checkout.",
    "Sync tool fails with conflict errors for large files. We are losing progress on changes.",
    "The CRM portal page load is taking over 10 seconds. Our sales reps are complaining.",
    "ERP payroll calculation failed to generate invoices. This is a critical regulatory blocker.",
    "We need an API endpoint to download raw metrics from VisionAI; currently, we can only view them in the dashboard.",
    "Session keeps expiring every 15 minutes, forcing our staff to log in repeatedly. Extremely frustrating.",
    "Can you support Webhooks for AtlasPay transaction status changes? Polling is too slow.",
    "The search filter in NovaCommerce is returning incorrect inventory counts."
]
