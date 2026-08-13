import { useEffect, useRef, useState } from 'react'
import type { CaseContactLogItem, CaseItem, CasePartyItem, CasePartyStateDetailItem } from '../services/api'
import { CaseTimelinePanel } from './CaseTimelinePanel'

type WhatsAppTemplateKey = 'documents' | 'evidence' | 'hearing' | 'status_update' | 'confirm_data'

type WitnessFormInput = {
  name: string
  role: string
  whatKnows: string
}

type WitnessContactInput = {
  whatsapp: string
  consent: boolean
  note?: string
}

type WitnessContactActionKey = 'open_whatsapp' | 'evidence' | 'confirm_data' | 'reminder'

type AssistantDestinationRequest = {
  destination: string
  requestId: number
}

type CaseContactUpdateInput = {
  client_name?: string
  client_whatsapp?: string
  client_whatsapp_consent?: boolean
}

export type CaseReadinessSnapshot = {
  score: number
  statusLabel: string
  statusTone: 'critical' | 'preparing' | 'almost' | 'ready'
  contactLogCount: number
  witnessCount: number
  attachmentCount: number
  checklistTotal: number
  checklistOpen: number
  checklistValidated: number
  missingItems: string[]
  loadedAt: string
}

export type CaseInternalDossierSnapshot = {
  caseId: number
  caseTitle: string
  caseNumber: string
  clientName: string
  clientWhatsapp: string
  readinessScore: number
  readinessStatus: string
  contactLogCount: number
  witnessCount: number
  attachmentCount: number
  checklistTotal: number
  checklistOpen: number
  checklistValidated: number
  lastContactSummary: string | null
  keyPeople: string[]
  evidenceSummary: string[]
  openChecklistItems: string[]
  nextSteps: string[]
  loadedAt: string
}

type CaseCardProps = {
  caso: CaseItem
  token: string
  selectedCaseId: number | null
  assistantDestinationRequest?: AssistantDestinationRequest | null
  showAdvancedTools?: boolean
  getStatusLabel: (status: string) => string
  isArchiving: boolean
  isAnalyzing: boolean
  isLoadingSummary: boolean
  isLoadingReport: boolean
  isLoadingPdf: boolean
  isLoadingContactLogs: boolean
  isLoadingReadiness: boolean
  isLoadingDossier: boolean
  isLoadingWitnessGrid: boolean
  contactLogs: CaseContactLogItem[]
  partyState: CasePartyStateDetailItem | null
  readiness: CaseReadinessSnapshot | null
  dossier: CaseInternalDossierSnapshot | null
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
  onAddWitness: (caso: CaseItem, witnessInput: WitnessFormInput) => void
  onUpdateWitness: (caso: CaseItem, party: CasePartyItem, witnessInput: WitnessFormInput) => void
  onSaveWitnessContact: (caso: CaseItem, party: CasePartyItem, input: WitnessContactInput) => void
  onRegisterWitnessContactAction: (caso: CaseItem, party: CasePartyItem, actionKey: WitnessContactActionKey) => void
  onClearWitnesses: (caso: CaseItem) => void
  onLoadReadiness: (caso: CaseItem) => void
  onLoadDossier: (caso: CaseItem) => void
  onOpenWhatsAppTemplate: (caseId: number, whatsapp: string, templateKey: WhatsAppTemplateKey) => void
  onRegisterWhatsAppContact: (caseId: number) => void
  onDeleteCaseContactLog: (caseId: number, logId: number) => void
  onUpdateCaseContact: (caso: CaseItem, payload: CaseContactUpdateInput) => void
  onSelectCase: (caseId: number) => void
}

