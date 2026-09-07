# Referência: FamilySearch

FamilySearch (familysearch.org) é o maior acervo gratuito de genealogia do mundo, mantido pela
Igreja SUD. Tem bilhões de registos indexados, milhões de imagens digitalizadas de livros
paroquiais e civis, e uma camada recente de **busca por texto completo via OCR/IA**.

> **Sessão autorizada.** O acesso depende do conteúdo e da conta. Quando o usuário
> autorizar a sessão existente, descubra os perfis e abas disponíveis; não assuma um
> nome de perfil nem repita um diagnóstico antigo de login indisponível. O usuário faz
> login no próprio site. Não extraia cookies, senhas, códigos ou links de autenticação.
> Use controles observados e respeite as restrições das coleções.

---

## 1. Três motores de busca distintos (não confundir)

FamilySearch tem três sistemas de busca que respondem a perguntas diferentes. Saber qual usar é
metade do trabalho.

| Motor | URL base | O que pesquisa | Quando usar |
|---|---|---|---|
| **Registos indexados** | `/search/record/results` | Campos extraídos por humanos/IA (nome, pais, cônjuge, datas, lugares) | Quando há um índice por NOME — busca rápida e estruturada |
| **Texto completo (OCR/IA)** | `/search/full-text/results` | Texto bruto reconhecido dentro das imagens, mesmo de livros **não indexados** | Quando o livro não tem índice por nome, ou para achar menções soltas (testamentos, notariais) |
| **Catálogo** | `/search/catalog/results` | Os *acervos/livros em si* (não as pessoas) — que livros existem para um lugar | Para descobrir QUE fontes existem para uma paróquia/concelho/município |

### 1.1 Registos indexados — `/search/record/results`

Busca estruturada por campos. Parâmetros úteis (query string `q.*`):

```
https://www.familysearch.org/search/record/results
    ?q.givenName=NOME_PROPRIO
    &q.surname=APELIDO
    &q.spouseGivenName=NOME_DO_CONJUGE
    &q.spouseSurname=APELIDO_DO_CONJUGE
    &q.fatherGivenName=...&q.motherGivenName=...
    &q.birthLikePlace=LUGAR&q.birthLikeDate.from=ANO&q.birthLikeDate.to=ANO
    &q.deathLikePlace=LUGAR
    &q.marriageLikePlace=LUGAR
```

Dicas:
- Os campos `*LikePlace` e `*LikeDate` toleram aproximação — use intervalos de data largos.
- O **casamento** é o registo mais valioso para subir gerações: indexa os pais do noivo E da noiva.
  Pesquisar por `q.spouseSurname` é uma forma poderosa de cruzar um casal.
- Resultados podem ser filtrados por coleção depois de carregar (facetas à esquerda).
- Nem tudo indexado tem imagem; e nem tudo imageado está indexado (ver §1.2).
- Quando já houver árvore acessível, abra fontes vinculadas e sugestões dos perfis do
  alvo, pais e irmãos antes de buscas amplas. Fonte anexada ao pai pode documentar apenas
  o casamento do filho; a anexação não comprova todos os campos do perfil.
- Faça buscas progressivas: grafias e nomes compostos; casal/conjugação de pais; somente
  os pais, sem nome do filho. Retire "exact", data e local um de cada vez e registre o efeito.
  Naturalidade, prenome e ano podem estar indexados incorretamente; uma busca muito restrita
  pode excluir a própria família.
- Se há registro tardio, procure também o contemporâneo no lugar de nascimento. Não
  confunda a data ou o local de lavratura com os do evento.

### 1.2 Texto completo (OCR/IA) — `/search/full-text/results`

Lê o texto *dentro* das imagens, incluindo acervos sem índice por nome. Excelente para "muros"
onde o livro existe mas ninguém indexou.

```
https://www.familysearch.org/search/full-text/results?q.text="FRASE EXATA"
```

- Use **aspas** para frase exata: `q.text="filho de FULANO e de SICRANA"`.
- Combine termos do jargão de assento (ver §4) com nomes: `q.text="testamento de TERMO"`.
- A IA comete erros de leitura paleográfica — varie a grafia (acentos, abreviaturas, nomes
  devocionais como "da Conceição"/"de Jesus"/"dos Santos").
- Cada resultado aponta para imagem/excerto. **Abra a imagem e confirme**: OCR é pista,
  não prova. Dois nomes podem estar em notícias ou termos distintos na mesma página.
- Quando nomes forem requisitos conjuntos, prefixe cada termo/frase por `+`, como
  `+"NOME DO PAI" +"NOME DO FILHO"`, e confira a consulta e o total na interface.
  Frases apenas separadas por espaços podem ampliar a busca; não presuma interseção.
