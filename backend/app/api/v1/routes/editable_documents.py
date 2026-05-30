import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import (
    Case,
    User,
    CaseAttachment,
    CasePartyEventModel,
    CasePartyModel,
    CasePartyRelationshipModel,
    CasePartyRepresentativeModel,
    CasePartyStateModel,
)
from app.api.v1.routes.cases import _get_or_create_case_analysis_record
from app.models.editable_document import EditableDocument, EditableDocumentVersion
from app.schemas.editable_document import (
    EditableDocumentCreate,
    EditableDocumentDetailOut,
    EditableDocumentOut,
    EditableDocumentVersionCreate,
    EditableDocumentVersionOut,
)
from app.services.editor_export_service import build_editor_html, generate_editor_pdf
from app.services.analysis_foundations import build_analysis_foundations

router = APIRouter(
    prefix="/editable-documents",
    tags=["editable-documents"],
)


def _resolve_current_user_id(db: Session, current_user: dict) -> int | None:
    username = current_user.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user.id if user else None



def _is_audiencia_estrategica_document_type(document_type: str | None) -> bool:
    normalized = (document_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    return normalized in {
        "audiencia_estrategica",
        "roteiro_audiencia",
        "perguntas_testemunhas",
        "prova_oral_estrategica",
    }



def _is_criminal_audiencia_area(area: str | None) -> bool:
    normalized = (area or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return normalized in {
        "criminal",
        "penal",
        "direito penal",
        "processo penal",
    }


def _build_criminal_audiencia_person_specific_questions(context_text: str) -> str:
    return "\n\n".join([
        _paragraphs([
            "Vítima / ofendido:",
            "1. A vítima presenciou diretamente os fatos ou tomou conhecimento por terceiros?",
            "2. A vítima reconhece o acusado? De onde o conhece?",
            "3. O reconhecimento foi feito em quais condições e por qual procedimento?",
            "4. Havia outras pessoas no local no momento dos fatos?",
            "5. Existe divergência entre boletim de ocorrência, depoimento inicial e relato atual?",
            "6. A vítima consegue separar o que viu diretamente do que ouviu de terceiros?",
            "7. Há alguma relação anterior, conflito, dívida, ameaça ou motivo de animosidade envolvendo as partes?",
        ]),
        _paragraphs([
            "Policial militar / agente da abordagem:",
            "1. Qual foi o motivo objetivo da abordagem?",
            "2. Houve denúncia anônima, flagrante visual, patrulhamento de rotina ou outra motivação concreta?",
            "3. A denúncia foi registrada, documentada ou confirmada por outro meio?",
            "4. Havia testemunhas independentes no momento da abordagem?",
            "5. Houve uso de câmera corporal, viatura com gravação, imagem pública ou outro registro audiovisual?",
            "6. Onde exatamente estavam os objetos apreendidos?",
            "7. Quem tinha posse direta dos objetos no momento da abordagem?",
            "8. A cadeia de custódia foi preservada desde a apreensão até a apresentação à autoridade policial?",
        ]),
        _paragraphs([
            "Policial civil / investigador:",
            "1. Quais diligências foram efetivamente realizadas durante a investigação?",
            "2. Todas as testemunhas relevantes foram ouvidas?",
            "3. Foram buscadas imagens, mensagens, laudos, registros telefônicos ou documentos complementares?",
            "4. Houve alguma linha alternativa de investigação descartada? Por qual motivo?",
            "5. A conclusão investigativa se baseia em prova direta, prova indireta ou presunção?",
            "6. Há algum ponto relevante que permaneceu sem diligência complementar?",
        ]),
        _paragraphs([
            "Delegado / autoridade policial:",
            "1. Quais elementos concretos justificaram o indiciamento ou a conclusão policial?",
            "2. Quais provas foram consideradas centrais para formar a convicção da autoridade policial?",
            "3. Houve pedido de perícia, imagem, quebra de dados, reconhecimento ou oitiva complementar?",
            "4. Alguma diligência relevante foi indeferida, dispensada ou não realizada?",
            "5. A conclusão policial distingue materialidade, autoria e participação de cada envolvido?",
        ]),
        _paragraphs([
            "Testemunha de acusação:",
            "1. A testemunha presenciou diretamente os fatos?",
            "2. Qual é a relação da testemunha com vítima, acusado, policiais ou demais envolvidos?",
            "3. A testemunha consegue indicar data, local, horário aproximado e sequência dos acontecimentos?",
            "4. A testemunha viu o acusado praticar a conduta atribuída a ele?",
            "5. O relato contém algo que a testemunha sabe apenas por ouvir dizer?",
            "6. Existe interesse, conflito, promessa, pressão ou vínculo que possa influenciar o depoimento?",
        ]),
        _paragraphs([
            "Testemunha de defesa:",
            "1. O que a testemunha presenciou diretamente?",
            "2. A testemunha confirma álibi, ausência de posse, ausência de autoria, ausência de ameaça ou ausência de participação?",
            "3. Há documento, imagem, mensagem ou outro elemento que confirme o relato?",
            "4. O relato da testemunha é direto ou baseado em informação recebida de terceiros?",
            "5. A testemunha consegue apontar data, local e circunstância com segurança?",
            "6. Há algum ponto que possa gerar contradição com documentos ou depoimentos já existentes?",
        ]),
        _paragraphs([
            "Acusado / réu:",
            "1. A defesa pretende que o acusado exerça o direito ao silêncio ou apresente versão em audiência?",
            "2. Onde o acusado afirma que estava no momento dos fatos?",
            "3. Há prova documental, testemunhal ou digital que sustente essa versão?",
            "4. O acusado conhecia a vítima, as testemunhas ou os policiais antes dos fatos?",
            "5. Houve abordagem, prisão, apreensão ou reconhecimento? Como ocorreu?",
            "6. Há risco de autoincriminação em alguma pergunta ou linha de esclarecimento?",
            "7. Qual versão curta, objetiva e segura pode ser sustentada sem extrapolar as provas existentes?",
        ]),
        _paragraphs([
            "Perito / responsável por laudo:",
            "1. Qual metodologia foi utilizada no laudo ou exame técnico?",
            "2. A cadeia de custódia foi documentada desde a coleta até a análise?",
            "3. Houve lacre, identificação, registro de recebimento e preservação do material?",
            "4. A conclusão é categórica, probabilística ou limitada pelas condições do exame?",
            "5. O laudo vincula o acusado ao fato ou apenas confirma materialidade?",
            "6. Há limitações técnicas, ausência de dados ou margem de incerteza relevante?",
        ]),
    ])



def _is_trabalhista_audiencia_area(area: str | None) -> bool:
    normalized = (area or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return normalized in {
        "trabalhista",
        "trabalho",
        "laboral",
        "direito do trabalho",
        "processo do trabalho",
    }


def _build_trabalhista_audiencia_person_specific_questions(context_text: str) -> str:
    return "\n\n".join([
        _paragraphs([
            "Reclamante / empregado:",
            "1. Qual era sua função, data de admissão, data de desligamento e rotina diária de trabalho?",
            "2. Quem dava ordens diretas e fiscalizava a execução do serviço?",
            "3. Qual era o horário real de entrada, saída e intervalo intrajornada?",
            "4. Os controles de ponto refletiam a jornada efetivamente cumprida?",
            "5. Havia horas extras habituais, trabalho em feriados, domingos ou supressão de intervalo?",
            "6. Os pagamentos em holerite correspondiam ao que era efetivamente trabalhado?",
            "7. Houve pagamento por fora, descontos indevidos, acúmulo de função ou alteração contratual relevante?",
            "8. O FGTS era depositado corretamente durante todo o contrato?",
            "9. Na rescisão, recebeu TRCT, guias, aviso-prévio, saldo de salário, férias, 13º salário e multa de 40% quando cabível?",
            "10. Quais documentos, mensagens ou testemunhas confirmam sua versão?",
        ]),
        _paragraphs([
            "Preposto / representante da reclamada:",
            "1. O preposto tem conhecimento direto da rotina do reclamante ou fala apenas por documentos internos?",
            "2. Qual era a função contratual e a função efetivamente exercida pelo reclamante?",
            "3. Quem controlava jornada, pausas, escala, banco de horas e autorização de horas extras?",
            "4. A empresa possui controles de ponto completos, assinados e compatíveis com a rotina real?",
            "5. Como eram registradas horas extras, intervalos, faltas, atrasos e compensações?",
            "6. A empresa confirma a entrega de holerites, comprovantes de pagamento e documentos rescisórios?",
            "7. A empresa confirma recolhimento integral de FGTS, INSS e demais verbas durante o contrato?",
            "8. Houve advertências, suspensões, acordos de compensação, banco de horas ou alteração contratual?",
            "9. Quais documentos a empresa trouxe para comprovar sua versão?",
            "10. Há algum ponto da rotina que o preposto não consiga confirmar por conhecimento próprio?",
        ]),
        _paragraphs([
            "Testemunha do reclamante:",
            "1. A testemunha trabalhou no mesmo setor, turno ou período do reclamante?",
            "2. O que presenciou diretamente sobre jornada, intervalo, horas extras e controle de ponto?",
            "3. A testemunha via o reclamante chegando antes, saindo depois ou trabalhando sem registro correto?",
            "4. A testemunha presenciou ordens de superiores, metas, cobrança ou fiscalização da rotina?",
            "5. A testemunha sabe informar se havia pagamento por fora, acúmulo de função ou desvio de função?",
            "6. A testemunha presenciou condições de insalubridade, periculosidade, falta de EPI ou risco ocupacional?",
            "7. O relato é baseado em convivência direta ou em comentário de terceiros?",
            "8. Há contradição possível entre o relato da testemunha e documentos de ponto, holerites ou mensagens?",
        ]),
        _paragraphs([
            "Testemunha da reclamada:",
            "1. A testemunha trabalhou diretamente com o reclamante ou apenas conhece a rotina geral da empresa?",
            "2. A testemunha consegue confirmar a jornada real do reclamante por conhecimento direto?",
            "3. A testemunha acompanhava registro de ponto, intervalos, escalas e horas extras?",
            "4. A testemunha sabe se havia autorização formal para horas extras ou banco de horas?",
            "5. A testemunha presenciou entrega e uso efetivo de EPI, treinamentos ou fiscalização de segurança?",
            "6. A testemunha tem cargo de confiança, vínculo hierárquico ou interesse que possa influenciar o depoimento?",
            "7. O relato confirma documentos da empresa ou apenas reproduz procedimento padrão?",
            "8. Há algum ponto que a testemunha não tenha presenciado diretamente?",
        ]),
        _paragraphs([
            "Gestor / encarregado:",
            "1. O gestor distribuía tarefas, controlava jornada ou autorizava horas extras do reclamante?",
            "2. Como eram registradas ordens, metas, escalas, trocas de turno e necessidade de permanência após o horário?",
            "3. Havia cobrança para iniciar atividades antes do registro de ponto ou continuar após o encerramento?",
            "4. O gestor fiscalizava intervalo intrajornada, pausas, uso de EPI e condições do ambiente?",
            "5. O gestor comunicava ao RH diferenças de jornada, faltas, atrasos ou ocorrências?",
            "6. Havia acúmulo de função, substituição de colegas ou tarefas fora da função contratada?",
            "7. O gestor consegue indicar documentos ou mensagens que confirmem sua versão?",
        ]),
        _paragraphs([
            "RH / responsável por folha, ponto e rescisão:",
            "1. Quem era responsável por ponto, holerites, banco de horas, férias, FGTS e verbas rescisórias?",
            "2. Os controles de ponto foram conferidos antes do fechamento da folha?",
            "3. Houve pagamento de horas extras, adicionais, DSR, férias, 13º salário, FGTS e verbas rescisórias?",
            "4. Existem TRCT, recibos, comprovantes de pagamento, extrato de FGTS e guias rescisórias?",
            "5. Houve acordo de compensação, banco de horas, descontos ou ajustes manuais no ponto?",
            "6. Como a empresa apurou saldo de salário, aviso-prévio, férias, 13º e multa de 40% do FGTS?",
            "7. Há divergência entre CTPS, contrato, holerites, ponto, TRCT e comprovantes?",
        ]),
        _paragraphs([
            "Técnico de segurança / medicina do trabalho:",
            "1. Existem PPP, LTCAT, PGR, PCMSO, laudos ambientais, fichas de EPI e registros de treinamento?",
            "2. O reclamante estava exposto a agente insalubre, perigoso, calor, ruído, produtos químicos ou risco acentuado?",
            "3. A exposição era habitual, intermitente ou eventual?",
            "4. Os EPIs eram adequados, entregues, substituídos, fiscalizados e efetivamente usados?",
            "5. Há registros de orientação, treinamento, fiscalização e advertência por não uso de EPI?",
            "6. O ambiente foi avaliado por medição técnica ou apenas por procedimento interno?",
            "7. Há divergência entre documentos ambientais e a rotina descrita por empregados/testemunhas?",
        ]),
        _paragraphs([
            "Perito / responsável por laudo trabalhista:",
            "1. Qual metodologia foi utilizada para avaliar jornada, ambiente, insalubridade, periculosidade ou nexo ocupacional?",
            "2. A análise considerou documentos, inspeção, medições, entrevistas e rotina efetiva de trabalho?",
            "3. Os EPIs eram suficientes para neutralizar ou reduzir o risco conforme documentação e prática real?",
            "4. A conclusão depende de prova testemunhal, medição ambiental, documentos de segurança ou cálculo trabalhista?",
            "5. Há limitações técnicas, ausência de documentos ou necessidade de diligência complementar?",
            "6. O laudo confirma condição trabalhista específica ou apenas aponta necessidade de apuração?",
        ]),
    ])



def _is_consumidor_audiencia_area(area: str | None) -> bool:
    normalized = (area or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return normalized in {
        "consumidor",
        "consumer",
        "direito do consumidor",
        "relacao de consumo",
        "relação de consumo",
    }


def _build_consumidor_audiencia_person_specific_questions(context_text: str) -> str:
    return "\n\n".join([
        _paragraphs([
            "Consumidor / autor:",
            "1. Qual produto, serviço, contrato, cobrança, negativação ou atendimento originou o problema?",
            "2. Quando o consumidor percebeu o defeito, cobrança indevida, falha do serviço ou inscrição negativa?",
            "3. O consumidor tentou resolver administrativamente? Por quais canais e em quais datas?",
            "4. Existem protocolos, prints, e-mails, mensagens, gravações, contratos, faturas ou comprovantes?",
            "5. O consumidor sofreu bloqueio, interrupção de serviço, restrição de crédito, prejuízo financeiro ou constrangimento?",
            "6. O consumidor reconhece a contratação, compra, dívida ou transação discutida?",
            "7. Houve informação clara sobre preço, prazo, juros, multa, tarifa, garantia, cancelamento ou risco?",
            "8. O dano alegado é material, moral, ambos ou apenas obrigação de fazer/não fazer?",
            "9. Há algo que possa indicar culpa exclusiva do consumidor, uso indevido, atraso ou contratação válida?",
            "10. Qual providência concreta o consumidor busca: cancelamento, baixa de negativação, restituição, indenização, reparo, troca ou cumprimento de oferta?",
        ]),
        _paragraphs([
            "Fornecedor / empresa ré:",
            "1. A empresa reconhece a relação de consumo e a contratação discutida?",
            "2. Quais documentos demonstram contratação, aceite, entrega, prestação do serviço ou origem da cobrança?",
            "3. A empresa possui gravações, logs, contrato, pedido, nota fiscal, faturas, protocolos ou histórico de atendimento?",
            "4. Houve falha reconhecida, cancelamento solicitado, contestação de cobrança ou reclamação prévia?",
            "5. A negativação, cobrança ou restrição foi precedida de comunicação adequada?",
            "6. A empresa consegue demonstrar que a informação ao consumidor foi clara, ostensiva e suficiente?",
            "7. Houve oferta, publicidade, promessa comercial ou condição contratual diferente da executada?",
            "8. A empresa adotou providência para corrigir o problema após reclamação?",
            "9. Há política interna, prazo de resposta, garantia, assistência técnica ou canal de ouvidoria aplicável?",
            "10. Algum ponto da defesa depende apenas de procedimento padrão sem prova individual do caso?",
        ]),
        _paragraphs([
            "Atendente / suporte / SAC / ouvidoria:",
            "1. O atendimento foi realizado por qual canal: telefone, WhatsApp, e-mail, chat, app, loja física ou ouvidoria?",
            "2. Qual protocolo foi aberto e qual solução foi prometida ao consumidor?",
            "3. O consumidor informou cobrança indevida, defeito, fraude, cancelamento, negativação ou falha de serviço?",
            "4. Houve orientação para aguardar prazo, reenviar documentos, pagar valor, cancelar serviço ou registrar nova reclamação?",
            "5. O atendimento registrou corretamente o pedido do consumidor?",
            "6. O consumidor recebeu resposta final clara e documentada?",
            "7. Há divergência entre o que foi dito no atendimento e o que a empresa alega no processo?",
        ]),
        _paragraphs([
            "Representante comercial / vendedor / loja:",
            "1. Qual oferta, promessa, preço, prazo, garantia ou condição foi apresentada ao consumidor?",
            "2. O consumidor recebeu contrato, nota fiscal, termo de garantia, regulamento ou comprovante da oferta?",
            "3. Houve diferença entre publicidade/oferta e produto ou serviço efetivamente entregue?",
            "4. O consumidor foi informado sobre limitações, fidelidade, multa, juros, tarifa ou condições de cancelamento?",
            "5. O vendedor presenciou reclamação, tentativa de troca, cancelamento ou contestação?",
            "6. Há comissão, meta, vínculo ou interesse que possa influenciar o relato?",
        ]),
        _paragraphs([
            "Testemunha do consumidor:",
            "1. A testemunha presenciou diretamente o defeito, falha de serviço, cobrança, atendimento ou constrangimento?",
            "2. A testemunha acompanhou tentativa de solução administrativa?",
            "3. A testemunha viu efeitos práticos como interrupção de serviço, recusa de atendimento, negativação, perda financeira ou exposição pública?",
            "4. O relato é baseado em fato presenciado ou em informação contada pelo consumidor?",
            "5. Há mensagens, fotos, vídeos, comprovantes ou protocolos que confirmem o relato?",
        ]),
        _paragraphs([
            "Testemunha do fornecedor:",
            "1. A testemunha conhece o caso concreto ou apenas explica o procedimento padrão da empresa?",
            "2. A testemunha participou da contratação, cobrança, entrega, assistência técnica ou atendimento?",
            "3. A testemunha consegue confirmar a regularidade da cobrança, negativação, serviço ou produto com base em documentos do caso?",
            "4. O relato depende de sistema interno, protocolo ou log que possa ser exibido nos autos?",
            "5. Há algum ponto que a testemunha não tenha presenciado diretamente?",
        ]),
        _paragraphs([
            "Responsável financeiro / cobrança / negativação:",
            "1. Qual é a origem exata da dívida, cobrança, tarifa, juros, multa ou negativação?",
            "2. A empresa possui contrato, fatura, comprovante de uso, aceite ou documento que demonstre o débito?",
            "3. O consumidor contestou a cobrança antes da negativação ou ajuizamento?",
            "4. A inscrição em cadastro restritivo observou valor, data, comunicação e identificação corretos?",
            "5. Houve baixa, acordo, pagamento parcial, cancelamento ou duplicidade de cobrança?",
            "6. Há risco de cobrança por serviço não contratado, fraude, erro sistêmico ou dívida prescrita?",
        ]),
        _paragraphs([
            "Técnico / assistência / perito do produto ou serviço:",
            "1. Qual defeito, vício, falha técnica ou limitação foi constatada?",
            "2. O problema decorre de fabricação, instalação, mau uso, desgaste, ausência de manutenção ou falha do serviço?",
            "3. Houve tentativa de reparo, troca, reembolso ou assistência técnica dentro do prazo?",
            "4. Existem laudo, ordem de serviço, fotos, vídeos, logs ou relatório técnico?",
            "5. A conclusão técnica é categórica ou depende de análise complementar?",
            "6. O defeito comprometeu uso, segurança, funcionalidade ou valor do produto/serviço?",
        ]),
    ])



def _is_familia_audiencia_area(area: str | None) -> bool:
    normalized = (area or "").strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return normalized in {
        "familia",
        "família",
        "family",
        "direito de familia",
        "direito de família",
        "familia e sucessoes",
        "família e sucessões",
        "vara de familia",
        "vara de família",
    }


def _build_familia_audiencia_person_specific_questions(context_text: str) -> str:
    return "\n\n".join([
        _paragraphs([
            "Genitor / requerente:",
            "1. Qual pedido principal está sendo discutido: guarda, alimentos, convivência, divórcio, união estável ou regulamentação de visitas?",
            "2. Qual é a rotina atual da criança ou adolescente, incluindo moradia, escola, saúde, alimentação, transporte e atividades?",
            "3. Quem exerce os cuidados diários e quem participa das decisões relevantes sobre educação, saúde e convivência?",
            "4. Como ocorre a convivência com o outro genitor e quais dificuldades práticas existem?",
            "5. Há registros de mensagens, acordos anteriores, comprovantes de despesas, relatórios escolares ou documentos médicos?",
            "6. Qual é a renda, ocupação, condição econômica e capacidade contributiva das partes quando houver pedido de alimentos?",
            "7. Há histórico de violência, ameaça, abandono, alienação parental, uso abusivo de álcool/drogas ou risco à criança?",
            "8. O pedido atende ao melhor interesse da criança ou adolescente? Como isso será demonstrado em prova?",
            "9. Há tentativa de acordo, mediação, composição familiar ou plano de convivência possível?",
            "10. Quais fatos o advogado precisa confirmar antes de sustentar a tese em audiência?",
        ]),
        _paragraphs([
            "Genitor / requerido:",
            "1. O requerido concorda com guarda, convivência, alimentos ou partilha nos termos pedidos?",
            "2. Qual é sua participação real na rotina da criança, escola, saúde, lazer, transporte e despesas?",
            "3. Alega impossibilidade financeira, alteração de renda, desemprego, nova família ou outras obrigações?",
            "4. Existem comprovantes de pagamento, transferências, compras, despesas diretas ou ajuda informal?",
            "5. Há divergência entre a rotina narrada pelo requerente e a rotina efetivamente praticada?",
            "6. O requerido afirma impedimento de convivência, afastamento injustificado ou dificuldade criada pela outra parte?",
            "7. Há elementos que indiquem risco, negligência, alienação parental ou conflito prejudicial à criança?",
            "8. O requerido propõe plano alternativo de guarda, convivência, alimentos ou responsabilidades?",
            "9. Alguma afirmação depende de prova documental, testemunhal, estudo social ou avaliação psicossocial?",
        ]),
        _paragraphs([
            "Criança / adolescente, quando houver escuta adequada:",
            "1. A oitiva é recomendável, necessária e compatível com idade, maturidade e proteção emocional?",
            "2. A criança/adolescente demonstra vínculo com ambos os genitores ou cuidadores?",
            "3. Há sinais de pressão, indução, medo, conflito de lealdade ou fala treinada?",
            "4. A rotina escolar, social, familiar e de saúde está preservada?",
            "5. A manifestação deve ser colhida por equipe técnica, escuta especializada ou meio menos invasivo?",
            "6. Há risco de exposição indevida, revitimização ou agravamento do conflito familiar?",
        ]),
        _paragraphs([
            "Responsável financeiro / alimentos:",
            "1. Qual é a renda formal e informal de cada parte?",
            "2. Existem holerites, extratos, declaração de imposto, MEI, contrato, carteira de trabalho ou indícios de renda não declarada?",
            "3. Quais são as despesas comprovadas da criança ou adolescente?",
            "4. Há gastos com escola, material, transporte, plano de saúde, medicamentos, alimentação, moradia e atividades extras?",
            "5. O valor pedido ou oferecido observa necessidade, possibilidade e proporcionalidade?",
            "6. Existem outros filhos, dependentes, dívidas relevantes ou alteração financeira recente?",
            "7. Há pagamentos informais que precisam ser reconhecidos ou organizados documentalmente?",
        ]),
        _paragraphs([
            "Testemunha familiar:",
            "1. A testemunha convive diretamente com a criança/adolescente e com as partes?",
            "2. O que presenciou sobre rotina, cuidado, convivência, comportamento, despesas e participação parental?",
            "3. O relato é baseado em observação direta ou em informação recebida de uma das partes?",
            "4. A testemunha presenciou impedimento de visitas, abandono, conflito, ameaça, negligência ou tentativa de acordo?",
            "5. Há vínculo afetivo, dependência econômica, inimizade ou interesse que possa influenciar o depoimento?",
            "6. O relato confirma documentos, mensagens, comprovantes ou histórico do caso?",
        ]),
        _paragraphs([
            "Testemunha escolar / cuidador / profissional próximo:",
            "1. A testemunha acompanha a rotina escolar, saúde, cuidados, horários ou comportamento da criança?",
            "2. Quem leva e busca a criança, participa de reuniões, acompanha tarefas e responde a chamados da escola?",
            "3. Houve mudança de comportamento, faltas, queda de desempenho, ansiedade, medo ou conflito familiar perceptível?",
            "4. A escola/cuidador recebeu informações divergentes dos genitores?",
            "5. Existem relatórios, comunicados, agendas, mensagens ou registros escolares relevantes?",
            "6. O relato é técnico/profissional ou apenas impressão pessoal?",
        ]),
        _paragraphs([
            "Assistente social / equipe técnica:",
            "1. Quais elementos foram observados sobre moradia, rede de apoio, rotina, vínculos e capacidade de cuidado?",
            "2. Foram ouvidas as partes, criança/adolescente, familiares, escola ou profissionais de saúde?",
            "3. O estudo social identificou risco, vulnerabilidade, negligência, alienação parental ou conflito intenso?",
            "4. A conclusão recomenda guarda, convivência, acompanhamento, mediação ou nova avaliação?",
            "5. Há limitações no estudo, ausência de entrevista, documentação incompleta ou necessidade de diligência complementar?",
            "6. A recomendação está alinhada ao melhor interesse da criança/adolescente?",
        ]),
        _paragraphs([
            "Psicólogo / perito psicossocial:",
            "1. Qual metodologia foi utilizada na avaliação psicossocial?",
            "2. Foram observados vínculos afetivos, conflito de lealdade, medo, indução, sofrimento emocional ou resistência injustificada?",
            "3. A avaliação diferencia conflito conjugal de risco parental concreto?",
            "4. Há sinais compatíveis com alienação parental, violência psicológica, negligência ou manipulação?",
            "5. A conclusão é definitiva ou recomenda acompanhamento, reavaliação, terapia familiar ou estudo complementar?",
            "6. A manifestação técnica preserva a criança/adolescente de exposição excessiva ao conflito?",
        ]),
    ])



def _is_previdenciario_audiencia_area(area: str | None) -> bool:
    normalized = (area or "").strip().lower().replace("_", " ").replace("-", " ").replace("/", " ")
    normalized = " ".join(normalized.split())
    return normalized in {
        "previdenciario",
        "previdenciário",
        "direito previdenciario",
        "direito previdenciário",
        "previdenciario bpc loas",
        "previdenciário bpc loas",
        "bpc",
        "loas",
        "bpc loas",
        "beneficio assistencial",
        "benefício assistencial",
        "beneficio previdenciario",
        "benefício previdenciário",
        "inss",
        "seguridade social",
    }


def _build_previdenciario_audiencia_person_specific_questions(context_text: str) -> str:
    return "\n\n".join([
        _paragraphs([
            "Requerente / segurado:",
            "1. Qual benefício está sendo discutido: BPC/LOAS, benefício por incapacidade, aposentadoria, revisão ou outro benefício previdenciário?",
            "2. Qual é a idade, escolaridade, profissão, histórico de trabalho e situação atual do requerente?",
            "3. No caso de BPC/LOAS, qual deficiência, impedimento de longo prazo, condição social ou vulnerabilidade fundamenta o pedido?",
            "4. No caso de incapacidade, quais atividades o requerente não consegue realizar e desde quando?",
            "5. Existem laudos médicos, receitas, exames, atestados, prontuários, relatórios terapêuticos ou documentos de reabilitação?",
            "6. O requerente já passou por perícia médica, avaliação social, atendimento no CRAS ou indeferimento administrativo do INSS?",
            "7. Há CadÚnico, NIS, comprovante de renda familiar, composição familiar e despesas essenciais atualizados?",
            "8. O requerente recebe ajuda de familiares, terceiros, benefício assistencial, pensão, aposentadoria ou renda informal?",
            "9. A condição alegada é permanente, temporária, progressiva, intermitente ou dependente de tratamento contínuo?",
            "10. Quais pontos o advogado precisa confirmar para evitar contradição entre relato, documentos e perícia?",
        ]),
        _paragraphs([
            "Familiar cuidador / responsável pela rotina:",
            "1. O familiar acompanha a rotina diária, cuidados pessoais, medicação, alimentação, deslocamento e consultas?",
            "2. Quais limitações concretas observa na vida diária do requerente?",
            "3. O requerente depende de ajuda para banho, alimentação, locomoção, higiene, comunicação, controle de medicação ou atos da vida civil?",
            "4. Quem mora na mesma residência e qual é a renda real de cada integrante do grupo familiar?",
            "5. Existem despesas relevantes com remédios, fraldas, transporte, consultas, exames, alimentação especial ou adaptações?",
            "6. Há rede de apoio, cuidador informal, vizinhos, familiares próximos ou assistência pública?",
            "7. O relato do cuidador é compatível com laudos, receitas, CadÚnico, fotos, comprovantes e demais documentos?",
            "8. Há risco de o familiar exagerar, omitir renda ou desconhecer informações importantes?",
        ]),
        _paragraphs([
            "Representante legal / procurador:",
            "1. Qual é o vínculo com o requerente e há procuração, curatela, tutela, guarda ou representação formal?",
            "2. Quem organizou o pedido administrativo, documentos médicos, CadÚnico e comprovantes de renda?",
            "3. O representante conhece diretamente a situação social, médica e financeira do requerente?",
            "4. Houve indeferimento administrativo? Qual motivo foi apontado pelo INSS?",
            "5. Foram juntados documentos atualizados ou há lacunas de prova médica/social?",
            "6. Há necessidade de atualizar CadÚnico, renda familiar, laudos ou composição do grupo familiar antes da audiência/perícia?",
        ]),
        _paragraphs([
            "Médico assistente / profissional de saúde:",
            "1. Qual diagnóstico, CID, histórico clínico e evolução do quadro?",
            "2. A condição gera incapacidade laboral, impedimento de longo prazo, limitação funcional ou necessidade de cuidado contínuo?",
            "3. Desde quando o profissional acompanha o requerente e com qual frequência?",
            "4. Quais exames, prontuários, relatórios, terapias, medicamentos ou tratamentos confirmam o quadro?",
            "5. A limitação é compatível com idade, escolaridade, profissão e realidade social do requerente?",
            "6. Existe possibilidade de reabilitação, melhora, tratamento, adaptação ou retorno ao trabalho?",
            "7. O relatório médico é objetivo, datado, assinado e suficiente para dialogar com a perícia?",
        ]),
        _paragraphs([
            "Perito médico:",
            "1. Qual metodologia foi usada na avaliação pericial?",
            "2. A perícia considerou documentos médicos, histórico clínico, exames, medicamentos e relato funcional?",
            "3. A conclusão diferencia diagnóstico de incapacidade funcional ou impedimento de longo prazo?",
            "4. A perícia avaliou compatibilidade entre limitações, profissão, idade, escolaridade e possibilidade de reabilitação?",
            "5. Há divergência entre laudo pericial e documentos do médico assistente?",
            "6. A conclusão é categórica, parcial, temporária ou depende de complementação documental?",
            "7. No BPC/LOAS, a perícia considerou impedimento de longo prazo e barreiras sociais, não apenas doença isolada?",
        ]),
        _paragraphs([
            "Assistente social / avaliador social:",
            "1. A avaliação social verificou moradia, renda familiar, despesas, vulnerabilidade, acessibilidade e rede de apoio?",
            "2. Quem compõe o grupo familiar e quais rendas devem ou não entrar no cálculo?",
            "3. O CadÚnico estava atualizado e compatível com a realidade encontrada?",
            "4. Há gastos extraordinários com saúde, transporte, alimentação, medicação ou cuidados?",
            "5. A moradia apresenta barreiras físicas, precariedade, dependência de terceiros ou risco social?",
            "6. A conclusão social é compatível com documentos, visitas, entrevistas e comprovantes?",
            "7. Há necessidade de nova avaliação social, estudo complementar ou atualização documental?",
        ]),
        _paragraphs([
            "Servidor / representante do INSS:",
            "1. Qual foi o motivo objetivo do indeferimento administrativo?",
            "2. Faltou qualidade de segurado, carência, incapacidade, deficiência, renda, CadÚnico ou documentação essencial?",
            "3. Quais documentos foram analisados no processo administrativo?",
            "4. Houve exigência não cumprida, pendência documental ou divergência cadastral?",
            "5. A decisão administrativa analisou todos os documentos médicos e sociais apresentados?",
            "6. O indeferimento se baseou em perícia, avaliação social, critério de renda ou outro fundamento?",
            "7. Há informação no CNIS, CadÚnico, Meu INSS ou processo administrativo que precise ser confrontada?",
        ]),
        _paragraphs([
            "Testemunha sobre rotina, incapacidade e vulnerabilidade:",
            "1. A testemunha convive diretamente com o requerente ou apenas sabe por comentários?",
            "2. O que presencia sobre limitações, dependência de terceiros, dificuldade de locomoção, trabalho, estudo ou cuidados pessoais?",
            "3. A testemunha conhece a renda, moradia, despesas e situação social da família?",
            "4. Viu o requerente tentando trabalhar, estudar, se deslocar, buscar tratamento ou depender de ajuda?",
            "5. O relato confirma laudos, receitas, CadÚnico, comprovantes e demais documentos?",
            "6. Há vínculo familiar, ajuda financeira, interesse ou conflito que possa influenciar o depoimento?",
        ]),
    ])


def _build_audiencia_person_specific_questions(
    context_text: str,
    area: str | None = None,
) -> str:
    if _is_previdenciario_audiencia_area(area):
        return _build_previdenciario_audiencia_person_specific_questions(context_text)

    if _is_familia_audiencia_area(area):
        return _build_familia_audiencia_person_specific_questions(context_text)

    if _is_consumidor_audiencia_area(area):
        return _build_consumidor_audiencia_person_specific_questions(context_text)

    if _is_trabalhista_audiencia_area(area):
        return _build_trabalhista_audiencia_person_specific_questions(context_text)

    if _is_criminal_audiencia_area(area):
        return _build_criminal_audiencia_person_specific_questions(context_text)

    normalized = (context_text or "").lower()

    has_pratic = "pratic sider" in normalized or "pratic" in normalized
    has_edson = "edson" in normalized
    has_rosangela = "rosangela" in normalized or "rosângela" in normalized
    has_dilson = "dilson" in normalized

    blocks: list[str] = []

    if has_pratic:
        blocks.append(_paragraphs([
            "Representante da PRATIC SIDER / parte autora:",
            "1. Quem procurou a empresa inicialmente para viabilizar a locação da carreta?",
            "2. Edson Estevão participou das tratativas antes ou durante a contratação?",
            "3. A empresa tinha conhecimento de que Edson seria usuário, condutor ou interessado prático na carreta?",
            "4. A empresa confirma se, nos autos, afirmou que Dilson teria apenas emprestado o CNPJ para Edson locar a carreta?",
            "5. A empresa sabe dizer quem estava com a posse direta ou condução da carreta no momento do desaparecimento?",
            "6. Há prova direta de que Dilson estava dirigindo ou com a posse física da carreta no momento do desaparecimento?",
            "7. A empresa foi comunicada sobre o desaparecimento/furto da carreta? Quando e por qual meio?",
            "8. Foi registrado boletim de ocorrência? Quem registrou e com quais informações?",
            "9. Havia seguro para furto/roubo da carreta? A apólice e eventual negativa foram juntadas aos autos?",
            "10. Como a empresa calculou o valor cobrado e quais documentos demonstram esse prejuízo?",
        ]))

    if has_edson:
        blocks.append(_paragraphs([
            "Edson Estevão:",
            "1. Foi o senhor quem pediu a Dilson que fizesse a locação da carreta?",
            "2. A carreta seria usada pelo senhor ou em atividade de seu interesse?",
            "3. A locação foi formalizada em nome de Dilson para atender a um pedido seu?",
            "4. Depois da locação, quem passou a usar ou conduzir a carreta no dia a dia?",
            "5. No momento do desaparecimento, quem estava com a posse direta ou condução da carreta?",
            "6. Dilson estava presente, dirigindo ou controlando a carreta quando ela desapareceu?",
            "7. Onde a carreta estava quando desapareceu?",
            "8. O local tinha controle de entrada, saída, vigilância, estacionamento ou responsável?",
            "9. O senhor comunicou Dilson sobre o desaparecimento? Quando e por qual meio?",
            "10. A empresa locadora foi comunicada? Quem comunicou e em qual momento aproximado?",
        ]))

    if has_rosangela:
        blocks.append(_paragraphs([
            "Rosangela de Lourdes Siqueira:",
            "1. A senhora conhece Dilson Pereira e Edson Estevão?",
            "2. A senhora sabe como surgiu a locação da carreta discutida no processo?",
            "3. Pelo que a senhora presenciou diretamente, Edson pediu ajuda de Dilson para locar a carreta?",
            "4. A carreta era para uso de Dilson ou para uso/interesse de Edson?",
            "5. Depois da locação, quem efetivamente passou a usar ou conduzir a carreta?",
            "6. A senhora soube quem estava com a carreta quando ela desapareceu?",
            "7. A senhora sabe se Dilson foi comunicado logo após o desaparecimento?",
            "8. A senhora presenciou alguma tentativa de esconder o fato ou, ao contrário, de comunicar e resolver a situação?",
        ]))

    if has_dilson:
        blocks.append(_paragraphs([
            "Dilson Pereira / parte ré:",
            "1. Qual foi a participação de Dilson na formalização da locação?",
            "2. A locação foi feita para uso próprio de Dilson ou para atender pedido/interesse de Edson?",
            "3. Dilson tinha posse direta, condução ou controle diário da carreta?",
            "4. Dilson estava com a carreta quando ela desapareceu?",
            "5. Quando Dilson tomou conhecimento do desaparecimento?",
            "6. Quais providências foram adotadas após essa comunicação?",
            "7. Há mensagens, testemunhas ou documentos que confirmem a participação de Edson?",
            "8. Há prova de que Dilson agiu de má-fé ou se beneficiou do desaparecimento?",
        ]))

    if not blocks:
        return _paragraphs([
            "Nenhuma pessoa específica foi identificada com segurança suficiente no contexto do caso.",
            "Separar manualmente as perguntas por parte, representante e testemunha antes da audiência.",
            "Quando houver nomes nos autos, revisar o roteiro para criar blocos individuais por pessoa.",
        ])

    return "\n\n".join(blocks)


def _build_audiencia_context_snapshot(
    db: Session | None,
    case: Case,
    tenant_id: int | None,
) -> str:
    if db is None or tenant_id is None:
        return ""

    lines: list[str] = []

    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == tenant_id,
            CasePartyStateModel.case_id == case.id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .first()
    )

    if state:
        state_metadata = state.state_metadata or {}
        metadata_parts = []
        for key in (
            "case_comarca",
            "cause_value",
            "signature_local",
            "signature_date",
            "source",
        ):
            value = _safe_text(state_metadata.get(key))
            if value:
                metadata_parts.append(f"{key}: {value}")

        if metadata_parts:
            lines.append("Metadados estruturados do caso: " + "; ".join(metadata_parts) + ".")

        parties = (
            db.query(CasePartyModel)
            .filter(
                CasePartyModel.tenant_id == tenant_id,
                CasePartyModel.party_state_id == state.id,
            )
            .order_by(CasePartyModel.id.asc())
            .all()
        )

        if parties:
            party_name_by_key = {
                party.party_key: _safe_text(party.name) or party.party_key
                for party in parties
            }

            active_party_lines = []
            historical_party_lines = []

            for party in parties[:20]:
                party_name = _safe_text(party.name) or party.party_key
                party_role = _safe_text(party.role) or "papel não informado"
                party_type = _safe_text(party.party_type) or "tipo não informado"
                party_status = _safe_text(party.status) or "status não informado"
                party_metadata = party.party_metadata or {}

                metadata_notes = []
                for key in (
                    "qualification",
                    "description",
                    "cargo",
                    "function",
                    "funcao",
                    "relation",
                    "relationship",
                    "witness_type",
                    "tipo_testemunha",
                ):
                    value = _safe_text(party_metadata.get(key))
                    if value:
                        metadata_notes.append(f"{key}: {value}")

                party_line = (
                    f"- {party_name} ({party_role}; {party_type}; status: {party_status})"
                )
                if metadata_notes:
                    party_line += " — " + "; ".join(metadata_notes)

                if party_status == "active":
                    active_party_lines.append(party_line)
                else:
                    historical_party_lines.append(party_line)

            if active_party_lines:
                lines.append("Partes/pessoas ativas cadastradas no caso:\n" + "\n".join(active_party_lines))

            if historical_party_lines:
                lines.append("Partes/pessoas históricas cadastradas no caso:\n" + "\n".join(historical_party_lines))

            representatives = (
                db.query(CasePartyRepresentativeModel)
                .filter(
                    CasePartyRepresentativeModel.tenant_id == tenant_id,
                    CasePartyRepresentativeModel.party_state_id == state.id,
                )
                .order_by(CasePartyRepresentativeModel.id.asc())
                .all()
            )
            if representatives:
                rep_lines = []
                for representative in representatives[:20]:
                    represented = party_name_by_key.get(
                        representative.represented_party_key,
                        representative.represented_party_key,
                    )
                    representative_name = party_name_by_key.get(
                        representative.representative_party_key,
                        representative.representative_party_key,
                    )
                    rep_type = _safe_text(representative.representation_type) or "representação"
                    status = _safe_text(representative.status) or "status não informado"
                    rep_lines.append(
                        f"- {representative_name} representa {represented} ({rep_type}; status: {status})"
                    )
                lines.append("Representantes cadastrados:\n" + "\n".join(rep_lines))

            relationships = (
                db.query(CasePartyRelationshipModel)
                .filter(
                    CasePartyRelationshipModel.tenant_id == tenant_id,
                    CasePartyRelationshipModel.party_state_id == state.id,
                )
                .order_by(CasePartyRelationshipModel.id.asc())
                .all()
            )
            if relationships:
                relationship_lines = []
                for relationship in relationships[:20]:
                    source = party_name_by_key.get(
                        relationship.source_party_key,
                        relationship.source_party_key,
                    )
                    target = party_name_by_key.get(
                        relationship.target_party_key,
                        relationship.target_party_key,
                    )
                    relationship_type = _safe_text(relationship.relationship_type) or "relação"
                    status = _safe_text(relationship.status) or "status não informado"
                    relationship_lines.append(
                        f"- {source} -> {target}: {relationship_type} (status: {status})"
                    )
                lines.append("Relações entre partes/pessoas:\n" + "\n".join(relationship_lines))

            events = (
                db.query(CasePartyEventModel)
                .filter(
                    CasePartyEventModel.tenant_id == tenant_id,
                    CasePartyEventModel.party_state_id == state.id,
                )
                .order_by(CasePartyEventModel.created_at.asc())
                .all()
            )
            if events:
                event_lines = []
                for event in events[:20]:
                    title = _safe_text(event.title) or _safe_text(event.event_type) or "evento"
                    description = _safe_text(event.description)
                    occurred_on = _safe_text(event.occurred_on)
                    event_party_names = [
                        party_name_by_key.get(party_key, party_key)
                        for party_key in (event.party_keys or [])
                    ]
                    event_line = f"- {title}"
                    if occurred_on:
                        event_line += f" em {occurred_on}"
                    if event_party_names:
                        event_line += " — partes: " + ", ".join(event_party_names)
                    if description:
                        event_line += f". {description}"
                    event_lines.append(event_line)
                lines.append("Eventos relevantes de partes:\n" + "\n".join(event_lines))

    attachments = (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.tenant_id == tenant_id,
            CaseAttachment.case_id == case.id,
        )
        .order_by(CaseAttachment.created_at.desc())
        .all()
    )

    if attachments:
        attachment_lines = []
        for attachment in attachments[:20]:
            filename = _safe_text(attachment.original_filename) or "arquivo sem nome"
            category = _safe_text(attachment.category) or "outro"
            description = _safe_text(attachment.description)
            event_date = attachment.event_date.isoformat() if attachment.event_date else ""
            line = f"- {filename} ({category})"
            if event_date:
                line += f" — data do evento: {event_date}"
            if description:
                line += f". {description}"
            attachment_lines.append(line)

        lines.append("Anexos/provas cadastrados no caso:\n" + "\n".join(attachment_lines))

    return "\n\n".join(line for line in lines if line).strip()


def _build_audiencia_estrategica_sections(
    case: Case,
    analysis_record,
    db: Session | None = None,
    tenant_id: int | None = None,
) -> list[dict]:
    case_number = _safe_text(getattr(case, "case_number", "")) or f"#{case.id}"
    case_title = _safe_text(getattr(case, "title", "")) or "Caso sem título"
    case_description = _safe_text(getattr(case, "description", ""))

    technical_summary = _safe_text(getattr(analysis_record, "technical_summary", ""))
    issues = getattr(analysis_record, "issues", None) or []
    next_steps = getattr(analysis_record, "next_steps", None) or []

    issues_text = "\n".join(f"- {item}" for item in issues if item)
    next_steps_text = "\n".join(f"- {item}" for item in next_steps if item)

    structured_context = _build_audiencia_context_snapshot(
        db=db,
        case=case,
        tenant_id=tenant_id,
    )

    combined_context_text = " ".join(
        [
            case_number,
            case_title,
            case_description,
            technical_summary,
            " ".join(str(item) for item in issues if item),
            " ".join(str(item) for item in next_steps if item),
            structured_context,
        ]
    )

    case_area = (
        _safe_text(getattr(case, "legal_area", ""))
        or _safe_text(getattr(case, "area", ""))
    )
    person_specific_questions = _build_audiencia_person_specific_questions(
        combined_context_text,
        area=case_area,
    )

    base_context_items = [
        f"Caso: {case_number} — {case_title}.",
        case_description,
        technical_summary,
        "Este roteiro é material de apoio estratégico para audiência/prova oral, sujeito à revisão e decisão final do advogado responsável.",
    ]
    if structured_context:
        base_context_items.append(
            "Contexto estruturado adicional identificado no caso:\n" + structured_context
        )

    base_context = _paragraphs(base_context_items)

    common_metadata = {
        "origin_sources": ["case", "technical_analysis", "executive_summary", "attachments"],
        "generation_mode": "audiencia_estrategica_from_analysis",
        "guardrail_status": "requires_professional_review",
        "export_visibility": "internal",
        "include_in_final_pdf": True,
        "document_family": "audiencia_estrategica",
    }

    return [
        {
            "key": "sintese_tese_audiencia",
            "title": "Síntese da tese para audiência",
            "content": _paragraphs(
                [
                    base_context,
                    "Objetivo: transformar os fatos, documentos e análise do caso em roteiro prático de perguntas para audiência.",
                    "A saída não é petição, manifestação, contestação ou peça para protocolo.",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "pontos_provar",
            "title": "Pontos que precisam ser provados",
            "content": _paragraphs(
                [
                    "Liste e revise os fatos que precisam ser confirmados em audiência.",
                    issues_text or "- Confirmar tese central do caso, fatos controvertidos, documentos existentes e pontos de prova oral.",
                    next_steps_text or "- Conferir documentos, anexos, testemunhas e riscos antes da audiência.",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_parte_autora",
            "title": "Perguntas indispensáveis para parte autora / representante da autora",
            "content": _paragraphs(
                [
                    "Use este bloco para perguntas objetivas à parte autora ou ao representante legal.",
                    "1. Quem participou diretamente dos fatos principais discutidos no caso?",
                    "2. Quais documentos comprovam a versão apresentada pela parte autora?",
                    "3. A parte autora tomou alguma providência concreta antes do ajuizamento?",
                    "4. Há registro formal de comunicação, cobrança, tentativa de solução ou providência administrativa?",
                    "5. Como a parte autora quantifica o dano, prejuízo ou pedido apresentado?",
                    "6. Existe documento que confirme a data, o valor e a origem do prejuízo alegado?",
                    "7. A parte autora possui prova direta do fato central controvertido?",
                    "8. A parte autora confirma se houve participação de terceiro nos fatos?",
                    "9. A parte autora realizou diligências para mitigar ou apurar o prejuízo?",
                    "10. Há algum ponto dos autos que a parte autora não consiga confirmar por conhecimento direto?",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_parte_re",
            "title": "Perguntas indispensáveis para parte ré",
            "content": _paragraphs(
                [
                    "Use este bloco quando houver depoimento pessoal da parte ré.",
                    "1. Qual foi sua participação direta nos fatos discutidos?",
                    "2. O senhor confirma ou nega a posse, guarda, uso ou controle do bem/objeto discutido no momento do fato?",
                    "3. Quais providências foram tomadas após tomar conhecimento do problema?",
                    "4. Houve comunicação à parte contrária? Por qual meio?",
                    "5. Existem documentos, mensagens ou testemunhas que confirmem sua versão?",
                    "6. Houve atuação de terceiro nos fatos? Quem e de que forma?",
                    "7. O senhor obteve vantagem com o fato discutido?",
                    "8. O senhor tentou ocultar, dificultar ou impedir a apuração dos fatos?",
                    "9. O senhor tem conhecimento direto sobre data, local e circunstâncias do fato?",
                    "10. Há algum ponto relevante que ainda não foi esclarecido?",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_testemunhas",
            "title": "Perguntas para testemunhas",
            "content": _paragraphs(
                [
                    "Separar perguntas por testemunha quando houver nomes nos autos.",
                    "Perguntas-base:",
                    "1. Qual é sua relação com as partes?",
                    "2. O que a testemunha presenciou diretamente?",
                    "3. O que sabe apenas por ouvir dizer?",
                    "4. Quem estava presente no momento do fato relevante?",
                    "5. Quem praticou ou acompanhou a conduta principal discutida?",
                    "6. A testemunha viu documentos, mensagens, pagamentos, entrega, posse ou comunicação?",
                    "7. A testemunha sabe informar datas, locais e sequência dos acontecimentos?",
                    "8. A testemunha percebeu tentativa de resolver o problema?",
                    "9. A testemunha percebeu tentativa de ocultar o fato?",
                    "10. Há algum detalhe importante que ainda não foi perguntado?",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_pessoas_identificadas",
            "title": "Perguntas por pessoa identificada",
            "content": person_specific_questions,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_repetitivas_perigosas",
            "title": "Perguntas repetitivas e perguntas perigosas",
            "content": _paragraphs(
                [
                    "Perguntas repetitivas devem ser cortadas quando buscam a mesma resposta com variações pequenas.",
                    "Usar repetição apenas se houver evasiva, contradição ou resposta incompleta.",
                    "Perguntas perigosas exigem cautela quando:",
                    "- reforçam responsabilidade formal da própria parte;",
                    "- afirmam fato ainda não comprovado;",
                    "- abrem tema sem documento mínimo;",
                    "- permitem confissão desfavorável;",
                    "- induzem testemunha;",
                    "- deixam a parte contrária explicar um ponto fraco sem contraponto.",
                    "A decisão final sobre manter ou cortar a pergunta é do advogado responsável.",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "perguntas_condicionais",
            "title": "Perguntas condicionais",
            "content": _paragraphs(
                [
                    "Perguntas condicionais só devem ser feitas se a resposta anterior abrir caminho.",
                    "Modelo:",
                    "Se a parte admitir ciência de fato relevante, perguntar desde quando sabia, como documentou e quais providências adotou.",
                    "Se a parte negar fato mencionado nos autos, perguntar por que o fato aparece em documento, manifestação ou anexo.",
                    "Se a testemunha disser que não presenciou diretamente, limitar o valor da resposta e evitar insistência improdutiva.",
                    "Se surgir contradição, pedir esclarecimento objetivo sem agressividade.",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "versao_curta",
            "title": "Versão curtíssima para audiência com pouco tempo",
            "content": _paragraphs(
                [
                    "Usar quando o tempo estiver curto.",
                    "1. Quem participou diretamente do fato central?",
                    "2. Quem tinha posse, guarda, uso, controle ou responsabilidade no momento do fato?",
                    "3. A outra parte foi comunicada? Quando e por qual meio?",
                    "4. Existe documento que confirme essa comunicação?",
                    "5. Quais providências foram adotadas após o fato?",
                    "6. Existe prova direta do prejuízo ou da responsabilidade alegada?",
                    "7. Houve atuação de terceiro? Qual?",
                    "8. Há contradição entre o que foi dito hoje e o que está nos autos?",
                    "9. O valor pedido está documentado? Como foi calculado?",
                    "10. Há algo relevante que a pessoa confirma por conhecimento direto?",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
        {
            "key": "pontos_confirmar_advogado",
            "title": "Pontos que o advogado deve confirmar antes da audiência",
            "content": _paragraphs(
                [
                    "- Conferir se os documentos citados realmente estão nos autos.",
                    "- Conferir se as testemunhas sabem por conhecimento direto ou por ouvir dizer.",
                    "- Conferir se as perguntas respeitam o saneamento e a prova deferida.",
                    "- Conferir riscos de contradição.",
                    "- Conferir se alguma pergunta pode reforçar responsabilidade formal indesejada.",
                    "- Conferir se há documentos para sustentar perguntas sobre valores, seguro, comunicação, posse, dano ou nexo.",
                    "- Revisar a versão final antes de usar em audiência.",
                    "Este material é apoio estratégico supervisionado, não substitui a condução técnica do advogado.",
                ]
            ),
            "source": "assisted_draft",
            "status": "draft",
            "metadata": common_metadata,
        },
    ]


def _build_document_detail_payload(
    db: Session,
    document: EditableDocument,
) -> dict:
    versions = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.tenant_id == document.tenant_id,
            EditableDocumentVersion.editable_document_id == document.id,
        )
        .order_by(EditableDocumentVersion.version_number.asc())
        .all()
    )

    return {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "case_id": document.case_id,
        "created_by_user_id": document.created_by_user_id,
        "area": document.area,
        "document_type": document.document_type,
        "title": document.title,
        "status": document.status,
        "current_version_number": document.current_version_number,
        "document_metadata": document.document_metadata or {},
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "versions": [
            {
                "id": version.id,
                "editable_document_id": version.editable_document_id,
                "tenant_id": version.tenant_id,
                "version_number": version.version_number,
                "approved": version.approved,
                "notes": version.notes,
                "sections": version.sections or [],
                "version_metadata": version.version_metadata or {},
                "created_by_user_id": version.created_by_user_id,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    }


def _safe_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


# PATCH: editor_export_display_title_v1
def _resolve_editor_export_title(
    db: Session,
    document: EditableDocument,
    tenant_id: int,
) -> str:
    metadata = document.document_metadata or {}

    for key in ("display_title", "editor_title", "export_title", "case_title"):
        title = _safe_text(metadata.get(key))
        if title:
            return title

    case = (
        db.query(Case)
        .filter(
            Case.id == document.case_id,
            Case.tenant_id == tenant_id,
        )
        .first()
    )
    if case:
        case_title = _safe_text(case.title)
        if case_title:
            return case_title

    return _safe_text(document.title) or "Documento Jurídico"


# PATCH: editor_fgts_claim_values_v1
def _format_brl(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    raw = f"{rounded:,.2f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_decimal_value(value) -> Decimal | None:
    if value is None or value == "":
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal(str(value))

    raw = str(value).strip()
    if not raw:
        return None

    cleaned = re.sub(r"[^0-9,.\-]", "", raw)
    if not cleaned:
        return None

    # Formato BR: 2.300,00
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        # Formato simples/US: 2300.00
        cleaned = cleaned

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_int_value(value) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value if value >= 0 else None

    match = re.search(r"\d+", str(value))
    if not match:
        return None

    parsed = int(match.group(0))
    return parsed if parsed >= 0 else None


def _metadata_first_value(metadata: dict, keys: list[str]):
    if not isinstance(metadata, dict):
        return None

    for key in keys:
        if key in metadata and metadata.get(key) not in (None, ""):
            return metadata.get(key)

    # fallback tolerante para metadados com nomes próximos
    lowered = {str(k).lower(): v for k, v in metadata.items()}
    for key in keys:
        normalized_key = key.lower()
        if normalized_key in lowered and lowered[normalized_key] not in (None, ""):
            return lowered[normalized_key]

    return None


def _case_combined_text(case, metadata: dict) -> str:
    chunks = [
        getattr(case, "case_number", "") or "",
        getattr(case, "title", "") or "",
        getattr(case, "description", "") or "",
        str(metadata or ""),
    ]
    return " ".join(chunks).lower()


def _extract_salary_from_text(text: str) -> Decimal | None:
    patterns = [
        r"sal[aá]rio(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
        r"remunera[cç][aã]o(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
        r"recebendo\s+remunera[cç][aã]o(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = _parse_decimal_value(match.group(1))
            if parsed is not None:
                return parsed
    return None


def _extract_fgts_missing_months_from_text(text: str) -> int | None:
    patterns = [
        r"(\d+)\s+(?:meses|compet[eê]ncias)\s+(?:sem|sem\s+dep[oó]sito|sem\s+recolhimento)\s+(?:de\s+)?fgts",
        r"fgts\s+(?:n[aã]o\s+recolhido|sem\s+recolhimento)\s+(?:por|durante)\s+(\d+)\s+(?:meses|compet[eê]ncias)",
        r"aus[eê]ncia\s+de\s+dep[oó]sitos?\s+(?:por|durante)\s+(\d+)\s+(?:meses|compet[eê]ncias)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _is_without_cause_dismissal(metadata: dict, text: str) -> bool:
    value = _metadata_first_value(
        metadata,
        [
            "dispensa_sem_justa_causa",
            "houve_dispensa_sem_justa_causa",
            "sem_justa_causa",
            "dismissal_without_cause",
            "modalidade_rescisao",
            "tipo_rescisao",
        ],
    )

    if isinstance(value, bool):
        return value

    value_text = str(value or "").lower()
    combined = f"{value_text} {text}"

    negative_markers = [
        "pedido de demissão",
        "pedido de demissao",
        "justa causa",
        "rescisão indireta",
        "rescisao indireta",
    ]
    if any(marker in combined for marker in negative_markers) and "sem justa causa" not in combined:
        return False

    return "sem justa causa" in combined or "dispensado sem justa causa" in combined


def _build_default_claim_values_section(cause_value: str) -> str:
    return "\n\n".join(
        [
            "Os pedidos deverão ser acompanhados de indicação de valores estimados ou liquidados antes do protocolo, conforme os dados disponíveis no caso e a memória de cálculo revisada pelo advogado responsável.",
            f"Valor da causa atualmente informado: R$ {cause_value}.",
            "Caso ainda não exista memória de cálculo, recomenda-se inserir os valores por pedido antes do ajuizamento, com indicação expressa de eventual natureza estimativa/preliminar.",
        ]
    )


# PATCH: editor_protocol_readiness_checklist_v1
def _has_placeholder(value: str) -> bool:
    normalized = _safe_text(value).lower()
    return (
        not normalized
        or "[" in normalized
        or "a complementar" in normalized
        or "a definir" in normalized
    )


def _build_protocol_readiness_checklist_section(
    *,
    author_inline_qualification: str,
    defendant_inline_qualification: str,
    lawyer_name: str,
    lawyer_oab: str,
    lawyer_uf: str,
    signature_local: str,
    signature_date: str,
    cause_value: str,
    is_fgts_case: bool,
    is_labor_case: bool = True,
) -> str:
    pending_items: list[str] = []
    ready_items: list[str] = []

    author_label = "do reclamante" if is_labor_case else "da parte autora"
    defendant_label = "da reclamada" if is_labor_case else "da parte ré"

    if "[CPF a complementar]" in author_inline_qualification:
        pending_items.append(f"Informar e conferir CPF {author_label}.")
    if "[RG a complementar]" in author_inline_qualification:
        pending_items.append(f"Informar e conferir RG/documento pessoal {author_label}, se necessário.")
    if "[endereço completo" in author_inline_qualification:
        pending_items.append(f"Informar endereço completo {author_label}.")

    if "[CNPJ a complementar]" in defendant_inline_qualification:
        pending_items.append(f"Informar e conferir CNPJ {defendant_label}.")
    if "[endereço completo" in defendant_inline_qualification:
        pending_items.append(f"Informar endereço completo {defendant_label}.")
    elif "sede em" in defendant_inline_qualification.lower():
        pending_items.append(f"Conferir se a sede/endereço {defendant_label} está completo para citação.")

    if _has_placeholder(lawyer_name):
        pending_items.append("Informar nome do advogado responsável.")
    if _has_placeholder(lawyer_oab) or _has_placeholder(lawyer_uf):
        pending_items.append("Informar OAB/UF do advogado responsável.")
    if _has_placeholder(signature_local):
        pending_items.append("Informar local de assinatura.")
    if _has_placeholder(signature_date):
        pending_items.append("Informar data de assinatura.")

    if _has_placeholder(cause_value):
        pending_items.append("Definir ou revisar valor da causa antes do protocolo.")
    else:
        ready_items.append(f"Valor da causa preenchido/revisável: R$ {cause_value}.")

    if is_fgts_case:
        pending_items.extend(
            [
                "Anexar extrato analítico completo do FGTS.",
                "Anexar ou conferir holerites/recibos salariais do período discutido.",
                "Anexar CTPS, contrato de trabalho ou documento equivalente.",
                "Conferir documentos rescisórios, especialmente se houver pedido de multa de 40%.",
                "Conferir GFIP, SEFIP, eSocial, fichas financeiras e comprovantes de recolhimento, quando disponíveis ou sob guarda da reclamada.",
                "Revisar memória de cálculo das competências sem recolhimento antes do ajuizamento.",
            ]
        )

    if not pending_items:
        pending_items.append("Sem pendências automatizadas identificadas; manter revisão profissional final antes do protocolo.")

    ready_items.append("Qualificação básica das partes gerada com os dados disponíveis no caso.")
    ready_items.append("Peça gerada pelo Editor Jurídico Vivo sujeita à validação do advogado responsável.")

    pending_block = "\n".join(f"- {item}" for item in dict.fromkeys(pending_items))
    ready_block = "\n".join(f"- {item}" for item in dict.fromkeys(ready_items))

    return "\n\n".join(
        [
            "Checklist interno de prontidão para protocolo. Este bloco serve como apoio operacional do escritório e deve ser revisado antes do ajuizamento.",
            f"Pendências e conferências obrigatórias:\n{pending_block}",
            f"Itens já tratados ou encaminhados pela peça:\n{ready_block}",
        ]
    )


def _build_fgts_claim_values_section(metadata: dict, case, cause_value: str) -> tuple[str, str | None]:
    combined_text = _case_combined_text(case, metadata)

    salary = _parse_decimal_value(
        _metadata_first_value(
            metadata,
            [
                "salario_mensal",
                "salario",
                "remuneracao_mensal",
                "remuneração_mensal",
                "monthly_salary",
            ],
        )
    ) or _extract_salary_from_text(combined_text)

    missing_months = _parse_int_value(
        _metadata_first_value(
            metadata,
            [
                "meses_sem_fgts",
                "competencias_sem_fgts",
                "meses_fgts_nao_recolhido",
                "fgts_missing_months",
            ],
        )
    ) or _extract_fgts_missing_months_from_text(combined_text)

    deposited = _parse_decimal_value(
        _metadata_first_value(
            metadata,
            [
                "valor_fgts_depositado",
                "fgts_depositado",
                "valor_ja_depositado_fgts",
                "fgts_already_deposited",
            ],
        )
    ) or Decimal("0")

    without_cause = _is_without_cause_dismissal(metadata, combined_text)

    missing_items = []
    if salary is None:
        missing_items.append("Informar salário/remuneração mensal base para cálculo do FGTS.")
    if missing_months is None:
        missing_items.append("Informar quantidade de meses ou competências sem recolhimento de FGTS.")
    missing_items.append("Anexar e conferir extrato analítico completo do FGTS.")
    missing_items.append("Conferir holerites, CTPS/contrato, comprovantes de pagamento, GFIP, SEFIP/eSocial e documentos rescisórios, se houver.")
    if not without_cause:
        missing_items.append("Confirmar modalidade de rescisão para definir se há multa rescisória de 40%.")

    if salary is None or missing_months is None:
        pending_lines = "\n".join(f"- {item}" for item in missing_items)
        content = "\n\n".join(
            [
                "Cálculo pendente para ajuizamento.",
                "Ainda não há base numérica mínima suficiente para liquidar ou estimar com segurança as diferenças de FGTS diretamente na peça.",
                f"Pendências de cálculo:\n{pending_lines}",
                f"Valor da causa atualmente informado: R$ {cause_value}. Caso não haja valor definitivo, o advogado deverá inserir valor estimado por pedido antes do protocolo.",
            ]
        )
        return content, None

    fgts_due = (salary * Decimal("0.08") * Decimal(missing_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fgts_difference = max(Decimal("0"), (fgts_due - deposited).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    fgts_fine = (fgts_difference * Decimal("0.40")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if without_cause else Decimal("0")
    total = (fgts_difference + fgts_fine).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    fine_line = (
        f"II. Diferença estimada da multa rescisória de 40% sobre o FGTS, considerada a hipótese de dispensa sem justa causa: R$ {_format_brl(fgts_fine)}."
        if without_cause
        else "II. Multa rescisória de 40% sobre o FGTS: pendente de confirmação da modalidade de rescisão, não somada ao valor estimado neste momento."
    )

    content = "\n\n".join(
        [
            "Memória preliminar de cálculo para ajuizamento, sujeita à revisão do advogado responsável, conferência documental e adequação antes do protocolo.",
            f"Base informada/identificada: salário mensal de R$ {_format_brl(salary)} e {missing_months} competência(s)/mês(es) sem recolhimento integral de FGTS.",
            f"I. Diferenças estimadas de FGTS não recolhido ou recolhido a menor: R$ {_format_brl(fgts_difference)}.",
            fine_line,
            "III. Honorários advocatícios sucumbenciais: a serem estimados ou requeridos conforme estratégia profissional e percentual aplicável, sem inclusão automática nesta memória preliminar.",
            f"IV. Valor estimado da causa, limitado aos pedidos economicamente quantificados neste cálculo preliminar: R$ {_format_brl(total)}.",
            "Observação técnica: os valores possuem natureza preliminar/estimativa e devem ser confrontados com extrato analítico do FGTS, holerites, CTPS/contrato, comprovantes de pagamento, GFIP, SEFIP/eSocial, documentos rescisórios e memória de cálculo revisada antes do ajuizamento.",
        ]
    )

    return content, _format_brl(total)


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        item_text = str(item).strip()
        if item_text:
            items.append(item_text)
    return items


def _paragraphs(lines: list[str]) -> str:
    clean_lines: list[str] = []
    seen: set[str] = set()

    for line in lines:
        normalized = _safe_text(line)
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        clean_lines.append(normalized)

    return "\n\n".join(clean_lines)


def _series_block(title: str, items: list[str], limit: int = 4) -> str:
    normalized_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned = _safe_text(item).rstrip(".;:, ")
        if not cleaned:
            continue
        fingerprint = cleaned.lower()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized_items.append(cleaned)

    if not normalized_items:
        return ""

    lines = [title]
    for item in normalized_items[:limit]:
        lines.append(f"- {item}.")

    if len(normalized_items) > limit:
        lines.append("- Os demais pontos correlatos devem ser detalhados na versão final da minuta.")

    return "\n".join(lines)


def _build_missing_context_items(
    case_description: str,
    technical_summary: str,
    issues: list[str],
    next_steps: list[str],
    *,
    is_labor_case: bool = False,
) -> list[str]:
    missing: list[str] = []

    if len(case_description) < 80:
        if is_labor_case:
            missing.append(
                "detalhar fatos, período, jornada, vínculo, pedidos pretendidos e provas disponíveis no cadastro do caso"
            )
        else:
            missing.append(
                "detalhar fatos, período/cronologia, contexto do conflito, pedidos pretendidos e provas disponíveis no cadastro do caso"
            )
    if not technical_summary:
        missing.append("executar ou complementar a análise técnica do caso")
    if not issues:
        missing.append("explicitar controvérsias jurídicas e pontos críticos")
    if not next_steps:
        missing.append("registrar diligências, documentos e próximos passos relevantes")

    return missing


def _build_insufficient_content(
    block_title: str,
    missing_items: list[str],
    *,
    is_labor_case: bool = False,
) -> str:
    if is_labor_case:
        block_guidance = {
            "Resumo Fático": [
                "Faltam elementos para narrar os fatos trabalhistas com segurança.",
                "Complete datas, período, jornada, vínculo, contexto do conflito e provas disponíveis para este bloco.",
            ],
            "Fundamentação": [
                "Faltam elementos para sustentar a tese jurídica trabalhista com segurança.",
                "Complete controvérsia principal, violação legal, enquadramento jurídico, verbas discutidas e estratégia para este bloco.",
            ],
            "Pedidos": [
                "Faltam elementos para estruturar os pedidos trabalhistas com segurança.",
                "Complete pretensões principais, verbas buscadas, reflexos e requerimentos finais para este bloco.",
            ],
        }
    else:
        block_guidance = {
            "Resumo Fático": [
                "Faltam elementos para narrar os fatos cíveis com segurança.",
                "Complete datas, período/cronologia, contexto do conflito, relação jurídica e provas disponíveis para este bloco.",
            ],
            "Fundamentação": [
                "Faltam elementos para sustentar a tese jurídica cível com segurança.",
                "Complete controvérsia principal, obrigação discutida, violação contratual/legal, enquadramento jurídico e estratégia para este bloco.",
            ],
            "Pedidos": [
                "Faltam elementos para estruturar os pedidos cíveis com segurança.",
                "Complete pretensões principais, valor envolvido, encargos, provas e requerimentos finais para este bloco.",
            ],
        }

    guidance = block_guidance.get(
        block_title,
        [
            "Faltam elementos para montar este bloco com segurança.",
            "Complete o caso com informações materiais e estratégicas antes de gerar a peça assistida.",
        ],
    )

    base = [
        f"Dados insuficientes para montar automaticamente o bloco '{block_title}' com segurança.",
        guidance[0],
        guidance[1],
    ]

    if missing_items:
        base.append("Pendências mínimas identificadas:")
        base.extend([f"- {item}" for item in missing_items])

    return "\n".join(base)


def _normalize_role_token(value) -> str:
    raw = _safe_text(value).lower()
    if not raw:
        return ""
    return "".join(
        char for char in unicodedata.normalize("NFD", raw)
        if unicodedata.category(char) != "Mn"
    )


def _load_case_active_parties(db: Session, tenant_id: int, case_id: int) -> list[dict]:
    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == tenant_id,
            CasePartyStateModel.case_id == case_id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .first()
    )
    if not state:
        return []

    parties = (
        db.query(CasePartyModel)
        .filter(
            CasePartyModel.tenant_id == tenant_id,
            CasePartyModel.party_state_id == state.id,
            CasePartyModel.status == "active",
        )
        .order_by(CasePartyModel.is_original_party.desc(), CasePartyModel.id.asc())
        .all()
    )

    return [
        {
            "name": party.name,
            "role": party.role,
            "party_type": party.party_type,
            "document_id": party.document_id,
            "party_metadata": party.party_metadata or {},
        }
        for party in parties
    ]


def _load_case_state_metadata(db: Session, tenant_id: int, case_id: int) -> dict:
    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == tenant_id,
            CasePartyStateModel.case_id == case_id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .first()
    )
    if not state:
        return {}
    return dict(state.state_metadata or {})


def _select_primary_party(parties: list[dict], keywords: list[str]) -> dict | None:
    normalized_keywords = [_normalize_role_token(keyword) for keyword in keywords]

    for party in parties:
        role = _normalize_role_token(party.get("role"))
        role_tokens = set(role.split())

        for keyword in normalized_keywords:
            if not keyword:
                continue

            # PATCH: prevent_author_selected_as_defendant_v1
            # Termos curtos como "ré" normalizam para "re" e não podem bater
            # por substring dentro de palavras como "reclamante".
            if len(keyword) <= 2:
                if role == keyword or keyword in role_tokens:
                    return party
                continue

            if keyword in role:
                return party

    return None


def _format_party_inline_qualification(
    party: dict | None,
    fallback_name: str,
    *,
    default_is_company: bool = False,
) -> str:
    if not party:
        if default_is_company:
            return f"{fallback_name}, pessoa jurídica inscrita no CNPJ nº [CNPJ a complementar], com sede em [endereço completo]"
        return f"{fallback_name}, [nacionalidade], [estado civil], [profissão], inscrito(a) no CPF nº [CPF a complementar] e RG nº [RG a complementar], residente e domiciliado(a) em [endereço completo]"

    metadata = party.get("party_metadata") or {}
    raw_qualification = _safe_text(metadata.get("qualificacao"))
    if raw_qualification:
        return raw_qualification.rstrip(".")

    name = _safe_text(party.get("name")) or fallback_name
    document_id = (
        _safe_text(party.get("document_id"))
        or _safe_text(metadata.get("cpf"))
        or _safe_text(metadata.get("cnpj"))
    )
    address = (
        _safe_text(metadata.get("endereco"))
        or _safe_text(metadata.get("address"))
        or _safe_text(metadata.get("endereco_completo"))
        or _safe_text(metadata.get("residencia"))
        or "[endereço completo]"
    )

    normalized_party_type = _normalize_role_token(
        party.get("party_type") or metadata.get("party_type") or ""
    )
    digits = "".join(ch for ch in str(document_id) if ch.isdigit())
    is_company = default_is_company or normalized_party_type in {"company", "legal_entity", "pj", "empresa"} or len(digits) == 14

    if is_company:
        cnpj = document_id if document_id else "[CNPJ a complementar]"
        return f"{name}, pessoa jurídica inscrita no CNPJ nº {cnpj}, com sede em {address}"

    nationality = (
        _safe_text(metadata.get("nacionalidade"))
        or _safe_text(metadata.get("nationality"))
        or "[nacionalidade]"
    )
    civil_status = (
        _safe_text(metadata.get("estado_civil"))
        or _safe_text(metadata.get("estado civil"))
        or _safe_text(metadata.get("civil_status"))
        or "[estado civil]"
    )
    profession = (
        _safe_text(metadata.get("profissao"))
        or _safe_text(metadata.get("profissão"))
        or _safe_text(metadata.get("profession"))
        or _safe_text(metadata.get("occupation"))
        or "[profissão]"
    )

    cpf = document_id if document_id else "[CPF a complementar]"
    rg = _safe_text(metadata.get("rg")) or "[RG a complementar]"
    return f"{name}, {nationality}, {civil_status}, {profession}, inscrito(a) no CPF nº {cpf} e RG nº {rg}, residente e domiciliado(a) em {address}"


# PATCH: editor_extract_parties_from_description_v1
def _extract_labor_parties_from_case_description(case_description: str) -> list[dict]:
    """
    Extrai partes mínimas da descrição quando ainda não há CasePartyState estruturado.

    Não inventa CPF, CNPJ ou endereço completo. Apenas aproveita dados explícitos
    do texto do caso para reduzir placeholders na peça.
    """
    text = _safe_text(case_description)
    if not text:
        return []

    parties: list[dict] = []

    author_match = re.search(
        r"parte\s+reclamante\s*:\s*(?P<name>[^\n,\.]+)",
        text,
        flags=re.IGNORECASE,
    )
    profession_match = re.search(
        r"exercendo\s+a\s+fun[cç][aã]o\s+de\s+(?P<profession>[^,\n\.]+)",
        text,
        flags=re.IGNORECASE,
    )

    if author_match:
        author_name = author_match.group("name").strip(" .")
        profession = (
            profession_match.group("profession").strip(" .")
            if profession_match
            else ""
        )
        parties.append(
            {
                "name": author_name,
                "role": "reclamante",
                "party_type": "person",
                "document_id": "",
                "party_metadata": {
                    "profissao": profession or "[profissão]",
                    "qualificacao_source": "case_description_fallback",
                },
            }
        )

    defendant_match = re.search(
        r"parte\s+reclamada\s*:\s*(?P<raw>[^\n]+)",
        text,
        flags=re.IGNORECASE,
    )

    if defendant_match:
        raw_defendant = defendant_match.group("raw").strip(" .")
        defendant_name = raw_defendant
        address = "[endereço completo]"

        if "," in raw_defendant:
            first, rest = raw_defendant.split(",", 1)
            defendant_name = first.strip(" .")
            address_candidate = rest.strip(" .")
            if address_candidate:
                address = address_candidate

        parties.append(
            {
                "name": defendant_name,
                "role": "reclamada",
                "party_type": "company",
                "document_id": "",
                "party_metadata": {
                    "endereco": address,
                    "qualificacao_source": "case_description_fallback",
                },
            }
        )

    return parties


def _build_assisted_sections(
    db: Session,
    case: Case,
    analysis_record,
    tenant_id: int,
    document_metadata: dict | None = None,
) -> list[dict]:
    full_analysis = analysis_record.analysis or {}
    executive_data = analysis_record.executive_data or {}

    technical = full_analysis.get("technical", {}) if isinstance(full_analysis, dict) else {}
    strategic = full_analysis.get("strategic", {}) if isinstance(full_analysis, dict) else {}
    viability = executive_data.get("viability") or (
        full_analysis.get("viability", {}) if isinstance(full_analysis, dict) else {}
    )
    decision = executive_data.get("decision") or (
        full_analysis.get("decision", {}) if isinstance(full_analysis, dict) else {}
    )

    foundations = build_analysis_foundations(
        case={
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "legal_area": getattr(case, "legal_area", None),
            "action_type": getattr(case, "action_type", None),
        },
        technical=technical,
        viability=viability,
        decision=decision,
    )

    normative_basis = _string_list(foundations.get("normative_basis") if isinstance(foundations, dict) else [])
    factual_elements = _string_list(foundations.get("factual_elements_considered") if isinstance(foundations, dict) else [])
    probative_gaps = _string_list(foundations.get("probative_gaps") if isinstance(foundations, dict) else [])

    case_description = _safe_text(case.description)
    technical_summary = _safe_text(technical.get("summary") if isinstance(technical, dict) else "")
    issues = _string_list(technical.get("issues") if isinstance(technical, dict) else [])
    next_steps = _string_list(technical.get("next_steps") if isinstance(technical, dict) else [])
    recommended_strategy = _safe_text(
        strategic.get("recommended_strategy") if isinstance(strategic, dict) else ""
    )
    critical_points = _string_list(
        strategic.get("critical_points") if isinstance(strategic, dict) else []
    )
    viability_recommendation = _safe_text(
        viability.get("recommendation") if isinstance(viability, dict) else ""
    )
    executive_summary = _safe_text(
        decision.get("executive_summary") if isinstance(decision, dict) else ""
    )
    if executive_summary:
        import re as _re

        executive_summary = _re.sub(
            r",?\s*com probabilidade estimada de êxito em\s+\d+%\.?",
            ".",
            executive_summary,
            flags=_re.IGNORECASE,
        )
        executive_summary = _re.sub(
            r"probabilidade estimada\s*:?\s*\d+%\.?",
            "avaliação qualitativa, sem previsão percentual de resultado judicial.",
            executive_summary,
            flags=_re.IGNORECASE,
        )
        executive_summary = executive_summary.replace("..", ".").strip()

    final_status = _safe_text(decision.get("final_status") if isinstance(decision, dict) else "")
    normalized_area = str(getattr(case, "legal_area", "") or "").strip().lower()
    normalized_action_type = str(getattr(case, "action_type", "") or "").strip().lower()
    case_search_text = " ".join(
        [
            str(getattr(case, "title", "") or ""),
            str(getattr(case, "description", "") or ""),
            normalized_action_type,
        ]
    ).lower()
    is_civil_ambiental = normalized_area == "civil_ambiental"
    is_civel_area = normalized_area in {"civel", "civil_ambiental"}
    is_trabalhista_area = normalized_area in {"trabalhista", "trabalho", "laboral"}
    is_criminal_area = normalized_area in {"criminal", "penal"}
    is_civel_cobranca = is_civel_area and any(
        marker in case_search_text
        for marker in ["cobran", "inadimpl", "dívida", "divida", "saldo contratual", "contrato de prestação"]
    )
    is_trabalhista_insalubridade_periculosidade = is_trabalhista_area and any(
        marker in case_search_text
        for marker in [
            "insalubr",
            "periculos",
            "calor",
            "fusão",
            "fusao",
            "metal em fusão",
            "metal em fusao",
            "epi",
            "ppp",
            "ltcat",
            "pgr",
            "pcmso",
        ]
    )
    controverted_points = list(dict.fromkeys([item for item in [*issues, *critical_points] if item]))
    proof_checklist = list(dict.fromkeys([item for item in [*probative_gaps, *next_steps] if item]))

    if is_civel_cobranca:
        cleaned_proof_checklist = []
        for item in proof_checklist:
            item_text = str(item or "").strip()
            item_lower = item_text.lower()

            if "persistência da conduta" in item_lower:
                cleaned_proof_checklist.append(
                    "Necessidade de cronologia objetiva dos vencimentos, pagamentos realizados, mora, tentativas de cobrança e saldo atualizado."
                )
                continue

            if any(
                forbidden in item_lower
                for forbidden in [
                    "ambiental",
                    "acústica",
                    "acustica",
                    "mitigação",
                    "mitigacao",
                    "obrigação de fazer",
                    "obrigacao de fazer",
                    "não fazer",
                    "nao fazer",
                    "impactos narrados",
                    "reiteração dos impactos",
                ]
            ):
                continue

            cleaned_proof_checklist.append(item_text)

        proof_checklist = list(dict.fromkeys([item for item in cleaned_proof_checklist if item]))


    is_trabalhista_verbas_rescisorias = is_trabalhista_area and (
        any(
            term in case_search_text
            for term in [
                "verbas rescisórias",
                "verbas rescisorias",
                "dispensa sem justa causa",
                "saldo de salário",
                "saldo de salario",
                "aviso-prévio",
                "aviso previo",
                "aviso prévio",
                "13º salário",
                "13o salario",
                "art. 477",
                "art. 467",
            ]
        )
        or (
            ("rescisão" in case_search_text or "rescisao" in case_search_text)
            and any(
                term in case_search_text
                for term in [
                    "saldo de salário",
                    "saldo de salario",
                    "aviso-prévio",
                    "aviso previo",
                    "férias proporcionais",
                    "ferias proporcionais",
                    "13º salário",
                    "13o salario",
                ]
            )
        )
    )

    is_trabalhista_horas_extras = is_trabalhista_area and any(
        term in case_search_text
        for term in [
            "horas extras",
            "hora extra",
            "jornada excedente",
            "jornada superior",
            "jornada habitual",
            "intervalo intrajornada",
            "intervalo reduzido",
            "intervalo irregular",
            "controle de ponto",
            "controles de ponto",
            "cartão de ponto",
            "cartao de ponto",
            "cartões de ponto",
            "cartoes de ponto",
            "dsr",
            "descanso semanal remunerado",
            "adicional de horas extras",
            "escala de trabalho",
            "escalas de trabalho",
        ]
    )


    is_trabalhista_fgts_nao_recolhido = is_trabalhista_area and any(
        term in case_search_text
        for term in [
            "fgts não recolhido",
            "fgts nao recolhido",
            "depósitos de fgts",
            "depositos de fgts",
            "depósitos mensais de fgts",
            "depositos mensais de fgts",
            "depósitos parciais",
            "depositos parciais",
            "depósitos irregulares",
            "depositos irregulares",
            "ausência de depósitos",
            "ausencia de depositos",
            "extrato analítico do fgts",
            "extrato analitico do fgts",
            "extrato do fgts",
            "conta vinculada",
            "saldo fundiário",
            "saldo fundiario",
            "regularização de depósitos",
            "regularizacao de depositos",
            "diferenças de fgts",
            "diferencas de fgts",
            "gfip",
            "sefip",
            "esocial",
            "recolhimento de fgts",
        ]
    )

    if is_trabalhista_insalubridade_periculosidade:
        labor_proof_checklist = []
        for item in proof_checklist:
            item_text = str(item or "").strip()
            item_lower = item_text.lower()

            if "laudo/relatório médico" in item_lower or "relatório médico" in item_lower:
                labor_proof_checklist.append(
                    "Necessidade de prova técnica ambiental/pericial para aferir exposição a calor, proximidade com metal em fusão, condições do setor de fusão e eventual neutralização por EPI."
                )
                continue

            if "persistência da conduta" in item_lower:
                labor_proof_checklist.append(
                    "Necessidade de confirmação da rotina real de trabalho, frequência da exposição, distância da fonte de calor, EPIs fornecidos e eficácia da proteção."
                )
                continue

            labor_proof_checklist.append(item_text)

        labor_proof_checklist.extend(
            [
                "Necessidade de obtenção e análise de PPP, LTCAT, PGR, PCMSO, mapa de riscos e ficha de entrega de EPI.",
                "Necessidade de cálculo trabalhista preliminar considerando adicional de insalubridade em grau eventualmente apurado, ou periculosidade de forma subsidiária, com reflexos em férias + 1/3, 13º salário, FGTS e demais verbas cabíveis.",
            ]
        )
        proof_checklist = list(dict.fromkeys([item for item in labor_proof_checklist if item]))

    active_parties = _load_case_active_parties(db, tenant_id, case.id)
    state_metadata = _load_case_state_metadata(db, tenant_id, case.id)
    # PATCH: pass_document_metadata_to_assisted_sections_v1
    # Dados do documento aprovado/atual entram como complemento para cálculo e fechamento da peça.
    if isinstance(document_metadata, dict) and document_metadata:
        state_metadata = {
            **state_metadata,
            **document_metadata,
        }

    case_comarca = _safe_text(state_metadata.get("case_comarca")) or "[COMARCA A DEFINIR PELO ADVOGADO]"
    cause_value = _safe_text(state_metadata.get("cause_value")) or "[valor a ser definido pelo advogado]"
    pedidos_valores_estimados = _build_default_claim_values_section(cause_value)
    lawyer_name = _safe_text(state_metadata.get("lawyer_name")) or "[Nome do advogado]"
    lawyer_oab = _safe_text(state_metadata.get("lawyer_oab")) or "[número]"
    lawyer_uf = _safe_text(state_metadata.get("lawyer_uf")) or "[UF]"
    signature_local = _safe_text(state_metadata.get("signature_local")) or "[Local]"
    signature_date = _safe_text(state_metadata.get("signature_date")) or "[data]"

    normalized_area_text = f"{normalized_area}".lower()
    is_labor_case = (
        is_trabalhista_area
        or is_trabalhista_insalubridade_periculosidade
        or "trabalh" in normalized_area_text
        or "reclamação trabalhista" in case_search_text
        or "reclamacao trabalhista" in case_search_text
        or "vara do trabalho" in case_search_text
        or "adicional de insalubridade" in case_search_text
        or "adicional de periculosidade" in case_search_text
        or "verbas rescisórias" in case_search_text
        or "verbas rescisorias" in case_search_text
        or "dispensa sem justa causa" in case_search_text
        or "multa de 40" in case_search_text
        or "trct" in case_search_text
        or "horas extras" in case_search_text
        or "jornada excedente" in case_search_text
        or "intervalo intrajornada" in case_search_text
        or "controle de ponto" in case_search_text
        or "fgts não recolhido" in case_search_text
        or "fgts nao recolhido" in case_search_text
        or "extrato analítico do fgts" in case_search_text
        or "extrato analitico do fgts" in case_search_text
        or "depósitos de fgts" in case_search_text
        or "depositos de fgts" in case_search_text
        or "conta vinculada" in case_search_text
        or ("reclamante" in case_search_text and "reclamada" in case_search_text)
    )

    active_parties = _load_case_active_parties(db, tenant_id, case.id)
    if not active_parties:
        active_parties = _extract_labor_parties_from_case_description(case_description)

    author_party = _select_primary_party(
        active_parties,
        ["autor", "autora", "parte autora", "requerente", "demandante", "reclamante", "impetrante"],
    )
    defendant_party = _select_primary_party(
        active_parties,
        ["reu", "ré", "réu", "parte re", "parte ré", "requerido", "demandado", "reclamada", "impetrado"],
    )

    if author_party is None and active_parties:
        author_party = active_parties[0]

    if defendant_party is None or defendant_party is author_party:
        defendant_party = next((party for party in active_parties if party is not author_party), None)

    author_inline_qualification = _format_party_inline_qualification(
        author_party,
        "[NOME COMPLETO DA PARTE AUTORA]",
    )
    defendant_inline_qualification = _format_party_inline_qualification(
        defendant_party,
        "[NOME/RAZÃO SOCIAL DA PARTE RÉ]",
        default_is_company=True,
    )

    missing_items = _build_missing_context_items(
        case_description=case_description,
        technical_summary=technical_summary,
        issues=issues,
        next_steps=next_steps,
        is_labor_case=is_labor_case,
    )

    insufficient_context = (
        len(case_description) < 80
        or not technical_summary
        or "apenas identificador" in f"{case_description} {technical_summary}".lower()
        or "dados insuficientes" in f"{case_description} {technical_summary}".lower()
        or (len(case_description) < 140 and len(proof_checklist) >= 2)
    )

    if insufficient_context:
        return [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": _build_insufficient_content("Resumo Fático", missing_items, is_labor_case=is_labor_case),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["case", "technical_analysis"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
                },
            },
            {
                "key": "fundamentacao",
                "title": "Fundamentação",
                "content": _build_insufficient_content("Fundamentação", missing_items, is_labor_case=is_labor_case),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["technical_analysis", "strategic_analysis", "viability"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
                },
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
                "content": _build_insufficient_content("Pedidos", missing_items, is_labor_case=is_labor_case),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["decision", "viability", "technical_analysis"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
                },
            },
        ]

    resumo_fatico = _paragraphs(
        [
            f"Trata-se do caso {case.case_number} — {case.title}.",
            case_description,
            (
                "A narrativa fática acima deverá ser revisada e completada, na versão final, com datas, períodos, documentos e demais elementos concretos já disponíveis no caso."
                if len(case_description) < 220
                else ""
            ),
        ]
    )

    fundamentacao = _paragraphs(
        [
            (
                "I. Do cabimento da pretensão. À luz do quadro fático descrito, a demanda deve ser estruturada como ação de cobrança contratual, voltada à condenação da parte ré ao pagamento do saldo inadimplido, com os encargos contratuais e legais cabíveis."
                if is_civel_cobranca
                else (
                    "I. Do cabimento da pretensão. À luz do quadro fático descrito, a demanda deve ser estruturada para cessar a lesão narrada, recompor o status jurídico violado e prevenir a reiteração dos impactos ao direito material discutido."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "I. Do cabimento da pretensão. À luz do quadro fático narrado, a demanda deve ser estruturada para tutelar o direito material afirmado e enfrentar a controvérsia central com base na prova já disponível."
                )
            ),
            (
                "II. Dos fundamentos jurídicos da cobrança. A pretensão deve se apoiar na existência de relação contratual, no cumprimento da prestação pela parte autora, no inadimplemento das parcelas vencidas pela parte ré, na mora e na responsabilidade pelo pagamento do principal, multa, juros, correção monetária, custas e honorários."
                if is_civel_cobranca
                else _series_block("II. Dos fundamentos normativos aplicáveis:", normative_basis, limit=5)
            ),
            (
                f"III. Da estratégia jurídica sugerida. {recommended_strategy}"
                if recommended_strategy
                else "III. Da estratégia jurídica sugerida. A condução da tese deve priorizar coerência entre narrativa fática, prova disponível, pedido principal e tutela pretendida."
            ),
            _series_block("IV. Dos pontos controvertidos que exigem enfrentamento direto:", controverted_points, limit=5),
            _series_block("V. Das lacunas probatórias a suprir antes do protocolo definitivo:", proof_checklist, limit=5),
            (
                f"VI. Da síntese conclusiva considerada na redação. {executive_summary}"
                if executive_summary and "dados insuficientes" not in executive_summary.lower()
                else ""
            ),
        ]
    )

    pedidos = _paragraphs(
        [
            (
                "I. Requer-se a citação da parte ré para, querendo, apresentar contestação, sob pena de revelia e confissão quanto à matéria de fato."
                if is_civel_cobranca
                else (
                    "I. Requer-se, em tutela provisória de urgência, quando presentes os requisitos legais, a imediata cessação, redução ou mitigação dos impactos narrados, inclusive por obrigação de fazer e/ou não fazer."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "I. Requer-se, quando presentes os requisitos legais, a concessão da tutela provisória cabível para resguardar desde logo a utilidade do provimento final."
                )
            ),
            (
                "II. Requer-se a condenação da parte ré ao pagamento do saldo contratual inadimplido, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios."
                if is_civel_cobranca
                else _series_block("II. Pedidos principais sugeridos para a minuta final:", issues, limit=5)
            ),
            (
                "III. Requer-se que os encargos de mora sejam calculados a partir do vencimento de cada parcela inadimplida, observando-se a cláusula contratual aplicável e a planilha de cálculo a ser juntada na versão final."
                if is_civel_cobranca
                else (
                    "III. Requer-se, ao final, a procedência dos pedidos principais, com imposição das obrigações materiais compatíveis com a narrativa, a prova produzida e a extensão do dano demonstrado."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "III. Requer-se, ao final, a procedência dos pedidos compatíveis com os fatos narrados, a tese sustentada e a prova disponível."
                )
            ),
            (
                "IV. Requer-se a produção de prova documental suplementar, testemunhal e demais meios de prova em direito admitidos, especialmente contrato, comprovantes de pagamento, relatório técnico, fotografias, mensagens, notificação extrajudicial, e-mails e planilha de cálculo."
                if is_civel_cobranca
                else "IV. Requer-se, ainda, a citação da parte ré, a produção de prova documental, testemunhal e pericial, bem como os requerimentos acessórios pertinentes ao rito e à estratégia processual adotada."
            ),
            (
                "V. Requer-se a condenação da parte ré ao pagamento das custas processuais e honorários advocatícios, nos termos da legislação processual aplicável."
                if is_civel_cobranca
                else (
                    f"V. O enquadramento provisório da análise indica a seguinte diretriz para fechamento dos pedidos: {final_status}."
                    if final_status and "dados insuficientes" not in final_status.lower()
                    else ""
                )
            ),
            (
                "VI. Antes do protocolo definitivo, o advogado deverá revisar valor da causa, memória de cálculo, índice de correção monetária, competência territorial e documentos comprobatórios do inadimplemento."
                if is_civel_cobranca
                else "VI. Antes do protocolo definitivo, o advogado deverá revisar a aderência entre pedidos, causa de pedir, prova disponível, tutela de urgência e liquidez dos danos postulados."
            ),
        ]
    )

    enderecamento = _paragraphs(
        [
            (
                f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DE UMA DAS VARAS CÍVEIS DA COMARCA DE {case_comarca}."
                if normalized_area in {"civel", "civil_ambiental"}
                else f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DO JUÍZO COMPETENTE DA COMARCA DE {case_comarca}."
            ),
            "Na versão final, o advogado deverá confirmar a competência territorial, o órgão jurisdicional, eventual prevenção e o rito adequado antes do protocolo.",
        ]
    )

    qualificacao_partes = _paragraphs(
        [
            f"{author_inline_qualification}, por seu advogado, vem, respeitosamente, à presença de Vossa Excelência, propor a presente demanda em face de {defendant_inline_qualification}.",
            "Na revisão final, deverão ser confirmados os dados completos de qualificação, a legitimidade ativa e passiva, a existência de representantes, sucessores, litisconsortes e demais elementos subjetivos relevantes ao caso.",
            "Se houver representantes, espólio, sucessores, litisconsórcio ou pessoa jurídica no polo passivo, complementar a qualificação com os dados formais constantes dos documentos do caso.",
        ]
    )

    provas_requerimentos = _paragraphs(
        [
            "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial, conforme a natureza das controvérsias identificadas.",
            (
                "Na versão final, devem ser especificados e anexados os documentos de cobrança: contrato assinado, comprovante de pagamento parcial, relatório de execução dos serviços, fotografias, mensagens de reconhecimento da dívida, notificação extrajudicial, e-mails e planilha de cálculo atualizada."
                if is_civel_cobranca
                else (
                    "Na versão final, devem ser especificados os documentos já existentes, a necessidade de prova técnica ambiental/acústica, eventual inspeção judicial e o fundamento da tutela de urgência."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "Na versão final, devem ser especificados os documentos já existentes, a prova técnica pertinente e os requerimentos probatórios adequados ao caso."
                )
            ),
            (
                "Também devem ser ajustados os requerimentos acessórios, especialmente valor da causa, memória de cálculo, índice de correção monetária, comprovação de mora e eventual tentativa extrajudicial de composição."
                if is_civel_cobranca
                else "Também devem ser ajustados os requerimentos acessórios, a intimação da parte contrária e as providências processuais cabíveis ao rito escolhido."
            ),
        ]
    )

    fechamento = _paragraphs(
        [
            "Ante o exposto, requer o regular processamento da presente demanda e, ao final, o acolhimento dos pedidos formulados, nos limites da narrativa fática, da prova produzida e da estratégia jurídica consolidada na versão final da peça.",
            "Protesta por todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial, sem prejuízo de outros que se tornem necessários no curso da instrução.",
            f"Dá-se à causa o valor de R$ {cause_value}, sujeito a ajuste conforme os critérios legais aplicáveis e a consolidação definitiva dos pedidos.",
            "Termos em que, pede deferimento.",
            f"{signature_local}, {signature_date}.",
            f"{lawyer_name} — OAB/{lawyer_uf} {lawyer_oab}.",
        ]
    )

    if is_civil_ambiental:
        import re

        def _first_match(patterns: list[str]) -> str:
            for pattern in patterns:
                match = re.search(pattern, case_description, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
                if match:
                    return _safe_text(match.group(1)).strip().rstrip(".;:")
            return ""

        civil_amb_comarca = case_comarca
        if civil_amb_comarca.startswith("[") and ("itapoá" in case_search_text or "itapoa" in case_search_text):
            civil_amb_comarca = "ITAPOÁ/SC"

        civil_amb_author_name = _first_match([
            r"\bA autora\s+(.+?)\s+reside\b",
            r"\bO autor\s+(.+?)\s+reside\b",
            r"^\s*Autora?\s*:\s*(.+?)\s*$",
            r"^\s*Autor\s*:\s*(.+?)\s*$",
        ])

        civil_amb_defendant_name = _first_match([
            r"ao lado da empresa\s+(.+?),\s+que\s+explora",
            r"ao lado da empresa\s+(.+?)\s*,",
            r"^\s*R[ée]u\s*:\s*(.+?)\s*$",
            r"^\s*Parte ré\s*:\s*(.+?)\s*$",
        ])

        if civil_amb_author_name:
            author_inline_qualification = (
                f"{civil_amb_author_name.upper()}, [nacionalidade], [estado civil], [profissão], "
                "inscrita no CPF nº [CPF a complementar] e RG nº [RG a complementar], "
                "residente e domiciliada em [endereço completo a complementar]"
            )

        if civil_amb_defendant_name:
            defendant_inline_qualification = (
                f"{civil_amb_defendant_name.upper()}, pessoa jurídica de direito privado, "
                "inscrita no CNPJ sob nº [CNPJ a complementar], com sede em [endereço completo a complementar]"
            )

        civil_amb_signature_local = (
            civil_amb_comarca.replace("/Sc", "/SC").replace("/sc", "/SC").title().replace("/Sc", "/SC")
            if not civil_amb_comarca.startswith("[")
            else "[local a definir]"
        )

        enderecamento = _paragraphs([
            f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA CÍVEL DA COMARCA DE {civil_amb_comarca}.",
        ])

        qualificacao_partes = _paragraphs([
            (
                f"{author_inline_qualification}, por seu advogado infra-assinado, vem, respeitosamente, "
                "à presença de Vossa Excelência, propor a presente "
                "AÇÃO DE OBRIGAÇÃO DE FAZER E/OU NÃO FAZER C/C PEDIDO DE TUTELA DE URGÊNCIA "
                f"E INDENIZAÇÃO POR DANOS MORAIS E MATERIAIS em face de {defendant_inline_qualification}, "
                "pelos fatos e fundamentos a seguir expostos."
            )
        ])

        resumo_fatico = _paragraphs([
            case_description.strip(),
            (
                "A situação narrada indica uso potencialmente anormal da propriedade vizinha, com impactos "
                "continuados ao sossego, à saúde, à segurança e ao uso regular do imóvel residencial da parte autora, "
                "justificando a apreciação urgente das medidas de contenção e cessação dos danos."
            ),
        ])

        fundamentacao = _paragraphs([
            "I. DO USO ANORMAL DA PROPRIEDADE E DO DIREITO DE VIZINHANÇA",
            (
                "A controvérsia decorre da emissão de poeira de cimento, ruído contínuo, vibração diária, "
                "obstrução da via e ausência de barreira física adequada entre o imóvel residencial da autora "
                "e a atividade industrial exercida pela ré."
            ),
            (
                "Nos termos do art. 1.277 do Código Civil, o proprietário ou possuidor tem direito de fazer cessar "
                "interferências prejudiciais à segurança, ao sossego e à saúde dos que habitam o imóvel, quando "
                "decorrentes da utilização anormal da propriedade vizinha."
            ),
            "II. DA RESPONSABILIDADE CIVIL E DA PROTEÇÃO À SAÚDE",
            (
                "A persistência de poeira, ruído e vibração, especialmente em imóvel ocupado por pessoa idosa com "
                "problemas pulmonares, pode configurar conduta lesiva apta a gerar obrigação de cessação, mitigação, "
                "reparação e prevenção de novos danos, observados os arts. 186, 187 e 927 do Código Civil."
            ),
            (
                "A proteção ao meio ambiente equilibrado e à saúde também encontra amparo no art. 225 da Constituição "
                "Federal, sem prejuízo da incidência das normas de proteção reforçada à pessoa idosa, quando demonstrada "
                "situação de vulnerabilidade e risco agravado."
            ),
            "III. DA TUTELA DE URGÊNCIA",
            (
                "A tutela de urgência mostra-se juridicamente pertinente quando houver elementos que indiquem a "
                "probabilidade do direito e o perigo de dano ou risco ao resultado útil do processo, especialmente "
                "diante de impactos contínuos à saúde, ao repouso e ao uso regular da residência."
            ),
            (
                "A medida urgente poderá abranger providências de contenção de poeira, redução de ruído e vibração, "
                "instalação de barreira física, desobstrução da via e abstenção de práticas que agravem os impactos "
                "narrados, sem prejuízo de fiscalização e multa diária em caso de descumprimento."
            ),
            "IV. DA NECESSIDADE DE PROVA TÉCNICA E DOCUMENTAL",
            (
                "A prova documental, fotográfica, audiovisual, testemunhal, médica e pericial é relevante para demonstrar "
                "a extensão dos impactos, o nexo com a atividade da ré, a urgência das medidas e a existência de danos "
                "morais e materiais eventualmente indenizáveis."
            ),
        ])

        pedidos = _paragraphs([
            "I. Requer-se a citação da parte ré para, querendo, apresentar contestação, sob pena de revelia e confissão quanto à matéria de fato.",
            (
                "II. Requer-se, em tutela de urgência, que a parte ré seja obrigada a adotar medidas imediatas para "
                "cessar ou reduzir a emissão de poeira, ruído e vibração, bem como impedir a obstrução da via e demais "
                "práticas que agravem o uso anormal da propriedade vizinha."
            ),
            (
                "III. Requer-se que a parte ré seja compelida a instalar barreira física, muro, contenção ou outro meio "
                "tecnicamente adequado para reduzir os impactos da atividade industrial sobre o imóvel da autora, conforme "
                "definição técnica a ser confirmada nos autos."
            ),
            (
                "IV. Requer-se a fixação de multa diária para o caso de descumprimento das obrigações impostas, nos termos "
                "dos arts. 497 e 537 do Código de Processo Civil."
            ),
            (
                "V. Requer-se, ao final, a confirmação da tutela e a condenação da parte ré em obrigação de fazer e/ou "
                "não fazer, com adoção permanente das medidas necessárias para cessar ou mitigar os impactos narrados."
            ),
            (
                "VI. Requer-se a condenação da parte ré ao pagamento de indenização por danos morais e, se comprovados, "
                "danos materiais, em valor a ser definido pelo advogado responsável e/ou arbitrado por Vossa Excelência."
            ),
            (
                "VII. Requer-se a produção de prova documental suplementar, testemunhal, pericial ambiental/acústica, "
                "perícia de engenharia, inspeção judicial e demais meios de prova admitidos em direito."
            ),
            "VIII. Requer-se a condenação da parte ré ao pagamento das custas processuais e honorários advocatícios.",
        ])

        pedidos_valores_estimados = _paragraphs([
            (
                "O valor da causa deverá ser definido pelo advogado responsável antes do protocolo, considerando "
                "a obrigação de fazer/não fazer, eventual tutela de urgência, danos morais, danos materiais e critérios "
                "processuais aplicáveis."
            ),
            f"Valor da causa atualmente informado: R$ {cause_value}.",
        ])

        provas_requerimentos = _paragraphs([
            (
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documentos, fotos, "
                "vídeos, testemunhas, notificação extrajudicial, documentos médicos, prova pericial ambiental/acústica, "
                "perícia de engenharia e eventual inspeção judicial."
            ),
            (
                "Deverão ser juntados, conforme disponibilidade, registros datados da poeira, ruído, vibração, obstrução "
                "da via, ausência de barreira, comunicações extrajudiciais, comprovantes de recebimento da notificação, "
                "documentos médicos e identificação de testemunhas."
            ),
        ])

        fechamento = _paragraphs([
            (
                "Ante o exposto, requer o regular processamento da presente ação e, ao final, a procedência dos pedidos, "
                "com a condenação da parte ré ao cumprimento das obrigações de fazer e/ou não fazer necessárias à cessação "
                "ou mitigação dos impactos narrados."
            ),
            (
                "Requer-se, ainda, a confirmação das medidas urgentes eventualmente deferidas, a fixação de multa diária "
                "em caso de descumprimento, a produção das provas requeridas e a condenação da parte ré ao pagamento das "
                "verbas indenizatórias cabíveis, custas e honorários."
            ),
            f"Dá-se à causa, para fins fiscais e processuais, o valor de R$ {cause_value}, sujeito à revisão do advogado responsável antes do protocolo.",
            "Termos em que, pede deferimento.",
            f"{civil_amb_signature_local}, {signature_date}.",
            f"{lawyer_name} — OAB/{lawyer_uf} {lawyer_oab}.",
        ])

    if is_civel_cobranca:
        import re

        civil_case_comarca = case_comarca
        if civil_case_comarca.startswith("[") and ("itapoá" in case_search_text or "itapoa" in case_search_text):
            civil_case_comarca = "ITAPOÁ/SC"

        def _parse_brl_amount(value: str) -> float:
            return float(value.replace(".", "").replace(",", "."))

        def _format_brl_amount(value: float) -> str:
            formatted = f"{value:,.2f}"
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

        civil_cause_value = cause_value
        if civil_cause_value.startswith("["):
            cause_match = re.search(
                r"(?:saldo principal|d[ií]vida principal|valor principal)(?:[^R]{0,120})R\$\s*([\d\.\,]+)",
                case_description,
                flags=re.IGNORECASE,
            )
            if not cause_match:
                cause_match = re.search(
                    r"principal de R\$\s*([\d\.\,]+)",
                    case_description,
                    flags=re.IGNORECASE,
                )
            if cause_match:
                civil_cause_value = cause_match.group(1).strip().rstrip(".;:")
            else:
                open_marker_match = re.search(
                    r"(?:permaneceram em aberto|parcelas? em aberto|saldo em aberto)",
                    case_description,
                    flags=re.IGNORECASE,
                )
                if open_marker_match:
                    open_window = case_description[
                        open_marker_match.start() : open_marker_match.start() + 450
                    ]
                    installment_values = re.findall(
                        r"R\$\s*([\d]{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})",
                        open_window,
                        flags=re.IGNORECASE,
                    )
                    if installment_values:
                        total = sum(_parse_brl_amount(item) for item in installment_values)
                        civil_cause_value = _format_brl_amount(total)

        company_match = re.search(
            r"A empresa\s+(.+?)\s+foi contratada pela empresa\s+(.+?)\s+para",
            case_description,
            flags=re.IGNORECASE | re.DOTALL,
        )
        structured_author_match = re.search(
            r"^\s*Autor(?:a)?\s*:\s*(.+?)\s*$",
            case_description,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        structured_defendant_match = re.search(
            r"^\s*R[ée]u\s*:\s*(.+?)\s*$",
            case_description,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        civil_author_name = ""
        civil_defendant_name = ""

        if company_match:
            civil_author_name = _safe_text(company_match.group(1))
            civil_defendant_name = _safe_text(company_match.group(2))
        elif structured_author_match or structured_defendant_match:
            civil_author_name = _safe_text(structured_author_match.group(1)) if structured_author_match else ""
            civil_defendant_name = _safe_text(structured_defendant_match.group(1)) if structured_defendant_match else ""

        civil_author_name = civil_author_name.strip().rstrip(".;:")
        civil_defendant_name = civil_defendant_name.strip().rstrip(".;:")

        if civil_author_name:
            author_inline_qualification = (
                f"{civil_author_name.upper()}, pessoa jurídica de direito privado, "
                "inscrita no CNPJ sob nº [CNPJ a complementar], com sede em [endereço completo a complementar], "
                "neste ato representada na forma de seu contrato social"
            )
        if civil_defendant_name:
            defendant_inline_qualification = (
                f"{civil_defendant_name.upper()}, pessoa jurídica de direito privado, "
                "inscrita no CNPJ sob nº [CNPJ a complementar], com sede em [endereço completo a complementar]"
            )

        civil_summary = case_description.strip()
        for marker in ("Documentos disponíveis:", "Pedido pretendido:", "Observação estratégica:"):
            idx = civil_summary.lower().find(marker.lower())
            if idx >= 0:
                civil_summary = civil_summary[:idx].strip()
                break

        resumo_fatico = _paragraphs(
            [
                civil_summary,
                "Diante do inadimplemento contratual e da ausência de solução extrajudicial, a presente ação busca a condenação da parte ré ao pagamento do saldo contratual devido, acrescido dos encargos contratuais e legais cabíveis, além de custas processuais e honorários advocatícios.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. DA RELAÇÃO CONTRATUAL E DO CUMPRIMENTO DA OBRIGAÇÃO PELA AUTORA",
                "Conforme demonstram os documentos que instruem a presente demanda, a parte autora foi contratada pela parte ré para a execução dos serviços contratados descritos na narrativa fática e comprovados pelos documentos do caso.",
                "A autora cumpriu integralmente a obrigação assumida, executando os serviços contratados, com emissão de relatório técnico de conclusão, fotografias do serviço realizado e demais documentos comprobatórios da efetiva prestação dos serviços.",
                "Além disso, a própria ré efetuou o pagamento da primeira parcela contratual, o que reforça a existência da relação jurídica, a validade do ajuste firmado entre as partes e o início regular da execução contratual.",
                "II. DO INADIMPLEMENTO CONTRATUAL DA RÉ",
                "Embora a autora tenha cumprido sua obrigação contratual, a ré deixou de pagar as parcelas finais ajustadas, totalizando saldo principal inadimplido indicado na documentação do caso.",
                "A inadimplência permaneceu mesmo após tentativas extrajudiciais de solução. A ré reconheceu a existência da dívida por mensagens de WhatsApp e, posteriormente, mesmo notificada, não realizou a quitação do débito nem apresentou proposta formal de acordo.",
                "III. DA MORA E DOS ENCARGOS CONTRATUAIS E LEGAIS",
                "O inadimplemento das parcelas vencidas colocou a ré em mora, tornando exigível o pagamento do saldo contratual em aberto, acrescido dos encargos previstos no contrato e dos consectários legais cabíveis.",
                f"O débito principal corresponde a R$ {civil_cause_value}, sem prejuízo da incidência de multa contratual, juros de mora e correção monetária, conforme previsão contratual e memória de cálculo a ser atualizada até a data do ajuizamento.",
                "Assim, a ré deve responder pelo pagamento do valor principal, acrescido de multa, juros, atualização monetária, custas processuais e honorários advocatícios, em razão do descumprimento da obrigação assumida.",
                "IV. DA PROVA DOCUMENTAL DO DÉBITO",
                "A pretensão da autora está amparada por conjunto probatório documental robusto, composto por contrato de prestação de serviços assinado pelas partes, comprovante de pagamento parcial, relatório técnico de execução, fotografias do serviço concluído, conversas de WhatsApp com reconhecimento da dívida, notificação extrajudicial, e-mails trocados entre as empresas e planilha de cálculo.",
                "Tais documentos demonstram a existência da contratação, a efetiva execução dos serviços, o pagamento parcial, o inadimplemento das parcelas finais e a tentativa extrajudicial de recebimento do crédito.",
                "Eventual alegação defensiva de vício no serviço, compensação ou discordância quanto à execução deverá ser comprovada pela ré, pois a documentação disponível indica que os serviços foram concluídos e que a dívida foi posteriormente reconhecida.",
                "V. DO CABIMENTO DA AÇÃO DE COBRANÇA",
                "Diante da existência de relação contratual, da execução dos serviços pela autora e do inadimplemento da ré, é cabível a presente ação de cobrança, com o objetivo de obter a condenação da parte ré ao pagamento do saldo contratual inadimplido.",
                f"A demanda busca o recebimento do valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios, nos termos do contrato, da legislação civil aplicável e da prova documental juntada aos autos.",
            ]
        )

        pedidos = _paragraphs(
            [
                "I. Requer-se a citação da parte ré para, querendo, apresentar contestação, sob pena de revelia e confissão quanto à matéria de fato.",
                f"II. Requer-se a condenação da parte ré ao pagamento do saldo contratual inadimplido no valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios.",
                "III. Requer-se que os encargos de mora sejam calculados a partir do vencimento de cada parcela inadimplida, observando-se a cláusula contratual aplicável e a planilha de cálculo a ser juntada aos autos.",
                "IV. Requer-se a produção de prova documental suplementar, testemunhal e demais meios de prova em direito admitidos, especialmente contrato, comprovantes de pagamento, relatório técnico, fotografias, mensagens, notificação extrajudicial, e-mails e planilha de cálculo.",
                "V. Requer-se a condenação da parte ré ao pagamento das custas processuais e honorários advocatícios, nos termos da legislação processual aplicável.",
            ]
        )

        civil_has_defined_comarca = not civil_case_comarca.startswith("[")
        civil_enderecamento_text = (
            f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA CÍVEL DA COMARCA DE {civil_case_comarca}."
            if civil_has_defined_comarca
            else "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA CÍVEL DA COMARCA COMPETENTE."
        )
        civil_signature_local = (
            civil_case_comarca.replace("/Sc", "/SC").replace("/sc", "/SC").title().replace("/Sc", "/SC")
            if civil_has_defined_comarca
            else "[local a definir]"
        )

        enderecamento = _paragraphs(
            [
                civil_enderecamento_text,
            ]
        )

        qualificacao_partes = _paragraphs(
            [
                f"{author_inline_qualification}, por seu advogado infra-assinado, vem, respeitosamente, à presença de Vossa Excelência, propor a presente AÇÃO DE COBRANÇA em face de {defendant_inline_qualification}, pelos fatos e fundamentos a seguir expostos.",
            ]
        )

        pedidos_valores_estimados = _paragraphs(
            [
                f"O valor principal inadimplido corresponde a R$ {civil_cause_value}, referente ao saldo contratual em aberto indicado nos documentos do caso.",
                "Sobre o valor principal deverão incidir multa contratual, juros de mora e correção monetária, conforme previsão contratual e memória de cálculo a ser revisada e atualizada até a data do ajuizamento.",
                f"Dá-se à causa, para fins fiscais e processuais, o valor inicial de R$ {civil_cause_value}, correspondente ao saldo principal inadimplido, sem prejuízo da atualização por multa contratual, juros de mora e correção monetária conforme memória de cálculo a ser apresentada.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental suplementar e testemunhal.",
                "Deverão instruir a demanda, conforme disponibilidade e conferência do advogado responsável, o contrato assinado, comprovante de pagamento parcial, relatório de execução dos serviços, fotografias, mensagens de reconhecimento da dívida, notificação extrajudicial, e-mails e planilha de cálculo atualizada.",
            ]
        )

        fechamento = _paragraphs(
            [
                f"Ante o exposto, requer o regular processamento da presente demanda e, ao final, a total procedência dos pedidos, com a condenação da parte ré ao pagamento do saldo contratual inadimplido no valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios.",
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental suplementar, testemunhal e demais provas necessárias à demonstração da relação contratual, da execução dos serviços, do pagamento parcial, do inadimplemento e das tentativas extrajudiciais de cobrança.",
                f"Dá-se à causa, para fins fiscais e processuais, o valor inicial de R$ {civil_cause_value}, correspondente ao saldo principal inadimplido, sem prejuízo da atualização por multa contratual, juros de mora e correção monetária conforme memória de cálculo a ser apresentada.",
                "Termos em que, pede deferimento.",
                f"{civil_signature_local}, {signature_date}.",
                f"{lawyer_name} — OAB/{lawyer_uf} {lawyer_oab}.",
            ]
        )

    if is_labor_case:
        labor_jurisdiction = "JOINVILLE/SC" if "joinville" in case_search_text else "[LOCALIDADE A DEFINIR]"
        enderecamento = _paragraphs(
            [
                f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA ___ VARA DO TRABALHO DE {labor_jurisdiction}.",
                "Na versão final, o advogado deverá confirmar a competência territorial, a Vara do Trabalho competente, o rito aplicável e eventual necessidade de adequação do endereçamento antes do protocolo.",
            ]
        )

    if is_trabalhista_insalubridade_periculosidade:
        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da pretensão trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à apuração de adicional de insalubridade por exposição a calor intenso e, de forma subsidiária, adicional de periculosidade caso a prova técnica demonstre risco acentuado juridicamente enquadrável.",
                "II. Dos fundamentos normativos aplicáveis. A pretensão deve observar a CLT, a Constituição Federal, as Normas Regulamentadoras de saúde e segurança do trabalho, especialmente os parâmetros técnicos relacionados à insalubridade, periculosidade, fornecimento de EPI, prova pericial e documentação ambiental/ocupacional.",
                "III. Da estratégia jurídica sugerida. A condução da tese deve priorizar prova técnica, documentação ocupacional e cálculo trabalhista preliminar, sem promessa de resultado judicial e com validação profissional antes do protocolo.",
                _series_block("IV. Dos pontos controvertidos que exigem enfrentamento direto:", controverted_points, limit=6),
                _series_block("V. Das lacunas probatórias a suprir antes do protocolo definitivo:", proof_checklist, limit=6),
                (
                    f"VI. Da síntese conclusiva considerada na redação. {executive_summary}"
                    if executive_summary and "dados insuficientes" not in executive_summary.lower()
                    else ""
                ),
            ]
        )

        pedidos = _paragraphs(
            [
                "I. Requer-se o reconhecimento do direito ao adicional de insalubridade, em grau a ser apurado por prova técnica, em razão da exposição habitual a calor intenso no setor de fusão.",
                "II. Subsidiariamente, caso a prova técnica indique enquadramento em situação de risco acentuado, requer-se a análise do adicional de periculosidade, observada a impossibilidade de cumulação entre insalubridade e periculosidade.",
                "III. Requer-se a condenação da reclamada ao pagamento das diferenças de adicional eventualmente reconhecidas no período contratual indicado na narrativa fática.",
                "IV. Requer-se a condenação da reclamada ao pagamento dos reflexos do adicional reconhecido em férias acrescidas de 1/3, 13º salário, FGTS e demais verbas trabalhistas cabíveis, conforme cálculo a ser apresentado e revisado pelo advogado.",
                "V. Requer-se a produção de prova pericial técnica no ambiente de trabalho, ou por meio técnico equivalente, a fim de verificar exposição a calor, condições do setor de fusão, fornecimento e eficácia dos EPIs.",
                "VI. Requer-se que a reclamada apresente PPP, LTCAT, PGR, PCMSO, mapa de riscos, ficha de entrega de EPI, registros de treinamento, holerites e demais documentos ambientais e ocupacionais relacionados ao período contratual.",
                "VII. Requer-se a produção de prova documental, testemunhal e pericial, sem prejuízo de outros meios de prova admitidos em direito.",
                "VIII. Requer-se, ao final, a procedência dos pedidos, nos limites da prova produzida, com juros, correção monetária, custas e demais cominações legais aplicáveis.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e pericial técnica.",
                "Requer-se a realização de perícia técnica para aferir a exposição a calor, proximidade com metal em fusão, condições ambientais do setor de fusão, fornecimento, adequação e eficácia dos EPIs.",
                "Requer-se que a reclamada seja intimada a apresentar PPP, LTCAT, PGR, PCMSO, mapa de riscos, ficha de entrega de EPI, registros de treinamento, holerites, documentos ambientais e demais registros ocupacionais do período contratual.",
                "Na versão final, o advogado deverá ajustar valor da causa, memória de cálculo, reflexos trabalhistas, grau de insalubridade eventualmente postulado e eventual pedido subsidiário de periculosidade conforme a prova disponível.",
            ]
        )



    # PATCH: labor_insalubridade_final_text_v1
    if is_trabalhista_insalubridade_periculosidade:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à apuração de eventual direito ao adicional de insalubridade por exposição ocupacional ao calor e, de forma subsidiária, ao adicional de periculosidade, conforme as condições reais de trabalho a serem demonstradas nos autos.",
                "O reclamante afirma ter laborado em ambiente industrial ligado ao setor de fusão, com possível exposição habitual a calor intenso, proximidade de fontes térmicas relevantes e processo produtivo envolvendo metal em fusão em temperatura aproximada de 1.500°C. Ressalta-se que essa referência diz respeito à temperatura do processo industrial, não significando, por si só, a temperatura efetivamente suportada pelo trabalhador, circunstância que deverá ser apurada por prova técnica.",
                "Segundo a narrativa apresentada, durante o contrato de trabalho não teria havido pagamento de adicional de insalubridade ou periculosidade relacionado às condições ambientais do setor de fusão, embora o reclamante alegue ter exercido suas atividades em ambiente potencialmente agressivo à saúde e/ou à integridade física.",
                "A controvérsia principal consiste em verificar se as condições reais de trabalho caracterizavam exposição ocupacional a calor acima dos limites juridicamente toleráveis, apta a ensejar o pagamento de adicional de insalubridade. De forma subsidiária, deverá ser analisada eventual periculosidade, caso a prova técnica identifique situação de risco acentuado juridicamente enquadrável.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos trabalhistas e ocupacionais, tais como holerites, contrato de trabalho, PPP, LTCAT, PGR, PCMSO, mapa de riscos, fichas de entrega de EPI, registros de treinamento, bem como a produção de prova testemunhal e pericial, a fim de verificar a rotina efetiva de trabalho, a frequência da exposição, a proximidade das fontes de calor, as pausas existentes, o fornecimento e a eficácia dos equipamentos de proteção.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento do labor em condições insalubres, em razão da exposição ocupacional habitual a calor intenso no setor de fusão da reclamada, com condenação da reclamada ao pagamento do adicional de insalubridade em grau a ser definido por prova técnica, observados os parâmetros legais, regulamentares e periciais aplicáveis.",
                "II. A condenação da reclamada ao pagamento das diferenças de adicional de insalubridade relativas ao período contratual indicado na narrativa fática, ou outro período que vier a ser confirmado nos autos, com apuração em liquidação de sentença.",
                "III. De forma subsidiária, caso a prova técnica conclua pelo enquadramento da atividade em situação de risco acentuado juridicamente caracterizável como perigosa, requer o reconhecimento do direito ao adicional de periculosidade, observada a impossibilidade de cumulação automática entre os adicionais de insalubridade e periculosidade, com adoção do adicional cabível ou mais favorável, conforme validação judicial e profissional.",
                "IV. A condenação da reclamada ao pagamento dos reflexos do adicional eventualmente reconhecido em férias acrescidas de 1/3, 13º salário, FGTS, aviso-prévio, quando cabível, e demais verbas trabalhistas de natureza salarial que sejam juridicamente aplicáveis ao caso concreto.",
                "V. A determinação de realização de perícia técnica no ambiente de trabalho, ou por meio técnico equivalente caso inviável a inspeção direta, a fim de apurar a exposição ocupacional ao calor, a intensidade e habitualidade da exposição, a proximidade das fontes térmicas, a existência de pausas, a taxa metabólica da atividade, as condições reais do setor de fusão e a eventual neutralização do agente nocivo por equipamentos de proteção.",
                "VI. A intimação da reclamada para apresentar todos os documentos ambientais, ocupacionais e trabalhistas relacionados ao período contratual, especialmente PPP, LTCAT, PGR, PCMSO, mapa de riscos, laudos ambientais, fichas de entrega de EPI, certificados de aprovação dos equipamentos fornecidos, registros de treinamento, registros de fiscalização de uso de EPI, holerites, contrato de trabalho, controles de jornada e demais documentos necessários à completa elucidação dos fatos.",
                "VII. O reconhecimento de que a simples apresentação de fichas de entrega de EPI não comprova, por si só, a efetiva neutralização do agente nocivo, devendo ser analisadas a adequação, certificação, regularidade de entrega, substituição, fiscalização, treinamento e eficácia real dos equipamentos nas condições concretas de trabalho.",
                "VIII. A autorização para produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, pericial técnica e demais provas que se fizerem necessárias durante a instrução processual.",
                "IX. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, na forma definida pela legislação e pela jurisprudência vigente no momento da liquidação.",
                "X. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XI. A atribuição à causa de valor provisório a ser definido pelo advogado responsável, com possibilidade de posterior adequação após apresentação de cálculo trabalhista, documentos complementares e conclusão da prova técnica.",
                "XII. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, reconhecendo-se o direito do reclamante ao adicional cabível e às respectivas diferenças e reflexos trabalhistas.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, pericial técnica e demais provas que se fizerem necessárias no curso da instrução.",
                "Requer, de forma específica, a realização de perícia técnica no ambiente de trabalho, ou por meio técnico equivalente caso a inspeção direta se torne inviável, a fim de apurar as condições reais de trabalho no setor de fusão da reclamada, especialmente quanto à exposição ocupacional ao calor, proximidade de fontes térmicas, habitualidade da exposição, intensidade do agente, existência de pausas, taxa metabólica da atividade, medidas de controle adotadas e eventual neutralização por equipamentos de proteção.",
                "Requer que a perícia avalie, de forma expressa, se a exposição ocupacional ao calor ultrapassava os limites juridicamente toleráveis, observando os critérios técnicos aplicáveis, inclusive medições ambientais, parâmetros reconhecidos de avaliação térmica, rotina efetiva de trabalho e demais elementos necessários à correta caracterização da condição laboral.",
                "Requer, ainda, que a reclamada seja intimada a apresentar todos os documentos ambientais, ocupacionais e trabalhistas relacionados ao período contratual, especialmente PPP, LTCAT, PGR, PCMSO, mapa de riscos, laudos ambientais, fichas de entrega de EPI, certificados de aprovação dos equipamentos fornecidos, registros de treinamento, registros de fiscalização de uso de EPI, controles de jornada, holerites, contrato de trabalho e demais documentos relacionados à saúde e segurança do trabalho.",
                "Requer que seja analisada a efetiva adequação dos equipamentos de proteção eventualmente fornecidos, considerando não apenas a existência de ficha de entrega, mas também a compatibilidade do equipamento com o agente nocivo, sua certificação, periodicidade de substituição, treinamento, fiscalização de uso e capacidade real de neutralização ou redução da exposição nas condições concretas de trabalho.",
                "Requer a oitiva de testemunhas que possam esclarecer a rotina laboral do reclamante, a frequência da exposição ao calor, a proximidade das fontes térmicas, as condições do setor de fusão, o uso ou não de equipamentos de proteção, a existência de pausas, a fiscalização pela reclamada e demais fatos relevantes à apuração da insalubridade ou, subsidiariamente, da periculosidade.",
                "Requer que eventual ausência, incompletude ou inconsistência dos documentos ambientais e ocupacionais seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas produzidas sejam analisadas em conjunto, a fim de permitir a correta apuração das condições reais de trabalho, do adicional eventualmente devido, dos reflexos trabalhistas cabíveis e dos valores a serem apurados em liquidação, sempre com observância da prova técnica, documental e testemunhal produzida nos autos.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, reconhecendo-se o direito do reclamante ao adicional de insalubridade por exposição ocupacional ao calor, em grau a ser apurado por prova técnica, ou, subsidiariamente, ao adicional de periculosidade, caso constatado enquadramento jurídico próprio, com o pagamento das diferenças correspondentes e respectivos reflexos trabalhistas.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e pericial técnica, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução processual.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares, prova técnica e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )



    # PATCH: labor_verbas_rescisorias_final_text_v1
    if is_trabalhista_verbas_rescisorias:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança de verbas rescisórias decorrentes de dispensa sem justa causa, conforme os fatos narrados e documentos a serem conferidos nos autos.",
                "Segundo a narrativa apresentada, o reclamante laborou para a reclamada em período aproximado informado no cadastro do caso, exercendo função remunerada, tendo sido dispensado sem justa causa sem o recebimento integral e tempestivo das parcelas rescisórias que afirma serem devidas.",
                "O reclamante alega que não foram pagos, ou foram pagos de forma incompleta, saldo de salário, aviso-prévio, férias vencidas e/ou proporcionais acrescidas de 1/3, 13º salário proporcional, depósitos de FGTS do período contratual e multa rescisória de 40% sobre o FGTS.",
                "Também afirma que não recebeu corretamente as guias para saque do FGTS e habilitação no seguro-desemprego, ou que houve dificuldade para acessar tais direitos em razão de pendências atribuídas à empregadora.",
                "A controvérsia principal consiste em verificar a data exata de admissão e desligamento, a modalidade de rescisão, os valores efetivamente pagos, a regularidade dos depósitos de FGTS, a entrega das guias rescisórias e a existência de diferenças trabalhistas a serem apuradas por cálculo técnico.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos como CTPS ou contrato de trabalho, TRCT, aviso de dispensa, holerites, comprovantes de pagamento, extrato analítico do FGTS, comunicações entre as partes e demais documentos relacionados à rescisão contratual.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à cobrança de verbas rescisórias decorrentes de dispensa sem justa causa, com apuração documental e cálculo das parcelas efetivamente devidas.",
                "II. Das verbas rescisórias em dispensa sem justa causa. Em regra, a dispensa sem justa causa pode gerar direito ao pagamento de saldo de salário, aviso-prévio, férias vencidas e proporcionais acrescidas de 1/3, 13º salário proporcional, liberação do FGTS, multa rescisória de 40% sobre o FGTS e demais parcelas cabíveis conforme o contrato e a prova documental.",
                "III. Do prazo de pagamento e da multa do art. 477 da CLT. Deverá ser verificado se as verbas rescisórias foram pagas dentro do prazo legal aplicável. Caso constatado atraso ou inadimplemento injustificado, poderá ser analisado o cabimento da multa prevista no art. 477 da CLT, conforme validação profissional e prova dos autos.",
                "IV. Da multa do art. 467 da CLT. Havendo verbas incontroversas não quitadas no momento processual adequado, deverá ser analisado o cabimento da multa prevista no art. 467 da CLT, especialmente quanto às parcelas reconhecidas como devidas e não pagas oportunamente.",
                "V. Do FGTS, multa de 40% e guias rescisórias. A apuração deverá considerar o extrato analítico do FGTS, a regularidade dos depósitos durante o contrato, a incidência da multa rescisória de 40%, bem como eventual necessidade de expedição ou regularização das guias para saque do FGTS e habilitação no seguro-desemprego.",
                "VI. Da necessidade de prova documental e cálculo trabalhista. A conclusão sobre valores depende da conferência de CTPS, contrato, TRCT, holerites, comprovantes de pagamento, extrato de FGTS, aviso de dispensa e demais documentos rescisórios, além de cálculo trabalhista preliminar revisado pelo advogado responsável.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, evitando promessa de resultado e condicionando a liquidação dos valores à prova documental, à memória de cálculo e à validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da dispensa sem justa causa, caso confirmada pela documentação trabalhista e rescisória, com a condenação da reclamada ao pagamento das verbas rescisórias devidas e não quitadas, ou quitadas de forma incompleta.",
                "II. A condenação da reclamada ao pagamento de saldo de salário eventualmente devido, conforme dias trabalhados no mês da rescisão e apuração em cálculo trabalhista.",
                "III. A condenação da reclamada ao pagamento de aviso-prévio indenizado ou diferenças de aviso-prévio, conforme modalidade de cumprimento, tempo de serviço e documentos rescisórios.",
                "IV. A condenação da reclamada ao pagamento de férias vencidas e/ou proporcionais acrescidas de 1/3 constitucional, conforme período aquisitivo, período proporcional e valores já eventualmente pagos.",
                "V. A condenação da reclamada ao pagamento de 13º salário proporcional e eventuais diferenças, conforme período trabalhado no ano da rescisão.",
                "VI. A condenação da reclamada ao recolhimento ou pagamento das diferenças de FGTS do período contratual, com apresentação do extrato analítico e confrontação com os salários pagos.",
                "VII. A condenação da reclamada ao pagamento da multa rescisória de 40% sobre o FGTS devido, caso confirmada a dispensa sem justa causa e constatada ausência ou insuficiência de pagamento.",
                "VIII. A condenação da reclamada à entrega, regularização ou indenização substitutiva das guias necessárias ao saque do FGTS e à habilitação no seguro-desemprego, quando cabível e conforme prova documental.",
                "IX. A condenação da reclamada ao pagamento da multa prevista no art. 477 da CLT, caso comprovado atraso ou ausência de pagamento tempestivo das verbas rescisórias no prazo legal.",
                "X. A aplicação da multa prevista no art. 467 da CLT sobre verbas incontroversas, caso existentes e não quitadas no momento processual adequado.",
                "XI. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "XII. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XIII. A produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outros meios necessários à completa apuração dos fatos.",
                "XIV. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, depoimento pessoal da reclamada e demais provas que se fizerem necessárias durante a instrução.",
                "Requer a juntada e análise de CTPS ou contrato de trabalho, termo de rescisão do contrato de trabalho, aviso de dispensa, holerites, comprovantes de pagamento, extrato analítico do FGTS, guias rescisórias, comunicações entre as partes e demais documentos relacionados à admissão, remuneração, jornada e rescisão contratual.",
                "Requer que a reclamada seja intimada a apresentar documentos rescisórios e trabalhistas sob sua guarda, especialmente TRCT, recibos de pagamento, comprovantes de depósito de FGTS, comprovantes de entrega de guias, registros funcionais, ficha de empregado e demais documentos necessários à conferência das parcelas postuladas.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar saldo de salário, aviso-prévio, férias vencidas e/ou proporcionais acrescidas de 1/3, 13º salário proporcional, FGTS, multa de 40%, multas legais eventualmente cabíveis, juros e correção monetária.",
                "Requer a oitiva de testemunhas, caso necessário, para esclarecer a modalidade da dispensa, a data de desligamento, a entrega de documentos rescisórios, pagamentos realizados e demais circunstâncias relevantes à controvérsia.",
                "Requer que eventual ausência, incompletude ou inconsistência dos documentos rescisórios seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração das verbas rescisórias, das diferenças de FGTS, das guias devidas e das multas legais eventualmente aplicáveis.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao pagamento das verbas rescisórias devidas, diferenças de FGTS, multa de 40%, guias rescisórias, multas legais eventualmente cabíveis e demais parcelas reconhecidas nos autos.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    # PATCH: labor_horas_extras_final_text_v1
    if is_trabalhista_horas_extras:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança de horas extras, reflexos trabalhistas e eventuais diferenças decorrentes de jornada excedente e intervalo intrajornada irregular.",
                "Segundo a narrativa apresentada, o reclamante afirma ter laborado em jornada habitual superior à contratual, com início das atividades por volta das 7h e encerramento por volta das 19h, de segunda a sábado, em rotina que teria extrapolado a jornada ordinária.",
                "O reclamante também sustenta que o intervalo para refeição e descanso era frequentemente reduzido ou não concedido integralmente, circunstância que deverá ser apurada por meio de controles de ponto, escalas, mensagens, ordens de serviço, holerites e prova testemunhal.",
                "Alega, ainda, que parte das horas extras realizadas não era registrada corretamente nos controles de ponto, ou era registrada apenas parcialmente, sem o pagamento integral do adicional de horas extras e dos reflexos trabalhistas correspondentes.",
                "A controvérsia principal consiste em verificar a jornada contratual, a jornada efetivamente cumprida, a fidelidade dos controles de ponto, a regularidade do intervalo intrajornada, os pagamentos realizados e a existência de diferenças de horas extras a serem apuradas por cálculo trabalhista.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos como contrato de trabalho ou CTPS, holerites, controles de ponto, escalas, recibos de pagamento, mensagens, ordens de serviço e demais elementos capazes de demonstrar a rotina real de trabalho.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à cobrança de horas extras, diferenças de jornada, intervalo intrajornada e reflexos trabalhistas, conforme prova documental, testemunhal e cálculo técnico.",
                "II. Da jornada excedente e das horas extras. Caso comprovado que o reclamante laborava além da jornada legal ou contratual sem a correspondente quitação, serão devidas as diferenças de horas extras, com adicional legal, convencional ou contratual aplicável, observada a jornada efetivamente comprovada.",
                "III. Dos controles de ponto e da prova da jornada. A apuração da jornada depende da análise dos controles de ponto, escalas, holerites, recibos de pagamento, mensagens, ordens de serviço e prova testemunhal. Caso os controles sejam ausentes, incompletos ou incompatíveis com a realidade laboral, a prova deverá ser valorada em conjunto.",
                "IV. Do intervalo intrajornada. Havendo supressão ou concessão parcial do intervalo para refeição e descanso, deverá ser analisado o direito ao pagamento correspondente ao período irregular, conforme legislação trabalhista aplicável, prova da rotina e parâmetros de cálculo definidos na fase própria.",
                "V. Dos reflexos trabalhistas. As horas extras habitualmente prestadas podem gerar reflexos em descanso semanal remunerado, férias acrescidas de 1/3, 13º salário, FGTS e demais parcelas juridicamente cabíveis, conforme habitualidade, base de cálculo e prova dos autos.",
                "VI. Da necessidade de cálculo trabalhista. A quantificação das diferenças depende de cálculo técnico, com confrontação entre jornada alegada, cartões de ponto, holerites, valores pagos, adicionais aplicáveis, compensações eventualmente existentes e reflexos legais.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, sem promessa de resultado judicial, condicionando a liquidação dos valores à prova documental, testemunhal, memória de cálculo e validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da jornada extraordinária efetivamente prestada, conforme prova documental, controles de ponto, prova testemunhal e demais elementos produzidos nos autos.",
                "II. A condenação da reclamada ao pagamento das horas extras laboradas além da jornada legal ou contratual, com o adicional legal, convencional ou contratual aplicável, conforme apuração em cálculo trabalhista.",
                "III. A condenação da reclamada ao pagamento de diferenças de horas extras eventualmente quitadas a menor, mediante confronto entre controles de ponto, holerites, recibos e jornada efetivamente comprovada.",
                "IV. A condenação da reclamada ao pagamento do período correspondente ao intervalo intrajornada suprimido ou concedido parcialmente, quando comprovada a irregularidade, com os reflexos cabíveis conforme legislação aplicável.",
                "V. A condenação da reclamada ao pagamento dos reflexos das horas extras e diferenças reconhecidas em descanso semanal remunerado, férias acrescidas de 1/3, 13º salário, FGTS e demais verbas trabalhistas juridicamente cabíveis.",
                "VI. A intimação da reclamada para apresentar controles de ponto, escalas de trabalho, registros de jornada, holerites, recibos de pagamento de horas extras, acordos de compensação ou banco de horas, caso existentes, e demais documentos relacionados à jornada do reclamante.",
                "VII. O reconhecimento da invalidade ou insuficiência dos controles de ponto, caso sejam apresentados registros incompatíveis com a jornada efetivamente praticada, britânicos, incompletos ou sem correspondência com a realidade laboral, conforme prova produzida.",
                "VIII. A produção de prova testemunhal para confirmação da jornada real, frequência das horas extras, rotina de intervalos, metas operacionais, fechamento de rotas e demais circunstâncias relevantes.",
                "IX. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "X. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XI. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, depoimento pessoal da reclamada e demais provas necessárias à apuração da jornada efetivamente cumprida.",
                "Requer a juntada e análise de contrato de trabalho ou CTPS, holerites, controles de ponto, cartões de ponto, escalas de trabalho, recibos de pagamento de horas extras, registros de banco de horas, acordos de compensação, mensagens, ordens de serviço, relatórios de rota, registros de metas e demais documentos relacionados à jornada.",
                "Requer que a reclamada seja intimada a apresentar todos os controles de jornada do período contratual discutido, inclusive espelhos de ponto, registros eletrônicos, escalas, recibos de pagamento e documentos relativos a banco de horas ou compensação de jornada.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar horas extras, adicional aplicável, intervalo intrajornada, reflexos em DSR, férias acrescidas de 1/3, 13º salário, FGTS, juros, correção monetária e compensação de valores eventualmente pagos.",
                "Requer a oitiva de testemunhas que possam esclarecer a jornada real, o horário de entrada e saída, a frequência das horas extras, a regularidade dos intervalos, a existência de metas, carregamento, separação de mercadorias, fechamento de rotas e demais aspectos da rotina laboral.",
                "Requer que eventual ausência, incompletude, inconsistência ou artificialidade dos controles de ponto seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração da jornada, das horas extras, dos intervalos irregulares, dos reflexos trabalhistas e dos valores devidos.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao pagamento das horas extras devidas, diferenças de jornada, intervalo intrajornada irregular, reflexos trabalhistas e demais parcelas reconhecidas nos autos.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    # PATCH: labor_fgts_nao_recolhido_final_text_v1
    # PATCH: prevent_fgts_template_overriding_severance_v1
    # Casos de verbas rescisórias podem mencionar FGTS/multa de 40% como pedidos acessórios,
    # mas não devem ser roteados para o template principal de FGTS não recolhido.
    if is_trabalhista_fgts_nao_recolhido and not is_trabalhista_verbas_rescisorias:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança, regularização ou indenização de depósitos de FGTS não recolhidos, recolhidos parcialmente ou realizados de forma irregular durante o contrato de trabalho.",
                "Segundo a narrativa apresentada, o reclamante afirma que, ao consultar o extrato analítico da conta vinculada do FGTS, identificou ausência de depósitos em determinados meses do contrato, valores inferiores aos devidos ou períodos sem movimentação compatível com a remuneração recebida.",
                "O reclamante sustenta que a irregularidade no recolhimento do FGTS prejudicou a formação do saldo fundiário e a regularidade das obrigações trabalhistas da empregadora, sendo necessária a conferência mês a mês entre remuneração, holerites, extrato analítico e comprovantes de recolhimento.",
                "De forma subsidiária ou condicionada, caso confirmada dispensa sem justa causa, deverá ser analisada eventual diferença na multa rescisória de 40% sobre o FGTS, limitada ao saldo e às diferenças efetivamente reconhecidas.",
                "A controvérsia principal consiste em verificar se houve ausência total ou parcial de depósitos de FGTS, se os valores recolhidos correspondem à remuneração mensal devida, quais competências apresentam inconsistência e se há diferenças a serem recolhidas, regularizadas ou indenizadas.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de CTPS ou contrato de trabalho, holerites, extrato analítico completo do FGTS, comprovantes de pagamento salarial, documentos rescisórios, GFIP, SEFIP, eSocial, comprovantes de recolhimento e demais documentos sob guarda da empregadora.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à apuração de depósitos de FGTS não recolhidos, recolhidos parcialmente ou realizados de forma irregular durante o contrato de trabalho.",
                "II. Da obrigação de recolhimento do FGTS. O empregador possui dever de realizar os depósitos fundiários incidentes sobre a remuneração do empregado, cabendo apurar, por documentos e cálculo técnico, se houve regularidade dos recolhimentos durante todo o período contratual discutido.",
                "III. Das diferenças de FGTS. A existência de diferenças deve ser verificada mediante confronto entre extrato analítico da conta vinculada, holerites, remuneração mensal, comprovantes de recolhimento, documentos fiscais/trabalhistas e demais registros apresentados pelas partes.",
                "IV. Da exibição documental. Considerando que documentos como GFIP, SEFIP, eSocial, comprovantes de recolhimento, fichas financeiras e registros funcionais podem estar sob guarda da reclamada, mostra-se cabível requerer sua apresentação para completa apuração das competências e valores devidos.",
                "V. Da multa rescisória de 40%, se cabível. A multa de 40% sobre o FGTS somente deverá ser analisada caso confirmada a modalidade rescisória que a autorize, especialmente dispensa sem justa causa, e deverá incidir sobre o saldo e diferenças efetivamente reconhecidos, conforme cálculo trabalhista.",
                "VI. Da necessidade de cálculo trabalhista. A quantificação depende de cálculo mês a mês, com apuração das competências sem recolhimento, valores recolhidos a menor, base remuneratória, atualização, juros e eventual repercussão na multa rescisória, quando cabível.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, sem promessa de resultado judicial, condicionando a conclusão à prova documental, ao extrato analítico completo, à exibição de documentos pela reclamada e à validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da existência de ausência, insuficiência ou irregularidade nos depósitos de FGTS durante o contrato de trabalho, conforme apuração documental e cálculo trabalhista.",
                "II. A condenação da reclamada ao recolhimento, regularização ou pagamento indenizado das diferenças de FGTS devidas no período contratual, conforme competências apuradas e valores identificados no extrato analítico da conta vinculada.",
                "III. A determinação para que a reclamada apresente comprovantes de recolhimento de FGTS, GFIP, SEFIP, eSocial, fichas financeiras, registros funcionais, holerites, recibos salariais e demais documentos necessários à conferência das competências discutidas.",
                "IV. A condenação da reclamada ao pagamento das diferenças de FGTS apuradas mês a mês, considerando a remuneração devida, verbas salariais integrantes da base de cálculo e valores já eventualmente recolhidos.",
                "V. Caso confirmada dispensa sem justa causa ou hipótese legal equivalente, a condenação da reclamada ao pagamento das diferenças da multa rescisória de 40% sobre o FGTS, calculada sobre o saldo e as diferenças reconhecidas.",
                "VI. A regularização da conta vinculada do FGTS do reclamante, quando tecnicamente possível, ou, subsidiariamente, o pagamento indenizado das diferenças correspondentes.",
                "VII. A produção de prova documental, contábil, testemunhal e demais meios de prova admitidos em direito, especialmente para apuração da remuneração, das competências sem recolhimento e dos valores devidos.",
                "VIII. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "IX. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "X. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        pedidos_valores_estimados, calculated_cause_value = _build_fgts_claim_values_section(
            state_metadata,
            case,
            cause_value,
        )
        if calculated_cause_value:
            cause_value = calculated_cause_value

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, contábil, testemunhal, depoimento pessoal da reclamada e demais provas necessárias à apuração da regularidade dos depósitos de FGTS.",
                "Requer a juntada e análise de CTPS ou contrato de trabalho, holerites, comprovantes de pagamento salarial, extrato analítico completo do FGTS, termo de rescisão, quando houver, comprovantes de recolhimento, GFIP, SEFIP, eSocial, fichas financeiras e demais documentos relacionados à remuneração e aos recolhimentos fundiários.",
                "Requer que a reclamada seja intimada a apresentar todos os documentos sob sua guarda relacionados ao FGTS, inclusive comprovantes de recolhimento por competência, GFIP, SEFIP, eSocial, fichas financeiras, folhas de pagamento, registros funcionais e demais documentos necessários à conferência dos depósitos.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar competências sem recolhimento, depósitos realizados a menor, base remuneratória, atualização, juros e eventual diferença de multa rescisória de 40%, se cabível.",
                "Requer que eventual ausência, incompletude ou inconsistência dos comprovantes de recolhimento seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Requer a oitiva de testemunhas, caso necessário, para esclarecer a rotina contratual, remuneração, comunicações internas sobre FGTS e demais fatos relevantes, sem prejuízo da prioridade da prova documental e contábil.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração das diferenças de FGTS, da regularização da conta vinculada, dos valores indenizáveis e das parcelas acessórias eventualmente cabíveis.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao recolhimento, regularização ou pagamento indenizado das diferenças de FGTS devidas, bem como à diferença da multa rescisória de 40%, caso cabível e comprovada a hipótese legal correspondente.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, contábil, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    # PATCH: criminal_editable_document_routing_v1
    # Criminal V1 entra como minuta supervisionada, sem promessa de resultado,
    # sem juízo definitivo de culpa/inocência e sem uso externo sem revisão do advogado.
    if is_criminal_area:
        is_criminal_liberdade = any(
            term in case_search_text
            for term in [
                "liberdade provisória",
                "liberdade provisoria",
                "medidas cautelares",
                "prisão em flagrante",
                "prisao em flagrante",
                "audiência de custódia",
                "audiencia de custodia",
            ]
        ) or "liberdade" in normalized_action_type

        is_criminal_relaxamento = any(
            term in case_search_text
            for term in [
                "relaxamento de prisão",
                "relaxamento de prisao",
                "prisão ilegal",
                "prisao ilegal",
                "ilegalidade da prisão",
                "ilegalidade da prisao",
            ]
        ) or "relaxamento" in normalized_action_type

        is_criminal_habeas = "habeas" in case_search_text or "habeas" in normalized_action_type
        is_criminal_resposta = any(
            term in case_search_text
            for term in [
                "resposta à acusação",
                "resposta a acusacao",
                "denúncia",
                "denuncia",
                "acusação",
                "acusacao",
            ]
        ) or "resposta" in normalized_action_type

        if is_criminal_resposta:
            response_accusation_forbidden_context_markers = [
                "relatório médico",
                "relatorio medico",
                "laudo médico",
                "laudo medico",
                "urgência médica",
                "urgencia medica",
                "nexo causal",
                "quantificação de impactos",
                "quantificacao de impactos",
                "impactos alegados",
                "incapacidade laboral",
                "benefício previdenciário",
                "beneficio previdenciario",
                "dano material ambiental",
                "direito de vizinhança",
                "direito de vizinhanca",
                "verbas rescisórias",
                "verbas rescisorias",
                "fgts",
                "clt",
                "vara do trabalho",
                "obrigação de fazer",
                "obrigacao de fazer",
            ]

            def _has_response_accusation_contamination(item: str) -> bool:
                item_lower = str(item or "").lower()
                return any(
                    marker in item_lower
                    for marker in response_accusation_forbidden_context_markers
                )

            controverted_points = [
                item
                for item in controverted_points
                if not _has_response_accusation_contamination(item)
            ]
            proof_checklist = [
                item
                for item in proof_checklist
                if not _has_response_accusation_contamination(item)
            ]

            if executive_summary and _has_response_accusation_contamination(executive_summary):
                executive_summary = ""

            proof_checklist.extend(
                [
                    "Necessidade de conferir denúncia, decisão de recebimento, citação/intimação e prazo para resposta.",
                    "Necessidade de organizar preliminares, justa causa, materialidade, autoria, provas disponíveis e rol de testemunhas.",
                    "Necessidade de validar estratégia defensiva e requerimentos probatórios antes do protocolo.",
                ]
            )
            proof_checklist = list(dict.fromkeys([item for item in proof_checklist if item]))
            controverted_points = list(dict.fromkeys([item for item in controverted_points if item]))

        if is_criminal_relaxamento:
            criminal_title = "PEDIDO DE RELAXAMENTO DE PRISÃO"
            criminal_core_request = (
                "o relaxamento da prisão, caso confirmada ilegalidade formal ou material, "
                "com expedição do alvará de soltura, salvo se houver outro motivo legal para manutenção da custódia"
            )
            criminal_focus = (
                "legalidade da prisão, formalidades do flagrante, comunicação, nota de culpa, fundamentação judicial, "
                "audiência de custódia e eventual constrangimento ilegal"
            )
        elif is_criminal_habeas:
            criminal_title = "HABEAS CORPUS COM PEDIDO LIMINAR"
            criminal_core_request = (
                "a concessão da ordem, inclusive em caráter liminar quando presentes os requisitos, "
                "para cessar constrangimento ilegal objetivamente demonstrado"
            )
            criminal_focus = (
                "constrangimento ilegal, urgência, ato coator, autoridade apontada, fundamentação concreta da medida "
                "e adequação do habeas corpus ao caso"
            )
        elif is_criminal_resposta:
            criminal_title = "RESPOSTA À ACUSAÇÃO"
            criminal_core_request = (
                "o recebimento da resposta defensiva, com análise de preliminares, mérito, provas, testemunhas "
                "e demais requerimentos defensivos cabíveis"
            )
            criminal_focus = (
                "imputação narrada na denúncia, preliminares, justa causa, provas disponíveis, testemunhas, "
                "tese defensiva e requerimentos probatórios"
            )
        else:
            criminal_title = "PEDIDO DE LIBERDADE PROVISÓRIA COM OU SEM MEDIDAS CAUTELARES"
            criminal_core_request = (
                "a concessão de liberdade provisória, com ou sem medidas cautelares diversas da prisão, "
                "conforme avaliação técnica do advogado e documentos disponíveis"
            )
            criminal_focus = (
                "legalidade da prisão, necessidade concreta da custódia, adequação de medidas cautelares, "
                "condições pessoais, documentos, decisão de custódia e riscos processuais"
            )

        criminal_review_warning = (
            "ATENÇÃO: minuta criminal gerada em modo assistido. O conteúdo não substitui a atuação de advogado "
            "habilitado, não representa promessa de resultado, não afirma culpa ou inocência de forma definitiva "
            "e não deve ser usado externamente sem revisão, validação e aprovação profissional."
        )

        enderecamento = _paragraphs(
            [
                f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DO JUÍZO CRIMINAL COMPETENTE DA COMARCA DE {case_comarca}.",
                "Na versão final, o advogado deverá confirmar competência, prevenção, autoridade coatora quando aplicável, fase procedimental e rito adequado antes de qualquer protocolo.",
            ]
        )

        qualificacao_partes = _paragraphs(
            [
                (
                    f"{author_inline_qualification}, por seu advogado, vem, respeitosamente, à presença de Vossa Excelência, "
                    f"apresentar a presente minuta de {criminal_title}, conforme fatos, documentos e fundamentos a seguir expostos."
                ),
                "A qualificação das partes, investigado/acusado/paciente, autoridade policial ou judicial, Ministério Público, vítima, testemunhas e demais envolvidos deverá ser conferida e complementada pelo advogado na versão final.",
                criminal_review_warning,
            ]
        )

        resumo_fatico = _paragraphs(
            [
                f"Trata-se do caso criminal {case.case_number} — {case.title}.",
                case_description,
                (
                    "A narrativa deverá ser revisada pelo advogado com atenção especial à data e local dos fatos, fase do procedimento, existência de prisão, autoridade responsável, documentos recebidos, provas disponíveis, testemunhas conhecidas e prazos urgentes."
                ),
                (
                    f"A leitura inicial do sistema indica foco em {criminal_focus}, sem conclusão definitiva sobre culpa, inocência, legalidade da medida ou resultado judicial."
                ),
            ]
        )

        fundamentacao = _paragraphs(
            [
                f"I. DO CABIMENTO DA MEDIDA. A presente minuta é estruturada como {criminal_title}, em caráter assistido, para revisão técnica do advogado responsável antes de qualquer uso externo.",
                (
                    "II. DAS GARANTIAS PROCESSUAIS. A análise deve observar devido processo legal, contraditório, ampla defesa, presunção de inocência, controle judicial da prisão e necessidade de fundamentação concreta das medidas restritivas de liberdade."
                ),
                _series_block("III. DA BASE NORMATIVA INICIAL CONSIDERADA:", normative_basis, limit=5),
                (
                    f"IV. DOS PONTOS JURÍDICOS A SEREM ENFRENTADOS. A minuta deve concentrar a argumentação em {criminal_focus}, sempre com base nos documentos efetivamente disponíveis e sem presunção de fatos não informados."
                ),
                _series_block("V. DOS PONTOS CONTROVERTIDOS E RISCOS TÉCNICOS:", controverted_points, limit=5),
                _series_block("VI. DAS LACUNAS PROBATÓRIAS A SUPRIR ANTES DO PROTOCOLO:", proof_checklist, limit=5),
                (
                    f"VII. DA SÍNTESE TÉCNICA CONSIDERADA. {executive_summary}"
                    if executive_summary and "dados insuficientes" not in executive_summary.lower()
                    else ""
                ),
                criminal_review_warning,
            ]
        )

        pedidos = _paragraphs(
            [
                f"Diante do exposto, requer-se, após revisão e validação do advogado:",
                f"I. {criminal_core_request.capitalize()}.",
                "II. A análise expressa da legalidade, necessidade, adequação e proporcionalidade da medida restritiva discutida, conforme documentos e decisões constantes do caso.",
                "III. Subsidiariamente, quando juridicamente adequado, a aplicação de medidas cautelares diversas da prisão, observados os fatos concretos, a fase procedimental e a avaliação profissional do advogado.",
                "IV. A juntada e consideração dos documentos, provas e registros indicados pela defesa, sem prejuízo de complementação documental antes do protocolo.",
                "V. A intimação do Ministério Público ou da autoridade competente, quando cabível ao rito e à medida adotada.",
                "VI. A expedição das comunicações, alvarás, ofícios ou providências cabíveis somente se deferida a medida pelo juízo competente.",
                "VII. Que todos os pedidos sejam revisados pelo advogado para adequação ao caso concreto, à competência, à fase procedimental e aos documentos efetivamente disponíveis.",
            ]
        )

        pedidos_valores_estimados = _paragraphs(
            [
                "Em regra, a minuta criminal inicial não depende de estimativa econômica de pedidos.",
                "Caso haja pedido indenizatório, fiança, custas, multa, reparação mínima, valor de causa ou outro reflexo econômico, o advogado deverá preencher e validar o valor aplicável na versão final.",
                f"Valor econômico/custas/fiança: R$ {cause_value}, sujeito a confirmação técnica e documental pelo advogado.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer-se a análise e juntada dos documentos criminais disponíveis, conforme a fase do caso e a medida escolhida pelo advogado.",
                "Devem ser conferidos, quando existentes: boletim de ocorrência, auto de prisão em flagrante, nota de culpa, decisão judicial, ata de audiência de custódia, denúncia, citação/intimação, certidões, procuração e documentos pessoais.",
                "Também devem ser organizados registros digitais, prints, conversas, áudios, vídeos, fotografias, comprovantes de endereço, documentos profissionais, testemunhas e demais elementos relevantes à versão defensiva.",
                "Antes do protocolo, o advogado deverá verificar autenticidade, pertinência, cadeia mínima de preservação, origem dos documentos e eventual necessidade de sigilo ou tarja de dados sensíveis.",
                "Nenhuma prova deve ser inventada, adulterada, ocultada ou orientada de forma ilegal. O sistema apenas organiza informações fornecidas e pendências de validação.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Ante o exposto, requer-se o regular processamento da medida criminal cabível, nos limites dos fatos narrados, documentos disponíveis e fundamentos revisados pelo advogado.",
                f"Requer-se, conforme validação profissional, {criminal_core_request}.",
                "A presente minuta permanece em estado de rascunho assistido e deverá ser integralmente revisada, ajustada e aprovada por advogado habilitado antes de qualquer uso externo.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    protocolo_checklist = _build_protocol_readiness_checklist_section(
        author_inline_qualification=author_inline_qualification,
        defendant_inline_qualification=defendant_inline_qualification,
        lawyer_name=lawyer_name,
        lawyer_oab=lawyer_oab,
        lawyer_uf=lawyer_uf,
        signature_local=signature_local,
        signature_date=signature_date,
        cause_value=cause_value,
        is_fgts_case=is_trabalhista_fgts_nao_recolhido and not is_trabalhista_verbas_rescisorias,
        is_labor_case=is_labor_case,
    )

    return [
        {
            "key": "enderecamento",
            "title": "Endereçamento",
            "content": enderecamento,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "qualificacao_partes",
            "title": "Qualificação das Partes",
            "content": qualificacao_partes,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "resumo_fatico",
            "title": "Resumo Fático",
            "content": resumo_fatico,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "technical_analysis"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "fundamentacao",
            "title": "Fundamentação",
            "content": fundamentacao,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["technical_analysis", "strategic_analysis", "viability", "decision"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "pedidos",
            "title": "Pedidos",
            "content": pedidos,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["decision", "viability", "technical_analysis"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "pedidos_valores_estimados",
            "title": "Pedidos e Valores Estimados",
            "content": pedidos_valores_estimados,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "calculation", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "requires_professional_review",
            },
        },
        {
            "key": "provas_requerimentos",
            "title": "Provas e Requerimentos",
            "content": provas_requerimentos,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["technical_analysis", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "fechamento",
            "title": "Fechamento",
            "content": fechamento,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "checklist_final_protocolo",
            "title": "Checklist Final para Protocolo",
            "content": protocolo_checklist,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "calculation", "strategy", "protocol_readiness"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "requires_professional_review",
                "export_visibility": "internal",
                "include_in_final_pdf": False,
            },
        },
    ]

@router.post(
    "",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document(
    payload: EditableDocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    current_user_id = _resolve_current_user_id(db, current_user)

    document = EditableDocument(
        tenant_id=current_user["tenant_id"],
        case_id=payload.case_id,
        created_by_user_id=current_user_id,
        area=payload.area,
        document_type=payload.document_type,
        title=payload.title,
        status="draft",
        current_version_number=1,
        document_metadata=payload.metadata,
    )
    db.add(document)
    db.flush()

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=1,
        approved=False,
        notes=payload.notes,
        sections=[section.model_dump() for section in payload.sections],
        version_metadata={
            **payload.metadata,
            "source": "api_create_editable_document",
        },
    )
    db.add(version)
    db.commit()
    db.refresh(document)

    return _build_document_detail_payload(db, document)


@router.get(
    "/case/{case_id}",
    response_model=list[EditableDocumentOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_editable_documents_for_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return (
        db.query(EditableDocument)
        .filter(
            EditableDocument.tenant_id == current_user["tenant_id"],
            EditableDocument.case_id == case_id,
        )
        .order_by(EditableDocument.updated_at.desc())
        .all()
    )


@router.get(
    "/{document_id}",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    return _build_document_detail_payload(db, document)


@router.delete(
    "/{document_id}",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    versions_count = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
        )
        .count()
    )

    db.delete(document)
    db.commit()

    return {
        "deleted_document_id": document_id,
        "deleted_versions_count": versions_count,
        "detail": "Editable document deleted successfully",
    }


@router.get(
    "/{document_id}/export/html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_html(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": _resolve_editor_export_title(db, document, current_user["tenant_id"]),
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    return HTMLResponse(content=html)


@router.get(
    "/{document_id}/export/pdf",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": _resolve_editor_export_title(db, document, current_user["tenant_id"]),
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    pdf_bytes = generate_editor_pdf(html)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="editable_document_{document.id}_v{approved_version.version_number}.pdf"'
        },
    )



@router.post(
    "/{document_id}/generate-assisted-draft",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def generate_assisted_draft(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == document.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Archived cases cannot generate assisted draft",
        )

    analysis_record = _get_or_create_case_analysis_record(db=db, case=case, current_user=current_user)

    if _is_audiencia_estrategica_document_type(document.document_type):
        assisted_sections = _build_audiencia_estrategica_sections(
            case,
            analysis_record,
            db=db,
            tenant_id=current_user["tenant_id"],
        )
        version_notes = "Roteiro de audiência estratégica gerado a partir da análise do caso"
        version_source = "audiencia_estrategica_from_analysis"
        version_generation_mode = "audiencia_estrategica_from_analysis"
    else:
        assisted_sections = _build_assisted_sections(
            db,
            case,
            analysis_record,
            current_user["tenant_id"],
            document_metadata=document.document_metadata or {},
        )
        version_notes = "Minuta assistida gerada a partir da análise do caso"
        version_source = "assisted_draft_from_analysis"
        version_generation_mode = "assisted_draft_from_analysis"

    current_user_id = _resolve_current_user_id(db, current_user)
    latest_version_number = (
        db.query(EditableDocumentVersion.version_number)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .limit(1)
        .scalar()
    )
    next_version_number = (latest_version_number or document.current_version_number or 0) + 1
    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=False,
        notes="Minuta assistida gerada a partir da análise do caso",
        sections=assisted_sections,
        version_metadata={
            "source": "assisted_draft_from_analysis",
            "analysis_id": analysis_record.id,
            "case_id": case.id,
            "origin_modules": [
                "analysis",
                "executive_summary",
                "executive_decision",
                "analysis_foundations",
            ],
        },
    )
    db.add(version)

    approved_version_number = (
        db.query(EditableDocumentVersion.version_number)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .limit(1)
        .scalar()
    )

    if approved_version_number is None:
        document.current_version_number = next_version_number
        document.status = "draft"
    else:
        document.current_version_number = approved_version_number
        document.status = "approved"

    document_metadata = {
        **(document.document_metadata or {}),
        "last_generation_mode": "assisted_draft_from_analysis",
        "last_assisted_draft_version_number": next_version_number,
    }
    if approved_version_number is not None:
        document_metadata["preserved_current_version_number"] = approved_version_number

    document.document_metadata = document_metadata
    db.add(document)

    db.commit()
    db.refresh(document)

    return _build_document_detail_payload(db, document)


@router.post(
    "/{document_id}/versions",
    response_model=EditableDocumentVersionOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document_version(
    document_id: int,
    payload: EditableDocumentVersionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    current_user_id = _resolve_current_user_id(db, current_user)
    latest_version_number = (
        db.query(EditableDocumentVersion.version_number)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .limit(1)
        .scalar()
    )
    next_version_number = (latest_version_number or document.current_version_number or 0) + 1
    payload_sections = [section.model_dump() for section in payload.sections]
    payload_metadata = payload.metadata or {}

    def _section_has_assisted_origin(section):
        section_source = str(section.get("source") or "")
        section_metadata = section.get("metadata") or {}
        generation_mode = str(section_metadata.get("generation_mode") or "")
        return (
            section_source == "assisted_draft"
            or generation_mode == "assisted_draft_from_analysis"
        )

    def _version_has_assisted_origin(version):
        if not version:
            return False
        version_metadata = version.version_metadata or {}
        version_source = str(version_metadata.get("source") or "")
        generation_mode = str(version_metadata.get("generation_mode") or "")
        sections = version.sections or []
        return (
            version_source == "assisted_draft_from_analysis"
            or generation_mode == "assisted_draft_from_analysis"
            or any(_section_has_assisted_origin(section) for section in sections)
        )

    if payload.approved:
        based_on_version_number = payload_metadata.get("based_on_version_number")
        base_version = None

        if based_on_version_number is not None:
            try:
                based_on_version_number = int(based_on_version_number)
            except (TypeError, ValueError):
                based_on_version_number = None

        if based_on_version_number is not None:
            base_version = (
                db.query(EditableDocumentVersion)
                .filter(
                    EditableDocumentVersion.editable_document_id == document.id,
                    EditableDocumentVersion.tenant_id == current_user["tenant_id"],
                    EditableDocumentVersion.version_number == based_on_version_number,
                )
                .first()
            )

        payload_has_assisted_origin = any(
            _section_has_assisted_origin(section) for section in payload_sections
        )

        if (
            not _is_audiencia_estrategica_document_type(document.document_type)
            and (payload_has_assisted_origin or _version_has_assisted_origin(base_version))
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Assisted draft versions cannot be approved directly. "
                    "Create a reviewed draft version and approve only after manual coherence validation."
                ),
            )

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=payload.approved,
        notes=payload.notes,
        sections=payload_sections,
        version_metadata=payload.metadata,
    )
    db.add(version)

    approved_version_number = (
        db.query(EditableDocumentVersion.version_number)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .limit(1)
        .scalar()
    )

    if payload.approved:
        document.current_version_number = next_version_number
        document.status = "approved"
    elif approved_version_number is not None:
        document.current_version_number = approved_version_number
        document.status = "approved"
    else:
        document.current_version_number = next_version_number
        document.status = "draft"

    db.add(document)

    db.commit()
    db.refresh(version)

    return version
