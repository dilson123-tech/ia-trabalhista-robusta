import './App.css'
import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, createCase, getCases, getCaseAnalysis, getExecutiveSummary, getExecutiveReport, getExecutivePdf, login, type CaseItem, type CaseAnalysisResponse, type ExecutiveSummaryResponse, type ExecutiveReportResponse } from './services/api'

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
  const navigate = useNavigate()
  const location = useLocation()
  const isLoginRoute = location.pathname === '/login'

  const [newCaseForm, setNewCaseForm] = useState({
    case_number: '',
    title: '',
    description: '',
    status: 'draft',
  })

  if (!isLoginRoute && !token.trim()) {
    return <Navigate to="/login" replace />
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
      setCases(data)
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
      setCases(data)
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
      const fallback = handleApiFailure(err, 'Não foi possível carregar o executive summary do caso.')
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
      const fallback = handleApiFailure(err, 'Não foi possível carregar o executive report do caso.')
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
      const fallback = handleApiFailure(err, 'Não foi possível abrir o executive PDF do caso.')
      if (fallback) {
        setExecutivePdfError(fallback)
      }
    } finally {
      setExecutivePdfLoading(false)
    }
  }

  function handleNewCaseFieldChange(field: 'case_number' | 'title' | 'description' | 'status', value: string) {
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
        status: newCaseForm.status,
      })

      setCases((prev) => [createdCase, ...prev])
      setLoaded(true)
      setShowNewCaseForm(false)
      setNewCaseForm({
        case_number: '',
        title: '',
        description: '',
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


  if (isLoginRoute) {
    return (
      <main className="app-shell">
        <section className="app-container">
          <section className="hero-panel">
            <div className="hero-card">
              <p className="hero-kicker">IA Trabalhista Robusta</p>
              <h1 className="hero-heading">Acesso ao sistema</h1>
              <p className="hero-description">
                Entre com usuário e senha para acessar o painel do advogado, a carteira de casos
                e os fluxos executivos da plataforma.
              </p>

              <div className="hero-actions">
                <button
                  className="btn btn-ghost"
                  type="button"
                  onClick={() => navigate('/')}
                >
                  Voltar ao painel
                </button>
              </div>
            </div>

            <aside className="technical-card" key={loginFormKey}>
              <div className="technical-topbar">
                <div>
                  <h2 className="technical-title">Login oficial</h2>
                  <p className="technical-description">
                    Entrada dedicada para autenticação do frontend, separada do hero principal
                    para deixar a experiência mais limpa e com cara de produto SaaS.
                  </p>
                </div>

                <span className={`connection-badge ${token.trim() ? 'connection-badge--ok' : 'connection-badge--pending'}`}>
                  {token.trim() ? 'Sessão pronta' : 'Sessão inativa'}
                </span>
              </div>

              <div className="form-grid token-field">
                <input
                  className="login-decoy"
                  type="text"
                  tabIndex={-1}
                  autoComplete="username"
                  aria-hidden="true"
                />

                <input
                  className="login-decoy"
                  type="password"
                  tabIndex={-1}
                  autoComplete="current-password"
                  aria-hidden="true"
                />

                <input
                  className="form-control"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setLoginFieldsUnlocked(true)}
                  readOnly={!loginFieldsUnlocked}
                  placeholder="Usuário"
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  name={`login-user-${loginFormKey}`}
                />

                <div className="password-field">
                  <input
                    className="form-control"
                    type={showToken ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setLoginFieldsUnlocked(true)}
                    readOnly={!loginFieldsUnlocked}
                    placeholder="Senha"
                    autoComplete="new-password"
                    name={`login-password-${loginFormKey}`}
                  />
                  <button
                    className="password-toggle-icon"
                    type="button"
                    onClick={() => setShowToken((prev) => !prev)}
                    disabled={!password.trim()}
                    aria-label={showToken ? 'Ocultar senha' : 'Mostrar senha'}
                    title={showToken ? 'Ocultar senha' : 'Mostrar senha'}
                  >
                    {showToken ? (
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M3 3l18 18" />
                        <path d="M10.58 10.58a2 2 0 1 0 2.84 2.84" />
                        <path d="M9.88 5.09A10.94 10.94 0 0 1 12 4c5 0 9.27 3.11 11 8-.9 2.54-2.66 4.61-4.94 5.94" />
                        <path d="M6.1 6.1C3.8 7.45 2.04 9.5 1 12c1.73 4.89 6 8 11 8 1.73 0 3.37-.37 4.84-1.03" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="actions-row">
                <button
                  className={`btn ${authLoading || !username.trim() || !password.trim() ? 'btn-muted' : 'btn-primary'}`}
                  type="button"
                  onClick={handleLogin}
                  disabled={authLoading || !username.trim() || !password.trim()}
                >
                  {authLoading ? 'Entrando...' : 'Entrar no sistema'}
                </button>

                <button
                  className="btn btn-ghost"
                  type="button"
                  onClick={() => {
                    setShowToken(false)
                    setUsername('')
                    setPassword('')
                    setError('')
                  }}
                >
                  Limpar
                </button>

                {token.trim() ? (
                  <button
                    className="btn btn-secondary"
                    type="button"
                    onClick={() => navigate('/')}
                  >
                    Ir para o painel
                  </button>
                ) : null}
              </div>

              {error ? (
                <p className="status-message status-message--error">{error}</p>
              ) : null}
            </aside>
          </section>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <section className="app-container">
        <section className="hero-panel">
          <div className="hero-card">
            <p className="hero-kicker">Plataforma estratégica trabalhista</p>
            <h1 className="hero-heading">Painel do Advogado</h1>
            <p className="hero-description">
              Centralize análise jurídica, leitura de risco, resumos executivos e relatórios estratégicos
              em um ambiente com visão clara para decisão, operação e apresentação ao cliente.
            </p>

            <div className="hero-actions">
              <button
                className={`btn ${showNewCaseForm ? 'btn-secondary' : 'btn-primary'}`}
                type="button"
                onClick={() => {
                  setShowNewCaseForm((prev) => !prev)
                  setNewCaseError('')
                  setNewCaseSuccess('')
                }}
              >
                {showNewCaseForm ? 'Fechar Novo Caso' : '+ Novo Caso'}
              </button>

              <button
                className="btn btn-ghost"
                type="button"
                onClick={handleLoadCases}
                disabled={loading || !token.trim()}
              >
                {loading ? 'Carregando casos...' : 'Atualizar carteira'}
              </button>
            </div>
          </div>

            <aside className="technical-card technical-card--connected">
              <div className="technical-topbar">
                <div>
                  <h2 className="technical-title">Sessão ativa</h2>
                  <p className="technical-description">
                    Backend autenticado e carteira pronta para operação no painel.
                  </p>
                </div>

                <span className="connection-badge connection-badge--ok">
                  API conectada
                </span>
              </div>

              <div className="actions-row">
                <button
                  className="btn btn-ghost"
                  type="button"
                  onClick={() => {
                    clearSession()
                    navigate('/login')
                  }}
                >
                  Trocar acesso
                </button>
              </div>

              {error ? (
                <p className="status-message status-message--error">{error}</p>
              ) : null}
            </aside>
        </section>

        {showNewCaseForm ? (
          <section className="section-card">
            <div className="section-head">
              <h2 className="section-heading">Novo Caso</h2>
              <p className="section-description">
                Cadastre um novo processo com dados reais para alimentar a esteira analítica e executiva.
              </p>
            </div>

            <div className="form-grid">
              <input
                className="form-control"
                value={newCaseForm.case_number}
                onChange={(e) => handleNewCaseFieldChange('case_number', e.target.value)}
                placeholder="Número do processo"
              />

              <input
                className="form-control"
                value={newCaseForm.title}
                onChange={(e) => handleNewCaseFieldChange('title', e.target.value)}
                placeholder="Título do caso"
              />

              <textarea
                className="form-control form-control--textarea"
                value={newCaseForm.description}
                onChange={(e) => handleNewCaseFieldChange('description', e.target.value)}
                placeholder="Descrição do caso"
              />

              <select
                className="form-control"
                value={newCaseForm.status}
                onChange={(e) => handleNewCaseFieldChange('status', e.target.value)}
              >
                <option value="draft">draft</option>
                <option value="active">active</option>
                <option value="review">review</option>
              </select>

              <div className="actions-row">
                <button
                  className={`btn ${
                    newCaseLoading ||
                    !token.trim() ||
                    !newCaseForm.case_number.trim() ||
                    !newCaseForm.title.trim()
                      ? 'btn-muted'
                      : 'btn-primary'
                  }`}
                  type="button"
                  onClick={handleCreateNewCase}
                  disabled={
                    newCaseLoading ||
                    !token.trim() ||
                    !newCaseForm.case_number.trim() ||
                    !newCaseForm.title.trim()
                  }
                >
                  {newCaseLoading ? 'Criando caso...' : 'Criar caso real'}
                </button>

                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={() => {
                    setShowNewCaseForm(false)
                    setNewCaseError('')
                    setNewCaseSuccess('')
                  }}
                >
                  Cancelar
                </button>
              </div>

              {!token.trim() ? (
                <p className="status-message status-message--warning">
                  Informe um token válido antes de criar um caso.
                </p>
              ) : null}

              {newCaseError ? (
                <p className="status-message status-message--error">{newCaseError}</p>
              ) : null}

              {newCaseSuccess ? (
                <p className="status-message status-message--success">{newCaseSuccess}</p>
              ) : null}
            </div>
          </section>
        ) : null}

        <section className="metrics-grid metrics-grid--hero">
          {[
            ['Casos carregados', String(cases.length), 'metric-card metric-card--highlight', 'metric-value metric-value--gold'],
            ['Backend', 'Online', 'metric-card', 'metric-value'],
            ['Modo', loaded ? 'Real' : 'Demo', 'metric-card', 'metric-value'],
            ['Sessão', token.trim() ? 'Ativa' : 'Pendente', 'metric-card', 'metric-value'],
          ].map(([label, value, cardClass, valueClass]) => (
            <article key={label} className={cardClass}>
              <p className="metric-label">{label}</p>
              <h2 className={valueClass}>{value}</h2>
            </article>
          ))}
        </section>

        <section className="insight-card">
          <div className="insight-head">
            <div>
              <p className="insight-kicker">Diagnóstico técnico</p>
              <h2 className="insight-title">Resultado da análise jurídica</h2>
              <p className="insight-description">
                Retorno analítico da IA para apoiar decisão, estratégia e priorização do caso selecionado.
              </p>
            </div>
            <span className="insight-badge">Leitura técnica em tempo real</span>
          </div>

          {analysisError ? (
            <p className="status-message status-message--error">{analysisError}</p>
          ) : null}

          {!analysisData && !analysisLoading ? (
            <p className="insight-empty">
              Clique em “Analisar caso” em um dos cards para carregar o diagnóstico estratégico.
            </p>
          ) : null}

          {analysisLoading ? (
            <p className="insight-empty">Analisando caso selecionado...</p>
          ) : null}

          {analysisData ? (
            <div className="content-stack">
              <article className="info-card">
                <p className="info-meta">
                  Caso analisado: {analysisData.case_id} | Análise: {analysisData.analysis_id}
                </p>

                <p className="info-text">
                  <strong>Resumo técnico:</strong>{' '}
                  {analysisData.analysis?.technical?.summary || 'Resumo não disponível.'}
                </p>

                <p className="info-text">
                  <strong>Nível de risco:</strong>{' '}
                  {analysisData.analysis?.technical?.risk_level || 'Não informado'}
                </p>

                <div style={{ marginBottom: '12px' }}>
                  <strong className="info-list-title">Pontos de atenção</strong>
                  <ul className="info-list">
                    {(analysisData.analysis?.technical?.issues || []).length > 0 ? (
                      (analysisData.analysis?.technical?.issues || []).map((item, index) => (
                        <li key={index}>{item}</li>
                      ))
                    ) : (
                      <li>Nenhum ponto crítico informado.</li>
                    )}
                  </ul>
                </div>

                <div>
                  <strong className="info-list-title">Próximos passos</strong>
                  <ul className="info-list">
                    {(analysisData.analysis?.technical?.next_steps || []).length > 0 ? (
                      (analysisData.analysis?.technical?.next_steps || []).map((item, index) => (
                        <li key={index}>{item}</li>
                      ))
                    ) : (
                      <li>Nenhum próximo passo informado.</li>
                    )}
                  </ul>
                </div>
              </article>
            </div>
          ) : null}
        </section>

        <section className="insight-card">
          <div className="insight-head">
            <div>
              <p className="insight-kicker">Resumo executivo</p>
              <h2 className="insight-title">Executive Summary</h2>
              <p className="insight-description">
                Versão consolidada do caso para leitura rápida, comunicação interna e alinhamento com gestão.
              </p>
            </div>
            <span className="insight-badge">Visão executiva</span>
          </div>

          {executiveSummaryError ? (
            <p className="status-message status-message--error">{executiveSummaryError}</p>
          ) : null}

          {!executiveSummaryData && !executiveSummaryLoading ? (
            <p className="insight-empty">
              Clique em “Executive Summary” em um dos casos para carregar o resumo executivo.
            </p>
          ) : null}

          {executiveSummaryLoading ? (
            <p className="insight-empty">Carregando executive summary...</p>
          ) : null}

          {executiveSummaryData ? (
            <article className="info-card">
              <p className="info-meta">
                Caso: {executiveSummaryData.case.title} | Nº {executiveSummaryData.case.case_number}
              </p>

              <p className="info-text">
                <strong>Status final:</strong>{' '}
                {executiveSummaryData.executive_decision?.final_status || executiveSummaryData.viability?.label || 'Não informado'}
              </p>

              <p className="info-text">
                <strong>Probabilidade estimada:</strong>{' '}
                {typeof executiveSummaryData.executive_decision?.probability_percent === 'number'
                  ? `${executiveSummaryData.executive_decision.probability_percent}%`
                  : typeof executiveSummaryData.viability?.probability === 'number'
                    ? `${Math.round(executiveSummaryData.viability.probability * 100)}%`
                    : 'Não informado'}
              </p>

              <p className="info-text">
                <strong>Resumo executivo:</strong>{' '}
                {executiveSummaryData.executive_decision?.executive_summary || executiveSummaryData.technical_analysis?.summary || 'Resumo não disponível.'}
              </p>

              <p className="info-text">
                <strong>Recomendação:</strong>{' '}
                {executiveSummaryData.viability?.recommendation || executiveSummaryData.strategic_analysis?.recommended_strategy || 'Não informada'}
              </p>

              <div style={{ marginBottom: '12px' }}>
                <strong className="info-list-title">Indicadores estratégicos</strong>
                <ul className="info-list">
                  <li>Risco técnico: {executiveSummaryData.technical_analysis?.risk_level || 'Não informado'}</li>
                  <li>Risco financeiro: {executiveSummaryData.strategic_analysis?.financial_risk || 'Não informado'}</li>
                  <li>Complexidade: {executiveSummaryData.viability?.complexity || executiveSummaryData.strategic_analysis?.complexity || 'Não informada'}</li>
                  <li>Tempo estimado: {executiveSummaryData.executive_decision?.estimated_time || executiveSummaryData.viability?.estimated_time || 'Não informado'}</li>
                  <li>
                    Score:{' '}
                    {typeof executiveSummaryData.viability?.score === 'number'
                      ? `${executiveSummaryData.viability.score}/100`
                      : typeof executiveSummaryData.executive_decision?.score === 'number'
                        ? `${executiveSummaryData.executive_decision.score}/100`
                        : 'Não informado'}
                  </li>
                </ul>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <strong className="info-list-title">Pontos críticos</strong>
                <ul className="info-list">
                  {(executiveSummaryData.strategic_analysis?.critical_points || executiveSummaryData.technical_analysis?.issues || []).length > 0 ? (
                    (executiveSummaryData.strategic_analysis?.critical_points || executiveSummaryData.technical_analysis?.issues || []).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))
                  ) : (
                    <li>Nenhum ponto crítico informado.</li>
                  )}
                </ul>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <strong className="info-list-title">Pontos fortes</strong>
                <ul className="info-list">
                  {(executiveSummaryData.strategic_analysis?.strong_points || []).length > 0 ? (
                    (executiveSummaryData.strategic_analysis?.strong_points || []).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))
                  ) : (
                    <li>Nenhum ponto forte destacado.</li>
                  )}
                </ul>
              </div>

              <div>
                <strong className="info-list-title">Próximos passos</strong>
                <ul className="info-list">
                  {(executiveSummaryData.technical_analysis?.next_steps || []).length > 0 ? (
                    (executiveSummaryData.technical_analysis?.next_steps || []).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))
                  ) : (
                    <li>Nenhum próximo passo informado.</li>
                  )}
                </ul>
              </div>
            </article>
          ) : null}
        </section>

        <section className="insight-card">
          <div className="insight-head">
            <div>
              <p className="insight-kicker">Relatório executivo</p>
              <h2 className="insight-title">Executive Report</h2>
              <p className="insight-description">
                Documento executivo para apresentação estruturada, leitura aprofundada e comunicação estratégica.
              </p>
            </div>
            <span className="insight-badge">Relatório analítico</span>
          </div>

          {executiveReportError ? (
            <p className="status-message status-message--error">{executiveReportError}</p>
          ) : null}

          {executivePdfError ? (
            <p className="status-message status-message--error">{executivePdfError}</p>
          ) : null}

          {!executiveReportData && !executiveReportLoading ? (
            <p className="insight-empty">
              Clique em “Executive Report” em um dos casos para carregar o relatório executivo.
            </p>
          ) : null}

          {executiveReportLoading ? (
            <p className="insight-empty">Carregando executive report...</p>
          ) : null}

          {executiveReportData ? (
            <article
              style={{
                background: 'linear-gradient(180deg, #0f172a 0%, #0b1220 100%)',
                border: '1px solid #2a3655',
                borderRadius: '18px',
                padding: '20px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.28)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '16px',
                  flexWrap: 'wrap',
                }}
              >
                <p
                  style={{
                    margin: 0,
                    color: '#cbd5e1',
                    fontSize: '14px',
                    fontWeight: 600,
                    letterSpacing: '0.2px',
                  }}
                >
                  Caso analisado: #{executiveReportData.case_id}
                </p>

                <span className="insight-badge">
                  Relatório executivo real
                </span>
              </div>

              <div
                style={{
                  background: '#0a0f1c',
                  border: '1px solid #24304f',
                  borderRadius: '14px',
                  padding: '22px',
                  color: '#dbe4f0',
                  overflowX: 'auto',
                  lineHeight: 1.7,
                  fontSize: '15px',
                }}
              >
                <style>
                  {`
                    .executive-report-html,
                    .executive-report-html * {
                      color: #cfd9e8 !important;
                      box-sizing: border-box;
                    }

                    .executive-report-html {
                      background: #0a0f1c !important;
                    }

                    .executive-report-html h1,
                    .executive-report-html h2,
                    .executive-report-html h3,
                    .executive-report-html h4 {
                      color: #eaf2ff !important;
                      margin-top: 0;
                      margin-bottom: 12px;
                      line-height: 1.25;
                      background: transparent !important;
                    }

                    .executive-report-html h1 {
                      font-size: 28px;
                      margin-bottom: 18px;
                      padding-bottom: 10px;
                      border-bottom: 1px solid #2b456b;
                    }

                    .executive-report-html h2 {
                      font-size: 22px;
                      margin-top: 28px;
                      padding-left: 12px;
                      border-left: 4px solid #6fd6b2;
                    }

                    .executive-report-html h3 {
                      font-size: 18px;
                      margin-top: 22px;
                      color: #cfe1ff !important;
                    }

                    .executive-report-html p,
                    .executive-report-html span,
                    .executive-report-html div,
                    .executive-report-html li,
                    .executive-report-html small {
                      color: #b8c7da !important;
                      background: transparent !important;
                    }

                    .executive-report-html p {
                      margin: 0 0 14px;
                    }

                    .executive-report-html ul,
                    .executive-report-html ol {
                      margin: 0 0 16px 0;
                      padding-left: 22px;
                      color: #b8c7da !important;
                      background: transparent !important;
                    }

                    .executive-report-html li {
                      margin-bottom: 8px;
                    }

                    .executive-report-html strong,
                    .executive-report-html b {
                      color: #eaf2ff !important;
                    }

                    .executive-report-html section,
                    .executive-report-html article,
                    .executive-report-html header {
                      background: transparent !important;
                    }

                    .executive-report-html table {
                      width: 100%;
                      border-collapse: collapse;
                      margin: 18px 0;
                      background: #0f172a !important;
                      border: 1px solid #2b456b;
                      border-radius: 12px;
                      overflow: hidden;
                    }

                    .executive-report-html th,
                    .executive-report-html td {
                      border: 1px solid #2b456b;
                      padding: 12px;
                      text-align: left;
                      color: #c7d4e6 !important;
                      background: #0f172a !important;
                    }

                    .executive-report-html th {
                      background: #10203a !important;
                      color: #eaf2ff !important;
                      font-weight: 700;
                    }

                    .executive-report-html tr:nth-child(even) td {
                      background: #0d1d36 !important;
                    }

                    .executive-report-html blockquote {
                      margin: 18px 0;
                      padding: 14px 16px;
                      border-left: 4px solid #60a5fa;
                      background: rgba(96, 165, 250, 0.05) !important;
                      color: #cfe1ff !important;
                      border-radius: 10px;
                    }

                    .executive-report-html hr {
                      border: none;
                      border-top: 1px solid #24304f;
                      margin: 24px 0;
                    }

                    .executive-report-html code {
                      background: #111827 !important;
                      border: 1px solid #2b456b;
                      color: #f6d979 !important;
                      padding: 2px 6px;
                      border-radius: 6px;
                      font-size: 13px;
                    }

                    .executive-report-html [style*="background"],
                    .executive-report-html [style*="background-color"] {
                      background: transparent !important;
                    }

                    .executive-report-html [style*="color: white"],
                    .executive-report-html [style*="color:#fff"],
                    .executive-report-html [style*="color: #fff"],
                    .executive-report-html [style*="color:#ffffff"],
                    .executive-report-html [style*="color: #ffffff"],
                    .executive-report-html [style*="color: black"],
                    .executive-report-html [style*="color:#000"],
                    .executive-report-html [style*="color: #000"],
                    .executive-report-html [style*="color:#000000"],
                    .executive-report-html [style*="color: #000000"] {
                      color: #cfd9e8 !important;
                    }

                    .executive-report-html > div,
                    .executive-report-html > section,
                    .executive-report-html > article {
                      background: transparent !important;
                    }
                  `}
                </style>

                <div
                  className="executive-report-html"
                  dangerouslySetInnerHTML={{ __html: executiveReportData.report_html }}
                />
              </div>
            </article>
          ) : null}
        </section>

        <section className="insight-card">
          <div className="insight-head">
            <div>
              <p className="insight-kicker">Carteira jurídica</p>
              <h2 className="insight-title">Casos do escritório</h2>
              <p className="insight-description">
                Lista operacional dos casos carregados via API da IA Trabalhista Robusta.
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

          <div
            style={{
              display: 'grid',
              gap: '12px',
            }}
          >
            {cases.map((caso) => (
              <article
                key={caso.id}
                style={{
                  background: '#0f172a',
                  border: '1px solid #24304f',
                  borderRadius: '14px',
                  padding: '16px',
                }}
              >
                <strong style={{ display: 'block', marginBottom: '6px', fontSize: '18px' }}>
                  {caso.title}
                </strong>

                <p style={{ margin: '0 0 8px', color: '#9aa4bf' }}>
                  {caso.case_number}
                </p>

                <p style={{ margin: '0 0 12px', color: '#c7d0e0' }}>
                  {caso.description}
                </p>

                <div
                  style={{
                    display: 'flex',
                    gap: '10px',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                  }}
                >
                  <span
                    style={{
                      display: 'inline-block',
                      background: '#1d2842',
                      color: '#d4af37',
                      borderRadius: '999px',
                      padding: '6px 10px',
                      fontSize: '12px',
                      fontWeight: 700,
                    }}
                  >
                    {caso.status}
                  </span>

                  <span style={{ color: '#9aa4bf', fontSize: '13px' }}>
                    ID do caso: {caso.id}
                  </span>

                  <span style={{ color: '#9aa4bf', fontSize: '13px' }}>
                    Tenant: {caso.tenant_id}
                  </span>

                  <button
                    type="button"
                    onClick={() => handleAnalyzeCase(caso.id)}
                    disabled={analysisLoading}
                    style={{
                      background: analysisLoading && selectedCaseId === caso.id ? '#5b6478' : '#d4af37',
                      color: '#111',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '10px 14px',
                      fontWeight: 700,
                      cursor: analysisLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {analysisLoading && selectedCaseId === caso.id ? 'Analisando...' : 'Analisar caso'}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleLoadExecutiveSummary(caso.id)}
                    disabled={executiveSummaryLoading}
                    style={{
                      background: executiveSummaryLoading && selectedCaseId === caso.id ? '#5b6478' : '#7dd3fc',
                      color: '#111',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '10px 14px',
                      fontWeight: 700,
                      cursor: executiveSummaryLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {executiveSummaryLoading && selectedCaseId === caso.id ? 'Carregando resumo...' : 'Executive Summary'}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleLoadExecutiveReport(caso.id)}
                    disabled={executiveReportLoading}
                    style={{
                      background: executiveReportLoading && selectedCaseId === caso.id ? '#5b6478' : '#86efac',
                      color: '#111',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '10px 14px',
                      fontWeight: 700,
                      cursor: executiveReportLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {executiveReportLoading && selectedCaseId === caso.id ? 'Carregando report...' : 'Executive Report'}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOpenExecutivePdf(caso.id)}
                    disabled={executivePdfLoading}
                    style={{
                      background: executivePdfLoading && selectedCaseId === caso.id ? '#5b6478' : '#fca5a5',
                      color: '#111',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '10px 14px',
                      fontWeight: 700,
                      cursor: executivePdfLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {executivePdfLoading && selectedCaseId === caso.id ? 'Abrindo PDF...' : 'Executive PDF'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
