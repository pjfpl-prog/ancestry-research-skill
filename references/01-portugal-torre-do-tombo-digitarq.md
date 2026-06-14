# Portugal — Arquivo Nacional Torre do Tombo (ANTT) via API REST do DigitArq

Referência prática para pesquisa genealógica no **Arquivo Nacional Torre do Tombo (ANTT)**
através da API REST do sistema **DigitArq** (`digitarq.arquivos.pt`).

> **Sem login.** Todos os endpoints abaixo são públicos e respondem JSON ou imagem
> diretamente. Não há API key, cookie ou token necessário para consulta e download.

O DigitArq é o catálogo arquivístico do ANTT. Cobre, entre muito mais:
- **Registos paroquiais** (baptismos, casamentos, óbitos, mistos) digitalizados.
- **Inquisição** (Lisboa, Évora, Coimbra) — processos e habilitações.
- **Habilitações** de Ordens Militares e do Santo Ofício (genealogias de limpeza de sangue).
- Fundos notariais, da Chancelaria, etc.

---

## 1. Endpoints da API

Todos partem do host `https://digitarq.arquivos.pt`.

| Função | Método / URL | Resposta |
|---|---|---|
| Busca | `GET /api/docs/search?query=TERMO&objType=DOCUMENT` | JSON: `total` + `results[]` |
| Detalhe de um documento | `GET /api/docs/details/{GUID}` | JSON: descrição arquivística completa |
| Lista de imagens de um doc | `GET /rdigital/{GUID}?from=0&max=500` | JSON: `results[]` de imagens |
| Imagem em alta resolução | `GET /rdigital/dissemination?fileId=N` | JPEG (binário) |
| Miniatura (thumbnail) | `GET /rdigital/thumb?fileId=N` | JPEG pequeno (binário) |

Notação usada neste documento:
- `{GUID}` = identificador do documento (string longa estilo UUID, ex. `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`).
- `N` / `{fileId}` = identificador numérico de uma imagem individual.
- `TERMO` = texto de busca (URL-encoded).

---

## 2. Busca — `/api/docs/search`

```
GET https://digitarq.arquivos.pt/api/docs/search?query=TERMO&objType=DOCUMENT
```

Parâmetros úteis:
- `query` — texto livre. Pode ser um nome, um lugar, ou (melhor — ver §6) um **reference code**.
- `objType=DOCUMENT` — restringe a documentos (em vez de fundos/séries de nível superior).

Formato da resposta (campos principais):

```json
{
  "total": 123,
  "results": [
    {
      "id": "{GUID}",
      "titles": ["<título do documento>"],
      "referenceCode": "PT/TT/PRQ/<cod-paroquia>/<serie>/<livro>",
      "dateInitial": "1700-01-01",
      "dateFinal": "1750-12-31",
      "hasImages": true
    }
  ]
}
```

Notas:
- `total` é o número total de resultados (pode exceder os devolvidos numa página).
- `hasImages: true` indica que existem digitalizações — só esses valem para varredura página-a-página.
- `referenceCode` é a cota arquivística; é a chave para localizar o livro físico/digital (§4).
- `titles` é um array (pode ter mais de um título/forma).

Exemplo curl (URL-encode o termo; espaço = `%20`):

```bash
curl -s 'https://digitarq.arquivos.pt/api/docs/search?query=TERMO&objType=DOCUMENT'
```

Buscar por cota (recomendado — ver §6):

```bash
curl -s 'https://digitarq.arquivos.pt/api/docs/search?query=PT%2FTT%2FPRQ%2F<cod-paroquia>&objType=DOCUMENT'
```

> Dica de extração com `jq`:
> ```bash
> curl -s 'https://digitarq.arquivos.pt/api/docs/search?query=TERMO&objType=DOCUMENT' \
>   | jq '.total, (.results[] | {id, referenceCode, dateInitial, dateFinal, hasImages})'
> ```

---

## 3. Detalhe do documento — `/api/docs/details/{GUID}`

```
GET https://digitarq.arquivos.pt/api/docs/details/{GUID}
```

Devolve a descrição arquivística completa do documento identificado por `{GUID}`:
datas, dimensão, âmbito/conteúdo, cota (`referenceCode`), e — para muitos fundos —
campos de **filiação** e contexto que ajudam a confirmar identidade antes de baixar imagens.

