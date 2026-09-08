---
name: ancestry-research
description: Pesquisar árvores genealógicas e resolver filiações com fontes primárias, catálogo, imagens, paleografia e correlação documental. Use para localizar registros ou avançar além de um muro genealógico.
---

# Ancestry Research — pesquisa com fontes primárias

Avance uma ligação documentada por vez, a partir de uma pessoa conhecida.

## Entrada operacional

Para executar uma rodada, leia primeiro [execução guiada](references/14-execucao-guiada.md)
e preencha a [ficha de operação](templates/operation_card.template.md) no acervo do projeto.
Depois abra apenas a receita pertinente em [receitas operacionais](references/15-receitas-operacionais.md):
A DigitArq; B livros/inventários; C FamilySearch; D documentos/imagens; E datas/entrevistas;
F Gramps/auditoria/desenho; G correspondência/imigração; H APIs/aprendizado;
I CRAV/reprodução/orçamento.
O ciclo abaixo orienta a pesquisa; o roteiro detalha as verificações antes de cada avanço.

Modelos compactos executam unidades verificáveis; leitura ou identidade ambígua pede
revisão da evidência. Preserve pendências e continue as partes independentes autorizadas.

## Ciclo de pesquisa

### 1. Definir alvo, âncoras e pergunta

Recupere primeiro os documentos e o diário já disponíveis. Registre nome e variantes,
datas (com indicação de estimativa), lugares históricos, pais/cônjuge/filhos conhecidos
e exatamente o que falta. Pergunte só pelo que realmente não puder ser recuperado.
Frentes independentes são possíveis dentro do pedido; cada uma deve ter recorte claro.

### 2. Identificar acervo e cobertura

- **Portugal:** DigitArq, Torre do Tombo e Arquivos Distritais. Identifique o detentor
  na ficha; `PT/TT/PRQ/...` é exemplo, não prefixo universal. Copie a cota real e confirme
  séries, datas e imagens do livro, não apenas do fundo.
- Para época posterior ao fundo paroquial, procure o **registro civil**. A transição de
  1911 orienta a busca, mas não prova ausência do registro nem sua custódia atual.
- **Brasil:** FamilySearch para registros civis e paroquiais; arquivos locais e
  cartórios conforme lugar/época. Para o período colonial, AHU/Projeto Resgate.
- **Imprensa:** hemerotecas da Biblioteca Nacional brasileira e portuguesa.

Para imigração, consulte [o roteiro](references/10-imigracao-portugal-brasil.md).
Para recuperar links antigos ou avaliar catálogos por API, use
[APIs públicas complementares](references/13-apis-publicas-e-arquivo-web.md).

Leia os guias de [DigitArq](references/01-portugal-torre-do-tombo-digitarq.md),
[FamilySearch](references/02-familysearch.md) ou [outros arquivos](references/08-outros-arquivos.md)
conforme a frente. Não extrapole lacuna de uma entrada do catálogo para todos os acervos.

Para pedir reproduções ou orientação aos arquivos DGLAB, consulte
[o fluxo CRAV](references/16-crav-pedidos-reproducao.md); protocolo de pedido não é prova do ato.

### 3. Procurar o documento que responde à pergunta

**Casamento** costuma render filiação e naturalidade de ambos os cônjuges. Para data
natal, prefira o próprio nascimento/batismo contemporâneo, distinguindo esses eventos.
Óbitos, habilitações e notariais complementam as âncoras; o informante e a proximidade
do evento importam. [Tipos de registro](references/04-tipos-de-registo.md).

- **DigitArq:** ficha é descrição de catálogo, não leitura da imagem. Preserve total,
  returned, notes e IDs únicos; limite, ordenação e filesCount não provam cobertura
  completa nem acesso ao conteúdo. Use a receita A e confirme disponibilidade no livro.
- **FamilySearch:** use a sessão autorizada; descubra perfis/abas em vez de assumir
  nome de perfil. Comece por fontes vinculadas e sugestões dos perfis pertinentes.
  Distinga árvore editada, índice, OCR, catálogo e imagem.
- Varie grafias/nomes compostos; relaxe um filtro por vez. Pesquise pelo casal parental
  sem o nome do filho. Campo “exact”, data ou naturalidade incorreta no índice pode
  ocultar a pessoa certa. Dois nomes na mesma página não necessariamente formam um casal.
- **Familiares:** irmãos, cônjuges, avós e testemunhas podem resolver variantes maternas,
  naturalidades e migração. Compare filiação, cronologia, cônjuge e endereço na época.
  Nome/endereço isolado não basta; padrinho homônimo não é automaticamente o avô.
  [Correlação e arquivo](references/09-correlacao-e-arquivo.md).
- **Registro tardio:** busque também o contemporâneo no local de nascimento. Não
  confunda local/data do evento com os da lavratura ou da emissão da certidão.

### 3b. Livro sem índice

