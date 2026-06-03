import './App.css'
import { useEffect, useState, type KeyboardEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, cleanupDemoCases, createPlanChangeCheckout, createCase, createCaseContactLog, createCasePartyState, addCaseParty, getCasePartyState, getCases, listCaseAttachments, listCaseContactLogs, listCaseEvidenceChecklist, listCasePartyStates, getCaseAnalysis, getLegalModules, getExecutiveSummary, getExecutiveReport, getExecutivePdf, getUsageSummaryV2, login, updateCaseStatus, type CaseAttachmentItem, type CaseContactLogItem, type CaseEvidenceChecklistItem, type CaseItem, type CasePartyStateDetailItem, type CaseAnalysisResponse, type ExecutiveSummaryResponse, type ExecutiveReportResponse, type LegalModule, type UsageSummaryV2Response } from './services/api'
import { ExpansionWorkspace } from './components/expansion/ExpansionWorkspace'
import { CaseFiltersBar } from './components/CaseFiltersBar'
import { CaseCard, type CaseInternalDossierSnapshot, type CaseReadinessSnapshot } from './components/CaseCard'
import { DashboardTopPanel } from './components/DashboardTopPanel'
import { LoginPanel } from './components/LoginPanel'
import { CaseFocusPanel } from './components/CaseFocusPanel'
import { getPlanLabel as getCatalogPlanLabel, getPlanPricing, getPlanStatusLabel as getCatalogPlanStatusLabel, listPlanPricing } from './config/pricing'

const AUTH_TOKEN_STORAGE_KEY = 'ia_trabalhista_auth_token'

type WhatsAppContactTemplateKey = 'documents' | 'evidence' | 'hearing' | 'status_update' | 'confirm_data'

const WHATSAPP_CONTACT_TEMPLATES: Record<
  WhatsAppContactTemplateKey,
  { label: string; summary: string; message: string }
> = {
  documents: {
    label: 'Pedir documentos',
    summary: 'Solicitação de documentos pelo WhatsApp',
    message:
      'Olá, estamos entrando em contato sobre seu caso. Por favor, envie os documentos relacionados ao processo para que possamos avançar na análise.',
  },
  evidence: {
    label: 'Pedir provas',
    summary: 'Solicitação de provas pelo WhatsApp',
    message:
      'Olá, estamos entrando em contato sobre seu caso. Por favor, envie as provas que tiver disponíveis, como fotos, vídeos, comprovantes, prints, conversas ou documentos relacionados.',
  },
  hearing: {
    label: 'Lembrar audiência',
    summary: 'Lembrete de audiência pelo WhatsApp',
    message:
      'Olá, estamos entrando em contato para lembrar sobre a audiência do seu caso. Por favor, confirme o recebimento desta mensagem e mantenha atenção às orientações do escritório.',
  },
  status_update: {
    label: 'Avisar andamento',
    summary: 'Aviso de andamento pelo WhatsApp',
    message:
      'Olá, estamos entrando em contato para informar que houve andamento no seu caso. Em caso de dúvida, responda esta mensagem para alinharmos os próximos passos.',
  },
  confirm_data: {
    label: 'Confirmar dados',
    summary: 'Confirmação de dados pelo WhatsApp',
    message:
      'Olá, estamos entrando em contato sobre seu caso. Por favor, confirme se seus dados de contato e informações principais continuam corretos.',
  },
}

