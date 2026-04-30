import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ApiError,
  createEditableDocument,
  createEditableDocumentVersion,
  deleteEditableDocument,
  generateAssistedDraft,
  getEditableDocument,
  listEditableDocumentsForCase,
  type EditableDocumentDetail,
  type EditableDocumentItem,
} from '../../services/api'

const EDITOR_SUPPORTED_AREAS = [
  { value: 'trabalhista', label: 'Trabalhista' },
  { value: 'civil_ambiental', label: 'Civil/Ambiental' },
  { value: 'consumidor', label: 'Consumidor' },
  { value: 'previdenciario', label: 'Previdenciário' },
] as const

const EDITOR_SUPPORTED_AREA_VALUES = new Set(
  EDITOR_SUPPORTED_AREAS.map((item) => item.value),
)

const normalizeEditorArea = (area: string | null | undefined): string => {
  const normalized = (area || '').trim().toLowerCase()
  return EDITOR_SUPPORTED_AREA_VALUES.has(
    normalized as (typeof EDITOR_SUPPORTED_AREAS)[number]['value']
  )
    ? normalized
    : 'trabalhista'
}

const isEditorAreaSupported = (area: string | null | undefined): boolean => {
  const normalized = (area || '').trim().toLowerCase()
  return EDITOR_SUPPORTED_AREA_VALUES.has(
    normalized as (typeof EDITOR_SUPPORTED_AREAS)[number]['value']
  )
}

const getAreaLabel = (area: string | null | undefined): string => {
  const normalized = (area || '').trim().toLowerCase()
  const labels: Record<string, string> = {
    trabalhista: 'Trabalhista',
    civel: 'Cível',
    civil_ambiental: 'Civil/Ambiental',
    criminal: 'Criminal',
    consumidor: 'Consumidor',
    familia: 'Família',
    previdenciario: 'Previdenciário',
    empresarial: 'Empresarial',
    tributario: 'Tributário',
    administrativo: 'Administrativo',
    imobiliario: 'Imobiliário',
    outro: 'Outro',
  }
  return labels[normalized] || (area && area.trim() ? area : 'não informada')
}

const getSectionPlaceholder = (sectionKey: string | null | undefined): string => {
  switch (sectionKey) {
    case 'resumo_fatico':
      return 'Descreva os fatos relevantes, as partes envolvidas, datas, jornada, acontecimentos principais e o problema central do caso.'
    case 'fundamentacao':
      return 'Indique a base legal, artigos aplicáveis, teses, jurisprudência e o enquadramento jurídico dos fatos.'
    case 'pedidos':
      return 'Liste os requerimentos objetivos: condenações, reflexos, verbas, justiça gratuita, honorários e demais providências.'
    default:
      return 'Escreva o conteúdo deste bloco com objetividade, clareza e coerência jurídica.'
  }
}

const getSectionHelpText = (sectionKey: string | null | undefined): string => {
  switch (sectionKey) {
    case 'resumo_fatico':
      return 'Aqui entra a narrativa objetiva do caso: quem, quando, o que aconteceu e qual é o núcleo do problema.'
    case 'fundamentacao':
      return 'Aqui entra o raciocínio jurídico: por que os fatos narrados geram direito, com base legal e técnica.'
    case 'pedidos':
      return 'Aqui entra exatamente o que será requerido ao final da peça, de forma direta e organizada.'
    default:
      return 'Use este espaço para redigir o bloco com clareza, lógica e linguagem jurídica consistente.'
  }
}


const getSectionGuardrailStatus = (section: EditableSection): string => {
  const value = section.metadata?.guardrail_status
  return typeof value === 'string' ? value : ''
}

