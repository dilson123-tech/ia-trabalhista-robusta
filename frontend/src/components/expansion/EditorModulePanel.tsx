import { useEffect, useMemo, useState } from 'react'
import {
  ApiError,
  createEditableDocument,
  getEditableDocument,
  listEditableDocumentsForCase,
  type EditableDocumentDetail,
  type EditableDocumentItem,
} from '../../services/api'

type EditorModulePanelProps = {
  token: string
  selectedCaseId: number | null
}

export function EditorModulePanel({ token, selectedCaseId }: EditorModulePanelProps) {
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
  const [newDocumentTitle, setNewDocumentTitle] = useState('')
  const [newDocumentType, setNewDocumentType] = useState('peticao_inicial')
  const [newDocumentArea, setNewDocumentArea] = useState('trabalhista')

  useEffect(() => {
    if (!token.trim() || !selectedCaseId) {
      setDocuments([])
      setSelectedDocumentId(null)
      setSelectedDocument(null)
      setError('')
      setCreateError('')
      setCreateSuccess('')
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

  const currentVersion = useMemo(() => {
    if (!selectedDocument || selectedDocument.versions.length === 0) return null
    return selectedDocument.versions[selectedDocument.versions.length - 1]
  }, [selectedDocument])

  async function handleCreateDocument() {
    if (!token.trim() || !selectedCaseId || !newDocumentTitle.trim()) return

    setCreateLoading(true)
    setCreateError('')
    setCreateSuccess('')

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

      setDocuments((prev) => [
        {
          id: created.id,
          tenant_id: created.tenant_id,
          case_id: created.case_id,
          created_by_user_id: created.created_by_user_id,
          area: created.area,
          document_type: created.document_type,
          title: created.title,
          status: created.status,
          current_version_number: created.current_version_number,
          document_metadata: created.document_metadata,
          created_at: created.created_at,
          updated_at: created.updated_at,
        },
        ...prev,
      ])
      setSelectedDocumentId(created.id)
      setSelectedDocument(created)
      setShowCreateForm(false)
      setNewDocumentTitle('')
      setNewDocumentType('peticao_inicial')
      setNewDocumentArea('trabalhista')
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
            Lista real de documentos editáveis do caso, com detalhe, versão atual e blocos estruturados.
          </p>
        </div>
        <span className="insight-badge">
          Caso em foco: #{selectedCaseId}
        </span>
      </div>

      <div className="actions-row" style={{ marginBottom: '16px' }}>
        <button
          type="button"
          className={`btn ${showCreateForm ? 'btn-secondary' : 'btn-primary'}`}
          onClick={() => {
            setShowCreateForm((prev) => !prev)
            setCreateError('')
            setCreateSuccess('')
          }}
        >
          {showCreateForm ? 'Ocultar criação' : 'Novo documento editável'}
        </button>
      </div>

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
              <option value="trabalhista">Trabalhista</option>
              <option value="civel">Cível</option>
              <option value="consumidor">Consumidor</option>
              <option value="previdenciario">Previdenciário</option>
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

      {error ? (
        <p className="status-message status-message--error">{error}</p>
      ) : null}

      {createError ? (
        <p className="status-message status-message--error">{createError}</p>
      ) : null}

      {createSuccess ? (
        <p className="status-message status-message--success">{createSuccess}</p>
      ) : null}

      {loadingList ? (
        <p className="insight-empty">Carregando documentos editáveis do caso...</p>
      ) : null}

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
                  onClick={() => setSelectedDocumentId(document.id)}
                >
                  {document.title}
                </button>
              ))}
            </div>
          </article>

          {loadingDetail ? (
            <p className="insight-empty">Carregando detalhe do documento...</p>
          ) : null}

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
                      <ul className="info-list">
                        {currentVersion.sections.length > 0 ? (
                          currentVersion.sections.map((section, index) => (
                            <li key={`${section.key}-${index}`}>
                              <strong>{section.title}</strong> — {section.status || 'draft'} ({section.source || 'manual'})
                            </li>
                          ))
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
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
