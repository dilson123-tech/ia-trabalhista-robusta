import type {
  CaseAnalysisResponse,
  ExecutiveReportResponse,
  ExecutiveSummaryResponse,
} from '../services/api'

type FocusTab = 'analysis' | 'summary' | 'report'

type CaseFocusPanelProps = {
  selectedCaseId: number | null
  activeTab: FocusTab
  onTabChange: (tab: FocusTab) => void
  analysisData: CaseAnalysisResponse | null
  analysisLoading: boolean
  analysisError: string
  executiveSummaryData: ExecutiveSummaryResponse | null
  executiveSummaryLoading: boolean
  executiveSummaryError: string
  executiveReportData: ExecutiveReportResponse | null
  executiveReportLoading: boolean
  executiveReportError: string
  executivePdfError: string
  getRiskLabel: (risk: string | undefined) => string
}

const tabLabels: Record<FocusTab, string> = {
  analysis: 'Análise',
  summary: 'Resumo Executivo',
  report: 'Relatório Executivo',
}

const panelTitles: Record<FocusTab, string> = {
  analysis: 'Leitura técnica do caso',
  summary: 'Resumo executivo do caso',
  report: 'Relatório executivo do caso',
}

const panelDescriptions: Record<FocusTab, string> = {
  analysis: 'Diagnóstico rápido para apoiar decisão operacional sem tirar a usuária do fluxo da carteira.',
  summary: 'Visão consolidada para alinhamento interno, priorização e comunicação com gestão.',
  report: 'Documento analítico completo para leitura aprofundada e apresentação estruturada.',
}

const emptyMessages: Record<FocusTab, string> = {
  analysis: 'Clique em “Analisar caso” no card para carregar a análise deste caso.',
  summary: 'Clique em “Resumo Executivo” no card para carregar o resumo deste caso.',
  report: 'Clique em “Relatório Executivo” no card para carregar o relatório deste caso.',
}

export function CaseFocusPanel({
  selectedCaseId,
  activeTab,
  onTabChange,
  analysisData,
  analysisLoading,
  analysisError,
  executiveSummaryData,
  executiveSummaryLoading,
  executiveSummaryError,
  executiveReportData,
  executiveReportLoading,
  executiveReportError,
  executivePdfError,
  getRiskLabel,
}: CaseFocusPanelProps) {
  const renderAnalysisContent = () => {
    if (analysisError) {
      return <p className="status-message status-message--error">{analysisError}</p>
    }

    if (analysisLoading) {
      return <p className="insight-empty">Analisando caso selecionado...</p>
    }

    if (!analysisData) {
      return <p className="insight-empty">{emptyMessages.analysis}</p>
    }

    return (
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
            {getRiskLabel(analysisData.analysis?.technical?.risk_level)}
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
    )
  }

  const renderSummaryContent = () => {
    if (executiveSummaryError) {
      return <p className="status-message status-message--error">{executiveSummaryError}</p>
    }

    if (executiveSummaryLoading) {
      return <p className="insight-empty">Carregando resumo executivo...</p>
    }

    if (!executiveSummaryData) {
      return <p className="insight-empty">{emptyMessages.summary}</p>
    }

    return (
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
            <li>Risco técnico: {getRiskLabel(executiveSummaryData.technical_analysis?.risk_level)}</li>
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
    )
  }

  const renderReportContent = () => {
    if (executiveReportError) {
      return <p className="status-message status-message--error">{executiveReportError}</p>
    }

    if (executivePdfError) {
      return <p className="status-message status-message--error">{executivePdfError}</p>
    }

    if (executiveReportLoading) {
      return <p className="insight-empty">Carregando relatório executivo...</p>
    }

    if (!executiveReportData) {
      return <p className="insight-empty">{emptyMessages.report}</p>
    }

    return (
      <article
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
        <p className="info-meta" style={{ marginBottom: '14px' }}>
          Caso analisado: #{executiveReportData.case_id}
        </p>

        <style>
          {`
            .executive-report-html,
            .executive-report-html * {
              color: #cfd9e8 !important;
              box-sizing: border-box;
            }

            .executive-report-html {
              background: transparent !important;
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
      </article>
    )
  }

  const renderActiveContent = () => {
    if (!selectedCaseId) {
      return (
        <p className="insight-empty">
          Selecione um caso e clique em “Analisar caso”, “Resumo Executivo” ou “Relatório Executivo”.
        </p>
      )
    }

    if (activeTab === 'analysis') return renderAnalysisContent()
    if (activeTab === 'summary') return renderSummaryContent()
    return renderReportContent()
  }

  return (
    <div
      style={{
        position: 'sticky',
        top: '20px',
        display: 'grid',
        gap: '12px',
        alignSelf: 'start',
      }}
    >
      <section className="insight-card">
        <div className="insight-head">
          <div>
            <p className="insight-kicker">Caso em foco</p>
            <h2 className="insight-title">Painel operacional</h2>
            <p className="insight-description">
              Resultado imediato do caso selecionado, sem precisar subir a tela para localizar a resposta.
            </p>
          </div>
          <span className="insight-badge">
            {selectedCaseId ? `Caso #${selectedCaseId}` : 'Nenhum caso selecionado'}
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gap: '14px',
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
              gap: '10px',
            }}
          >
            {(['analysis', 'summary', 'report'] as FocusTab[]).map((tab) => {
              const isActive = activeTab === tab
              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => onTabChange(tab)}
                  style={{
                    background: isActive ? '#d4af37' : '#13233f',
                    color: isActive ? '#111827' : '#dbe7f6',
                    border: isActive ? 'none' : '1px solid rgba(125,211,252,0.18)',
                    borderRadius: '12px',
                    minHeight: '48px',
                    padding: '10px 14px',
                    fontWeight: 800,
                    fontSize: '13px',
                    lineHeight: 1.2,
                    cursor: 'pointer',
                    boxShadow: isActive ? '0 12px 28px rgba(212,175,55,0.24)' : 'none',
                  }}
                >
                  {tabLabels[tab]}
                </button>
              )
            })}
          </div>

          <div
            style={{
              borderRadius: '16px',
              border: '1px solid rgba(212,175,55,0.16)',
              background: 'linear-gradient(180deg, rgba(12,20,38,0.96) 0%, rgba(10,16,30,0.98) 100%)',
              padding: '18px',
              boxShadow: '0 18px 40px rgba(0,0,0,0.22)',
            }}
          >
            <div style={{ marginBottom: '14px' }}>
              <p
                style={{
                  margin: '0 0 6px',
                  color: '#f3c969',
                  fontSize: '11px',
                  fontWeight: 800,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                }}
              >
                {tabLabels[activeTab]}
              </p>
              <h3
                style={{
                  margin: '0 0 6px',
                  color: '#f8fafc',
                  fontSize: '24px',
                  lineHeight: 1.15,
                }}
              >
                {panelTitles[activeTab]}
              </h3>
              <p
                style={{
                  margin: 0,
                  color: '#aebed8',
                  fontSize: '14px',
                  lineHeight: 1.6,
                }}
              >
                {panelDescriptions[activeTab]}
              </p>
            </div>

            {renderActiveContent()}
          </div>
        </div>
      </section>
    </div>
  )
}
