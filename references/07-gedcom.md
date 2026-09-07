# GEDCOM — auditar e usar a árvore extraída

Depois de extrair a sua árvore do FamilySearch com `getmyancestors`
(ver [`02-familysearch.md`](02-familysearch.md), §5) você fica com um ficheiro
**`.ged`** (GEDCOM). É o formato-padrão de troca de genealogia desde os anos 80 e
quase todo software lê e escreve (Gramps, Ancestry, Family Tree Maker, etc.).

Para a skill, o GEDCOM serve a dois propósitos:

1. **mapa de muros** — listar quem **não tem pais conhecidos** (são esses os
   alvos da pesquisa documental: para cada um, ir buscar o casamento/batismo que
   nomeia os pais — ver [`04-tipos-de-registo.md`](04-tipos-de-registo.md));
2. **fonte de erros silenciosos** — a extração automática frequentemente introduz
   lixo (datas trocadas, mojibake, nós que não são pessoas) que, se não for caçado,
   contamina toda a análise a jusante. **Audite antes de confiar.**

Trate o `.ged` como **dado pessoal**: não o versione em repositório público, não o
cole em logs. A autenticação deve seguir o fluxo seguro do ambiente, sem segredos
em argumentos, URLs, comandos ou variáveis/interpolação de shell.

---

## 1. Estrutura do GEDCOM — o mínimo para ler e auditar

GEDCOM é um ficheiro de texto em linhas, cada uma com um **nível** (inteiro), uma
**tag** e um valor. O nível indica aninhamento (o nível N+1 é detalhe do N).

Dois tipos de registo importam para genealogia:

- **`INDI`** = indivíduo (uma pessoa).
- **`FAM`** = família (uma unidade: tipicamente um casal e os filhos).

Cada registo tem um **identificador** entre arrobas, ex. `@I123@` (indivíduo) e
`@F45@` (família). As ligações entre registos são feitas por esses identificadores.

### Tags essenciais

| Tag | Onde | Significa |
|---|---|---|
| `NAME` | em `INDI` | nome (o apelido vai entre barras: `Maria /Silva/`) |
| `SEX` | em `INDI` | `M` / `F` / `U` |
| `BIRT` | em `INDI` | evento de **nascimento** (tem `DATE`/`PLAC` aninhados) |
| `BAPM`/`CHR` | em `INDI` | **batismo** |
| `DEAT` | em `INDI` | evento de **óbito** |
| `MARR` | em `FAM` | evento de **casamento** |
| `DATE` | sob um evento | a data do evento |
| `PLAC` | sob um evento | o lugar do evento |
| `FAMC` | em `INDI` | aponta para a **família onde a pessoa é FILHO** (Child) |
| `FAMS` | em `INDI` | aponta para a **família onde a pessoa é CÔNJUGE** (Spouse) |
| `HUSB`/`WIFE` | em `FAM` | marido/mulher (apontam para `INDI`) |
| `CHIL` | em `FAM` | um filho (aponta para `INDI`) |
| `SOUR` | vários | fonte/citação |

**Mnemónica das duas tags que mais confundem:**
- **`FAMC` = família onde é Child** → é por aqui que se sobe (estão os PAIS dela).
- **`FAMS` = família onde é Spouse** → é por aqui que se desce (cônjuge e filhos).

Quem **não tem `FAMC`** (ou tem `FAMC` mas a `FAM` não tem `HUSB`/`WIFE`) é uma
pessoa **sem pais conhecidos** = um **muro**. Essa é a lista de trabalho.

### Esqueleto mínimo (placeholders, registo neutro)

```gedcom
0 @I1@ INDI
1 NAME Maria /Silva/
1 SEX F
1 BIRT
2 DATE 12 MAR 1820
2 PLAC Freguesia X, Concelho Y, Portugal
1 DEAT
2 DATE 4 JUL 1890
2 PLAC Freguesia X, Concelho Y, Portugal
1 FAMC @F2@        <- família onde Maria é FILHA (estão aqui os pais dela)
1 FAMS @F1@        <- família onde Maria é CÔNJUGE

0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
1 MARR
2 DATE 1842
2 PLAC Freguesia X
1 CHIL @I3@

0 @F2@ FAM         <- a família dos pais de Maria
1 HUSB @I9@        <- pai
1 WIFE @I8@        <- mãe
1 CHIL @I1@        <- Maria
```

