import { useEffect, useMemo, useState } from 'react'
import {
  createCaseTimelineItem,
  deleteCaseTimelineItem,
  listCaseTimeline,
  updateCaseTimelineItem,
  type CaseTimelineCreatePayload,
  type CaseTimelineItem,
} from '../services/api'

type CaseTimelinePanelProps = {
  token: string
  caseId: number
}

type TimelineFormState = {
  event_date: string
  title: string
  description: string
  related_evidence: string
  related_witness: string
  pending_note: string
  sort_order: string
}

const emptyTimelineForm: TimelineFormState = {
  event_date: '',
  title: '',
  description: '',
  related_evidence: '',
  related_witness: '',
  pending_note: '',
  sort_order: '',
}

function buildTimelinePayload(form: TimelineFormState): CaseTimelineCreatePayload {
  const payload: CaseTimelineCreatePayload = {
    title: form.title.trim(),
    description: form.description.trim(),
  }

  if (form.event_date.trim()) payload.event_date = form.event_date.trim()
  if (form.related_evidence.trim()) payload.related_evidence = form.related_evidence.trim()
  if (form.related_witness.trim()) payload.related_witness = form.related_witness.trim()
  if (form.pending_note.trim()) payload.pending_note = form.pending_note.trim()

  if (form.sort_order.trim()) {
    const sortOrder = Number(form.sort_order)
    if (Number.isFinite(sortOrder)) payload.sort_order = sortOrder
  }

  return payload
}

function getDisplayValue(value?: string | null) {
  return value && value.trim() ? value : 'Não informado'
}

