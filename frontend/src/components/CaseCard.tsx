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
    <article className={`case-card ${isSelected ? 'case-card--selected' : ''}`}>
      <div className="case-card__header">
        <div className="case-card__content">
          <strong className="case-card__title">{caso.title}</strong>
          <p className="case-card__number">{caso.case_number}</p>
          <p className="case-card__description">{caso.description}</p>
        </div>

        <span className="case-card__status">{getStatusLabel(caso.status)}</span>
      </div>

      <div className="case-card__meta">
        <span className="case-card__meta-pill">
          <strong>ID:</strong> {caso.id}
        </span>

        <span className="case-card__meta-pill">
          <strong>Tenant:</strong> {caso.tenant_id}
        </span>

        {isSelected ? (
          <span className="case-card__focus-badge">Caso em foco</span>
        ) : null}
      </div>

      <div className="case-card__actions">
        {caso.status !== 'archived' ? (
          <button
            type="button"
            onClick={() => onArchive(caso.id)}
            disabled={isArchiving}
            className="case-card__action case-card__action--archive"
          >
            {isArchiving ? 'Arquivando...' : 'Arquivar'}
          </button>
        ) : null}

        <button
          type="button"
          onClick={() => onAnalyze(caso.id)}
          disabled={analysisLoading}
          className="case-card__action case-card__action--analysis"
        >
          {isAnalyzing ? 'Analisando...' : 'Analisar caso'}
        </button>

        <button
          type="button"
          onClick={() => onLoadExecutiveSummary(caso.id)}
          disabled={executiveSummaryLoading}
          className="case-card__action case-card__action--summary"
        >
          {isLoadingSummary ? 'Carregando resumo...' : 'Resumo Executivo'}
        </button>

        <button
          type="button"
          onClick={() => onLoadExecutiveReport(caso.id)}
          disabled={executiveReportLoading}
          className="case-card__action case-card__action--report"
        >
          {isLoadingReport ? 'Carregando relatório...' : 'Relatório Executivo'}
        </button>

        <button
          type="button"
          onClick={() => onOpenExecutivePdf(caso.id)}
          disabled={executivePdfLoading}
          className="case-card__action case-card__action--pdf"
        >
          {isLoadingPdf ? 'Abrindo PDF...' : 'PDF Executivo'}
        </button>
      </div>
    </article>
  )
}
