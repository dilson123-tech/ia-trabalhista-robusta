import type { CaseContactLogItem, CaseItem, CasePartyItem, CasePartyStateDetailItem } from '../services/api'

type WhatsAppTemplateKey = 'documents' | 'evidence' | 'hearing' | 'status_update' | 'confirm_data'

type CaseCardProps = {
  caso: CaseItem
  selectedCaseId: number | null
  getStatusLabel: (status: string) => string
  isArchiving: boolean
  isAnalyzing: boolean
  isLoadingSummary: boolean
  isLoadingReport: boolean
  isLoadingPdf: boolean
  isLoadingContactLogs: boolean
  isLoadingWitnessGrid: boolean
  contactLogs: CaseContactLogItem[]
  partyState: CasePartyStateDetailItem | null
  analysisLoading: boolean
  executiveSummaryLoading: boolean
  executiveReportLoading: boolean
  executivePdfLoading: boolean
  onArchive: (caseId: number) => void
  onAnalyze: (caseId: number) => void
  onLoadExecutiveSummary: (caseId: number) => void
  onLoadExecutiveReport: (caseId: number) => void
  onOpenExecutivePdf: (caseId: number) => void
  onLoadCaseContactLogs: (caseId: number) => void
  onLoadWitnessGrid: (caseId: number) => void
  onAddWitness: (caso: CaseItem) => void
  onOpenWhatsAppTemplate: (caseId: number, whatsapp: string, templateKey: WhatsAppTemplateKey) => void
  onRegisterWhatsAppContact: (caseId: number) => void
  onSelectCase: (caseId: number) => void
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
  isLoadingContactLogs,
  isLoadingWitnessGrid,
  contactLogs,
  partyState,
  analysisLoading,
  executiveSummaryLoading,
  executiveReportLoading,
  executivePdfLoading,
  onArchive,
  onAnalyze,
  onLoadExecutiveSummary,
  onLoadExecutiveReport,
  onOpenExecutivePdf,
  onLoadCaseContactLogs,
  onLoadWitnessGrid,
  onAddWitness,
  onOpenWhatsAppTemplate,
  onRegisterWhatsAppContact,
  onSelectCase,
}: CaseCardProps) {
  const isSelected = selectedCaseId === caso.id
  const isArchived = caso.status === 'archived'

  function formatContactLogDate(value: string) {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value

    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date)
  }

  function getPartyMetadataText(party: CasePartyItem, key: string) {
    const value = party.party_metadata?.[key]

    if (typeof value === 'string') return value
    if (typeof value === 'number' || typeof value === 'boolean') return String(value)
    if (Array.isArray(value)) {
      return value
        .filter((item) => typeof item === 'string')
        .join(', ')
    }

    return ''
  }

  const witnessParties = (partyState?.parties ?? []).filter((party) => {
    const role = party.role.toLowerCase()
    return (
      role.includes('testemunha') ||
      role.includes('depoente') ||
      role.includes('preposto') ||
      role.includes('representante') ||
      role.includes('perito') ||
      role.includes('fiscal') ||
      role.includes('cuidador') ||
      role.includes('vizinho')
    )
  })

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

      {(caso.client_name || caso.client_whatsapp) ? (
        <div
          style={{
            marginBottom: '12px',
            padding: '12px',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
          }}
        >
          {caso.client_name ? (
            <p style={{ margin: '0 0 6px 0' }}>
              <strong>Cliente:</strong> {caso.client_name}
            </p>
          ) : null}

          {caso.client_whatsapp ? (
            <p style={{ margin: '0 0 6px 0' }}>
              <strong>WhatsApp:</strong> {caso.client_whatsapp}
            </p>
          ) : null}

          {caso.client_whatsapp_consent ? (
            <p
              style={{
                margin: 0,
                fontSize: '0.9rem',
                opacity: 0.85,
              }}
            >
              ✓ Cliente autorizou contato por WhatsApp
            </p>
          ) : null}
        </div>
      ) : null}

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
        {!isArchived ? (
          <>
            <button
              type="button"
              onClick={() => onArchive(caso.id)}
              disabled={isArchiving}
              className="case-card__action case-card__action--archive"
            >
              {isArchiving ? 'Arquivando...' : 'Arquivar'}
            </button>

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

            {caso.client_whatsapp ? (
              <>
                <a
                  href={`https://wa.me/${caso.client_whatsapp}?text=${encodeURIComponent(
                    'Olá, estamos entrando em contato sobre seu caso.'
                  )}`}
                  target="_blank"
                  rel="noreferrer"
                  className="case-card__action case-card__action--analysis"
                  style={{
                    textDecoration: 'none',
                    textAlign: 'center',
                  }}
                >
                  Abrir WhatsApp
                </a>

                <button
                  type="button"
                  onClick={() => onRegisterWhatsAppContact(caso.id)}
                  className="case-card__action case-card__action--summary"
                >
                  Registrar contato
                </button>

                <div
                  style={{
                    display: 'grid',
                    gap: '8px',
                    marginTop: '8px',
                    width: '100%',
                  }}
                >
                  <p
                    style={{
                      fontSize: '0.86rem',
                      margin: '0',
                      opacity: 0.82,
                      width: '100%',
                    }}
                  >
                    Mensagens prontas:
                  </p>

                  <button
                    type="button"
                    onClick={() => onOpenWhatsAppTemplate(caso.id, caso.client_whatsapp || '', 'documents')}
                    className="case-card__action case-card__action--summary"
                  >
                    Pedir documentos
                  </button>

                  <button
                    type="button"
                    onClick={() => onOpenWhatsAppTemplate(caso.id, caso.client_whatsapp || '', 'evidence')}
                    className="case-card__action case-card__action--summary"
                  >
                    Pedir provas
                  </button>

                  <button
                    type="button"
                    onClick={() => onOpenWhatsAppTemplate(caso.id, caso.client_whatsapp || '', 'hearing')}
                    className="case-card__action case-card__action--summary"
                  >
                    Lembrar audiência
                  </button>

                  <button
                    type="button"
                    onClick={() => onOpenWhatsAppTemplate(caso.id, caso.client_whatsapp || '', 'status_update')}
                    className="case-card__action case-card__action--summary"
                  >
                    Avisar andamento
                  </button>

                  <button
                    type="button"
                    onClick={() => onOpenWhatsAppTemplate(caso.id, caso.client_whatsapp || '', 'confirm_data')}
                    className="case-card__action case-card__action--summary"
                  >
                    Confirmar dados
                  </button>
                </div>
              </>
            ) : null}
          </>
        ) : (
          <button
            type="button"
            onClick={() => onSelectCase(caso.id)}
            className="case-card__action case-card__action--analysis"
          >
            Abrir caso
          </button>
        )}
      </div>

      <div
        style={{
          marginTop: '12px',
          padding: '12px',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '10px',
        }}
      >
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            gap: '10px',
            justifyContent: 'space-between',
            marginBottom: '8px',
          }}
        >
          <strong>Testemunhas/depoentes</strong>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={() => onLoadWitnessGrid(caso.id)}
              className="case-card__action case-card__action--summary"
              style={{ padding: '6px 10px' }}
            >
              {isLoadingWitnessGrid ? 'Carregando...' : 'Atualizar'}
            </button>

            <button
              type="button"
              onClick={() => onAddWitness(caso)}
              className="case-card__action case-card__action--analysis"
              style={{ padding: '6px 10px' }}
            >
              Adicionar V1
            </button>
          </div>
        </div>

        {partyState ? (
          witnessParties.length > 0 ? (
            <div style={{ display: 'grid', gap: '8px' }}>
              {witnessParties.slice(0, 6).map((party) => {
                const preparationStatus = getPartyMetadataText(party, 'preparation_status') || party.status
                const whatKnows = getPartyMetadataText(party, 'what_knows')
                const confirmsFacts = getPartyMetadataText(party, 'confirms_facts')
                const riskLevel = getPartyMetadataText(party, 'risk_level')
                const sensitivePoints = getPartyMetadataText(party, 'sensitive_points')

                return (
                  <div
                    key={party.id}
                    style={{
                      borderTop: '1px solid rgba(255,255,255,0.08)',
                      paddingTop: '8px',
                    }}
                  >
                    <p style={{ margin: '0 0 4px 0' }}>
                      <strong>{party.name}</strong> — {party.role} / {preparationStatus}
                    </p>

                    {whatKnows ? (
                      <p style={{ margin: '0 0 4px 0', opacity: 0.88 }}>
                        <strong>O que sabe:</strong> {whatKnows}
                      </p>
                    ) : null}

                    {confirmsFacts ? (
                      <p style={{ margin: '0 0 4px 0', opacity: 0.88 }}>
                        <strong>Confirma:</strong> {confirmsFacts}
                      </p>
                    ) : null}

                    {riskLevel ? (
                      <p style={{ margin: '0 0 4px 0', opacity: 0.82 }}>
                        <strong>Risco:</strong> {riskLevel}
                      </p>
                    ) : null}

                    {sensitivePoints ? (
                      <p style={{ margin: 0, opacity: 0.82 }}>
                        <strong>Pontos sensíveis:</strong> {sensitivePoints}
                      </p>
                    ) : null}
                  </div>
                )
              })}
            </div>
          ) : (
            <p style={{ margin: 0, opacity: 0.82 }}>
              Grade carregada, mas ainda sem testemunhas/depoentes cadastrados.
            </p>
          )
        ) : (
          <p style={{ margin: 0, opacity: 0.82 }}>
            Clique em Atualizar para carregar a grade ou em Adicionar V1 para cadastrar a primeira pessoa.
          </p>
        )}
      </div>

      {(contactLogs.length > 0 || caso.client_whatsapp) ? (
        <div
          style={{
            marginTop: '12px',
            padding: '12px',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
          }}
        >
          <div
            style={{
              alignItems: 'center',
              display: 'flex',
              gap: '10px',
              justifyContent: 'space-between',
              marginBottom: '8px',
            }}
          >
            <strong>Histórico de contatos</strong>

            <button
              type="button"
              onClick={() => onLoadCaseContactLogs(caso.id)}
              className="case-card__action case-card__action--summary"
              style={{ padding: '6px 10px' }}
            >
              {isLoadingContactLogs ? 'Carregando...' : 'Atualizar'}
            </button>
          </div>

          {contactLogs.length > 0 ? (
            <div style={{ display: 'grid', gap: '8px' }}>
              {contactLogs.slice(0, 5).map((log) => (
                <div
                  key={log.id}
                  style={{
                    borderTop: '1px solid rgba(255,255,255,0.08)',
                    paddingTop: '8px',
                  }}
                >
                  <p style={{ margin: '0 0 4px 0' }}>
                    <strong>{formatContactLogDate(log.occurred_at)}</strong> — {log.contact_type} / {log.direction}
                  </p>
                  <p style={{ margin: '0 0 4px 0' }}>{log.summary}</p>
                  {log.note ? (
                    <p style={{ margin: 0, opacity: 0.82 }}>{log.note}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ margin: 0, opacity: 0.82 }}>
              Nenhum contato registrado carregado ainda.
            </p>
          )}
        </div>
      ) : null}
    </article>
  )
}
