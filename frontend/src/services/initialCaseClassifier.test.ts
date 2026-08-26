import { describe, expect, it } from 'vitest'

import {
  buildInitialCaseTitle,
  inferInitialActionType,
  inferInitialCaseArea,
} from './initialCaseClassifier'

describe('initialCaseClassifier', () => {
  it('prioriza restrição profissional por análise de risco sobre marcadores trabalhistas genéricos', () => {
    const message = `
      Edson é motorista profissional e trabalha como empregado CLT.
      Recebe salário e realiza carregamentos.
      Seus dados são enviados para análise de risco e a gerenciadora de risco
      retorna que ele não está liberado para realizar carregamentos.
      Ele busca acesso aos dados pessoais, critérios e revisão da restrição.
    `

    const area = inferInitialCaseArea(message)

    expect(area).toBe('cível')
    expect(buildInitialCaseTitle(message, area)).toBe(
      'Restrição profissional de motorista por análise de risco a esclarecer',
    )
    expect(inferInitialActionType(message, area)).toBe(
      'Obrigação de fazer / revisão de restrição profissional / dados e responsabilidade civil, a confirmar',
    )
  })

  it('preserva caso trabalhista verdadeiro sem marcadores de restrição por análise de risco', () => {
    const message = `
      Empregado trabalha sem registro em CTPS, possui horas extras não pagas,
      salário atrasado e foi demitido sem receber as verbas rescisórias.
    `

    const area = inferInitialCaseArea(message)

    expect(area).toBe('trabalhista')
    expect(buildInitialCaseTitle(message, area)).toBe(
      'Possível vínculo trabalhista, horas extras e provas digitais',
    )
    expect(inferInitialActionType(message, area)).toBe(
      'Reclamação trabalhista / reconhecimento de vínculo e verbas',
    )
  })
})

it('preserva caso consumidor comum', () => {
  const message = `
    Consumidor comprou um produto com defeito em uma loja.
    O fornecedor não resolveu o problema dentro da garantia.
  `

  const area = inferInitialCaseArea(message)

  expect(area).toBe('consumidor')
  expect(inferInitialActionType(message, area)).toBe(
    'Ação consumerista / reparação por falha na prestação ou produto',
  )
})

it('preserva cobrança cível', () => {
  const message = `
    O devedor recebeu um empréstimo por Pix, prometeu devolver o valor
    em parcelas e não pagou nenhuma parcela.
  `

  const area = inferInitialCaseArea(message)

  expect(area).toBe('cível')
  expect(inferInitialActionType(message, area)).toBe(
    'Cobrança cível / obrigação de pagamento não cumprida, a confirmar conforme documentos',
  )
})

it('preserva caso criminal', () => {
  const message = `
    O acusado recebeu denúncia e precisa apresentar resposta à acusação.
  `

  const area = inferInitialCaseArea(message)

  expect(area).toBe('criminal')
  expect(buildInitialCaseTitle(message, area)).toBe(
    'Defesa criminal com acusação e fase processual a confirmar',
  )
})

it('preserva caso de veículo com revendedora e Pix', () => {
  const message = `
    O consumidor comprou um veículo em uma revendedora, pagou entrada por Pix
    e parcelas. Depois a garagem retomou o carro.
  `

  const area = inferInitialCaseArea(message)

  expect(inferInitialActionType(message, area)).toBe(
    'Exibição de contrato / restituição de veículo ou valores / indenização',
  )
  expect(buildInitialCaseTitle(message, area)).toBe(
    'Retomada de veículo por revendedora após pagamento parcelado via Pix',
  )
})
