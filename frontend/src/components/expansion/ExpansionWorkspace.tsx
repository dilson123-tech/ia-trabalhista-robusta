import { useEffect, useState } from 'react'
import { AppealsModulePanel } from './AppealsModulePanel'
import { EditorModulePanel } from './EditorModulePanel'
import { ExpansionModulesNav, type ExpansionModule } from './ExpansionModulesNav'
import { SuccessionModulePanel } from './SuccessionModulePanel'

type ExpansionWorkspaceProps = {
  token: string
  selectedCaseId: number | null
  selectedCaseArea?: string | null
  forcedModule?: ExpansionModule
  pieceReadyRequestId?: number
}

export function ExpansionWorkspace({
  token,
  selectedCaseId,
  selectedCaseArea,
  forcedModule,
  pieceReadyRequestId,
}: ExpansionWorkspaceProps) {
  const [activeModule, setActiveModule] = useState<ExpansionModule>('editor')

  useEffect(() => {
    if (!forcedModule) return
    setActiveModule(forcedModule)
  }, [forcedModule])

  return (
    <>
      <section className="section-card expansion-shell-card">
        <div className="section-head">
          <h2 className="section-heading">Expansão da plataforma</h2>
          <p className="section-description">
            O bloco trabalhista atual continua operacional. Esta área inaugura a camada nova da plataforma sem reabrir o que já está validado.
          </p>
        </div>

        <div className="expansion-shell-card__meta">
          <span className="insight-badge">UX em camadas</span>
          <span className="insight-badge">Base #70 a #75 preservada</span>
          <span className="insight-badge">
            {selectedCaseId ? `Caso em contexto: #${selectedCaseId}` : 'Selecione um caso para aprofundar'}
          </span>
        </div>

        <p className="body-text expansion-shell-card__text">
          Estratégia ativa: expansão forte por dentro, experiência simples por fora.
        </p>
      </section>

      <ExpansionModulesNav
        activeModule={activeModule}
        onChange={setActiveModule}
      />

      {activeModule === 'editor' ? (
        <EditorModulePanel
          token={token}
          selectedCaseId={selectedCaseId}
          selectedCaseArea={selectedCaseArea}
          pieceReadyRequestId={pieceReadyRequestId}
        />
      ) : null}
      {activeModule === 'succession' ? <SuccessionModulePanel selectedCaseId={selectedCaseId} /> : null}
      {activeModule === 'appeals' ? <AppealsModulePanel selectedCaseId={selectedCaseId} /> : null}
    </>
  )
}
