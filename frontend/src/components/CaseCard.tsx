import type { CaseItem } from '../services/api'

type CaseCardProps = {
  caso: CaseItem
  selectedCaseId: number | null
  getStatusLabel: (status: string) => string
  isArchiving: boolean
  isAnalyzing: boolean
  isLoadingSummary: boolean
  isLoadingReport: boolean
  isLoadingPdf: boolean
  analysisLoading: boolean
  executiveSummaryLoading: boolean
  executiveReportLoading: boolean
  executivePdfLoading: boolean
  onArchive: (caseId: number) => void
  onAnalyze: (caseId: number) => void
  onLoadExecutiveSummary: (caseId: number) => void
  onLoadExecutiveReport: (caseId: number) => void
  onOpenExecutivePdf: (caseId: number) => void
}

export function CaseCard({
  caso,
  selectedCaseId,
  getStatusLabel,
  isArchiving,
  isAnalyzing,
  isLoadingSummary,
  isLoadingReport,
  isLoadingPdf,
  analysisLoading,
  executiveSummaryLoading,
  executiveReportLoading,
  executivePdfLoading,
  onArchive,
  onAnalyze,
  onLoadExecutiveSummary,
  onLoadExecutiveReport,
  onOpenExecutivePdf,
}: CaseCardProps) {
  const isSelected = selectedCaseId === caso.id

  return (
    <article
      style={{
        background: isSelected
          ? 'linear-gradient(180deg, rgba(20,33,61,0.96) 0%, rgba(12,23,45,0.98) 100%)'
          : '#0f172a',
        border: isSelected ? '1px solid #d4af37' : '1px solid #24304f',
        borderRadius: '16px',
        padding: '18px 18px 16px',
        boxShadow: isSelected
          ? '0 0 0 1px rgba(212,175,55,0.12), 0 18px 40px rgba(0,0,0,0.24)'
          : '0 10px 24px rgba(0,0,0,0.18)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '12px',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          marginBottom: '10px',
        }}
      >
        <div style={{ minWidth: 0, flex: '1 1 480px' }}>
          <strong
            style={{
              display: 'block',
              marginBottom: '6px',
              fontSize: '20px',
              lineHeight: 1.2,
              color: '#f8fafc',
            }}
          >
            {caso.title}
          </strong>

          <p
            style={{
              margin: '0 0 10px',
              color: '#f3c969',
              fontSize: '13px',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {caso.case_number}
          </p>

          <p
            style={{
              margin: 0,
              color: '#d6deeb',
              fontSize: '14px',
              lineHeight: 1.55,
              maxWidth: '920px',
            }}
          >
            {caso.description}
          </p>
        </div>

        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#1b2740',
            color: '#f3c969',
            border: '1px solid rgba(212,175,55,0.28)',
            borderRadius: '999px',
            padding: '7px 12px',
            fontSize: '12px',
            fontWeight: 700,
            whiteSpace: 'nowrap',
          }}
        >
          {getStatusLabel(caso.status)}
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '14px',
          flexWrap: 'wrap',
          alignItems: 'center',
          marginBottom: '14px',
          paddingTop: '10px',
          borderTop: '1px solid rgba(212,175,55,0.12)',
        }}
      >
        <span style={{ color: '#93a4c3', fontSize: '12px' }}>
          <strong style={{ color: '#cdd8ea' }}>ID:</strong> {caso.id}
        </span>

        <span style={{ color: '#93a4c3', fontSize: '12px' }}>
          <strong style={{ color: '#cdd8ea' }}>Tenant:</strong> {caso.tenant_id}
        </span>

        {isSelected ? (
          <span
            style={{
              color: '#f3c969',
              fontSize: '12px',
              fontWeight: 700,
              letterSpacing: '0.02em',
            }}
          >
            Caso em foco
          </span>
        ) : null}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '10px',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        {caso.status !== 'archived' ? (
          <button
            type="button"
            onClick={() => onArchive(caso.id)}
            disabled={isArchiving}
            style={{
              background: isArchiving ? '#4b5565' : '#182235',
              color: '#f3c969',
              border: '1px solid rgba(212,175,55,0.28)',
              borderRadius: '10px',
              padding: '9px 14px',
              fontWeight: 700,
              cursor: isArchiving ? 'not-allowed' : 'pointer',
              opacity: 0.92,
            }}
          >
            {isArchiving ? 'Arquivando...' : 'Arquivar'}
          </button>
        ) : null}

        <button
          type="button"
          onClick={() => onAnalyze(caso.id)}
          disabled={analysisLoading}
          style={{
            background: isAnalyzing ? '#4b5565' : '#d4af37',
            color: '#111827',
            border: 'none',
            borderRadius: '10px',
            padding: '9px 14px',
            fontWeight: 800,
            cursor: analysisLoading ? 'not-allowed' : 'pointer',
            boxShadow: isAnalyzing ? 'none' : '0 12px 28px rgba(212,175,55,0.28)',
            transform: 'translateY(0)',
          }}
        >
          {isAnalyzing ? 'Analisando...' : 'Analisar caso'}
        </button>

        <button
          type="button"
          onClick={() => onLoadExecutiveSummary(caso.id)}
          disabled={executiveSummaryLoading}
          style={{
            background: isLoadingSummary ? '#4b5565' : '#13233f',
            color: '#cfe0ff',
            border: '1px solid rgba(125,211,252,0.22)',
            borderRadius: '10px',
            padding: '9px 14px',
            fontWeight: 700,
            cursor: executiveSummaryLoading ? 'not-allowed' : 'pointer',
            opacity: 0.92,
          }}
        >
          {isLoadingSummary ? 'Carregando resumo...' : 'Resumo Executivo'}
        </button>

        <button
          type="button"
          onClick={() => onLoadExecutiveReport(caso.id)}
          disabled={executiveReportLoading}
          style={{
            background: isLoadingReport ? '#4b5565' : '#132a22',
            color: '#c9f7da',
            border: '1px solid rgba(134,239,172,0.22)',
            borderRadius: '10px',
            padding: '9px 14px',
            fontWeight: 700,
            cursor: executiveReportLoading ? 'not-allowed' : 'pointer',
            opacity: 0.92,
          }}
        >
          {isLoadingReport ? 'Carregando relatório...' : 'Relatório Executivo'}
        </button>

        <button
          type="button"
          onClick={() => onOpenExecutivePdf(caso.id)}
          disabled={executivePdfLoading}
          style={{
            background: isLoadingPdf ? '#4b5565' : '#2a1720',
            color: '#ffd5de',
            border: '1px solid rgba(252,165,165,0.22)',
            borderRadius: '10px',
            padding: '9px 14px',
            fontWeight: 700,
            cursor: executivePdfLoading ? 'not-allowed' : 'pointer',
            opacity: 0.92,
          }}
        >
          {isLoadingPdf ? 'Abrindo PDF...' : 'PDF Executivo'}
        </button>
      </div>
    </article>
  )
}
