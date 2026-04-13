import type { ExecutiveSummaryResponse } from '../services/api'

type ExecutiveSummaryPanelProps = {
  executiveSummaryData: ExecutiveSummaryResponse | null
  executiveSummaryLoading: boolean
  executiveSummaryError: string
  getRiskLabel: (risk: string | undefined) => string
}

export function ExecutiveSummaryPanel({
  executiveSummaryData,
  executiveSummaryLoading,
  executiveSummaryError,
  getRiskLabel,
}: ExecutiveSummaryPanelProps) {
  return (
    <section className="insight-card">
      <div className="insight-head">
        <div>
          <p className="insight-kicker">Resumo executivo</p>
          <h2 className="insight-title">Resumo Executivo</h2>
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
          Clique em “Resumo Executivo” em um dos casos para carregar o resumo executivo.
        </p>
      ) : null}

      {executiveSummaryLoading ? (
        <p className="insight-empty">Carregando resumo executivo...</p>
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
            
              <strong className="info-list-title">Base normativa considerada</strong>
              <ul className="info-list">
                {(executiveSummaryData.analysis_foundations?.normative_basis || []).length > 0 ? (
                  (executiveSummaryData.analysis_foundations?.normative_basis || []).map((item, index) => (
                    <li key={index}>{item}</li>
                  ))
                ) : (
                  <li>Base normativa não informada.</li>
                )}
              </ul>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <strong className="info-list-title">Elementos fáticos considerados</strong>
              <ul className="info-list">
                {(executiveSummaryData.analysis_foundations?.factual_elements_considered || []).length > 0 ? (
                  (executiveSummaryData.analysis_foundations?.factual_elements_considered || []).map((item, index) => (
                    <li key={index}>{item}</li>
                  ))
                ) : (
                  <li>Elementos fáticos não informados.</li>
                )}
              </ul>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <strong className="info-list-title">Lacunas probatórias que impactam a conclusão</strong>
              <ul className="info-list">
                {(executiveSummaryData.analysis_foundations?.probative_gaps || []).length > 0 ? (
                  (executiveSummaryData.analysis_foundations?.probative_gaps || []).map((item, index) => (
                    <li key={index}>{item}</li>
                  ))
                ) : (
                  <li>Nenhuma lacuna probatória destacada.</li>
                )}
              </ul>
            </div>

            <p className="info-text">
              <strong>Critério de confiança:</strong>{' '}
              {executiveSummaryData.analysis_foundations?.disclaimer || 'Critério de confiança não informado.'}
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
      ) : null}
    </section>
  )
}
