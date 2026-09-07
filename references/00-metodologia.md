# Metodologia geral de pesquisa genealógica documental

Referência base da skill. Define COMO se pesquisa ascendência com rigor documental:
identificar o problema (o "muro"), escolher fontes na ordem certa, iterar até quebrar
o muro, e registar cada achado com confiança e fonte. Tudo aqui é genérico — use
placeholders (`TERMO`, `{GUID}`, `<ARK>`, `Pessoa-A`, `Lugar-X`, `ANO`).

---

## 1. Princípio central

Genealogia documental responde a uma pergunta de cada vez:

> "Quem eram os pais de `Pessoa-A`, que viveu em `Lugar-X` por volta de `ANO`?"

Não se pesquisa "a família" em abstrato. Pesquisa-se **uma ligação geracional** de
cada vez, do conhecido para o desconhecido (de filho para pai, nunca o contrário).
Cada ligação confirmada vira o novo ponto de partida.

---

## 2. O "muro" (brick wall): o último antepassado certo

O **muro** é o antepassado mais antigo numa linha sobre quem você tem prova documental
sólida, mas cujos pais ainda não conseguiu documentar. É a fronteira entre o que está
provado e o que falta.

Antes de atacar um muro, escreva-o de forma operacional:

```
MURO atual (linha paterna de Pessoa-A):
  Pessoa certa: <nome completo como aparece nos documentos>
  Naturalidade: <freguesia/cidade + país>  [ou "desconhecida"]
  Datas-âncora: nasc. ~ANO  |  casou ~ANO em Lugar-X  |  morreu ~ANO
  Cônjuge: <nome>            (âncora muito forte — ver §6)
  O que falta: nomes dos pais + naturalidade dele
  Fonte do que já sei: <citação — ver §9>
```

Ter o muro escrito assim faz três coisas:
1. define **o objetivo** (subir uma geração: achar os pais);
2. dá os **critérios de prova** (qualquer candidato tem de bater com naturalidade,
   datas e cônjuge);
3. impede de "redescobrir" o que já se sabe.

Mantenha um alvo explícito por frente. Investigue familiares ou frentes independentes quando
isso ajudar as perguntas autorizadas; não troque o objetivo por expansão indiscriminada.

---

## 3. Hierarquia de fontes

Avalie a origem do documento (original ou derivado), a informação de cada campo
(conhecimento direto ou declaração posterior) e a inferência usada. As categorias abaixo
orientam a busca; não garantem automaticamente a verdade de todas as afirmações.

### 3.1 Fonte primária (prova)
Um documento contemporâneo pode fornecer informação direta de um evento, mas secundária
sobre outro. Por exemplo, um casamento documenta o casamento e declara o nascimento dos
noivos; não substitui o assento natal. Avalie informante e contexto antes de confirmar o elo.

- **Assentos paroquiais**: batismo, casamento, óbito (livros da paróquia).
- **Registo civil** (a partir da sua criação em cada país).
- **Notariais**: testamentos, justificações, escrituras, sesmarias, inventários.
- **Habilitações** (ordens militares, familiar do Santo Ofício): inquéritos de
  genealogia de 3-4 gerações — uma fonte primária densíssima quando existe.
- **Processos** (incl. inquisitoriais) com sessão de genealogia.

> Prefira informação próxima do evento e de informante qualificado, sem declarar uma
> fonte infalível. Batismo e nascimento são eventos diferentes; só atribua data natal
> que o documento efetivamente declare. Idade no óbito é informação para cálculo/estimativa:
> preserve a idade literal, o método e os valores conflitantes.

### 3.2 Fonte secundária (pista)
Compilada **depois**, por terceiros, a partir de outras fontes (que podem estar certas,
erradas ou copiadas com engano):

- Genealogias impressas, nobiliários, livros de família.
- Árvores online colaborativas (tipo Geni, WikiTree, FamilySearch Family Tree na parte
  *editada por utilizadores*, MyHeritage).
- Índices, transcrições e bases indexadas por terceiros.

