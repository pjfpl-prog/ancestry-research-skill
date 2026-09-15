# Hemeroteca Digital Brasileira (Biblioteca Nacional)

Como achar, baixar e **ler de verdade** jornal antigo no acervo da Biblioteca Nacional do Brasil,
e como extrair texto de página escaneada sem se enganar. Ferramenta: `scripts/hemeroteca_bn.py`.

Este documento tem duas partes de natureza diferente, e a separação é de propósito:

- **§1 a §5, doutrina:** o que não muda quando o servidor muda (estratégia de busca, ritmo,
  leitura, cobertura). Não leva data.
- **§6, fatos de endpoint:** URLs, formatos, comportamentos do servidor. Cada um leva a data em
  que foi verificado, e **envelhece sem aviso**. Antes de uma coleta em escala, corra o teste
  live (`HEMEROTECA_BN_LIVE=1 pytest -q -m live tests/test_hemeroteca_bn_live.py`); se falhar,
  diagnostique primeiro (rede, dependência em falta, regressão local) e só depois conclua que o
  servidor mudou; aí é o §6 que precisa de revisão, não a doutrina.

Nada aqui depende de login, senha ou ferramenta paga. Placeholders: `TERMO`, `<BIB>`, `<ANO>`,
`<EDICAO>`.

---

## 1. O que é o acervo e o que esperar dele

A Hemeroteca Digital Brasileira (`memoria.bn.gov.br`) tem jornais e revistas brasileiros
digitalizados, do século XIX aos anos 1990, com **busca de texto por OCR**. A cobertura é
desigual: alguns títulos têm décadas inteiras, outros têm poucos anos. Os grandes diários do Rio
de Janeiro são a espinha dorsal para qualquer pesquisa de pessoa entre 1900 e 1970, e os jornais
de província (Maranhão, Pernambuco, Bahia, São Paulo) cobrem o século XIX melhor do que se espera.

O que o jornal dá à genealogia, e o seu lugar na cadeia de prova (datar e localizar; filiação
secundária até o assento), está em [`08-outros-arquivos.md`](08-outros-arquivos.md) §5. Este
documento trata só do como.

Duas coisas que mudam a estratégia:

1. **A busca é por frase exata quando se usa aspas.** Sem aspas, ou com as aspas mal
   codificadas, vira "páginas com todas as palavras, em qualquer lugar" (§6.2, a armadilha mais
   cara deste acervo). Se ignora acento e como o índice se compara ao texto do PDF são
   comportamentos medidos do serviço, e por isso estão datados no §6.
2. **O OCR erra muito** em tipografia antiga: nome quebrado ("Mar ia Sou za"), palavras coladas,
   letras trocadas. Isso é o material, não defeito seu.

---

## 2. Fluxo: mapear, listar, coletar, triar, ler, declarar

1. **Mapear** (só no navegador): descobrir em que periódicos e décadas o `TERMO` aparece, e
   anotar o `bib` de cada título. É o passo que nenhum script faz (ver §6.1).
2. **Listar** (a frio): por título, as edições com ocorrência,
   `python scripts/hemeroteca_bn.py edicoes <BIB> "TERMO" --json`.
3. **Coletar**: baixar a edição em PDF, achar a página pelo texto OCR, extrair a página (PDF
   isolado, PNG, texto, recorte) e registrar numa tabela: termo, título, ano, edição, página, URL
   de origem, sha256 do arquivo inteiro, status. **A edição inteira é o original recebido**;
   guarde-a enquanto o disco permitir. Se precisar apagá-la, o que fica no registro (URL e
   sha256) é o que permite baixá-la de novo e provar que é a mesma; a página isolada é derivado.
   ```
   python scripts/hemeroteca_bn.py pdf <BIB> <ANO> <EDICAO> edicao.pdf
   python scripts/hemeroteca_bn.py paginas edicao.pdf "TERMO" --json
   python scripts/hemeroteca_bn.py extrair edicao.pdf <PAGINA> saida/ --termo "TERMO"
   ```
4. **Triar** pelo texto: quem é a pessoa certa, quem é homônimo, o que é dúbio. Homônimo é a
   regra, não a exceção: dois parentes com o mesmo sobrenome e a mesma profissão acontecem.
5. **Ler na imagem** o que for virar afirmação (o PNG ou o recorte que `extrair` grava), e só então
   escrever, com título, data, edição e página em cada linha. **OCR nunca é prova**: serve para
   achar e triar; três OCRs podem concordar no mesmo erro.
