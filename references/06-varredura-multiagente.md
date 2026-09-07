# Varredura multi-agente de livros NÃO indexados por nome

Referência operacional. Quando um livro (paroquial, notarial, processo) **não está
indexado ao nível do indivíduo** — o catálogo descreve o *livro*, não cada assento — a
busca por nome falha. A solução é **varrer página-a-página**, mas um livro tem dezenas
ou centenas de imagens; ler tudo numa só sessão é lento e a atenção degrada. O padrão é
**paralelizar**: dividir as imagens em lotes, despachar um subagente por lote, e
consolidar os achados.

> Modelo mental: você é o **coordenador**. Não lê o livro inteiro; lê a *lista* de
> imagens, distribui o trabalho, e reconcilia o que volta. Cada **subagente** é um
> trabalhador efémero que recebe ~10-13 imagens, baixa, lê e devolve achados
> estruturados — e nada mais.

Endpoints do DigitArq usados aqui estão em `01-portugal-torre-do-tombo-digitarq.md`;
a leitura paleográfica em `03-paleografia.md`; a disciplina de homónimo/confiança em
`00-metodologia.md`. Esqueleto de código em `templates/scan_workflow.example.js`.

---

## 1. Quando (e quando NÃO) varrer página-a-página

Varra só depois de ter esgotado o atalho. A varredura é cara — use-a quando há sinal e
não há índice.

**Use varredura quando:**
- O livro certo já está **localizado** (cota + `{GUID}` + datas que cobrem o ano-alvo) e
  `filesCount > 0` na busca (ou `hasImages: true` no `details`), mas a busca por nome não devolve o assento.
- **Não há índice onomástico** legível, ou o índice salta o nome procurado.
- O ano-alvo é conhecido com margem (ex.: "casou ~ANO ± 5"), de modo a que a varredura
  fique limitada a um intervalo de fólios, não ao livro inteiro.

**Não varra (ainda) quando:**
- Há **índice onomástico** — abra primeiro as últimas (ou primeiras) imagens; o índice dá
  o fólio e você salta direto (ver `01-...digitarq.md` §5.3).
- O registo pode estar **indexado por nome** noutra base (FamilySearch full-text/records);
  tente o atalho antes (ver `02-familysearch.md`).
- Você **não sabe se é o livro certo**: confirme cota, série e datas primeiro. Varrer o
  livro errado é puro desperdício.

---

## 2. Visão geral do padrão (3 fases)

```
FASE A — COORDENADOR: preparar
   1. localizar o livro: {GUID} + cota + datas (search/details)
   2. listar imagens:    GET /rdigital/{GUID}?from=0&max=500  -> results[].id = fileId
   3. (opcional) baixar miniaturas para mapear capa/índice/intervalo de anos
   4. recortar o intervalo de fólios plausível (não o livro inteiro, se houver âncora de ano)
   5. dividir os fileIds em LOTES de ~10-13

FASE B — SUBAGENTES (um por lote, em paralelo): ler
   para cada fileId do lote:
       baixar hi-res   -> curl dissemination?fileId=N -o N.jpg
       ler a imagem    -> ferramenta Read sobre N.jpg (recortar/ampliar se preciso)
       extrair achados -> objeto estruturado (ver §5)
   devolver a lista de achados do lote (JSON), nada de prosa

FASE C — COORDENADOR: consolidar
   juntar achados de todos os lotes
   marcar homónimos (mesmo nome, contexto diferente)
   ranquear candidatos ao ALVO por nº de eixos que batem (§6)
   registar com fonte + confiança (`templates/research_log.template.md`); negativos contam
```

---

## 3. Fase A — Coordenador: obter a lista de fileIds e lotear

### 3.1 Localizar e listar

```bash
# Confirmar o livro (cota + datas cobrindo o ano-alvo) e que tem imagens
curl -s 'https://digitarq.arquivos.pt/api/docs/details/{GUID}' | jq '{referenceCode, dateInitial, dateFinal}'

# Listar TODAS as imagens -> results[].id é o fileId que se baixa
curl -s 'https://digitarq.arquivos.pt/rdigital/{GUID}?from=0&max=500' \
  | jq -c '.results[] | {id, name}'
```

O campo `id` de cada item é o `fileId` numérico passado a `dissemination?fileId=N`.
O `name` costuma conter número de fólio ou ordem de captura — guarde-o, ajuda no §7.

### 3.2 Recortar o intervalo antes de lotear

Se há **âncora de ano** (ex.: casamento ~ANO), não varra o livro inteiro. Os livros
costumam ser cronológicos: use as miniaturas (`thumb?fileId=N`) ou uma amostra de fólios
para localizar onde começa o ano-alvo e restrinja a varredura a esse bloco (± folga).

```bash
# miniatura rápida para sondar onde está o ano, sem baixar tudo em hi-res
curl -s 'https://digitarq.arquivos.pt/rdigital/thumb?fileId=N' -o thumb-N.jpg
```

