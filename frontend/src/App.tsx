import './App.css'
import { useEffect, useState, type KeyboardEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, cleanupDemoCases, createBillingCheckoutSession, createBillingRequest, createCase, getCases, getCaseAnalysis, getExecutiveSummary, getExecutiveReport, getExecutivePdf, getUsageSummaryV2, login, updateCaseStatus, type CaseItem, type CaseAnalysisResponse, type ExecutiveSummaryResponse, type ExecutiveReportResponse, type UsageSummaryV2Response } from './services/api'
import { ExpansionWorkspace } from './components/expansion/ExpansionWorkspace'
import { CaseFiltersBar } from './components/CaseFiltersBar'
import { CaseCard } from './components/CaseCard'
import { DashboardTopPanel } from './components/DashboardTopPanel'
import { LoginPanel } from './components/LoginPanel'
import { CaseFocusPanel } from './components/CaseFocusPanel'
import { getPlanLabel as getCatalogPlanLabel, getPlanPricing, getPlanStatusLabel as getCatalogPlanStatusLabel, listPlanPricing } from './config/pricing'

const AUTH_TOKEN_STORAGE_KEY = 'ia_trabalhista_auth_token'

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
  const [cleanupDemoLoading, setCleanupDemoLoading] = useState(false)
  const [usageSummary, setUsageSummary] = useState<UsageSummaryV2Response | null>(null)
  const [usageLoading, setUsageLoading] = useState(false)
  const [usageError, setUsageError] = useState('')
  const [planActionNotice, setPlanActionNotice] = useState('')
  const [planPanelCollapsed, setPlanPanelCollapsed] = useState(false)
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

  function getStatusLabel(status: string) {
    return statusLabelMap[status] ?? status
  }

  function getRiskLabel(risk: string | undefined) {
    if (!risk) return 'Não informado'
    return riskLabelMap[risk] ?? risk
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

    const tenantId = cases[0]?.tenant_id
    if (!tenantId) {
      setPlanActionNotice('Não foi possível identificar o tenant para iniciar a mudança de plano.')
      return
    }

    try {
      setPlanActionNotice(`Criando solicitação de mudança para o plano ${planLabel}...`)
      const selectedPlanPricing = getPlanPricing(planType)
      const currentMonthlyPrice = currentPlanPricing?.monthlyPrice ?? 0
      const selectedMonthlyPrice = selectedPlanPricing?.monthlyPrice ?? 0
      const billingReason = selectedMonthlyPrice < currentMonthlyPrice ? 'plan_downgrade' : 'plan_upgrade'
      const billing = await createBillingRequest(tenantId, planType, billingReason)
      const checkout = await createBillingCheckoutSession(billing.billing_request.id)

      setPlanActionNotice(
        `Checkout criado para o plano ${planLabel}. Link: ${checkout.checkout.checkout_url ?? 'checkout indisponível'}`
      )
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

    const haystack = `${caso.case_number} ${caso.title} ${caso.description ?? ''}`.toLowerCase()
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

  const usageCapacityMessage =
    !usageSummary
      ? 'Conecte o painel para carregar a capacidade operacional do plano.'
      : usageActiveRemaining === 0
        ? 'Limite de casos ativos atingido. Arquive um caso ou faça upgrade.'
        : usageRecordsRemaining === 0
          ? 'Limite de acervo atingido. Faça upgrade para armazenar mais casos.'
          : usageActiveRemaining <= 3
            ? `Atenção: restam apenas ${usageActiveRemaining} vaga(s) ativa(s) neste plano.`
            : 'Operação dentro da capacidade do plano.'

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
    setError('')
    setUsageError('')

    try {
      const [casesData, usageData] = await Promise.all([
        getCases(authToken),
        getUsageSummaryV2(authToken),
      ])

      setCases(sortCasesForDisplay(casesData))
      setUsageSummary(usageData)
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

  function handleNewCaseFieldChange(
    field: 'case_number' | 'title' | 'description' | 'legal_area' | 'action_type' | 'status',
    value: string,
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

        <section className="insight-card" style={{ marginBottom: '20px' }}>
              <div className="insight-head">
                <div>
                  <p className="insight-kicker">Capacidade comercial</p>
                  <h2 className="insight-title">Plano e ocupação da carteira</h2>
                  <p className="insight-description">
                    Leitura operacional do plano atual para decidir quando arquivar, quando ainda há folga
                    e quando o escritório precisa subir de nível.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span className="insight-badge">{getPlanLabel(usagePlanType)}</span>
                  <button
                    type="button"
                    onClick={() => setPlanPanelCollapsed((prev) => !prev)}
                    style={{
                      border: '1px solid rgba(148, 163, 184, 0.24)',
                      borderRadius: '999px',
                      padding: '8px 14px',
                      background: 'rgba(15, 23, 42, 0.42)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                    }}
                  >
                    {planPanelCollapsed ? 'Abrir visão executiva' : 'Recolher visão executiva'}
                  </button>
                </div>
              </div>

              {planPanelCollapsed ? (
                  <p className="insight-empty">
                    Visão executiva recolhida. Abra este bloco para consultar plano, ocupação e decisão operacional.
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
                <div style={{ display: 'grid', gap: '16px' }}>
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
                      display: 'grid',
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

                  <section
                    style={{
                      border: '1px solid rgba(148, 163, 184, 0.16)',
                      borderRadius: '18px',
                      padding: '16px',
                      background: 'rgba(15, 23, 42, 0.22)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div>
                        <p className="insight-kicker">Próximos planos</p>
                        <h3 style={{ margin: '6px 0 4px', fontSize: '1.02rem' }}>Comparativo rápido de planos</h3>
                        <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                          Visualize a evolução comercial sem mexer na base operacional já validada.
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
                            border: '1px solid rgba(148, 163, 184, 0.18)',
                            borderRadius: '16px',
                            padding: '14px',
                            background: 'rgba(15, 23, 42, 0.24)',
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
                                background: 'rgba(59, 130, 246, 0.14)',
                                color: '#bfdbfe',
                                border: '1px solid rgba(96, 165, 250, 0.22)',
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
                              border: '1px solid rgba(96, 165, 250, 0.22)',
                              background: 'rgba(59, 130, 246, 0.10)',
                              color: '#dbeafe',
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

                  {planActionNotice ? (
                    <div
                      style={{
                        border: '1px solid rgba(96, 165, 250, 0.22)',
                        borderRadius: '18px',
                        padding: '16px',
                        background: 'rgba(59, 130, 246, 0.08)',
                      }}
                    >
                      <p className="insight-kicker">Fluxo comercial</p>
                      <strong style={{ display: 'block', marginBottom: '6px' }}>{planActionNotice}</strong>
                      <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                        Nesta fase, o clique registra intenção no painel. A ligação com upgrade real será conectada ao fluxo comercial/admin sem mudança automática de plano.
                      </p>
                    </div>
                  ) : null}

                  <div
                    style={{
                      border: '1px solid rgba(245, 158, 11, 0.22)',
                      borderRadius: '18px',
                      padding: '16px',
                      background: 'rgba(245, 158, 11, 0.08)',
                    }}
                  >
                    <p className="insight-kicker">Decisão operacional</p>
                    <strong style={{ display: 'block', marginBottom: '6px' }}>{usageCapacityMessage}</strong>
                    <p style={{ margin: 0, color: 'var(--muted-text)' }}>
                      Regra comercial: ativos contam na operação, arquivados continuam no acervo e upgrade
                      amplia o teto sem apagar histórico.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="insight-empty">
                  Não foi possível carregar a régua comercial do plano neste momento.
                </p>
              )}
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
