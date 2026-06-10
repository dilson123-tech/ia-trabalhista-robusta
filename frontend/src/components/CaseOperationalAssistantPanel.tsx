import { useState } from 'react'

import {
  askCaseOperationalAssistant,
  type CaseOperationalAssistantResponse,
  type CaseOperationalAssistantSuggestion,
} from '../services/api'

type CaseOperationalAssistantPanelProps = {
  token: string
  caseId: number | null
  caseLabel?: string | null
  onDestinationClick?: (destination: string) => void
}

const destinationLabels: Record<string, string> = {
  linha_do_tempo: 'Linha do tempo',
  checklist: 'Checklist de provas',
  anexos: 'Anexos/provas',
  testemunhas: 'Testemunhas/depoentes',
  dossie: 'Dossiê interno',
  analise: 'Análise do caso',
  editor_minuta: 'Editor/minuta',
  contato_cliente: 'Cliente/WhatsApp',
}

function getDestinationLabel(destination: string): string {
  return destinationLabels[destination] ?? destination
}

function renderSuggestion(item: CaseOperationalAssistantSuggestion, index: number, onDestinationClick?: (destination: string) => void) {
  return (
    <div
      key={`${item.destination}-${item.label}-${index}`}
      style={{
        border: '1px solid rgba(250,204,21,0.24)',
        borderRadius: '14px',
        padding: '12px',
        background: 'rgba(15, 23, 42, 0.42)',
      }}
    >
      <div style={{ alignItems: 'center', display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'space-between' }}>
        <strong>{item.label}</strong>
        <button
          type="button"
          onClick={() => onDestinationClick?.(item.destination)}
          className="case-card__meta-pill"
          style={{
            cursor: onDestinationClick ? 'pointer' : 'default',
            border: '1px solid rgba(148,163,184,0.24)',
          }}
          title={`Abrir ${getDestinationLabel(item.destination)}`}
        >
          Abrir {getDestinationLabel(item.destination)} • prioridade {item.priority || 'normal'}
        </button>
      </div>

      {item.suggested_text ? (
        <p style={{ margin: '8px 0 0 0', whiteSpace: 'pre-wrap' }}>
          {item.suggested_text}
        </p>
      ) : null}

      {item.reason ? (
        <p style={{ margin: '8px 0 0 0', opacity: 0.78 }}>
          <strong>Por quê:</strong> {item.reason}
        </p>
      ) : null}
    </div>
  )
}

