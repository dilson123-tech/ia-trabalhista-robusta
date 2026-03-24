type AppealsModulePanelProps = {
  selectedCaseId: number | null
}

export function AppealsModulePanel({ selectedCaseId }: AppealsModulePanelProps) {
  return (
    <section className="insight-card">
      <div className="insight-head">
        <div>
          <p className="insight-kicker">Decisão, estratégia e recurso</p>
          <h2 className="insight-title">Reação pós-decisão</h2>
          <p className="insight-description">
            Casca inicial para leitura da decisão, prazo, estratégia recursal e futura minuta vinculada ao caso.
          </p>
        </div>
        <span className="insight-badge">Shell frontend</span>
      </div>

      <div className="content-stack">
        <article className="info-card">
          <p className="info-text">
            <strong>Caso selecionado:</strong>{' '}
            {selectedCaseId ? `#${selectedCaseId}` : 'nenhum caso selecionado'}
          </p>
          <p className="body-text">
            Próximo encaixe visual: decisão resumida, pontos perdidos, prazo, estratégia e gatilho para peça recursal.
          </p>
        </article>

        <article className="info-card">
          <strong className="info-list-title">Escopo desta fase</strong>
          <ul className="info-list">
            <li>separar leitura da decisão do fluxo principal</li>
            <li>preparar painel recursal com UX em camadas</li>
            <li>abrir caminho para integração futura com editor</li>
          </ul>
        </article>
      </div>
    </section>
  )
}
