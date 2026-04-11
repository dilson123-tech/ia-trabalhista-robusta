const API_URL = "http://127.0.0.1:8099/api/v1"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function parseError(response: Response, fallbackMessage: string): Promise<never> {
  if (response.status === 401) {
    if (fallbackMessage === "Erro ao autenticar no sistema") {
      throw new ApiError("Usuário ou senha inválidos. Verifique os dados e tente novamente.", 401)
    }

    throw new ApiError("Sessão expirada ou token inválido. Faça login novamente.", 401)
  }

  let message = fallbackMessage

  try {
    const data = await response.json()
    if (data && typeof data.detail === "string" && data.detail.trim()) {
      message = data.detail
    }
  } catch {
    // ignora parse inválido e mantém fallback
  }

  throw new ApiError(message, response.status)
}

export type CaseItem = {
  id: number
  case_number: string
  title: string
  description: string
  legal_area: string
  action_type?: string
  status: string
  tenant_id: number
  created_at: string
  updated_at: string
}

export type CaseCreatePayload = {
  case_number: string
  title: string
  description?: string
  legal_area?: string
  action_type?: string
  status?: string
}

export type LoginPayload = {
  username: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao autenticar no sistema")
  }

  return response.json()
}

export async function getCases(token: string): Promise<CaseItem[]> {
  const response = await fetch(`${API_URL}/cases`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar casos")
  }

  return response.json()
}

export type CaseAnalysisResponse = {
  case_id: number
  analysis_id: number
  analysis: {
    technical?: {
      summary?: string
      risk_level?: string
      issues?: string[]
      next_steps?: string[]
    }
    strategic?: Record<string, unknown>
    viability?: Record<string, unknown>
    decision?: Record<string, unknown>
  }
  viability?: Record<string, unknown>
}

export async function getCaseAnalysis(token: string, caseId: number): Promise<CaseAnalysisResponse> {
  const response = await fetch(`${API_URL}/cases/${caseId}/analysis`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao analisar caso")
  }

  return response.json()
}

export type ExecutiveSummaryResponse = {
  case: {
    id: number
    case_number: string
    title: string
  }
  technical_analysis?: {
    summary?: string
    risk_level?: string
    issues?: string[]
    next_steps?: string[]
  }
  strategic_analysis?: {
    success_probability?: number
    complexity?: string
    financial_risk?: string
    recommended_strategy?: string
    critical_points?: string[]
    strong_points?: string[]
  }
  viability?: {
    score?: number
    probability?: number
    label?: string
    complexity?: string
    estimated_time?: string
    recommendation?: string
  }
  executive_decision?: {
    executive_summary?: string
    final_status?: string
    confidence_level?: number
    probability_percent?: number
    score?: number
    complexity?: string
    estimated_time?: string
  }
  analysis_foundations?: {
    normative_basis?: string[]
    factual_elements_considered?: string[]
    probative_gaps?: string[]
    disclaimer?: string
    analysis_context?: {
      legal_area?: string
      final_status?: string
      probability_percent?: number
      viability_label?: string
    }
  }
}

export async function getExecutiveSummary(token: string, caseId: number): Promise<ExecutiveSummaryResponse> {
  const response = await fetch(`${API_URL}/cases/${caseId}/executive-summary`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar executive summary")
  }

  return response.json()
}

export type ExecutiveReportResponse = {
  case_id: number
  executive_decision?: Record<string, unknown>
  report_html: string
}

export async function getExecutiveReport(token: string, caseId: number): Promise<ExecutiveReportResponse> {
  const response = await fetch(`${API_URL}/cases/${caseId}/executive-report`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar executive report")
  }

  return response.json()
}

export async function getExecutivePdf(token: string, caseId: number): Promise<Blob> {
  const response = await fetch(`${API_URL}/cases/${caseId}/executive-pdf`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar executive pdf")
  }

  return response.blob()
}

export type CaseStatus = "draft" | "active" | "review" | "archived"

export type CaseStatusUpdatePayload = {
  status: CaseStatus
}

export type DemoCleanupResponse = {
  deleted_cases: number
  deleted_analyses: number
}

export async function updateCaseStatus(
  token: string,
  caseId: number,
  payload: CaseStatusUpdatePayload,
): Promise<CaseItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/status`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar status do caso")
  }

  return response.json()
}

export async function cleanupDemoCases(token: string): Promise<DemoCleanupResponse> {
  const response = await fetch(`${API_URL}/cases/cleanup-demo`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao limpar casos de demonstração")
  }

  return response.json()
}

export async function createCase(token: string, payload: CaseCreatePayload): Promise<CaseItem> {
  const response = await fetch(`${API_URL}/cases`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar novo caso")
  }

  return response.json()
}

export type EditableSection = {
  key: string
  title: string
  content: string
  source?: string
  status?: string
  metadata?: Record<string, unknown>
}

export type EditableDocumentCreatePayload = {
  case_id: number
  area: string
  document_type: string
  title: string
  sections?: EditableSection[]
  notes?: string
  metadata?: Record<string, unknown>
}

export type EditableDocumentVersionCreatePayload = {
  sections?: EditableSection[]
  notes?: string
  metadata?: Record<string, unknown>
  approved?: boolean
}

export type EditableDocumentVersionItem = {
  id: number
  editable_document_id: number
  tenant_id: number
  version_number: number
  approved: boolean
  notes?: string | null
  sections: EditableSection[]
  version_metadata: Record<string, unknown>
  created_by_user_id?: number | null
  created_at: string
}

export type EditableDocumentItem = {
  id: number
  tenant_id: number
  case_id: number
  created_by_user_id?: number | null
  area: string
  document_type: string
  title: string
  status: string
  current_version_number: number
  document_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type EditableDocumentDetail = EditableDocumentItem & {
  versions: EditableDocumentVersionItem[]
}

export async function listEditableDocumentsForCase(
  token: string,
  caseId: number,
): Promise<EditableDocumentItem[]> {
  const response = await fetch(`${API_URL}/editable-documents/case/${caseId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao listar documentos editáveis do caso")
  }

  return response.json()
}

export async function getEditableDocument(
  token: string,
  documentId: number,
): Promise<EditableDocumentDetail> {
  const response = await fetch(`${API_URL}/editable-documents/${documentId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao carregar documento editável")
  }

  return response.json()
}

export async function deleteEditableDocument(
  token: string,
  documentId: number,
): Promise<{
  deleted_document_id: number
  deleted_versions_count: number
  detail: string
}> {
  const response = await fetch(`${API_URL}/editable-documents/${documentId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao excluir documento editável")
  }

  return response.json()
}

export async function createEditableDocument(
  token: string,
  payload: EditableDocumentCreatePayload,
): Promise<EditableDocumentDetail> {
  const response = await fetch(`${API_URL}/editable-documents`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar documento editável")
  }

  return response.json()
}

export async function createEditableDocumentVersion(
  token: string,
  documentId: number,
  payload: EditableDocumentVersionCreatePayload,
): Promise<EditableDocumentVersionItem> {
  const response = await fetch(`${API_URL}/editable-documents/${documentId}/versions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar nova versão do documento")
  }

  return response.json()
}


export async function generateAssistedDraft(
  token: string,
  documentId: number,
): Promise<EditableDocumentDetail> {
  const response = await fetch(`${API_URL}/editable-documents/${documentId}/generate-assisted-draft`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao gerar peça assistida a partir da análise")
  }

  return response.json()
}