6. **Declarar a cobertura**: quantas edições a busca deu, quantas foram baixadas, quantas foram
   lidas no texto, **quantas foram abertas na imagem**. Esse último número costuma ser muito menor
   que o primeiro, e dizê-lo é o que dá credibilidade ao resto. Documento que não abriu, veio sem
   PDF ou saiu ilegível é resultado e vai no relatório com o identificador.

Uma pesquisa com mil edições de 20 MB são 20 GB. Cache o que baixou e nunca peça a mesma coisa
duas vezes; se apagar originais por falta de espaço, apague só o que já tem URL e sha256 no
registro.

---

## 3. Coletar sem abusar do servidor

O acervo é público e gratuito, mantido com dinheiro público. Coletar com educação é o que mantém o
acesso funcionando:

- **Um pedido por vez por servidor.** O script não paraleliza dentro de um processo e pausa entre
  pedidos da mesma sessão. Isso **não** coordena processos diferentes: se vários scripts seus
  coletam ao mesmo tempo, a carga que o servidor sente é a soma, e a trava por host é sua.
- **Intervalo entre pedidos, sorteado.** A razão é reduzir carga sobre um serviço público; o
  sorteio evita o padrão regular que filtros anti-robô procuram. O script sorteia entre `--delay`
  e o dobro; para coleta longa, suba a base para 6 a 8 segundos e acrescente uma pausa longa a
  cada dezena de pedidos. Declare antes de começar quantas edições vai pedir, e **pare** se o
  servidor responder 429 ou 5xx repetidos: isso é o servidor a pedir para parar, não um obstáculo.
- **Cabeçalhos de navegador de verdade**, e `Referer` do visualizador no pedido do PDF (o
  script já manda os dois).
- **Não burle CAPTCHA.** Se o caminho exige CAPTCHA, ou você resolve à mão, ou aquele material fica
  fora da sua cobertura e você **declara isso**. O script não toca no visualizador oficial.

---

## 4. Ler o PDF: onde o OCR funciona, onde mente

**Junte a hifenização antes de procurar.** Jornal parte palavra no fim da linha o tempo todo;
"Sou-\nza" não casa com "Souza". O script faz isso (`normalizar`), e também tira acento e põe em
minúsculas, porque o OCR da BN é insensível a acento.

**Tenha um plano B com uma palavra só.** Se o termo inteiro não casar em nenhuma página da edição,
repita com a palavra que mais distingue (em geral o sobrenome); o OCR quebra nomes com frequência
("fra nklin"). O script repete com a **palavra mais longa** (em empate, a última) e **diz que fez**
(`termo_usado`); a heurística não sabe o que é sobrenome, então `--alternativa PALAVRA` fixa a
escolha, e `--so-termo-inteiro` desliga a segunda tentativa.

**Palavra partida entre linhas não tem caixa única.** `page.search_for` não junta "Sou-" no fim de
uma linha com "za" no início da seguinte, então o recorte em volta do nome falharia justamente nos
casos difíceis. O script monta um "fio" contínuo de palavras, colando o hífen final à palavra
seguinte **só quando ela está noutra linha** ("alfa- beta" na mesma linha continua duas palavras),
e mapeia cada caractere para a caixa da palavra de origem. A busca exige fronteira de palavra:
`TERMO` não casa dentro de `termonuclear`, ao custo de perder OCR que colou letras ao nome.
Apelido composto com hífen ("Sá-Carneiro") casa também quando o jornal o partiu no fim da linha
e a normalização o juntou ("sacarneiro"). `extrair` grava até `--max-recortes` (6) recortes por página e **declara** quando havia mais
ocorrências do que recortes, para a cobertura dos recortes não passar por completa.

**Quando o texto do PDF não corresponde à imagem.** Existe o caso perverso: a busca acha o nome
numa edição, o PDF traz um fragmento de texto com esse nome, e a imagem da página é outra coisa. O
texto embutido está desalinhado da imagem. `paginas` devolve lista vazia ou uma página errada;
registre a ocorrência como **pendente**, não como achado, e anote o que tentou.

**Meça antes de prometer OCR próprio.** `python scripts/hemeroteca_bn.py dpi edicao.pdf` dá a
resolução real da imagem embutida. Piso prático para texto impresso: 300 dpi. Abaixo de 200, o OCR
começa a errar dígito, e ampliar não recupera o que não foi capturado. Acervos digitalizados nos
anos 2000 costumam estar em 100 a 120 dpi: legível para gente, ruim para máquina.

