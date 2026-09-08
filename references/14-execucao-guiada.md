# Execução guiada de pesquisa genealógica

Use este roteiro para uma rodada documental, especialmente com modelos compactos. Execute uma pergunta verificável por vez; abra somente a receita e a referência necessárias. O roteiro organiza trabalho autorizado, não cria permissão para contato, compra, publicação ou edição online.

## 1. Recuperar o estado antes de agir
1. Leia o diário e a ficha da pessoa-alvo no acervo canônico definido pelo projeto.
2. Anote a pergunta em uma frase: obter o ato natal, identificar pais, resolver homônimo, recuperar imagem ou atualizar dado já recebido. Data conhecida e assento obtido são estados diferentes.
3. Preencha a [ficha de operação](../templates/operation_card.template.md): identidade/IDs existentes, âncoras e fontes, conflitos, recursos já consultados, pergunta pendente, ações autorizadas e destino privado.
4. Escolha a receita em [receitas operacionais](15-receitas-operacionais.md). Se a resposta já está no acervo, confira a fonte antes de repetir busca ou contato.

**Pronto para avançar:** há alvo, pergunta, evidência de partida, destino e limite de ação identificados. Dado ausente fica nulo/não identificado; não complete por intuição.

## 2. Escolher e executar a próxima ação
- Para nascimento, tente o registro próprio; casamento fornece filiação e naturalidades; habilitação pode conservar certidões. Use inventário/parentes quando existe ligação documentada ou candidato explicitamente separado.
- Primeiro registre o que a coleção cobre: instituição, local histórico, tipo de ato, faixa por livro e acesso. Ano final de um fundo, projeto de digitalização e período de um volume são coisas distintas.
- Consulte fontes anexadas e referências exatas antes de buscas amplas. Mude um filtro por vez; registre consulta e resultado. Não repita a mesma chamada esperando que o mesmo resultado prove mais.
- Use `--help` do script instalado antes de construir comando. Copie IDs/cotas da resposta observada; placeholders nos guias não são valores reais.
- Diferencie erro da ferramenta de negativa documental. Para login/restrição, siga outra frente permitida e registre o bloqueio; não fabrique endpoints nem extraia autenticação.

**Pronto para avançar:** resposta preservada, filtros observados, IDs e limites registrados; se não houver conteúdo pertinente, registre a negativa delimitada e escolha outra ação.

## 3. Validar arquivo e cobertura
1. Compare nome, tipo real, tamanho e SHA-256. Um HTML salvo como PDF não é certidão. Texto extraído vazio exige verificar se o documento é imagem.
2. Verifique se é download integral, captura, índice, transcrição ou segunda via. Arquive original recebido sem alteração; use derivados para renderização, recorte e contraste.
3. Registre o conjunto de IDs recebidos e o conjunto realmente examinado. Só conte como lida uma imagem aberta e examinada. Texto fornecido por terceiro é leitura indireta, não inspeção visual sua.
4. Em lotes, compare início recebido, IDs, total e lacunas. Índice errado ou lote repetido interrompe a aceitação dessa página; mantenha a cobertura válida anterior. Avance pela quantidade recebida validada.
5. Cite imagem/fileId separadamente de fólio/termo. Leia cabeçalho, continuação e margens antes de concluir ausência de informação.

**Pronto para avançar:** o arquivo é o esperado e a cobertura descreve precisamente o que foi visto, sem contar download ou repetição como nova leitura.

## 4. Extrair sem resolver cedo demais
Produza uma linha por afirmação, não uma confiança única para todo o documento:

| Campo | Preencher |
|---|---|
| pessoa/ID candidato | Perfil existente ou candidato separado |
| evento | nascimento, batismo, lavratura, emissão, casamento, óbito, migração |
| literal | palavras/números do trecho; `[?]` em incerteza |
| normalizado | forma pesquisável, mantendo o literal |
| fonte e localização | instituição/cota, página/folha/termo ou lacuna |
| estado | declarado, calculado, tradição, hipótese, comprovado ou excluído |
| suporte/contradição | por que a leitura e a identidade são ou não sustentadas |
| dependência | mesmo ato, cópia, índice ou declaração independente |

