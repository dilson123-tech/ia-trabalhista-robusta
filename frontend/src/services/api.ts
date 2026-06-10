const API_URL = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8099/api/v1').replace(/\/$/, '')

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
  client_name?: string | null
  client_whatsapp?: string | null
  client_whatsapp_consent?: boolean
  client_whatsapp_consent_at?: string | null
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
  client_name?: string
  client_whatsapp?: string
  client_whatsapp_consent?: boolean
  status?: string
}

export type CaseContactUpdatePayload = {
  client_name?: string
  client_whatsapp?: string
  client_whatsapp_consent?: boolean
}

export type LoginPayload = {
  username: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type LegalModule = {
  id: string
  label: string
  canonical_legal_area: string
  status: string
  aliases: string[]
  action_keywords: string[]
  safety_notes: string[]
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

export async function getLegalModules(): Promise<LegalModule[]> {
  const response = await fetch(`${API_URL}/legal-modules`)

  if (!response.ok) {
    await parseError(response, "Erro ao buscar módulos jurídicos")
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

export type UsageSummaryV2Response = {
  plan: {
    type: string
    status: string
  }
  limits: {
    active_cases: number
    case_records: number
    ai_analyses_per_month?: number
    cases_per_month?: number
  }
  current: {
    active_cases: number
    archived_cases: number
    case_records: number
    ai_analyses_generated?: number
    cases_created?: number
  }
  remaining: {
    active_cases: number
    case_records: number
    ai_analyses_per_month?: number
    ai_analyses?: number
    cases?: number
  }
}

type UsageSummaryV2ApiResponse = {
  plan?: {
    type?: string
    status?: string
  }
  limits?: {
    active_cases?: number
    case_records?: number
    ai_analyses_per_month?: number
    cases_per_month?: number
  }
  current?: {
    active_cases?: number
    archived_cases?: number
    case_records?: number
    ai_analyses_generated?: number
    cases_created?: number
  }
  used?: {
    active_cases?: number
    archived_cases?: number
    case_records?: number
    ai_analyses_generated?: number
    cases_created?: number
  }
  remaining?: {
    active_cases?: number
    case_records?: number
    ai_analyses_per_month?: number
    ai_analyses?: number
    cases?: number
  }
}

export async function getUsageSummaryV2(token: string): Promise<UsageSummaryV2Response> {
  const response = await fetch(`${API_URL}/usage/summary-v2`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar resumo de uso do plano")
  }

  const data = (await response.json()) as UsageSummaryV2ApiResponse
  const current = data.current ?? data.used ?? {}

  return {
    plan: {
      type: data.plan?.type ?? 'basic',
      status: data.plan?.status ?? 'active',
    },
    limits: {
      active_cases: data.limits?.active_cases ?? 0,
      case_records: data.limits?.case_records ?? 0,
      ai_analyses_per_month: data.limits?.ai_analyses_per_month ?? 0,
      cases_per_month: data.limits?.cases_per_month ?? 0,
    },
    current: {
      active_cases: current.active_cases ?? 0,
      archived_cases: current.archived_cases ?? 0,
      case_records: current.case_records ?? 0,
      ai_analyses_generated: current.ai_analyses_generated ?? 0,
      cases_created: current.cases_created ?? 0,
    },
    remaining: {
      active_cases: data.remaining?.active_cases ?? 0,
      case_records: data.remaining?.case_records ?? 0,
      ai_analyses_per_month:
        data.remaining?.ai_analyses_per_month ?? data.remaining?.ai_analyses ?? 0,
      ai_analyses: data.remaining?.ai_analyses ?? 0,
      cases: data.remaining?.cases ?? 0,
    },
  }
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


export type PlanChangeCheckoutResponse = {
  billing_request: {
    id: number
    status: string
    payment_provider: string
    provider_reference?: string
    checkout_url?: string
  }
  checkout: {
    provider: string
    provider_reference: string
    checkout_url?: string
  }
}

export async function createPlanChangeCheckout(
  token: string,
  requestedPlanType: string
): Promise<PlanChangeCheckoutResponse> {
  const response = await fetch(`${API_URL}/billing/plan-change`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      requested_plan_type: requestedPlanType,
    }),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar checkout da mudança de plano")
  }

  return response.json()
}

export type CaseAttachmentCategory =
  | "foto"
  | "video"
  | "pdf"
  | "documento_medico"
  | "notificacao"
  | "documento_pessoal"
  | "contrato"
  | "testemunha"
  | "outro"

export type CaseAttachmentItem = {
  id: number
  tenant_id: number
  case_id: number
  original_filename: string
  mime_type?: string | null
  file_size_bytes: number
  category: string
  description?: string | null
  event_date?: string | null
  created_at: string
  updated_at: string
}

export type CaseAttachmentUploadPayload = {
  file: File
  category: CaseAttachmentCategory
  description?: string
  event_date?: string
}

export type CaseAttachmentUpdatePayload = {
  category?: CaseAttachmentCategory
  description?: string
  event_date?: string
}

export async function listCaseAttachments(
  token: string,
  caseId: number,
): Promise<CaseAttachmentItem[]> {
  const response = await fetch(`${API_URL}/cases/${caseId}/attachments`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao listar provas/anexos do caso")
  }

  return response.json()
}

export async function uploadCaseAttachment(
  token: string,
  caseId: number,
  payload: CaseAttachmentUploadPayload,
): Promise<CaseAttachmentItem> {
  const formData = new FormData()
  formData.append("file", payload.file)
  formData.append("category", payload.category)

  if (payload.description?.trim()) {
    formData.append("description", payload.description.trim())
  }

  if (payload.event_date?.trim()) {
    formData.append("event_date", payload.event_date.trim())
  }

  const response = await fetch(`${API_URL}/cases/${caseId}/attachments`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    await parseError(response, "Erro ao anexar prova ao caso")
  }

  return response.json()
}

export async function updateCaseAttachment(
  token: string,
  caseId: number,
  attachmentId: number,
  payload: CaseAttachmentUpdatePayload,
): Promise<CaseAttachmentItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/attachments/${attachmentId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar prova/anexo")
  }

  return response.json()
}

export async function downloadCaseAttachment(
  token: string,
  caseId: number,
  attachmentId: number,
): Promise<Blob> {
  const response = await fetch(`${API_URL}/cases/${caseId}/attachments/${attachmentId}/download`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao baixar prova/anexo")
  }

  return response.blob()
}

export async function deleteCaseAttachment(
  token: string,
  caseId: number,
  attachmentId: number,
): Promise<void> {
  const response = await fetch(`${API_URL}/cases/${caseId}/attachments/${attachmentId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao excluir prova/anexo")
  }
}


export async function updateCaseContact(
  token: string,
  caseId: number,
  payload: CaseContactUpdatePayload,
): Promise<CaseItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/contact`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar WhatsApp do caso")
  }

  return response.json()
}


export type CaseContactLogItem = {
  id: number
  tenant_id: number
  case_id: number
  contact_type: string
  direction: string
  summary: string
  note?: string | null
  occurred_at: string
  created_by_user_id?: number | null
  created_at: string
  updated_at: string
}

export type CaseContactLogCreatePayload = {
  contact_type: string
  direction: string
  summary: string
  note?: string
}

export async function createCaseContactLog(
  token: string,
  caseId: number,
  payload: CaseContactLogCreatePayload,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/cases/${caseId}/contact-logs`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    await parseError(response, "Erro ao registrar contato")
  }
}


export async function deleteCaseContactLog(
  token: string,
  caseId: number,
  logId: number,
): Promise<void> {
  const response = await fetch(`${API_URL}/cases/${caseId}/contact-logs/${logId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao excluir contato")
  }
}


export async function listCaseContactLogs(
  token: string,
  caseId: number,
): Promise<CaseContactLogItem[]> {
  const response = await fetch(`${API_URL}/cases/${caseId}/contact-logs`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar histórico de contatos")
  }

  return response.json()
}

export type CasePartyItem = {
  id: number
  tenant_id: number
  party_state_id: number
  party_key: string
  name: string
  role: string
  party_type: string
  document_id?: string | null
  status: string
  is_original_party: boolean
  party_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type CasePartyStateItem = {
  id: number
  tenant_id: number
  case_id: number
  area: string
  state_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type CasePartyStateDetailItem = CasePartyStateItem & {
  parties: CasePartyItem[]
  representatives: unknown[]
  relationships: unknown[]
  events: unknown[]
}

export type CasePartyCreatePayload = {
  key: string
  name: string
  role: string
  party_type?: string
  document_id?: string | null
  status?: string
  is_original_party?: boolean
  metadata?: Record<string, unknown>
}

export type CasePartyUpdatePayload = {
  party_key: string
  name?: string
  role?: string
  party_type?: string
  document_id?: string | null
  metadata?: Record<string, unknown>
  description?: string
}

export type CasePartyStateCreatePayload = {
  case_id: number
  area: string
  parties?: CasePartyCreatePayload[]
  metadata?: Record<string, unknown>
}

export async function listCasePartyStates(
  token: string,
  caseId: number,
): Promise<CasePartyStateItem[]> {
  const response = await fetch(`${API_URL}/case-party-states/case/${caseId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar partes/pessoas do caso")
  }

  return response.json()
}

export async function getCasePartyState(
  token: string,
  stateId: number,
): Promise<CasePartyStateDetailItem> {
  const response = await fetch(`${API_URL}/case-party-states/${stateId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao carregar grade de pessoas do caso")
  }

  return response.json()
}

export async function createCasePartyState(
  token: string,
  payload: CasePartyStateCreatePayload,
): Promise<CasePartyStateDetailItem> {
  const response = await fetch(`${API_URL}/case-party-states`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar grade de pessoas do caso")
  }

  return response.json()
}

export async function addCaseParty(
  token: string,
  stateId: number,
  payload: CasePartyCreatePayload,
): Promise<CasePartyStateDetailItem> {
  const response = await fetch(`${API_URL}/case-party-states/${stateId}/parties`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao adicionar testemunha/depoente")
  }

  return response.json()
}

export async function updateCasePartyData(
  token: string,
  stateId: number,
  payload: CasePartyUpdatePayload,
): Promise<CasePartyStateDetailItem> {
  const response = await fetch(`${API_URL}/case-party-states/${stateId}/party-data`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar testemunha/depoente")
  }

  return response.json()
}

export async function deleteCaseParty(
  token: string,
  stateId: number,
  partyId: number,
): Promise<CasePartyStateDetailItem> {
  const response = await fetch(`${API_URL}/case-party-states/${stateId}/parties/${partyId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao remover testemunha/depoente")
  }

  return response.json()
}


export type CaseEvidenceChecklistStatus =
  | "pending"
  | "requested"
  | "received"
  | "validated"
  | "waived"
  | "needs_review"

export type CaseEvidenceChecklistPriority =
  | "low"
  | "normal"
  | "high"
  | "urgent"

export type CaseEvidenceChecklistCategory =
  | "documento"
  | "prova_documental"
  | "prova_oral"
  | "prova_tecnica"
  | "comprovante"
  | "contrato"
  | "mensagem"
  | "foto_video"
  | "documento_pessoal"
  | "outro"

export type CaseEvidenceChecklistItem = {
  id: number
  tenant_id: number
  case_id: number
  attachment_id?: number | null
  item_key: string
  title: string
  category: string
  status: string
  priority: string
  requested_from?: string | null
  due_date?: string | null
  notes?: string | null
  checklist_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type CaseEvidenceChecklistCreatePayload = {
  item_key?: string
  title: string
  category?: CaseEvidenceChecklistCategory
  status?: CaseEvidenceChecklistStatus
  priority?: CaseEvidenceChecklistPriority
  requested_from?: string
  due_date?: string
  notes?: string
  attachment_id?: number | null
  metadata?: Record<string, unknown>
}

export type CaseEvidenceChecklistUpdatePayload = {
  title?: string
  category?: CaseEvidenceChecklistCategory
  status?: CaseEvidenceChecklistStatus
  priority?: CaseEvidenceChecklistPriority
  requested_from?: string
  due_date?: string
  notes?: string
  attachment_id?: number | null
  metadata?: Record<string, unknown>
}

export async function listCaseEvidenceChecklist(
  token: string,
  caseId: number,
): Promise<CaseEvidenceChecklistItem[]> {
  const response = await fetch(`${API_URL}/cases/${caseId}/evidence-checklist`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao listar checklist de provas e pendências")
  }

  return response.json()
}

export async function createCaseEvidenceChecklistItem(
  token: string,
  caseId: number,
  payload: CaseEvidenceChecklistCreatePayload,
): Promise<CaseEvidenceChecklistItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/evidence-checklist`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar item do checklist de provas")
  }

  return response.json()
}

export async function updateCaseEvidenceChecklistItem(
  token: string,
  caseId: number,
  itemId: number,
  payload: CaseEvidenceChecklistUpdatePayload,
): Promise<CaseEvidenceChecklistItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/evidence-checklist/${itemId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar item do checklist de provas")
  }

  return response.json()
}

export async function deleteCaseEvidenceChecklistItem(
  token: string,
  caseId: number,
  itemId: number,
): Promise<void> {
  const response = await fetch(`${API_URL}/cases/${caseId}/evidence-checklist/${itemId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao excluir item do checklist de provas")
  }
}

export type CaseTimelineItem = {
  id: number
  tenant_id: number
  case_id: number
  event_date?: string | null
  title: string
  description: string
  related_evidence?: string | null
  related_witness?: string | null
  pending_note?: string | null
  sort_order: number
  timeline_metadata?: Record<string, unknown>
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type CaseTimelineCreatePayload = {
  event_date?: string
  title: string
  description: string
  related_evidence?: string
  related_witness?: string
  pending_note?: string
  sort_order?: number
  metadata?: Record<string, unknown>
}

export type CaseTimelineUpdatePayload = Partial<CaseTimelineCreatePayload>

export async function listCaseTimeline(
  token: string,
  caseId: number,
): Promise<CaseTimelineItem[]> {
  const response = await fetch(`${API_URL}/cases/${caseId}/timeline`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao buscar linha do tempo do caso")
  }

  return response.json()
}

export async function createCaseTimelineItem(
  token: string,
  caseId: number,
  payload: CaseTimelineCreatePayload,
): Promise<CaseTimelineItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/timeline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao criar item da linha do tempo")
  }

  return response.json()
}

export async function updateCaseTimelineItem(
  token: string,
  caseId: number,
  itemId: number,
  payload: CaseTimelineUpdatePayload,
): Promise<CaseTimelineItem> {
  const response = await fetch(`${API_URL}/cases/${caseId}/timeline/${itemId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await parseError(response, "Erro ao atualizar item da linha do tempo")
  }

  return response.json()
}

export async function deleteCaseTimelineItem(
  token: string,
  caseId: number,
  itemId: number,
): Promise<void> {
  const response = await fetch(`${API_URL}/cases/${caseId}/timeline/${itemId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    await parseError(response, "Erro ao excluir item da linha do tempo")
  }
}
