import type {
  Case,
  Entity,
  Evidence,
  Relationship,
  AIAnalyzeResponse,
  AIStatusResponse,
  AIProvider,
  AITaskType,
  FIRIngestPayload,
  CDRIngestPayload,
  FinanceIngestPayload,
  CyberComplaintPayload,
  DigitalEvidencePayload,
  IngestionResponse,
  DashboardMetrics,
  NCRBOverview,
  NCRBStateCrime,
  NCRBCategoryCrime,
  NCRBITActSection,
} from "@/types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Generic REST client wrapper for Cyber Cell API endpoints.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  fallbackValue?: T,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-User-ID": "IN-BOSE-4417",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `API Request Failed [${response.status} ${response.statusText}]: ${errorBody}`,
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    if (fallbackValue !== undefined) {
      console.warn(`[NetraGraph API] Fallback used for ${endpoint}:`, error);
      return fallbackValue;
    }
    throw error;
  }
}

export const api = {
  // ==========================================
  // Ingestion Services (FIR, CDR, Finance, Cyber, Evidence)
  // ==========================================
  async ingestFIR(payload: FIRIngestPayload): Promise<IngestionResponse> {
    return request<IngestionResponse>("/ingestion/fir", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async ingestCDR(payload: CDRIngestPayload): Promise<IngestionResponse> {
    return request<IngestionResponse>("/ingestion/cdr", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async ingestFinance(payload: FinanceIngestPayload): Promise<IngestionResponse> {
    return request<IngestionResponse>("/ingestion/finance", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async ingestCyberComplaint(payload: CyberComplaintPayload): Promise<IngestionResponse> {
    return request<IngestionResponse>("/ingestion/cyber", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async ingestDigitalEvidence(payload: DigitalEvidencePayload): Promise<IngestionResponse> {
    return request<IngestionResponse>("/ingestion/evidence", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // ==========================================
  // Entities & Network Graph
  // ==========================================
  async getEntities(params?: { search?: string; minRisk?: number; type?: string }): Promise<Entity[]> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.minRisk !== undefined) query.set("min_risk", params.minRisk.toString());
    if (params?.type) query.set("type", params.type);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<Entity[]>(`/entities${qs}`, { method: "GET" }, []);
  },

  async getEntity(id: string): Promise<Entity | undefined> {
    return request<Entity>(`/entities/${id}`, { method: "GET" });
  },

  async getRelationships(): Promise<Relationship[]> {
    return request<Relationship[]>("/relationships", { method: "GET" }, []);
  },

  async getMultiHopGraph(entityId: string, hops: number = 2) {
    return request(`/network/${entityId}?hops=${hops}`, { method: "GET" });
  },

  async getPublicGraph() {
    return request("/graph/network?graph_source=ncrb_public", { method: "GET" }, null);
  },

  // ==========================================
  // Cases & Investigation Registry
  // ==========================================
  async getCases(): Promise<Case[]> {
    return request<Case[]>("/cases", { method: "GET" }, []);
  },

  async getCase(id: string): Promise<Case | undefined> {
    return request<Case>(`/cases/${id}`, { method: "GET" });
  },

  async createCase(caseData: Partial<Case>): Promise<Case> {
    return request<Case>("/cases", {
      method: "POST",
      body: JSON.stringify(caseData),
    });
  },

  // ==========================================
  // Digital Evidence Vault
  // ==========================================
  async getEvidence(): Promise<Evidence[]> {
    return request<Evidence[]>("/evidence", { method: "GET" }, []);
  },

  async uploadEvidence(evidenceItem: Partial<Evidence>): Promise<Evidence> {
    return request<Evidence>("/evidence", {
      method: "POST",
      body: JSON.stringify(evidenceItem),
    });
  },

  // ==========================================
  // Analytics & Dashboard Telemetry
  // ==========================================
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return request<DashboardMetrics>("/analytics/metrics", { method: "GET" }, {
      summary: {
        totalEntities: 0,
        totalRelationships: 0,
        totalCases: 0,
        totalEvidence: 0,
        highRiskTargets: 0,
      },
      threatMatrix: [
        {"name": "Critical", "value": 0, "key": "crit"},
        {"name": "High", "value": 0, "key": "high"},
        {"name": "Moderate", "value": 0, "key": "mod"},
        {"name": "Low", "value": 0, "key": "low"},
      ],
      syndicates: [],
      totalRecords: 0,
    });
  },

  async getAuditLogs(limit: number = 50) {
    return request(`/audit/logs?limit=${limit}`, { method: "GET" }, []);
  },

  // ==========================================
  // Open Government Data (data.gov.in) & Neo4j Graph
  // ==========================================
  async getOGDPipelineStatus(): Promise<OGDPipelineStatus> {
    return request<OGDPipelineStatus>("/ncrb/pipeline/status", { method: "GET" });
  },

  async syncOGDPipeline(): Promise<any> {
    return request("/ncrb/pipeline/sync", { method: "POST" });
  },

  async getNeo4jGraph(params?: {
    search?: string;
    state?: string;
    category?: string;
    node_type?: string;
  }): Promise<Neo4jGraphPayload> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.state) query.set("state", params.state);
    if (params?.category) query.set("category", params.category);
    if (params?.node_type) query.set("node_type", params.node_type);

    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<Neo4jGraphPayload>(`/ncrb/graph${qs}`, { method: "GET" });
  },

  // ==========================================
  // Phase 3 — Official NCRB Open Government Data APIs
  // ==========================================
  async getNCRBCyberCrime(params?: { state?: string; year?: number }): Promise<NCRBCyberCrime[]> {
    const query = new URLSearchParams();
    if (params?.state) query.set("state", params.state);
    if (params?.year) query.set("year", params.year.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<NCRBCyberCrime[]>(`/ncrb/cyber-crime${qs}`, { method: "GET" }, []);
  },

  async getNCRBMotives(params?: { state?: string; year?: number; motive?: string }): Promise<NCRBMotiveRecord[]> {
    const query = new URLSearchParams();
    if (params?.state) query.set("state", params.state);
    if (params?.year) query.set("year", params.year.toString());
    if (params?.motive) query.set("motive", params.motive);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<NCRBMotiveRecord[]>(`/ncrb/motives${qs}`, { method: "GET" }, []);
  },

  async getNCRBInvestigation(params?: { crime_head?: string }): Promise<NCRBInvestigationRecord[]> {
    const query = new URLSearchParams();
    if (params?.crime_head) query.set("crime_head", params.crime_head);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<NCRBInvestigationRecord[]>(`/ncrb/investigation${qs}`, { method: "GET" }, []);
  },

  async getNCRBCourt(params?: { crime_head?: string }): Promise<NCRBCourtRecord[]> {
    const query = new URLSearchParams();
    if (params?.crime_head) query.set("crime_head", params.crime_head);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<NCRBCourtRecord[]>(`/ncrb/court${qs}`, { method: "GET" }, []);
  },

  async getDominantMotives(): Promise<DominantMotive[]> {
    return request<DominantMotive[]>("/ncrb/analytics/motives", { method: "GET" }, []);
  },

  async getPolicePendency(): Promise<PoliceDisposalStat[]> {
    return request<PoliceDisposalStat[]>("/ncrb/analytics/police-pendency", { method: "GET" }, []);
  },

  async getCourtEfficiency(): Promise<CourtDisposalStat[]> {
    return request<CourtDisposalStat[]>("/ncrb/analytics/court-efficiency", { method: "GET" }, []);
  },

  async getArrestTrends(): Promise<ArrestDisposalStat[]> {
    return request<ArrestDisposalStat[]>("/ncrb/analytics/arrest-trends", { method: "GET" }, []);
  },

  async getNCRBOverview(): Promise<NCRBOverview> {
    return request<NCRBOverview>("/ncrb/overview", { method: "GET" });
  },

  async getNCRBStates(limit?: number): Promise<NCRBStateCrime[]> {
    const qs = limit ? `?limit=${limit}` : "";
    return request<NCRBStateCrime[]>(`/ncrb/states${qs}`, { method: "GET" }, []);
  },

  async getNCRBCategories(): Promise<NCRBCategoryCrime[]> {
    return request<NCRBCategoryCrime[]>("/ncrb/categories", { method: "GET" }, []);
  },

  async getNCRBITActSections(): Promise<NCRBITActSection[]> {
    return request<NCRBITActSection[]>("/ncrb/it-act", { method: "GET" }, []);
  },

  async ingestNCRBCSV(file?: File, rawCsv?: string): Promise<any> {
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      const url = `${API_BASE_URL}/ncrb/ingest`;
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Failed to upload NCRB CSV");
      return response.json();
    } else {
      const formData = new FormData();
      formData.append("raw_csv", rawCsv || "");
      const url = `${API_BASE_URL}/ncrb/ingest`;
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Failed to ingest raw NCRB CSV");
      return response.json();
    }
  },

  // ==========================================
  // Phase 6 — Graph-Augmented AI Reasoning (Gemini / Nemotron)
  // ==========================================
  async queryGraphAI(payload: {
    question: string;
    provider?: "gemini" | "nemotron";
  }): Promise<{
    question: string;
    answer: string;
    provider_used: string;
    model: string;
    confidence_score: number;
    ground_truth_metrics: {
      nationalTotal: number;
      yoyGrowth: string;
      financialLoss: string;
      topHotspots: string[];
      stateFocused?: any;
    };
    graph_subgraph: {
      totalNodesRetrieved: number;
      totalRelationshipsRetrieved: number;
      nodes: any[];
      relationships: any[];
    };
    provenance: {
      source: string;
      datasets: string[];
      graphDatabase: string;
    };
  }> {
    return request("/ai/graph-query", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getAIProviders(): Promise<any> {
    return request("/ai/providers", { method: "GET" });
  },

  async getAIStatus(): Promise<AIStatusResponse> {
    return request<AIStatusResponse>("/ai/status", { method: "GET" }, {
      nemotron_available: true,
      gemini_available: true,
      default_provider: "gemini",
      version: "2.5.0",
    });
  },

  async analyzeWithAI(payload: {
    provider: AIProvider;
    task: AITaskType;
    text: string;
    context?: Record<string, any>;
  }): Promise<AIAnalyzeResponse> {
    return request<AIAnalyzeResponse>("/ai/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
