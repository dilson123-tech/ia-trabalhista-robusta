type CaseFiltersBarProps = {
  filteredCount: number
  totalCount: number
  caseSearchTerm: string
  onCaseSearchTermChange: (value: string) => void
  caseStatusFilter: string
  onCaseStatusFilterChange: (value: string) => void
  onResetFilters: () => void
  onCleanupDemo: () => void
  cleanupDemoLoading: boolean
  caseActionError: string
  caseActionSuccess: string
}

export function CaseFiltersBar({
  filteredCount,
  totalCount,
  caseSearchTerm,
  onCaseSearchTermChange,
  caseStatusFilter,
  onCaseStatusFilterChange,
  onResetFilters,
  onCleanupDemo,
  cleanupDemoLoading,
  caseActionError,
  caseActionSuccess,
}: CaseFiltersBarProps) {
  return (
    <div
      style={{
        display: 'grid',
        gap: '12px',
        marginBottom: '18px',
      }}
    >
      <div
        style={{
          display: 'grid',
          gap: '12px',
          padding: '14px',
          borderRadius: '16px',
          border: '1px solid rgba(212, 175, 55, 0.14)',
          background: 'linear-gradient(180deg, rgba(16,24,39,0.82) 0%, rgba(15,23,42,0.96) 100%)',
          boxShadow: '0 16px 36px rgba(0,0,0,0.18)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: '12px',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <p
              style={{
                margin: '0 0 4px',
                color: '#f3c969',
                fontSize: '12px',
                fontWeight: 800,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              Filtros da carteira
            </p>

            <p
              style={{
                margin: 0,
                color: '#9fb0cc',
                fontSize: '13px',
              }}
            >
              Exibindo {filteredCount} de {totalCount} caso(s) carregado(s).
            </p>
          </div>

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              borderRadius: '999px',
              padding: '7px 12px',
              background: 'rgba(27,39,64,0.95)',
              border: '1px solid rgba(212,175,55,0.18)',
              color: '#d7e1f0',
              fontSize: '12px',
              fontWeight: 700,
            }}
          >
            Base operacional ativa
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
            alignItems: 'center',
          }}
        >
          <input
            className="form-control"
            style={{
              maxWidth: '320px',
              background: '#0f1a2e',
              border: '1px solid #2a395a',
              color: '#e5edf8',
            }}
            value={caseSearchTerm}
            onChange={(e) => onCaseSearchTermChange(e.target.value)}
            placeholder="Buscar por número ou título"
          />

          <select
            className="form-control"
            style={{
              maxWidth: '220px',
              background: '#0f1a2e',
              border: '1px solid #2a395a',
              color: '#e5edf8',
            }}
            value={caseStatusFilter}
            onChange={(e) => onCaseStatusFilterChange(e.target.value)}
          >
            <option value="main">Carteira principal</option>
            <option value="all">Todos os status</option>
            <option value="draft">Rascunhos</option>
            <option value="active">Ativos</option>
            <option value="review">Em revisão</option>
            <option value="archived">Arquivados</option>
          </select>

          <button
            className="btn btn-ghost"
            type="button"
            style={{
              borderColor: '#32435f',
              color: '#d8e2f0',
              background: '#162033',
            }}
            onClick={onResetFilters}
          >
            Limpar filtros
          </button>

          <button
            className="btn btn-ghost"
            type="button"
            style={{
              borderColor: 'rgba(212,175,55,0.22)',
              color: cleanupDemoLoading ? '#9aa7bb' : '#f3c969',
              background: cleanupDemoLoading ? '#1a2332' : '#182235',
            }}
            onClick={onCleanupDemo}
            disabled={cleanupDemoLoading}
          >
            {cleanupDemoLoading ? 'Limpando demonstração...' : 'Limpar demonstração'}
          </button>
        </div>

        {caseActionError ? (
          <p
            className="status-message status-message--error"
            style={{
              margin: 0,
              borderRadius: '12px',
            }}
          >
            {caseActionError}
          </p>
        ) : null}

        {caseActionSuccess ? (
          <p
            className="status-message status-message--success"
            style={{
              margin: 0,
              borderRadius: '12px',
            }}
          >
            {caseActionSuccess}
          </p>
        ) : null}
      </div>
    </div>
  )
}
