type NewCaseFormState = {
  case_number: string
  title: string
  description: string
  legal_area: string
  action_type: string
  status: string
}

type DashboardTopPanelProps = {
  showNewCaseForm: boolean
  onToggleNewCaseForm: () => void
  onLoadCases: () => void
  loading: boolean
  token: string
  onClearSessionAndGoToLogin: () => void
  error: string
  newCaseForm: NewCaseFormState
  onNewCaseFieldChange: (
    field: 'case_number' | 'title' | 'description' | 'legal_area' | 'action_type' | 'status',
    value: string,
  ) => void
  newCaseLoading: boolean
  onCreateNewCase: () => void
  onCancelNewCase: () => void
  newCaseError: string
  newCaseSuccess: string
  casesCount: number
  loaded: boolean
}

export function DashboardTopPanel({
  showNewCaseForm,
  onToggleNewCaseForm,
  onLoadCases,
  loading,
  token,
  onClearSessionAndGoToLogin,
  error,
  newCaseForm,
  onNewCaseFieldChange,
  newCaseLoading,
  onCreateNewCase,
  onCancelNewCase,
  newCaseError,
  newCaseSuccess,
  casesCount,
  loaded,
}: DashboardTopPanelProps) {
  return (
    <>
      <section className="hero-panel">
        <div className="hero-card">
          <p className="hero-kicker">Plataforma jurídica estratégica multiárea</p>
          <h1 className="hero-heading">Painel do Advogado</h1>
          <p className="hero-description">
            Centralize análise jurídica, leitura de risco, resumos executivos e relatórios estratégicos
            em um ambiente com visão clara para decisão, operação e apresentação ao cliente.
          </p>

          <div className="hero-actions">
            <button
              className={`btn ${showNewCaseForm ? 'btn-secondary' : 'btn-primary'}`}
              type="button"
              onClick={onToggleNewCaseForm}
            >
              {showNewCaseForm ? 'Ocultar formulário' : '+ Novo Caso'}
            </button>

            <button
              className="btn btn-ghost"
              type="button"
              onClick={onLoadCases}
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

            <span className="connection-badge connection-badge--ok">API conectada</span>
          </div>

          <div className="actions-row">
            <button
              className="btn btn-ghost"
              type="button"
              onClick={onClearSessionAndGoToLogin}
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
              Cadastre um novo caso com número do processo ou referência interna para alimentar a esteira analítica e executiva.
            </p>
          </div>

          <div className="form-grid">
            <input
              className="form-control"
              value={newCaseForm.case_number}
              onChange={(e) => onNewCaseFieldChange('case_number', e.target.value)}
              placeholder="Número do processo / referência do caso"
            />

            <input
              className="form-control"
              value={newCaseForm.title}
              onChange={(e) => onNewCaseFieldChange('title', e.target.value)}
              placeholder="Título do caso"
            />

            <textarea
              className="form-control form-control--textarea"
              value={newCaseForm.description}
              onChange={(e) => onNewCaseFieldChange('description', e.target.value)}
              placeholder="Descrição do caso"
            />

            <select
              className="form-control"
              value={newCaseForm.legal_area}
              onChange={(e) => onNewCaseFieldChange('legal_area', e.target.value)}
            >
              <option value="trabalhista">Trabalhista</option>
              <option value="civel">Cível</option>
              <option value="civil_ambiental">Civil/Ambiental</option>
              <option value="criminal">Criminal</option>
              <option value="consumidor">Consumidor</option>
              <option value="familia">Família</option>
              <option value="previdenciario">Previdenciário</option>
              <option value="empresarial">Empresarial</option>
              <option value="tributario">Tributário</option>
              <option value="administrativo">Administrativo</option>
              <option value="imobiliario">Imobiliário</option>
              <option value="outro">Outro</option>
            </select>

            <input
              className="form-control"
              value={newCaseForm.action_type}
              onChange={(e) => onNewCaseFieldChange('action_type', e.target.value)}
              placeholder="Tipo de ação (opcional)"
            />

            <select
              className="form-control"
              value={newCaseForm.status}
              onChange={(e) => onNewCaseFieldChange('status', e.target.value)}
            >
              <option value="draft">Rascunho</option>
              <option value="active">Ativo</option>
              <option value="review">Em revisão</option>
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
                onClick={onCreateNewCase}
                disabled={
                  newCaseLoading ||
                  !token.trim() ||
                  !newCaseForm.case_number.trim() ||
                  !newCaseForm.title.trim()
                }
              >
                {newCaseLoading ? 'Criando caso...' : 'Cadastrar caso'}
              </button>

              <button
                className="btn btn-secondary"
                type="button"
                onClick={onCancelNewCase}
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
          ['Casos carregados', String(casesCount), 'metric-card metric-card--highlight', 'metric-value metric-value--gold'],
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
    </>
  )
}