function App() {
  const [token, setToken] = useState(() => {
    if (typeof window === 'undefined') return ''
    return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) ?? ''
  })
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [sessionBootstrapPending, setSessionBootstrapPending] = useState(() => Boolean(token.trim()))
  const [authLoading, setAuthLoading] = useState(false)
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [activeFocusTab, setActiveFocusTab] = useState<'analysis' | 'summary' | 'report'>('analysis')
  const [analysisData, setAnalysisData] = useState<CaseAnalysisResponse | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisError, setAnalysisError] = useState('')
  const [executiveSummaryData, setExecutiveSummaryData] = useState<ExecutiveSummaryResponse | null>(null)
  const [executiveSummaryLoading, setExecutiveSummaryLoading] = useState(false)
  const [executiveSummaryError, setExecutiveSummaryError] = useState('')
  const [executiveReportData, setExecutiveReportData] = useState<ExecutiveReportResponse | null>(null)
  const [executiveReportLoading, setExecutiveReportLoading] = useState(false)
  const [executiveReportError, setExecutiveReportError] = useState('')
  const [executivePdfLoading, setExecutivePdfLoading] = useState(false)
  const [executivePdfError, setExecutivePdfError] = useState('')
  const [showNewCaseForm, setShowNewCaseForm] = useState(false)
  const [newCaseLoading, setNewCaseLoading] = useState(false)
  const [newCaseError, setNewCaseError] = useState('')
  const [newCaseSuccess, setNewCaseSuccess] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [loginFormKey, setLoginFormKey] = useState(0)
  const [loginFieldsUnlocked, setLoginFieldsUnlocked] = useState(false)
  const [caseSearchTerm, setCaseSearchTerm] = useState('')
  const [caseStatusFilter, setCaseStatusFilter] = useState('main')
  const [caseActionLoadingId, setCaseActionLoadingId] = useState<number | null>(null)
  const [caseActionError, setCaseActionError] = useState('')
  const [caseActionSuccess, setCaseActionSuccess] = useState('')
  const [contactLogsByCaseId, setContactLogsByCaseId] = useState<Record<number, CaseContactLogItem[]>>({})
  const [contactLogsLoadingId, setContactLogsLoadingId] = useState<number | null>(null)
  const [partyStatesByCaseId, setPartyStatesByCaseId] = useState<Record<number, CasePartyStateDetailItem | null>>({})
  const [witnessGridLoadingId, setWitnessGridLoadingId] = useState<number | null>(null)
  const [readinessByCaseId, setReadinessByCaseId] = useState<Record<number, CaseReadinessSnapshot | null>>({})
  const [readinessLoadingId, setReadinessLoadingId] = useState<number | null>(null)
  const [caseDossiersByCaseId, setCaseDossiersByCaseId] = useState<Record<number, CaseInternalDossierSnapshot | null>>({})
  const [dossierLoadingId, setDossierLoadingId] = useState<number | null>(null)
  const [cleanupDemoLoading, setCleanupDemoLoading] = useState(false)
  const [usageSummary, setUsageSummary] = useState<UsageSummaryV2Response | null>(null)
  const [usageLoading, setUsageLoading] = useState(false)
  const [usageError, setUsageError] = useState('')
  const [legalModules, setLegalModules] = useState<LegalModule[]>([])
  const [legalModulesLoading, setLegalModulesLoading] = useState(false)
  const [legalModulesError, setLegalModulesError] = useState('')
  const [planActionNotice, setPlanActionNotice] = useState('')
  const [planPanelCollapsed, setPlanPanelCollapsed] = useState(false)
  const [planWorkspaceView, setPlanWorkspaceView] = useState<'capacity' | 'commercial'>('capacity')
  const [dashboardWorkspace, setDashboardWorkspace] = useState<'production' | 'commercial'>('production')
  const [pieceReadyRequestId, setPieceReadyRequestId] = useState(0)
  const [pieceReadyNotice, setPieceReadyNotice] = useState('')
  const [expansionModuleTarget, setExpansionModuleTarget] = useState<'editor' | 'succession' | 'appeals'>('editor')
  const navigate = useNavigate()
  const location = useLocation()
  const isLoginRoute = location.pathname === '/login'

  const statusLabelMap: Record<string, string> = {
    draft: 'Rascunho',
    active: 'Ativo',
    review: 'Em revisão',
    archived: 'Arquivado',
  }

  const riskLabelMap: Record<string, string> = {
    high: 'Alto',
    medium: 'Médio',
    low: 'Baixo',
  }

  const legalModuleStatusLabelMap: Record<string, string> = {
    operational_real_supervised: 'Operacional supervisionado',
    operational_initial_package: 'Pacote inicial validado',
    qa_existing: 'Base QA existente',
    qa_existing_to_formalize: 'Base pronta para formalizar',
  }

  function getStatusLabel(status: string) {
    return statusLabelMap[status] ?? status
  }

  function getRiskLabel(risk: string | undefined) {
    if (!risk) return 'Não informado'
    return riskLabelMap[risk] ?? risk
  }

  function getLegalModuleStatusLabel(status: string) {
    return legalModuleStatusLabelMap[status] ?? status
  }

  function getPlanLabel(planType: string | undefined) {
    return getCatalogPlanLabel(planType)
  }

  function getPlanStatusLabel(status: string | undefined) {
    return getCatalogPlanStatusLabel(status)
  }

  async function handlePlanAction(planType: string, planLabel: string) {
    if (planType === usagePlanType) {
      setPlanActionNotice(`Você já está no plano ${planLabel}.`)
      return
    }

    try {
      setPlanActionNotice(`Criando checkout para o plano ${planLabel}...`)
      const checkout = await createPlanChangeCheckout(token, planType)

      const checkoutUrl = checkout.checkout.checkout_url ?? ''
      if (checkoutUrl) {
        window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
        setPlanActionNotice(`Checkout do plano ${planLabel} aberto em nova aba.`)
      } else {
        setPlanActionNotice(`Checkout criado para o plano ${planLabel}, mas o link não foi retornado.`)
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Erro ao iniciar mudança de plano.'
      setPlanActionNotice(message)
    }
  }

  function getCapacityPercent(current: number, limit: number) {
    if (limit <= 0) return 0
    return Math.min((current / limit) * 100, 100)
  }

  function formatCapacityPercent(value: number) {
    if (!Number.isFinite(value) || value <= 0) return '0%'
    if (value >= 100) return '100%'
    return `${Math.floor(value)}%`
  }

  function sortCasesForDisplay(list: CaseItem[]) {
    const statusPriority: Record<string, number> = {
      active: 0,
      draft: 1,
      review: 2,
      archived: 3,
    }

    return [...list].sort((a, b) => {
      const statusDiff = (statusPriority[a.status] ?? 99) - (statusPriority[b.status] ?? 99)
      if (statusDiff !== 0) return statusDiff

      const aTime = new Date(a.updated_at || a.created_at).getTime()
      const bTime = new Date(b.updated_at || b.created_at).getTime()
      return bTime - aTime
    })
  }

  const [newCaseForm, setNewCaseForm] = useState({
    case_number: '',
    title: '',
    description: '',
    legal_area: 'trabalhista',
    action_type: '',
    client_name: '',
    client_whatsapp: '',
    client_whatsapp_consent: false,
    status: 'draft',
  })

  const normalizedCaseSearch = caseSearchTerm.trim().toLowerCase()

  const filteredCases = cases.filter((caso) => {
    const statusMatches =
      caseStatusFilter === 'all'
        ? true
        : caseStatusFilter === 'main'
          ? caso.status !== 'archived'
          : caso.status === caseStatusFilter

    if (!statusMatches) return false

    if (!normalizedCaseSearch) return true

    const haystack = `${caso.case_number} ${caso.title} ${caso.description ?? ''} ${caso.client_name ?? ''} ${caso.client_whatsapp ?? ''}`.toLowerCase()
    return haystack.includes(normalizedCaseSearch)
  })

  const selectedCase = selectedCaseId ? cases.find((caso) => caso.id === selectedCaseId) ?? null : null

  const usagePlanType = usageSummary?.plan?.type ?? 'basic'
  const usagePlanStatus = usageSummary?.plan?.status ?? 'active'
  const currentPlanPricing = getPlanPricing(usagePlanType)
  const planActionOptions = listPlanPricing().filter((plan) => plan.type !== usagePlanType)
  const usageActiveCurrent = usageSummary?.current?.active_cases ?? 0
  const usageArchivedCurrent = usageSummary?.current?.archived_cases ?? 0
  const usageRecordsCurrent = usageSummary?.current?.case_records ?? 0
  const usageActiveLimit = usageSummary?.limits?.active_cases ?? 0
  const usageRecordsLimit = usageSummary?.limits?.case_records ?? 0
  const usageActiveRemaining = usageSummary?.remaining?.active_cases ?? 0
  const usageRecordsRemaining = usageSummary?.remaining?.case_records ?? 0
  const usageActivePercent = getCapacityPercent(usageActiveCurrent, usageActiveLimit)
  const usageRecordsPercent = getCapacityPercent(usageRecordsCurrent, usageRecordsLimit)

  useEffect(() => {
    if (!token.trim()) return
    if (!sessionBootstrapPending) return
    if (authLoading) return

    void (async () => {
      try {
        await refreshPortfolioAndUsage(token)
      } finally {
        setSessionBootstrapPending(false)
      }
    })()
  }, [token, authLoading, sessionBootstrapPending])

  if (!isLoginRoute && !token.trim()) {
    return <Navigate to="/login" replace />
  }

  if (isLoginRoute && token.trim()) {
    return <Navigate to="/" replace />
  }

  const isBootstrappingSession =
    !isLoginRoute &&
    Boolean(token.trim()) &&
    (sessionBootstrapPending || (!loaded && (loading || usageLoading)))

  if (isBootstrappingSession) {
    return (
      <main className="app-shell">
        <section className="app-container">
          <section className="insight-card">
            <div className="insight-head">
              <div>
                <p className="insight-kicker">Sessão persistida</p>
                <h2 className="insight-title">Restaurando painel do advogado</h2>
                <p className="insight-description">
                  Recarregando carteira, capacidade do plano e contexto operacional sem sair do painel.
                </p>
              </div>
              <span className="insight-badge">Reidratação em andamento</span>
            </div>

            <p className="insight-empty">
              Aguarde um instante. Sua sessão foi preservada e os dados estão sendo carregados novamente.
            </p>
          </section>
        </section>
      </main>
    )
  }

  function clearSession() {
    setToken('')
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
    }
    setUsername('')
    setPassword('')
    setCases([])
    setLoaded(false)
    setSelectedCaseId(null)
    setAnalysisData(null)
    setExecutiveSummaryData(null)
    setExecutiveReportData(null)
    setError('')
    setLoginFieldsUnlocked(false)
    setLoginFormKey((prev) => prev + 1)
    setAnalysisError('')
    setExecutiveSummaryError('')
    setExecutiveReportError('')
    setExecutivePdfError('')
    setShowToken(false)
    setShowNewCaseForm(false)
    setNewCaseError('')
    setNewCaseSuccess('')
    setCaseActionError('')
    setCaseActionSuccess('')
    setContactLogsByCaseId({})
    setPartyStatesByCaseId({})
    setWitnessGridLoadingId(null)
    setCaseSearchTerm('')
    setCaseStatusFilter('main')
    setCleanupDemoLoading(false)
    setCaseActionLoadingId(null)
    setUsageSummary(null)
    setUsageLoading(false)
    setUsageError('')
    setPieceReadyNotice('')
    setSessionBootstrapPending(false)
    setLoginFieldsUnlocked(false)
    setLoginFormKey((prev) => prev + 1)
  }

  function handleApiFailure(err: unknown, fallbackMessage: string) {
    console.error(err)

    if (err instanceof ApiError && err.status === 401) {
      clearSession()
      setError(err.message)
      navigate('/login')
      return
    }

    setError('')
    return fallbackMessage
  }

  async function refreshPortfolioAndUsage(authToken: string) {
    setLoading(true)
    setUsageLoading(true)
    setLegalModulesLoading(true)
    setError('')
    setUsageError('')
    setLegalModulesError('')

    try {
      const [casesData, usageData] = await Promise.all([
        getCases(authToken),
        getUsageSummaryV2(authToken),
      ])

      setCases(sortCasesForDisplay(casesData))
      setUsageSummary(usageData)

      try {
        const legalModulesData = await getLegalModules()
        setLegalModules(legalModulesData)
      } catch (err) {
        console.error(err)
        setLegalModules([])
        setLegalModulesError('Não foi possível carregar os módulos jurídicos oficiais.')
      }

      setLoaded(true)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar os dados principais do painel.')
      if (fallback) {
        setError(fallback)
        setUsageError(fallback)
        setLoaded(true)
      }
    } finally {
      setLoading(false)
      setUsageLoading(false)
      setLegalModulesLoading(false)
    }
  }

  async function handleLoadCases() {
    await refreshPortfolioAndUsage(token)
  }

  async function handleLogin() {
    setAuthLoading(true)
    setError('')

    try {
      const auth = await login({
        username: username.trim(),
        password,
      })

      setToken(auth.access_token)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, auth.access_token)
      }

      await refreshPortfolioAndUsage(auth.access_token)
      setShowToken(false)
      setPassword('')
      navigate('/')
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível autenticar no sistema.')
      if (fallback) {
        setError(fallback)
      }
    } finally {
      setAuthLoading(false)
    }
  }



  function handleLoginKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Enter') return
    event.preventDefault()

    if (authLoading || !username.trim() || !password.trim()) return
    void handleLogin()
  }

  async function handleAnalyzeCase(caseId: number) {
    setAnalysisLoading(true)
    setAnalysisError('')
    setSelectedCaseId(caseId)

    try {
      const data = await getCaseAnalysis(token, caseId)
      setAnalysisData(data)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível analisar o caso selecionado.')
      if (fallback) {
        setAnalysisError(fallback)
      }
    } finally {
      setAnalysisLoading(false)
    }
  }

  async function handleLoadExecutiveSummary(caseId: number) {
    setExecutiveSummaryLoading(true)
    setExecutiveSummaryError('')
    setSelectedCaseId(caseId)

    try {
      const data = await getExecutiveSummary(token, caseId)
      setExecutiveSummaryData(data)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar o resumo executivo do caso.')
      if (fallback) {
        setExecutiveSummaryError(fallback)
      }
    } finally {
      setExecutiveSummaryLoading(false)
    }
  }

  async function handleLoadExecutiveReport(caseId: number) {
    setExecutiveReportLoading(true)
    setExecutiveReportError('')
    setSelectedCaseId(caseId)

    try {
      const data = await getExecutiveReport(token, caseId)
      setExecutiveReportData(data)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar o relatório executivo do caso.')
      if (fallback) {
        setExecutiveReportError(fallback)
      }
    } finally {
      setExecutiveReportLoading(false)
    }
  }

  async function handleOpenExecutivePdf(caseId: number) {
    setExecutivePdfLoading(true)
    setExecutivePdfError('')
    setSelectedCaseId(caseId)

    try {
      const pdfBlob = await getExecutivePdf(token, caseId)
      const pdfUrl = window.URL.createObjectURL(pdfBlob)
      window.open(pdfUrl, '_blank', 'noopener,noreferrer')
      window.setTimeout(() => window.URL.revokeObjectURL(pdfUrl), 60000)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível abrir o PDF executivo do caso.')
      if (fallback) {
        setExecutivePdfError(fallback)
      }
    } finally {
      setExecutivePdfLoading(false)
    }
  }


  function countWitnessParties(partyState: CasePartyStateDetailItem | null) {
    return (partyState?.parties ?? []).filter((party) => {
      const role = party.role.toLowerCase()
      return (
        role.includes('testemunha') ||
        role.includes('depoente') ||
        role.includes('preposto') ||
        role.includes('representante') ||
        role.includes('perito') ||
        role.includes('fiscal') ||
        role.includes('cuidador') ||
        role.includes('vizinho')
      )
    }).length
  }

  function buildCaseReadinessSnapshot(
    caso: CaseItem,
    contactLogs: CaseContactLogItem[],
    partyState: CasePartyStateDetailItem | null,
    attachments: CaseAttachmentItem[],
    checklistItems: CaseEvidenceChecklistItem[],
  ): CaseReadinessSnapshot {
    const witnessCount = countWitnessParties(partyState)
    const openChecklistCount = checklistItems.filter((item) =>
      ['pending', 'requested', 'needs_review'].includes(item.status),
    ).length
    const validatedChecklistCount = checklistItems.filter((item) => item.status === 'validated').length

    const checks = [
      {
        label: 'Cliente/contato cadastrado',
        ok: Boolean(caso.client_name || caso.client_whatsapp),
        weight: 12,
        missing: 'Cadastrar cliente ou contato principal do caso.',
      },
      {
        label: 'WhatsApp informado',
        ok: Boolean(caso.client_whatsapp),
        weight: 12,
        missing: 'Informar WhatsApp do cliente para comunicação operacional.',
      },
      {
        label: 'Consentimento WhatsApp',
        ok: Boolean(caso.client_whatsapp_consent),
        weight: 10,
        missing: 'Confirmar autorização de contato por WhatsApp.',
      },
      {
        label: 'Histórico de contato',
        ok: contactLogs.length > 0,
        weight: 14,
        missing: 'Registrar pelo menos um contato com o cliente.',
      },
      {
        label: 'Testemunhas/depoentes',
        ok: witnessCount > 0,
        weight: 14,
        missing: 'Cadastrar testemunha, depoente, preposto ou pessoa relevante.',
      },
      {
        label: 'Checklist de provas',
        ok: checklistItems.length > 0 && openChecklistCount === 0,
        weight: 20,
        missing:
          checklistItems.length === 0
            ? 'Cadastrar checklist de provas e pendências.'
            : `Resolver ${openChecklistCount} pendência(s) aberta(s) no checklist.`,
      },
      {
        label: 'Anexos/provas',
        ok: attachments.length > 0,
        weight: 18,
        missing: 'Anexar pelo menos uma prova/documento ao caso.',
      },
    ]

    const score = checks.reduce((sum, check) => sum + (check.ok ? check.weight : 0), 0)
    const missingItems = checks.filter((check) => !check.ok).map((check) => check.missing)

    let statusLabel = 'Crítico'
    let statusTone: CaseReadinessSnapshot['statusTone'] = 'critical'

    if (score >= 85) {
      statusLabel = 'Pronto para revisão do advogado'
      statusTone = 'ready'
    } else if (score >= 65) {
      statusLabel = 'Quase pronto'
      statusTone = 'almost'
    } else if (score >= 40) {
      statusLabel = 'Em preparação'
      statusTone = 'preparing'
    }

    return {
      score,
      statusLabel,
      statusTone,
      contactLogCount: contactLogs.length,
      witnessCount,
      attachmentCount: attachments.length,
      checklistTotal: checklistItems.length,
      checklistOpen: openChecklistCount,
      checklistValidated: validatedChecklistCount,
      missingItems,
      loadedAt: new Date().toISOString(),
    }
  }

  async function handleLoadCaseContactLogs(caseId: number) {
    setContactLogsLoadingId(caseId)
    setCaseActionError('')

    try {
      const logs = await listCaseContactLogs(token, caseId)
      setContactLogsByCaseId((prev) => ({
        ...prev,
        [caseId]: logs,
      }))
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar o histórico de contatos.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setContactLogsLoadingId(null)
    }
  }


  async function handleLoadWitnessGrid(caseId: number) {
    setWitnessGridLoadingId(caseId)
    setCaseActionError('')
    setSelectedCaseId(caseId)

    try {
      const states = await listCasePartyStates(token, caseId)
      if (states.length === 0) {
        setPartyStatesByCaseId((prev) => ({
          ...prev,
          [caseId]: null,
        }))
        setCaseActionSuccess('Nenhuma grade de pessoas criada ainda para este caso.')
        return
      }

      const detail = await getCasePartyState(token, states[0].id)
      setPartyStatesByCaseId((prev) => ({
        ...prev,
        [caseId]: detail,
      }))
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar a grade de testemunhas/depoentes.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setWitnessGridLoadingId(null)
    }
  }

  async function handleAddWitnessToCase(caso: CaseItem) {
    const name = window.prompt('Nome da testemunha/depoente:')
    if (!name?.trim()) return

    const role =
      window.prompt(
        'Papel na audiência/prova oral:',
        'testemunha',
      )?.trim() || 'testemunha'

    const whatKnows =
      window.prompt(
        'O que essa pessoa sabe ou confirma? Pode deixar curto para o V1:',
        '',
      )?.trim() || 'A revisar com o advogado.'

    setWitnessGridLoadingId(caso.id)
    setCaseActionError('')
    setCaseActionSuccess('')
    setSelectedCaseId(caso.id)

    try {
      const existingStates = await listCasePartyStates(token, caso.id)
      const existingState =
        existingStates.length > 0 ? await getCasePartyState(token, existingStates[0].id) : null

      const partyPayload = {
        key: `witness_${Date.now()}`,
        name: name.trim(),
        role,
        party_type: 'person',
        status: 'active',
        is_original_party: true,
        metadata: {
          grid_source: 'case_witness_grid_v1',
          preparation_status: 'pendente',
          what_knows: whatKnows,
          confirms_facts: whatKnows,
          risk_level: 'a revisar',
          sensitive_points: 'A revisar pelo advogado antes da audiência.',
          recommended_questions: 'A gerar/refinar na Audiência Estratégica.',
          dangerous_questions: 'Evitar perguntas que induzam resposta ou sugiram versão pronta.',
        },
      }

      const nextState = existingState
        ? await addCaseParty(token, existingState.id, partyPayload)
        : await createCasePartyState(token, {
            case_id: caso.id,
            area: caso.legal_area || 'civel',
            parties: [partyPayload],
            metadata: {
              source: 'case_witness_grid_v1',
              witness_grid_enabled: true,
            },
          })

      setPartyStatesByCaseId((prev) => ({
        ...prev,
        [caso.id]: nextState,
      }))
      setCaseActionSuccess('Testemunha/depoente adicionado à grade do caso.')
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível adicionar testemunha/depoente ao caso.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setWitnessGridLoadingId(null)
    }
  }



  function buildCaseInternalDossierSnapshot(
    caso: CaseItem,
    contactLogs: CaseContactLogItem[],
    partyState: CasePartyStateDetailItem | null,
    attachments: CaseAttachmentItem[],
    checklistItems: CaseEvidenceChecklistItem[],
    readiness: CaseReadinessSnapshot,
  ): CaseInternalDossierSnapshot {
    const witnessParties = (partyState?.parties ?? []).filter((party) => {
      const role = party.role.toLowerCase()
      return (
        role.includes('testemunha') ||
        role.includes('depoente') ||
        role.includes('preposto') ||
        role.includes('representante') ||
        role.includes('perito') ||
        role.includes('fiscal') ||
        role.includes('cuidador') ||
        role.includes('vizinho')
      )
    })

    const openChecklistItems = checklistItems.filter((item) =>
      ['pending', 'requested', 'needs_review'].includes(item.status),
    )

    const nextSteps = [
      ...readiness.missingItems,
      ...(openChecklistItems.length > 0
        ? openChecklistItems.slice(0, 4).map((item) => `Resolver pendência: ${item.title}`)
        : []),
    ]

    if (nextSteps.length === 0) {
      nextSteps.push('Revisar o caso com o advogado antes de qualquer protocolo.')
    }

    return {
      caseId: caso.id,
      caseTitle: caso.title,
      caseNumber: caso.case_number,
      clientName: caso.client_name || 'Cliente não informado',
      clientWhatsapp: caso.client_whatsapp || 'WhatsApp não informado',
      readinessScore: readiness.score,
      readinessStatus: readiness.statusLabel,
      contactLogCount: contactLogs.length,
      witnessCount: witnessParties.length,
      attachmentCount: attachments.length,
      checklistTotal: checklistItems.length,
      checklistOpen: readiness.checklistOpen,
      checklistValidated: readiness.checklistValidated,
      lastContactSummary: contactLogs[0]?.summary || null,
      keyPeople: witnessParties.slice(0, 5).map((party) => `${party.name} — ${party.role}`),
      evidenceSummary: attachments.slice(0, 5).map((attachment) => `${attachment.original_filename} — ${attachment.category}`),
      openChecklistItems: openChecklistItems.slice(0, 5).map((item) => `${item.title} — ${item.status}`),
      nextSteps: nextSteps.slice(0, 6),
      loadedAt: new Date().toISOString(),
    }
  }

  async function handleLoadCaseReadiness(caso: CaseItem) {
    setReadinessLoadingId(caso.id)
    setCaseActionError('')
    setCaseActionSuccess('')
    setSelectedCaseId(caso.id)

    try {
      const [contactLogs, states, attachments, checklistItems] = await Promise.all([
        listCaseContactLogs(token, caso.id),
        listCasePartyStates(token, caso.id),
        listCaseAttachments(token, caso.id),
        listCaseEvidenceChecklist(token, caso.id),
      ])

      const partyState =
        states.length > 0 ? await getCasePartyState(token, states[0].id) : null

      setContactLogsByCaseId((prev) => ({
        ...prev,
        [caso.id]: contactLogs,
      }))

      setPartyStatesByCaseId((prev) => ({
        ...prev,
        [caso.id]: partyState,
      }))

      setReadinessByCaseId((prev) => ({
        ...prev,
        [caso.id]: buildCaseReadinessSnapshot(caso, contactLogs, partyState, attachments, checklistItems),
      }))

      setCaseActionSuccess('Prontidão do caso atualizada.')
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível calcular a prontidão do caso.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setReadinessLoadingId(null)
    }
  }


  async function handleLoadCaseDossier(caso: CaseItem) {
    setDossierLoadingId(caso.id)
    setCaseActionError('')
    setCaseActionSuccess('')
    setSelectedCaseId(caso.id)

    try {
      const [contactLogs, states, attachments, checklistItems] = await Promise.all([
        listCaseContactLogs(token, caso.id),
        listCasePartyStates(token, caso.id),
        listCaseAttachments(token, caso.id),
        listCaseEvidenceChecklist(token, caso.id),
      ])

      const partyState =
        states.length > 0 ? await getCasePartyState(token, states[0].id) : null

      const readiness = buildCaseReadinessSnapshot(caso, contactLogs, partyState, attachments, checklistItems)
      const dossier = buildCaseInternalDossierSnapshot(
        caso,
        contactLogs,
        partyState,
        attachments,
        checklistItems,
        readiness,
      )

      setContactLogsByCaseId((prev) => ({
        ...prev,
        [caso.id]: contactLogs,
      }))

      setPartyStatesByCaseId((prev) => ({
        ...prev,
        [caso.id]: partyState,
      }))

      setReadinessByCaseId((prev) => ({
        ...prev,
        [caso.id]: readiness,
      }))

      setCaseDossiersByCaseId((prev) => ({
        ...prev,
        [caso.id]: dossier,
      }))

      setCaseActionSuccess('Dossiê interno do caso atualizado.')
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível montar o dossiê interno do caso.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setDossierLoadingId(null)
    }
  }

  async function handleOpenWhatsAppTemplate(
    caseId: number,
    whatsapp: string,
    templateKey: WhatsAppContactTemplateKey,
  ) {
    const digits = whatsapp.replace(/\D/g, '')
    const template = WHATSAPP_CONTACT_TEMPLATES[templateKey]

    if (!digits) {
      setCaseActionError('WhatsApp do cliente não informado.')
      return
    }

    setCaseActionLoadingId(caseId)
    setCaseActionError('')
    setCaseActionSuccess('')
    setSelectedCaseId(caseId)

    try {
      await createCaseContactLog(token, caseId, {
        contact_type: 'whatsapp',
        direction: 'outgoing',
        summary: template.summary,
        note: `Mensagem pronta aberta: ${template.label}`,
      })
      await handleLoadCaseContactLogs(caseId)

      const url = `https://wa.me/${digits}?text=${encodeURIComponent(template.message)}`
      window.open(url, '_blank', 'noopener,noreferrer')
      setCaseActionSuccess(`${template.label}: WhatsApp aberto e contato registrado.`)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível abrir e registrar a mensagem pronta.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setCaseActionLoadingId(null)
    }
  }

  async function handleRegisterWhatsAppContact(caseId: number) {
    setCaseActionLoadingId(caseId)
    setCaseActionError('')
    setCaseActionSuccess('')
    setSelectedCaseId(caseId)

    try {
      await createCaseContactLog(token, caseId, {
        contact_type: 'whatsapp',
        direction: 'outgoing',
        summary: 'Contato realizado via WhatsApp',
      })
      await handleLoadCaseContactLogs(caseId)

      setCaseActionSuccess('Contato via WhatsApp registrado com sucesso.')
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível registrar o contato via WhatsApp.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setCaseActionLoadingId(null)
    }
  }

  function handleNewCaseFieldChange(
    field: 'case_number' | 'title' | 'description' | 'legal_area' | 'action_type' | 'client_name' | 'client_whatsapp' | 'client_whatsapp_consent' | 'status',
    value: string | boolean,
  ) {
    setNewCaseForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  async function handleCreateNewCase() {
    setNewCaseLoading(true)
    setNewCaseError('')
    setNewCaseSuccess('')

    try {
      const createdCase = await createCase(token, {
        case_number: newCaseForm.case_number.trim(),
        title: newCaseForm.title.trim(),
        description: newCaseForm.description.trim() || undefined,
        legal_area: newCaseForm.legal_area,
        action_type: newCaseForm.action_type.trim() || undefined,
        client_name: newCaseForm.client_name.trim() || undefined,
        client_whatsapp: newCaseForm.client_whatsapp.replace(/\D/g, '') || undefined,
        client_whatsapp_consent: Boolean(newCaseForm.client_whatsapp_consent),
        status: newCaseForm.status,
      })

      await refreshPortfolioAndUsage(token)
      setSelectedCaseId(createdCase.id)
      setCaseActionError('')
      setCaseActionSuccess('')
      setShowNewCaseForm(false)
      setNewCaseForm({
        case_number: '',
        title: '',
        description: '',
        legal_area: 'trabalhista',
        action_type: '',
        client_name: '',
        client_whatsapp: '',
        client_whatsapp_consent: false,
        status: 'draft',
      })
      setNewCaseSuccess(`Caso "${createdCase.title}" criado com sucesso.`)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível criar o novo caso.')
      if (fallback) {
        setNewCaseError(fallback)
      }
    } finally {
      setNewCaseLoading(false)
    }
  }

  async function handleArchiveCase(caseId: number) {
    setCaseActionLoadingId(caseId)
    setCaseActionError('')
    setCaseActionSuccess('')

    try {
      const updatedCase = await updateCaseStatus(token, caseId, { status: 'archived' })

      await refreshPortfolioAndUsage(token)
      setSelectedCaseId(caseId)
      setCaseActionSuccess(`Caso "${updatedCase.title}" arquivado com sucesso.`)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível arquivar o caso selecionado.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setCaseActionLoadingId(null)
    }
  }

  async function handleCleanupDemo() {
    const confirmed = window.confirm(
      'Isso vai remover permanentemente os casos de demonstração com prefixo DEMO-. Deseja continuar?',
    )

    if (!confirmed) return

    setCleanupDemoLoading(true)
    setCaseActionError('')
    setCaseActionSuccess('')

    try {
      const result = await cleanupDemoCases(token)
      await refreshPortfolioAndUsage(token)
      setCaseActionSuccess(
        `Limpeza concluída: ${result.deleted_cases} caso(s) demo e ${result.deleted_analyses} análise(s) removidos.`,
      )
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível limpar os casos de demonstração.')
      if (fallback) {
        setCaseActionError(fallback)
      }
    } finally {
      setCleanupDemoLoading(false)
    }
  }

    if (isLoginRoute) {
    return (
      <LoginPanel
        token={token}
        loginFormKey={loginFormKey}
        username={username}
        password={password}
        showToken={showToken}
        authLoading={authLoading}
        error={error}
        loginFieldsUnlocked={loginFieldsUnlocked}
        onGoToPanel={() => navigate('/')}
        onUsernameChange={setUsername}
        onPasswordChange={setPassword}
        onUnlockFields={() => setLoginFieldsUnlocked(true)}
        onToggleShowToken={() => setShowToken((prev) => !prev)}
        onLogin={handleLogin}
        onLoginKeyDown={handleLoginKeyDown}
        onClear={() => {
          setShowToken(false)
          setUsername('')
          setPassword('')
          setError('')
        }}
      />
    )
  }

  return (
    <main className="app-shell">
      <section className="app-container">
        <DashboardTopPanel
          showNewCaseForm={showNewCaseForm}
          onToggleNewCaseForm={() => {
            setShowNewCaseForm((prev) => !prev)
            setNewCaseError('')
            setNewCaseSuccess('')
          }}
          onLoadCases={handleLoadCases}
          loading={loading}
          token={token}
          onClearSessionAndGoToLogin={() => {
            clearSession()
            navigate('/login')
          }}
          error={error}
          newCaseForm={newCaseForm}
          onNewCaseFieldChange={handleNewCaseFieldChange}
          newCaseLoading={newCaseLoading}
          onCreateNewCase={handleCreateNewCase}
          onCancelNewCase={() => {
            setShowNewCaseForm(false)
            setNewCaseError('')
            setNewCaseSuccess('')
          }}
          newCaseError={newCaseError}
          newCaseSuccess={newCaseSuccess}
          casesCount={cases.length}
          loaded={loaded}
        />
        <section
          className="insight-card"
          style={{
            marginBottom: '20px',
            paddingTop: '14px',
            paddingBottom: '14px',
          }}
        >
              <div
                className="insight-head"
                style={{
                  alignItems: 'center',
                  marginBottom: dashboardWorkspace === 'production' ? '0' : undefined,
                }}
              >
                <div>
                  <p className="insight-kicker">Navegação do painel</p>
                  <h2 className="insight-title" style={{ marginBottom: '4px' }}>Workspaces</h2>
                  <p className="insight-description" style={{ marginBottom: 0 }}>
                    Alterne entre operação principal e gestão comercial sem poluir o painel.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => setDashboardWorkspace('production')}
                    style={{
                      border: dashboardWorkspace === 'production'
                        ? '1px solid rgba(245, 158, 11, 0.44)'
                        : '1px solid rgba(148, 163, 184, 0.20)',
                      borderRadius: '999px',
                      padding: '10px 16px',
                      minWidth: '118px',
                      background: dashboardWorkspace === 'production'
                        ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.30), rgba(234, 179, 8, 0.18))'
                        : 'rgba(15, 23, 42, 0.42)',
                      color: dashboardWorkspace === 'production' ? '#fff4cc' : 'var(--text-primary)',
                      boxShadow: dashboardWorkspace === 'production'
                        ? '0 10px 24px rgba(245, 158, 11, 0.18)'
                        : 'none',
                      cursor: 'pointer',
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      letterSpacing: '0.01em',
                    }}
                  >
                    Produção
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setDashboardWorkspace('commercial')
                      setPlanPanelCollapsed(false)
                    }}
                    style={{
                      border: dashboardWorkspace === 'commercial'
                        ? '1px solid rgba(168, 85, 247, 0.44)'
                        : '1px solid rgba(148, 163, 184, 0.20)',
                      borderRadius: '999px',
                      padding: '10px 16px',
                      minWidth: '154px',
                      background: dashboardWorkspace === 'commercial'
                        ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.30), rgba(126, 34, 206, 0.18))'
                        : 'rgba(15, 23, 42, 0.42)',
                      color: dashboardWorkspace === 'commercial' ? '#f5e8ff' : 'var(--text-primary)',
                      boxShadow: dashboardWorkspace === 'commercial'
                        ? '0 10px 24px rgba(168, 85, 247, 0.18)'
                        : 'none',
                      cursor: 'pointer',
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      letterSpacing: '0.01em',
                    }}
                  >
                    Gestão comercial
                  </button>

                  {dashboardWorkspace === 'commercial' ? (
                    <button
                      type="button"
                      onClick={() => setPlanPanelCollapsed((prev) => !prev)}
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '999px',
                        padding: '8px 12px',
                        background: 'rgba(15, 23, 42, 0.20)',
                        color: 'var(--muted-text)',
                        cursor: 'pointer',
                        fontSize: '0.79rem',
                        fontWeight: 600,
                      }}
                    >
                      {planPanelCollapsed ? 'Abrir visão executiva' : 'Recolher visão executiva'}
                    </button>
                  ) : null}
                </div>
              </div>

              {dashboardWorkspace === 'production' ? (
                  <>
                    <div
                      className="insight-head"
                      style={{
                        alignItems: 'flex-start',
                        marginBottom: '14px',
                      }}
                    >
                      <div>
                        <p className="insight-kicker">Plataforma IA Jurídica Pro</p>
                        <h2 className="insight-title" style={{ marginBottom: '4px' }}>
                          Módulos jurídicos oficiais
                        </h2>
                        <p className="insight-description" style={{ marginBottom: 0 }}>
                          Cada área fica no seu quadrado, com status operacional e notas de segurança para uso supervisionado.
                        </p>
                      </div>
                    </div>

                    {legalModulesLoading ? (
                      <p className="insight-empty">Carregando módulos jurídicos oficiais...</p>
                    ) : legalModulesError ? (
                      <p className="insight-empty">{legalModulesError}</p>
                    ) : legalModules.length === 0 ? (
                      <p className="insight-empty">Nenhum módulo jurídico carregado ainda.</p>
                    ) : (
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: '14px',
                        }}
                      >
                        {legalModules.map((legalModule) => (
                          <article
                            key={legalModule.id}
                            style={{
                              border: '1px solid rgba(245, 158, 11, 0.18)',
                              borderRadius: '18px',
                              padding: '16px',
                              background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.72), rgba(30, 41, 59, 0.42))',
                              boxShadow: '0 16px 34px rgba(15, 23, 42, 0.22)',
                              minHeight: '190px',
                            }}
                          >
                            <p className="insight-kicker" style={{ marginBottom: '8px' }}>
                              {getLegalModuleStatusLabel(legalModule.status)}
                            </p>
                            <h3
                              style={{
                                margin: '0 0 8px',
                                color: 'var(--text-primary)',
                                fontSize: '1.08rem',
                              }}
                            >
                              {legalModule.label}
                            </h3>
                            <p
                              className="insight-description"
                              style={{
                                marginBottom: '12px',
                                fontSize: '0.86rem',
                              }}
                            >
                              Área canônica: {legalModule.canonical_legal_area}
                            </p>
                            <p
                              style={{
                                margin: '0 0 12px',
                                color: 'var(--muted-text)',
                                fontSize: '0.82rem',
                                lineHeight: 1.45,
                              }}
                            >
                              {legalModule.action_keywords.slice(0, 3).join(' • ')}
                            </p>
                            <p
                              style={{
                                margin: 0,
                                color: '#fde68a',
                                fontSize: '0.78rem',
                                lineHeight: 1.45,
                              }}
                            >
                              {legalModule.safety_notes[0]}
                            </p>
                          </article>
                        ))}
                      </div>
                    )}
                  </>
                ) : planPanelCollapsed ? (
                  <p className="insight-empty">
                    Visão comercial recolhida. Abra quando quiser consultar assinatura, capacidade e cobrança.
                  </p>
                ) : !loaded ? (
                <p className="insight-empty">
                  Conecte o painel para carregar a régua de capacidade do plano.
                </p>
              ) : usageLoading ? (
                <p className="insight-empty">Atualizando capacidade operacional do plano...</p>
              ) : usageError ? (
                <p className="insight-empty">{usageError}</p>
              ) : usageSummary ? (
                <>
                <div
                  style={{
                    display: 'flex',
                    gap: '10px',
                    flexWrap: 'wrap',
                    marginBottom: '14px',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setPlanWorkspaceView('capacity')}
                    style={{
                      border: planWorkspaceView === 'capacity'
                        ? '1px solid rgba(245, 158, 11, 0.30)'
                        : '1px solid rgba(148, 163, 184, 0.18)',
                      background: planWorkspaceView === 'capacity'
                        ? 'rgba(245, 158, 11, 0.16)'
                        : 'rgba(15, 23, 42, 0.28)',
                      color: planWorkspaceView === 'capacity' ? '#fef3c7' : '#dbeafe',
                      borderRadius: '12px',
                      padding: '11px 14px',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    Capacidade comercial
                  </button>

                  <button
                    type="button"
                    onClick={() => setPlanWorkspaceView('commercial')}
                    style={{
                      border: planWorkspaceView === 'commercial'
                        ? '1px solid rgba(168, 85, 247, 0.30)'
                        : '1px solid rgba(148, 163, 184, 0.18)',
                      background: planWorkspaceView === 'commercial'
                        ? 'rgba(168, 85, 247, 0.16)'
                        : 'rgba(15, 23, 42, 0.28)',
                      color: planWorkspaceView === 'commercial' ? '#f3e8ff' : '#dbeafe',
                      borderRadius: '12px',
                      padding: '11px 14px',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    Assinatura e cobrança
                  </button>
                </div>

                <div style={{ display: planWorkspaceView === 'capacity' ? 'grid' : 'none', gap: '16px' }}>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                      gap: '12px',
                    }}
                  >
                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.28)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'flex-start' }}>
                        <div>
                          <p className="insight-kicker">Plano atual</p>
                          <h3 style={{ margin: '6px 0 4px', fontSize: '1.08rem' }}>{getPlanLabel(usagePlanType)}</h3>
                        </div>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '6px 10px',
                            borderRadius: '999px',
                            fontSize: '0.76rem',
                            fontWeight: 700,
                            background: 'rgba(59, 130, 246, 0.16)',
                            color: '#bfdbfe',
                            border: '1px solid rgba(96, 165, 250, 0.26)',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {currentPlanPricing?.badge ?? 'Plano operacional'}
                        </span>
                      </div>

                      <p style={{ margin: '2px 0 0', color: 'var(--muted-text)' }}>
                        {getPlanStatusLabel(usagePlanStatus)}
                      </p>

                      <p
                        style={{
                          margin: '14px 0 6px',
                          fontSize: '1.32rem',
                          fontWeight: 800,
                          letterSpacing: '-0.02em',
                        }}
                      >
                        {currentPlanPricing?.formattedMonthlyPrice ?? 'Preço sob consulta'}
                      </p>

                      <p style={{ margin: 0, color: 'var(--muted-text)', lineHeight: 1.5 }}>
                        {currentPlanPricing?.description ?? 'Plano carregado conforme capacidade operacional do tenant.'}
                      </p>

                      <p style={{ margin: '12px 0 0', color: 'var(--muted-text)', lineHeight: 1.45, fontSize: '0.93rem' }}>
                        {currentPlanPricing?.onboardingNote ?? 'Condição comercial sujeita à proposta e maturidade operacional.'}
                      </p>

                      <button
                        type="button"
                        onClick={() => handlePlanAction(usagePlanType, getPlanLabel(usagePlanType))}
                        style={{
                          marginTop: '14px',
                          width: '100%',
                          border: '1px solid rgba(96, 165, 250, 0.26)',
                          background: 'rgba(59, 130, 246, 0.14)',
                          color: '#dbeafe',
                          borderRadius: '12px',
                          padding: '12px 14px',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        Plano atual em uso
                      </button>
                    </article>

                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.28)',
                      }}
                    >
                      <p className="insight-kicker">Casos ativos</p>
                      <h3 style={{ margin: '6px 0 4px', fontSize: '1.08rem' }}>
                        {usageActiveCurrent} / {usageActiveLimit}
                      </h3>
                      <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                        {usageActiveRemaining} vaga(s) disponível(is)
                      </p>
                    </article>

                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.28)',
                      }}
                    >
                      <p className="insight-kicker">Arquivados</p>
                      <h3 style={{ margin: '6px 0 4px', fontSize: '1.08rem' }}>{usageArchivedCurrent}</h3>
                      <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                        Organizam a operação, mas seguem contando no acervo
                      </p>
                    </article>

                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.28)',
                      }}
                    >
                      <p className="insight-kicker">Acervo total</p>
                      <h3 style={{ margin: '6px 0 4px', fontSize: '1.08rem' }}>
                        {usageRecordsCurrent} / {usageRecordsLimit}
                      </h3>
                      <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                        {usageRecordsRemaining} espaço(s) restante(s) no histórico
                      </p>
                    </article>
                  </div>

                  <div
                    style={{
                      display: planWorkspaceView === 'capacity' ? 'grid' : 'none',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                      gap: '12px',
                    }}
                  >
                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.22)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '8px' }}>
                        <strong>Ocupação de ativos</strong>
                        <span>{formatCapacityPercent(usageActivePercent)}</span>
                      </div>
                      <div
                        style={{
                          height: '8px',
                          borderRadius: '999px',
                          background: 'rgba(148, 163, 184, 0.18)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${usageActivePercent}%`,
                            height: '100%',
                            borderRadius: '999px',
                            background:
                              usageActivePercent >= 100
                                ? 'linear-gradient(90deg, #dc2626, #f97316)'
                                : usageActivePercent >= 80
                                  ? 'linear-gradient(90deg, #f59e0b, #f97316)'
                                  : 'linear-gradient(90deg, #22c55e, #84cc16)',
                          }}
                        />
                      </div>
                      <p style={{ margin: '10px 0 0', color: 'var(--muted-text)' }}>
                        Ativos pressionam a operação diária e são o primeiro gatilho de upgrade.
                      </p>
                    </article>

                    <article
                      style={{
                        border: '1px solid rgba(148, 163, 184, 0.18)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(15, 23, 42, 0.22)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '8px' }}>
                        <strong>Ocupação do acervo</strong>
                        <span>{formatCapacityPercent(usageRecordsPercent)}</span>
                      </div>
                      <div
                        style={{
                          height: '8px',
                          borderRadius: '999px',
                          background: 'rgba(148, 163, 184, 0.18)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${usageRecordsPercent}%`,
                            height: '100%',
                            borderRadius: '999px',
                            background:
                              usageRecordsPercent >= 100
                                ? 'linear-gradient(90deg, #dc2626, #f97316)'
                                : usageRecordsPercent >= 80
                                  ? 'linear-gradient(90deg, #f59e0b, #f97316)'
                                  : 'linear-gradient(90deg, #22c55e, #84cc16)',
                          }}
                        />
                      </div>
                      <p style={{ margin: '10px 0 0', color: 'var(--muted-text)' }}>
                        Arquivados preservam histórico, mas continuam consumindo capacidade do plano.
                      </p>
                    </article>
                  </div>


                </div>
                </>
              ) : (
                <p className="insight-empty">
                  Não foi possível carregar a régua comercial do plano neste momento.
                </p>
              )}
