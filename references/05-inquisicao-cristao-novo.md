# Inquisição e "cristão-novo" para genealogia

Referência prática para usar os fundos da **Inquisição (Santo Ofício)** como fonte
genealógica, e para entender a marca histórico-jurídica **"cristão-novo"**.

> **Aviso ético e historiográfico (ler antes de tudo).**
> "Cristão-novo" **não** é uma fé nem uma identidade escolhida: é uma **condição
> jurídica de sangue imposta** a cristãos descendentes de judeus convertidos
> (sobretudo após a conversão forçada de 1497 em Portugal). Era usada para discriminar,
> vigiar e excluir — e a Inquisição perseguiu, torturou e matou com base nela.
> Encontrar um ancestral classificado como cristão-novo num processo **diz respeito à
> categorização da época, não à religião atual de quem descende dele**. Trate o tema com
> rigor de fonte, sem essencializar ("sangue judeu"), sem romantizar e sem reduzir uma
> pessoa à acusação que pesou sobre ela. O documento é prova de uma *perseguição*, não
> de uma "essência".

Apesar de ser produto de um aparelho de repressão, a documentação inquisitorial é,
ironicamente, **uma das fontes genealógicas mais ricas que existem** para os séculos
XVI–XVIII: os inquéritos de limpeza de sangue obrigavam a reconstruir a ascendência de
um indivíduo por **três a quatro gerações**, com nomes, naturalidades e relações. Onde
os livros paroquiais falham (anteriores ou perdidos), um processo ou habilitação pode
salvar uma linha inteira.

---

## 1. Onde estão os fundos (Torre do Tombo)

Os tribunais do Santo Ofício português depositam no **Arquivo Nacional Torre do Tombo
(ANTT)**, consultável pela API pública do **DigitArq** (ver
`01-portugal-torre-do-tombo-digitarq.md` — sem login). Os três tribunais metropolitanos:

| Tribunal | Sigla de série típica |
|---|---|
| Inquisição de **Lisboa** | `TSO/IL` |
| Inquisição de **Évora** | `TSO/IE` |
| Inquisição de **Coimbra** | `TSO/IC` |

`TSO` = **Tribunal do Santo Ofício** (o fundo de topo). Dentro de cada tribunal, os
dois tipos de documento mais úteis para genealogia são:

- **Processos** (`.../Processo/{nº}`) — o auto completo contra um réu: denúncia,
  genealogia, confissões, sentença. É aqui que aparece o detalhe mais rico.
- **Habilitações** — *incidentais* (do próprio Santo Ofício, para quem queria servir
  como **familiar** ou ministro) e as **habilitações de Ordens Militares**. São
  inquéritos de **limpeza de sangue**: provam-se 3–4 gerações de ascendência "limpa"
  (sem cristãos-novos, mouros, mulatos ou penitenciados). Ver a lógica destas habilitações
  também em `00-metodologia.md`.

> Atenção: uma **habilitação aprovada** prova que a banca *não encontrou* mácula — não
> que ela não existisse. Uma habilitação **recusada/embargada** é, em si, um indício forte.

### Como localizar pela API

A busca do DigitArq aceita texto livre **e** reference codes:

```
GET https://digitarq.arquivos.pt/api/docs/search?query=TERMO&objType=DOCUMENT
```

Estratégias de busca (`TERMO`, URL-encoded):

- por **nome** do réu/habilitando (ex.: `query=NOME%20SOBRENOME`);
- por **série**, para varrer um tribunal (ex.: `query=TSO%2FIC` para Coimbra);
- por **lugar de origem** (a Inquisição registava a naturalidade — ver §3).

Depois, o **detalhe** traz a descrição arquivística, com filiação e — crucial — o
campo de **estatuto social** (§2):

```
GET https://digitarq.arquivos.pt/api/docs/details/{GUID}
```

A cota (reference code) de um processo tem a forma aproximada
`PT/TT/TSO/IC/.../Proc.{nº}` — guarde-a sempre como **fonte citável**.

---

## 2. Onde aparece a marca "cristão-novo"

A classificação não está num "campo religião" — aparece em **vários lugares** e com
**vocabulário de época** que é preciso reconhecer:

### a) Na capa do maço / do processo (paleografia)

Os escrivães anotavam a condição na **capa** do maço, muitas vezes **abreviada**:

- **"Xão novo"** = *christão novo* (o `X` é o grego *chi*, abreviatura de *Chr-*; o mesmo
  `X` aparece em "Xpo" = Cristo, "Xão" = christão).
