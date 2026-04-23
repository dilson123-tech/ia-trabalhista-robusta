export type PlanType = 'basic' | 'pro' | 'office'
export type PlanStatus = 'trial' | 'active' | 'past_due' | 'canceled'

export type PlanPricing = {
  type: PlanType
  label: string
  monthlyPrice: number
  formattedMonthlyPrice: string
  badge: string
  description: string
  recommendedFor: string
  onboardingNote: string
  ctaLabel: string
}

const planCatalog: Record<PlanType, PlanPricing> = {
  basic: {
    type: 'basic',
    label: 'Básico',
    monthlyPrice: 247,
    formattedMonthlyPrice: 'R$ 247/mês',
    badge: 'Entrada profissional',
    description: 'Para advogado(a) ou operação enxuta que quer ganhar organização e produtividade sem complexidade extra.',
    recommendedFor: 'Ideal para entrada controlada no produto.',
    onboardingNote: 'Implantação simples, sem promessa de customização profunda.',
    ctaLabel: 'Começar no Básico',
  },
  pro: {
    type: 'pro',
    label: 'Pro',
    monthlyPrice: 497,
    formattedMonthlyPrice: 'R$ 497/mês',
    badge: 'Mais escolhido',
    description: 'Para operação recorrente que precisa de mais capacidade, continuidade e uso mais forte da plataforma.',
    recommendedFor: 'Ideal para escritório ou operação que já validou valor e precisa subir de nível.',
    onboardingNote: 'Pode incluir apoio inicial de ativação, sem virar implantação enterprise.',
    ctaLabel: 'Fazer upgrade para Pro',
  },
  office: {
    type: 'office',
    label: 'Escritório',
    monthlyPrice: 1097,
    formattedMonthlyPrice: 'R$ 1.097/mês',
    badge: 'Estrutura avançada',
    description: 'Para escritório com uso mais intenso, mais acervo e necessidade de operação jurídica mais estruturada.',
    recommendedFor: 'Ideal para operação com maior volume e rotina consolidada.',
    onboardingNote: 'Onboarding assistido/comercial pode ser tratado à parte, conforme proposta.',
    ctaLabel: 'Solicitar plano Escritório',
  },
}

const planStatusLabelMap: Record<PlanStatus, string> = {
  trial: 'Período de teste',
  active: 'Ativo',
  past_due: 'Pagamento pendente',
  canceled: 'Cancelado',
}

export function getPlanPricing(planType: string | undefined | null): PlanPricing | null {
  if (!planType) return null
  if (planType === 'basic' || planType === 'pro' || planType === 'office') {
    return planCatalog[planType]
  }
  return null
}

export function listPlanPricing(): PlanPricing[] {
  return [planCatalog.basic, planCatalog.pro, planCatalog.office]
}

export function getPlanLabel(planType: string | undefined | null): string {
  return getPlanPricing(planType)?.label ?? 'Plano não identificado'
}

export function getPlanStatusLabel(status: string | undefined | null): string {
  if (!status) return 'Status não informado'
  if (status === 'trial' || status === 'active' || status === 'past_due' || status === 'canceled') {
    return planStatusLabelMap[status]
  }
  return status
}