export function CaseTimelinePanel({ token, caseId }: CaseTimelinePanelProps) {
  const [items, setItems] = useState<CaseTimelineItem[]>([])
  const [form, setForm] = useState<TimelineFormState>(emptyTimelineForm)
  const [editingItemId, setEditingItemId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [actionItemId, setActionItemId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const orderedItems = useMemo(
    () =>
      [...items].sort((left, right) => {
        const leftOrder = Number.isFinite(left.sort_order) ? left.sort_order : 0
        const rightOrder = Number.isFinite(right.sort_order) ? right.sort_order : 0
        if (leftOrder !== rightOrder) return leftOrder - rightOrder
        return left.id - right.id
      }),
    [items],
  )

  async function loadTimeline() {
    if (!token.trim() || !caseId) {
      setItems([])
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await listCaseTimeline(token, caseId)
      setItems(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao carregar linha do tempo.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadTimeline()
  }, [token, caseId])

  function resetForm() {
    setForm(emptyTimelineForm)
    setEditingItemId(null)
  }

  function startEdit(item: CaseTimelineItem) {
    setEditingItemId(item.id)
    setForm({
      event_date: item.event_date ?? '',
      title: item.title,
      description: item.description,
      related_evidence: item.related_evidence ?? '',
      related_witness: item.related_witness ?? '',
      pending_note: item.pending_note ?? '',
      sort_order: String(item.sort_order ?? ''),
    })
    setError('')
    setSuccess('')
  }

  async function handleSubmit() {
    if (!token.trim() || !caseId) return

    if (!form.title.trim() || !form.description.trim()) {
      setError('Informe pelo menos o título e a descrição do fato.')
      return
    }

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const payload = buildTimelinePayload(form)

      if (editingItemId) {
        const updated = await updateCaseTimelineItem(token, caseId, editingItemId, payload)
        setItems((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
        setSuccess('Item da linha do tempo atualizado.')
      } else {
        const created = await createCaseTimelineItem(token, caseId, payload)
        setItems((prev) => [...prev, created])
        setSuccess('Item adicionado à linha do tempo.')
      }

      resetForm()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao salvar item da linha do tempo.'
      setError(message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(item: CaseTimelineItem) {
    if (!token.trim() || !caseId) return

    const confirmed = window.confirm(`Excluir o fato "${item.title}" da linha do tempo?`)
    if (!confirmed) return

    setActionItemId(item.id)
    setError('')
    setSuccess('')

    try {
      await deleteCaseTimelineItem(token, caseId, item.id)
      setItems((prev) => prev.filter((current) => current.id !== item.id))
      if (editingItemId === item.id) resetForm()
      setSuccess('Item removido da linha do tempo.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao excluir item da linha do tempo.'
      setError(message)
    } finally {
      setActionItemId(null)
    }
  }

  return (
    <section
      style={{
        marginTop: '12px',
        padding: '12px',
        border: '1px solid rgba(250, 204, 21, 0.26)',
        borderRadius: '10px',
        background: 'rgba(250, 204, 21, 0.06)',
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
        <strong>Linha do tempo do caso</strong>

        <button
          type="button"
          onClick={() => void loadTimeline()}
          className="case-card__action case-card__action--summary"
          style={{ padding: '6px 10px' }}
        >
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>

      <p style={{ margin: '0 0 10px 0', opacity: 0.82 }}>
        Organize a sequência dos fatos antes de gerar dossiê, análise e minuta. Linha do tempo não é prova e não substitui anexos, BO, contrato ou comprovantes.
      </p>

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
        <strong>{editingItemId ? 'Editar fato da linha do tempo' : 'Adicionar fato à linha do tempo'}</strong>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Data/período</span>
          <input
            value={form.event_date}
            onChange={(event) => setForm((prev) => ({ ...prev, event_date: event.target.value }))}
            placeholder="Ex.: A confirmar, maio/2026, 10/06/2026..."
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Título do fato</span>
          <input
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            placeholder="Ex.: Não devolução da carreta/semi-reboque"
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Descrição do fato</span>
          <textarea
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            placeholder="Descreva o fato com objetividade, separando o que aconteceu, quem participou e o que falta provar."
            rows={4}
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Prova relacionada</span>
          <input
            value={form.related_evidence}
            onChange={(event) => setForm((prev) => ({ ...prev, related_evidence: event.target.value }))}
            placeholder="Ex.: BO, contrato, petição inicial, roteiro de audiência..."
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Testemunha/depoente relacionado</span>
          <input
            value={form.related_witness}
            onChange={(event) => setForm((prev) => ({ ...prev, related_witness: event.target.value }))}
            placeholder="Ex.: Rosangela de Lourdes Siqueira, Edson Estevão..."
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Pendência/observação</span>
          <textarea
            value={form.pending_note}
            onChange={(event) => setForm((prev) => ({ ...prev, pending_note: event.target.value }))}
            placeholder="Ex.: localizar contrato, confirmar data, anexar BO..."
            rows={2}
          />
        </label>

        <label style={{ display: 'grid', gap: '4px' }}>
          <span>Ordem</span>
          <input
            type="number"
            value={form.sort_order}
            onChange={(event) => setForm((prev) => ({ ...prev, sort_order: event.target.value }))}
            placeholder="Ex.: 1"
          />
        </label>

        {error ? <p style={{ margin: 0, color: '#fca5a5' }}>{error}</p> : null}
        {success ? <p style={{ margin: 0, color: '#86efac' }}>{success}</p> : null}

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <button
            type="button"
            disabled={saving}
            onClick={() => {
              void handleSubmit()
            }}
            className="case-card__action case-card__action--analysis"
            style={{ padding: '6px 10px' }}
          >
            {saving ? 'Salvando...' : editingItemId ? 'Salvar edição' : 'Adicionar à linha do tempo'}
          </button>

          <button
            type="button"
            onClick={resetForm}
            className="case-card__action case-card__action--summary"
            style={{ padding: '6px 10px' }}
          >
            Cancelar
          </button>
        </div>
      </div>

      {orderedItems.length > 0 ? (
        <div style={{ display: 'grid', gap: '8px' }}>
          {orderedItems.map((item, index) => (
            <div
              key={item.id}
              style={{
                borderTop: '1px solid rgba(255,255,255,0.10)',
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
                  <strong>{item.sort_order || index + 1}. {item.title}</strong>
                </p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    disabled={saving || actionItemId === item.id}
                    onClick={() => startEdit(item)}
                    className="case-card__action case-card__action--summary"
                    style={{ padding: '4px 8px' }}
                  >
                    Editar
                  </button>

                  <button
                    type="button"
                    disabled={saving || actionItemId === item.id}
                    onClick={() => {
                      void handleDelete(item)
                    }}
                    className="case-card__action case-card__action--archive"
                    style={{ padding: '4px 8px' }}
                  >
                    {actionItemId === item.id ? 'Excluindo...' : 'Excluir'}
                  </button>
                </div>
              </div>

              <p style={{ margin: '0 0 4px 0', opacity: 0.86 }}>
                <strong>Data/período:</strong> {getDisplayValue(item.event_date)}
              </p>

              <p style={{ margin: '0 0 4px 0', opacity: 0.9 }}>
                {item.description}
              </p>

              <p style={{ margin: '0 0 4px 0', opacity: 0.82 }}>
                <strong>Prova relacionada:</strong> {getDisplayValue(item.related_evidence)}
              </p>

              <p style={{ margin: '0 0 4px 0', opacity: 0.82 }}>
                <strong>Testemunha/depoente:</strong> {getDisplayValue(item.related_witness)}
              </p>

              {item.pending_note ? (
                <p style={{ margin: 0, opacity: 0.82 }}>
                  <strong>Pendência/observação:</strong> {item.pending_note}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <p style={{ margin: 0, opacity: 0.82 }}>
          {loading
            ? 'Carregando linha do tempo...'
            : 'Nenhum fato cadastrado na linha do tempo. Use este bloco para organizar a sequência dos fatos antes de gerar a minuta.'}
        </p>
      )}
    </section>
  )
}