export function CaseCard({
  caso,
  token,
  selectedCaseId,
  assistantDestinationRequest,
  showAdvancedTools = false,
  getStatusLabel,
  isArchiving,
  isAnalyzing,
  isLoadingSummary,
  isLoadingReport,
  isLoadingPdf,
  isLoadingReadiness,
  isLoadingDossier,
  isLoadingWitnessGrid,
  contactLogs,
  partyState,
  readiness,
  dossier,
  analysisLoading,
  executiveSummaryLoading,
  executiveReportLoading,
  executivePdfLoading,
  onArchive,
  onAnalyze,
  onLoadExecutiveSummary,
  onLoadExecutiveReport,
  onOpenExecutivePdf,
  onLoadWitnessGrid,
  onAddWitness,
  onUpdateWitness,
  onSaveWitnessContact,
  onRegisterWitnessContactAction,
    onClearWitnesses,
  onLoadReadiness,
  onLoadDossier,
  onOpenWhatsAppTemplate,
  onRegisterWhatsAppContact,
  onSelectCase,
}: CaseCardProps) {
  const isSelected = selectedCaseId === caso.id
  const isArchived = caso.status === 'archived'
  const [isWitnessFormOpen, setIsWitnessFormOpen] = useState(false)
  const [witnessName, setWitnessName] = useState('')
  const [witnessRole, setWitnessRole] = useState('')
  const [witnessWhatKnows, setWitnessWhatKnows] = useState('')
  const [editingWitnessPartyKey, setEditingWitnessPartyKey] = useState<string | null>(null)
  const [witnessFormError, setWitnessFormError] = useState('')
  const [openWitnessContactPartyKey, setOpenWitnessContactPartyKey] = useState<string | null>(null)
  const [witnessContactWhatsapp, setWitnessContactWhatsapp] = useState('')
  const [witnessContactConsent, setWitnessContactConsent] = useState(false)
  const [witnessContactNote, setWitnessContactNote] = useState('')
  const [witnessContactError, setWitnessContactError] = useState('')
  const [witnessFormSubmitting, setWitnessFormSubmitting] = useState(false)
  const dossierSectionRef = useRef<HTMLDivElement | null>(null)
  const timelineSectionRef = useRef<HTMLDivElement | null>(null)
  const witnessSectionRef = useRef<HTMLDivElement | null>(null)
  const witnessNameInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!assistantDestinationRequest || !isSelected) return

    const scrollToRef = (ref: { current: HTMLElement | null }) => {
      window.setTimeout(() => {
        ref.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      }, 120)
    }

    if (assistantDestinationRequest.destination === 'testemunhas') {
      handleOpenWitnessForm()
      scrollToRef(witnessSectionRef)
      window.setTimeout(() => {
        witnessNameInputRef.current?.focus()
      }, 300)
      return
    }

    if (assistantDestinationRequest.destination === 'linha_do_tempo') {
      scrollToRef(timelineSectionRef)
      return
    }

    if (assistantDestinationRequest.destination === 'dossie') {
      scrollToRef(dossierSectionRef)
    }
  }, [assistantDestinationRequest?.requestId])

  function normalizeWitnessDuplicateKey(value: string) {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim()
  }

  function resetWitnessForm() {
    setWitnessName('')
    setWitnessRole('')
    setWitnessWhatKnows('')
    setEditingWitnessPartyKey(null)
    setWitnessFormError('')
  }

  function handleOpenWitnessForm() {
    resetWitnessForm()
    setIsWitnessFormOpen(true)
    setWitnessFormError('')
  }

  function handleOpenWitnessEditForm(party: CasePartyItem) {
    setEditingWitnessPartyKey(party.party_key)
    setWitnessName(party.name)
    setWitnessRole(party.role)
    setWitnessWhatKnows(
      getPartyMetadataText(party, 'what_knows') || getPartyMetadataText(party, 'confirms_facts'),
    )
    setWitnessFormError('')
    setIsWitnessFormOpen(true)
  }

  function handleOpenWitnessContactPanel(party: CasePartyItem) {
    const isOpening = openWitnessContactPartyKey !== party.party_key

    if (isOpening) {
      setWitnessContactWhatsapp(getPartyMetadataText(party, 'witness_contact_whatsapp'))
      setWitnessContactConsent(Boolean(party.party_metadata?.witness_contact_consent))
      setWitnessContactNote(getPartyMetadataText(party, 'witness_contact_note'))
      setWitnessContactError('')
      setOpenWitnessContactPartyKey(party.party_key)
      return
    }

    setOpenWitnessContactPartyKey(null)
    setWitnessContactError('')
  }

  async function handleSubmitWitnessContact(party: CasePartyItem) {
    const whatsappDigits = witnessContactWhatsapp.replace(/\D/g, '')

    if (witnessContactConsent && !whatsappDigits) {
      setWitnessContactError('Informe o WhatsApp antes de marcar autorização para esta testemunha/depoente.')
      return
    }

    setWitnessContactError('')
    await onSaveWitnessContact(caso, party, {
      whatsapp: witnessContactWhatsapp,
      consent: witnessContactConsent,
      note: witnessContactNote,
    })
  }

  async function handleWitnessContactAction(party: CasePartyItem, actionKey: WitnessContactActionKey) {
    setWitnessContactError('')
    await onRegisterWitnessContactAction(caso, party, actionKey)
  }

  async function handleSubmitWitnessForm() {
    if (witnessFormSubmitting || isLoadingWitnessGrid) return

    const name = witnessName.trim()
    const role = witnessRole.trim()
    const whatKnows = witnessWhatKnows.trim()

    if (!name || !role || !whatKnows) {
      setWitnessFormError('Preencha nome, papel e o que a pessoa sabe/confirma antes de salvar.')
      return
    }

    const normalizedName = normalizeWitnessDuplicateKey(name)
    const normalizedRole = normalizeWitnessDuplicateKey(role)
    const duplicateWitness = witnessParties.some((party) => {
      if (editingWitnessPartyKey && party.party_key === editingWitnessPartyKey) {
        return false
      }

      return (
        normalizeWitnessDuplicateKey(party.name) === normalizedName &&
        normalizeWitnessDuplicateKey(party.role) === normalizedRole
      )
    })

    if (duplicateWitness) {
      setWitnessFormError('Essa testemunha/depoente já está cadastrada com o mesmo papel neste caso.')
      return
    }

    setWitnessFormSubmitting(true)
    setWitnessFormError('')

    try {
      const editingWitness = editingWitnessPartyKey
        ? witnessParties.find((party) => party.party_key === editingWitnessPartyKey)
        : null

      if (editingWitnessPartyKey && !editingWitness) {
        setWitnessFormError('Não foi possível localizar a testemunha/depoente para edição.')
        return
      }

      if (editingWitness) {
        await onUpdateWitness(caso, editingWitness, { name, role, whatKnows })
      } else {
        await onAddWitness(caso, { name, role, whatKnows })
      }

      resetWitnessForm()
      setIsWitnessFormOpen(false)
    } finally {
      setWitnessFormSubmitting(false)
    }
  }


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
          <strong>Registro interno:</strong> #{caso.id}
        </span>

        <span className="case-card__meta-pill">
          <strong>Tenant:</strong> {caso.tenant_id}
        </span>

        {isSelected ? (
          <span className="case-card__focus-badge">Caso em foco</span>
        ) : null}
      </div>

      {showAdvancedTools ? (
          <>
        <div
        style={{
          marginTop: '12px',
          padding: '12px',
          border: '1px solid rgba(111, 214, 178, 0.22)',
          borderRadius: '10px',
          background: 'rgba(111, 214, 178, 0.06)',
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
          <strong>Prontidão do caso</strong>

          <button
            type="button"
            onClick={() => onLoadReadiness(caso)}
            className="case-card__action case-card__action--summary"
            style={{ padding: '6px 10px' }}
          >
            {isLoadingReadiness ? 'Calculando...' : 'Atualizar prontidão'}
          </button>
        </div>

        {readiness ? (
          <>
            <p style={{ margin: '0 0 8px 0' }}>
              <strong>{readiness.score}%</strong> — {readiness.statusLabel}
            </p>

            <div className="case-card__meta" style={{ marginBottom: '8px' }}>
              <span className="case-card__meta-pill">Contatos: {readiness.contactLogCount}</span>
              <span className="case-card__meta-pill">Testemunhas: {readiness.witnessCount}</span>
              <span className="case-card__meta-pill">Checklist: {readiness.checklistValidated}/{readiness.checklistTotal}</span>
              <span className="case-card__meta-pill">Pendências: {readiness.checklistOpen}</span>
              <span className="case-card__meta-pill">Anexos: {readiness.attachmentCount}</span>
            </div>

            {readiness.missingItems.length > 0 ? (
              <ul style={{ margin: '0 0 8px 18px', opacity: 0.86 }}>
                {readiness.missingItems.slice(0, 4).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: '0 0 8px 0', opacity: 0.86 }}>
                Caso sem pendências operacionais principais na régua V1.
              </p>
            )}

            <p style={{ margin: 0, fontSize: '0.86rem', opacity: 0.78 }}>
              “Pronto” significa pronto para revisão humana do advogado, não protocolo automático.
            </p>
          </>
        ) : (
          <p style={{ margin: 0, opacity: 0.82 }}>
            Clique em Atualizar prontidão para consolidar cliente, contatos, testemunhas, checklist e anexos.
          </p>
        )}
      </div>

      <div
        id={`case-card-${caso.id}-dossie`}
        ref={dossierSectionRef}
        style={{
          scrollMarginTop: '18px',
          marginTop: '12px',
          padding: '12px',
          border: '1px solid rgba(96, 165, 250, 0.22)',
          borderRadius: '10px',
          background: 'rgba(96, 165, 250, 0.06)',
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
          <strong>Dossiê interno do caso</strong>

          <button
            type="button"
            onClick={() => onLoadDossier(caso)}
            className="case-card__action case-card__action--summary"
            style={{ padding: '6px 10px' }}
          >
            {isLoadingDossier ? 'Montando...' : 'Atualizar dossiê'}
          </button>
        </div>

        {dossier ? (
          <>
            <p style={{ margin: '0 0 8px 0' }}>
              <strong>{dossier.caseNumber}</strong> — {dossier.readinessScore}% / {dossier.readinessStatus}
            </p>

            <div className="case-card__meta" style={{ marginBottom: '8px' }}>
              <span className="case-card__meta-pill">Contatos: {dossier.contactLogCount}</span>
              <span className="case-card__meta-pill">Pessoas: {dossier.witnessCount}</span>
              <span className="case-card__meta-pill">Checklist: {dossier.checklistValidated}/{dossier.checklistTotal}</span>
              <span className="case-card__meta-pill">Anexos: {dossier.attachmentCount}</span>
            </div>

            <p style={{ margin: '0 0 6px 0', opacity: 0.86 }}>
              <strong>Cliente:</strong> {dossier.clientName} • {dossier.clientWhatsapp}
            </p>

            {dossier.lastContactSummary ? (
              <p style={{ margin: '0 0 8px 0', opacity: 0.86 }}>
                <strong>Último contato:</strong> {dossier.lastContactSummary}
              </p>
            ) : null}

            {dossier.keyPeople.length > 0 ? (
              <p style={{ margin: '0 0 8px 0', opacity: 0.86 }}>
                <strong>Pessoas-chave:</strong> {dossier.keyPeople.join('; ')}
              </p>
            ) : null}

            {dossier.evidenceSummary.length > 0 ? (
              <p style={{ margin: '0 0 8px 0', opacity: 0.86 }}>
                <strong>Provas/anexos:</strong> {dossier.evidenceSummary.join('; ')}
              </p>
            ) : null}

            {dossier.openChecklistItems.length > 0 ? (
              <p style={{ margin: '0 0 8px 0', opacity: 0.86 }}>
                <strong>Pendências abertas:</strong> {dossier.openChecklistItems.join('; ')}
              </p>
            ) : null}

            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '8px' }}>
              <strong style={{ display: 'block', marginBottom: '4px' }}>Próximos passos operacionais</strong>
              <ul style={{ margin: '0 0 0 18px', opacity: 0.86 }}>
                {dossier.nextSteps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <p style={{ margin: '8px 0 0 0', fontSize: '0.86rem', opacity: 0.78 }}>
              Dossiê interno é apoio operacional supervisionado, não peça processual e não protocolo automático.
            </p>
          </>
        ) : (
          <p style={{ margin: 0, opacity: 0.82 }}>
            Clique em Atualizar dossiê para consolidar cliente, contatos, provas, pendências, pessoas e prontidão.
          </p>
        )}
      </div>
      <div
        id={`case-card-${caso.id}-linha_do_tempo`}
        ref={timelineSectionRef}
        style={{ scrollMarginTop: '18px' }}
      >
        <CaseTimelinePanel token={token} caseId={caso.id} />
      </div>
                </>
        ) : null}

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

            {showAdvancedTools ? (
                <>
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

                            </>
              ) : null}

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
        id={`case-card-${caso.id}-testemunhas`}
        ref={witnessSectionRef}
        style={{
          scrollMarginTop: '18px',
          marginTop: '12px',
          padding: '12px',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '10px',
          maxHeight: '620px',
          overflowY: 'auto',
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
              onClick={handleOpenWitnessForm}
              className="case-card__action case-card__action--analysis"
              style={{ padding: '6px 10px' }}
            >
              Adicionar V1
            </button>

              {witnessParties.length > 0 ? (
                <button
                  type="button"
                  onClick={() => onClearWitnesses(caso)}
                  className="case-card__action case-card__action--summary"
                  style={{ padding: '6px 10px' }}
                >
                  Limpar testemunhas
                </button>
              ) : null}
          </div>
        </div>

          {isWitnessFormOpen ? (
            <div
              style={{
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '10px',
                display: 'grid',
                gap: '8px',
                marginBottom: '10px',
                padding: '10px',
              }}
            >
              <strong>Adicionar testemunha/depoente</strong>

              <label style={{ display: 'grid', gap: '4px' }}>
                <span>Nome</span>
                <input
                  ref={witnessNameInputRef}
                  value={witnessName}
                  onChange={(event) => setWitnessName(event.target.value)}
                  placeholder="Ex.: Edson Estevão"
                />
              </label>

              <label style={{ display: 'grid', gap: '4px' }}>
                <span>Papel</span>
                <input
                  value={witnessRole}
                  onChange={(event) => setWitnessRole(event.target.value)}
                  placeholder="Ex.: testemunha / condutor"
                />
              </label>

              <label style={{ display: 'grid', gap: '4px' }}>
                <span>O que sabe ou confirma</span>
                <textarea
                  value={witnessWhatKnows}
                  onChange={(event) => setWitnessWhatKnows(event.target.value)}
                  placeholder="Descreva o que essa pessoa pode esclarecer no caso."
                  rows={4}
                />
              </label>

              {witnessFormError ? (
                <p style={{ margin: 0, color: '#fca5a5' }}>{witnessFormError}</p>
              ) : null}

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                <button
                  type="button"
                  disabled={witnessFormSubmitting || isLoadingWitnessGrid}
                  onClick={() => {
                    void handleSubmitWitnessForm()
                  }}
                  className="case-card__action case-card__action--analysis"
                  style={{ padding: '6px 10px' }}
                >
                  {witnessFormSubmitting || isLoadingWitnessGrid ? 'Salvando...' : editingWitnessPartyKey ? 'Salvar edição' : 'Salvar testemunha'}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    resetWitnessForm()
                    setIsWitnessFormOpen(false)
                  }}
                  className="case-card__action case-card__action--summary"
                  style={{ padding: '6px 10px' }}
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : null}

        {partyState ? (
          witnessParties.length > 0 ? (
            <div style={{ display: 'grid', gap: '8px' }}>
              {witnessParties.slice(0, 6).map((party) => {
                const preparationStatus = getPartyMetadataText(party, 'preparation_status') || party.status
                const whatKnows = getPartyMetadataText(party, 'what_knows')
                const confirmsFacts = getPartyMetadataText(party, 'confirms_facts')
                const normalizedWhatKnows = whatKnows.trim().toLowerCase()
                const normalizedConfirmsFacts = confirmsFacts.trim().toLowerCase()
                const hasDuplicatedKnowledge =
                  normalizedWhatKnows.length > 0 && normalizedWhatKnows === normalizedConfirmsFacts
                const riskLevel = getPartyMetadataText(party, 'risk_level')
                const sensitivePoints = getPartyMetadataText(party, 'sensitive_points')
                const savedWitnessContactWhatsapp = getPartyMetadataText(party, 'witness_contact_whatsapp')
                const savedWitnessContactConsent = Boolean(party.party_metadata?.witness_contact_consent)
                const witnessContactHistory = Array.isArray(party.party_metadata?.witness_contact_history)
                  ? (party.party_metadata.witness_contact_history as Array<Record<string, unknown>>)
                  : []
                const isWitnessContactPanelOpen = openWitnessContactPartyKey === party.party_key

                return (
                  <div
                    key={party.id}
                    style={{
                      borderTop: '1px solid rgba(255,255,255,0.08)',
                      paddingTop: '8px',
                    }}
                  >
                    <div
                      style={{
                        alignItems: 'center',
                        display: 'flex',
                        gap: '8px',
                        justifyContent: 'space-between',
                        marginBottom: '4px',
                      }}
                    >
                      <p style={{ margin: 0 }}>
                        <strong>{party.name}</strong> — {party.role} / {preparationStatus}
                      </p>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          disabled={witnessFormSubmitting|| isLoadingWitnessGrid}
                          onClick={() => handleOpenWitnessEditForm(party)}
                          className="case-card__action case-card__action--summary"
                          style={{ padding: '4px 8px' }}
                        >
                          Editar
                        </button>

                        <button
                          type="button"
                          disabled={witnessFormSubmitting || isLoadingWitnessGrid}
                          onClick={() => handleOpenWitnessContactPanel(party)}
                          className="case-card__action case-card__action--summary"
                          style={{ padding: '4px 8px' }}
                        >
                          {isWitnessContactPanelOpen ? 'Fechar contato' : 'Contato'}
                        </button>
                      </div>
                    </div>

                    {whatKnows ? (
                      <p style={{ margin: '0 0 4px 0', opacity: 0.88 }}>
                        <strong>{hasDuplicatedKnowledge ? 'O que sabe/confirma:' : 'O que sabe:'}</strong> {whatKnows}
                      </p>
                    ) : null}

                    {confirmsFacts && !hasDuplicatedKnowledge ? (
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

                    {savedWitnessContactWhatsapp ? (
                      <p style={{ margin: '6px 0 0 0', opacity: 0.82 }}>
                        <strong>Contato da testemunha:</strong> {savedWitnessContactWhatsapp}
                        {savedWitnessContactConsent ? ' — autorizado' : ' — autorização não confirmada'}
                      </p>
                    ) : null}

                    {isWitnessContactPanelOpen ? (
                      <div
                        style={{
                          border: '1px solid rgba(255,255,255,0.12)',
                          borderRadius: '10px',
                          display: 'grid',
                          gap: '8px',
                          marginTop: '8px',
                          padding: '10px',
                        }}
                      >
                        <strong>Janela de contato — {party.name}</strong>

                        <label style={{ display: 'grid', gap: '4px' }}>
                          <span>WhatsApp desta testemunha/depoente</span>
                          <input
                            value={witnessContactWhatsapp}
                            onChange={(event) => setWitnessContactWhatsapp(event.target.value)}
                            placeholder="Ex.: 5547999999999"
                          />
                        </label>

                        <label style={{ alignItems: 'center', display: 'flex', gap: '8px' }}>
                          <input
                            type="checkbox"
                            checked={witnessContactConsent}
                            onChange={(event) => setWitnessContactConsent(event.target.checked)}
                          />
                          <span>Autorizou contato por WhatsApp</span>
                        </label>

                        <label style={{ display: 'grid', gap: '4px' }}>
                          <span>Observação/lembrete desta pessoa</span>
                          <textarea
                            value={witnessContactNote}
                            onChange={(event) => setWitnessContactNote(event.target.value)}
                            placeholder="Ex.: ligar à tarde, pedir documento, confirmar endereço..."
                            rows={2}
                          />
                        </label>

                        {witnessContactError ? (
                          <p style={{ margin: 0, color: '#fca5a5' }}>{witnessContactError}</p>
                        ) : null}

                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          <button type="button" onClick={() => { void handleSubmitWitnessContact(party) }} className="case-card__action case-card__action--analysis" style={{ padding: '5px 9px' }}>
                            Salvar contato
                          </button>

                          <button type="button" onClick={() => { void handleWitnessContactAction(party, 'open_whatsapp') }} className="case-card__action case-card__action--summary" style={{ padding: '5px 9px' }}>
                            Abrir WhatsApp
                          </button>

                          <button type="button" onClick={() => { void handleWitnessContactAction(party, 'evidence') }} className="case-card__action case-card__action--summary" style={{ padding: '5px 9px' }}>
                            Pedir provas
                          </button>

                          <button type="button" onClick={() => { void handleWitnessContactAction(party, 'confirm_data') }} className="case-card__action case-card__action--summary" style={{ padding: '5px 9px' }}>
                            Confirmar dados
                          </button>

                          <button type="button" onClick={() => { void handleWitnessContactAction(party, 'reminder') }} className="case-card__action case-card__action--summary" style={{ padding: '5px 9px' }}>
                            Registrar lembrete
                          </button>
                        </div>

                        {witnessContactHistory.length > 0 ? (
                          <div style={{ display: 'grid', gap: '6px' }}>
                            <strong>Registros desta testemunha</strong>
                            {witnessContactHistory.slice(0, 4).map((item, index) => (
                              <p key={`${party.id}-witness-contact-${index}`} style={{ margin: 0, opacity: 0.78 }}>
                                {String(item.created_at || '')} — {String(item.summary || 'Contato registrado')}
                              </p>
                            ))}
                          </div>
                        ) : (
                          <p style={{ margin: 0, opacity: 0.68 }}>
                            Nenhum registro próprio desta testemunha/depoente ainda.
                          </p>
                        )}
                      </div>
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

        <div
          style={{
            marginTop: '12px',
            padding: '12px',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
            maxHeight: '420px',
            overflowY: 'auto',
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
            <strong>Histórico de contatos / WhatsApp</strong>


          </div>

          <div
            style={{
              borderTop: '1px solid rgba(255,255,255,0.08)',
              display: 'grid',
              gap: '8px',
              marginBottom: '10px',
              paddingTop: '8px',
            }}
          >
            <p style={{ margin: 0, opacity: 0.9 }}>
              <strong>WhatsApp principal:</strong>{' '}
              {caso.client_whatsapp ? caso.client_whatsapp : 'não informado'}
            </p>

            <p style={{ margin: 0, opacity: 0.78 }}>
              Histórico operacional de contatos, mensagens, lembretes e registros do caso.
            </p>

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
    </article>
  )
}
