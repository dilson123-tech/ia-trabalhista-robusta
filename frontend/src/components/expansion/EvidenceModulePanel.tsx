import { type ChangeEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  createCaseEvidenceChecklistItem,
  deleteCaseAttachment,
  deleteCaseEvidenceChecklistItem,
  downloadCaseAttachment,
  listCaseAttachments,
  listCaseEvidenceChecklist,
  updateCaseEvidenceChecklistItem,
  uploadCaseAttachment,
  type CaseAttachmentCategory,
  type CaseAttachmentItem,
  type CaseEvidenceChecklistCategory,
  type CaseEvidenceChecklistItem,
  type CaseEvidenceChecklistPriority,
  type CaseEvidenceChecklistStatus,
} from '../../services/api'

type EvidenceModulePanelProps = {
  token: string
  selectedCaseId: number | null
}

const categoryOptions: Array<{ value: CaseAttachmentCategory; label: string }> = [
  { value: 'foto', label: 'Foto' },
  { value: 'video', label: 'Vídeo' },
  { value: 'pdf', label: 'PDF' },
  { value: 'documento_medico', label: 'Documento médico' },
  { value: 'notificacao', label: 'Notificação' },
  { value: 'documento_pessoal', label: 'Documento pessoal' },
  { value: 'contrato', label: 'Contrato' },
  { value: 'testemunha', label: 'Testemunha' },
  { value: 'outro', label: 'Outro' },
]

const checklistCategoryOptions: Array<{ value: CaseEvidenceChecklistCategory; label: string }> = [
  { value: 'documento', label: 'Documento' },
  { value: 'prova_documental', label: 'Prova documental' },
  { value: 'prova_oral', label: 'Prova oral' },
  { value: 'prova_tecnica', label: 'Prova técnica' },
  { value: 'comprovante', label: 'Comprovante' },
  { value: 'contrato', label: 'Contrato' },
  { value: 'mensagem', label: 'Mensagem/print' },
  { value: 'foto_video', label: 'Foto/vídeo' },
  { value: 'documento_pessoal', label: 'Documento pessoal' },
  { value: 'outro', label: 'Outro' },
]

const checklistStatusOptions: Array<{ value: CaseEvidenceChecklistStatus; label: string }> = [
  { value: 'pending', label: 'Pendente' },
  { value: 'requested', label: 'Solicitado' },
  { value: 'received', label: 'Recebido' },
  { value: 'validated', label: 'Validado' },
  { value: 'waived', label: 'Dispensado' },
  { value: 'needs_review', label: 'Precisa revisar' },
]

const checklistPriorityOptions: Array<{ value: CaseEvidenceChecklistPriority; label: string }> = [
  { value: 'low', label: 'Baixa' },
  { value: 'normal', label: 'Normal' },
  { value: 'high', label: 'Alta' },
  { value: 'urgent', label: 'Urgente' },
]

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let unitIndex = 0

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }

  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

function getCategoryLabel(category: string) {
  return categoryOptions.find((option) => option.value === category)?.label ?? category
}

function getChecklistCategoryLabel(category: string) {
  return checklistCategoryOptions.find((option) => option.value === category)?.label ?? category
}

function getChecklistStatusLabel(status: string) {
  return checklistStatusOptions.find((option) => option.value === status)?.label ?? status
}

function getChecklistPriorityLabel(priority: string) {
  return checklistPriorityOptions.find((option) => option.value === priority)?.label ?? priority
}

function getFileKind(attachment: CaseAttachmentItem) {
  const mime = attachment.mime_type?.toLowerCase() ?? ''
  if (mime.includes('pdf') || attachment.original_filename.toLowerCase().endsWith('.pdf')) return 'PDF'
  if (mime.startsWith('image/')) return 'Imagem'
  if (mime.startsWith('video/')) return 'Vídeo'
  return 'Arquivo'
}

