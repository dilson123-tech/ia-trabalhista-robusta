const API_URL = "http://127.0.0.1:8099/api/v1"

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
    throw new Error("Erro ao buscar casos")
  }

  return response.json()
}