- Separe evento, lavratura e emissão; uma certidão tardia pode transcrever evento antigo.
- Para idade em anos completos na data D, use o intervalo **(D menos idade+1 anos, D menos idade anos]**, convertendo o limite inferior exclusivo no dia seguinte para uma faixa inclusiva. Mostre idade literal e cálculo. Se houver 29 de fevereiro, unidade ambígua ou idade aproximada, não force precisão diária; registre o limite e revise o cálculo.
- “Ano A ou B” permanece duas alternativas, não intervalo contínuo nem escolha automática.
- Campo de óbito ausente não gera evento de óbito. Campo incoerente em OCR fica como erro/pista até a imagem ser lida.
- Não normalize letra ambígua para coincidir com a hipótese. Retorne ao original, compare traços na página e mantenha variantes; se a leitura decisiva continuar incerta, peça revisão dessa leitura e continue as partes independentes.

**Pronto para avançar:** cada dado tem origem e qualificador; divergências não foram apagadas, datas calculadas não foram promovidas a comprovadas.

### Conferência de extração antes da conclusão
Releia a tabela comparando cada nome, ID/cota/termo, data e parentesco com o trecho do
alvo atual. Não transporte identificadores ou números de outra pessoa, processo ou
tarefa, mesmo quando o formato é semelhante. Campo não fornecido continua não identificado.
Para relações “antes/depois”, compare os valores ordenados antes de redigir: escreva
data menor < data maior e então expresse a relação. Uma inversão no resumo invalida
a frase, ainda que o cálculo ou a ferramenta estejam certos. Separe alertas heurísticos
de auditoria (por exemplo, suspeita de BIRT indevido) de fatos confirmados.

## 5. Resolver identidade e decidir mudanças
Compare pais, avós, cônjuge, datas, lugares e residência na época numa matriz. Conte independência de atos, não quantidade de arquivos ou leitores.

| Situação | Ação |
|---|---|
| Apenas nome/endereço/índice concorda | Candidato, sem fusão ou filiação nova confirmada |
| Campo ausente | Identidade não resolvida; procurar a âncora faltante |
| Pais, cônjuge ou cronologia incompatíveis | Manter separado; registrar conflito e documento discriminante |
| Variações de nome com ponte documental | Explicar a ponte, registrar qualificadores e alternativas |
| Certidão da criança confirmada, adulto ainda sem ponte | Registrar criança; não transferir automaticamente os ascendentes ao adulto |
| Segunda união após óbito | Manter famílias distintas; filhos só na união/filiação sustentada |

Não use número fixo de coincidências ou pontuação como prova. Uma contradição não resolvida não desaparece por maioria de fontes dependentes. Para fusão, filiação conflitante ou leitura decisiva, a saída pode ser **revisão necessária**, com a evidência exata e a pergunta que falta resolver.

## 6. Alterar somente o que está sustentado
Para atualização autorizada: faça backup verificável, resolva IDs existentes, escreva uma lista `objeto: antes → depois; fonte; motivo`, aplique a mudança mínima e releia os objetos. Nunca execute importação completa como atalho para atualizar uma pessoa. Falha de verificação impede declarar conclusão: preserve logs e restaure somente pelo procedimento validado da instalação.

Atualize ficha da pessoa, fontes, diário, perguntas e índice do acervo. Não reescreva arquivos históricos ou originais para fazer a nova leitura parecer antiga. A árvore visual deriva dos dados reconciliados; candidatos e datas incertas precisam de marca visível.

## 7. Encerrar com evidência
Confira manifestos/links e backup efetivamente produzido quando houve alteração. Feche apenas recursos temporários de sua autoria. Entregue:
- achado e estado (documento lido, índice, relato, cálculo ou candidato);
- fonte reencontrável e o que sustenta;
- ação realmente executada e artefato preservado;
- limites/cobertura e próximo passo concreto.

“Sem achado” é válido quando o recorte foi registrado. Não declare imagem lida, conta criada, mensagem enviada, backup restaurável, skill publicada ou push concluído sem resultado correspondente.