> Encoding: GEDCOM 5.5.1 usa `UTF-8` ou `ANSEL`; ficheiros antigos podem vir em
> `latin-1`/`cp1252`. O cabeçalho (`0 HEAD` → `1 CHAR <encoding>`) **declara** o
> encoding — mas nem sempre diz a verdade. Daí o mojibake (ver §2.2).

---

## 2. Erros comuns de extração — o que caçar

Estes são os defeitos que mais aparecem em GEDCOM gerado por scraping/IA e que a
auditoria tem de apanhar antes de você usar a árvore.

### 2.1 Data de ÓBITO lançada como NASCIMENTO (e vice-versa)

O erro mais perigoso porque **parece um dado válido**. Acontece quando o extrator
confunde os campos, ou quando o registo de origem só tinha uma data e o parser a
colou no campo errado.

**Sintomas detetáveis por script:**
- `BIRT.DATE` **posterior** a `DEAT.DATE` (nasceu depois de morrer) — impossível;
- idade ao morrer **negativa** ou **absurda** (> ~115 anos);
- a `BIRT.DATE` coincide exatamente com a `DEAT.DATE` de um registo paroquial de
  óbito (sinal de que a data do óbito foi copiada para o nascimento);
- pessoa **mais velha que o próprio pai/mãe**, ou nascida **antes** do casamento
  dos pais por margem implausível.

**Conduta:** marque, **não corrija no escuro**. Volte ao assento original (a `SOUR`
ou a imagem) e confira que tipo de data era. Lembre que a **idade no óbito é
notoriamente imprecisa** ([`04-tipos-de-registo.md`](04-tipos-de-registo.md), §3) —
não a use para reconstituir a data de nascimento.

### 2.2 Mojibake / encoding partido

Texto com `Ã§`, `Ã£`, `Ã©`, `Ã¡`, `Â`, etc., no lugar de `ç`, `ã`, `é`, `á`. É o
clássico **UTF-8 lido como latin-1** (ou cp1252). Atrapalha a busca por nome e
corrompe lugares.

**Fix canónico** (re-decodificar): o texto correto sai de
`bytes_errados.encode("latin-1").decode("utf-8")`. Em Python, dada uma string já
lida erradamente:

```python
def fix_mojibake(s: str) -> str:
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s  # já estava ok, ou padrão diferente — não force
```

Melhor ainda: **abra o ficheiro no encoding certo de início**. Tente `utf-8`,
depois `utf-8-sig` (BOM), depois `latin-1`/`cp1252`, e veja qual produz menos
sequências suspeitas (`Ã`, `Â`, ` Â`). O `gedcom_audit.py` faz essa deteção.

> Atenção: re-decodificar um texto que **já está correto** estraga-o. Aplique o fix
> só onde detetar o padrão mojibake, nunca em bloco e às cegas.

### 2.3 Nós-lixo (lembretes digitados como pessoa)

Pessoas que não são pessoas: notas que alguém digitou no campo do nome, como
`"VER LIVRO 2"`, `"???"`, `"a confirmar"`, `"duplicado?"`, `"Living"` (placeholder
de pessoa viva), nomes só com pontuação, ou um `INDI` **sem nenhum** `NAME`,
`BIRT`, `DEAT` nem ligação a família. São ruído que infla a contagem e polui a
lista de muros.

**Sintomas:** `NAME` que casa com padrões de lembrete (interrogação, "ver",
"confirmar", "??", maiúsculas tipo grito); `INDI` órfão de tudo (sem `FAMC`,
sem `FAMS`, sem datas).

**Conduta:** sinalizar para revisão humana. Não apague automaticamente — pode ser
uma pessoa real mal preenchida.

### 2.4 Duplicados e loops

- **Duplicados:** a mesma pessoa entra duas vezes (mesmo nome + mesma data de
  nascimento + mesmo lugar) com identificadores diferentes — comum quando se
  importa de mais de uma fonte. Inflam a árvore e quebram a contagem de gerações.
- **Loops de ascendência:** alguém acaba por ser **seu próprio antepassado** —
  `FAMC`/`CHIL` formam um ciclo (A é filho de B que é filho de A). Em geral é fruto
  de ligação errada (apontou o identificador trocado). Um percurso ingénuo da
  árvore que não detete o ciclo entra em **recursão infinita**.

**Conduta:** o auditor agrupa duplicados candidatos (mesma assinatura nome+data) e
deteta ciclos percorrendo a ascendência com um conjunto de "visitados".

