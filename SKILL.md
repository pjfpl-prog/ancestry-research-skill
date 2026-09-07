---
name: ancestry-research
description: Pesquisar árvores genealógicas e resolver filiações com fontes primárias, catálogo, imagens, paleografia e correlação documental. Use para localizar registros ou avançar além de um muro genealógico.
---

# Ancestry Research — pesquisa com fontes primárias

Avance uma ligação documentada por vez, a partir de uma pessoa conhecida.

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

Leia os guias de [DigitArq](references/01-portugal-torre-do-tombo-digitarq.md),
[FamilySearch](references/02-familysearch.md) ou [outros arquivos](references/08-outros-arquivos.md)
conforme a frente. Não extrapole lacuna de uma entrada do catálogo para todos os acervos.

### 3. Procurar o documento que responde à pergunta

**Casamento** costuma render filiação e naturalidade de ambos os cônjuges. Para data
natal, prefira o próprio nascimento/batismo contemporâneo, distinguindo esses eventos.
Óbitos, habilitações e notariais complementam as âncoras; o informante e a proximidade
do evento importam. [Tipos de registro](references/04-tipos-de-registo.md).

- **DigitArq:** `python scripts/digitarq.py search "TERMO" --json` e
  `python scripts/digitarq.py details {GUID} --json`. A ficha é descrição de catálogo,
  não leitura da imagem. A busca pagina até `--max` (teto 500): preserve `total`,
  `returned` e `notes`. Para nomes, relevância favorece descoberta, mas pode repetir ou
  saltar resultados; para cotas, use `--sort reference_code`. A ordenação não congela
  o acervo. `--with-images` filtra no servidor; `filesCount` conta ficheiros, não prova
  conteúdo ou acesso. Confirme a disponibilidade no livro.
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

Só varra um livro pertinente e acessível. Procure índice interno e delimite anos/fólios.
Use `python scripts/digitarq.py images {GUID} --start 0 --max 10 --json` para um lote.
`--start` é de base zero e envia `fromIndex`. Confirme o índice retornado antes de usar
o lote; o script rejeita índice ausente, inválido ou diferente do pedido. Compare IDs
entre lotes e avance pelo índice recebido mais a quantidade recebida, não pelo limite
pedido. A posição da imagem não é fólio. Confira cobertura conforme o guia DigitArq
(§5.1); lotes de 10–13 imagens são um ponto de partida, ajustável à densidade.

Quando houver trabalho independente e delegação permitida, distribua lotes entre
subagentes; caso contrário, faça a mesma leitura localmente. Cada lote devolve cobertura,
fólio/fileId, transcrição, confiança e candidatos/homônimos. O limite de pedidos é por processo: conte a carga conjunta sobre o arquivo e ajuste
concorrência e pausas. O coordenador reconcilia os
achados, sem aceitar pontuação automática como prova. O
[protocolo](references/06-varredura-multiagente.md) e o
[template](templates/scan_workflow.example.js) são adaptáveis, não automação pronta.

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

Confira `--help`; instale só dependências necessárias. Saídas ficam no projeto.

- `scripts/digitarq.py`: search, details, images e download público. Downloads recusam
  conteúdo não-imagem e sobrescrita sem `--force`; preservam arquivo anterior em falha.
- `scripts/image_tools.py`: download, crop, enhance, folio e split em derivados.
- `scripts/gedcom_audit.py arvore.ged --walls --json`: auditoria somente leitura;
  preserva tratamento de FAMC/CHIL, datas aproximadas, PEDI e STAT disproven.
  [GEDCOM](references/07-gedcom.md): exportação opcional, nunca requisito de pesquisa.
- `scripts/notify.py`: notificador opcional; use só destino autorizado e credenciais
  protegidas. A versão atual redige tokens em erros; não configure por estar incluída.
- [Inquisição](references/05-inquisicao-cristao-novo.md): só quando pertinente;
  categoria histórica não presume identidade.

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
