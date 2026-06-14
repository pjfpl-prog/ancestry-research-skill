---
name: ancestry-research
description: Quebrar muros genealogicos com fontes primarias - Torre do Tombo (DigitArq), FamilySearch, registos paroquiais/notariais/Inquisicao, paleografia e varredura multi-agente. Use quando o usuario quer pesquisar/expandir uma arvore genealogica, achar registos de um antepassado, ou subir uma geracao alem de um "muro".
---

# Ancestry Research — quebrar muros com fontes primarias

Esta skill orienta a pesquisa genealogica seria: partir de um antepassado conhecido e
**subir uma geracao** atras de outra usando documentos primarios (assentos paroquiais,
processos da Inquisicao, habilitacoes, notariais), nao palpites. O produto e sempre um
fato **com fonte e nivel de confianca**, nunca uma narrativa inflada.

## 1. Quando usar

Use esta skill quando o usuario quiser:

- **Expandir uma arvore** — adicionar pais, avos, bisavos de uma pessoa ja conhecida.
- **Quebrar um "muro"** — um antepassado em que a linhagem trava (nao se sabe os pais,
  ou a naturalidade, ou se perdeu a pista num arquivo).
- **Achar o registo de um antepassado** — batismo, casamento, obito, testamento, processo.
- **Investigar uma origem especifica** — nobreza, cristao-novo/ascendencia judaica (via
  Inquisicao), imigracao, presenca no Brasil colonial (AHU/Projeto Resgate).
- **Verificar/derrubar uma tradicao de familia** — separar o documentado da lenda.

Nao use para arvores ja completas que so precisam de formatacao, nem para "achismos"
sem ancestral concreto de partida.

## 2. Fluxo de trabalho passo-a-passo

Genealogia e iterativa: cada documento novo abre o proximo. Repita este ciclo por geracao.

### Passo 1 — Definir o ALVO e a PAREDE

Escreva explicitamente, antes de pesquisar:

- **Alvo**: a pessoa cuja geracao acima queremos descobrir (nome + variantes ortograficas).
- **Ancoras conhecidas**: datas (nascimento/casamento/obito, mesmo aproximadas), lugares
  (paroquia, concelho, comarca, pais), conjuge, filhos, profissao/estatuto.
