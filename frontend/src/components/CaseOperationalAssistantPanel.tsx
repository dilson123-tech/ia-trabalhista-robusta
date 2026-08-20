import { useState } from 'react'

import {
  askCaseOperationalAssistant,
  type CaseOperationalAssistantResponse,
  type CaseOperationalAssistantSuggestion,
} from '../services/api'


const ALL_BLOCKS_READY_MINUTA_PROMPT = `Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento

BLOCO 2 — Qualificação das partes

BLOCO 3 — Resumo Fático

BLOCO 4 — Fundamentação preliminar

BLOCO 5 — Pedidos

BLOCO 6 — Provas e requerimentos

BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não misture pedidos, provas, testemunhas ou pendências dentro do Resumo Fático. Coloque cada conteúdo no bloco próprio.

Não invente dados. Use linguagem prudente, como “o Autor relata”, “segundo informado”, “a confirmar”, “até o momento” e “sujeito à conferência documental”.

Quando faltar informação, escreva “a confirmar”.

Antes de gerar, considere os dados já existentes no caso em foco e mantenha coerência com os fatos, provas disponíveis, pendências e revisão obrigatória do advogado.

Comarca, competência, rito, valor da causa, pedidos finais, tutela de urgência e estratégia devem permanecer sujeitos à revisão do advogado.

Comece direto pelo BLOCO 1.`