Só varra livro pertinente e acessível. Valide início, IDs únicos e lacunas antes de aceitar
cada lote; posição da imagem não é fólio e download não é leitura.
Siga a receita B de [execução operacional](references/15-receitas-operacionais.md)
e a validação de paginação do [guia DigitArq](references/01-portugal-torre-do-tombo-digitarq.md).
Delegue lotes somente quando permitido e houver trabalho independente; cada leitor
devolve cobertura, fileId/fólio, transcrição, confiança e candidatos. Caso contrário,
leia localmente. [Protocolo de lotes](references/06-varredura-multiagente.md).

### 4. Ler a imagem e preservar o recebido

Baixe a imagem integral oferecida pela fonte, com verso, continuação e margens/retificações.
Captura de tela deve ser identificada como captura. PDF sem texto pode ser um escaneamento:
renderize para leitura, mantendo o arquivo recebido intacto.

Transcreva literalmente primeiro; normalize em separado, indique transcrição parcial e
marque `[?]` no incerto. Use recortes, ampliação e contraste como derivados e compare
com a imagem sem tratamento. Nunca reconstrua letras por geração de imagens.
Abreviaturas e dificuldades de leitura: [paleografia](references/03-paleografia.md).
Guarde número do termo/retificações; posição no visualizador não é fólio.
Em inventários, examine anexos tardios e certidões: [leitura de processos](references/11-inventarios-e-certidoes-anexas.md).

### 5. Correlacionar e registrar

Use o [modelo de diário](templates/research_log.template.md) e a estrutura do projeto.

- **Estado por afirmação:** comprovada, declarada, calculada, hipótese, tradição familiar
  ou candidato excluído. Documento legível não confirma automaticamente toda afirmação.
- **Confiança por fato e vínculo:** alta/média/baixa com justificativa, informante quando
  conhecido, proximidade do evento, independência e contradições. Propague incerteza de
  identidade aos ascendentes; nunca funda pessoas só pelo nome.
- **Datas distintas:** evento, lavratura e emissão. Idade no óbito permite cálculo/intervalo
  natal, não data comprovada. Preserve idade literal, método e valores conflitantes.
- **Fontes dependentes:** páginas, segunda via, fotografia e índice do mesmo ato não são
  confirmações independentes. Distinga arquivos, atos, eventos e vínculos novos.
- **Citação e arquivo:** instituição, jurisdição, cota, livro/folha/termo, ARK/GUID/fileId
  e imagem disponíveis; campos ausentes ficam não identificados. Preserve originais,
  derivados, transcrições e índice com origem, tamanhos e SHA-256.
- **Negativa delimitada:** consulta/filtros realmente aplicados, total/retornados e imagens
  efetivamente lidas. Falha de acesso, ausência no índice ou resposta parcial não provam
  inexistência do registro.

Para correlação de nomes, correspondência, organização e pacotes com integridade verificada,
leia [correlação e arquivo](references/09-correlacao-e-arquivo.md). A imagem e a justificativa permitem revisão humana; prossiga com atualizações locais já autorizadas.
Negativas delimitadas e candidatos excluídos também são progresso.

### 6. Iterar sem perder contexto

Escolha a próxima pergunta pela nova âncora. Registre recorte, hipóteses concorrentes e
documento capaz de distingui-las; continue as frentes autorizadas com avanço possível.
Uma pista não fecha linhagem. Para datas ausentes e entrevistas, siga
[correlação e arquivo](references/09-correlacao-e-arquivo.md). Ao atualizar uma base
Gramps ou uma visualização autorizada, use [migração e manutenção](references/12-gramps-e-arvores-visuais.md). [Metodologia](references/00-metodologia.md).

## Ferramentas especializadas

Confira `--help` da versão instalada; saídas ficam no acervo do projeto.
- `scripts/digitarq.py`: search, details, images e download público; não sobrescreva originais.
- `scripts/image_tools.py`: crop, enhance, folio e split em derivados.
- `scripts/gedcom_audit.py`: auditoria somente leitura de exportação, não prova genealógica.
- `scripts/notify.py`: opcional, apenas para destino autorizado e autenticação protegida.
- [GEDCOM](references/07-gedcom.md) é opcional; [Inquisição](references/05-inquisicao-cristao-novo.md)
  só quando pertinente, sem presumir identidade por categoria histórica.

## Acesso, privacidade e escopo

O usuário faz login no site; senha, código, cookie e links de autenticação ficam fora do
chat, comandos e logs. Integrações usam entrada mascarada e referência protegida do
ambiente; sem fluxo seguro, continue pelo caminho documental disponível.

Mantenha só método genérico na skill. Imagens, árvores, GEDCOMs, emails, identificadores
privados e contatos ficam no projeto. Pesquisa, edição de árvore online, contato externo
e serviço pago são escopos distintos. Preserve autorizações e limites existentes;
uma minuta não é envio nem contrato, e consultas enviadas não devem ser duplicadas.

## Aprendizagem baseada em resultados

Quando autorizado, incorpore procedimentos demonstrados, não hipóteses genealógicas,
falhas transitórias ou tarefas pendentes. Use a ferramenta de autoria disponível, leia a
revisão vigente, preserve recursos e valide. Diferencie proposta de versão publicada.
Sincronizar Git exige comparar as mudanças do autor antes de exportar a versão revista;
a atualização pessoal não publica automaticamente no repositório de origem.