### 2.5 Nomes / lugares vazios

`INDI` sem `NAME`, ou com `NAME` vazio/`//`; eventos com `DATE` mas **sem `PLAC`**
(ou ao contrário). Lugar vazio é especialmente custoso porque a **naturalidade é o
que diz em que paróquia procurar** a geração seguinte
([`04-tipos-de-registo.md`](04-tipos-de-registo.md)). Cada lugar em falta num muro é
um item de pesquisa.

### 2.6 Datas mal formadas / impossíveis

`DATE` que não casa o padrão GEDCOM (`DD MMM YYYY`, com mês em inglês de 3 letras:
`JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC`), anos no futuro, dias `> 31`,
meses inválidos, ou qualificadores (`ABT`, `BEF`, `AFT`, `EST`, `CAL`, `BET ... AND
...`) que o seu parser não trate. Normalize antes de comparar datas, e preserve o
qualificador (uma data `ABT 1820` **não** é igual a `1820` exata).

---

## 3. `scripts/gedcom_audit.py` — o auditor

O ficheiro [`scripts/gedcom_audit.py`](../scripts/gedcom_audit.py) acompanha esta
skill. É um parser/auditor **sem dependências externas** (só a biblioteca-padrão do
Python) que lê um `.ged` e reporta os defeitos do §2, **sem alterar o ficheiro**
(auditoria é só leitura; correção é decisão humana).

### Uso

```bash
# relatório legível no terminal
python scripts/gedcom_audit.py caminho/para/arvore.ged

# saída em JSON (para um agente consumir)
python scripts/gedcom_audit.py caminho/para/arvore.ged --json

# listar especificamente os muros (sem pais conhecidos), com lugar de nascimento
python scripts/gedcom_audit.py caminho/para/arvore.ged --walls
```

### O que reporta

- **Resumo:** total de `INDI`, total de `FAM`, encoding detetado.
- **Muros:** indivíduos sem `FAMC` válida (sem pais conhecidos) → **a lista de
  trabalho** da pesquisa documental. Para cada um, nome + data/lugar de nascimento
  (e marca se o lugar está em falta).
- **Datas impossíveis:** nascimento depois do óbito; idade ao morrer negativa ou
  > 115; filho mais velho que o pai/mãe.
- **Mojibake:** registos cujo texto exibe o padrão `Ã`/`Â` + sugestão de leitura
  corrigida.
- **Nós-lixo candidatos:** nomes-lembrete e `INDI` órfãos de tudo.
- **Duplicados candidatos:** grupos com a mesma assinatura nome+data de nascimento.
- **Loops:** ciclos de ascendência detetados.
- **Vazios:** indivíduos sem nome; eventos com data e sem lugar.

Cada achado vem com o **identificador** (`@I..@`/`@F..@`) e a **linha**, para você
voltar ao ficheiro e decidir. O script **nunca corrige sozinho** — apenas aponta.

### Disciplina

- A correção de uma data trocada ou de uma ligação errada exige **voltar ao assento
  original** (a `SOUR`/imagem), não adivinhar.
- Mojibake pode ser corrigido em lote **com cuidado** (só onde o padrão aparece);
  tudo o resto é revisão caso a caso.
- Os muros sem lugar de nascimento são prioridade dupla: primeiro descobrir a
  **naturalidade** (de um casamento/óbito), depois ir à paróquia certa.

---

## 4. Receita rápida

1. Use o GEDCOM disponibilizado ou uma exportação autorizada por fluxo seguro; ver §5 de `02-familysearch.md`.
2. **Audite**: `python scripts/gedcom_audit.py arvore.ged` — leia o relatório.
3. **Limpe o óbvio**: corrija mojibake (com cuidado), remova/sinalize nós-lixo,
   funda duplicados, desfaça loops. Sempre voltando à fonte para datas/ligações.
4. **Tire a lista de muros** (`--walls`): cada pessoa sem pais conhecidos é um alvo.
5. Para cada muro, planeie o assento que **nomeia os pais** dela (casamento de
   preferência — ver [`04-tipos-de-registo.md`](04-tipos-de-registo.md)) e vá aos
   arquivos (Torre do Tombo/DigitArq, FamilySearch, AHU, distritais).
6. À medida que documenta, **acrescente** as gerações novas com `SOUR` (cota +
   fólio). Marque `[?]` em leitura incerta; nunca apresente homónimo como prova.
7. O `.ged` é dado pessoal — **não** versione em repositório público.
