# Referência: FamilySearch

FamilySearch (familysearch.org) é o maior acervo gratuito de genealogia do mundo, mantido pela
Igreja SUD. Tem bilhões de registos indexados, milhões de imagens digitalizadas de livros
paroquiais e civis, e uma camada recente de **busca por texto completo via OCR/IA**.

> **Login obrigatório.** Quase tudo de útil (registos indexados, imagens, catálogo, full-text)
> exige conta. A conta é **gratuita**. A skill **nunca** guarda credenciais: o utilizador põe as
> dele via variáveis de ambiente / sessão de browser. Não há API pública com chave para o público
> geral — o acesso prático é via a sessão autenticada no browser do próprio utilizador.

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
- Cada resultado aponta para a imagem e ao excerto onde o termo apareceu. **Sempre abrir a imagem
  e confirmar** — o OCR é pista, não prova.

### 1.3 Catálogo — `/search/catalog/results`

Inventário de acervos, não de pessoas. Responde "que livros existem para este lugar?".

```
https://www.familysearch.org/search/catalog/results?q.placeName=LUGAR
```

- Pesquisar pelo nome do lugar **na época** (concelho/freguesia em Portugal; município/distrito no
  Brasil) revela coleções de registos paroquiais, civis, notariais, etc.
- Cada entrada do catálogo lista os filmes/livros, com indicação se têm imagens online, se estão
  restritos, ou se só existem em microfilme/centro de história familiar.

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
  que o arquivo de origem não tem. (Ver `01-digitarq.md` para a Torre do Tombo.)
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

## 5. Extrair a SUA árvore para GEDCOM — `getmyancestors`

Para puxar a árvore que o **próprio utilizador** já tem no FamilySearch para um ficheiro local
(`.ged`), use a ferramenta open-source **getmyancestors**.

- Pacote Python, instalável via `pip`. Projeto open-source (no PyPI / GitHub).
- Usa o **login do próprio utilizador** — não há API key. A autenticação é a sessão pessoal do
  utilizador na sua própria conta.
- Exporta a ascendência/descendência a partir de uma pessoa-raiz para **GEDCOM**, que depois se
  abre em qualquer software de genealogia (Gramps, etc.) ou se processa por script.

Instalação e uso (esqueleto — sem credenciais embutidas):

```bash
pip install getmyancestors

# Credenciais via ambiente — NUNCA hardcoded no script/repo:
export FS_USERNAME="$FAMILYSEARCH_USER"     # o utilizador põe o seu próprio
export FS_PASSWORD="$FAMILYSEARCH_PASS"

# Exporta a partir de uma pessoa-raiz (PID = identificador FamilySearch da pessoa, ex. XXXX-XXX)
getmyancestors \
  --username "$FS_USERNAME" \
  --password "$FS_PASSWORD" \
  --individual {PID_RAIZ} \
  --ascendancy {N_GERACOES} \
  --out arvore.ged
```

Notas:
- Passe as credenciais por variável de ambiente ou prompt interativo; **nunca** as escreva no
  código nem as commite. Trate `.ged` como dado pessoal (não versionar em repo público).
- A ferramenta extrai **a árvore do utilizador** — só puxa o que a conta dele já tem acesso/inseriu;
  não é um scraper geral do acervo.
- Depois de ter o GEDCOM, processe-o localmente (parsing por script, deduplicação, deteção de
  "muros" = pessoas sem pais conhecidos) para planear que assentos procurar a seguir.

---

## 6. Limitações e armadilhas

- **Login obrigatório** em tudo de prático. Sem sessão autenticada, as buscas retornam pouco ou
  nada. A skill assume que o utilizador autentica no seu próprio browser/sessão.
- **Sem API pública com chave** para o público geral. O acesso programático fiável é via a sessão
  já autenticada (browser). Não codifique fluxos que dependam de uma API key inexistente.
- **Imagens em deepzoom** — o visualizador serve as imagens em tiles (mosaicos) com zoom
  progressivo, o que torna a **raspagem direta difícil**: não há um JPEG único e simples por URL
  como nalguns arquivos (contraste com o DigitArq, que serve o JPEG inteiro por `fileId`). Para ler,
  prefira o download/print oferecido pela própria interface quando disponível.
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
5. Para a árvore própria: `getmyancestors` → GEDCOM (credenciais por env, ficheiro tratado como
   dado pessoal).
6. Cruzar com a Torre do Tombo/DigitArq (`01-digitarq.md`), Arquivos Distritais, AHU e hemerotecas
   para o que o FamilySearch não cobre.