### 3.3 Lotear (~10-13 imagens por lote)

Por que ~10-13: é o que um subagente lê com atenção numa passagem sem degradar a
qualidade nem estourar contexto. Lotes maiores → leituras apressadas e mais erros;
lotes minúsculos → overhead de coordenação. Ajuste para baixo (8-10) se as imagens forem
densas (duas colunas, letra apertada) ou se cada Read trouxer recortes múltiplos.

```
fileIds = [101, 102, ..., 137]            # do passo 3.1, já recortados ao intervalo (3.2)
lotes   = chunk(fileIds, 12)              # ~10-13 por lote
# -> lote 0: [101..112], lote 1: [113..124], lote 2: [125..137]
```

Despache **um subagente por lote**, em paralelo. Dê a cada um exatamente: a sua lista de
fileIds, o `{GUID}` e a cota (para a citação), o **alvo** (nome + naturalidade + datas +
cônjuge que se procura), e o **contrato de saída** (§5).

---

## 4. Fase B — Subagente: baixar, ler, devolver

Cada subagente faz, para cada `fileId` do seu lote:

```bash
# 1) baixar a página em alta resolução
curl -s 'https://digitarq.arquivos.pt/rdigital/dissemination?fileId=N' -o N.jpg
```

```
# 2) LER com a ferramenta Read aplicada ao ficheiro N.jpg
#    (se a tinta estiver fraca ou a letra apertada, recortar/ampliar antes —
#     ver scripts/image_tools.py e 03-paleografia.md: autocontrast, threshold)
# 3) EXTRAIR cada assento legível para um objeto estruturado (§5)
```

Regras do subagente (inegociáveis):
- **Lê a imagem, não adivinha.** Marca `[?]` em qualquer palavra/nome/data incerta;
  incerteza lida ≠ facto.
- **Não decide** se o achado é "a pessoa certa" de forma definitiva — apenas reporta os
  campos e o seu juízo (`isAlvo`, `isHomonimo`, `confianca`). A decisão final é do
  coordenador (§6), com todos os lotes à vista.
- **Devolve JSON, não prosa.** Uma lista de achados por imagem. Nada de narrativa.
- **Conta o que viu**: total de imagens recebidas, quantas legíveis, quantas em branco/
  ilegíveis, quais falharam o download. Isto alimenta o controlo de cobertura (§7).

---

## 5. Contrato de saída (achado estruturado)

Cada subagente devolve uma lista destes objetos. Um objeto por **assento legível**
(uma página pode ter vários; uma página em branco gera um registo de cobertura sem
pessoas).

```json
{
  "fileId": 117,
  "folio": "23v [?]",
  "anoCabecalho": 1718,
  "tipoAssento": "casamento",        // batismo | casamento | obito | outro | ilegivel
  "transcricao": "Aos ... dias ... se receberam TERMO, f.o de ..., e TERMO, f.a de ... [?]",
  "pessoas": [
    {
      "nome": "TERMO",
      "papel": "noivo",              // noivo|noiva|baptizando|falecido|pai|mae|padrinho|testemunha
      "pais": ["TERMO (pai)", "TERMO (mae) [?]"],
      "avos": [],                    // preencher só se o assento os nomear (raro)
      "naturalidade": "Lugar-X [?]",
      "data": "1718-05-?? [?]"
    }
  ],
  "isAlvo": "candidato",             // sim | candidato | nao   (juízo do subagente)
  "isHomonimo": "possivel",          // sim | possivel | nao    (mesmo nome, contexto a confirmar)
  "confianca": "media",              // alta | media | baixa
  "notas": "tinta passada da página de trás; sobrenome da mãe ilegível"
}
```

Registo de cobertura (página sem assento útil), para o subagente não “sumir” com imagens:

```json
{ "fileId": 118, "folio": "?", "tipoAssento": "ilegivel", "pessoas": [],
  "isAlvo": "nao", "confianca": "baixa", "notas": "página em branco / guarda" }
```

Campos e o seu porquê:
- `folio` / `anoCabecalho` — o fólio manuscrito (canto) e o ano lido no **cabeçalho** do
  assento. Servem para detetar fólios fora de ordem e confirmar que se está no ano certo (§7).
- `tipoAssento` — casamento nomeia pais de ambos (sobe geração nos dois lados); batismo
  dá pais + data; óbito dá idade/cônjuge (ver `04-tipos-de-registo.md`).
- `transcricao` — o trecho que **prova** a ligação, literal, com `[?]` no incerto.
  Sem transcrição não há achado.
- `isAlvo` / `isHomonimo` / `confianca` — juízos, não veredictos. O coordenador reconcilia.

---

## 6. Fase C — Coordenador: consolidar e marcar homónimos

Junte as listas de todos os lotes e processe:

1. **Agrupar por pessoa-candidata.** Mesmo nome aparecendo em vários assentos pode ser:
   a mesma pessoa (batismo + casamento + óbito), parentes homónimos, ou ruído. Não
   funda registos só porque o nome bate.

2. **Marcar homónimos.** Aplique a disciplina de `00-metodologia.md` §6: dois assentos
   só são da **mesma** pessoa se coincidirem em **vários eixos independentes** — não basta
   o nome. Eixos: naturalidade (freguesia, não só país), filiação, datas compatíveis,
   cônjuge (âncora fortíssima), padrinhos/testemunhas recorrentes.

3. **Ranquear candidatos ao ALVO** por número de eixos que batem com o muro definido
   (§2 da metodologia). Um candidato cujo nome **e** naturalidade **e** cônjuge batem
   vence um que só bate no nome. Em empate real, mantenha **hipóteses concorrentes** —
   não escolha o conveniente.

4. **Atribuir confiança final** e **registar** cada achado aceite com fonte completa
   (`templates/research_log.template.md`): cota + `{GUID}` + `fileId` + fólio + transcrição. A confiança
   da cadeia herda o **elo mais fraco**.

5. **Registar o negativo.** Se o alvo não apareceu: anote o intervalo de fólios varrido,
   os anos cobertos pelos cabeçalhos, quantas imagens ficaram ilegíveis, e a próxima fonte
   a tentar. Negativo documentado é progresso (evita revarrer o mesmo).

---

## 7. Dicas que evitam erros caros

- **Fólios fora de ordem.** Livros foram encadernados/digitalizados com folhas trocadas,
  intercaladas ou repetidas. **Não** confie no índice da lista de imagens como ordem
  cronológica garantida. Confirme sempre pelo **fólio manuscrito** no canto e pelo
  **ano no cabeçalho** do assento (`folio` + `anoCabecalho`).
- **Confirme os anos pelos cabeçalhos, não pela posição.** Cada novo ano costuma abrir
  com um cabeçalho ("Ano de 17..."). Use-o para validar que o lote cobre o ano-alvo; se
  os cabeçalhos saltam o ano, alargue o intervalo e despache mais um lote.
- **Conte as imagens legíveis.** Total recebido ≠ total legível. Páginas em branco,
  guardas, capas, fólios com tinta apagada ou rasgões contam para a cobertura mas não
  têm assento. Registe-as (§5) para a contagem de cobertura fechar.
- **Capa, guardas e termo de abertura no início** (não numerados) deslocam o offset
  fólio↔imagem; o índice onomástico costuma estar **no fim**. Olhe as extremidades antes
  de varrer o miolo.
- **Nunca tratar leitura incerta como certa.** Um `[?]` no contrato de saída tem de
  sobreviver até ao relatório. Se o sobrenome da mãe ficou ilegível, ele fica ilegível —
  não se “completa” por palpite nem por homónimo conveniente.
- **Marque homónimos cedo.** É mais barato anotar "possível homónimo" no lote do que
  descobrir mais tarde que se subiu uma geração na pessoa errada.
- **Lotes densos → encolher.** Páginas a duas colunas ou com letra muito apertada
  merecem lotes de 8-10, não 13.
- **Idempotência.** Nomeie os ficheiros pelo `fileId` (`N.jpg`); reexecutar um lote
  reusa downloads e não duplica trabalho.

---

## 8. Template de orquestração

O esqueleto de orquestração (lotear fileIds, despachar um subagente por lote, recolher e
consolidar JSON) está em:

```
templates/scan_workflow.example.js
```

É um **exemplo** com placeholders (`{GUID}`, `fileId`, `TERMO`) e funções marcadas como
TODO onde se liga ao harness de subagentes em uso (Claude Code / Codex / outro). Adapte
o despacho e a leitura de imagem ao seu ambiente; o padrão (lotear → ler em paralelo →
consolidar → marcar homónimos) é o que importa.

---

## 9. Referência rápida

| Quero... | Faço... |
|---|---|
| Listar imagens de um livro | `GET /rdigital/{GUID}?from=0&max=500` → `results[].id` = fileId |
| Restringir a varredura ao ano-alvo | sondar com `thumb?fileId=N`, recortar o intervalo de fólios |
| Dividir o trabalho | lotes de ~10-13 fileIds (8-10 se denso), 1 subagente por lote |
| Baixar uma página (subagente) | `GET /rdigital/dissemination?fileId=N -o N.jpg` → ferramenta Read |
| Receber do subagente | lista JSON de achados (§5), 1 por assento legível, `[?]` no incerto |
| Detetar fólio fora de ordem | comparar `folio` manuscrito + `anoCabecalho` com a posição |
| Aceitar mesma pessoa | vários eixos batem (naturalidade+filiação+datas+cônjuge), não só nome |
| Fechar um negativo | registar fólios varridos + anos cobertos + ilegíveis + próxima fonte |
| Esqueleto de código | `templates/scan_workflow.example.js` |
