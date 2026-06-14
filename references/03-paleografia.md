# Paleografia prática — registos manuscritos ibéricos séc. XVI-XVIII

Referência para **ler** o que está na imagem: como preparar a digitalização (recorte +
ampliação + contraste), como achar o fólio, a estrutura típica de um assento, as
abreviaturas e armadilhas do escrivão, e como atacar tinta esmaecida ou trespassada.

> A regra de ouro vem da metodologia (`00-metodologia.md`): **nunca afirmar o que não se
> leu.** Marque `[?]` em tudo que ficou incerto; incerteza lida não é facto.

Para localizar e baixar a imagem (DigitArq, sem login) veja `01-portugal-torre-do-tombo-digitarq.md`.
Para o tratamento de imagem use o script **`scripts/image_tools.py`** (§1).

---

## 1. Preparar a imagem antes de ler

Nunca tente ler a página inteira em tamanho de tela. O fluxo é sempre o mesmo:

1. **Baixar em ALTA resolução** (no DigitArq: `rdigital/dissemination?fileId=N`, não a
   `thumb`). A miniatura serve só para escolher qual imagem abrir.
2. **Recortar** só o assento/trecho da filiação (um assento ocupa poucas linhas; o resto
   da página é ruído).
3. **Ampliar** o recorte (reamostragem LANCZOS preserva o traço fino da pena).
4. **Realçar** o contraste (`autocontrast`) e, se a tinta estiver fraca, binarizar
   (`threshold`) em escala de cinza.

### 1.1 Com PIL (Pillow) — o essencial

```python
from PIL import Image, ImageOps

im = Image.open("pagina-N.jpg")

# 1) RECORTAR o trecho do assento — caixa (left, upper, right, lower) em pixels
#    (descubra a caixa olhando a página inteira primeiro; veja §1.2)
box = (LEFT, UPPER, RIGHT, LOWER)
crop = im.crop(box)

# 2) AMPLIAR ~3x com reamostragem de qualidade (LANCZOS preserva o traço)
w, h = crop.size
big = crop.resize((w * 3, h * 3), Image.LANCZOS)

# 3) ESCALA DE CINZA + AUTOCONTRASTE (espalha o histograma; realça tinta desbotada)
gray = ImageOps.grayscale(big)
auto = ImageOps.autocontrast(gray, cutoff=2)   # cutoff 1-3% corta extremos e dá mais "punch"
auto.save("recorte-autocontrast.png")

# 4) THRESHOLD (binarização) — quando a tinta está fraca e o fundo manchado.
#    Ajuste T (0-255) por tentativa: T alto = mais preto; T baixo = mais branco.
T = 128
bw = auto.point(lambda p: 255 if p > T else 0).convert("1")
bw.save("recorte-threshold.png")
```

> **Não jogue fora a versão em cinza.** A binarização (`threshold`) é ótima para tinta
> esmaecida mas *engole* traços finos e detalhe; mantenha sempre a versão em escala de
> cinza com `autocontrast` ao lado e compare as duas para o nome/data crítico.

Outros gestos úteis do PIL:
- `ImageOps.invert(gray)` — inverte (tinta clara sobre fundo escuro vira escura sobre claro).
- `im.rotate(ÂNGULO, expand=True)` — endireitar páginas tortas (escrita inclinada cansa a leitura).
- `ImageOps.equalize(gray)` — equalização de histograma (alternativa ao autocontrast em
  páginas muito desigualmente iluminadas).
- `crop.resize((w*4, h*4), Image.LANCZOS)` — para uma abreviatura/rubrica minúscula, suba a 4x.

### 1.2 Achar a caixa de recorte (box)

A caixa `(left, upper, right, lower)` é em pixels, origem no canto superior-esquerdo.
Forma prática de descobrir:
1. Abra a imagem inteira; estime a fração da página onde está o assento.
2. Multiplique pelas dimensões reais: se o assento está no terço superior de uma página
   de `3000×4000` px, comece com `box = (0, 0, 3000, 1333)` e vá apertando.
3. Salve o recorte e confira; ajuste. Recortar de menos perde o início/fim do assento;
   recortar de mais inclui tinta trespassada da página vizinha.

### 1.3 Script da skill

`scripts/image_tools.py` encapsula este fluxo (baixar → recortar → ampliar → autocontrast
→ threshold → salvar variantes). Use-o em vez de reescrever PIL a cada página; chame
recorte/contraste/threshold como opções. Quando o livro não é indexado e a varredura é
multi-agente (lotes de ~10-13 imagens), cada subagente roda o mesmo `image_tools.py` e
devolve o recorte realçado + a transcrição.

---