Para a **Inquisição**, a ficha costuma trazer o campo **"Estatuto social"**
(ex.: cristão-novo / parte de... / meio... / da nação), que é exatamente onde se
sinaliza a ascendência relevante para genealogia de limpeza de sangue.
A ascendência detalhada (pais, avós, bisavós, com indicação de quem foi penitenciado)
aparece na própria sessão de genealogia (in genere) do processo, não na ficha de catálogo.

```bash
curl -s 'https://digitarq.arquivos.pt/api/docs/details/{GUID}' | jq .
```

---

## 4. Reference codes de paróquias — anatomia da cota

Os registos paroquiais seguem o padrão:

```
PT / TT / PRQ / <cod-paroquia> / <serie> / <livro>
```

- `PT` — país (Portugal).
- `TT` — arquivo (Torre do Tombo).
- `PRQ` — fundo de registos **paroquiais**.
- `<cod-paroquia>` — código da paróquia (ex. concelho + freguesia codificados).
- `<serie>` — tipo de assento (ver tabela abaixo).
- `<livro>` — número sequencial do livro dentro da série.

### Códigos de série (o que cada série contém)

| Série | Tipo de assento | O que nomeia (lógica genealógica) |
|---|---|---|
| `001` | **Baptismos** | pais (às vezes avós/padrinhos), data; por vezes naturalidade do pai |
| `002` | **Casamentos** | **pais do noivo E da noiva** + naturalidades — o melhor para subir uma geração |
| `003` | **Óbitos** | filiação, estado civil, cônjuge, idade |
| `004` | **Mistos** | os três tipos acima num só livro (paróquias pequenas) |

> Estratégia: para **subir uma geração**, priorize a série `002` (casamento), porque
> nomeia os pais de ambos os cônjuges e as naturalidades. O baptismo (`001`) confirma a
> geração seguinte; o óbito (`003`) fecha idade/cônjuge. Em paróquias pequenas, tudo cai
> no livro misto (`004`).

Exemplo de cota completa (placeholder):

```
PT/TT/PRQ/<cod-paroquia>/002/<livro>
```

---

## 5. Lista de imagens e mapeamento fólio → imagem

### 5.1. Listar as imagens de um documento

```
GET https://digitarq.arquivos.pt/rdigital/{GUID}?from=0&max=500
```

- `from` — índice inicial (paginação; comece em `0`).
- `max` — quantas imagens devolver (use um valor alto, ex. `500`, para apanhar o livro inteiro).

Resposta (campos principais):

```json
{
  "results": [
    { "id": N, "name": "<nome/rótulo da imagem>" }
  ]
}
```

- `id` = `fileId` numérico — é o que se passa a `dissemination?fileId=N` para baixar.
- `name` = rótulo da imagem (frequentemente contém número de página/fólio ou ordem de captura).

```bash
curl -s 'https://digitarq.arquivos.pt/rdigital/{GUID}?from=0&max=500' \
  | jq '.results[] | {id, name}'
```

### 5.2. Baixar a imagem

Alta resolução (para leitura paleográfica):

```bash
curl -s 'https://digitarq.arquivos.pt/rdigital/dissemination?fileId=N' -o pagina-N.jpg
```

Miniatura (para varrer rápido qual imagem abrir):

```bash
curl -s 'https://digitarq.arquivos.pt/rdigital/thumb?fileId=N' -o thumb-N.jpg
```

### 5.3. Mapear o número de fólio para a imagem

Os assentos não têm número de página da web — têm o **fólio** escrito no canto do
documento original. Para chegar à imagem certa:

1. Liste as imagens (`/rdigital/{GUID}?from=0&max=500`) e guarde a **ordem** dos `id` (fileId).
2. O índice na lista ≈ ordem de captura. Em geral, **imagem(n) ≈ fólio inicial + n**, mas
   o offset varia: as primeiras capturas costumam ser **capa, guardas e termo de abertura**
   (não numerados), por isso o fólio 1 não é a 1ª imagem.
3. Confirme abrindo uma imagem e lendo o número de fólio manuscrito no **canto superior**
   (frente = recto; verso não numerado). Calcule o offset e salte direto.
4. Muitos livros têm **índice onomástico** no fim (ou início) — abra primeiro as últimas
   imagens; se houver índice, ele dá o fólio do nome e você converte fólio → imagem.

> Quando o livro **não é indexado por nome**, a varredura é página-a-página. Divida as
> imagens em lotes de ~10-13 entre subagentes; cada um baixa em alta-res, lê e devolve
> achados (nome, data, filiação, fólio, fileId), marcando homónimos e nível de confiança.