- **"chr.ão novo"**, **"x.novo"**, **"c.n."** — variantes abreviadas.
- Por oposição, **"Xão velho"** / **"christão velho"** = sem ascendência judaica conhecida.

Como são marcas manuscritas na capa, é frequente precisar **baixar a imagem em alta
resolução e ampliar/recortar** o canto — ver técnicas em `03-paleografia.md` (autocontrast,
threshold, recorte). Cuidado com riscos e correções do escrivão.

### b) Na ficha do arquivo — campo "Estatuto social"

A descrição arquivística (no detalhe do DigitArq) costuma normalizar a condição num
campo **"Estatuto social"**, com formulações como:

- `Estatuto social: cristão-novo`
- `Estatuto social: cristão-novo, parte de cristão-novo`
- `Estatuto social: meio cristão-novo` / `um quarto de cristão-novo`
- `Estatuto social: da nação`

### c) Os **graus** ("parte / meio / um quarto")

A burocracia quantificava a ascendência judaica por **fração de sangue** — uma lógica
genealógica explícita, útil (e perturbadora) para reconstruir a árvore:

| Expressão de época | Leitura genealógica |
|---|---|
| **cristão-novo "inteiro"** | ascendência judaica em ambas as linhas |
| **meio cristão-novo** | um dos pais cristão-novo, o outro cristão-velho |
| **um quarto / "parte de"** | a mácula vinha de um(a) avô/avó |
| **"de tantas partes"** | quantificação ainda mais fina (oitavos), por bisavô |

Ou seja: o **grau** é, na prática, uma **pista de em que geração** procurar o ancestral
convertido. "Meio" aponta para os pais; "um quarto" para os avós; frações menores para
bisavós.

### d) O eufemismo **"da nação"**

**"da nação"** (= *gente da nação [hebreia]*, "homens de negócio da nação") é o termo
**eufemístico** mais comum nos documentos para "cristão-novo", sobretudo em contextos
comerciais e fora de Portugal. Reconhecê-lo é essencial: muitas vezes a condição **não**
está escrita como "cristão-novo", mas como "**da nação**".

---

## 3. A "sessão de genealogia" / *in genere* — o ouro genealógico

Dentro de um processo (e de toda habilitação) há uma fase chamada **genealogia** —
também referida como inquirição **"*in genere*"** (geral, sobre as origens, antes do
**"*in specie*"**, sobre os factos concretos). É **a peça mais valiosa** para a árvore.

Nessa sessão o réu/habilitando (ou as testemunhas) declarava, ordenadamente:

1. **Próprio** — nome, idade, profissão, naturalidade, morada.
2. **Pais** — nome do pai e da mãe, naturalidade de cada um, profissão.
3. **Avós** — paternos e maternos, com nome e naturalidade.
4. **Bisavós** — frequentemente nomeados (sobretudo nas habilitações de limpeza de sangue).
5. Por vezes **tios, irmãos e cônjuge**, com filiação.

E, para o tema cristão-novo, o ponto decisivo: **de cada ascendente costuma dizer-se se
foi "penitenciado" pelo Santo Ofício** (preso, processado, relaxado/queimado, reconciliado).
Isso permite **encadear processos** — o nome de um avô "penitenciado em Évora" é a deixa
para ir buscar *o processo desse avô*, recuando outra geração.

> **Por que isto bate qualquer paróquia:** uma única sessão de genealogia pode entregar
> 3–4 gerações **com naturalidades**, o que normalmente exigiria dezenas de assentos
> espalhados por várias paróquias — e muitas vezes cobre períodos em que os livros já não
> existem.

**Cautelas de leitura** (ver disciplina de qualidade em `00-metodologia.md`):

- Declarações podiam ser **interessadas**: réus omitiam ascendentes "manchados"; habilitandos
  escondiam cristãos-novos. Confronte com testemunhos de terceiros dentro do mesmo processo.
