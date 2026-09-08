# CRAV — obter documentos custodiados pela rede DGLAB

Use quando o catálogo aponta para documentação de um arquivo da rede DGLAB, mas a imagem
não está disponível/completa, ou quando é necessário pedir reprodução, pesquisa ou certidão.
O [CRAV](https://crav.arquivos.pt/login) é um balcão de atendimento: não é uma base nominal
alternativa nem uma API anónima de assentos. Confira a instituição que guarda o documento.
Fluxo de reprodução observado em 08/09/2026; confirme rótulos, condições e opções atuais.

## 1. Escolher a modalidade pelo resultado necessário

| Necessidade | Modalidade observada | Limite |
|---|---|---|
| Orientação genérica sobre acervo ou serviço | Pedido de Informação | Não equivale a encomendar pesquisa documental |
| Encontrar informação sem referência suficiente | Pedido de Pesquisa | Verificar custos e cobertura antes de autorizar trabalho |
| Ler uma imagem/cópia de documento identificado | Pedido de Reprodução | Cópia simples não é certificação legal |
| Certificação para finalidade que a exige | Pedido de Certidão | Não selecionar só porque o documento é um assento |
| Consultar presencialmente | Pedido Antecipado de Consulta / Consulta Presencial | A opção presencial observada vale para o próprio dia |
| Atualizar informação de documento | Pedido de Averbamento | Não usar para corrigir a árvore ou um erro de índice |

**Conclusão da escolha:** modalidade, detentor, documento e finalidade estão definidos.
Pedido de cópia de um ato e pedido de leitura integral de um livro são escopos diferentes.

## 2. Preparar sem duplicar pedidos ou expor dados

1. Recupere a resposta do arquivo, minutas, pedidos enviados, protocolos e imagens já
   obtidas. Uma certidão anexa a outro processo pode ter resolvido a busca natal inicialmente
   proposta; retire apenas essa busca redundante, não a referência histórica.
2. Para cada ato, anote nomes como constam do catálogo, tipo, data, paróquia/concelho,
   código de referência individual, referência do livro e URL reencontrável.
   Registe divergências com a identidade familiar; a descrição ainda não é imagem lida.
3. Use a [ficha de pedido](../templates/crav_request.template.md) no acervo privado.
   Reutilize dados atuais autorizados do titular; não escolha morada antiga de certidão.
4. Confirme o escopo autorizado de envio e de custos. Se só houve autorização para
   orçamento, diga explicitamente que a execução onerosa depende de aceitação posterior.
   Se as condições do portal vincularem a submissão a pagamento/execução não autorizada,
   prepare o formulário e pare antes desse compromisso, apresentando as condições.
5. Consulte os pedidos existentes antes de reenviar uma submissão de resultado incerto.
   Não clique novamente em Submeter apenas porque a resposta inicial demora.

**Pronto:** uma minuta por ato, referências verificadas e limites de despesas claros.
Nunca introduza credenciais, números de identificação pessoal, protocolos reais ou
documentos familiares no repositório desta skill.

## 3. Cadastro e autenticação

O cadastro é gratuito segundo a interface consultada; serviços documentais podem ter custo.
No cadastro observado há email, nome, nascimento, nacionalidade, identificação civil,
habilitações, profissão/atividade e morada, além de senha. Campos e listas podem mudar.
Mapeie apenas os valores realmente oferecidos e registe a correspondência quando não há
opção exata. Não adira a eventos ou inquéritos opcionais sem autorização.

O titular preenche senha e identificação diretamente no portal ou por mecanismo protegido
permitido pelo ambiente. Não recolha senha, código, cookie, token ou URL de retorno de login
para o contexto do modelo, comandos ou relatórios. Evite imprimir URLs de abas de callback:
podem conter credenciais no fragmento mesmo quando o título só diz CRAV.

**Teste de acesso:** nome no cabeçalho não basta. Abra **Novo pedido** e confirme que as
modalidades e o formulário carregam; conta visível e área de trabalho utilizável são
estados distintos.

### Recuperação delimitada de sessão

Se o retorno de Autenticacao.Gov permanecer em “Por favor aguarde” ou gerar
“ERR_TOO_MANY_REDIRECTS”:
1. Registe só a mensagem e a etapa, sem a URL de autenticação.
2. Tente Sair pela interface e reabrir a página pública de login uma vez.
3. Se persistir, compare com perfil separado sem a sessão problemática. Quando o
   formulário público abre, peça ao titular para entrar com email/senha do CRAV,
   se dispõe dessa modalidade. Não crie conta duplicada nem transfira tokens.
4. Só considere a recuperação verificada quando Novo pedido realmente abrir.
   Um teste anónimo positivo não prova login completo. Se ambas as vias falharem,
   conserve as minutas e descreva o bloqueio; não classifique como negativa do acervo.

A alternativa email/senha funcionou num caso observado; isso não prova defeito permanente
da autenticação Gov nem autoriza limpeza global de cookies. Feche apenas recursos
temporários de sua autoria; preserve a sessão que o titular está usando.

## 4. Reprodução de um assento com cota individual

Sequência observada: **Novo pedido → Pedido de Reprodução → Iniciar Pedido →
Documento → Detalhes → Confirmação de Dados**.

1. Em Iniciar Pedido, escolha **Código de referência/cota** quando já existe referência
   exata. Há também formulário **Paroquiais e Registo Civil**; use os campos observados,
   sem inventar uma cota para desbloquear o formulário.
2. Em Documento, selecione o arquivo detentor e introduza o código individual.
   Use Informação adicional para data, nomes do catálogo, propósito, margens/continuação
   e limites de orçamento. Não preencha o campo Cota atual por suposição.
3. O portal pode resolver automaticamente uma cota atual. Confira-a na revisão e cite-a
   como metadado do portal, ainda não como leitura do fólio original. O sufixo numérico
   de uma referência não é automaticamente número de termo ou folha.
4. Em Detalhes, para leitura genealógica simples escolha **Digital**, finalidade
   **Investigação** e entrega **Descarregar a partir da web**, quando disponíveis.
   Use **Total** apenas se o código identifica o assento individual desejado. Se identifica
   um livro, Total pode encomendar o livro inteiro: delimite a parte e não invente a
   quantidade de páginas quando o formulário a exige.
5. Na Confirmação de Dados, releia arquivo, referência, cota resolvida, tipo/extensão,
   finalidade, entrega e texto sobre custos. Corrija antes de marcar
   **Confirmo que os dados estão corretos**.
6. Submeta uma vez dentro da autorização. Aguarde uma confirmação observável de sucesso
   e abra **Meus pedidos** para localizar protocolo, documento e estado.
   Campos desativados durante envio não justificam um segundo clique.

**Saída:** protocolo associado à referência solicitada e estado confirmado.
“Em processamento” não significa reprodução entregue, orçamento aceite ou pagamento.

## 5. Preservar comprovativo e acompanhar

1. Em Os meus pedidos, confira a linha do protocolo e a referência. Use
   **Imprimir comprovativo** quando disponível; o fluxo observado descarregou um PDF.
2. Valide formato real e leia o PDF para confirmar protocolos e cotas. Preserve os bytes
   recebidos, SHA-256 e nome original de download; uma captura textual ou de ecrã fica
   identificada separadamente, não substitui silenciosamente o comprovativo oficial.
3. Guarde o texto efetivamente enviado e a associação ato → protocolo. Horários do PDF
   e da interface podem diferir; conserve ambos literalmente se o fuso não estiver
   indicado, sem converter por intuição.
4. Atualize fontes, diário, questões e perfis autorizados como **correspondência
   administrativa**. Não crie casamento/nascimento novo a partir da submissão.
   Se o projeto usa Gramps e site privado, siga a atualização documentada da instalação,
   com IDs estáveis, backup, sincronização e verificação, sem reimportar a árvore.
5. Mantenha as minutas antigas como histórico, acrescentando o estado posterior.
   Aguardar orçamento é uma pendência; não repetir o pedido a cada rodada.
   Só aceite/pague dentro de autorização específica de custos.
6. Quando chegar a reprodução, confira o ato, continuação, margens, filiação e
   naturalidades; só então reavalie candidatos. Receber o documento não resolve
   automaticamente a identidade pesquisada.

**Fechamento:** comprovativo e texto arquivados, protocolo/estado conferidos, destinos
privados atualizados conforme escopo, despesas e leituras ainda pendentes declaradas.