## 2. Ler o número do fólio (o canto)

O assento **não tem número de página da web** — tem o **fólio** escrito à mão no
documento original. É o que entra na citação da fonte (`00-metodologia.md`, §9).

- O fólio costuma estar no **canto superior** da página, em geral do lado de fora
  (direito na frente). Pode ser algarismo ou, em livros mais antigos, **numeração
  romana** (`xxiij` = 23; repare no `j` final = `i` terminal).
- Numera-se a **folha**, não a página: a **frente** = *recto* (numerada), o **verso** =
  *vº* (mesmo número, sem novo algarismo). Cite sempre frente/verso (ex.: "fl. 23v").
- Pode haver **dupla numeração** (antiga a tinta + moderna a lápis/carimbo) que não
  coincidem. Anote qual você usou.
- Recorte e amplie o canto à parte — fólios estão muitas vezes esmaecidos ou cortados na
  digitalização. Se ilegível, registe o **fileId** e a **posição na sequência** de imagens
  como localizador de recurso (e marque o fólio com `[?]`).

> O mapeamento fólio ↔ imagem (offset por capa/guardas, índice onomástico no fim) está
> detalhado em `01-portugal-torre-do-tombo-digitarq.md`, §5.3.

---

## 3. Estrutura típica de um assento

Os assentos seguem **fórmulas** quase fixas. Conhecer a fórmula é meia leitura: você sabe
onde olhar o nome do pai mesmo sem decifrar todas as palavras à volta.

### 3.1 Batismo (esqueleto)

```
"Aos [DIA] dias do mês de [MÊS] de [ANO por extenso] baptizei (ou: pus os santos óleos a)
 [NOME], f.o de [PAI] e de sua m.er [MÃE], [moradores / naturais de LUGAR];
 foram padrinhos [PADRINHO] e [MADRINHA]. [Assinatura do P.e / pároco]"
```
Onde olhar: **`f.o de … e de sua m.er …`** = filiação. Padrinhos às vezes revelam avós ou
tios (úteis para confirmar identidade — `00-metodologia.md`, §6).

### 3.2 Casamento (esqueleto) — o que mais sobe geração

```
"Aos [DIA] de [MÊS] de [ANO] … receberam-se por marido e m.er [NOIVO], f.o de [PAI DO NOIVO]
 e de [MÃE DO NOIVO], natural de [LUGAR A], com [NOIVA], f.a de [PAI DA NOIVA] e de
 [MÃE DA NOIVA], natural de [LUGAR B]; testemunhas [...]"
```
Onde olhar: **duas filiações + duas naturalidades** num só assento. É o documento que
sobe dois ramos de uma vez (ver `02-...` / `00-metodologia.md`, §4).

### 3.3 Óbito (esqueleto)

```
"Aos [DIA] de [MÊS] de [ANO] faleceu [NOME], [estado civil: casado com / viúvo de CÔNJUGE
 | solteiro, f.o de PAI e MÃE], de idade de [N] anos pouco mais ou menos; recebeu os
 sacramentos; foi sepultado em [LUGAR]."
```
Onde olhar: cônjuge e **idade "pouco mais ou menos"** (aproximada — pode errar 5-10 anos;
o batismo vence o óbito para a data de nascimento).

> As fórmulas variam por diocese, época e mão do escrivão, mas a **ordem dos elementos**
> (data → ato → nome → filiação/cônjuge → naturalidade → testemunhas → assinatura) é
> notavelmente estável. Aprenda a fórmula da paróquia lendo 2-3 assentos legíveis antes de
> atacar o esmaecido.

---

## 4. Abreviaturas comuns e expansão

Os escrivães abreviavam para poupar tinta e espaço. As mais frequentes:

| Abreviatura | Expansão | Notas |
|---|---|---|
| `P.e` | **Padre** | sobre-escrito o `e`; muito comum antes do nome do celebrante |
| `R.do` / `R.do P.e` | **Reverendo** / Reverendo Padre | tratamento do clero |
| `B.el` | **Bacharel** | grau/estatuto |
| `Lic.do` | **Licenciado** | grau |
| `Dr.` / `D.or` | **Doutor** | |
| `m.er` | **mulher** (= esposa) | "sua m.er" = sua esposa |
| `md.or` / `mor.or` | **morador** | "mor.or em LUGAR" |
| `f.o` / `f.a` | **filho** / **filha** | a chave da filiação |
| `f.os` | **filhos** | plural |
| `leg.mo` / `leg.ma` | **legítimo / legítima** | "f.o leg.mo" = filho legítimo (vs. natural/exposto) |
| `N.S.a` | **Nossa Senhora** | em invocações e em nomes devocionais (ver §5) |
| `Sñr` / `Sr.` | **Senhor** | |
| `S.to` / `S.ta` | **Santo / Santa** | em nomes/lugares |
| `Js` / `Jhs` / `Jesu` | **Jesus** | monograma; aparece em nomes devocionais |
| `q` (com til/traço) | **que** | sinal de abreviatura geral |
| `qm` | **quem** | |
| `nñ` / `ñ` | **não** | til sobre vogal/letra = `n`/`m` omitido |
| `tpo` | **tempo** | |
| `m.to` / `m.ta` | **muito / muita** | |
| `p.a` | **para** | |
| `p.lo` / `p.la` | **pelo / pela** | |
| `q.do` | **quando** | |
| `dr.os` | **direitos** | em notariais |
| `test.as` | **testemunhas** | fecho de casamento/escritura |
| `fall.eo` / `fal.eo` | **faleceu** | em óbitos |
| `bapt.ei` / `bautizei` | **baptizei** | em batismos |
| `nat.al` | **natural (de)** | a naturalidade — crucial para subir ramo noutra paróquia |

Regras gerais de abreviatura:
- **Letra sobre-escrita** (em expoente) indica abreviatura: `f`+`o` = `f.o` = "filho".
- **Til ou traço horizontal** sobre uma letra = `m` ou `n` omitido (`Joã` = "João",
  `cõ` = "com", `bẽ` = "bem").
- **`9` inicial** ou cifra parecida = prefixo "con-/com-" em alguns punhos.
- Quando expandir, registe a **forma literal** primeiro e a expansão depois (ex.:
  `f.o leg.mo` → "filho legítimo") — assim outra pessoa pode auditar a leitura.

---

## 5. Nomes devocionais variáveis

Os apelidos religiosos **não são apelidos de família fixos** e variam de assento para
assento da mesma pessoa. Trate-os como parte fluida do nome, não como prova de identidade.

Formas comuns: **da Conceição**, **de Jesus**, **dos Santos**, **do Espírito Santo**,
**das Neves**, **do Rosário**, **da Assunção**, **da Piedade**, **das Dores**, **da Glória**.

Cuidados:
- A **mesma pessoa** pode ser "Maria da Conceição" no batismo e "Maria dos Santos" no
  casamento. A coincidência ou divergência de devocional **não** confirma nem descarta
  identidade sozinha — desempate por filiação + naturalidade + datas + cônjuge
  (`00-metodologia.md`, §6).
- Frequentemente abreviados: `da Conç.am`, `de Js`, `do E.S.to`. Expanda com cuidado.
- O **nome próprio** (primeiro nome) é o eixo mais estável; o devocional é o mais volátil.
  Não construa uma identificação só sobre o devocional.

> Patronímicos e apelidos toponímicos também variam (ortografia, com/sem preposição). O
> nome é uma pista; a **âncora** é a teia de filiação + lugar + datas + cônjuge.

---

## 6. Correções, riscos e inserções do escrivão

A página não é limpa. O escrivão erra, risca, corrige e insere:

- **Riscado (tachado)**: palavra cancelada — leia o que está **por cima/à margem**, não o
  riscado. Mas confira: às vezes o risco é só um borrão e a palavra vale.
- **Entrelinha**: palavra acrescentada **acima da linha** (com um sinal de inserção `^`)
  pertence ao texto; integre-a na posição marcada.
- **Notas de margem**: averbamentos (ex.: "casou em [ANO] em [LUGAR]", anotação de óbito
  posterior no assento de batismo). Pode ser **a peça que liga dois eventos** — leia
  sempre a margem.
- **`Emendei` / `vale` / `não vale`**: fórmulas de validação de emenda. "vale o
  entrelinhado X" = aquela inserção é válida; "não vale o riscado Y" = ignore o riscado.
- **Repetição/salto**: o escrivão às vezes repete uma linha ou salta; compare com o
  assento anterior e seguinte se algo não fecha.

Marque `[?]` em qualquer trecho onde a correção tornou a leitura ambígua, e descreva o que
viu ("nome riscado, ilegível; por cima lê-se `[?]`...").

---

## 7. Datas por extenso

As datas vêm quase sempre **por extenso**, não em algarismos. Saber decompô-las evita erro
de século.

Estrutura: `Aos [DIA] dias do mês de [MÊS] de [ANO]`.

- **Ano**: "**mil sete centos e [...]**" = 17xx; "**mil seis centos e [...]**" = 16xx;
  "**mil oito centos e [...]**" = 18xx. A unidade/dezena fecha o ano: "mil sete centos e
  trinta e quatro" = 1734.
