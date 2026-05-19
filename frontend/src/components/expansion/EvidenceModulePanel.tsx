import { type ChangeEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  deleteCaseAttachment,
  downloadCaseAttachment,
  listCaseAttachments,
  uploadCaseAttachment,
  type CaseAttachmentCategory,
  type CaseAttachmentItem,
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

function getFileKind(attachment: CaseAttachmentItem) {
  const mime = attachment.mime_type?.toLowerCase() ?? ''
  if (mime.includes('pdf') || attachment.original_filename.toLowerCase().endsWith('.pdf')) return 'PDF'
  if (mime.startsWith('image/')) return 'Imagem'
  if (mime.startsWith('video/')) return 'Vídeo'
  return 'Arquivo'
}

export function EvidenceModulePanel({ token, selectedCaseId }: EvidenceModulePanelProps) {
  const [attachments, setAttachments] = useState<CaseAttachmentItem[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [category, setCategory] = useState<CaseAttachmentCategory>('pdf')
  const [description, setDescription] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const totalSize = useMemo(
    () => attachments.reduce((sum, attachment) => sum + (attachment.file_size_bytes || 0), 0),
    [attachments],
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

  useEffect(() => {
    void loadAttachments()
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
          Organize os arquivos do caso antes da revisão do advogado e do protocolo.
        </p>
      </div>

      <div className="expansion-shell-card__meta">
        <span className="insight-badge">{attachments.length} anexo(s)</span>
        <span className="insight-badge">{formatBytes(totalSize)}</span>
        <span className="insight-badge">Upload seguro por caso</span>
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
