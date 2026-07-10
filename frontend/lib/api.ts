const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return res.json();
  } catch (error) {
    console.error(`[API] ${path} failed:`, error);
    throw error;
  }
}

/* ─── Types ─── */

export interface StatsResponse {
  decisions: number;
  artifacts: number;
  relationships: number;
  projects: number;
  slack: number;
  incidents: number;
  deployments: number;
  jira?: number;
  commits?: number;
  prs?: number;
  initialized: boolean;
  [key: string]: any;
}

export interface ArtifactItem {
  artifact_id: string;
  source: string;
  source_type: string;
  external_id: string;
  title: string;
  content: string;
  author: string;
  timestamps: Record<string, string>;
  url: string | null;
  context: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface DecisionItem {
  decision_id: string;
  title: string;
  problem: string;
  context: string;
  constraints: string;
  alternatives: string;
  decision: string;
  reasoning: string;
  implementation: string;
  outcomes: string;
  lessons: string;
  confidence: number;
  evidence_ids: string[];
  timeline?: TimelineItem[];
}

export interface TimelineItem {
  artifact_id: string;
  source: string;
  source_type: string;
  external_id: string;
  title: string;
  content: string;
  author: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface RelationshipItem {
  relationship_id: string;
  source_id: string;
  target_id: string;
  relationship_type: string;
  confidence: number;
  reasoning: string;
}

export interface GraphSummary {
  nodes_by_type: Record<string, number>;
  nodes_by_source: Record<string, number>;
  edges_by_type: Record<string, number>;
  total_nodes: number;
  total_edges: number;
  top_connected: {
    artifact_id: string;
    title: string;
    source_type: string;
    source: string;
    connection_count: number;
  }[];
}

export interface GraphCluster {
  nodes: {
    artifact_id: string;
    source: string;
    source_type: string;
    external_id: string;
    title: string;
    author: string;
  }[];
  edges: {
    source_id: string;
    target_id: string;
    relationship_type: string;
    confidence: number;
  }[];
  center: string;
}

export interface ActivityItem {
  artifact_id: string;
  source: string;
  source_type: string;
  external_id: string;
  title: string;
  author: string;
  timestamp: string;
  url: string | null;
}

/* ─── Fetchers ─── */

export const api = {
  getStats: () => fetchAPI<StatsResponse>("/api/stats"),

  getDecisions: (search?: string) =>
    fetchAPI<DecisionItem[]>(`/api/decisions${search ? `?search=${encodeURIComponent(search)}` : ""}`),

  getDecision: (id: string) => fetchAPI<DecisionItem>(`/api/decisions/${encodeURIComponent(id)}`),

  getArtifacts: (params?: {
    source?: string;
    source_type?: string;
    search?: string;
    author?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.source) qs.set("source", params.source);
    if (params?.source_type) qs.set("source_type", params.source_type);
    if (params?.search) qs.set("search", params.search);
    if (params?.author) qs.set("author", params.author);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return fetchAPI<{ artifacts: ArtifactItem[]; total: number }>(`/api/artifacts${q ? `?${q}` : ""}`);
  },

  getArtifact: (id: string) => fetchAPI<ArtifactItem>(`/api/artifacts/${encodeURIComponent(id)}`),

  getRelationships: (params?: {
    source_id?: string;
    target_id?: string;
    relationship_type?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.source_id) qs.set("source_id", params.source_id);
    if (params?.target_id) qs.set("target_id", params.target_id);
    if (params?.relationship_type) qs.set("relationship_type", params.relationship_type);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return fetchAPI<{ relationships: RelationshipItem[]; total: number }>(`/api/relationships${q ? `?${q}` : ""}`);
  },

  getGraphSummary: () => fetchAPI<GraphSummary>("/api/graph/summary"),

  getGraphCluster: (artifactId: string, hops = 2) =>
    fetchAPI<GraphCluster>(`/api/graph/cluster/${encodeURIComponent(artifactId)}?hops=${hops}`),

  getActivity: (params?: { source_type?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.source_type) qs.set("source_type", params.source_type);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return fetchAPI<{ items: ActivityItem[]; total: number }>(`/api/activity${q ? `?${q}` : ""}`);
  },

  query: (q: string) =>
    fetchAPI<{ response: string }>(`/api/query?q=${encodeURIComponent(q)}`),
};