type CaseOperationalAssistantPanelProps = {
  token: string
  caseId: number | null
  caseLabel?: string | null
  showAdvancedTools?: boolean
  onDestinationClick?: (destination: string, suggestedText?: string, label?: string) => void
  onStartNewCase?: () => void
  onInitialCaseDraft?: (draft: {
    case_number: string
    title: string
    description: string
    legal_area: string
    action_type: string
  }) => void
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

function isCivilCollectionCase(message: string): boolean {
  const text = message.toLowerCase()

  const obligationMarker =
    /(empréstimo|emprestimo|emprestou|emprestado|dívida|divida|devedor|credor|inadimpl|parcela|parcelas|prometeu devolver|prometeu pagar|valor devido|não pagou|nao pagou|não foi pago|nao foi pago|nenhuma parcela foi paga|cobrança|cobranca)/.test(text)

  const paymentMarker =
    /(pagamento|pagar|pago|paga|devolver|devolução|devolucao|transferência|transferencia|pix|depósito|deposito|valor|r\$)/.test(text)

  return obligationMarker && paymentMarker
}

function isCivilProfessionalRiskRestrictionCase(message: string): boolean {
  const text = message.toLowerCase()

  const professionalMarker =
    /(motorista|motorista profissional|carregamento|carregamentos|frete|fretes|transportadora|atividade profissional|exercício da atividade|exercicio da atividade)/.test(text)

  const restrictionMarker =
    /(restrição|restricao|bloqueio|bloqueado|bloqueada|impedido|impedida|impedimento|não liberado|nao liberado|não consegue carregar|nao consegue carregar|impedido de realizar carregamentos)/.test(text)

  const riskMarker =
    /(análise de risco|analise de risco|gerenciadora de risco|gerenciamento de risco|seguradora|pesquisa de risco|consulta de risco|cadastro de risco)/.test(text)

  return professionalMarker && restrictionMarker && riskMarker
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

  if (isCivilCollectionCase(message)) {
    return 'cível'
  }

  if (isCivilProfessionalRiskRestrictionCase(message)) {
    return 'cível'
  }

  const civilCustodyPropertyCase =
    /(pátio|patio|carreta)/.test(text) &&
    /(guarda|desapareceu|desaparecimento|sumiu|furto|roubo|responsabilidade)/.test(text)

  if (civilCustodyPropertyCase) {
    return 'cível'
  }

  if (
    /(furto|roubo|ameaça|ameaca|agressão|agressao|delegacia|boletim de ocorrência|bo|crime|prisão|prisao|preso|flagrante|audiência de custódia|audiencia de custodia|denúncia|denuncia|acusação|acusacao|resposta à acusação|resposta a acusacao|liberdade provisória|liberdade provisoria)/.test(text)
  ) {
    return 'criminal'
  }

  if (
    /(pátio|patio|carreta|veículo|veiculo|contrato|indenização|indenizacao|dano|responsabilidade civil|locação|locacao)/.test(text)
  ) {
    return 'cível'
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

  if (area === 'criminal') {
    if (/(liberdade provisória|liberdade provisoria)/.test(text)) {
      return 'Pedido criminal de liberdade provisória, sujeito à confirmação dos autos e requisitos aplicáveis'
    }

    if (/(resposta à acusação|resposta a acusacao|denúncia|denuncia|acusação|acusacao)/.test(text)) {
      return 'Defesa criminal / resposta à acusação, sujeita à confirmação da fase processual e dos autos'
    }

    return 'Medida criminal a definir conforme fatos, autos e situação processual'
  }

  if (area === 'cível' && isCivilProfessionalRiskRestrictionCase(message)) {
    const hasDataTreatment =
      /(dados pessoais|tratamento de dados|banco de dados|lgpd|cadastro|perfil profissional|critério|criterio|critérios|criterios|compartilhamento)/.test(text)

    return hasDataTreatment
      ? 'Obrigação de fazer / revisão de restrição profissional e tratamento de dados / responsabilidade civil, a confirmar conforme provas'
      : 'Obrigação de fazer / revisão de restrição profissional / responsabilidade civil, a confirmar conforme provas'
  }

  if (area === 'cível' && isCivilCollectionCase(message)) {
    return 'Cobrança cível / obrigação de pagamento não cumprida, a confirmar conforme documentos'
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

  if (area === 'cível' && isCivilProfessionalRiskRestrictionCase(message)) {
    return 'Restrição profissional de motorista por análise de risco a esclarecer'
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

  if (area === 'criminal') {
    if (/(liberdade provisória|liberdade provisoria)/.test(text)) {
      return 'Pedido de liberdade provisória com situação processual a confirmar'
    }

    if (/(resposta à acusação|resposta a acusacao|denúncia|denuncia|acusação|acusacao)/.test(text)) {
      return 'Defesa criminal com acusação e fase processual a confirmar'
    }

    return 'Questão criminal com fatos e situação processual a confirmar'
  }

  if (area === 'cível' && isCivilCollectionCase(message)) {
    return 'Cobrança cível por obrigação de pagamento não cumprida'
  }

  return 'Caso em montagem inicial'
}

function buildInitialCaseNumber(area: string, message = ''): string {
  const normalized = area
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 18)

  const base = isVehicleDealerPixCase(message)
    ? (/quintino/i.test(message) ? 'VEICULO-QUINTINO-PIX' : 'VEICULO-REVENDEDORA-PIX')
    : (normalized || 'CASO')

  const now = new Date()
  const stamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
    '-',
    String(now.getHours()).padStart(2, '0'),
    String(now.getMinutes()).padStart(2, '0'),
    String(now.getSeconds()).padStart(2, '0'),
  ].join('')

  return `${base}-${stamp}`
}

function buildInitialCaseDescription(message: string): string {
  const cleaned = normalizeInitialCaseText(message).replace(/[.!?]+$/, '')

  return `Relato inicial do cliente: ${cleaned}. Informações sujeitas à conferência do advogado antes da geração e do uso da minuta.`
}

export function CaseOperationalAssistantPanel({
  token,
  caseId,
  caseLabel,
  showAdvancedTools = false,
  onDestinationClick,
  onStartNewCase,
  onInitialCaseDraft,
}: CaseOperationalAssistantPanelProps) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState<CaseOperationalAssistantResponse | null>(null)
  const [allBlocksReadyPromptCopied, setAllBlocksReadyPromptCopied] = useState(false)

  async function handleCopyAllBlocksReadyPrompt() {
    try {
      await navigator.clipboard.writeText(ALL_BLOCKS_READY_MINUTA_PROMPT)
      setAllBlocksReadyPromptCopied(true)
      window.setTimeout(() => setAllBlocksReadyPromptCopied(false), 2200)
    } catch {
      setMessage(ALL_BLOCKS_READY_MINUTA_PROMPT)
      setAllBlocksReadyPromptCopied(true)
      window.setTimeout(() => setAllBlocksReadyPromptCopied(false), 2200)
    }
  }

  function handleUseAllBlocksReadyPrompt() {
    setMessage(ALL_BLOCKS_READY_MINUTA_PROMPT)
    setResponse(null)
    setError('')
  }

  async function handleAskAssistant() {
    const cleanedMessage = message.trim()

    if (!cleanedMessage || loading) return

    if (!caseId) {
      const initialArea = inferInitialCaseArea(cleanedMessage)
      const initialActionType = inferInitialActionType(cleanedMessage, initialArea)
      const initialTitle = buildInitialCaseTitle(cleanedMessage, initialArea)
      const initialCaseNumber = buildInitialCaseNumber(initialArea, cleanedMessage)
      const initialDescription = extractInitialCaseDescription(cleanedMessage) || buildInitialCaseDescription(cleanedMessage)

      onInitialCaseDraft?.({
        case_number: initialCaseNumber,
        title: initialTitle,
        description: initialDescription,
        legal_area: initialArea,
        action_type: initialActionType,
      })

      setResponse({
        case_id: 0,
        assistant_mode: 'initial_case_setup',
        summary: 'Entendi. Já organizei seu relato e preenchi automaticamente os campos principais do Novo Caso.',
        rewritten_input: cleanedMessage,
        suggested_actions: [
          {
            destination: 'novo_caso',
            label: 'Conferir e criar o caso',
            suggested_text: `Caso identificado:
${initialTitle}

Área provável:
${initialArea}

Tipo de ação:
${initialActionType}

Relato organizado:
${initialDescription}`,
            reason: 'A IA já estruturou o relato. Confira os dados essenciais do cliente e confirme para criar o caso e preparar a minuta.',
            priority: 'alta',
          },
        ],
        next_steps: [
          'Confira o resumo preparado pela IA.',
          'Complete somente os dados essenciais do cliente e os ajustes que considerar necessários.',
          'Clique em “Cadastrar e gerar minuta”.',
          'Revise a minuta no Editor antes de qualquer uso externo.',
        ],
        warnings: [
          'Nenhum documento, prova, pedido, valor, data ou fato adicional deve ser presumido além do que foi informado.',
          'A minuta gerada permanece sujeita à revisão do advogado responsável.',
        ],
        disclaimer: 'Copiloto jurídico de apoio. A revisão profissional do advogado é obrigatória antes de qualquer protocolo ou uso externo.',
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
            Conte o caso com suas palavras. A IA organiza as informações, identifica os pontos relevantes e prepara a estrutura inicial para revisão do advogado.
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

          {showAdvancedTools ? (
        <div
          style={{
            border: '1px solid rgba(250,204,21,0.22)',
            borderRadius: '16px',
            margin: '12px 0',
            padding: '12px',
            background: 'rgba(250,204,21,0.08)',
          }}
        >
          <div style={{ alignItems: 'center', display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'space-between' }}>
            <div>
              <strong>Prompt principal para todos os blocos da minuta</strong>
              <p style={{ margin: '4px 0 0 0', color: 'var(--muted-text)' }}>
                Use como caminho principal para gerar Endereçamento, Qualificação, Resumo Fático, Fundamentação, Pedidos, Provas e Fechamento em uma única resposta.
              </p>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              <button
                type="button"
                onClick={() => {
                  void handleCopyAllBlocksReadyPrompt()
                }}
                className="case-card__action case-card__action--summary"
                style={{ padding: '9px 12px' }}
              >
                {allBlocksReadyPromptCopied ? 'Prompt copiado' : 'Copiar prompt'}
              </button>

              <button
                type="button"
                onClick={handleUseAllBlocksReadyPrompt}
                className="case-card__action case-card__action--analysis"
                style={{ padding: '9px 12px' }}
              >
                Usar no campo
              </button>
            </div>
          </div>

          <pre
            style={{
              margin: '10px 0 0 0',
              maxHeight: '145px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              fontFamily: 'inherit',
              fontSize: '0.88rem',
              lineHeight: 1.45,
              color: 'var(--muted-text)',
            }}
          >
            {ALL_BLOCKS_READY_MINUTA_PROMPT}
          </pre>
        </div>
        ) : null}

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

          {caseId ? (
            <button
              type="button"
              onClick={() => {
                setMessage('')
                setResponse(null)
                setError('')
                onStartNewCase?.()
              }}
              disabled={loading}
              className="case-card__action case-card__action--analysis"
              style={{ padding: '11px 16px' }}
            >
              Iniciar novo caso com IA
            </button>
          ) : null}

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
              <div style={{ margin: '10px 0 0 0' }}>
                <strong>Texto corrigido/sugerido:</strong>
                <pre
                  style={{
                    margin: '8px 0 0 0',
                    padding: '12px',
                    border: '1px solid rgba(148,163,184,0.22)',
                    borderRadius: '12px',
                    background: 'rgba(15,23,42,0.48)',
                    color: 'var(--text-primary)',
                    fontFamily: 'inherit',
                    fontSize: '0.94rem',
                    lineHeight: 1.6,
                    maxHeight: '520px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {response.rewritten_input}
                </pre>
              </div>
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
          A IA organiza o relato e prepara o caso para conferência. O advogado revisa os dados antes de salvar e gerar a minuta.
        </p>
      )}
    </section>
  )
}
