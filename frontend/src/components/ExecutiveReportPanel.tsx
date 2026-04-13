import type { ExecutiveReportResponse } from '../services/api'

type ExecutiveReportPanelProps = {
  executiveReportData: ExecutiveReportResponse | null
  executiveReportLoading: boolean
  executiveReportError: string
  executivePdfError: string
}

export function ExecutiveReportPanel({
  executiveReportData,
  executiveReportLoading,
  executiveReportError,
  executivePdfError,
}: ExecutiveReportPanelProps) {
  return (
    <section className="insight-card">
      <div className="insight-head">
        <div>
          <p className="insight-kicker">Relatório executivo</p>
          <h2 className="insight-title">Relatório Executivo</h2>
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
          Clique em “Relatório Executivo” em um dos casos para carregar o relatório executivo.
        </p>
      ) : null}

      {executiveReportLoading ? (
        <p className="insight-empty">Carregando relatório executivo...</p>
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

            <span className="insight-badge">Relatório executivo real</span>
          </div>

          {(executiveReportData.analysis_foundations?.normative_basis?.length ||
            executiveReportData.analysis_foundations?.factual_elements_considered?.length ||
            executiveReportData.analysis_foundations?.probative_gaps?.length ||
            executiveReportData.analysis_foundations?.analysis_context ||
            executiveReportData.analysis_foundations?.disclaimer) ? (
            <div
              style={{
                marginBottom: '16px',
                padding: '16px',
                borderRadius: '14px',
                border: '1px solid #24304f',
                background: '#0a0f1c',
                color: '#dbe4f0',
              }}
            >
              <h3 style={{ marginTop: 0, marginBottom: '12px', color: '#eaf2ff' }}>Base de confiança da análise</h3>

              {(executiveReportData.analysis_foundations?.normative_basis || []).length > 0 ? (
                <>
                  <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#cfe1ff' }}>Base normativa considerada</p>
                  <ul style={{ marginTop: 0, marginBottom: '12px', paddingLeft: '20px' }}>
                    {(executiveReportData.analysis_foundations?.normative_basis || []).map((item, index) => (
                      <li key={`normative-${index}`}>{item}</li>
                    ))}
                  </ul>
                </>
              ) : null}

              {(executiveReportData.analysis_foundations?.factual_elements_considered || []).length > 0 ? (
                <>
                  <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#cfe1ff' }}>Elementos fáticos considerados</p>
                  <ul style={{ marginTop: 0, marginBottom: '12px', paddingLeft: '20px' }}>
                    {(executiveReportData.analysis_foundations?.factual_elements_considered || []).map((item, index) => (
                      <li key={`facts-${index}`}>{item}</li>
                    ))}
                  </ul>
                </>
              ) : null}

              {(executiveReportData.analysis_foundations?.probative_gaps || []).length > 0 ? (
                <>
                  <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#cfe1ff' }}>Lacunas probatórias</p>
                  <ul style={{ marginTop: 0, marginBottom: '12px', paddingLeft: '20px' }}>
                    {(executiveReportData.analysis_foundations?.probative_gaps || []).map((item, index) => (
                      <li key={`gaps-${index}`}>{item}</li>
                    ))}
                  </ul>
                </>
              ) : null}

              {executiveReportData.analysis_foundations?.analysis_context ? (
                <p style={{ margin: '0 0 10px', color: '#b8c7da' }}>
                  <strong style={{ color: '#eaf2ff' }}>Critério de confiança:</strong>{' '}
                  Área {executiveReportData.analysis_foundations.analysis_context.legal_area || 'não informada'} •
                  status {executiveReportData.analysis_foundations.analysis_context.final_status || 'não informado'} •
                  probabilidade {executiveReportData.analysis_foundations.analysis_context.probability_percent ?? 'não informada'}% •
                  viabilidade {executiveReportData.analysis_foundations.analysis_context.viability_label || 'não informada'}
                </p>
              ) : null}

              {executiveReportData.analysis_foundations?.disclaimer ? (
                <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
                  {executiveReportData.analysis_foundations.disclaimer}
                </p>
              ) : null}
            </div>
          ) : null}

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
  )
}
