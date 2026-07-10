document.addEventListener("DOMContentLoaded", () => {
    // API base URL
    const BASE_URL = "";

    // DOM Elements
    const countDecisions = document.getElementById("count-decisions");
    const countArtifacts = document.getElementById("count-artifacts");
    const countRelationships = document.getElementById("count-relationships");
    const countProjects = document.getElementById("count-projects");

    const queryInput = document.getElementById("query-input-field");
    const querySubmitBtn = document.getElementById("query-submit-btn");
    const ragDisplayBox = document.getElementById("rag-display-box");
    const ragDisplayContent = document.getElementById("rag-display-content");

    const decisionSearch = document.getElementById("decision-search-input");
    const decisionsFeed = document.getElementById("decisions-feed-container");
    const inspectorContent = document.getElementById("inspector-body-content");

    // Live state cache
    let decisionsList = [];
    let activeDecisionId = null;

    // --------------------------------------------------
    // API FETCH FUNCTIONS
    // --------------------------------------------------

    // Fetch and display dashboard statistics
    async function fetchStats() {
        try {
            const res = await fetch(`${BASE_URL}/api/stats`);
            const data = await res.json();
            
            countDecisions.textContent = data.decisions.toLocaleString();
            countArtifacts.textContent = data.artifacts.toLocaleString();
            countRelationships.textContent = data.relationships.toLocaleString();
            countProjects.textContent = data.projects.toLocaleString();

            // Populate sub-metrics bar
            document.getElementById("sub-jira").textContent = data.jira.toLocaleString();
            document.getElementById("sub-slack").textContent = data.slack.toLocaleString();
            document.getElementById("sub-k8s").textContent = data.deployments.toLocaleString();
            document.getElementById("sub-datadog").textContent = data.incidents.toLocaleString();
            document.getElementById("sub-prs").textContent = data.prs.toLocaleString();
            document.getElementById("sub-commits").textContent = data.commits.toLocaleString();
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
    }

    // Register global tab switcher function
    window.switchInspectorTab = function(tabName) {
        const overviewTab = document.getElementById("tab-overview");
        const timelineTab = document.getElementById("tab-timeline");
        const overviewContent = document.getElementById("inspector-tab-content-overview");
        const timelineContent = document.getElementById("inspector-tab-content-timeline");
        
        if (!overviewTab || !timelineTab || !overviewContent || !timelineContent) return;
        
        if (tabName === "overview") {
            overviewTab.classList.add("active");
            timelineTab.classList.remove("active");
            overviewContent.style.display = "flex";
            timelineContent.style.display = "none";
        } else {
            overviewTab.classList.remove("active");
            timelineTab.classList.add("active");
            overviewContent.style.display = "none";
            timelineContent.style.display = "flex";
        }
    }

    // Fetch and display reconstructed decisions feed
    async function fetchDecisions(searchQuery = "") {
        try {
            const url = searchQuery 
                ? `${BASE_URL}/api/decisions?search=${encodeURIComponent(searchQuery)}`
                : `${BASE_URL}/api/decisions`;
            
            const res = await fetch(url);
            decisionsList = await res.json();
            
            renderDecisionsFeed(decisionsList);
        } catch (err) {
            console.error("Failed to fetch decisions:", err);
            decisionsFeed.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 20px;">Failed to load decisions feed.</div>`;
        }
    }

    // Render decisions feed HTML
    function renderDecisionsFeed(decisions) {
        if (decisions.length === 0) {
            decisionsFeed.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 20px;">No matching decisions found.</div>`;
            return;
        }

        decisionsFeed.innerHTML = decisions.map(dec => {
            let projectKey = "SHARED";
            const match = dec.title.match(/in\s+([a-zA-Z0-9\-]+)/i);
            if (match) {
                projectKey = match[1].toUpperCase();
            } else if (dec.title.includes("novacommerce")) {
                projectKey = "NOVACOMMERCE";
            } else if (dec.title.includes("atlaspay")) {
                projectKey = "ATLASPAY";
            } else if (dec.title.includes("insightcrm")) {
                projectKey = "INSIGHTCRM";
            }

            const isActive = dec.decision_id === activeDecisionId ? "active" : "";

            return `
                <div class="decision-item ${isActive}" data-id="${dec.decision_id}">
                    <div class="decision-meta">
                        <span class="decision-title-text">${dec.title}</span>
                        <span class="decision-problem-snippet">${dec.problem}</span>
                        <div class="decision-tags">
                            <span class="tag-confidence">Confidence: ${(dec.confidence * 100).toFixed(0)}%</span>
                            <span class="tag-project">${projectKey}</span>
                        </div>
                    </div>
                    <i data-lucide="chevron-right" style="color: var(--text-secondary); flex-shrink: 0; width: 18px; height: 18px;"></i>
                </div>
            `;
        }).join("");

        lucide.createIcons();

        document.querySelectorAll(".decision-item").forEach(card => {
            card.addEventListener("click", () => {
                const decId = card.getAttribute("data-id");
                selectDecision(decId);
            });
        });
    }

    // Load decision details in the inspector side panel
    async function selectDecision(decId) {
        activeDecisionId = decId;
        
        document.querySelectorAll(".decision-item").forEach(card => {
            if (card.getAttribute("data-id") === decId) {
                card.classList.add("active");
            } else {
                card.classList.remove("active");
            }
        });

        inspectorContent.innerHTML = `<div style="text-align: center; color: var(--text-secondary); padding: 40px;"><i data-lucide="loader" class="animate-spin" style="margin: 0 auto 12px auto; color: var(--accent-primary);"></i>Loading details...</div>`;
        lucide.createIcons();

        try {
            const res = await fetch(`${BASE_URL}/api/decisions/${decId}`);
            const dec = await res.json();
            
            renderInspectorDetails(dec);
        } catch (err) {
            console.error("Failed to load decision details:", err);
            inspectorContent.innerHTML = `<div style="color: var(--text-secondary); text-align: center; padding: 40px;">Failed to load decision details.</div>`;
        }
    }

    // Render detailed decision panels inside inspector body
    async function renderInspectorDetails(dec) {
        // Compile evidence list badges
        const evidenceRows = [];
        
        for (const artId of dec.evidence_ids) {
            let label = "Artifact";
            let badgeClass = "badge-pr";

            if (artId.startsWith("github:") && artId.includes(":adr:")) {
                label = "ADR";
                badgeClass = "badge-adr";
            } else if (artId.startsWith("github:") && artId.includes(":pull_request:")) {
                label = "PR";
                badgeClass = "badge-pr";
            } else if (artId.startsWith("github:") && artId.includes(":commit:")) {
                label = "Commit";
                badgeClass = "badge-commit";
            } else if (artId.startsWith("jira:issue:")) {
                label = "Issue";
                badgeClass = "badge-issue";
            } else if (artId.startsWith("slack:chat:")) {
                label = "Slack";
                badgeClass = "badge-chat";
            } else if (artId.startsWith("datadog:incident:")) {
                label = "Incident";
                badgeClass = "badge-incident";
            } else if (artId.startsWith("kubernetes:deployment:")) {
                label = "Deployment";
                badgeClass = "badge-deployment";
            }

            const cleanId = artId.split(":").pop().toUpperCase();
            
            evidenceRows.push(`
                <div class="evidence-item">
                    <span class="evidence-badge ${badgeClass}">${label}</span>
                    <span style="font-family: monospace; font-weight: 500;">${cleanId}</span>
                </div>
            `);
        }

        // Render Chronological Ingestion Trace Timeline
        const timelineEvents = [];
        const timelineData = dec.timeline || [];
        
        for (const item of timelineData) {
            let label = item.source_type.toUpperCase();
            let badgeClass = "badge-pr";
            let iconName = "file-text";
            
            if (item.source_type === "adr") {
                label = "ADR";
                badgeClass = "badge-adr";
                iconName = "file-text";
            } else if (item.source_type === "pull_request") {
                label = "PR";
                badgeClass = "badge-pr";
                iconName = "git-pull-request";
            } else if (item.source_type === "commit") {
                label = "Commit";
                badgeClass = "badge-commit";
                iconName = "git-commit";
            } else if (item.source_type === "issue") {
                label = "Issue";
                badgeClass = "badge-issue";
                iconName = "alert-circle";
            } else if (item.source_type === "chat") {
                label = "Slack Feedback";
                badgeClass = "badge-chat";
                iconName = "message-square";
            } else if (item.source_type === "incident") {
                label = "Incident";
                badgeClass = "badge-incident";
                iconName = "alert-triangle";
            } else if (item.source_type === "deployment") {
                label = "Deployment";
                badgeClass = "badge-deployment";
                iconName = "server";
            }

            const cleanId = item.external_id || item.artifact_id.split(":").pop().toUpperCase();
            
            // Format Timestamp
            let dateStr = "Unknown Time";
            if (item.timestamp) {
                try {
                    dateStr = new Date(item.timestamp.replace(" ", "T")).toLocaleString();
                } catch(e) {
                    dateStr = item.timestamp;
                }
            }
            
            const authorText = item.author ? `@${item.author}` : "System";
            
            timelineEvents.push(`
                <div class="timeline-event">
                    <div class="timeline-node" style="border-color: ${item.source_type === 'incident' ? 'var(--accent-danger)' : 'var(--accent-primary)'};">
                        <i data-lucide="${iconName}" style="width: 8px; height: 8px; color: white;"></i>
                    </div>
                    <div class="timeline-event-header">
                        <span class="evidence-badge ${badgeClass}">${label} - ${cleanId}</span>
                        <span class="timeline-event-time">${dateStr}</span>
                    </div>
                    <div class="timeline-event-title">${item.title}</div>
                    <div class="timeline-event-body">
                        ${item.content ? item.content.substring(0, 150) + (item.content.length > 150 ? '...' : '') : ''}
                    </div>
                    <div style="font-size: 10px; color: var(--text-secondary); margin-top: 4px;">
                        By ${authorText} via ${item.source}
                    </div>
                </div>
            `);
        }
        
        const timelineHTML = timelineEvents.length > 0 
            ? `<div class="timeline-container">${timelineEvents.join("")}</div>`
            : `<div style="color: var(--text-secondary); text-align: center; padding: 20px;">No timeline evidence connected.</div>`;

        const altSection = dec.alternatives && dec.alternatives !== "No alternatives considered." 
            ? `
                <div class="inspector-section">
                    <span class="section-label">Alternatives Considered</span>
                    <span class="section-content-text">${dec.alternatives}</span>
                </div>
            `
            : "";

        inspectorContent.innerHTML = `
            <!-- Tab bar -->
            <div class="inspector-tabs">
                <div class="inspector-tab active" id="tab-overview" onclick="switchInspectorTab('overview')">Overview</div>
                <div class="inspector-tab" id="tab-timeline" onclick="switchInspectorTab('timeline')">Evidence Timeline (${timelineData.length})</div>
            </div>

            <!-- Tab content: Overview -->
            <div id="inspector-tab-content-overview" style="display: flex; flex-direction: column; gap: 20px; width: 100%;">
                <div class="inspector-section">
                    <span class="section-label">Decision Title</span>
                    <h2 style="font-size: 16px; font-weight: 700; color: white; line-height: 1.4;">${dec.title}</h2>
                </div>
                
                <div class="inspector-section" style="background: rgba(16, 185, 129, 0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.15);">
                    <span class="section-label" style="color: var(--accent-success);">Operational Status</span>
                    <span class="section-content-text" style="color: #a7f3d0; font-size: 12px;">${dec.outcomes}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Problem Statement</span>
                    <span class="section-content-text">${dec.problem}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Context & Triggers</span>
                    <span class="section-content-text">${dec.context}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Technical Direction</span>
                    <span class="section-content-text" style="color: white; font-weight: 500;">${dec.decision}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Architecture Justification</span>
                    <span class="section-content-text">${dec.reasoning}</span>
                </div>

                ${altSection}

                <div class="inspector-section">
                    <span class="section-label">Implementation Summary</span>
                    <span class="section-content-text">${dec.implementation}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Lessons Learned</span>
                    <span class="section-content-text">${dec.lessons}</span>
                </div>

                <div class="inspector-section">
                    <span class="section-label">Connected Graph Evidence (${dec.evidence_ids.length})</span>
                    <div class="evidence-list">
                        ${evidenceRows.join("")}
                    </div>
                </div>
            </div>

            <!-- Tab content: Evidence Timeline -->
            <div id="inspector-tab-content-timeline" style="display: none; flex-direction: column; gap: 20px; width: 100%;">
                <div class="inspector-section">
                    <span class="section-label">Chronological Ingestion Trace</span>
                    ${timelineHTML}
                </div>
            </div>
        `;

        lucide.createIcons();
    }

    // Ask Query Agent portal
    async function askQueryAgent() {
        const query = queryInput.value.trim();
        if (!query) return;

        ragDisplayBox.style.display = "block";
        ragDisplayContent.innerHTML = `<div style="display: flex; align-items: center; gap: 8px;"><i data-lucide="loader" class="animate-spin" style="color: var(--accent-secondary); width: 16px; height: 16px;"></i><span>Thinking... Grounding details in Evidence Graph...</span></div>`;
        lucide.createIcons();

        try {
            const res = await fetch(`${BASE_URL}/api/query?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            // Render markdown using Marked
            ragDisplayContent.innerHTML = marked.parse(data.response);
            lucide.createIcons();
        } catch (err) {
            console.error("Query failed:", err);
            ragDisplayContent.textContent = "Query failed. Ensure backend server is running.";
        }
    }

    // --------------------------------------------------
    // EVENT LISTENERS
    // --------------------------------------------------

    // Ask Button triggers
    querySubmitBtn.addEventListener("click", askQueryAgent);
    queryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            askQueryAgent();
        }
    });

    // Search bar search debounce
    let searchTimeout = null;
    decisionSearch.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchDecisions(decisionSearch.value.trim());
        }, 300);
    });

    // --------------------------------------------------
    // INITIALIZATION & REAL-TIME POLLS
    // --------------------------------------------------
    
    // Initial loads
    fetchStats();
    fetchDecisions();

    // Set a live poller to update statistics and decisions list every 6 seconds
    // to dynamically capture incoming live webhook events
    setInterval(() => {
        fetchStats();
    }, 6000);
});
