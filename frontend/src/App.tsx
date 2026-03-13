import { useState } from 'react'
import { ApiError, getCases, getCaseAnalysis, getExecutiveSummary, getExecutiveReport, getExecutivePdf, type CaseItem, type CaseAnalysisResponse, type ExecutiveSummaryResponse, type ExecutiveReportResponse } from './services/api'

function App() {
  const [token, setToken] = useState('')
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

  function handleApiFailure(err: unknown, fallbackMessage: string) {
    console.error(err)

    if (err instanceof ApiError && err.status === 401) {
      setToken('')
      setCases([])
      setLoaded(false)
      setSelectedCaseId(null)
      setAnalysisData(null)
      setExecutiveSummaryData(null)
      setExecutiveReportData(null)
      setError(err.message)
      setAnalysisError('')
      setExecutiveSummaryError('')
      setExecutiveReportError('')
      setExecutivePdfError('')
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

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#0b1020',
        color: '#f5f7fb',
        fontFamily: 'Arial, sans-serif',
        padding: '32px',
      }}
    >
      <section
        style={{
          maxWidth: '1100px',
          margin: '0 auto',
        }}
      >
        <header
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '32px',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <p style={{ margin: 0, color: '#9aa4bf', fontSize: '14px' }}>
              IA Trabalhista Robusta
            </p>
            <h1 style={{ margin: '8px 0 0', fontSize: '32px' }}>
              Painel do Advogado
            </h1>
          </div>

          <button
            style={{
              background: '#d4af37',
              color: '#111',
              border: 'none',
              borderRadius: '10px',
              padding: '14px 20px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
            type="button"
          >
            + Novo Caso
          </button>
        </header>

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <h2 style={{ marginTop: 0 }}>Conectar com a API</h2>
          <p style={{ color: '#9aa4bf' }}>
            Cole abaixo o token Bearer obtido no backend para carregar os casos reais.
          </p>

          <textarea
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Cole aqui o token JWT"
            style={{
              width: '100%',
              minHeight: '110px',
              resize: 'vertical',
              borderRadius: '12px',
              border: '1px solid #24304f',
              background: '#0f172a',
              color: '#f5f7fb',
              padding: '14px',
              fontSize: '14px',
              boxSizing: 'border-box',
              marginBottom: '16px',
            }}
          />

          <button
            type="button"
            onClick={handleLoadCases}
            disabled={loading || !token.trim()}
            style={{
              background: loading || !token.trim() ? '#5b6478' : '#d4af37',
              color: '#111',
              border: 'none',
              borderRadius: '10px',
              padding: '14px 20px',
              fontWeight: 700,
              cursor: loading || !token.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Carregando casos...' : 'Carregar casos reais'}
          </button>

          {error ? (
            <p style={{ color: '#ff7b7b', marginTop: '14px' }}>{error}</p>
          ) : null}
        </section>

        <section
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            marginBottom: '32px',
          }}
        >
          {[
            ['Casos carregados', String(cases.length)],
            ['Backend', 'Online'],
            ['Modo', loaded ? 'Real' : 'Demo'],
            ['Token', token.trim() ? 'Informado' : 'Pendente'],
          ].map(([label, value]) => (
            <article
              key={label}
              style={{
                background: '#121a2f',
                border: '1px solid #1e2945',
                borderRadius: '16px',
                padding: '20px',
              }}
            >
              <p style={{ margin: 0, color: '#9aa4bf', fontSize: '14px' }}>{label}</p>
              <h2 style={{ margin: '10px 0 0', fontSize: '28px' }}>{value}</h2>
            </article>
          ))}
        </section>

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '22px' }}>Resultado da análise jurídica</h2>
            <p style={{ margin: '8px 0 0', color: '#9aa4bf' }}>
              Retorno real da IA para o caso selecionado.
            </p>
          </div>

          {analysisError ? (
            <p style={{ color: '#ff7b7b', marginBottom: '12px' }}>{analysisError}</p>
          ) : null}

          {!analysisData && !analysisLoading ? (
            <p style={{ color: '#9aa4bf' }}>
              Clique em “Analisar caso” em um dos cards para carregar o diagnóstico.
            </p>
          ) : null}

          {analysisLoading ? (
            <p style={{ color: '#9aa4bf' }}>Analisando caso selecionado...</p>
          ) : null}

          {analysisData ? (
            <div
              style={{
                display: 'grid',
                gap: '12px',
              }}
            >
              <article
                style={{
                  background: '#0f172a',
                  border: '1px solid #24304f',
                  borderRadius: '14px',
                  padding: '16px',
                }}
              >
                <p style={{ margin: '0 0 10px', color: '#9aa4bf' }}>
                  Caso analisado: {analysisData.case_id} | Análise: {analysisData.analysis_id}
                </p>

                <p style={{ margin: '0 0 10px', color: '#f5f7fb' }}>
                  <strong>Resumo técnico:</strong>{' '}
                  {analysisData.analysis?.technical?.summary || 'Resumo não disponível.'}
                </p>

                <p style={{ margin: '0 0 10px', color: '#f5f7fb' }}>
                  <strong>Nível de risco:</strong>{' '}
                  {analysisData.analysis?.technical?.risk_level || 'Não informado'}
                </p>

                <div style={{ marginBottom: '10px' }}>
                  <strong style={{ display: 'block', marginBottom: '6px' }}>Pontos de atenção</strong>
                  <ul style={{ margin: 0, paddingLeft: '18px', color: '#c7d0e0' }}>
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
                  <strong style={{ display: 'block', marginBottom: '6px' }}>Próximos passos</strong>
                  <ul style={{ margin: 0, paddingLeft: '18px', color: '#c7d0e0' }}>
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

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '22px' }}>Executive Summary</h2>
            <p style={{ margin: '8px 0 0', color: '#9aa4bf' }}>
              Resumo executivo real do caso selecionado.
            </p>
          </div>

          {executiveSummaryError ? (
            <p style={{ color: '#ff7b7b', marginBottom: '12px' }}>{executiveSummaryError}</p>
          ) : null}

          {!executiveSummaryData && !executiveSummaryLoading ? (
            <p style={{ color: '#9aa4bf' }}>
              Clique em “Executive Summary” em um dos casos para carregar o resumo executivo.
            </p>
          ) : null}

          {executiveSummaryLoading ? (
            <p style={{ color: '#9aa4bf' }}>Carregando executive summary...</p>
          ) : null}

          {executiveSummaryData ? (
            <article
              style={{
                background: '#0f172a',
                border: '1px solid #24304f',
                borderRadius: '14px',
                padding: '16px',
              }}
            >
              <p style={{ margin: '0 0 10px', color: '#9aa4bf' }}>
                Caso: {executiveSummaryData.case.title} | Nº {executiveSummaryData.case.case_number}
              </p>

              <p style={{ margin: '0 0 10px', color: '#f5f7fb' }}>
                <strong>Resumo técnico:</strong>{' '}
                {executiveSummaryData.technical_analysis?.summary || 'Resumo não disponível.'}
              </p>

              <p style={{ margin: '0 0 10px', color: '#f5f7fb' }}>
                <strong>Risco:</strong>{' '}
                {executiveSummaryData.technical_analysis?.risk_level || 'Não informado'}
              </p>

              <div style={{ marginBottom: '10px' }}>
                <strong style={{ display: 'block', marginBottom: '6px' }}>Pontos de atenção</strong>
                <ul style={{ margin: 0, paddingLeft: '18px', color: '#c7d0e0' }}>
                  {(executiveSummaryData.technical_analysis?.issues || []).length > 0 ? (
                    (executiveSummaryData.technical_analysis?.issues || []).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))
                  ) : (
                    <li>Nenhum ponto crítico informado.</li>
                  )}
                </ul>
              </div>

              <div>
                <strong style={{ display: 'block', marginBottom: '6px' }}>Próximos passos</strong>
                <ul style={{ margin: 0, paddingLeft: '18px', color: '#c7d0e0' }}>
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

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '22px' }}>Executive Report</h2>
            <p style={{ margin: '8px 0 0', color: '#9aa4bf' }}>
              Relatório executivo real do caso selecionado.
            </p>
          </div>

          {executiveReportError ? (
            <p style={{ color: '#ff7b7b', marginBottom: '12px' }}>{executiveReportError}</p>
          ) : null}

          {executivePdfError ? (
            <p style={{ color: '#ff7b7b', marginBottom: '12px' }}>{executivePdfError}</p>
          ) : null}

          {!executiveReportData && !executiveReportLoading ? (
            <p style={{ color: '#9aa4bf' }}>
              Clique em “Executive Report” em um dos casos para carregar o relatório executivo.
            </p>
          ) : null}

          {executiveReportLoading ? (
            <p style={{ color: '#9aa4bf' }}>Carregando executive report...</p>
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

                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '6px 10px',
                    borderRadius: '999px',
                    background: 'rgba(134, 239, 172, 0.12)',
                    border: '1px solid rgba(134, 239, 172, 0.35)',
                    color: '#86efac',
                    fontSize: '12px',
                    fontWeight: 700,
                  }}
                >
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
                      color: #e5edf7 !important;
                      box-sizing: border-box;
                    }

                    .executive-report-html {
                      background: #0a0f1c !important;
                    }

                    .executive-report-html h1,
                    .executive-report-html h2,
                    .executive-report-html h3,
                    .executive-report-html h4 {
                      color: #f8fafc !important;
                      margin-top: 0;
                      margin-bottom: 12px;
                      line-height: 1.25;
                      background: transparent !important;
                    }

                    .executive-report-html h1 {
                      font-size: 28px;
                      margin-bottom: 18px;
                      padding-bottom: 10px;
                      border-bottom: 1px solid #24304f;
                    }

                    .executive-report-html h2 {
                      font-size: 22px;
                      margin-top: 28px;
                      padding-left: 12px;
                      border-left: 4px solid #86efac;
                    }

                    .executive-report-html h3 {
                      font-size: 18px;
                      margin-top: 22px;
                      color: #dbeafe !important;
                    }

                    .executive-report-html p,
                    .executive-report-html span,
                    .executive-report-html div,
                    .executive-report-html li,
                    .executive-report-html small {
                      color: #cbd5e1 !important;
                      background: transparent !important;
                    }

                    .executive-report-html p {
                      margin: 0 0 14px;
                    }

                    .executive-report-html ul,
                    .executive-report-html ol {
                      margin: 0 0 16px 0;
                      padding-left: 22px;
                      color: #cbd5e1 !important;
                      background: transparent !important;
                    }

                    .executive-report-html li {
                      margin-bottom: 8px;
                    }

                    .executive-report-html strong,
                    .executive-report-html b {
                      color: #f8fafc !important;
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
                      border: 1px solid #24304f;
                      border-radius: 12px;
                      overflow: hidden;
                    }

                    .executive-report-html th,
                    .executive-report-html td {
                      border: 1px solid #24304f;
                      padding: 12px;
                      text-align: left;
                      color: #dbe4f0 !important;
                      background: #0f172a !important;
                    }

                    .executive-report-html th {
                      background: #111a2e !important;
                      color: #f8fafc !important;
                      font-weight: 700;
                    }

                    .executive-report-html tr:nth-child(even) td {
                      background: #101a30 !important;
                    }

                    .executive-report-html blockquote {
                      margin: 18px 0;
                      padding: 14px 16px;
                      border-left: 4px solid #60a5fa;
                      background: rgba(96, 165, 250, 0.08) !important;
                      color: #dbeafe !important;
                      border-radius: 10px;
                    }

                    .executive-report-html hr {
                      border: none;
                      border-top: 1px solid #24304f;
                      margin: 24px 0;
                    }

                    .executive-report-html code {
                      background: #111827 !important;
                      border: 1px solid #24304f;
                      color: #fde68a !important;
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
                      color: #e5edf7 !important;
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

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '22px' }}>Casos do escritório</h2>
            <p style={{ margin: '8px 0 0', color: '#9aa4bf' }}>
              Lista vinda da API da IA Trabalhista Robusta.
            </p>
          </div>

          {!loaded ? (
            <p style={{ color: '#9aa4bf' }}>
              Informe o token e clique em “Carregar casos reais”.
            </p>
          ) : null}

          {loaded && !loading && cases.length === 0 && !error ? (
            <p style={{ color: '#9aa4bf' }}>Nenhum caso encontrado para este token.</p>
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