- Compare leitura automática com cabeçalho, número do termo e retificações; não corrija
  silenciosamente um índice. Cite o índice errado e a leitura manuscrita com a fonte.
- Restrinja por coleção/grupo de imagens quando conhecido; se não houver resultado,
  varie grafias e termos. Ausência no OCR não equivale a varredura integral do livro.

### 1.3 Catálogo — `/search/catalog/results`

Inventário de acervos, não de pessoas. Responde "que livros existem para este lugar?".

```
https://www.familysearch.org/search/catalog/results?q.placeName=LUGAR
```

- Pesquisar pelo nome do lugar **na época** (concelho/freguesia em Portugal; município/distrito no
  Brasil) revela coleções de registos paroquiais, civis, notariais, etc.
- Cada entrada lista filmes/livros e condições de acesso. Consulte também as páginas
  seguintes das notas digitais; leia tipos e datas por volume, não apenas a faixa da coleção.
- Copie jurisdição histórica, livro, filme/DGS/grupo de imagens, item e referência do catálogo.
  Se faltar um ano numa entrada, registre essa lacuna sem concluir ausência no município.

---

## 2. Ler um registo ARK

ARK ("Archival Resource Key") é o identificador permanente de cada item no FamilySearch. Formato:

```
https://www.familysearch.org/ark:/61903/<ARK>
```

O **prefixo do ARK** indica o tipo:

| Prefixo | Tipo | Significa |
|---|---|---|
| `1:1:` | **Registo indexado** | Uma pessoa/evento extraído (campos estruturados) — ex.: `ark:/61903/1:1:XXXX-XXX` |
| `3:1:` | **Imagem** | Uma imagem digitalizada (frame de filme/livro) — ex.: `ark:/61903/3:1:XXXX-XXX` |

