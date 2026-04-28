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
      <section
        className="hero-panel"
        style={{
          gap: '14px',
          alignItems: 'stretch',
          marginBottom: '14px',
        }}
      >
        <div
          className="hero-card"
          style={{
            padding: '22px 20px',
            minHeight: 'unset',
          }}
        >
          <p className="hero-kicker">Plataforma jurídica estratégica multiárea</p>
          <h1
            className="hero-heading"
            style={{
              fontSize: '2.05rem',
              lineHeight: 1.05,
              marginBottom: '10px',
            }}
          >
            Painel do Advogado
          </h1>
          <p
            className="hero-description"
            style={{
              maxWidth: '58ch',
              fontSize: '0.98rem',
              lineHeight: 1.55,
              marginBottom: '14px',
            }}
          >
            Centralize análise jurídica, leitura de risco, resumos executivos e relatórios estratégicos
            em um ambiente com visão clara para decisão, operação e apresentação ao cliente.
          </p>

          <div className="hero-actions" style={{ gap: '10px' }}>
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

        <aside
          className="technical-card technical-card--connected"
          style={{
            padding: '18px 18px 16px',
            minHeight: 'unset',
          }}
        >
          <div className="technical-topbar" style={{ marginBottom: '10px' }}>
            <div>
              <h2
                className="technical-title"
                style={{
                  fontSize: '1.08rem',
                  marginBottom: '4px',
                }}
              >
                Sessão ativa
              </h2>
              <p
                className="technical-description"
                style={{
                  fontSize: '0.92rem',
                  lineHeight: 1.45,
                  marginBottom: 0,
                }}
              >
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

      <section
        className="metrics-grid metrics-grid--hero"
        style={{
          gap: '10px',
          marginTop: '2px',
          marginBottom: '12px',
        }}
      >
        {[
          ['Casos carregados', String(casesCount), 'metric-card metric-card--highlight', 'metric-value metric-value--gold'],
          ['Backend', 'Online', 'metric-card', 'metric-value'],
          ['Modo', loaded ? 'Real' : 'Demo', 'metric-card', 'metric-value'],
          ['Sessão', token.trim() ? 'Ativa' : 'Pendente', 'metric-card', 'metric-value'],
        ].map(([label, value, cardClass, valueClass]) => (
          <article
            key={label}
            className={cardClass}
            style={{
              padding: '14px 16px',
              minHeight: 'unset',
              borderRadius: '16px',
            }}
          >
            <p className="metric-label" style={{ marginBottom: '6px', fontSize: '0.72rem' }}>{label}</p>
            <h2 className={valueClass} style={{ fontSize: '1.02rem', margin: 0 }}>{value}</h2>
          </article>
        ))}
      </section>
    </>
  )
}
