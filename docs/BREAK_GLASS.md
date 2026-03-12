# BREAK-GLASS — IA Trabalhista Robusta

## Objetivo
Este documento define o uso emergencial de acesso privilegiado no projeto **IA Trabalhista Robusta**, exclusivamente para contenção, diagnóstico ou recuperação de incidente crítico.

Princípios:
- acesso excepcional não é fluxo normal de operação
- todo uso de break-glass deve ser justificável, rastreável e temporário
- privilégio emergencial deve ser usado no menor escopo possível
- após o incidente, o contexto excepcional deve ser encerrado e revisado

---

## Escopo
Este documento cobre o uso excepcional de acesso ampliado em situações de:
- incidente grave em produção
- falha de autenticação ou autorização que impeça contenção
- falha operacional que exija diagnóstico privilegiado
- recuperação controlada após problema de banco, tenant ou configuração

---

## Quando o break-glass pode ser usado
O uso é admitido apenas quando houver necessidade real e imediata de:
- conter impacto relevante em operação crítica
- restaurar disponibilidade mínima do sistema
- diagnosticar incidente sem alternativa operacional segura no fluxo normal
- recuperar contexto administrativo estritamente para correção emergencial

## Quando o break-glass não pode ser usado
- conveniência operacional
- tarefas rotineiras de administração
- atalhos para evitar correção estrutural
- consulta indevida de dados de tenant sem motivo técnico legítimo
- atividades comerciais, testes improvisados ou exploração fora de incidente

---

## Regras de uso
- usar o menor nível de privilégio possível
- limitar o tempo de uso ao estritamente necessário
- atuar apenas sobre o escopo técnico do incidente
- evitar leitura ou exposição de dados além do necessário para contenção e diagnóstico
- preferir evidência objetiva e comandos reproduzíveis

## Registro obrigatório do uso
Toda ativação de break-glass deve registrar no mínimo:
- data e hora
- motivo do uso
- ambiente afetado
- operador responsável
- tenant ou recurso impactado, se aplicável
- ação executada
- resultado obtido
- horário de encerramento do acesso excepcional

---

## Encerramento obrigatório
Após o uso de break-glass, é obrigatório:
- encerrar o contexto excepcional imediatamente após a ação
- validar se o acesso ampliado deixou de estar ativo
- registrar evidência mínima do que foi feito
- avaliar necessidade de correção estrutural para evitar novo uso indevido

---

## Pós-uso e revisão
Todo uso de break-glass deve gerar revisão posterior para responder:
- o uso era realmente inevitável?
- houve excesso de privilégio?
- faltou ferramenta, rota ou observabilidade no fluxo normal?
- é necessário criar hardening para evitar repetição?

## Checklist mínimo
- houve motivo técnico real e urgente?
- o uso foi registrado com data, hora e responsável?
- o escopo foi limitado ao necessário?
- o contexto excepcional foi encerrado?
- houve revisão posterior do incidente?

## Dono operacional
Este documento deve ser revisado sempre que houver mudança relevante em autenticação, administração global, tenant isolation, incidentes de produção ou mecanismo de acesso privilegiado.