**Por que são só pistas, não prova:** ninguém auditou a cadeia. Erros comuns: cópia
de homónimo, "salto" de geração não documentado, datas arredondadas, ligação inventada
para encaixar numa linha nobre. Uma árvore online com 200 fontes pode ter zero fontes
**naquela** ligação específica.

> Uso correto de uma secundária: **lê-la como hipótese e ir buscar a primária que ela
> deveria citar.** "A genealogia X diz que o pai é `Pessoa-B`, de `Lugar-Y`, ~ANO →
> então procuro o assento de casamento/batismo que prove isso." Se a primária aparece e
> bate, o achado sobe para confiança alta. Se não aparece, fica como pista (baixa).

### 3.3 Tradição / lenda
Memória oral, "diz-se que descende de...", origem nobre/bíblica/sefardita por boato.
**Nunca** é prova. Pode orientar onde procurar, mas entra no relatório claramente
rotulada como tradição (ver §8).

---

## 4. Qual assento subir uma geração — e o que cada um nomeia

Escolher o tipo de documento certo poupa semanas. O que cada um entrega:

| Assento | O que nomeia | Valor para quebrar muro |
|---|---|---|
| **Casamento** | pais do noivo **E** da noiva + naturalidades dos noivos | **O melhor** — sobe uma geração nos dois lados de uma vez |
| **Batismo** | pais; por vezes avós/padrinhos; data; às vezes naturalidade do pai | Forte — documenta o batismo e pode declarar a data de nascimento |
| **Óbito** | filiação, estado civil, cônjuge, idade (aproximada) | Útil — confirma cônjuge e dá idade (para estimar nascimento) |
| **Habilitação** (ordem/Santo Ofício) | genealogia formal de 3-4 gerações | Excecional quando existe |
| **Notariais** (testamento, justificação, sesmaria) | filiação, herdeiros, bens, por vezes naturalidade | Bom complemento e desempate |

Para filiação e naturalidades, o casamento costuma ter alto retorno; ajuste a prioridade
à pergunta e à cobertura. Para resolver nascimento, busque o próprio registro contemporâneo.
Para variantes de nomes, correlacione filhos e cônjuges conforme
[correlação e arquivo](09-correlacao-e-arquivo.md).

---

## 5. O ciclo iterativo de quebrar um muro

Trate cada muro como um ciclo curto e repetível:

```
1. DEFINIR   → escreva o muro (§2): pessoa certa, lugar, datas, cônjuge, o que falta.
2. PREVER    → que documento nomearia os pais? (casamento > batismo > óbito > notarial)
               em que arquivo/base ele estaria? (paróquia de Lugar-X, no período ANO)
3. LOCALIZAR → busca indexada por nome/lugar/data. Há índice? Há imagens?
4. LER       → abrir a imagem; ler a filiação e naturalidades (ver paleografia, §10).
5. AVALIAR   → bate com naturalidade + datas + cônjuge? É a pessoa certa ou homónimo (§6)?
6. REGISTAR  → grave o achado com fonte e nível de confiança (§7, §9).
7. AVANÇAR   → a ligação confirmada vira o NOVO muro. Volte ao passo 1.
```

Se o passo 3 falha (livro **não indexado por nome**), passa-se à varredura
página-a-página: dividir as imagens do livro em lotes (~10-13 por agente/sessão),
cada lote é baixado e lido, e os achados (com homónimos marcados) voltam para
reconciliação. É lento mas é como muitos muros caem.

Se um ciclo não resolve, **não invente**: registe o muro como ainda em aberto, anote o
que já se eliminou (paróquias varridas, anos cobertos) e qual a próxima fonte a tentar.
Negativo documentado também é progresso.

---

## 6. Disciplina de homónimo (a regra que evita 90% dos erros)

**Mesmo nome ≠ mesma pessoa.** Em registos antigos, nomes devocionais e patronímicos
repetem-se imenso numa mesma freguesia e época. Encontrar "`Pessoa-A`" num assento
**não** prova que é o **seu** `Pessoa-A`.