**OCR próprio, quando vale:** Tesseract **com o idioma português** (sem `por.traineddata` ele lê
português como inglês e devolve lixo com cara de texto). Pelo PyMuPDF,
`pagina.get_textpage_ocr(language="por", dpi=300, full=True, tessdata=...)` devolve a **caixa de
cada palavra**, o que permite recortar a evidência em página que é só imagem. Página de revista
muito grande estoura o limite interno do MuPDF (rect de 32767): extraia a imagem embutida
(`doc.extract_image`) e trabalhe nela.

**Dois passes e confronto** quando a leitura decide algo: texto nativo do PDF × OCR do render, ou
dois motores. Onde concordam, confiança alta; onde divergem, a palavra fica marcada. Divergência
sistemática na página inteira é página para revisão humana.

Para manuscrito (certidão, termo, despacho), OCR nenhum resolve: ver
[`03-paleografia.md`](03-paleografia.md) e `scripts/image_tools.py`.

---

## 5. Armadilhas em uma lista

- Aspas codificadas com `+` no lugar do espaço → a busca deixa de ser por frase e a lista vem
  **maior**, o que parece melhor e é pior (§6.2).
- Regex de edição que não aceita prefixo de letra → perde edições extra/vespertinas em silêncio.
- Combos da busca global reutilizados sem recarregar a página → resultado do filtro anterior.
- Ler a página de resultados antes de as contagens terminarem → zero ocorrências.
- Lista vazia lida como "não existe" → pode ser bloco de década inexistente (§6.2).
- 404 no PDF lido como "edição não existe" → alguns títulos não têm PDF estático (§6.3).
- `requests` do Python falhando com `CERTIFICATE_VERIFY_FAILED` → `truststore` (§6.4).
- Nome quebrado pelo OCR → buscar também com uma palavra só (`--alternativa`).
- Texto do PDF desalinhado da imagem → pendência, não achado.
- Página gigante estourando o MuPDF → extrair a imagem embutida.
- "Não achei" tratado como "não existe": só é ausência quando você diz onde procurou, com que
  termos, em que período e em que blocos.

---

## 6. Fatos de endpoint (verificados em 15/09/2026; conferir antes de confiar)

### 6.1 A busca global só roda no navegador

- Endereço: `https://memoria.bn.gov.br/hdb/DefaultNew.aspx`, aba **Período** → Local "Todos" →
  Periódico "Todos" → expressão entre aspas → Pesquisar. O resultado abre em
  `DocReader/docmulti.aspx` com a lista de acervos, páginas e ocorrências por título.
- **O resultado é calculado de forma assíncrona**: a tabela aparece vazia e vai preenchendo. Espere
  o total de "Ocorrências" aparecer no alto antes de ler.
- **Os menus são em cascata e só funcionam uma vez por carregamento**: para outra década,
  recarregue a página. Trocar só o período faz a busca rodar com os filtros velhos, sem avisar.
- `docmulti.aspx` **não responde a frio** (lê de sessão e devolve erro de referência nula). Por isso
  o mapa "em que títulos o termo aparece" é o único passo que fica no navegador.
- **Anote o `bib` de cada título**: 5 a 7 dígitos, quase sempre com sufixo de bloco de década
  (`089842_05`, `093718_02`). Está no HTML da tabela de resultados e no endereço do DocReader.
  Alguns códigos de grandes diários do Rio, como ponto de partida (o sufixo é o bloco; sufixo
  inexistente devolve lista vazia): Correio da Manhã `089842` (`_03` anos 1920, `_04` 1930-39,
  `_05` 1940-49, `_06` 1950-59, `_07` 1960-69), Diário de Notícias `093718`, Jornal do Brasil
  `030015`, O Jornal `110523`, Diário Carioca `093092`, Jornal do Commercio `364568`, A Noite
  `348970`, Gazeta de Notícias `103730` (`_05` = 1920-29), Almanak do Ministério da Marinha
  `157988` (oficiais por posto e antiguidade, 1858-1960).

### 6.2 Lista de edições de um título, a frio

- **A busca ignora acento** ("Corrêa" e "Correa" dão o mesmo): observado na busca global e na
  lista em 2026; não há documentação oficial que o afirme.