Fluxo típico: um registo `1:1:` muitas vezes **liga** à imagem `3:1:` correspondente ("View the
original document" / "Document Information"). Sempre que possível, salte do indexado para a imagem
e leia o assento original — o índice resume e por vezes erra.

- Um item `1:1:` traz os campos extraídos + a coleção de origem + (às vezes) o link para a imagem.
- Um item `3:1:` é a imagem em si, exibida num **visualizador deepzoom** (ver §5 sobre limitações).

---

## 3. Coleções paroquiais e civis

### 3.1 Portugal

- **Registos paroquiais** (baptismos, casamentos, óbitos) digitalizados, muitos do séc. XVI ao XX.
  Procurar no catálogo pelo nome da **freguesia** e do **concelho**.
- Sobreposição parcial com os Arquivos Distritais portugueses e com a Torre do Tombo/DigitArq —
  o mesmo livro pode estar nos dois sítios; o FamilySearch frequentemente tem OCR/índice por nome
  que o arquivo de origem não tem. (Ver `01-portugal-torre-do-tombo-digitarq.md` para a Torre do Tombo.)
- **Registo civil** português (a partir de 1911, e antes em alguns lugares) também presente.

### 3.2 Brasil

- **Registos paroquiais católicos** (batismos, casamentos, óbitos) cobrem boa parte do período
  colonial e imperial; muitos imageados, parte indexada.
- **Registo civil** (nascimentos, casamentos, óbitos a partir do final do séc. XIX) por
  cartório/município.
- Pesquisar no catálogo pelo **município** (e pela divisão da época, pois fronteiras mudaram).
- Para o **Brasil colonial**, complementar com o Arquivo Histórico Ultramarino / Projeto Resgate
  (documentos administrativos) — fora do FamilySearch.

> Cobertura é desigual: algumas freguesias/municípios têm tudo online e indexado; outras só têm
> imagens sem índice (use full-text §1.2) ou só referência em microfilme (use o catálogo §1.3).

---

## 4. Vocabulário de assento (para full-text e leitura)

Reforço rápido (detalhe completo no guia de tipos de assento):

- **Casamento** — nomeia os PAIS do noivo E da noiva + naturalidades → melhor para subir uma geração.
- **Batismo** — pais (por vezes avós/padrinhos), data, às vezes naturalidade do pai.
- **Óbito** — filiação, estado civil, cônjuge, idade.
- Abreviaturas comuns: `P.e` (Padre), `f.o`/`f.a` (filho/filha), `m.er` (mulher), `R.do` (Reverendo),
  `N.S.a` (Nossa Senhora). Use-as como termos de busca no full-text.

---

## 5. Guardar imagens e, quando pertinente, GEDCOM

Para documentos, use o download oferecido pela interface e confirme que o arquivo recebido
é a imagem integral esperada. Preserve também as páginas de continuação, verso e margens.
Se Download abrir opções, selecione **JPG Only** para preservar a imagem sem destaques
da interface e confirme no botão final do diálogo. Verifique o formato real do arquivo:
a extensão escolhida para salvá-lo não prova que seja JPEG. Uma exportação PDF com
realces/citação fica separada como derivado, não como nova reprodução independente.
Se só houver captura de tela, identifique-a assim e registre a limitação.

Cite ARK de índice e de imagem, grupo/filme, número da imagem, livro, folha e termo quando
disponíveis. Posição no visualizador não é fólio. Mantenha as correções marginais e a
distinção entre ato original, segunda via e índice; veja
[correlação e arquivo](09-correlacao-e-arquivo.md).

Exportar GEDCOM é opcional. Só investigue a exportação se servir ao pedido e houver fluxo
de autenticação compatível com o ambiente. A ferramenta externa `getmyancestors` é uma
possibilidade histórica a verificar, não um caminho validado por estas rodadas. Não assuma
interface, acesso ou compatibilidade atuais. Nunca ponha senha em argumentos, comandos,
URLs ou variáveis/interpolação de shell; use a sessão autorizada ou entrada mascarada
suportada pelo ambiente. Se não houver exportação segura, continue a pesquisa documental.

Para uma avaliação autorizada de `getmyancestors`, preserve o isolamento de dependências
em `scripts/requirements-familysearch.txt` e confirme as flags da versão instalada.
A utilização da própria conta não autoriza recolha automatizada em massa: confira os
[termos vigentes](https://www.familysearch.org/legal/terms) e o escopo permitido.

Quando houver GEDCOM pertinente, audite a cópia local com `scripts/gedcom_audit.py`.
Arquivo exportado não torna as relações da árvore automaticamente comprovadas. Detalhes:
[GEDCOM](07-gedcom.md).

---

## 6. Limitações e armadilhas

- **Acesso variável.** Se houver exigência de login ou restrição de coleção, registre-a como
  limite de acesso, não como resultado negativo da pesquisa.
- **API oficial e elegibilidade.** Antes de configurar uma integração, leia o portal
  [oficial](https://developers.familysearch.org/), o formulário de inscrição que ele liga
  e os critérios vigentes. Existência de API, gratuidade e login no site não significam
  acesso automático para um projeto pessoal. Confira aprovação da aplicação, ambiente
  habilitado e autenticação OAuth suportada antes de declarar uma conexão ativa.
- **Escopo da API.** Distinga leitura de pessoas/relações/fontes de pesquisa em registros
  históricos e Full-Text. Não deduza disponibilidade por uma página promocional ou um
  exemplo antigo. Se o formulário atual restringir o caso ou divergir dos guias, registre
  a limitação e consulte o suporte oficial; não invente organização, escala ou finalidade
  para obter aprovação. A API não remove as restrições de acesso às imagens.
- **Visualizador e downloads.** A visualização pode usar mosaicos, mas algumas imagens têm
  download integral pela interface. Verifique a opção disponível, sem extrair sessão nem
  inventar URLs de mídia. Não confunda captura de tela com o arquivo integral.
- **Restrições de acesso** — algumas coleções estão limitadas (por contrato com o arquivo de
  origem) a centros de história familiar ou bloqueadas em certas regiões. O catálogo indica isso.
- **OCR/índice falham** — nomes mal lidos, datas trocadas, homónimos. Tratar todo resultado como
  pista; confirmar na imagem original; marcar `[?]` em leituras incertas.
- **Homónimos** — nunca apresentar um homónimo como prova de filiação. Cruzar sempre com
  cônjuge/pais/lugar/data. A verificação final é do utilizador.

---

## 7. Receita rápida

1. **Catálogo** (`/search/catalog`): que livros existem para este lugar/época? Há imagens online?
2. **Indexados** (`/search/record`): há índice por nome? Buscar a pessoa, e o casamento dela.
3. **Full-text** (`/search/full-text`): livro sem índice, ou menção solta? Buscar frase + nome.
4. Saltar de `1:1:` (indexado) para `3:1:` (imagem) e **ler o assento original**.
5. Preserve imagens integrais, citações e transcrições. GEDCOM só se pertinente e com
   autenticação segura; não é requisito para obter documentos.
6. Cruzar com a Torre do Tombo/DigitArq (`01-portugal-torre-do-tombo-digitarq.md`), Arquivos Distritais, AHU e hemerotecas
   para o que o FamilySearch não cobre.
