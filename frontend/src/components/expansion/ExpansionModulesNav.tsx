export type ExpansionModule = 'editor' | 'succession' | 'appeals'

type ExpansionModulesNavProps = {
  activeModule: ExpansionModule
  onChange: (module: ExpansionModule) => void
}

const modules: Array<{
  id: ExpansionModule
  label: string
  description: string
  stage: string
}> = [
  {
    id: 'editor',
    label: 'Editor Jurídico Vivo',
    description: 'Estrutura, blocos, versões e aprovação da peça com leitura organizada.',
    stage: 'Frontend shell',
  },
  {
    id: 'succession',
    label: 'Partes e Sucessão',
    description: 'Partes, representantes, sucessores, espólio e eventos com histórico preservado.',
    stage: 'Frontend shell',
  },
  {
    id: 'appeals',
    label: 'Decisão e Recurso',
    description: 'Decisão desfavorável, prazo, estratégia e minuta recursal por contexto.',
    stage: 'Frontend shell',
  },
]

export function ExpansionModulesNav({
  activeModule,
  onChange,
}: ExpansionModulesNavProps) {
  return (
    <section className="section-card">
      <div className="section-head">
        <h2 className="section-heading">Módulos de expansão</h2>
        <p className="section-description">
          A expansão entra por contexto. O advogado continua no fluxo principal e abre o módulo certo quando precisar.
        </p>
      </div>

      <div className="expansion-nav-grid">
        {modules.map((module) => {
          const isActive = activeModule === module.id

          return (
            <button
              key={module.id}
              type="button"
              className={`expansion-nav-card ${isActive ? 'expansion-nav-card--active' : ''}`}
              onClick={() => onChange(module.id)}
            >
              <div className="expansion-nav-card__top">
                <span className="expansion-nav-card__badge">{module.stage}</span>
                {isActive ? <span className="expansion-nav-card__status">Ativo</span> : null}
              </div>

              <h3 className="expansion-nav-card__title">{module.label}</h3>
              <p className="expansion-nav-card__description">{module.description}</p>
            </button>
          )
        })}
      </div>
    </section>
  )
}
