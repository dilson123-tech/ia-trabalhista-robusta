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
    throw new ApiError("Sessão expirada ou token inválido. Gere um novo token e tente novamente.", 401)
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
  status: string
  tenant_id: number
  created_at: string
  updated_at: string
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
  strategic_analysis?: Record<string, unknown>
  viability?: Record<string, unknown>
  executive_decision?: Record<string, unknown>
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

