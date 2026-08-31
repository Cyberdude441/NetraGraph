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
  MLModel,
  MLPredictionResult,
  MLImportResponse,
  MLModelRegistryResponse,
} from "@/types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" ? "/api" : "http://localhost:8000/api");

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
      let errorMsg = `API Request Failed [${response.status} ${response.statusText}]: ${errorBody}`;
      try {
        const parsed = JSON.parse(errorBody);
        if (parsed.detail) {
          errorMsg = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
        }
      } catch {}
      throw new Error(errorMsg);
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

  async getCyberOverview() {
    return request("/cyber/overview", { method: "GET" }, {
      total_nodes: 0,
      total_relationships: 0,
      entity_counts: {},
      datasets: [],
      last_sync: "",
    });
  },

  async getCyberGraph(params?: { search?: string; nodeType?: string; relationshipType?: string }) {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.nodeType) query.set("node_type", params.nodeType);
    if (params?.relationshipType) query.set("relationship_type", params.relationshipType);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request(`/cyber/graph${suffix}`, { method: "GET" }, null);
  },

  async getCyberRisk(entityId: string) {
    return request(`/cyber/risk/${encodeURIComponent(entityId)}`, { method: "GET" });
  },

  async getCyberAnomalies() {
    return request("/cyber/anomalies", { method: "GET" }, { anomalies: [] });
  },

  async getGraphHealth() {
    return request("/graph/health", { method: "GET" });
  },

  async getGraphStats(graphSource: string = "investigation_evidence") {
    return request(`/graph/stats?graph_source=${encodeURIComponent(graphSource)}`, { method: "GET" });
  },

  async getGraphNodes(params?: { graph_source?: string; search?: string; label?: string; case_id?: string; risk_level?: string }) {
    const query = new URLSearchParams();
    if (params?.graph_source) query.set("graph_source", params.graph_source);
    if (params?.search) query.set("search", params.search);
    if (params?.label) query.set("label", params.label);
    if (params?.case_id) query.set("case_id", params.case_id);
    if (params?.risk_level) query.set("risk_level", params.risk_level);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request(`/graph/nodes${qs}`, { method: "GET" }, { nodes: [] });
  },

  async getGraphRelationships(params?: { graph_source?: string; rel_type?: string }) {
    const query = new URLSearchParams();
    if (params?.graph_source) query.set("graph_source", params.graph_source);
    if (params?.rel_type) query.set("rel_type", params.rel_type);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request(`/graph/relationships${qs}`, { method: "GET" }, { relationships: [] });
  },

  async calculateGraphPath(sourceId: string, targetId: string, graphSource: string = "investigation_evidence") {
    return request("/graph/path", {
      method: "POST",
      body: JSON.stringify({ source_id: sourceId, target_id: targetId, graph_source: graphSource }),
    });
  },

  async calculateGraphCommunities(graphSource: string = "investigation_evidence") {
    return request("/graph/communities", {
      method: "POST",
      body: JSON.stringify({ graph_source: graphSource }),
    });
  },

  async calculateGraphCentrality(graphSource: string = "investigation_evidence", limit: number = 10) {
    return request("/graph/centrality", {
      method: "POST",
      body: JSON.stringify({ graph_source: graphSource, limit }),
    });
  },

  async getGraphNeighborhood(entityId: string, hops: number = 2, graphSource: string = "investigation_evidence") {
    return request(`/graph/entities/${encodeURIComponent(entityId)}/neighbors?hops=${hops}&graph_source=${encodeURIComponent(graphSource)}`, { method: "GET" });
  },

  async getCaseGraph(caseId: string) {
    return request(`/graph/cases/${encodeURIComponent(caseId)}`, { method: "GET" });
  },

  async getEntityDetails(entityId: string) {
    return request(`/graph/entities/${encodeURIComponent(entityId)}`, { method: "GET" });
  },

  async getEntityNeighbors(entityId: string, hops: number = 2) {
    return request(`/graph/entities/${encodeURIComponent(entityId)}/neighbors?hops=${hops}`, { method: "GET" });
  },

  async getEntitySubgraph(entityId: string) {
    return request(`/graph/entities/${encodeURIComponent(entityId)}/subgraph`, { method: "GET" });
  },

  async searchGraph(params: { q?: string; entity_type?: string; case_id?: string; min_confidence?: number; verification_status?: string }) {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.entity_type) query.set("entity_type", params.entity_type);
    if (params.case_id) query.set("case_id", params.case_id);
    if (params.min_confidence !== undefined) query.set("min_confidence", params.min_confidence.toString());
    if (params.verification_status) query.set("verification_status", params.verification_status);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request(`/graph/search${qs}`, { method: "GET" });
  },

  async getGraphStatistics() {
    return request("/graph/statistics", { method: "GET" });
  },

  async explainRelationship(relationshipId: string) {
    return request(`/graph/relationships/${encodeURIComponent(relationshipId)}/explain`, { method: "GET" });
  },

  async generateCaseReport(caseId: string, officerId?: string, officerDesignation?: string) {
    return request(`/cases/${encodeURIComponent(caseId)}/report`, {
      method: "POST",
      body: JSON.stringify({ officer_id: officerId, officer_designation: officerDesignation }),
    });
  },

  async getSystemDataIntegrity() {
    return request("/system/data-integrity", { method: "GET" });
  },

  async getSystemHealth() {
    return request("/system/health", { method: "GET" });
  },

  async syncNCRB() {
    return request("/ncrb/sync", { method: "POST" });
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

  async getCaseWorkspace(caseId: string) {
    return request(`/cases/${encodeURIComponent(caseId)}/workspace`, { method: "GET" });
  },

  async getCaseTimeline(caseId: string) {
    return request(`/cases/${encodeURIComponent(caseId)}/timeline`, { method: "GET" });
  },

  async exportCaseGraph(caseId: string, format: string = "json") {
    return request(`/cases/${encodeURIComponent(caseId)}/export?format=${format}`, { method: "GET" });
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

  async getEvidenceMetadata(evidenceId: string) {
    return request(`/evidence/${encodeURIComponent(evidenceId)}/metadata`, { method: "GET" });
  },

  async getEvidenceHash(evidenceId: string) {
    return request(`/evidence/${encodeURIComponent(evidenceId)}/hash`, { method: "GET" });
  },

  async getEvidenceProvenance(evidenceId: string) {
    return request(`/evidence/${encodeURIComponent(evidenceId)}/provenance`, { method: "GET" });
  },

  async getStagedExtractions(evidenceId: string) {
    return request(`/evidence/${encodeURIComponent(evidenceId)}/staged-extractions`, { method: "GET" });
  },

  async reviewStagedExtraction(extractionId: string, action: string, actor?: string, editedAttributes?: Record<string, any>) {
    return request(`/evidence/extractions/${encodeURIComponent(extractionId)}/review`, {
      method: "POST",
      body: JSON.stringify({ action, actor: actor || "IN-BOSE-4417", edited_attributes: editedAttributes }),
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

  // ==========================================
  // Machine Learning Intelligence Subsystem
  // ==========================================
  async getMLModels(): Promise<MLModel[]> {
    const res = await request<MLModelRegistryResponse>("/ml/models", { method: "GET" }, { models: [] });
    return res.models || [];
  },

  async getMLModel(name: string): Promise<MLModel[]> {
    const res = await request<{ models: MLModel[] }>(`/ml/models/${encodeURIComponent(name)}`, { method: "GET" });
    return res.models || [];
  },

  async importMLModel(file: File): Promise<MLImportResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const url = `${API_BASE_URL}/ml/models/import`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "X-User-ID": "IN-BOSE-4417",
      },
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      let detail = errorBody;
      try {
        const parsed = JSON.parse(errorBody);
        if (parsed.detail) detail = parsed.detail;
      } catch {}
      throw new Error(`Model Import Failed: ${detail}`);
    }

    return (await response.json()) as MLImportResponse;
  },

  async activateMLModel(name: string, version: string): Promise<MLModel> {
    return request<MLModel>(`/ml/models/${encodeURIComponent(name)}/${encodeURIComponent(version)}/activate`, {
      method: "POST",
    });
  },

  async deactivateMLModel(name: string, version: string): Promise<MLModel> {
    return request<MLModel>(`/ml/models/${encodeURIComponent(name)}/${encodeURIComponent(version)}/deactivate`, {
      method: "POST",
    });
  },

  async predictIntrusion(payload: Record<string, any>, modelName?: string): Promise<MLPredictionResult> {
    const qs = modelName ? `?model=${encodeURIComponent(modelName)}` : "";
    return request<MLPredictionResult>(`/ml/predict/intrusion${qs}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async predictPhishingUrl(payload: Record<string, any>, modelName?: string): Promise<MLPredictionResult> {
    const qs = modelName ? `?model=${encodeURIComponent(modelName)}` : "";
    return request<MLPredictionResult>(`/ml/predict/phishing-url${qs}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async predictWebpagePhishing(payload: Record<string, any>, modelName?: string): Promise<MLPredictionResult> {
    const qs = modelName ? `?model=${encodeURIComponent(modelName)}` : "";
    return request<MLPredictionResult>(`/ml/predict/webpage-phishing${qs}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async predictPhishingEmail(payload: Record<string, any>, modelName?: string): Promise<MLPredictionResult> {
    const qs = modelName ? `?model=${encodeURIComponent(modelName)}` : "";
    return request<MLPredictionResult>(`/ml/predict/phishing-email${qs}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async predictModel(modelName: string, payload: Record<string, any>): Promise<MLPredictionResult> {
    return request<MLPredictionResult>(`/ml/predict/${encodeURIComponent(modelName)}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

