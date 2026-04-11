import './App.css'
import { useState, type KeyboardEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, cleanupDemoCases, createCase, getCases, getCaseAnalysis, getExecutiveSummary, getExecutiveReport, getExecutivePdf, login, updateCaseStatus, type CaseItem, type CaseAnalysisResponse, type ExecutiveSummaryResponse, type ExecutiveReportResponse } from './services/api'
import { ExpansionWorkspace } from './components/expansion/ExpansionWorkspace'
import { CaseFiltersBar } from './components/CaseFiltersBar'
import { CaseCard } from './components/CaseCard'
import { DashboardTopPanel } from './components/DashboardTopPanel'
import { LoginPanel } from './components/LoginPanel'
import { CaseFocusPanel } from './components/CaseFocusPanel'

function App() {
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
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

  if (!isLoginRoute && !token.trim()) {
    return <Navigate to="/login" replace />
  }

  if (isLoginRoute && token.trim()) {
    return <Navigate to="/" replace />
  }

  function clearSession() {
    setToken('')
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

  async function handleLoadCases() {
    setLoading(true)
    setError('')

    try {
      const data = await getCases(token)
      setCases(sortCasesForDisplay(data))
      setLoaded(true)
    } catch (err) {
      const fallback = handleApiFailure(err, 'Não foi possível carregar os casos. Verifique o token e o backend.')
      if (fallback) {
        setError(fallback)
        setLoaded(true)
      }
    } finally {
      setLoading(false)
    }
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

      const data = await getCases(auth.access_token)
      setCases(sortCasesForDisplay(data))
      setLoaded(true)
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

      setCases((prev) => sortCasesForDisplay([createdCase, ...prev]))
      setLoaded(true)
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

      setCases((prev) =>
        sortCasesForDisplay(prev.map((caso) => (caso.id === caseId ? updatedCase : caso))),
      )
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
      const refreshedCases = await getCases(token)
      setCases(sortCasesForDisplay(refreshedCases))
      setLoaded(true)
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

        <ExpansionWorkspace token={token} selectedCaseId={selectedCaseId} />

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