Para aceitar que dois registos são da MESMA pessoa, exija coincidência em **vários**
eixos independentes — não basta o nome:

- **Naturalidade / lugar** (freguesia, não só o país).
- **Filiação** (nomes dos pais batem com o que já sabia, ou são consistentes).
- **Datas** (idade/ano compatíveis: ninguém casa antes de nascer nem 30 anos depois de morrer).
- **Cônjuge** (âncora fortíssima: um casal `Pessoa-A` × `Pessoa-C` é muito mais único
  que um nome sozinho).
- **Padrinhos / testemunhas / vizinhança** recorrentes entre documentos.
- **Endereço na época** e avós concordantes ajudam a ligar irmãos e variantes de nomes,
  mas não bastam isoladamente. Padrinho homônimo do avô não é automaticamente o avô.

Sinais de alerta de homónimo:
- dois batismos com o mesmo nome na mesma freguesia em poucos anos (pode haver dois
  primos homónimos, ou uma criança que morreu e outra renomeada);
- a única coincidência é o nome, e lugar/datas "quase" batem;
- a única fonte é uma árvore online (secundária) que pode já ter trocado homónimos.

Quando há dúvida real entre dois candidatos, **não escolha o conveniente.** Registe
ambos como hipóteses concorrentes, com o que distingue cada um, e marque o muro como
não resolvido até desempatar com mais um documento.

---

## 7. Níveis de confiança

Atribua a CADA ligação um nível, e justifique-o:

- **ALTA** — fonte **primária** que nomeia explicitamente a filiação, **e** bate em
  naturalidade + datas + cônjuge, **sem** homónimo plausível por perto.
  *Ex.:* casamento de `Pessoa-A` em `Lugar-X`, `ANO`, nomeia os pais e a naturalidade;
  a noiva e as datas coincidem com o que já se sabia.

- **MÉDIA** — primária com **um eixo fraco ou faltando**, ou exige inferência razoável.
  *Ex.:* o óbito dá a idade e o cônjuge certos mas não nomeia os pais; ou a filiação
  aparece mas a naturalidade não foi confirmada; ou só há transcrição/índice, ainda não
  vi a imagem.

- **BAIXA** — só **secundária/pista**, ou primária com homónimo por resolver, ou
  leitura paleográfica muito incerta.
  *Ex.:* uma árvore online afirma a ligação mas não localizei o assento; ou achei um
  candidato cujo nome bate mas a naturalidade diverge.

Regras:
- Uma cadeia é tão forte quanto o **elo mais fraco**: se uma geração é BAIXA, tudo o que
  está acima dela herda essa incerteza.
- Confiança **não sobe por repetição** numa secundária: dez árvores que se copiaram
  continuam a valer uma pista, não uma prova.
- Uma segunda fonte independente concordante pode elevar a confiança; avalie também os
  conflitos. Segunda via, fotografia, índice e páginas do mesmo ato não são independentes.
- Registre confiança por afirmação e por vínculo. Diferencie dado declarado, cálculo,
  hipótese de identidade e fato comprovado; uma transcrição legível não resolve tudo.

---

## 8. Documentado vs tradição/lenda

Separe sempre, no raciocínio e no relatório:

- **DOCUMENTADO** — a declaração do documento tem fonte citável (§9); a conclusão
  genealógica deve indicar se está comprovada, declarada, calculada ou ainda em hipótese.
- **TRADIÇÃO / LENDA** — origem nobre, descendência de figura famosa, raiz
  sefardita/bíblica "de família", "veio de tal país". Pode ser ponto de partida de
  busca, mas só vira facto se uma primária a sustentar. Até lá, fica numa secção à parte
  e rotulada como tradição.

Nunca apresente tradição com a mesma tinta de um achado documentado. O erro clássico é
"emendar" uma lenda atraente forçando um homónimo conveniente (§6).

---

## 9. Como registar um achado (com citação de fonte)

Todo achado precisa ser **reencontrável por outra pessoa**. Mínimo a gravar:

```
ACHADO
  Ligação:     <Pessoa-A> é filho/a de <Pessoa-Pai> e <Pessoa-Mãe>
  Tipo:        casamento | batismo | óbito | habilitação | notarial
  Data/lugar do evento: ANO, <freguesia/cidade, país>
  Fonte (citação):
     Arquivo:   <nome do arquivo / base>
     Cota/ref:  <reference code ou cota — ex. PT/TT/PRQ/<paroquia>/<serie>/<livro>>
     Localização interna: livro <n>, fólio <n> (frente/verso)
     Identificador digital: {GUID} / <ARK> / {fileId}  (e URL se houver)
     Imagem: <link ou caminho do recorte guardado>
  Transcrição do trecho-chave: "<...filho de F.o de Pessoa-Pai e de Pessoa-Mãe,
     naturais de Lugar-Y...>"   (marque [?] o que ficou incerto)
  Confiança:   ALTA | MÉDIA | BAIXA  — porquê: <...>
  Homónimos:   <descartados como? ou candidatos concorrentes a desempatar>
```

Diretrizes de citação:
- Copie a **cota/reference code disponível** e identifique instituição e jurisdição.
  `PT/TT/PRQ/...` é exemplo da Torre do Tombo, não prefixo universal. Não invente cota:
  se ausente, marque a lacuna e use ARK/GUID, livro/folha/termo e metadados disponíveis.
- Guarde o **identificador digital** e a imagem integral disponibilizada, com continuação,
  verso e margens relevantes. Recortes são derivados; não substituem a imagem de origem.
- **Transcreva o trecho que sustenta a ligação**, não só "confirmado". O documento é a
  fonte; a transcrição e a justificativa permitem auditar a leitura e a inferência.

---

## 10. Leitura: nunca afirmar o que não se leu

- Trabalhe sobre a **imagem em alta resolução**; recorte e amplie o trecho da filiação
  (ferramentas de imagem: aumentar contraste/`autocontrast`, `threshold` para realçar
  tinta desbotada).
- Conheça as abreviaturas do período (ibérico séc. XVI-XVIII): `P.e`=Padre,
  `B.el`=Bacharel, `m.er`=mulher, `f.o`/`f.a`=filho/filha, `R.do`=Reverendo,
  `N.S.a`=Nossa Senhora. Nomes devocionais (da Conceição, de Jesus, dos Santos) variam.
- Cuidado com **correções/riscos do escrivão**, com o número do **fólio** no canto, e
  com tinta passada da página de trás.
- Marque `[?]` em qualquer palavra/nome/data que ficou incerta. **Incerteza lida ≠ facto.**

---

## 11. Regras invioláveis de qualidade

1. **Nunca inventar** nome, data ou cota. Se não está no documento, não existe.
2. **Nunca apresentar homónimo como prova.** Na dúvida, hipóteses concorrentes.
3. **Distinguir sempre** primária (prova) de secundária (pista) e de tradição (lenda).
4. **Citar a fonte** de cada achado (cota + identificador + transcrição do trecho).
5. **Marcar `[?]`** em leituras incertas e a confiança (ALTA/MÉDIA/BAIXA) em cada ligação.
6. A cadeia vale o **elo mais fraco**: propague a incerteza para cima.
7. **Negativo conta**: registe paróquias varridas e anos cobertos sem resultado.
8. **A verificação final é do utilizador.** A skill entrega achados com fonte e confiança;
   não declara linhagem "fechada" por conta própria.

---

## 12. Esqueleto de fluxo (resumo operacional)

```
para cada MURO em aberto:
    definir muro (pessoa certa, lugar, datas, cônjuge, o que falta)
    escolher assento-alvo (casamento > batismo > óbito > habilitação > notarial)
    localizar (busca indexada; se não indexado → varredura por lotes de imagens)
    ler imagem em alta-res (recorte + contraste; abreviaturas; [?] no incerto)
    avaliar homónimo (naturalidade + filiação + datas + cônjuge)
    registar achado (cota + identificador + transcrição + confiança + homónimos)
    se confirmado: a nova geração vira o próximo muro
    senão: registar negativo e próxima fonte a tentar
```