<div
                    style={{
                      display: dashboardWorkspace === 'commercial' && !planPanelCollapsed && planWorkspaceView === 'commercial' ? 'grid' : 'none',
                      gridTemplateColumns: '1fr',
                      gap: '14px',
                    }}
                  >
                    <section
                      style={{
                        border: '1px solid rgba(168, 85, 247, 0.24)',
                        borderRadius: '22px',
                        padding: '18px',
                        background: 'linear-gradient(180deg, rgba(88, 28, 135, 0.16), rgba(15, 23, 42, 0.30))',
                        boxShadow: '0 18px 40px rgba(15, 23, 42, 0.22)',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          gap: '12px',
                          alignItems: 'flex-start',
                          marginBottom: '14px',
                          flexWrap: 'wrap',
                        }}
                      >
                        <div>
                          <p className="insight-kicker">Comercial e assinatura</p>
                          <h3 style={{ margin: '6px 0 4px', fontSize: '1.08rem' }}>Planos, upgrade e cobrança</h3>
                          <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                            Área isolada da produção para assinatura, mudança de plano e checkout.
                          </p>
                        </div>

                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '7px 11px',
                            borderRadius: '999px',
                            fontSize: '0.74rem',
                            fontWeight: 800,
                            background: 'rgba(168, 85, 247, 0.18)',
                            color: '#f3e8ff',
                            border: '1px solid rgba(216, 180, 254, 0.22)',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          Plano atual: {getPlanLabel(usagePlanType)}
                        </span>
                      </div>

                      <section
                        style={{
                          border: '1px solid rgba(168, 85, 247, 0.14)',
                          borderRadius: '18px',
                          padding: '16px',
                          background: 'rgba(15, 23, 42, 0.18)',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            gap: '10px',
                            alignItems: 'flex-start',
                            marginBottom: '12px',
                          }}
                        >
                          <div>
                            <p className="insight-kicker">Próximos planos</p>
                            <h3 style={{ margin: '6px 0 4px', fontSize: '1.02rem' }}>Comparativo rápido de planos</h3>
                            <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                              Visualize a evolução comercial sem mexer no bloco operacional já validado.
                            </p>
                          </div>
                        </div>

                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                            gap: '12px',
                          }}
                        >
                          {planActionOptions.map((plan) => (
                            <article
                              key={plan.type}
                              style={{
                                border: '1px solid rgba(168, 85, 247, 0.18)',
                                borderRadius: '16px',
                                padding: '14px',
                                background: 'rgba(15, 23, 42, 0.28)',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', alignItems: 'flex-start' }}>
                                <div>
                                  <p className="insight-kicker">{plan.label}</p>
                                  <h4 style={{ margin: '6px 0 4px', fontSize: '1rem' }}>{plan.formattedMonthlyPrice}</h4>
                                </div>
                                <span
                                  style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '5px 9px',
                                    borderRadius: '999px',
                                    fontSize: '0.72rem',
                                    fontWeight: 700,
                                    background: 'rgba(168, 85, 247, 0.16)',
                                    color: '#f3e8ff',
                                    border: '1px solid rgba(216, 180, 254, 0.20)',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {plan.badge}
                                </span>
                              </div>

                              <p style={{ margin: '10px 0 0', color: 'var(--muted-text)', lineHeight: 1.5 }}>
                                {plan.description}
                              </p>

                              <p style={{ margin: '12px 0 0', color: 'var(--muted-text)', lineHeight: 1.45, fontSize: '0.92rem' }}>
                                {plan.recommendedFor}
                              </p>

                              <button
                                type="button"
                                onClick={() => handlePlanAction(plan.type, plan.label)}
                                style={{
                                  marginTop: '14px',
                                  width: '100%',
                                  border: '1px solid rgba(192, 132, 252, 0.24)',
                                  background: 'rgba(168, 85, 247, 0.14)',
                                  color: '#f5e8ff',
                                  borderRadius: '12px',
                                  padding: '11px 13px',
                                  fontWeight: 700,
                                  cursor: 'pointer',
                                }}
                              >
                                {plan.ctaLabel}
                              </button>
                            </article>
                          ))}
                        </div>
                      </section>

                      <div
                        style={{
                          marginTop: '14px',
                          border: '1px solid rgba(168, 85, 247, 0.18)',
                          borderRadius: '18px',
                          padding: '16px',
                          background: 'rgba(168, 85, 247, 0.10)',
                        }}
                      >
                        <p className="insight-kicker">Fluxo comercial</p>
                        <strong style={{ display: 'block', marginBottom: '6px' }}>
                          {planActionNotice ?? 'Ao clicar em um plano, o checkout é aberto em nova aba e a ativação depende da confirmação do pagamento.'}
                        </strong>
                        <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                          Contratação e cobrança ficam separadas da operação jurídica.
                        </p>
                      </div>
                    </section>
                  </div>
            </section>


          <ExpansionWorkspace
            token={token}
            selectedCaseId={selectedCaseId}
            selectedCaseArea={selectedCase?.legal_area ?? null}
            forcedModule={expansionModuleTarget}
            pieceReadyRequestId={pieceReadyRequestId}
          />

        <section className="cases-layout">
          <div className="cases-layout__list">
            <section className="insight-card">
              <div className="insight-head">
                <div>
                  <p className="insight-kicker">Carteira jurídica</p>
                  <h2 className="insight-title">Casos do escritório</h2>
                  <p className="insight-description">
                    Lista operacional dos casos carregados via API da Plataforma Jurídica Multiárea.
                  </p>
                </div>
                <span className="insight-badge">Base jurídica ativa</span>
              </div>

              {!loaded ? (
                <p className="insight-empty">
                  Informe o token e clique em “Conectar API” ou “Atualizar carteira”.
                </p>
              ) : null}

              {loaded && !loading && cases.length === 0 && !error ? (
                <p className="insight-empty">Nenhum caso encontrado para este token.</p>
              ) : null}

              {loaded && cases.length > 0 ? (
                <CaseFiltersBar
                  filteredCount={filteredCases.length}
                  totalCount={cases.length}
                  caseSearchTerm={caseSearchTerm}
                  onCaseSearchTermChange={setCaseSearchTerm}
                  caseStatusFilter={caseStatusFilter}
                  onCaseStatusFilterChange={setCaseStatusFilter}
                  onResetFilters={() => {
                    setCaseSearchTerm('')
                    setCaseStatusFilter('main')
                  }}
                  onCleanupDemo={() => {
                    void handleCleanupDemo()
                  }}
                  cleanupDemoLoading={cleanupDemoLoading}
                  caseActionError={caseActionError}
                  caseActionSuccess={caseActionSuccess}
                />
              ) : null}

              {loaded && !loading && cases.length > 0 && filteredCases.length === 0 ? (
                <p className="insight-empty">Nenhum caso encontrado para os filtros atuais.</p>
              ) : null}

              <div
                style={{
                  display: 'grid',
                  gap: '12px',
                }}
              >
                {filteredCases.map((caso) => {
                  const isArchiving = caseActionLoadingId === caso.id
                  const isAnalyzing = analysisLoading && selectedCaseId === caso.id
                  const isLoadingSummary = executiveSummaryLoading && selectedCaseId === caso.id
                  const isLoadingReport = executiveReportLoading && selectedCaseId === caso.id
                  const isLoadingPdf = executivePdfLoading && selectedCaseId === caso.id
                  const isLoadingContactLogs = contactLogsLoadingId === caso.id

                    const isLoadingReadiness = readinessLoadingId === caso.id
                    const isLoadingDossier = dossierLoadingId === caso.id
                    const isLoadingWitnessGrid = witnessGridLoadingId === caso.id
                  return (
                    <CaseCard
                      key={caso.id}
                      caso={caso}
                      selectedCaseId={selectedCaseId}
                      getStatusLabel={getStatusLabel}
                      isArchiving={isArchiving}
                      isAnalyzing={isAnalyzing}
                      isLoadingSummary={isLoadingSummary}
                      isLoadingReport={isLoadingReport}
                      isLoadingPdf={isLoadingPdf}
                      isLoadingContactLogs={isLoadingContactLogs}
                      isLoadingReadiness={isLoadingReadiness}
                        isLoadingDossier={isLoadingDossier}
                      isLoadingWitnessGrid={isLoadingWitnessGrid}
                        contactLogs={contactLogsByCaseId[caso.id] ?? []}
                        partyState={partyStatesByCaseId[caso.id] ?? null}
                          readiness={readinessByCaseId[caso.id] ?? null}
                          dossier={caseDossiersByCaseId[caso.id] ?? null}
                      analysisLoading={analysisLoading}
                      executiveSummaryLoading={executiveSummaryLoading}
                      executiveReportLoading={executiveReportLoading}
                      executivePdfLoading={executivePdfLoading}
                      onArchive={(caseId) => {
                        void handleArchiveCase(caseId)
                      }}
                      onAnalyze={handleAnalyzeCase}
                      onLoadExecutiveSummary={handleLoadExecutiveSummary}
                      onLoadExecutiveReport={handleLoadExecutiveReport}
                      onOpenExecutivePdf={handleOpenExecutivePdf}
                      onLoadCaseContactLogs={(caseId) => {
                        void handleLoadCaseContactLogs(caseId)
                      }}
                      onLoadWitnessGrid={(caseId) => {
                          void handleLoadWitnessGrid(caseId)
                        }}
                        onAddWitness={(targetCase) => {
                          void handleAddWitnessToCase(targetCase)
                        }}
                          onLoadReadiness={(targetCase) => {
                            void handleLoadCaseReadiness(targetCase)
                          }}
                          onLoadDossier={(targetCase) => {
                            void handleLoadCaseDossier(targetCase)
                          }}
                        onOpenWhatsAppTemplate={(caseId, whatsapp, templateKey) => {
                        void handleOpenWhatsAppTemplate(caseId, whatsapp, templateKey)
                      }}
                      onRegisterWhatsAppContact={(caseId) => {
                        void handleRegisterWhatsAppContact(caseId)
                      }}
                      onSelectCase={(caseId) => {
                        setSelectedCaseId(caseId)
                      }}
                    />
                  )
                })}
              </div>
            </section>
          </div>

          <div className="cases-layout__focus">
            <section className="insight-card" style={{ marginBottom: '16px' }}>
              <div className="insight-head">
                <div>
                  <p className="insight-kicker">Peça pronta</p>
                  <h2 className="insight-title">Montagem guiada para protocolo</h2>
                  <p className="insight-description">
                    Selecione um caso e gere a peça mastigada no Editor Jurídico Vivo com base na análise já produzida.
                  </p>
                </div>
                <span className="insight-badge">
                  {selectedCase ? `Caso pronto: #${selectedCase.id}` : 'Selecione um caso'}
                </span>
              </div>

              <p className="info-text" style={{ marginBottom: '12px' }}>
                <strong>Caso em foco:</strong>{' '}
                {selectedCase ? `${selectedCase.title} — ${selectedCase.case_number}` : 'Nenhum caso selecionado.'}
              </p>

              {pieceReadyNotice ? (
                <p className="status-message status-message--success" style={{ marginBottom: '12px' }}>
                  {pieceReadyNotice}
                </p>
              ) : null}

              <button
                type="button"
                onClick={() => {
                  if (!selectedCaseId) return
                  setExpansionModuleTarget('editor')
                  setPieceReadyRequestId((prev) => prev + 1)
                  setPieceReadyNotice('Abrindo o Editor Jurídico Vivo e preparando a peça pronta do caso selecionado.')
                  window.setTimeout(() => {
                    document.querySelector('.expansion-shell-card')?.scrollIntoView({
                      behavior: 'smooth',
                      block: 'start',
                    })
                  }, 50)
                }}
                disabled={!selectedCaseId}
                style={{
                  border: '1px solid rgba(148, 163, 184, 0.24)',
                  borderRadius: '999px',
                  padding: '10px 16px',
                  background: selectedCaseId ? 'rgba(15, 23, 42, 0.42)' : 'rgba(100, 116, 139, 0.24)',
                  color: 'var(--text-primary)',
                  cursor: selectedCaseId ? 'pointer' : 'not-allowed',
                  fontSize: '0.92rem',
                  fontWeight: 700,
                }}
              >
                Gerar peça pronta
              </button>
            </section>

            <CaseFocusPanel
              selectedCaseId={selectedCaseId}
              activeTab={activeFocusTab}
              onTabChange={setActiveFocusTab}
              analysisData={analysisData}
              analysisLoading={analysisLoading}
              analysisError={analysisError}
              executiveSummaryData={executiveSummaryData}
              executiveSummaryLoading={executiveSummaryLoading}
              executiveSummaryError={executiveSummaryError}
              executiveReportData={executiveReportData}
              executiveReportLoading={executiveReportLoading}
              executiveReportError={executiveReportError}
              executivePdfError={executivePdfError}
              getRiskLabel={getRiskLabel}
            />
          </div>
        </section>
      </section>
    </main>
  )
}
export default App