- **Dia**: "aos **vinte e três** dias", "ao **primeiro** dia", "aos **dezasseis**".
- **Mês** por extenso (atenção à grafia antiga): `Janeiro, Fevereiro/Feuereiro, Março,
  Abril, Mayo/Maio, Junho, Julho, Agosto, Setembro/Septembro, Outubro/Octubro, Novembro,
  Dezembro/Dezẽbro`.
- **Armadilha do século**: "mil sete centos" é **1700s**, não 1600s — confira contra as
  datas do livro (DigitArq dá `dateInitial`/`dateFinal` do volume; a data do assento tem
  de cair dentro).
- **Numeração romana** em fólios e por vezes em datas: `j`=1 (terminal), `v`=5, `x`=10,
  `l`=50, `c`=100. `xxiiij` = 24.
- Transcreva o ano **por extenso como está** e converta ao lado: "mil sete centos e trinta
  e quatro (1734)".

---

## 8. Tinta esmaecida, manchada ou trespassada

Os três problemas mais comuns e o que fazer:

### 8.1 Tinta esmaecida (fraca/apagada)
- Escala de cinza + `autocontrast` (cutoff 2-3) é a primeira tentativa.
- Se ainda fraco, `threshold` baixando o `T` até o traço aparecer sem encher de ruído.
- `ImageOps.equalize` quando a iluminação da digitalização é desigual.
- Inverter (`ImageOps.invert`) às vezes torna a tinta clara mais legível ao olho.
- Ampliar mais (4x) o trecho crítico; o traço fraco "ganha corpo" na reamostragem.

### 8.2 Tinta trespassada (a escrita do verso aparece de trás)
- É o **fantasma** da página seguinte/anterior atravessando o papel.
- A escrita real e a trespassada têm **direções/intensidades diferentes**: a trespassada
  costuma estar **espelhada** e mais clara. Compare com a página do verso para confirmar
  qual é qual.
- `threshold` mais agressivo (T mais alto) tende a apagar o fantasma (mais claro) e manter
  a tinta real (mais escura). Cuidado para não apagar também tinta real esmaecida.

### 8.3 Manchas, humidade, foxing
- Recorte **abaixo/ao lado** da mancha quando a linha relevante escapa dela.
- Canais de cor: às vezes um canal isolado (ex.: o canal **vermelho** ou o **azul**) separa
  melhor a tinta ferrogálica do fundo amarelado. Em PIL: `r, g, b = im.split()` e teste
  cada canal em cinza antes do autocontrast.
- Quando nada resolve: registe a **localização exata** (fileId + fólio) e marque o trecho
  `[ilegível]`; não chute. Um negativo documentado (`00-metodologia.md`, §11) vale mais que
  um palpite apresentado como leitura.

---

## 9. Disciplina de transcrição

1. **Transcreva literal primeiro**, normalize depois (duas linhas): preserve a grafia
   original como prova; a normalização é leitura sua.
2. **`[?]`** em palavra/nome/data incerta; **`[ilegível]`** no que não dá para ler;
   **`[...]`** no que omitiu de propósito.
3. **Expanda abreviaturas** marcando a expansão (itálico, colchetes ou nota) — não invente
   letras que não estão lá.
4. Anote **fólio + frente/verso + fileId** de cada trecho (a citação da fonte).
5. Nomes devocionais (§5) e ortografia variável **não** confirmam identidade sozinhos;
   desempate sempre por filiação + lugar + datas + cônjuge.
6. **Nunca** "melhore" a leitura para encaixar uma hipótese (homónimo conveniente). Se a
   tinta não diz, você não diz.

---

## 10. Referência rápida

| Quero... | Faço... |
|---|---|
| Realçar tinta fraca | escala de cinza + `ImageOps.autocontrast(g, cutoff=2)` |
| Tinta muito apagada | `threshold` (`point(lambda p: 255 if p>T else 0)`), baixar T |
| Ampliar sem borrar | `crop.resize((w*3, h*3), Image.LANCZOS)` |
| Apagar tinta trespassada | `threshold` com T mais alto; comparar canais de cor |
| Endireitar página torta | `im.rotate(ÂNGULO, expand=True)` |
| Achar o fólio | recortar/ampliar o canto superior externo; romanos: `j`=1 terminal |
| Expandir `f.o de … m.er …` | "filho de … esposa …" = a filiação |
| Decodificar o ano | "mil sete centos e …" = 17xx; converter ao lado |
| Tratar devocional variável | é nome fluido, não prova — desempatar por filiação+lugar+datas+cônjuge |
| Rodar o fluxo todo | `scripts/image_tools.py` (baixar→recortar→ampliar→contraste→threshold) |
