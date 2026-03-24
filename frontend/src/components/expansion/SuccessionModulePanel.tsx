type SuccessionModulePanelProps = {
  selectedCaseId: number | null
}

export function SuccessionModulePanel({ selectedCaseId }: SuccessionModulePanelProps) {
  return (
    <section className="insight-card">
      <div className="insight-head">
        <div>
          <p className="insight-kicker">Partes, representantes e sucessão</p>
          <h2 className="insight-title">Mapa de vínculos processuais</h2>
          <p className="insight-description">
            Base visual inicial para estados de partes, representantes, sucessores, espólio e eventos sem bagunçar a UX.
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
            Próximo encaixe visual: snapshot atual, histórico preservado e eventos relevantes de sucessão processual.
          </p>
        </article>

        <article className="info-card">
          <strong className="info-list-title">Escopo desta fase</strong>
          <ul className="info-list">
            <li>organizar a leitura de partes por contexto</li>
            <li>mostrar histórico sem substituição destrutiva</li>
            <li>preparar integração futura com peças e editor</li>
          </ul>
        </article>
      </div>
    </section>
  )
}