- **O índice de busca é melhor que o texto embutido no PDF**: há edições em que a lista aponta o
  termo e o texto do PDF não o tem em página nenhuma (observado em 2026 em revista ilustrada; a
  BN indexa com OCR próprio). Por isso `paginas: []` é resultado, não erro.

```
https://memoria.bn.gov.br/docreader/ListaPastaOcor.aspx?bib=<BIB>&pesq=%22TERMO%22
```

- Responde **sem sessão, sem cookie e sem CAPTCHA**, com um HTML cujo texto útil é o cabeçalho
  `PASTA` / `OCORRÊNCIAS` seguido de linhas `ano AAAA\edicao NNNNN  N` (uma `<table>` por edição;
  a edição pode ter **prefixo de letra**, `a00165`). Vem inteira numa resposta; não há paginação.
- **O espaço dentro das aspas tem de ser `%20`.** Medido no mesmo bloco e termo:
  `pesq=%22A%20B%22` → 9 edições; `pesq=%22A+B%22` (o que `urllib.parse.urlencode` produz) → 1.451;
  `pesq=A%20B` (sem aspas) → 1.451. Com `+` ou sem aspas o servidor deixa de procurar a frase.
  O script usa `quote(termo, safe="")`, e há um teste que barra a regressão. As duas formas
  largas (`+` entre aspas e sem aspas) devolveram o mesmo conjunto, a menos de 18 bytes de HTML.
- **Lista vazia é ambígua.** Bloco de década inexistente (`103730_99`) e termo sem ocorrência
  devolvem a **mesma** página (cabeçalho presente, zero linhas, HTTP 200). O script diz isso na
  nota em vez de afirmar ausência. Confira o sufixo no navegador.
- Resposta **sem** o cabeçalho é erro ou mudança de estrutura; o script levanta erro em vez de
  devolver lista vazia. Também levanta se o número de células de edição no HTML não bate com o
  número de linhas que interpretou: lista parcial em silêncio é o pior resultado possível.
- Para um humano abrir a edição no visualizador (com CAPTCHA), a própria página monta:
  `DocReader/DocReader.aspx?bib=<BIB>&pesq=TERMO&pasta=ano <ANO>\edicao <EDICAO>`. O script devolve
  esse link em `url_leitor`, para citar e para conferir na imagem.

### 6.3 O PDF da edição inteira, sem CAPTCHA

```
https://hemeroteca-pdf.bn.gov.br/<BIB_SEM_SUFIXO>/per<BIB_SEM_SUFIXO>_<ANO>_<EDICAO>.pdf
```

- Arquivo **estático** (Apache, `ETag`, `Last-Modified` de 2012 em edições antigas), servido a frio.
  O `bib` vai **sem** o sufixo de década; a edição vai **com** o prefixo de letra, quando houver.
- Tamanho de 5 a 30 MB; traz a **camada de texto do OCR** e a imagem embutida por página. Medido
  numa edição de 1921: 6 páginas, imagem de 2.940 px de largura, ~120 dpi. O script só publica o
  ficheiro no destino depois de conferir `%PDF-` no início, `%%EOF` no fim e, se o PyMuPDF estiver
  instalado, a abertura; download truncado ou página de erro não chegam ao destino.
- **Nem todo título tem PDF.** O Jornal do Brasil (`030015`) devolve 404 sistematicamente; revistas
  ilustradas também. 404 aqui **não prova** que a edição não existe: resta o visualizador, página a
  página, com CAPTCHA resolvido por gente. O script recusa gravar o que não começa por `%PDF-`.

### 6.4 TLS

`requests` sem ajuste falha com `CERTIFICATE_VERIFY_FAILED` nos **dois** hosts: o pacote de
certificados do Python (`certifi`) não tem a cadeia; o repositório do sistema operativo tem.
`truststore` (em `scripts/requirements-hemeroteca.txt`, **Python 3.10+**) resolve, e o script o
ativa sozinho quando instalado. `curl` do sistema funciona sem ajuste.

### 6.5 O visualizador oficial

`DocReader.aspx` exige **CAPTCHA por página desde 2025**. Serve para o humano conferir e citar; não
serve para automação, e este repositório não tenta contornar isso.

---

*Guia técnico, sem dados pessoais. O acervo é público; o crédito das imagens é da Biblioteca
Nacional, e reprodução de página deve citar título, data, edição e página.*