export function EvidenceModulePanel({ token, selectedCaseId }: EvidenceModulePanelProps) {
  const [attachments, setAttachments] = useState<CaseAttachmentItem[]>([])
  const [checklistItems, setChecklistItems] = useState<CaseEvidenceChecklistItem[]>([])
  const [loading, setLoading] = useState(false)
  const [checklistLoading, setChecklistLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [checklistSaving, setChecklistSaving] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [checklistActionId, setChecklistActionId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [category, setCategory] = useState<CaseAttachmentCategory>('pdf')
  const [description, setDescription] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [checklistTitle, setChecklistTitle] = useState('')
  const [checklistCategory, setChecklistCategory] = useState<CaseEvidenceChecklistCategory>('documento')
  const [checklistPriority, setChecklistPriority] = useState<CaseEvidenceChecklistPriority>('normal')
  const [checklistRequestedFrom, setChecklistRequestedFrom] = useState('')
  const [checklistDueDate, setChecklistDueDate] = useState('')
  const [checklistNotes, setChecklistNotes] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const totalSize = useMemo(
    () => attachments.reduce((sum, attachment) => sum + (attachment.file_size_bytes || 0), 0),
    [attachments],
  )

  const pendingChecklistCount = useMemo(
    () => checklistItems.filter((item) => ['pending', 'requested', 'needs_review'].includes(item.status)).length,
    [checklistItems],
  )

  const validatedChecklistCount = useMemo(
    () => checklistItems.filter((item) => item.status === 'validated').length,
    [checklistItems],
  )

  async function loadAttachments() {
    if (!token.trim() || !selectedCaseId) {
      setAttachments([])
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await listCaseAttachments(token, selectedCaseId)
      setAttachments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível carregar as provas/anexos.')
    } finally {
      setLoading(false)
    }
  }

  async function loadChecklist() {
    if (!token.trim() || !selectedCaseId) {
      setChecklistItems([])
      return
    }

    setChecklistLoading(true)
    setError('')

    try {
      const data = await listCaseEvidenceChecklist(token, selectedCaseId)
      setChecklistItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível carregar o checklist de provas.')
    } finally {
      setChecklistLoading(false)
    }
  }

  useEffect(() => {
    void loadAttachments()
    void loadChecklist()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, selectedCaseId])

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setSelectedFile(file)
    setSuccess('')
    setError('')
  }

  async function handleUpload() {
    if (!token.trim() || !selectedCaseId || !selectedFile) return

    setUploading(true)
    setError('')
    setSuccess('')

    try {
      const uploaded = await uploadCaseAttachment(token, selectedCaseId, {
        file: selectedFile,
        category,
        description: description.trim() || undefined,
        event_date: eventDate || undefined,
      })

      setAttachments((prev) => [uploaded, ...prev])
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      setDescription('')
      setEventDate('')
      setSuccess('Prova/anexo enviado com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível enviar a prova/anexo.')
    } finally {
      setUploading(false)
    }
  }

  async function handleDownload(attachment: CaseAttachmentItem) {
    if (!token.trim() || !selectedCaseId) return

    setDownloadingId(attachment.id)
    setError('')
    setSuccess('')

    try {
      const blob = await downloadCaseAttachment(token, selectedCaseId, attachment.id)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = attachment.original_filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      setSuccess(`Download concluído: ${attachment.original_filename}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível baixar o anexo.')
    } finally {
      setDownloadingId(null)
    }
  }

  async function handleDelete(attachment: CaseAttachmentItem) {
    if (!token.trim() || !selectedCaseId) return

    const confirmed = window.confirm(`Excluir o anexo "${attachment.original_filename}"?`)
    if (!confirmed) return

    setDeletingId(attachment.id)
    setError('')
    setSuccess('')

    try {
      await deleteCaseAttachment(token, selectedCaseId, attachment.id)
      setAttachments((prev) => prev.filter((item) => item.id !== attachment.id))
      setSuccess('Prova/anexo excluído com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível excluir o anexo.')
    } finally {
      setDeletingId(null)
    }
  }

  async function handleCreateChecklistItem() {
    if (!token.trim() || !selectedCaseId || !checklistTitle.trim()) return

    setChecklistSaving(true)
    setError('')
    setSuccess('')

    try {
      const created = await createCaseEvidenceChecklistItem(token, selectedCaseId, {
        title: checklistTitle.trim(),
        category: checklistCategory,
        status: 'pending',
        priority: checklistPriority,
        requested_from: checklistRequestedFrom.trim() || undefined,
        due_date: checklistDueDate || undefined,
        notes: checklistNotes.trim() || undefined,
        metadata: {
          source: 'case_evidence_checklist_v1_frontend',
        },
      })

      setChecklistItems((prev) => [created, ...prev])
      setChecklistTitle('')
      setChecklistCategory('documento')
      setChecklistPriority('normal')
      setChecklistRequestedFrom('')
      setChecklistDueDate('')
      setChecklistNotes('')
      setSuccess('Item do checklist criado com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível criar o item do checklist.')
    } finally {
      setChecklistSaving(false)
    }
  }

  async function handleUpdateChecklistStatus(
    item: CaseEvidenceChecklistItem,
    status: CaseEvidenceChecklistStatus,
  ) {
    if (!token.trim() || !selectedCaseId) return

    setChecklistActionId(item.id)
    setError('')
    setSuccess('')

    try {
      const updated = await updateCaseEvidenceChecklistItem(token, selectedCaseId, item.id, {
        status,
      })

      setChecklistItems((prev) => prev.map((current) => (current.id === item.id ? updated : current)))
      setSuccess('Status do checklist atualizado.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível atualizar o status do checklist.')
    } finally {
      setChecklistActionId(null)
    }
  }

  async function handleDeleteChecklistItem(item: CaseEvidenceChecklistItem) {
    if (!token.trim() || !selectedCaseId) return

    const confirmed = window.confirm(`Excluir a pendência "${item.title}"?`)
    if (!confirmed) return

    setChecklistActionId(item.id)
    setError('')
    setSuccess('')

    try {
      await deleteCaseEvidenceChecklistItem(token, selectedCaseId, item.id)
      setChecklistItems((prev) => prev.filter((current) => current.id !== item.id))
      setSuccess('Item do checklist excluído com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível excluir o item do checklist.')
    } finally {
      setChecklistActionId(null)
    }
  }

  if (!selectedCaseId) {
    return (
      <section className="section-card">
        <div className="section-head">
          <p className="insight-kicker">Provas e Anexos</p>
          <h2 className="section-heading">Selecione um caso para anexar provas</h2>
          <p className="section-description">
            Fotos, vídeos, PDFs, notificações, documentos médicos e documentos pessoais ficam vinculados ao caso.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="section-card">
      <div className="section-head">
        <p className="insight-kicker">Provas e Anexos</p>
        <h2 className="section-heading">Provas do caso #{selectedCaseId}</h2>
        <p className="section-description">
          Organize os arquivos, provas recebidas e pendências antes da revisão do advogado.
        </p>
      </div>

      <div className="expansion-shell-card__meta">
        <span className="insight-badge">{attachments.length} anexo(s)</span>
        <span className="insight-badge">{formatBytes(totalSize)}</span>
        <span className="insight-badge">{checklistItems.length} item(ns) no checklist</span>
        <span className="insight-badge">{pendingChecklistCount} pendente(s)</span>
        <span className="insight-badge">{validatedChecklistCount} validado(s)</span>
        <span className="insight-badge">Upload seguro por caso</span>
      </div>

      <div className="section-card" style={{ marginTop: 16 }}>
        <div className="section-head">
          <h3 className="section-heading">Checklist de provas e pendências</h3>
          <p className="section-description">
            Controle o que precisa ser pedido, recebido, validado ou dispensado antes da revisão do advogado.
          </p>
        </div>

        <div className="form-grid">
          <label className="form-field form-field--wide">
            <span>Item pendente</span>
            <input
              value={checklistTitle}
              onChange={(event) => setChecklistTitle(event.target.value)}
              placeholder="Ex.: Solicitar boletim de ocorrência, validar contrato, pedir prints..."
            />
          </label>

          <label className="form-field">
            <span>Categoria</span>
            <select
              value={checklistCategory}
              onChange={(event) => setChecklistCategory(event.target.value as CaseEvidenceChecklistCategory)}
            >
              {checklistCategoryOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Prioridade</span>
            <select
              value={checklistPriority}
              onChange={(event) => setChecklistPriority(event.target.value as CaseEvidenceChecklistPriority)}
            >
              {checklistPriorityOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Solicitar de</span>
            <input
              value={checklistRequestedFrom}
              onChange={(event) => setChecklistRequestedFrom(event.target.value)}
              placeholder="cliente, testemunha, advogado, órgão..."
            />
          </label>

          <label className="form-field">
            <span>Prazo</span>
            <input
              type="date"
              value={checklistDueDate}
              onChange={(event) => setChecklistDueDate(event.target.value)}
            />
          </label>

          <label className="form-field form-field--wide">
            <span>Observação</span>
            <textarea
              value={checklistNotes}
              onChange={(event) => setChecklistNotes(event.target.value)}
              placeholder="Ex.: pedir pelo WhatsApp, conferir legibilidade, validar com advogado..."
              rows={3}
            />
          </label>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void handleCreateChecklistItem()}
            disabled={checklistSaving || !checklistTitle.trim()}
          >
            {checklistSaving ? 'Salvando...' : 'Adicionar pendência'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setChecklistTitle('')
              setChecklistCategory('documento')
              setChecklistPriority('normal')
              setChecklistRequestedFrom('')
              setChecklistDueDate('')
              setChecklistNotes('')
            }}
            disabled={checklistSaving}
          >
            Limpar checklist
          </button>
        </div>

        {checklistLoading ? <p className="insight-empty">Carregando checklist de provas...</p> : null}

        {!checklistLoading && checklistItems.length === 0 ? (
          <p className="insight-empty" style={{ marginTop: 16 }}>
            Nenhuma pendência cadastrada ainda. Crie itens para controlar o que precisa ser pedido, recebido ou validado.
          </p>
        ) : null}

        <div className="case-list" style={{ marginTop: 16 }}>
          {checklistItems.map((item) => (
            <article key={item.id} className="case-card">
              <div className="case-card__header">
                <div>
                  <span className="insight-badge">{getChecklistStatusLabel(item.status)}</span>
                  <span className="insight-badge">{getChecklistPriorityLabel(item.priority)}</span>
                  <h3 className="case-card__title">{item.title}</h3>
                  <p className="case-card__meta">
                    {getChecklistCategoryLabel(item.category)}
                    {item.requested_from ? ` • Solicitar de: ${item.requested_from}` : ''}
                    {item.due_date ? ` • Prazo: ${item.due_date}` : ''}
                  </p>
                </div>
              </div>

              {item.notes ? (
                <p className="body-text">{item.notes}</p>
              ) : (
                <p className="body-text">Sem observação cadastrada.</p>
              )}

              <div className="case-card__actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => void handleUpdateChecklistStatus(item, 'requested')}
                  disabled={checklistActionId === item.id}
                >
                  Marcar solicitado
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => void handleUpdateChecklistStatus(item, 'received')}
                  disabled={checklistActionId === item.id}
                >
                  Marcar recebido
                </button>

                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void handleUpdateChecklistStatus(item, 'validated')}
                  disabled={checklistActionId === item.id}
                >
                  Validar
                </button>

                <button
                  type="button"
                  className="btn btn-muted"
                  onClick={() => void handleUpdateChecklistStatus(item, 'waived')}
                  disabled={checklistActionId === item.id}
                >
                  Dispensar
                </button>

                <button
                  type="button"
                  className="btn btn-muted"
                  onClick={() => void handleDeleteChecklistItem(item)}
                  disabled={checklistActionId === item.id}
                >
                  Excluir
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="section-card" style={{ marginTop: 16 }}>
        <div className="section-head">
          <h3 className="section-heading">Adicionar prova/anexo</h3>
          <p className="section-description">
            Envie o arquivo e classifique o tipo de prova para facilitar a conferência do advogado.
          </p>
        </div>

        <div className="form-grid">
          <label className="form-field">
            <span>Arquivo</span>
            <input ref={fileInputRef} type="file" onChange={handleFileChange} />
          </label>

          <label className="form-field">
            <span>Categoria</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value as CaseAttachmentCategory)}
            >
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Data da prova</span>
            <input
              type="date"
              value={eventDate}
              onChange={(event) => setEventDate(event.target.value)}
            />
          </label>

          <label className="form-field form-field--wide">
            <span>Descrição</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Ex.: Foto da poeira no quintal, vídeo do ruído, notificação enviada, atestado médico..."
              rows={3}
            />
          </label>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={uploading || !selectedFile}
          >
            {uploading ? 'Enviando...' : 'Anexar prova'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setSelectedFile(null)
              if (fileInputRef.current) fileInputRef.current.value = ''
              setDescription('')
              setEventDate('')
              setError('')
              setSuccess('')
            }}
            disabled={uploading}
          >
            Limpar
          </button>
        </div>

        {selectedFile ? (
          <p className="body-text" style={{ marginTop: 12 }}>
            Arquivo selecionado: <strong>{selectedFile.name}</strong> — {formatBytes(selectedFile.size)}
          </p>
        ) : null}
      </div>

      {error ? <p className="status-message status-message--error">{error}</p> : null}
      {success ? <p className="status-message status-message--success">{success}</p> : null}

      <div className="section-card" style={{ marginTop: 16 }}>
        <div className="section-head">
          <h3 className="section-heading">Arquivos anexados</h3>
          <p className="section-description">
            Lista real de provas vinculadas ao caso.
          </p>
        </div>

        {loading ? <p className="insight-empty">Carregando provas/anexos...</p> : null}

        {!loading && attachments.length === 0 ? (
          <p className="insight-empty">
            Nenhuma prova anexada ainda. Para caso real, anexe documentos antes da revisão final.
          </p>
        ) : null}

        <div className="case-list">
          {attachments.map((attachment) => (
            <article key={attachment.id} className="case-card">
              <div className="case-card__header">
                <div>
                  <span className="insight-badge">{getFileKind(attachment)}</span>
                  <h3 className="case-card__title">{attachment.original_filename}</h3>
                  <p className="case-card__meta">
                    {getCategoryLabel(attachment.category)} • {formatBytes(attachment.file_size_bytes)}
                    {attachment.event_date ? ` • Data da prova: ${attachment.event_date}` : ''}
                  </p>
                </div>
              </div>

              {attachment.description ? (
                <p className="body-text">{attachment.description}</p>
              ) : (
                <p className="body-text">Sem descrição cadastrada.</p>
              )}

              <div className="case-card__actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => void handleDownload(attachment)}
                  disabled={downloadingId === attachment.id}
                >
                  {downloadingId === attachment.id ? 'Baixando...' : 'Baixar'}
                </button>

                <button
                  type="button"
                  className="btn btn-muted"
                  onClick={() => void handleDelete(attachment)}
                  disabled={deletingId === attachment.id}
                >
                  {deletingId === attachment.id ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
