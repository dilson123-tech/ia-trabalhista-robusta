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
  onDestinationClick?: (destination: string, suggestedText?: string, label?: string) => void
}

const destinationLabels: Record<string, string> = {
  novo_caso: 'Novo caso',
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

function renderSuggestion(item: CaseOperationalAssistantSuggestion, index: number, onDestinationClick?: (destination: string, suggestedText?: string, label?: string) => void, hasSelectedCase = false) {
  const destinationLabel = getDestinationLabel(item.destination)
  const isUnavailableUntilCaseSaved = !hasSelectedCase && item.destination !== 'novo_caso'
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
          onClick={() => {
              if (isUnavailableUntilCaseSaved) {
                return
              }
              onDestinationClick?.(item.destination, item.suggested_text, item.label)
            }}
            disabled={isUnavailableUntilCaseSaved}
          className="case-card__meta-pill"
          style={{
            cursor: onDestinationClick ? 'pointer' : 'default',
            border: '1px solid rgba(148,163,184,0.24)',
          }}
          title={isUnavailableUntilCaseSaved ? `Salve o Novo Caso para abrir ${destinationLabel}` : `Abrir ${destinationLabel}`}
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


function normalizeInitialCaseText(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

function isVehicleDealerPixCase(message: string): boolean {
  const text = message.toLowerCase()

  const hasVehicle = /(veículo|veiculo|carro|automóvel|automovel|moto|placa|renavam|chassi)/.test(text)
  const hasDealer = /(revendedora|garagem|automóveis|automoveis|quintino|comércio de automóveis|comercio de automoveis)/.test(text)
  const hasPayment = /(pix|parcela|parcelamento|nota promissória|nota promissoria|entrada)/.test(text)
  const hasTaking = /(tomou|recolheu|retomou|retirada|bloqueio|busca e apreensão|busca e apreensao)/.test(text)

  return hasVehicle && hasDealer && hasPayment && hasTaking
}


function extractInitialCaseDescription(message: string): string {
  const lowerMessage = message.toLowerCase()
  const labels = ['Descrição inicial', 'Descricao inicial']

  let startIndex = -1
  let selectedLabel = ''

  for (const label of labels) {
    const index = lowerMessage.indexOf(`${label.toLowerCase()}:`)
    if (index >= 0 && (startIndex === -1 || index < startIndex)) {
      startIndex = index
      selectedLabel = label
    }
  }

  if (startIndex < 0) return ''

  const valueStart = startIndex + selectedLabel.length + 1
  const stopLabels = [
    'Alertas',
    'Documentos e provas',
    'Pessoas/testemunhas',
    'Próximos passos',
    'Proximos passos',
    'Objetivo',
    'Classificação sugerida',
    'Classificacao sugerida',
  ]

  let valueEnd = message.length

  for (const stopLabel of stopLabels) {
    const stopIndex = lowerMessage.indexOf(`${stopLabel.toLowerCase()}:`, valueStart)
    if (stopIndex >= 0 && stopIndex < valueEnd) {
      valueEnd = stopIndex
    }
  }

  return normalizeInitialCaseText(message.slice(valueStart, valueEnd))
}

function inferInitialCaseArea(message: string): string {
  const text = message.toLowerCase()

  if (/(sem registro|hora extra|horas extras|patrão|patrao|empregado|empregador|demitid|rescis|salário|salario|ctps)/.test(text)) {
    return 'trabalhista'
  }

  if (/(inss|benefício|beneficio|auxílio|auxilio|aposentadoria|bpc|loas|perícia|pericia|laudo médico|laudo medico)/.test(text)) {
    return 'previdenciário'
  }

  if (/(pensão|pensao|guarda|divórcio|divorcio|alimentos|criança|crianca|visita|união estável|uniao estavel)/.test(text)) {
    return 'família'
  }

  if (/(produto|defeito|loja|compra|fornecedor|consumidor|garantia|nota fiscal|cobrança indevida|cobranca indevida)/.test(text)) {
    return 'consumidor'
  }

  if (/(pátio|patio|carreta|veículo|veiculo|contrato|indenização|indenizacao|dano|responsabilidade civil|locação|locacao)/.test(text)) {
    return 'cível'
  }

  if (/(furto|roubo|ameaça|ameaca|agressão|agressao|delegacia|boletim de ocorrência|bo|crime)/.test(text)) {
    return 'cível / criminal'
  }

  return 'a definir'
}

function inferInitialActionType(message: string, area: string): string {
  const text = message.toLowerCase()

  if (isVehicleDealerPixCase(message)) {
    return 'Exibição de contrato / restituição de veículo ou valores / indenização'
  }

  if (area === 'trabalhista') {
    return 'Reclamação trabalhista / reconhecimento de vínculo e verbas'
  }

  if (area === 'previdenciário') {
    return 'Revisão/ concessão de benefício previdenciário ou assistencial'
  }

  if (area === 'família') {
    return 'Ação de família a definir conforme documentos e urgência'
  }

  if (area === 'consumidor') {
    return 'Ação consumerista / reparação por falha na prestação ou produto'
  }

  if (/(pátio|patio|carreta|veículo|veiculo|guarda|furto|desapareceu|sumiu)/.test(text)) {
    return 'Responsabilidade civil / indenização por guarda de bem'
  }

  return 'A definir após triagem jurídica'
}

function buildInitialCaseTitle(message: string, area: string): string {
  const text = message.toLowerCase()

  if (isVehicleDealerPixCase(message)) {
    return 'Retomada de veículo por revendedora após pagamento parcelado via Pix'
  }

  if (/(pátio|patio|carreta)/.test(text)) {
    return 'Responsabilidade de pátio por desaparecimento/furto de carreta'
  }

  if (area === 'trabalhista') {
    return 'Possível vínculo trabalhista, horas extras e provas digitais'
  }

  if (area === 'previdenciário') {
    return 'Benefício negado pelo INSS com documentos médicos'
  }

  if (area === 'família') {
    return 'Demanda familiar com pendências documentais'
  }

  if (area === 'consumidor') {
    return 'Falha de produto/serviço com documentos e mensagens'
  }

  return 'Caso em montagem inicial'
}

function buildInitialCaseNumber(area: string, message = ''): string {
  if (isVehicleDealerPixCase(message)) {
    return /quintino/i.test(message) ? 'VEICULO-QUINTINO-PIX-001' : 'VEICULO-REVENDEDORA-PIX-001'
  }

  const normalized = area
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 18)

  return `${normalized || 'CASO'}-001`
}

function buildInitialCaseDescription(message: string): string {
  const cleaned = normalizeInitialCaseText(message).replace(/[.!?]+$/, '')

  return `Relato inicial do cliente: ${cleaned}. O caso ainda está em montagem inicial e depende de conferência dos dados do cliente, documentos, provas, datas, pessoas envolvidas, valores e urgências. Antes de qualquer medida, recomenda-se organizar a linha do tempo, criar checklist de provas, identificar anexos/documentos necessários, levantar testemunhas/depoentes e atualizar o dossiê interno.`
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
      const initialArea = inferInitialCaseArea(cleanedMessage)
      const initialActionType = inferInitialActionType(cleanedMessage, initialArea)
      const initialTitle = buildInitialCaseTitle(cleanedMessage, initialArea)
      const initialCaseNumber = buildInitialCaseNumber(initialArea, cleanedMessage)
      const initialDescription = extractInitialCaseDescription(cleanedMessage) || buildInitialCaseDescription(cleanedMessage)

      setResponse({
        case_id: 0,
        assistant_mode: 'initial_case_setup',
        summary: 'Entendi. Vou transformar seu relato em um roteiro de preenchimento para montar o caso dentro do sistema.',
        rewritten_input: cleanedMessage,
        suggested_actions: [
          {
            destination: 'novo_caso',
            label: '1. Preencher Novo Caso',
            suggested_text: `Número do caso:
${initialCaseNumber}

Título:
${initialTitle}

Área provável:
${initialArea}

Tipo de ação:
${initialActionType}

Descrição inicial:
${initialDescription}`,
            reason: 'Este bloco já organiza o relato informal em campos prontos para copiar no formulário “+ Novo Caso”.',
            priority: 'alta',
          },
          {
            destination: 'linha_do_tempo',
            label: '2. Depois de criar o caso',
            suggested_text: 'Ordem recomendada: Linha do Tempo → Checklist de provas → Anexos/provas → Testemunhas/depoentes → Dossiê interno → Análise do caso → Editor/minuta.',
            reason: 'Essa sequência evita que o advogado se perca e garante que o caso seja montado antes da minuta.',
            priority: 'alta',
          },
          {
            destination: 'checklist',
            label: '3. Documentos e provas para pedir',
            suggested_text: 'Peça ao cliente todos os documentos citados no relato: contratos, comprovantes, prints, conversas, áudios, vídeos, fotos, laudos, boletins, notificações, decisões, recibos e qualquer registro de data, valor ou responsabilidade.',
            reason: 'A prova precisa ser organizada desde o início para alimentar checklist, anexos, dossiê, análise e futura minuta.',
            priority: 'alta',
          },
          {
            destination: 'testemunhas',
            label: '4. Pessoas e testemunhas para levantar',
            suggested_text: 'Identifique quem participou, viu, recebeu mensagens, assinou documentos, acompanhou os fatos ou pode confirmar datas, valores, guarda, uso, dano, negativa, cobrança, prestação de serviço ou relação entre as partes.',
            reason: 'Pessoas-chave ajudam a preencher testemunhas/depoentes e a validar a linha do tempo.',
            priority: 'normal',
          },
          {
            destination: 'dossie',
            label: '5. Alertas antes de salvar',
            suggested_text: 'Não acuse diretamente sem prova. Use linguagem técnica, como “relata”, “informa”, “alega”, “desaparecimento”, “possível falha”, “pendente de confirmação documental” e “responsabilidade a apurar”.',
            reason: 'A montagem inicial deve ser prudente e revisada por advogado antes de virar peça ou estratégia.',
            priority: 'normal',
          },
        ],
        next_steps: [
          'Clique em “Abrir Novo caso”.',
          'Copie os campos sugeridos para o formulário.',
          'Salve o caso.',
          'Depois volte ao Copiloto com o caso em foco para montar Linha do Tempo, Checklist, Anexos, Testemunhas e Dossiê.',
        ],
        warnings: [
          'Modo montagem inicial: ainda não há caso aberto, então nenhuma informação foi salva.',
          'Os campos sugeridos são rascunho operacional e exigem revisão humana.',
        ],
        disclaimer: 'Assistente operacional de apoio. Não substitui revisão jurídica profissional.',
        metadata: {
          source: 'initial_case_setup_frontend_v2',
          initial_area: initialArea,
          initial_action_type: initialActionType,
          initial_title: initialTitle,
          initial_case_number: initialCaseNumber,
        },
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
              {response.suggested_actions.map((item, index) => renderSuggestion(item, index, onDestinationClick, Boolean(caseId)))}
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
