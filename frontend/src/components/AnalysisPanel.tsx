import type { CaseAnalysisResponse } from '../services/api'

type AnalysisPanelProps = {
  analysisData: CaseAnalysisResponse | null
  analysisLoading: boolean
  analysisError: string
  getRiskLabel: (risk: string | undefined) => string
}

export function AnalysisPanel({
  analysisData,
  analysisLoading,
  analysisError,
  getRiskLabel,
}: AnalysisPanelProps) {
  return (
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
      ) : null}
    </section>
  )
}