---

## 6. Dica-chave: buscar por reference code acha livros melhor que por nome

A busca textual por **nome de pessoa** raramente funciona bem no DigitArq, porque os
assentos paroquiais **não estão indexados ao nível do indivíduo** — o catálogo descreve o
*livro*, não cada batizado. Procurar "TERMO" (um nome) tende a devolver pouco ou ruído.

O caminho fiável:

1. Descubra/confirme o **código da paróquia** e busque pela **cota** (reference code), não pelo nome:
   ```bash
   curl -s 'https://digitarq.arquivos.pt/api/docs/search?query=PT%2FTT%2FPRQ%2F<cod-paroquia>&objType=DOCUMENT'
   ```
2. Filtre por **série** (`002` casamento, `001` baptismo, `003` óbito, `004` mistos) e por
   **intervalo de datas** (`dateInitial`/`dateFinal`) para achar o livro que cobre o ano-alvo.
3. Confirme `hasImages: true`, pegue o `{GUID}`, liste as imagens e leia.

Ou seja: **encontre o LIVRO pela cota e pela data**, depois leia as imagens — em vez de
esperar que o motor encontre a PESSOA. É mais rápido, mais completo e evita falsos negativos.

---

## 7. Fluxo completo de exemplo (com placeholders)

```bash
# 1) Achar o livro da série de casamentos de uma paróquia
curl -s 'https://digitarq.arquivos.pt/api/docs/search?query=PT%2FTT%2FPRQ%2F<cod-paroquia>%2F002&objType=DOCUMENT' \
  | jq '.total, (.results[] | {id, referenceCode, dateInitial, dateFinal, hasImages})'

# 2) Ver a ficha do livro escolhido (confirmar datas/âmbito)
curl -s 'https://digitarq.arquivos.pt/api/docs/details/{GUID}' | jq .

# 3) Listar todas as imagens do livro
curl -s 'https://digitarq.arquivos.pt/rdigital/{GUID}?from=0&max=500' \
  | jq '.results[] | {id, name}'

# 4) Baixar miniaturas para varrer, depois a página-alvo em alta-res
curl -s 'https://digitarq.arquivos.pt/rdigital/thumb?fileId=N'          -o thumb-N.jpg
curl -s 'https://digitarq.arquivos.pt/rdigital/dissemination?fileId=N'  -o pagina-N.jpg
```

---

## 8. Leitura das imagens (paleografia séc. XVI-XVIII)

Depois de baixar em alta resolução:
- **Recorte e amplie** só o trecho do assento (PIL: `autocontrast`, `threshold`/binarização)
  para realçar a tinta desbotada.
- Abreviaturas comuns: `P.e` (Padre), `B.el` (Bacharel), `m.er` (mulher), `f.o`/`f.a`
  (filho/filha), `R.do` (Reverendo), `N.S.a` (Nossa Senhora).
- Nomes devocionais (da Conceição, de Jesus, dos Santos) variam de assento para assento.
- Cuidado com correções e riscos do escrivão; confira o número do fólio no canto.

---

## 9. Disciplina de qualidade

- Distinga **DOCUMENTADO** (com cota/fonte) de **TRADIÇÃO/LENDA**.
- Marque `[?]` em leituras paleográficas incertas.
- **Nunca** invente nome, data ou cota; **nunca** apresente homónimo como prova.
- Registe sempre a fonte completa: `referenceCode` (cota) + `{GUID}` + `fileId` + fólio.
- A verificação final é sempre do utilizador.

---

## 10. Referência rápida

| Quero... | Faço... |
|---|---|
| Encontrar livros de uma paróquia | `search?query=PT%2FTT%2FPRQ%2F<cod>` + filtrar série/data |
| Subir uma geração | série `002` (casamento) — nomeia pais de ambos os cônjuges |
| Confirmar a geração seguinte | série `001` (baptismo) |
| Fechar idade/cônjuge | série `003` (óbito) |
| Ver detalhes/filiação no catálogo | `details/{GUID}` (Inquisição: campo "Estatuto social") |
| Listar imagens de um livro | `rdigital/{GUID}?from=0&max=500` → `results[].id` = fileId |
| Baixar página em alta-res | `rdigital/dissemination?fileId=N` |
| Ver miniatura | `rdigital/thumb?fileId=N` |
