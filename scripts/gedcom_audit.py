#!/usr/bin/env python3
"""gedcom_audit.py - auditor de ficheiros GEDCOM (.ged) para a skill de genealogia.

So-leitura: NUNCA altera o ficheiro de entrada. Reporta os defeitos tipicos de
extracao automatica (ver references/07-gedcom.md) para que um humano decida a
correcao. Sem dependencias externas: usa apenas a biblioteca-padrao do Python 3.

Defeitos cacados:
  - ligacoes assimetricas: FAM.CHIL sem FAMC reciproco e vice-versa, ponteiros
    para registos inexistentes, XREF duplicado
  - muros: individuos sem pais conhecidos -> lista de trabalho
  - datas impossiveis: nascimento depois do obito; idade ao morrer negativa ou > 115;
    filho nascido cedo demais ou tarde demais em relacao ao pai/mae
  - BIRT que parece ser obito: nascimento POSTERIOR ao(s) filho(s) ou
    suspeitosamente proximo do obito -> tipico de data de obito lancada no campo BIRT
  - mojibake / encoding partido (padrao 'A~'/'A^' do UTF-8 lido como latin-1)
  - nos-lixo: nomes-lembrete ('ver livro 2', '??', etc.) e INDI orfaos de tudo
  - duplicados candidatos: mesma assinatura nome + data de nascimento
  - loops de ascendencia (alguem e seu proprio antepassado)
  - vazios: individuos sem nome; eventos com data e sem lugar

--- COMO ESTE AUDITOR TRATA A FILIACAO --------------------------------------
No GEDCOM 5.5.1 a filiacao aparece dos DOIS lados: `INDI.FAMC` aponta para a
familia onde a pessoa e filho, e `FAM.CHIL` aponta de volta para o filho. Os
dois deviam concordar; em ficheiros de extracao automatica muitas vezes nao
concordam.

A versao anterior deste auditor lia um lado para uns testes e o outro lado para
outros, e por isso conseguia, no MESMO relatorio, listar alguem como "sem pais
conhecidos" e ao mesmo tempo acusar que essa pessoa "nasceu antes do pai".

Aqui a regra e explicita:
  1. Toda ligacao de filiacao, venha de FAMC ou de CHIL, entra num mapa unico,
     COM a origem registada.
  2. Toda assimetria entra em `link_inconsistencies`. Reconciliar nao apaga o
     defeito: o ficheiro continua partido e o utilizador precisa de saber.
  3. `FAMC` pode trazer `PEDI` (birth/adopted/foster/sealing) e `STAT`
     (challenged/disproven/proven). Ligacao com `STAT disproven` NAO conta como
     ascendencia: o proprio ficheiro diz que ela foi refutada. Ligacao nao
     biologica (adopted/foster/sealing) conta para "tem pais", mas fica de fora
     dos testes de plausibilidade BIOLOGICA de idade.
Sem isso, "reconciliar" viraria inventar ascendencia que o ficheiro nega.

NB: este ficheiro evita acentos no codigo-fonte de proposito (placeholders/comentarios
ASCII); os dados do GEDCOM, esses, sao tratados no encoding correto.

Uso:
    python scripts/gedcom_audit.py arvore.ged
    python scripts/gedcom_audit.py arvore.ged --json
    python scripts/gedcom_audit.py arvore.ged --walls
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

# --------------------------------------------------------------------------- #
# Leitura do ficheiro com deteccao de encoding                                 #
# --------------------------------------------------------------------------- #

# Sequencias tipicas de mojibake (UTF-8 lido como latin-1/cp1252).
MOJIBAKE_RE = re.compile(r"[ÃÂ][\x80-¿]")


class GedcomError(Exception):
    """Ficheiro ilegivel ou que nao parece ser um GEDCOM."""


def _mojibake_score(text: str) -> int:
    """Quantas sequencias suspeitas de mojibake o texto contem."""
    return len(MOJIBAKE_RE.findall(text))


def read_gedcom(path: str) -> tuple[str, str]:
    """Le o ficheiro escolhendo o encoding que produz menos mojibake.

    Retorna (texto, encoding_usado). Tenta utf-16 (por BOM), utf-8-sig, utf-8,
    cp1252, latin-1. O latin-1 nunca falha, e por isso e o ultimo recurso: sem
    tentar os outros primeiro, um ficheiro UTF-16 seria lido como lixo e o
    parser devolveria zero individuos sem dizer porque.
    """
    with open(path, "rb") as fh:
        raw = fh.read()

    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return raw.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            pass

    candidates = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    best_text: Optional[str] = None
    best_enc = "latin-1"
    best_score = None
    for enc in candidates:
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        score = _mojibake_score(text)
        if best_score is None or score < best_score:
            best_text, best_enc, best_score = text, enc, score
            if score == 0 and enc in ("utf-8-sig", "utf-8"):
                break  # utf-8 limpo: e o que queremos
    if best_text is None:  # ultimo recurso: latin-1 nunca falha
        best_text, best_enc = raw.decode("latin-1"), "latin-1"
    return best_text, best_enc


def fix_mojibake(s: str) -> str:
    """Re-decodifica latin-1 -> utf-8 SO se o padrao mojibake estiver presente."""
    if not MOJIBAKE_RE.search(s):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


# --------------------------------------------------------------------------- #
# Parsing GEDCOM                                                               #
# --------------------------------------------------------------------------- #

LINE_RE = re.compile(r"^\s*(\d+)\s+(@[^@]+@\s+)?(\S+)(?:\s(.*))?$")

MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
# Qualificadores que tornam a data APROXIMADA ou um intervalo. Uma data assim
# nao pode sustentar acusacao de impossibilidade: "BEF 1900" contra um obito em
# 1890 e perfeitamente coerente (nasceu antes de 1900, e antes de 1890).
APPROX_QUALIFIERS = ("ABT", "ABOUT", "BEF", "BEFORE", "AFT", "AFTER", "EST",
                     "CAL", "FROM", "TO", "BET", "AND", "INT")
QUALIFIER_RE = re.compile(r"\b(%s)\b" % "|".join(APPROX_QUALIFIERS), re.IGNORECASE)
YEAR_RE = re.compile(r"\b(\d{3,4})\b")

# Campos de nivel 1 do INDI que aceitam continuacao por CONC/CONT.
CONTINUABLE = ("NAME", "PLAC", "NOTE", "TITL", "OCCU", "SOUR", "TEXT")

NON_BIOLOGICAL_PEDI = ("adopted", "foster", "sealing")


@dataclass
class GedLine:
    level: int
    tag: str
    xref: Optional[str]
    value: str
    lineno: int


@dataclass
class ChildLink:
    """Uma ligacao 'esta pessoa e filho desta familia', com a sua procedencia."""
    fam: str
    origem: str = "FAMC"          # FAMC | CHIL | ambos
    pedi: str = ""                # birth | adopted | foster | sealing | ""
    stat: str = ""                # challenged | disproven | proven | ""
    lineno: int = 0

    @property
    def conta_como_ascendencia(self) -> bool:
        return self.stat.lower() != "disproven"

    @property
    def e_biologica(self) -> bool:
        return self.pedi.lower() not in NON_BIOLOGICAL_PEDI


@dataclass
class Indi:
    xref: str
    lineno: int
    name: str = ""
    sex: str = ""
    birt_date: str = ""
    birt_place: str = ""
    birt_lineno: int = 0
    deat_date: str = ""
    deat_place: str = ""
    deat_lineno: int = 0
    famc: list = field(default_factory=list)   # list[ChildLink] declarados no INDI
    fams: list = field(default_factory=list)   # familias onde e CONJUGE


@dataclass
class Fam:
    xref: str
    lineno: int
    husb: Optional[str] = None
    wife: Optional[str] = None
    chil: list = field(default_factory=list)
    marr_date: str = ""
    marr_place: str = ""


def parse_lines(text: str) -> list:
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        m = LINE_RE.match(raw)
        if not m:
            continue  # linha que nao casa o formato: ignora (nao e fatal)
        level = int(m.group(1))
        xref = m.group(2).strip() if m.group(2) else None
        tag = m.group(3).upper()
        value = (m.group(4) or "").rstrip()
        out.append(GedLine(level, tag, xref, value, i))
    return out


def parse(text: str) -> tuple:
    """Constroi os dicionarios de INDI e FAM, mais a lista de XREF duplicados.

    Junta CONC/CONT: sem isso um nome ou lugar longo, partido em varias linhas
    pelo exportador, ficava truncado em silencio no primeiro pedaco.
    """
    lines = parse_lines(text)
    indis: dict = {}
    fams: dict = {}
    duplicados: list = []

    cur_indi: Optional[Indi] = None
    cur_fam: Optional[Fam] = None
    cur_event = ""
    cur_famc: Optional[ChildLink] = None
    # Para onde uma linha CONC/CONT deve escrever: (objeto, atributo).
    cont_alvo = None

    for ln in lines:
        if ln.level == 0:
            cur_indi = cur_fam = None
            cur_event = ""
            cur_famc = None
            cont_alvo = None
            if ln.tag == "INDI" and ln.xref:
                if ln.xref in indis:
                    duplicados.append({"xref": ln.xref, "tipo": "INDI",
                                       "line": ln.lineno,
                                       "line_anterior": indis[ln.xref].lineno})
                cur_indi = Indi(xref=ln.xref, lineno=ln.lineno)
                indis[ln.xref] = cur_indi
            elif ln.tag == "FAM" and ln.xref:
                if ln.xref in fams:
                    duplicados.append({"xref": ln.xref, "tipo": "FAM",
                                       "line": ln.lineno,
                                       "line_anterior": fams[ln.xref].lineno})
                cur_fam = Fam(xref=ln.xref, lineno=ln.lineno)
                fams[ln.xref] = cur_fam
            continue

        # Continuacao de valor longo. So se aplica ao campo imediatamente
        # anterior; qualquer outra tag limpa o alvo (evita colar uma NOTE no
        # fim do NAME anterior).
        if ln.tag in ("CONC", "CONT") and cont_alvo is not None:
            obj, attr = cont_alvo
            sep = "\n" if ln.tag == "CONT" else ""
            setattr(obj, attr, getattr(obj, attr) + sep + ln.value)
            continue

        if cur_indi is not None:
            if ln.level == 1:
                cur_event = ln.tag
                cur_famc = None
                cont_alvo = None
                if ln.tag == "NAME":
                    cur_indi.name = ln.value
                    cont_alvo = (cur_indi, "name")
                elif ln.tag == "SEX":
                    cur_indi.sex = ln.value
                elif ln.tag == "FAMC" and ln.value:
                    cur_famc = ChildLink(fam=ln.value.strip(), origem="FAMC",
                                         lineno=ln.lineno)
                    cur_indi.famc.append(cur_famc)
                elif ln.tag == "FAMS" and ln.value:
                    cur_indi.fams.append(ln.value.strip())
                elif ln.tag in ("BIRT", "CHR", "BAPM"):
                    cur_indi.birt_lineno = cur_indi.birt_lineno or ln.lineno
                elif ln.tag == "DEAT":
                    cur_indi.deat_lineno = cur_indi.deat_lineno or ln.lineno
            elif ln.level >= 2:
                if cur_event == "FAMC" and cur_famc is not None:
                    if ln.tag == "PEDI":
                        cur_famc.pedi = ln.value.strip()
                    elif ln.tag == "STAT":
                        cur_famc.stat = ln.value.strip()
                    cont_alvo = None
                elif cur_event in ("BIRT", "CHR", "BAPM"):
                    # So o nivel 2 do evento interessa: DATE dentro de SOUR/DATA
                    # (nivel 3+) e a data da FONTE, nao a do nascimento.
                    if ln.level == 2 and ln.tag == "DATE" and not cur_indi.birt_date:
                        cur_indi.birt_date = ln.value
                        cont_alvo = None
                    elif ln.level == 2 and ln.tag == "PLAC" and not cur_indi.birt_place:
                        cur_indi.birt_place = ln.value
                        cont_alvo = (cur_indi, "birt_place")
                    else:
                        cont_alvo = None
                elif cur_event == "DEAT":
                    if ln.level == 2 and ln.tag == "DATE" and not cur_indi.deat_date:
                        cur_indi.deat_date = ln.value
                        cont_alvo = None
                    elif ln.level == 2 and ln.tag == "PLAC" and not cur_indi.deat_place:
                        cur_indi.deat_place = ln.value
                        cont_alvo = (cur_indi, "deat_place")
                    else:
                        cont_alvo = None
                else:
                    cont_alvo = None
            continue

        if cur_fam is not None:
            cont_alvo = None
            if ln.level == 1:
                cur_event = ln.tag
                if ln.tag == "HUSB" and ln.value:
                    cur_fam.husb = ln.value.strip()
                elif ln.tag == "WIFE" and ln.value:
                    cur_fam.wife = ln.value.strip()
                elif ln.tag == "CHIL" and ln.value:
                    cur_fam.chil.append((ln.value.strip(), ln.lineno))
            elif ln.level == 2 and cur_event == "MARR":
                if ln.tag == "DATE" and not cur_fam.marr_date:
                    cur_fam.marr_date = ln.value
                elif ln.tag == "PLAC" and not cur_fam.marr_place:
                    cur_fam.marr_place = ln.value
            continue

    return indis, fams, duplicados


# --------------------------------------------------------------------------- #
# Utilidades de data e nome                                                     #
# --------------------------------------------------------------------------- #

def parse_year(date_value: str) -> Optional[int]:
    """Extrai o ano (int) de uma DATE GEDCOM, tolerando qualificadores."""
    if not date_value:
        return None
    m = YEAR_RE.search(date_value)
    return int(m.group(1)) if m else None


def date_is_approximate(date_value: str) -> bool:
    """True quando a data traz ABT/BEF/AFT/EST/CAL/BET..AND ou similar.

    Uma data aproximada nao serve para acusar impossibilidade: e um intervalo
    disfarçado de ano. So serve para levantar suspeita.
    """
    return bool(date_value) and bool(QUALIFIER_RE.search(date_value))


def clean_name(name: str) -> str:
    """Remove as barras do apelido GEDCOM e normaliza espacos."""
    return re.sub(r"\s+", " ", name.replace("/", " ")).strip()


# Nomes que sao o proprio lembrete, e nao uma pessoa.
# Dois niveis de propositio:
#   JUNK_WHOLE_RE so casa quando e o nome INTEIRO ("teste", "n/a", "living");
#   JUNK_ANY_RE casa lembretes com contexto ("ver livro 2", "a confirmar").
# Por que estreitar: a versao anterior tinha `\btest[ae]\b`, `\bver\b` e
# `\bvide\b` soltos, e marcava como lixo os apelidos REAIS portugueses "Testa"
# e "Vide". Falso positivo aqui e pior que falso negativo: um apelido marcado
# como lixo suja a lista de muros, que e a lista de trabalho do investigador;
# um lembrete que escapa custa uma linha a mais no relatorio.
# NB: o padrao roda DEPOIS de clean_name(), que troca as barras do apelido
# GEDCOM por espaco. Por isso "N/A" chega aqui como "N A", e o padrao tem de
# aceitar o separador ja convertido.
JUNK_WHOLE_RE = re.compile(
    r"^(?:\?+|x{3,}|n\s*[/\s]?\s*a|teste?|test|unknown|desconhecid[oa]s?|"
    r"sem\s+nome|living|vivo|viva|nn|n\.?\s*n\.?)$",
    re.IGNORECASE,
)
JUNK_ANY_RE = re.compile(
    r"(?:\?{2,}|\ba\s*confirmar\b|\bcorrigir\b|\bfixme\b|\btodo\b|"
    r"\bduplicad[oa]\b|\bver\s+(?:livro|liv\.?|fl\.?|folio|nota|pag|pagina)\b)",
    re.IGNORECASE,
)


def looks_like_junk_name(name: str) -> bool:
    n = clean_name(name)
    if not n:
        return False  # vazio e tratado a parte
    if JUNK_WHOLE_RE.match(n) or JUNK_ANY_RE.search(n):
        return True
    # Sem nenhuma letra (so pontuacao/numeros) tambem e lixo. Usa isalpha() em
    # vez de uma classe latina: a versao anterior exigia [A-Za-z...] e por isso
    # classificava como lixo qualquer nome chines, cirilico, arabe ou grego.
    if not any(ch.isalpha() for ch in n):
        return True
    return False


# --------------------------------------------------------------------------- #
# Reconciliacao das ligacoes de filiacao                                        #
# --------------------------------------------------------------------------- #

MAX_PLAUSIBLE_AGE = 115
MAX_PARENT_AGE = 70   # idade max plausivel de um pai/mae ao ter um filho
MIN_PARENT_AGE = 11   # idade min plausivel


def build_child_links(indis: dict, fams: dict, report: dict) -> dict:
    """Mapa xref -> list[ChildLink], unindo INDI.FAMC e FAM.CHIL.

    Cada assimetria vai para report["link_inconsistencies"]. Reconciliar sem
    reportar esconderia um defeito real do ficheiro; reportar sem reconciliar
    deixaria o auditor a contradizer-se de seccao para seccao.
    """
    inc = report["link_inconsistencies"]
    links: dict = {}
    for xref, ind in indis.items():
        links[xref] = []
        for cl in ind.famc:
            if cl.fam not in fams:
                inc.append({"tipo": "FAMC aponta para FAM inexistente",
                            "indi": xref, "fam": cl.fam, "line": cl.lineno})
                continue
            links[xref].append(cl)

    # CHIL -> FAMC
    for fam in fams.values():
        for filho, lineno in fam.chil:
            if filho not in indis:
                inc.append({"tipo": "CHIL aponta para INDI inexistente",
                            "fam": fam.xref, "indi": filho, "line": lineno})
                continue
            existente = next((c for c in links[filho] if c.fam == fam.xref), None)
            if existente is None:
                inc.append({"tipo": "FAM.CHIL sem FAMC reciproco no INDI",
                            "fam": fam.xref, "indi": filho, "line": lineno})
                links[filho].append(ChildLink(fam=fam.xref, origem="CHIL", lineno=lineno))
            else:
                existente.origem = "ambos"

    # FAMC -> CHIL
    for xref, cls in links.items():
        for cl in cls:
            if cl.origem == "FAMC":
                fam = fams.get(cl.fam)
                if fam is not None and not any(c == xref for c, _ in fam.chil):
                    inc.append({"tipo": "FAMC sem CHIL reciproco na FAM",
                                "indi": xref, "fam": cl.fam, "line": cl.lineno})

    # HUSB/WIFE sem FAMS reciproco
    for fam in fams.values():
        for papel, conjuge in (("HUSB", fam.husb), ("WIFE", fam.wife)):
            if not conjuge:
                continue
            if conjuge not in indis:
                inc.append({"tipo": "%s aponta para INDI inexistente" % papel,
                            "fam": fam.xref, "indi": conjuge, "line": fam.lineno})
            elif fam.xref not in indis[conjuge].fams:
                inc.append({"tipo": "%s sem FAMS reciproco no INDI" % papel,
                            "fam": fam.xref, "indi": conjuge, "line": fam.lineno})
    return links


def parents_of(xref: str, links: dict, fams: dict, so_biologicos: bool = False) -> list:
    """Pais de alguem, respeitando STAT disproven e, se pedido, so os biologicos."""
    out = []
    for cl in links.get(xref, []):
        if not cl.conta_como_ascendencia:
            continue
        if so_biologicos and not cl.e_biologica:
            continue
        fam = fams.get(cl.fam)
        if not fam:
            continue
        if fam.husb:
            out.append(fam.husb)
        if fam.wife:
            out.append(fam.wife)
    return out


# --------------------------------------------------------------------------- #
# Auditoria                                                                     #
# --------------------------------------------------------------------------- #

def audit(indis: dict, fams: dict, encoding: str, duplicados: list) -> dict:
    report: dict = {
        "summary": {
            "individuals": len(indis),
            "families": len(fams),
            "encoding": encoding,
        },
        "link_inconsistencies": [],
        "duplicate_xrefs": list(duplicados),
        "walls": [],
        "impossible_dates": [],
        "suspicious_dates": [],
        "birt_as_death": [],
        "mojibake": [],
        "junk_nodes": [],
        "duplicates": [],
        "ancestry_loops": [],
        "empty": {"no_name": [], "date_without_place": []},
    }

    links = build_child_links(indis, fams, report)

    # --- muros: ninguem aponta pais para esta pessoa ---
    for xref, ind in indis.items():
        tem_pais = False
        for cl in links.get(xref, []):
            if not cl.conta_como_ascendencia:
                continue
            fam = fams.get(cl.fam)
            if fam and (fam.husb or fam.wife):
                tem_pais = True
                break
        if not tem_pais:
            report["walls"].append({
                "id": xref,
                "name": clean_name(ind.name) or "(sem nome)",
                "birth_date": ind.birt_date,
                "birth_place": ind.birt_place,
                "place_missing": not bool(ind.birt_place),
                "line": ind.lineno,
            })

    def registar_data(destino_impossivel, item, aproximada):
        """Data aproximada vira suspeita, nao impossibilidade."""
        if aproximada:
            item = dict(item)
            item["issue"] += " (data aproximada: verificar, nao e prova)"
            report["suspicious_dates"].append(item)
        else:
            destino_impossivel.append(item)

    # --- datas impossiveis do proprio individuo ---
    for xref, ind in indis.items():
        by, dy = parse_year(ind.birt_date), parse_year(ind.deat_date)
        if by is None or dy is None:
            continue
        aprox = date_is_approximate(ind.birt_date) or date_is_approximate(ind.deat_date)
        if by > dy:
            registar_data(report["impossible_dates"], {
                "id": xref, "name": clean_name(ind.name),
                "issue": "nascimento depois do obito",
                "birth": ind.birt_date, "death": ind.deat_date,
                "line": ind.birt_lineno or ind.lineno}, aprox)
        else:
            idade = dy - by
            if idade < 0 or idade > MAX_PLAUSIBLE_AGE:
                registar_data(report["impossible_dates"], {
                    "id": xref, "name": clean_name(ind.name),
                    "issue": "idade ao morrer implausivel (%d anos)" % idade,
                    "birth": ind.birt_date, "death": ind.deat_date,
                    "line": ind.deat_lineno or ind.lineno}, aprox)

    # --- idade do pai/mae ao ter o filho (so ligacoes BIOLOGICAS) ---
    for filho, cls in links.items():
        child = indis.get(filho)
        if not child:
            continue
        cy = parse_year(child.birt_date)
        if cy is None:
            continue
        for cl in cls:
            if not cl.conta_como_ascendencia or not cl.e_biologica:
                continue
            fam = fams.get(cl.fam)
            if not fam:
                continue
            for pai_xref in (fam.husb, fam.wife):
                pai = indis.get(pai_xref) if pai_xref else None
                if not pai:
                    continue
                py = parse_year(pai.birt_date)
                if py is None:
                    continue
                gap = cy - py
                aprox = date_is_approximate(child.birt_date) or date_is_approximate(pai.birt_date)
                if gap < MIN_PARENT_AGE:
                    registar_data(report["impossible_dates"], {
                        "id": filho, "name": clean_name(child.name),
                        "issue": ("filho nasce %d ano(s) depois do pai/mae %s "
                                  "(minimo plausivel: %d)" % (gap, pai_xref, MIN_PARENT_AGE)),
                        "birth": child.birt_date, "parent_birth": pai.birt_date,
                        "line": child.birt_lineno or child.lineno}, aprox)
                elif gap > MAX_PARENT_AGE:
                    registar_data(report["impossible_dates"], {
                        "id": filho, "name": clean_name(child.name),
                        "issue": ("pai/mae %s teria %d anos ao nascer este filho "
                                  "(maximo plausivel: %d)" % (pai_xref, gap, MAX_PARENT_AGE)),
                        "birth": child.birt_date, "parent_birth": pai.birt_date,
                        "line": child.birt_lineno or child.lineno}, aprox)

    # --- BIRT que parece ser uma data de OBITO ---
    filho_mais_velho: dict = {}
    for filho, cls in links.items():
        child = indis.get(filho)
        cy = parse_year(child.birt_date) if child else None
        if cy is None:
            continue
        for cl in cls:
            # So filiacao BIOLOGICA: um pai adotivo pode legitimamente ser mais
            # novo que o filho, e isso nao e indicio de data trocada.
            if not cl.conta_como_ascendencia or not cl.e_biologica:
                continue
            fam = fams.get(cl.fam)
            if not fam:
                continue
            for pai_xref in (fam.husb, fam.wife):
                if pai_xref and pai_xref in indis:
                    anterior = filho_mais_velho.get(pai_xref)
                    filho_mais_velho[pai_xref] = cy if anterior is None else min(anterior, cy)

    for xref, ind in indis.items():
        by = parse_year(ind.birt_date)
        if by is None:
            continue
        razoes = []
        ecy = filho_mais_velho.get(xref)
        if ecy is not None and by > ecy + MIN_PARENT_AGE:
            razoes.append("BIRT (%d) posterior ao filho mais velho (%d); a data parece ser de obito"
                          % (by, ecy))
        dy = parse_year(ind.deat_date)
        if dy is not None and by > dy:
            razoes.append("BIRT (%d) > DEAT (%d); campos possivelmente trocados" % (by, dy))
        if razoes:
            report["birt_as_death"].append({
                "id": xref, "name": clean_name(ind.name),
                "birth": ind.birt_date, "death": ind.deat_date,
                "earliest_child_birth": ecy, "reasons": razoes,
                "line": ind.birt_lineno or ind.lineno})

    # --- mojibake ---
    for xref, ind in indis.items():
        for label, val in (("name", ind.name), ("birth_place", ind.birt_place),
                           ("death_place", ind.deat_place)):
            if val and MOJIBAKE_RE.search(val):
                report["mojibake"].append({
                    "id": xref, "field": label, "raw": val,
                    "suggested": fix_mojibake(val), "line": ind.lineno})

    # --- nos-lixo ---
    for xref, ind in indis.items():
        if looks_like_junk_name(ind.name):
            report["junk_nodes"].append({
                "id": xref, "name": ind.name,
                "reason": "nome parece lembrete/lixo", "line": ind.lineno})
            continue
        orfao = (not clean_name(ind.name) and not ind.birt_date and not ind.deat_date
                 and not links.get(xref) and not ind.fams)
        if orfao:
            report["junk_nodes"].append({
                "id": xref, "name": ind.name,
                "reason": "INDI orfao (sem nome/datas/familia)", "line": ind.lineno})

    # --- duplicados candidatos (assinatura nome + ano de nascimento) ---
    sig_map: dict = {}
    for xref, ind in indis.items():
        nome = clean_name(fix_mojibake(ind.name)).lower()
        ano = parse_year(ind.birt_date)
        if not nome or ano is None:
            continue
        sig_map.setdefault((nome, ano), []).append(xref)
    for (nome, ano), ids in sig_map.items():
        if len(ids) > 1:
            report["duplicates"].append({"name": nome, "birth_year": ano, "ids": ids})

    # --- loops de ascendencia (DFS iterativa de tres cores, O(V+E)) ---
    # A versao anterior partia de CADA individuo copiando a lista de caminho, o
    # que era quadratico e ainda incluia no "ciclo" descendentes que so levavam
    # ate ele (D -> A -> B -> A reportava D como parte do ciclo).
    BRANCO, CINZENTO, PRETO = 0, 1, 2
    cor = {x: BRANCO for x in indis}
    ciclos_vistos = set()
    for inicio in indis:
        if cor[inicio] != BRANCO:
            continue
        pilha = [(inicio, iter(parents_of(inicio, links, fams)))]
        caminho = [inicio]
        cor[inicio] = CINZENTO
        while pilha:
            no, it = pilha[-1]
            avancou = False
            for p in it:
                if p not in cor:
                    continue
                if cor[p] == CINZENTO:
                    # Ciclo: so os nos entre a ocorrencia anterior de p e o topo.
                    i = caminho.index(p)
                    ciclo = caminho[i:] + [p]
                    chave = frozenset(ciclo)
                    if chave not in ciclos_vistos:
                        ciclos_vistos.add(chave)
                        report["ancestry_loops"].append({
                            "cycle": ciclo,
                            "note": "ancestral aponta de volta (ligacao errada?)"})
                elif cor[p] == BRANCO:
                    cor[p] = CINZENTO
                    caminho.append(p)
                    pilha.append((p, iter(parents_of(p, links, fams))))
                    avancou = True
                    break
            if not avancou:
                cor[no] = PRETO
                pilha.pop()
                caminho.pop()

    # --- vazios ---
    for xref, ind in indis.items():
        if not clean_name(ind.name):
            report["empty"]["no_name"].append({"id": xref, "line": ind.lineno})
        if ind.birt_date and not ind.birt_place:
            report["empty"]["date_without_place"].append({
                "id": xref, "event": "BIRT", "date": ind.birt_date,
                "line": ind.birt_lineno or ind.lineno})
        if ind.deat_date and not ind.deat_place:
            report["empty"]["date_without_place"].append({
                "id": xref, "event": "DEAT", "date": ind.deat_date,
                "line": ind.deat_lineno or ind.lineno})

    return report


# --------------------------------------------------------------------------- #
# Apresentacao                                                                  #
# --------------------------------------------------------------------------- #

def print_human(report: dict, walls_only: bool = False) -> None:
    s = report["summary"]
    if walls_only:
        print("# Muros (sem pais conhecidos): %d" % len(report["walls"]))
        for w in report["walls"]:
            place = w["birth_place"] or ("(LUGAR EM FALTA)" if w["place_missing"] else "")
            print("  %-10s %-40s n. %s  %s"
                  % (w["id"], w["name"], w["birth_date"] or "s/d", place))
        return

    print("=" * 64)
    print("AUDITORIA GEDCOM")
    print("=" * 64)
    print("  Individuos (INDI): %d" % s["individuals"])
    print("  Familias  (FAM):   %d" % s["families"])
    print("  Encoding detetado: %s" % s["encoding"])
    print()

    def section(title, items, fmt):
        print("--- %s: %d ---" % (title, len(items)))
        for it in items[:200]:
            print("  " + fmt(it))
        if len(items) > 200:
            print("  ... (+%d mais; use --json para tudo)" % (len(items) - 200))
        print()

    section("XREF DUPLICADO (o segundo registo sobrepoe o primeiro)",
            report["duplicate_xrefs"],
            lambda d: "%s %s definido na linha %s e outra vez na linha %s"
                      % (d["tipo"], d["xref"], d["line_anterior"], d["line"]))
    section("LIGACOES ASSIMETRICAS (FAMC x CHIL, HUSB/WIFE x FAMS)",
            report["link_inconsistencies"],
            lambda i: "%-38s indi=%-10s fam=%-10s (linha %s)"
                      % (i["tipo"], i.get("indi", "-"), i.get("fam", "-"), i.get("line", "?")))
    section("MUROS (sem pais conhecidos = alvos de pesquisa)", report["walls"],
            lambda w: "%-10s %-36s n. %s %s"
                      % (w["id"], w["name"], w["birth_date"] or "s/d",
                         w["birth_place"] or ("[LUGAR EM FALTA]" if w["place_missing"] else "")))
    section("DATAS IMPOSSIVEIS", report["impossible_dates"],
            lambda d: "%-10s %-30s %s (linha %s)"
                      % (d["id"], d.get("name", "")[:30], d["issue"], d["line"]))
    section("DATAS SUSPEITAS (o mesmo teste, mas sobre data APROXIMADA)",
            report["suspicious_dates"],
            lambda d: "%-10s %-30s %s (linha %s)"
                      % (d["id"], d.get("name", "")[:30], d["issue"], d["line"]))
    section("BIRT QUE PARECE OBITO (data de obito lancada no nascimento?)",
            report["birt_as_death"],
            lambda b: "%-10s %-30s %s (linha %s)"
                      % (b["id"], b.get("name", "")[:30], "; ".join(b["reasons"]), b["line"]))
    section("MOJIBAKE (encoding partido)", report["mojibake"],
            lambda m: "%-10s %-12s %r -> %r" % (m["id"], m["field"], m["raw"], m["suggested"]))
    section("NOS-LIXO (rever)", report["junk_nodes"],
            lambda j: "%-10s %-40s %r (linha %s)" % (j["id"], j["reason"], j["name"], j["line"]))
    section("DUPLICADOS CANDIDATOS", report["duplicates"],
            lambda d: "%s (%s): %s" % (d["name"], d["birth_year"], ", ".join(d["ids"])))
    section("LOOPS DE ASCENDENCIA", report["ancestry_loops"],
            lambda c: " -> ".join(c["cycle"]))
    section("INDIVIDUOS SEM NOME", report["empty"]["no_name"],
            lambda e: "%s (linha %s)" % (e["id"], e["line"]))
    section("EVENTOS COM DATA E SEM LUGAR", report["empty"]["date_without_place"],
            lambda e: "%-10s %s %s (linha %s)" % (e["id"], e["event"], e["date"], e["line"]))

    print("Nota: este auditor NAO corrige nada. Volte ao assento original")
    print("(SOUR/imagem) para decidir cada correcao. Ver references/07-gedcom.md.")


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover
            pass

    ap = argparse.ArgumentParser(
        description="Audita um ficheiro GEDCOM (.ged). So-leitura.")
    ap.add_argument("gedcom", help="caminho para o ficheiro .ged")
    ap.add_argument("--json", action="store_true", help="saida em JSON")
    ap.add_argument("--walls", action="store_true",
                    help="listar so os muros (sem pais conhecidos)")
    args = ap.parse_args(argv)

    try:
        text, encoding = read_gedcom(args.gedcom)
    except OSError as e:
        sys.stderr.write("erro a abrir %r: %s\n" % (args.gedcom, e))
        return 2

    indis, fams, duplicados = parse(text)
    if not indis and not fams:
        sys.stderr.write(
            "erro: nenhum registo INDI ou FAM encontrado em %r (encoding lido: %s).\n"
            "      O ficheiro pode nao ser um GEDCOM, estar noutro encoding, ou estar\n"
            "      truncado. Um relatorio vazio aqui seria enganador, por isso e erro.\n"
            % (args.gedcom, encoding))
        return 2

    report = audit(indis, fams, encoding, duplicados)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report, walls_only=args.walls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
