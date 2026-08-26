export function isVehicleDealerPixCase(message: string): boolean {
  const text = message.toLowerCase()

  const hasVehicle = /(veículo|veiculo|carro|automóvel|automovel|moto|placa|renavam|chassi)/.test(text)
  const hasDealer = /(revendedora|garagem|automóveis|automoveis|quintino|comércio de automóveis|comercio de automoveis)/.test(text)
  const hasPayment = /(pix|parcela|parcelamento|nota promissória|nota promissoria|entrada)/.test(text)
  const hasTaking = /(tomou|recolheu|retomou|retirada|bloqueio|buscae apreensão|busca e apreensao)/.test(text)

  return hasVehicle && hasDealer && hasPayment && hasTaking
}

export function isCivilCollectionCase(message: string): boolean {
  const text = message.toLowerCase()

  const obligationMarker =
    /(empréstimo|emprestimo|emprestou|emprestado|dívida|divida|devedor|credor|inadimpl|parcela|parcelas|prometeu devolver|prometeu pagar|valor devido|não pagou|nao pagou|não foi pago|nao foi pago|nenhuma parcela foi paga|cobrança|cobranca)/.test(text)

  const paymentMarker =
    /(pagamento|pagar|pago|paga|devolver|devolução|devolucao|transferência|transferencia|pix|depósito|deposito|valor|r\$)/.test(text)

  return obligationMarker && paymentMarker
}

export function isCivilProfessionalRiskRestrictionCase(message: string): boolean {
  const text = message.toLowerCase()

  const professionalMarker =
    /(motorista|motorista profissional|carregamento|carregamentos|frete|fretes|transportadora|atividade profissional|exercício da atividade|exercicio da atividade)/.test(text)

  const restrictionMarker =
    /(restrição|restricao|bloqueio|bloqueado|bloqueada|impedido|impedida|impedimento|não liberado|nao liberado|não consegue carregar|nao consegue carregar|impedido de realizar carregamentos)/.test(text)

  const riskMarker =
    /(análise de risco|analise de risco|gerenciadora de risco|gerenciamento de risco|seguradora|pesquisa de risco|consulta de risco|cadastro de risco)/.test(text)

  return professionalMarker && restrictionMarker && riskMarker
}

export function inferInitialCaseArea(message: string): string {
  const text = message.toLowerCase()

  if (isCivilProfessionalRiskRestrictionCase(message)) {
    return 'cível'
  }

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

export function inferInitialActionType(message: string, area: string): string {
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
      ? 'Obrigação de fazer / revisão de restrição profissional / dados e responsabilidade civil, a confirmar'
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

export function buildInitialCaseTitle(message: string, area: string): string {
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