- **A parede**: o que falta exatamente (ex.: "nao sei os pais de TERMO" ou "nao sei de
  que paroquia ele veio antes de casar em X").

Sem alvo e parede definidos, a busca vira ruido. Confirme estes dados com o usuario se
estiverem vagos.

### Passo 2 — Identificar o ARQUIVO / PAROQUIA certo

Escolha a fonte pela geografia e epoca do alvo:

- **Portugal continental, paroquial/Inquisicao/notarial** -> DigitArq (Torre do Tombo),
  sem login. Reference codes de paroquia: `PT/TT/PRQ/<cod-paroquia>/<serie>/<livro>`
  (serie `001`=baptismos, `002`=casamentos, `003`=obitos, `004`=mistos).
- **Portugal regional** -> Arquivos Distritais (AD..), muitos no FamilySearch.
- **Brasil (paroquial e registo civil)** -> FamilySearch (login do proprio usuario).
- **Brasil colonial / administracao ultramarina** -> AHU / Projeto Resgate.
- **Imprensa (obituarios, anuncios, naturalizacoes)** -> hemerotecas: `memoria.bn.br`
  (Brasil) e `hemerotecadigital.bnportugal.gov.pt` (Portugal).

Veja `references/01-portugal-torre-do-tombo-digitarq.md`, `references/02-familysearch.md`
e `references/08-outros-arquivos.md` para os endpoints exatos de cada fonte.

### Passo 3 — Achar o registo que NOMEIA a geracao acima (priorize CASAMENTO)

Nem todo assento sobe uma geracao igual. Ordem de preferencia:

1. **CASAMENTO** — o melhor: nomeia os **pais do noivo E da noiva** + **naturalidades** de
   ambos. Um so assento de casamento sobe dois ramos de uma vez e revela de onde cada
   conjuge veio (essencial para perseguir o ramo em outra paroquia).
2. **HABILITACOES** (Ordem militar / Familiar do Santo Oficio) — inqueritos de *limpeza de
   sangue* com genealogia pronta de 3-4 geracoes. Achado de ouro quando existe.
3. **BATISMO** — nomeia pais (as vezes avos e padrinhos), data; por vezes a naturalidade
   do pai.
4. **OBITO** — filiacao, estado civil, conjuge, idade (permite estimar nascimento).
5. **NOTARIAIS** (testamentos, justificacoes, sesmarias) — filiacao e bens; uteis quando
   o paroquial falhou ou queimou.

Para a busca propriamente dita:

- DigitArq: `python scripts/digitarq.py search "TERMO"` (busca) -> `python scripts/digitarq.py details {GUID}`
  (le a ficha com a filiacao). Para Inquisicao, a ficha traz o campo **"Estatuto social"**.
- FamilySearch: registos indexados por nome/conjuge/lugar; texto completo (OCR/IA) por
  frase exata. Veja `references/02-familysearch.md`.
- **Se o livro NAO for indexado por nome** -> varredura pagina-a-pagina multi-agente
  (Passo 3b).

### Passo 3b — Varredura multi-agente (livro nao indexado)

Quando so existe a imagem do livro (sem indice de nomes):

1. `python scripts/digitarq.py images {GUID}` lista as imagens (`fileId` + `name`).
2. Divida as imagens em **lotes de ~10-13** entre subagentes.
3. Cada subagente baixa em alta resolucao (`python scripts/digitarq.py download {fileId}`), recorta/amplia e LE.
4. Cada um devolve os achados com **folio/fileId, transcricao, e nivel de confianca**.
5. Marque **homonimos** sempre que houver duvida. Veja `references/06-varredura-multiagente.md`
   e o template `templates/scan_workflow.example.js`.

### Passo 4 — Ler / transcrever (paleografia)

Os assentos antigos (sec. XVI-XVIII) exigem leitura paleografica:

- Baixe a imagem em **alta resolucao**, depois recorte e amplie o trecho relevante.
- Use realce de imagem (autocontrast, threshold, escala de cinza, recorte do folio) — ver
  `scripts/image_tools.py` (subcomandos `enhance`, `crop`, `folio`, `split`).
- Expanda abreviaturas: `P.e`=Padre, `B.el`=Bacharel, `m.er`=mulher, `f.o`/`f.a`=filho/filha,
  `R.do`=Reverendo, `N.S.a`=Nossa Senhora. Tabela completa em `references/03-paleografia.md`.
- Cuidado com nomes devocionais variaveis (da Conceicao, de Jesus, dos Santos), correcoes
  e riscos do escrivao, e o numero do folio no canto.
- Transcreva **literalmente** primeiro; so depois normalize a grafia numa segunda linha.

### Passo 5 — Registar com FONTE e CONFIANCA

Cada fato vai para a arvore com proveniencia completa. Use `templates/research_log.template.md`:

- **Fato**: quem, o que, quando, onde.
- **Fonte**: arquivo + reference code/ARK + GUID/fileId + folio/pagina + link.
- **Confianca**: Alta (documento direto e legivel) / Media (indireto ou parcialmente
  legivel) / Baixa (homonimo possivel, leitura `[?]`, inferencia).
- **Notas**: ambiguidades, homonimos descartados e por que, proximos passos.

### Passo 6 — Iterar

O fato novo (ex.: os pais e a naturalidade revelados no casamento) vira o **alvo do
proximo ciclo**. Volte ao Passo 1 com a nova parede. Pare quando a fonte secar ou a
confianca cair — e registe isso, e tambem um resultado valido.

## 3. Scripts e referencias

Tudo abaixo e generico e reutilizavel. Os scripts usam apenas endpoints publicos
(DigitArq sem login) ou as credenciais do proprio usuario (FamilySearch via env).

### scripts/ (executar com `python scripts/<arquivo>`; antes: `pip install -r scripts/requirements.txt`)

- `digitarq.py` — CLI do DigitArq (Torre do Tombo, sem login). Subcomandos:
  - `search "TERMO"` — busca; imprime total + resultados (`GUID`, titulos, reference code, datas, se tem imagens).
  - `details {GUID}` — ficha detalhada (descricao com filiacao; campo "Estatuto social" na Inquisicao).
  - `images {GUID}` — lista as imagens de um documento (`fileId` + `name`).
  - `download {fileId} [saida.jpg]` — baixa uma imagem em alta resolucao.
- `image_tools.py` — leitura paleografica (PIL). Subcomandos: `download`, `enhance`
  (autocontrast/threshold/zoom), `crop` (caixa relativa + zoom), `folio` (recorta o numero
  do folio no canto), `split` (separa as duas paginas de uma abertura).
- `gedcom_audit.py arvore.ged [--walls] [--json]` — audita um GEDCOM (so-leitura): nos-lixo,
  datas suspeitas (obito lancado como nascimento), mojibake, individuos sem familia, paredes.
- `notify.py msg "..."` / `notify.py file <caminho> --caption "..."` — envia resultado por
  Telegram lendo `NOTIFY_TELEGRAM_TOKEN`/`NOTIFY_TELEGRAM_CHAT` do ambiente (sem segredos no codigo).
- **Exportar a arvore para GEDCOM**: ferramenta open-source `getmyancestors`
  (`pip install getmyancestors`; login do proprio usuario; sem API key); depois audite com `gedcom_audit.py`.

### references/ (ler conforme a fase da pesquisa)

- `00-metodologia.md` — metodo geral: definir alvo/parede, hierarquia de fontes, ciclo de
  quebrar muros, niveis de confianca, disciplina de homonimo, documentado vs lenda.
- `01-portugal-torre-do-tombo-digitarq.md` — **endpoints exatos** do DigitArq e a anatomia
  dos reference codes paroquiais (`PT/TT/PRQ/...`, series 001-004) e mapeamento folio->imagem.
- `02-familysearch.md` — full-text por frase, registos por nome/conjuge/lugar, catalogo,
  leitura de ARKs (`1:1:`=indexado, `3:1:`=imagem) e extracao GEDCOM (getmyancestors).
- `03-paleografia.md` — abreviaturas, grafias, devocionais, armadilhas sec. XVI-XVIII; realce de imagem.
- `04-tipos-de-registo.md` — o que cada assento nomeia (casamento/batismo/obito/habilitacoes/
  notariais) e qual usar para subir geracao.
- `05-inquisicao-cristao-novo.md` — Inquisicao e ascendencia cristao-nova/judaica: a marca
  ("Xao novo"; ficha "Estatuto social: ...da nacao"), a sessao de genealogia *in genere*, e
  a questao do "nome judeu".
- `06-varredura-multiagente.md` — protocolo de varredura pagina-a-pagina por subagentes.
- `07-gedcom.md` — estrutura GEDCOM (INDI/FAM/FAMC/FAMS) e erros comuns de extracao.
- `08-outros-arquivos.md` — AHU/Projeto Resgate, Arquivos Distritais, registo civil/paroquial
  brasileiro, hemerotecas, e bases secundarias (Geni/Geneall) como pista.

### templates/

- `research_log.template.md` — diario de pesquisa + ficha de registo de fato
  (Achado | Fonte | Transcricao | Confianca | Homonimo? | Proximo passo).
- `scan_workflow.example.js` — template comentado de workflow multi-agente para varrer um livro.

### examples/

- Pasta para demonstracoes neutras usando **placeholders** (`{GUID}`, `{fileId}`, `TERMO`,
  `<ARK>`) — nunca a familia de um usuario. (Adicione as suas conforme usar a skill.)

## 4. Regras de ouro

1. **DOCUMENTADO vs TRADICAO/LENDA** — todo fato carrega o seu rotulo. Uma historia de
   familia sem assento e *tradicao*, e fica marcada como tal ate ter fonte.
2. **`[?]` em leitura incerta** — se a paleografia nao e certa, marque o trecho com `[?]`
   e proponha alternativas; nunca apresente um palpite como leitura firme.
3. **Homonimos nao sao prova** — mesma nome + mesma epoca ≠ mesma pessoa. So aceite a
   identificacao com ancora extra (lugar, conjuge, filiacao, profissao). Registe quais
   homonimos foram descartados e por que.
4. **NUNCA inventar** — nome, data, lugar ou cota/reference code que nao saiu de um
   documento nao entra na arvore. Sem fonte, nao existe.
5. **O usuario faz a verificacao final** — apresente os achados com fonte para que ele
   confira o documento; a skill propoe, o usuario confirma.
6. **Medir em registos NOVOS** — o valor de uma sessao e quantos fatos novos com fonte
   foram adicionados, nao o tamanho do texto produzido.

## 5. Privacidade e credenciais

- O usuario fornece as **proprias credenciais** — nunca embutir login/senha no codigo.
  FamilySearch e a ferramenta `getmyancestors` usam variaveis de ambiente
  (ex.: `FS_USERNAME`, `FS_PASSWORD`) ou o login interativo do proprio usuario.
- DigitArq/Torre do Tombo e publico e nao requer login.
- Nao guardar dados de pessoas vivas nem segredos no repositorio da skill. Caminhos,
  arvores e GEDCOMs do usuario ficam fora da skill, no espaco de trabalho dele.
- Esta skill e generica: ela descreve **metodo e fontes publicas**, nao a arvore de
  ninguem em particular.