const getSectionMissingItems = (section: EditableSection): string[] => {
  const value = section.metadata?.missing_items
  if (!Array.isArray(value)) return []
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

const getSectionGuidanceTitle = (section: EditableSection): string => {
  const value = section.metadata?.guidance_title
  return typeof value === 'string' && value.trim() ? value : 'O que falta preencher'
}

type EditorModulePanelProps = {
  token: string
  selectedCaseId: number | null
  selectedCaseArea?: string | null
  pieceReadyRequestId?: number
}

type EditableDocumentVersion = EditableDocumentDetail['versions'][number]
type EditableSection = EditableDocumentVersion['sections'][number]

function getVersionOriginLabel(version: EditableDocumentVersion): string {
  const source =
    version.version_metadata && typeof version.version_metadata.source === 'string'
      ? version.version_metadata.source
      : ''

  if (source === 'frontend_inline_edit') return 'edição'
  if (source === 'frontend_expansion_approval') return 'aprovada'
  if (source === 'frontend_expansion_new_version') return 'nova versão'

  const sectionSources = new Set(version.sections.map((section) => section.source))
  const hasEditedSection = version.sections.some((section) => section.status === 'edited')

  if (hasEditedSection) return 'edição'
  if (sectionSources.has('assisted_draft') && sectionSources.has('manual')) return 'mista'
  if (sectionSources.has('assisted_draft')) return 'análise'
  if (sectionSources.has('manual')) return 'inicial'

  return 'rascunho'
}

function getVersionDisplayLabel(version: EditableDocumentVersion): string {
  const status = version.approved ? 'aprovada' : 'rascunho'
  return `V${version.version_number} — ${getVersionOriginLabel(version)} — ${status}`
}

type CompareRow = {
  key: string
  title: string
  changed: boolean
  changeType: string
  changeSummary: string
  baseStatus: string
  targetStatus: string
  baseSource: string
  targetSource: string
  baseContent: string
  targetContent: string
}

function normalizeText(value: string | undefined) {
  return (value ?? '').replace(/\s+/g, ' ').trim()
}

function getSectionIdentifier(section: EditableSection) {
  return section.key || section.title
}

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8099/api/v1').replace(/\/$/, '')

export function EditorModulePanel({ token, selectedCaseId, selectedCaseArea, pieceReadyRequestId }: EditorModulePanelProps) {
  const [documents, setDocuments] = useState<EditableDocumentItem[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<EditableDocumentDetail | null>(null)
  const [loadingList, setLoadingList] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState('')
  const [createSuccess, setCreateSuccess] = useState('')
  const [versionActionLoading, setVersionActionLoading] = useState<'new' | 'approve' | null>(null)
  const [versionError, setVersionError] = useState('')
  const [versionSuccess, setVersionSuccess] = useState('')
  const [exportLoading, setExportLoading] = useState<'html' | 'pdf' | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [assistedDraftLoading, setAssistedDraftLoading] = useState(false)
  const [compareBaseVersionNumber, setCompareBaseVersionNumber] = useState<number | null>(null)
  const [compareTargetVersionNumber, setCompareTargetVersionNumber] = useState<number | null>(null)
  const [editingSectionKey, setEditingSectionKey] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState('')
  const [editingError, setEditingError] = useState('')
  const [editingSuccess, setEditingSuccess] = useState('')
  const [saveEditLoading, setSaveEditLoading] = useState(false)
  const [newDocumentTitle, setNewDocumentTitle] = useState('')
  const [newDocumentType, setNewDocumentType] = useState('peticao_inicial')
  const [newDocumentArea, setNewDocumentArea] = useState(normalizeEditorArea(selectedCaseArea))
  const [guidedInputs, setGuidedInputs] = useState<Record<string, string>>({})
  const handledPieceReadyRequestRef = useRef(0)

  useEffect(() => {
    if (!showCreateForm) return
    setNewDocumentArea(normalizeEditorArea(selectedCaseArea))
  }, [selectedCaseArea, showCreateForm])


  function mapDetailToListItem(detail: EditableDocumentDetail): EditableDocumentItem {
    return {
      id: detail.id,
      tenant_id: detail.tenant_id,
      case_id: detail.case_id,
      created_by_user_id: detail.created_by_user_id,
      area: detail.area,
      document_type: detail.document_type,
      title: detail.title,
      status: detail.status,
      current_version_number: detail.current_version_number,
      document_metadata: detail.document_metadata,
      created_at: detail.created_at,
      updated_at: detail.updated_at,
    }
  }

  function upsertDocumentInList(detail: EditableDocumentDetail) {
    const mapped = mapDetailToListItem(detail)

    setDocuments((prev) => {
      const exists = prev.some((doc) => doc.id === mapped.id)

      if (!exists) {
        return [mapped, ...prev]
      }

      return prev.map((doc) => (doc.id === mapped.id ? mapped : doc))
    })
  }

  async function refreshDocumentDetail(documentId: number) {
    const detail = await getEditableDocument(token, documentId)
    setSelectedDocument(detail)
    upsertDocumentInList(detail)
    return detail
  }

  async function handleGenerateReadyPiece() {
    if (!token.trim() || !selectedCaseId) return

    setAssistedDraftLoading(true)
    setCreateError('')
    setCreateSuccess('')
    setVersionError('')
    setVersionSuccess('')
    setEditingError('')
    setEditingSuccess('')

    try {
      let documentId = selectedDocumentId ?? documents[0]?.id ?? null
      let createdDetail: EditableDocumentDetail | null = null

      if (!documentId) {
        createdDetail = await createEditableDocument(token, {
          case_id: selectedCaseId,
          area: normalizeEditorArea(selectedCaseArea),
          document_type: 'peticao_inicial',
          title: `Peça pronta — Caso #${selectedCaseId}`,
          notes: 'Documento base criado automaticamente pelo fluxo Gerar peça pronta.',
          metadata: {
            source: 'piece_ready_quick_flow',
          },
          sections: [
            {
              key: 'resumo_fatico',
              title: 'Resumo fático',
              content: '',
              source: 'manual',
            },
            {
              key: 'fundamentacao',
              title: 'Fundamentação jurídica',
              content: '',
              source: 'manual',
            },
            {
              key: 'pedidos',
              title: 'Pedidos',
              content: '',
              source: 'manual',
            },
          ],
        })

        documentId = createdDetail.id
        setSelectedDocumentId(createdDetail.id)
        setSelectedDocument(createdDetail)
        upsertDocumentInList(createdDetail)
        setCreateSuccess('Documento base criado para iniciar a peça pronta.')
      }

      const assistedDetail = await generateAssistedDraft(token, documentId)
      setSelectedDocument(assistedDetail)
      upsertDocumentInList(assistedDetail)
      setSelectedDocumentId(assistedDetail.id)
      setCompareBaseVersionNumber(null)
      setCompareTargetVersionNumber(null)
      setEditingSectionKey(null)
      setEditingContent('')
      setShowCreateForm(false)
      setVersionSuccess(
        `Peça pronta gerada com sucesso na versão ${assistedDetail.current_version_number}. Revise, aprove e exporte o PDF final.`,
      )
    } catch (err) {
      if (err instanceof ApiError) {
        setVersionError(err.message)
      } else {
        setVersionError('Não foi possível gerar a peça pronta para o caso selecionado.')
      }
    } finally {
      setAssistedDraftLoading(false)
    }
  }

  async function handleGenerateAssistedDraft() {
    if (!token.trim() || !selectedDocumentId) return

    setAssistedDraftLoading(true)
    setVersionError('')
    setVersionSuccess('')
    setEditingError('')
    setEditingSuccess('')

    try {
      const detail = await generateAssistedDraft(token, selectedDocumentId)
      setSelectedDocument(detail)
      upsertDocumentInList(detail)
      setCompareBaseVersionNumber(null)
      setCompareTargetVersionNumber(null)
      setEditingSectionKey(null)
      setEditingContent('')
      setVersionSuccess(`Peça pronta atualizada com sucesso na versão ${detail.current_version_number}.`)
    } catch (err) {
      if (err instanceof ApiError) {
        setVersionError(err.message)
      } else {
        setVersionError('Não foi possível gerar a peça pronta a partir da análise.')
      }
    } finally {
      setAssistedDraftLoading(false)
    }
  }

  async function handleDeleteDocument() {
    if (!token.trim() || !selectedDocumentId) return
    if (!selectedCaseId) return

    const confirmed = window.confirm(
      'Tem certeza que deseja excluir este documento editável e todas as versões vinculadas? Esta ação não pode ser desfeita.',
    )

    if (!confirmed) return

    const documentId = selectedDocumentId

    setDeleteLoading(true)
    setError('')
    setVersionError('')
    setVersionSuccess('')
    setEditingError('')
    setEditingSuccess('')

    try {
      await deleteEditableDocument(token, documentId)

      const updatedDocuments = await listEditableDocumentsForCase(token, selectedCaseId)

      setDocuments(updatedDocuments)
      setSelectedDocument(null)
      setEditingSectionKey(null)
      setEditingContent('')
      setCompareBaseVersionNumber(null)
      setCompareTargetVersionNumber(null)

      setSelectedDocumentId((current) => {
        if (current && current !== documentId && updatedDocuments.some((doc) => doc.id === current)) {
          return current
        }
        return updatedDocuments.length > 0 ? updatedDocuments[0].id : null
      })

      setVersionSuccess('Documento editável excluído com sucesso.')
    } catch (err) {
      if (err instanceof ApiError) {
        setVersionError(err.message)
      } else {
        setVersionError('Não foi possível excluir o documento editável.')
      }
    } finally {
      setDeleteLoading(false)
    }
  }

  useEffect(() => {
    if (!token.trim() || !selectedCaseId) {
      setDocuments([])
      setSelectedDocumentId(null)
      setSelectedDocument(null)
      setError('')
      setCreateError('')
      setCreateSuccess('')
      setVersionError('')
      setVersionSuccess('')
      setCompareBaseVersionNumber(null)
      setCompareTargetVersionNumber(null)
      setShowCreateForm(false)
      return
    }

    const caseId = selectedCaseId
    let isActive = true

    async function run() {
      setLoadingList(true)
      setError('')

      try {
        const data = await listEditableDocumentsForCase(token, caseId)
        if (!isActive) return

        setDocuments(data)

        if (data.length === 0) {
          setSelectedDocumentId(null)
          setSelectedDocument(null)
          return
        }

        setSelectedDocumentId((current) => {
          if (current && data.some((doc) => doc.id === current)) {
            return current
          }
          return data[0].id
        })
      } catch (err) {
        if (!isActive) return

        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Não foi possível carregar os documentos editáveis do caso.')
        }

        setDocuments([])
        setSelectedDocumentId(null)
        setSelectedDocument(null)
      } finally {
        if (isActive) {
          setLoadingList(false)
        }
      }
    }

    void run()

    return () => {
      isActive = false
    }
  }, [token, selectedCaseId])

  useEffect(() => {
    if (!token.trim() || !selectedDocumentId) {
      setSelectedDocument(null)
      return
    }

    const documentId = selectedDocumentId
    let isActive = true

    async function run() {
      setLoadingDetail(true)
      setError('')

      try {
        const data = await getEditableDocument(token, documentId)
        if (!isActive) return
        setSelectedDocument(data)
        upsertDocumentInList(data)
      } catch (err) {
        if (!isActive) return

        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Não foi possível carregar o detalhe do documento editável.')
        }

        setSelectedDocument(null)
      } finally {
        if (isActive) {
          setLoadingDetail(false)
        }
      }
    }

    void run()

    return () => {
      isActive = false
    }
  }, [token, selectedDocumentId])

  useEffect(() => {
    if (!pieceReadyRequestId) return
    if (handledPieceReadyRequestRef.current === pieceReadyRequestId) return
    if (!token.trim() || !selectedCaseId) return
    if (loadingList || loadingDetail || createLoading || assistedDraftLoading) return

    handledPieceReadyRequestRef.current = pieceReadyRequestId
    void handleGenerateReadyPiece()
  }, [
    pieceReadyRequestId,
    token,
    selectedCaseId,
    loadingList,
    loadingDetail,
    createLoading,
    assistedDraftLoading,
  ])

  const currentVersion = useMemo(() => {
    if (!selectedDocument || selectedDocument.versions.length === 0) return null
    return selectedDocument.versions[selectedDocument.versions.length - 1]
  }, [selectedDocument])

  const versionsTimeline = useMemo(() => {
    if (!selectedDocument) return []
    return [...selectedDocument.versions].sort((a, b) => b.version_number - a.version_number)
  }, [selectedDocument])

  useEffect(() => {
    if (versionsTimeline.length === 0) {
      setCompareBaseVersionNumber(null)
      setCompareTargetVersionNumber(null)
      return
    }

    setCompareTargetVersionNumber((current) => {
      if (current && versionsTimeline.some((version) => version.version_number === current)) {
        return current
      }
      return versionsTimeline[0].version_number
    })

    setCompareBaseVersionNumber((current) => {
      if (current && versionsTimeline.some((version) => version.version_number === current)) {
        return current
      }
      return (versionsTimeline[1] ?? versionsTimeline[0]).version_number
    })
  }, [versionsTimeline])

  const compareBaseVersion = useMemo(() => {
    if (compareBaseVersionNumber === null) return null
    return versionsTimeline.find((version) => version.version_number === compareBaseVersionNumber) ?? null
  }, [compareBaseVersionNumber, versionsTimeline])

  const compareTargetVersion = useMemo(() => {
    if (compareTargetVersionNumber === null) return null
    return versionsTimeline.find((version) => version.version_number === compareTargetVersionNumber) ?? null
  }, [compareTargetVersionNumber, versionsTimeline])

  const compareRows = useMemo<CompareRow[]>(() => {
    if (!compareBaseVersion || !compareTargetVersion) return []

    const identifiers = Array.from(
      new Set([
        ...compareBaseVersion.sections.map((section) => getSectionIdentifier(section)),
        ...compareTargetVersion.sections.map((section) => getSectionIdentifier(section)),
      ]),
    )

    return identifiers.map((identifier) => {
      const baseSection =
        compareBaseVersion.sections.find((section) => getSectionIdentifier(section) === identifier) ?? null
      const targetSection =
        compareTargetVersion.sections.find((section) => getSectionIdentifier(section) === identifier) ?? null

      const baseContent = baseSection?.content ?? ''
      const targetContent = targetSection?.content ?? ''
      const baseStatus = baseSection?.status ?? '—'
      const targetStatus = targetSection?.status ?? '—'
      const baseSource = baseSection?.source ?? '—'
      const targetSource = targetSection?.source ?? '—'

      const contentChanged = normalizeText(baseContent) !== normalizeText(targetContent)
      const statusChanged = normalizeText(baseStatus) !== normalizeText(targetStatus)
      const sourceChanged = normalizeText(baseSource) !== normalizeText(targetSource)
      const added = !baseSection && !!targetSection
      const removed = !!baseSection && !targetSection

      const changed = contentChanged || statusChanged || sourceChanged || added || removed

      const changeParts: string[] = []
      if (added) changeParts.push('Bloco adicionado')
      if (removed) changeParts.push('Bloco removido')
      if (contentChanged && !added && !removed) changeParts.push('Conteúdo alterado')
      if (statusChanged) changeParts.push('Status alterado')
      if (sourceChanged) changeParts.push('Fonte alterada')

      const changeType = changeParts[0] ?? 'Sem mudança'
      const changeSummary = changeParts.length > 0 ? changeParts.join(' • ') : 'Sem mudança detectada'

      return {
        key: identifier,
        title: targetSection?.title ?? baseSection?.title ?? identifier,
        changed,
        changeType,
        changeSummary,
        baseStatus,
        targetStatus,
        baseSource,
        targetSource,
        baseContent,
        targetContent,
      }
    })
  }, [compareBaseVersion, compareTargetVersion])

  const compareSummary = useMemo(() => {
    const changed = compareRows.filter((row) => row.changed).length
    return {
      total: compareRows.length,
      changed,
      unchanged: Math.max(compareRows.length - changed, 0),
    }
  }, [compareRows])

  const approvedVersion = useMemo(() => {
    if (!selectedDocument) return null
    return [...selectedDocument.versions]
      .filter((version) => version.approved)
      .sort((a, b) => b.version_number - a.version_number)[0] ?? null
  }, [selectedDocument])

  async function handleExportDocument(format: 'html' | 'pdf') {
    if (!selectedDocumentId || !approvedVersion || !token.trim()) return

    try {
      setExportLoading(format)
      setVersionError('')
      setVersionSuccess('')

      const response = await fetch(
        `${API_BASE_URL}/editable-documents/${selectedDocumentId}/export/${format}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      if (!response.ok) {
        throw new Error(`Falha ao exportar documento em ${format.toUpperCase()}.`)
      }

      const blob = await response.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      window.open(blobUrl, '_blank', 'noopener,noreferrer')
      window.setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60000)

      setVersionSuccess(`Exportação ${format.toUpperCase()} iniciada com sucesso.`)
    } catch (err) {
      setVersionError(err instanceof Error ? err.message : 'Não foi possível exportar o documento.')
    } finally {
      setExportLoading(null)
    }
  }

  async function handleCreateDocument() {
    if (!token.trim() || !selectedCaseId || !newDocumentTitle.trim()) return

    if (!isEditorAreaSupported(selectedCaseArea)) {
      setCreateError(
        `Novo documento editável ainda não disponível para a área ${getAreaLabel(selectedCaseArea)}.`
      )
      setCreateSuccess('')
      return
    }

    setCreateLoading(true)
    setCreateError('')
    setCreateSuccess('')
    setVersionError('')
    setVersionSuccess('')

    try {
      const created = await createEditableDocument(token, {
        case_id: selectedCaseId,
        area: newDocumentArea,
        document_type: newDocumentType,
        title: newDocumentTitle.trim(),
        notes: 'Documento iniciado pelo frontend da expansão.',
        metadata: {
          source: 'frontend_expansion_shell',
        },
        sections: [
          {
            key: 'resumo_fatico',
            title: 'Resumo Fático',
            content: '',
            source: 'manual',
            status: 'draft',
            metadata: {},
          },
          {
            key: 'fundamentacao',
            title: 'Fundamentação',
            content: '',
            source: 'manual',
            status: 'draft',
            metadata: {},
          },
          {
            key: 'pedidos',
            title: 'Pedidos',
            content: '',
            source: 'manual',
            status: 'draft',
            metadata: {},
          },
        ],
      })

      setDocuments((prev) => [mapDetailToListItem(created), ...prev])
      setSelectedDocumentId(created.id)
      setSelectedDocument(created)
      setShowCreateForm(false)
      setNewDocumentTitle('')
      setNewDocumentType('peticao_inicial')
      setNewDocumentArea(normalizeEditorArea(selectedCaseArea))
      setCreateSuccess(`Documento "${created.title}" criado com sucesso.`)
    } catch (err) {
      if (err instanceof ApiError) {
        setCreateError(err.message)
      } else {
        setCreateError('Não foi possível criar o documento editável.')
      }
    } finally {
      setCreateLoading(false)
    }
  }

  async function handleCreateVersion(approved: boolean) {
    if (!token.trim() || !selectedDocument || !currentVersion) return

    setVersionActionLoading(approved ? 'approve' : 'new')
    setVersionError('')
    setVersionSuccess('')
    setCreateError('')
    setCreateSuccess('')

    try {
      const createdVersion = await createEditableDocumentVersion(token, selectedDocument.id, {
        sections: currentVersion.sections.map((section) => ({
          key: section.key,
          title: section.title,
          content: section.content,
          source: section.source,
          status: section.status,
          metadata: section.metadata ?? {},
        })),
        notes: approved
          ? currentVersion.notes
            ? `${currentVersion.notes}\n\nSnapshot aprovado pelo frontend da expansão.`
            : 'Snapshot aprovado pelo frontend da expansão.'
          : currentVersion.notes
            ? `${currentVersion.notes}\n\nNova versão gerada pelo frontend da expansão.`
            : 'Nova versão gerada pelo frontend da expansão.',
        metadata: {
          ...(currentVersion.version_metadata ?? {}),
          source: approved ? 'frontend_expansion_approval' : 'frontend_expansion_new_version',
          based_on_version_number: currentVersion.version_number,
        },
        approved,
      })

      await refreshDocumentDetail(selectedDocument.id)

      setVersionSuccess(
        approved
          ? `Versão ${createdVersion.version_number} criada como aprovada com sucesso.`
          : `Nova versão ${createdVersion.version_number} criada com sucesso.`,
      )
    } catch (err) {
      if (err instanceof ApiError) {
        setVersionError(err.message)
      } else {
        setVersionError(
          approved
            ? 'Não foi possível aprovar a versão atual.'
            : 'Não foi possível criar uma nova versão.',
        )
      }
    } finally {
      setVersionActionLoading(null)
    }
  }


  function handleStartSectionEdit(section: EditableSection) {
    if (currentVersion?.approved) {
      setEditingSectionKey(null)
      setEditingContent('')
      setEditingError('Versões aprovadas não podem ser editadas diretamente. Crie uma nova versão para continuar.')
      setEditingSuccess('')
      return
    }

    setEditingSectionKey(getSectionIdentifier(section))
    setEditingContent(section.content ?? '')
    setEditingError('')
    setEditingSuccess('')
    setVersionError('')
    setVersionSuccess('')
  }

  function handleCancelSectionEdit() {
    setEditingSectionKey(null)
    setEditingContent('')
    setEditingError('')
    setEditingSuccess('')
  }

  function handleGuidedInputChange(sectionKey: string, value: string) {
    setGuidedInputs((prev) => ({
      ...prev,
      [sectionKey]: value,
    }))
  }

  function handleApplyGuidedFill(section: EditableSection) {
    const sectionKey = getSectionIdentifier(section)
    const missingItems = getSectionMissingItems(section)
    const draftedInput = (guidedInputs[sectionKey] || '').trim()
    const guidedTemplate = draftedInput
      ? draftedInput
      : missingItems.map((item) => `- ${item}: `).join('\n')

    const currentBase = (section.content || '').trim()
    const guidedBlock = guidedTemplate
      ? `[Complementos guiados do advogado]\n${guidedTemplate}`
      : ''

    setEditingSectionKey(sectionKey)
    setEditingContent([currentBase, guidedBlock].filter(Boolean).join('\n\n'))
    setEditingError('')
    setEditingSuccess('')
    setVersionError('')
    setVersionSuccess('')
  }

  async function handleSaveSectionEdit(section: EditableSection) {
    if (!token.trim() || !selectedDocument || !currentVersion) return

    const sectionKey = getSectionIdentifier(section)
    const normalizedOriginal = section.content ?? ''
    const normalizedEdited = editingContent
    const guidedComplementMatch = normalizedEdited.match(/\[Complementos guiados do advogado\]\n([\s\S]*)$/)
    const guidedComplement = guidedComplementMatch?.[1]?.trim() || ''
    const shouldPropagateResumo = sectionKey === 'resumo_fatico' && guidedComplement.length > 0

    if (sectionKey !== editingSectionKey) {
      setEditingError('O bloco em edição não confere com a seleção atual.')
      return
    }

    if (normalizedOriginal === normalizedEdited) {
      setEditingError('Nenhuma alteração detectada para salvar.')
      setEditingSuccess('')
      return
    }

    setSaveEditLoading(true)
    setEditingError('')
    setEditingSuccess('')
    setVersionError('')
    setVersionSuccess('')

    try {
      const createdVersion = await createEditableDocumentVersion(token, selectedDocument.id, {
        sections: currentVersion.sections.map((currentSection) => {
          const currentKey = getSectionIdentifier(currentSection)

          if (currentKey !== sectionKey) {
            const shouldEnrichFromResumo =
              shouldPropagateResumo &&
              (currentKey === 'fundamentacao' || currentKey === 'pedidos')

            if (!shouldEnrichFromResumo) {
              return {
                key: currentSection.key,
                title: currentSection.title,
                content: currentSection.content,
                source: currentSection.source,
                status: currentSection.status,
                metadata: currentSection.metadata ?? {},
              }
            }

            const propagationTitle =
              currentKey === 'fundamentacao'
                ? '[Insumos reaproveitados do Resumo Fático para apoiar a fundamentação]'
                : '[Insumos reaproveitados do Resumo Fático para apoiar os pedidos]'

            const baseContent = (currentSection.content || '').trim()
            const propagatedBlock = `${propagationTitle}\n${guidedComplement}`
            const propagatedContent = baseContent.includes(propagationTitle)
              ? baseContent
              : [baseContent, propagatedBlock].filter(Boolean).join('\n\n')

            return {
              key: currentSection.key,
              title: currentSection.title,
              content: propagatedContent,
              source: currentSection.source,
              status: currentSection.status,
              metadata: {
                ...(currentSection.metadata ?? {}),
                propagated_from_resumo_fatico: true,
                propagated_source_version_number: currentVersion.version_number,
              },
            }
          }

          return {
            key: currentSection.key,
            title: currentSection.title,
            content: normalizedEdited,
            source: 'manual',
            status: 'edited',
            metadata: {
              ...(currentSection.metadata ?? {}),
              edited_in_frontend: true,
                guardrail_status: 'manual_completed',
                missing_items: [],
                guidance_title: '',
                manual_completion_source: 'guided_editor'
            },
          }
        }),
        notes: `Edição manual do bloco "${section.title}" via frontend da expansão.`,
        metadata: {
          ...(currentVersion.version_metadata ?? {}),
          source: 'frontend_inline_edit',
          based_on_version_number: currentVersion.version_number,
          edited_section_key: sectionKey,
        },
        approved: false,
      })

      await refreshDocumentDetail(selectedDocument.id)

      setCompareBaseVersionNumber(currentVersion.version_number)
      setCompareTargetVersionNumber(createdVersion.version_number)

      setEditingSuccess(`Bloco "${section.title}" salvo na versão ${createdVersion.version_number}.`)
      setEditingSectionKey(null)
      setEditingContent('')
    } catch (err) {
      if (err instanceof ApiError) {
        setEditingError(err.message)
      } else {
        setEditingError('Não foi possível salvar a edição do bloco.')
      }
    } finally {
      setSaveEditLoading(false)
    }
  }

  if (!selectedCaseId) {
    return (
      <section className="insight-card">
        <div className="insight-head">
          <div>
            <p className="insight-kicker">Editor Jurídico Vivo</p>
            <h2 className="insight-title">Peça editável por blocos</h2>
            <p className="insight-description">
              Selecione um caso no fluxo principal para abrir a camada de edição estruturada.
            </p>
          </div>
          <span className="insight-badge">Aguardando caso</span>
        </div>

        <p className="insight-empty">
          A expansão continua leve: o editor só aprofunda quando existe um caso em contexto.
        </p>
      </section>
    )
  }

  return (
    <section className="insight-card">
      <div className="insight-head">
        <div>
          <p className="insight-kicker">Editor Jurídico Vivo</p>
          <h2 className="insight-title">Peça editável por blocos</h2>
          <p className="insight-description">
            Lista real de documentos editáveis do caso, com detalhe, versão atual, blocos estruturados e comparação visual.
          </p>
        </div>
        <span className="insight-badge">Caso em foco: #{selectedCaseId}</span>
      </div>

      <div className="actions-row" style={{ marginBottom: '16px' }}>                    <button
                      type="button"
                      className={`btn ${deleteLoading ? 'btn-muted' : 'btn-secondary'}`}
                      onClick={() => void handleDeleteDocument()}
                      disabled={deleteLoading}
                      title="Excluir documento editável e todas as versões vinculadas"
                    >
                      {deleteLoading ? 'Excluindo documento...' : 'Excluir documento'}
                    </button>


        <button
          type="button"
          className={`btn ${!isEditorAreaSupported(selectedCaseArea) ? 'btn-muted' : showCreateForm ? 'btn-secondary' : 'btn-primary'}`}
          onClick={() => {
            if (!isEditorAreaSupported(selectedCaseArea)) return
            setShowCreateForm((prev) => !prev)
            setCreateError('')
            setCreateSuccess('')
          }}
          disabled={!isEditorAreaSupported(selectedCaseArea)}
          title={
            isEditorAreaSupported(selectedCaseArea)
              ? 'Criar novo documento editável'
              : `Editor estruturado ainda não disponível para a área ${getAreaLabel(selectedCaseArea)}`
          }
        >
          {showCreateForm ? 'Ocultar criação' : 'Novo documento editável'}
        </button>
      </div>

      {!isEditorAreaSupported(selectedCaseArea) ? (
        <article className="info-card" style={{ marginBottom: '16px' }}>
          <p className="info-text">
            <strong>Área do caso:</strong> {getAreaLabel(selectedCaseArea)}
          </p>
          <p className="body-text">
            O editor jurídico estruturado ainda não está liberado para esta área neste painel.
            Áreas disponíveis hoje: {EDITOR_SUPPORTED_AREAS.map((item) => item.label).join(', ')}.
          </p>
        </article>
      ) : null}

      {showCreateForm ? (
        <article className="info-card" style={{ marginBottom: '16px' }}>
          <div className="form-grid">
            <input
              className="form-control"
              value={newDocumentTitle}
              onChange={(e) => setNewDocumentTitle(e.target.value)}
              placeholder="Título do documento"
            />

            <select
              className="form-control"
              value={newDocumentType}
              onChange={(e) => setNewDocumentType(e.target.value)}
            >
              <option value="peticao_inicial">Petição inicial</option>
              <option value="contestacao">Contestação</option>
              <option value="manifestacao">Manifestação</option>
              <option value="recurso_ordinario">Recurso ordinário</option>
            </select>

            <select
              className="form-control"
              value={newDocumentArea}
              onChange={(e) => setNewDocumentArea(e.target.value)}
            >
              {EDITOR_SUPPORTED_AREAS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>

            <div className="actions-row">
              <button
                type="button"
                className={`btn ${createLoading || !newDocumentTitle.trim() ? 'btn-muted' : 'btn-primary'}`}
                onClick={handleCreateDocument}
                disabled={createLoading || !newDocumentTitle.trim()}
              >
                {createLoading ? 'Criando documento...' : 'Criar documento'}
              </button>

              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setShowCreateForm(false)
                  setCreateError('')
                  setCreateSuccess('')
                }}
              >
                Cancelar
              </button>
            </div>
          </div>
        </article>
      ) : null}

      {error ? <p className="status-message status-message--error">{error}</p> : null}
      {createError ? <p className="status-message status-message--error">{createError}</p> : null}
      {createSuccess ? <p className="status-message status-message--success">{createSuccess}</p> : null}
      {versionError ? <p className="status-message status-message--error">{versionError}</p> : null}
      {versionSuccess ? <p className="status-message status-message--success">{versionSuccess}</p> : null}
      {editingError ? <p className="status-message status-message--error">{editingError}</p> : null}
      {editingSuccess ? <p className="status-message status-message--success">{editingSuccess}</p> : null}

      {loadingList ? <p className="insight-empty">Carregando documentos editáveis do caso...</p> : null}

      {!loadingList && documents.length === 0 ? (
        <article className="info-card">
          <p className="info-text">
            <strong>Estado atual:</strong> este caso ainda não possui documento editável persistido.
          </p>
          <p className="body-text">
            Use “Novo documento editável” para inaugurar a primeira peça estruturada deste caso.
          </p>
        </article>
      ) : null}

      {documents.length > 0 ? (
        <div className="content-stack">
          <article className="info-card">
            <p className="info-text">
              <strong>Documentos encontrados:</strong> {documents.length}
            </p>

            <div className="actions-row" style={{ marginTop: '12px' }}>
              {documents.map((document) => (
                <button
                  key={document.id}
                  type="button"
                  className={`btn ${selectedDocumentId === document.id ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => {
                    setSelectedDocumentId(document.id)
                    setVersionError('')
                    setVersionSuccess('')
                  }}
                >
                  {document.title}
                </button>
              ))}
            </div>
          </article>

          {loadingDetail ? <p className="insight-empty">Carregando detalhe do documento...</p> : null}

          {selectedDocument ? (
            <>
              <article className="info-card">
                <p className="info-meta">
                  Documento #{selectedDocument.id} • {selectedDocument.document_type} • área {selectedDocument.area}
                </p>

                <p className="info-text">
                  <strong>Título:</strong> {selectedDocument.title}
                </p>
                <p className="info-text">
                  <strong>Status:</strong> {selectedDocument.status}
                </p>
                <p className="info-text">
                  <strong>Versão atual:</strong> {selectedDocument.current_version_number}
                </p>
                <p className="info-text">
                  <strong>Versões registradas:</strong> {selectedDocument.versions.length}
                </p>

                <p
                  className="info-meta"
                  style={{
                    marginTop: '12px',
                    marginBottom: '12px',
                    padding: '10px 12px',
                    borderRadius: '12px',
                    background: approvedVersion ? 'rgba(16, 185, 129, 0.10)' : 'rgba(148, 163, 184, 0.12)',
                    border: approvedVersion
                      ? '1px solid rgba(16, 185, 129, 0.30)'
                      : '1px solid rgba(148, 163, 184, 0.24)',
                    color: approvedVersion ? '#d1fae5' : 'rgba(226, 232, 240, 0.88)',
                  }}
                >
                  {approvedVersion
                    ? `Versão aprovada v${approvedVersion.version_number} pronta para exportação final em HTML e PDF.`
                    : 'Exportação final liberada após aprovação formal de uma versão do documento.'}
                </p>

                <div className="actions-row" style={{ marginTop: '12px', flexWrap: 'wrap', gap: '10px' }}>
                    <button
                      type="button"
                      className={`btn ${
                        assistedDraftLoading || !selectedDocumentId || versionActionLoading || exportLoading !== null
                          ? 'btn-muted'
                          : 'btn-secondary'
                      }`}
                      onClick={() => void handleGenerateAssistedDraft()}
                      disabled={
                        assistedDraftLoading || !selectedDocumentId || Boolean(versionActionLoading) || exportLoading !== null
                      }
                      title="Gerar rascunho inicial dos blocos com base na análise, resumo executivo e decisão do caso"
                    >
                      {assistedDraftLoading ? 'Gerando peça pronta...' : 'Gerar peça pronta'}
                    </button>

                  <button
                    type="button"
                    className={`btn ${versionActionLoading || !currentVersion ? 'btn-muted' : 'btn-primary'}`}
                    onClick={() => void handleCreateVersion(false)}
                    disabled={Boolean(versionActionLoading) || !currentVersion}
                  >
                    {versionActionLoading === 'new' ? 'Criando versão...' : 'Nova versão'}
                  </button>

                  <button
                    type="button"
                    className={`btn ${
                      versionActionLoading || !currentVersion || currentVersion.approved
                        ? 'btn-muted'
                        : 'btn-secondary'
                    }`}
                    onClick={() => void handleCreateVersion(true)}
                    disabled={Boolean(versionActionLoading) || !currentVersion || currentVersion.approved}
                  >
                    {versionActionLoading === 'approve'
                      ? 'Aprovando versão...'
                      : currentVersion?.approved
                        ? 'Versão já aprovada'
                        : 'Aprovar versão atual'}
                  </button>

                  <button
                    type="button"
                    className={`btn ${
                      approvedVersion && exportLoading !== 'html' ? 'btn-ghost' : 'btn-muted'
                    }`}
                    onClick={() => void handleExportDocument('html')}
                    disabled={!approvedVersion || exportLoading !== null}
                    title={approvedVersion ? 'Exportar versão aprovada em HTML' : 'A exportação exige uma versão aprovada'}
                  >
                    {exportLoading === 'html' ? 'Exportando HTML...' : 'Exportar HTML'}
                  </button>

                  <button
                    type="button"
                    className={`btn ${
                      approvedVersion && exportLoading !== 'pdf' ? 'btn-ghost' : 'btn-muted'
                    }`}
                    onClick={() => void handleExportDocument('pdf')}
                    disabled={!approvedVersion || exportLoading !== null}
                    title={approvedVersion ? 'Exportar versão aprovada em PDF' : 'A exportação exige uma versão aprovada'}
                  >
                    {exportLoading === 'pdf' ? 'Exportando PDF...' : 'Exportar PDF'}
                  </button>
                </div>
              </article>

              <article className="info-card">
                <strong className="info-list-title">Versão atual</strong>
                {currentVersion ? (
                  <>
                    <p className="info-text" style={{ marginTop: '12px' }}>
                      <strong>Número:</strong> {currentVersion.version_number}
                    </p>
                    <p className="info-text">
                      <strong>Aprovada:</strong> {currentVersion.approved ? 'Sim' : 'Não'}
                    </p>
                    <p className="info-text">
                      <strong>Notas:</strong> {currentVersion.notes || 'Sem notas registradas.'}
                    </p>

                    <div style={{ marginTop: '12px' }}>
                      <strong className="info-list-title">Blocos da versão</strong>
                      {currentVersion.approved ? (
                        <p
                          className="info-meta"
                          style={{
                            marginTop: '8px',
                            marginBottom: '12px',
                            padding: '10px 12px',
                            borderRadius: '12px',
                            background: 'rgba(245, 158, 11, 0.10)',
                            border: '1px solid rgba(245, 158, 11, 0.25)',
                          }}
                        >
                          Esta versão está aprovada e bloqueada para edição direta. Crie uma nova versão para alterar qualquer bloco.
                        </p>
                      ) : null}
                        <ul className="info-list">
                          {currentVersion.sections.length > 0 ? (
                            currentVersion.sections.map((section, index) => {
                              const isEditing = editingSectionKey === getSectionIdentifier(section)
                                const guardrailStatus = getSectionGuardrailStatus(section)
                                const missingItems = getSectionMissingItems(section)
                                const guidanceTitle = getSectionGuidanceTitle(section)

                              return (
                                <li key={`${section.key}-${index}`}>
                                  <strong>{section.title}</strong> — {section.status || 'draft'} ({section.source || 'manual'})

                                  <div style={{ marginTop: '8px' }}>
                                    {!isEditing ? (
                                      <>
                                          {guardrailStatus === 'insufficient_data' || missingItems.length > 0 ? (
                                            <div
                                              style={{
                                                marginBottom: '12px',
                                                padding: '12px',
                                                borderRadius: '12px',
                                                background: 'rgba(245, 158, 11, 0.10)',
                                                border: '1px solid rgba(245, 158, 11, 0.28)',
                                              }}
                                            >
                                              <p className="info-meta" style={{ marginBottom: '8px', fontWeight: 700 }}>
                                                Atenção: dados insuficientes neste bloco.
                                              </p>
                                              <p className="info-meta" style={{ marginBottom: missingItems.length > 0 ? '8px' : 0 }}>
                                                {guidanceTitle}
                                              </p>
                                              {missingItems.length > 0 ? (
                                                <ul className="info-list" style={{ marginBottom: 0 }}>
                                                  {missingItems.map((item, missingIndex) => (
                                                    <li key={`${section.key}-missing-${missingIndex}`}>{item}</li>
                                                  ))}
                                                </ul>
                                              ) : null}

                                                {missingItems.length > 0 ? (
                                                  <>
                                                    <textarea
                                                      className="form-control"
                                                      value={guidedInputs[getSectionIdentifier(section)] || ''}
                                                      onChange={(e) =>
                                                        handleGuidedInputChange(getSectionIdentifier(section), e.target.value)
                                                      }
                                                      placeholder={missingItems.map((item) => `- ${item}:`).join('\n')}
                                                      rows={4}
                                                      style={{ width: '100%', marginBottom: '8px' }}
                                                    />
                                                    <div className="actions-row">
                                                      <button
                                                        type="button"
                                                        className={`btn ${currentVersion.approved ? 'btn-muted' : 'btn-primary'}`}
                                                        onClick={() => handleApplyGuidedFill(section)}
                                                        disabled={currentVersion.approved}
                                                      >
                                                        Levar respostas para edição
                                                      </button>
                                                    </div>
                                                  </>
                                                ) : null}
                                            </div>
                                          ) : null}

                                          <p className="body-text" style={{ whiteSpace: 'pre-wrap', marginBottom: '8px' }}>
                                            {section.content || 'Sem conteúdo registrado neste bloco.'}
                                          </p>

                                        <button
                                          type="button"
                                          className={`btn ${currentVersion.approved ? 'btn-muted' : 'btn-ghost'}`}
                                          onClick={() => handleStartSectionEdit(section)}
                                          disabled={currentVersion.approved}
                                          title={
                                            currentVersion.approved
                                              ? 'Versão aprovada: crie uma nova versão para editar este bloco.'
                                              : 'Editar bloco'
                                          }
                                        >
                                          {currentVersion.approved ? 'Versão aprovada' : 'Editar bloco'}
                                        </button>

                                      </>
                                    ) : (
                                      <>
                                        <textarea
                                          className="form-control"
                                          value={editingContent}
                                          onChange={(e) => setEditingContent(e.target.value)}
                                          placeholder={getSectionPlaceholder(editingSectionKey)}
                                          rows={8}
                                          style={{ width: '100%', marginBottom: '8px' }}
                                        />
                                        <p className="info-meta" style={{ marginBottom: '8px' }}>
                                          {getSectionHelpText(editingSectionKey)}
                                        </p>

                                        <div className="actions-row">
                                          <button
                                            type="button"
                                            className={`btn ${saveEditLoading ? 'btn-muted' : 'btn-primary'}`}
                                            onClick={() => void handleSaveSectionEdit(section)}
                                            disabled={saveEditLoading}
                                          >
                                            {saveEditLoading ? 'Salvando edição...' : 'Salvar edição'}
                                          </button>

                                          <button
                                            type="button"
                                            className="btn btn-ghost"
                                            onClick={handleCancelSectionEdit}
                                            disabled={saveEditLoading}
                                          >
                                            Cancelar
                                          </button>
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </li>
                              )
                            })
                          ) : (
                            <li>Nenhum bloco registrado nesta versão.</li>
                          )}
                        </ul>
                    </div>
                  </>
                ) : (
                  <p className="body-text" style={{ marginTop: '12px' }}>
                    Nenhuma versão encontrada para este documento.
                  </p>
                )}
              </article>

              <article className="info-card">
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '12px',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    marginBottom: '12px',
                  }}
                >
                  <strong className="info-list-title">Comparação entre versões</strong>
                  <span className="insight-badge">
                    {compareSummary.changed} bloco(s) alterado(s) de {compareSummary.total}
                  </span>
                </div>

                {versionsTimeline.length < 2 ? (
                  <p className="body-text">
                    Crie ao menos duas versões para liberar a comparação visual.
                  </p>
                ) : (
                  <>
                    {versionsTimeline.length === 2 && compareBaseVersion && compareTargetVersion ? (
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          gap: '12px',
                          flexWrap: 'wrap',
                          marginBottom: '16px',
                        }}
                      >
                        <p className="info-text" style={{ margin: 0 }}>
                          <strong>Comparando:</strong> {getVersionDisplayLabel(compareBaseVersion)} → {getVersionDisplayLabel(compareTargetVersion)}
                        </p>

                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => {
                            setCompareBaseVersionNumber(compareTargetVersion.version_number)
                            setCompareTargetVersionNumber(compareBaseVersion.version_number)
                          }}
                        >
                          Inverter
                        </button>
                      </div>
                    ) : (
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: '12px',
                          marginBottom: '16px',
                        }}
                      >
                        <label style={{ display: 'grid', gap: '8px' }}>
                          <span className="info-meta">De</span>
                          <select
                            className="form-control"
                            value={compareBaseVersionNumber ?? ''}
                            onChange={(e) => setCompareBaseVersionNumber(Number(e.target.value))}
                          >
                            {versionsTimeline.map((version) => (
                              <option key={`base-${version.id}`} value={version.version_number}>
                                {getVersionDisplayLabel(version)}
                              </option>
                            ))}
                          </select>
                        </label>

                        <label style={{ display: 'grid', gap: '8px' }}>
                          <span className="info-meta">Para</span>
                          <select
                            className="form-control"
                            value={compareTargetVersionNumber ?? ''}
                            onChange={(e) => setCompareTargetVersionNumber(Number(e.target.value))}
                          >
                            {versionsTimeline.map((version) => (
                              <option key={`target-${version.id}`} value={version.version_number}>
                                {getVersionDisplayLabel(version)}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    )}

                    {compareBaseVersion && compareTargetVersion ? (
                      <>
                        <p className="info-text">
                          <strong>Resumo:</strong> {compareSummary.changed} alteração(ões) detectada(s) •{' '}
                          {compareSummary.unchanged} bloco(s) sem mudança
                        </p>

                        <div
                          style={{
                            display: 'grid',
                            gap: '12px',
                            marginTop: '16px',
                          }}
                        >
                          {compareRows.filter((row) => row.changed).map((row) => (
                            <article
                              key={row.key}
                              style={{
                                border: row.changed ? '1px solid rgba(212, 175, 55, 0.45)' : '1px solid rgba(255,255,255,0.08)',
                                borderLeft: row.changed ? '4px solid rgba(212, 175, 55, 0.9)' : '4px solid rgba(255,255,255,0.06)',
                                boxShadow: row.changed ? '0 10px 30px rgba(212, 175, 55, 0.10)' : 'none',
                                borderRadius: '16px',
                                padding: '16px',
                                background: row.changed
                                  ? 'linear-gradient(180deg, rgba(212, 175, 55, 0.10), rgba(255,255,255,0.02))'
                                  : 'rgba(255,255,255,0.02)',
                              }}
                            >
                              <div
                                style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  gap: '12px',
                                  alignItems: 'center',
                                  flexWrap: 'wrap',
                                  marginBottom: '12px',
                                }}
                              >
                                <strong>{row.title}</strong>
                                <span className="insight-badge">{row.changed ? 'Alterado' : 'Sem mudança'}</span>
                              </div>


                              <div
                                  style={{
                                    borderRadius: '12px',
                                    padding: '12px',
                                    background: 'rgba(34, 197, 94, 0.10)',
                                    border: '1px solid rgba(34, 197, 94, 0.28)',
                                  }}
                                >
                                  <p className="info-meta" style={{ marginBottom: '8px' }}>
                                    Conteúdo atualizado
                                  </p>
                                  <div
                                    style={{
                                      maxHeight: '320px',
                                      overflowY: 'auto',
                                      paddingRight: '6px',
                                    }}
                                  >
                                    <p className="body-text" style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                                      {row.targetContent || 'Sem conteúdo registrado nesta versão.'}
                                    </p>
                                  </div>
                                </div>
</article>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="body-text">Selecione duas versões válidas para comparar.</p>
                    )}
                  </>
                )}
              </article>

              <article className="info-card">
                <strong className="info-list-title">Linha do tempo de versões</strong>

                <ul className="info-list" style={{ marginTop: '12px' }}>
                  {versionsTimeline.length > 0 ? (
                    versionsTimeline.map((version) => (
                      <li key={version.id}>
                        <strong>{getVersionDisplayLabel(version)}</strong>
                        {version.version_number === selectedDocument.current_version_number ? ' • atual' : ''}
                      </li>
                    ))
                  ) : (
                    <li>Nenhuma versão registrada até aqui.</li>
                  )}
                </ul>
              </article>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