export function CaseOperationalAssistantPanel({ token, caseId, caseLabel, onDestinationClick }: CaseOperationalAssistantPanelProps) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState<CaseOperationalAssistantResponse | null>(null)

  async function handleAskAssistant() {
    const cleanedMessage = message.trim()

    if (!cleanedMessage || loading) return

    if (!caseId) {
      setResponse({
        case_id: 0,
        assistant_mode: 'initial_case_setup',
        summary: 'Entendi. Como ainda não há caso aberto, vou orientar a montagem inicial antes do cadastro.',
        rewritten_input: cleanedMessage,
        suggested_actions: [
          {
            destination: 'contato_cliente',
            label: 'Levantar dados básicos do cliente',
            suggested_text: 'Antes de cadastrar, confirme nome do cliente, WhatsApp, área provável, resumo dos fatos, datas principais e urgência.',
            reason: 'Esses dados ajudam a criar o caso com base mínima confiável.',
            priority: 'alta',
          },
          {
            destination: 'analise',
            label: 'Identificar área e tipo de ação',
            suggested_text: 'Use a narrativa para definir a área provável: trabalhista, cível, consumidor, família, previdenciário, criminal ou ambiental.',
            reason: 'A área jurídica orienta quais documentos, provas e perguntas serão necessários.',
            priority: 'alta',
          },
          {
            destination: 'editor_minuta',
            label: 'Preparar descrição inicial do caso',
            suggested_text: cleanedMessage,
            reason: 'A informação pode virar a primeira descrição do caso, depois de revisão humana.',
            priority: 'normal',
          },
          {
            destination: 'checklist',
            label: 'Criar lista inicial de documentos e provas',
            suggested_text: 'Liste documentos citados, prints, mensagens, contratos, laudos, comprovantes, decisões, notificações, testemunhas e pendências de confirmação.',
            reason: 'Mesmo antes de abrir o caso, já é possível orientar quais provas pedir ao cliente.',
            priority: 'alta',
          },
        ],
        next_steps: [
          'Revisar a narrativa enviada pelo cliente.',
          'Clicar em “+ Novo Caso” e preencher os dados básicos.',
          'Depois de criar o caso, voltar ao copiloto para orientar linha do tempo, checklist, anexos, testemunhas, dossiê e minuta.',
        ],
        warnings: [
          'Modo montagem inicial: ainda não há caso aberto, então nenhuma informação foi salva.',
          'Toda orientação deve ser revisada pelo advogado responsável.',
        ],
        disclaimer: 'Assistente operacional de apoio. Não substitui revisão jurídica profissional.',
        metadata: { source: 'initial_case_setup_frontend_v1' },
      })
      setError('')
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await askCaseOperationalAssistant(token, caseId, cleanedMessage)
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível consultar o assistente operacional.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section
      style={{
        border: '1px solid rgba(250,204,21,0.46)',
        borderRadius: '22px',
        margin: '18px 0',
        padding: '18px',
        background: 'linear-gradient(135deg, rgba(250,204,21,0.16), rgba(37,99,235,0.14), rgba(15,23,42,0.62))',
        boxShadow: '0 18px 44px rgba(0,0,0,0.22)',
      }}
    >
      <div style={{ alignItems: 'flex-start', display: 'flex', gap: '12px', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div>
          <p className="insight-kicker">Copiloto jurídico universal</p>
          <h2 className="insight-title" style={{ marginBottom: '6px' }}>
            IA assistente operacional do caso
          </h2>
          <p className="insight-description" style={{ maxWidth: '920px' }}>
            Escreva aqui qualquer informação do caso. A IA orienta onde aplicar: linha do tempo, checklist, anexos, testemunhas, dossiê, análise ou minuta.
          </p>
        </div>

        <span className="insight-badge">
          {caseId ? `Caso em foco: #${caseId}` : 'Pronta para orientar'}
        </span>
      </div>

      <div
        style={{
          border: '1px solid rgba(255,255,255,0.10)',
          borderRadius: '18px',
          marginTop: '14px',
          padding: '14px',
          background: 'rgba(2,6,23,0.34)',
        }}
      >
        <p style={{ margin: '0 0 10px 0', color: 'var(--muted-text)' }}>
          <strong>Contexto:</strong> {caseLabel || 'Modo montagem inicial: descreva o caso e eu te ajudo a organizar antes de cadastrar.'}
        </p>

        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ex.: Chegou um cliente dizendo que foi demitido sem registro, fazia horas extras e tem prints das conversas. Como monto esse caso?"
          rows={9}
          style={{
            width: '100%',
            minHeight: '190px',
            border: '1px solid rgba(250,204,21,0.28)',
            borderRadius: '16px',
            padding: '14px',
            background: 'rgba(15,23,42,0.72)',
            color: 'var(--text-primary)',
            outline: 'none',
            resize: 'vertical',
            lineHeight: 1.55,
            fontSize: '0.98rem',
          }}
        />

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
          <button
            type="button"
            onClick={() => {
              void handleAskAssistant()
            }}
            disabled={loading || !message.trim()}
            className="case-card__action case-card__action--analysis"
            style={{ padding: '11px 16px' }}
          >
            {loading ? 'Analisando informação...' : 'Pedir orientação da IA'}
          </button>

          <button
            type="button"
            onClick={() => {
              setMessage('')
              setResponse(null)
              setError('')
            }}
            disabled={loading}
            className="case-card__action case-card__action--summary"
            style={{ padding: '11px 16px' }}
          >
            Limpar conversa
          </button>
        </div>
      </div>

      {error ? (
        <p className="status-message status-message--error" style={{ marginTop: '10px' }}>
          {error}
        </p>
      ) : null}

      {response ? (
        <div style={{ display: 'grid', gap: '12px', marginTop: '14px' }}>
          <div
            style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '14px',
              padding: '12px',
            }}
          >
            <strong>O que a IA entendeu</strong>
            <p style={{ margin: '6px 0 0 0', opacity: 0.9 }}>{response.summary}</p>

            {response.rewritten_input ? (
              <p style={{ margin: '8px 0 0 0', opacity: 0.86 }}>
                <strong>Texto corrigido/sugerido:</strong> {response.rewritten_input}
              </p>
            ) : null}
          </div>

          {response.suggested_actions.length > 0 ? (
            <div style={{ display: 'grid', gap: '8px' }}>
              <strong>Sugestões de aplicação</strong>
              {response.suggested_actions.map((item, index) => renderSuggestion(item, index, onDestinationClick))}
            </div>
          ) : null}

          {response.next_steps.length > 0 ? (
            <div>
              <strong>Próximos passos</strong>
              <ul style={{ margin: '6px 0 0 18px', opacity: 0.88 }}>
                {response.next_steps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {response.warnings.length > 0 ? (
            <div>
              <strong>Alertas</strong>
              <ul style={{ margin: '6px 0 0 18px', opacity: 0.78 }}>
                {response.warnings.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <p style={{ margin: 0, fontSize: '0.86rem', opacity: 0.72 }}>
            {response.disclaimer}
          </p>
        </div>
      ) : (
        <p style={{ margin: '12px 0 0 0', fontSize: '0.9rem', opacity: 0.78 }}>
          A V1 não salva nada automaticamente. Ela orienta o advogado, organiza a informação e evita que ele se perca no painel.
        </p>
      )}
    </section>
  )
}