- **Homónimos** são frequentes (devocionais repetidos — "Maria de Jesus", "António dos
  Santos"). Marque `[?]` e desambigue por naturalidade + idade + nome do cônjuge.
- A naturalidade declarada pode ser onde **vivia**, não onde **nasceu**; trate como pista
  a confirmar no registo paroquial.

---

## 4. A questão do "nome judeu"

Pergunta comum — e a resposta correta evita um erro grave:

> **Em regra NÃO existe um "nome judeu" registado nos documentos portugueses.**

Razões:

- Após a conversão forçada (1497), os convertidos e seus descendentes usavam **nomes
  cristãos** (devocionais e de santos), iguais aos da população cristã-velha. **Não há,
  no assento, um nome hebraico a "denunciar" a origem.** Procurar sobrenomes supostamente
  "judaicos" é metodologicamente falho e produz falsos positivos.
- A condição de cristão-novo provava-se por **ascendência e por testemunho** (§2–§3),
  não pelo nome.

**As duas exceções** em que aparece um nome hebraico:

1. **Confissão / processo** — quando o réu confessava práticas "judaizantes", o auto podia
   registar nomes ou ritos hebraicos *atribuídos*. É testemunho sob coação inquisitorial:
   trate como documento da *perseguição*, com todas as reservas.
2. **Fuga para o estrangeiro** — quem fugia para comunidades judaicas toleradas (Amesterdão,
   Hamburgo, Veneza, Livorno, Salónica, Londres, Bordéus) frequentemente **retornava ao
   judaísmo abertamente**, circuncidava-se e **adotava um nome hebraico**. Aí o nome aparece
   — mas em fontes **da diáspora** (registos de *kahal*/comunidade, *ketubot*, lápides),
   não nos assentos portugueses. Cruzar o nome cristão (Portugal) com o nome hebraico
   (diáspora) é uma técnica avançada de ligação de fontes, sempre com nível de confiança explícito.

---

## 5. Exemplo de fluxo (ilustrativo, com placeholders)

> Ilustração **neutra** — substitua `{GUID}`, `{nº}`, `TERMO` pelos valores reais. Não
> presuma a condição de ninguém; deixe o documento falar.

1. **Buscar** o réu/habilitando por nome no tribunal provável:
   ```
   GET https://digitarq.arquivos.pt/api/docs/search?query=TERMO&objType=DOCUMENT
   ```
2. **Abrir o detalhe** do resultado e ler o campo **"Estatuto social"** e a filiação:
   ```
   GET https://digitarq.arquivos.pt/api/docs/details/{GUID}
   ```
   → anote o **grau** ("meio", "um quarto" — §2c) para saber em que geração procurar.
3. **Listar as imagens** do processo e baixar a(s) da **capa** (marca "Xão novo") e da
   **sessão de genealogia**:
   ```
   GET https://digitarq.arquivos.pt/rdigital/{GUID}?from=0&max=500
   GET https://digitarq.arquivos.pt/rdigital/dissemination?fileId=N
   ```
4. **Ler em paleografia** (ampliar/recortar — `03-paleografia.md`) pais → avós → bisavós,
   anotando quem foi **"penitenciado"**.
5. **Encadear**: para cada ascendente penitenciado, voltar ao passo 1 buscando **o
   processo dele**, recuando mais uma geração.
6. **Registar a cota** completa (ex.: `PT/TT/TSO/IC/.../Proc.{nº}`) como fonte de cada facto.

Como **exemplo público** de que estes autos existem e estão acessíveis: o processo de
**Frei Diogo da Assunção** (relaxado pela Inquisição de Lisboa em 1603) e os autos
relativos a **António José da Silva, "o Judeu"** (dramaturgo, relaxado em 1739) são casos
historicamente documentados e citados na bibliografia — úteis para *ver o formato* de um
processo. Use-os apenas como **modelo de estrutura**; nunca para inferir parentesco com
quem quer que seja.

---

## 6. Lista de verificação

- [ ] Identifiquei o **tribunal** provável (IL / IE / IC) pela região do ancestral.
- [ ] Busquei por **nome** *e* por **série/lugar** (não confiei só no nome).
- [ ] Li o campo **"Estatuto social"** e anotei o **grau** (parte/meio/quarto).
- [ ] Reconheci eufemismos: **"da nação"**, **"Xão novo"** na capa.
- [ ] Extraí a **sessão de genealogia** (pais → avós → bisavós + quem foi penitenciado).
- [ ] **Encadeei** processos pelos ascendentes penitenciados.
- [ ] Marquei **homónimos** e leituras incertas com `[?]`; separei **DOCUMENTADO** de
      **tradição/lenda**.
- [ ] Guardei a **cota** de cada documento como fonte.
- [ ] **Não** essencializei: tratei "cristão-novo" como categoria jurídica da época, não
      como identidade ou fé atual de quem descende.
