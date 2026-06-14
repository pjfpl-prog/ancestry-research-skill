#!/usr/bin/env python3
"""gedcom_audit.py - auditor de ficheiros GEDCOM (.ged) para a skill de genealogia.

So-leitura: NUNCA altera o ficheiro de entrada. Reporta os defeitos tipicos de
extracao automatica (ver references/07-gedcom.md) para que um humano decida a
correcao. Sem dependencias externas: usa apenas a biblioteca-padrao do Python 3.

Defeitos cacados:
  - muros: individuos sem pais conhecidos (sem FAMC valida) -> lista de trabalho
  - datas impossiveis: nascimento depois do obito; idade ao morrer negativa ou > 115;
    filho mais velho que o pai/mae
  - BIRT que parece ser obito: nascimento POSTERIOR ao(s) filho(s) ou
    suspeitosamente proximo do obito -> tipico de data de obito lancada no campo BIRT
  - mojibake / encoding partido (padrao 'A~'/'A^' do UTF-8 lido como latin-1)
  - nos-lixo: nomes-lembrete ('ver ...', '??', etc.) e INDI orfaos de tudo
  - duplicados candidatos: mesma assinatura nome + data de nascimento
  - loops de ascendencia (alguem e seu proprio antepassado)
  - vazios: individuos sem nome; eventos com data e sem lugar

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
MOJIBAKE_RE = re.compile(r"[ÃÂ][-¿]")


def _mojibake_score(text: str) -> int:
    """Quantas sequencias suspeitas de mojibake o texto contem."""
    return len(MOJIBAKE_RE.findall(text))


def read_gedcom(path: str) -> tuple[str, str]:
    """Le o ficheiro escolhendo o encoding que produz menos mojibake.

    Retorna (texto, encoding_usado). Tenta utf-8-sig, utf-8, cp1252, latin-1.
    """
    raw = open(path, "rb").read()
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
DATE_QUALIFIERS = ("ABT", "BEF", "AFT", "EST", "CAL", "FROM", "TO", "BET", "AND")
YEAR_RE = re.compile(r"\b(\d{3,4})\b")
DAY_RE = re.compile(r"^\s*(\d{1,2})\b")
MONTH_RE = re.compile(r"\b([A-Z]{3})\b")


@dataclass
class GedLine:
    level: int
    tag: str
    xref: Optional[str]
    value: str
    lineno: int


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
    famc: list[str] = field(default_factory=list)  # familia onde e FILHO
    fams: list[str] = field(default_factory=list)  # familia onde e CONJUGE


@dataclass
class Fam:
    xref: str
    lineno: int
    husb: Optional[str] = None
    wife: Optional[str] = None
    chil: list[str] = field(default_factory=list)
    marr_date: str = ""
    marr_place: str = ""


def parse_lines(text: str) -> list[GedLine]:
    out: list[GedLine] = []
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


def parse(text: str) -> tuple[dict[str, Indi], dict[str, Fam]]:
    """Constroi os dicionarios de INDI e FAM a partir das linhas."""
    lines = parse_lines(text)
    indis: dict[str, Indi] = {}
    fams: dict[str, Fam] = {}

    cur_indi: Optional[Indi] = None
    cur_fam: Optional[Fam] = None
    # contexto do ultimo evento de nivel 1 dentro de INDI/FAM
    cur_event: str = ""

    for ln in lines:
        if ln.level == 0:
            cur_indi = cur_fam = None
            cur_event = ""
            if ln.tag == "INDI" and ln.xref:
                cur_indi = Indi(xref=ln.xref, lineno=ln.lineno)
                indis[ln.xref] = cur_indi
            elif ln.tag == "FAM" and ln.xref:
                cur_fam = Fam(xref=ln.xref, lineno=ln.lineno)
                fams[ln.xref] = cur_fam
            continue

        if cur_indi is not None:
            if ln.level == 1:
                cur_event = ln.tag
                if ln.tag == "NAME":
                    cur_indi.name = ln.value
                elif ln.tag == "SEX":
                    cur_indi.sex = ln.value
                elif ln.tag == "FAMC" and ln.value:
                    cur_indi.famc.append(ln.value.strip())
                elif ln.tag == "FAMS" and ln.value:
                    cur_indi.fams.append(ln.value.strip())
                elif ln.tag in ("BIRT", "CHR", "BAPM"):
                    cur_indi.birt_lineno = cur_indi.birt_lineno or ln.lineno
                elif ln.tag == "DEAT":
                    cur_indi.deat_lineno = cur_indi.deat_lineno or ln.lineno
            elif ln.level >= 2:
                if cur_event in ("BIRT", "CHR", "BAPM"):
                    if ln.tag == "DATE" and not cur_indi.birt_date:
                        cur_indi.birt_date = ln.value
                    elif ln.tag == "PLAC" and not cur_indi.birt_place:
                        cur_indi.birt_place = ln.value
                elif cur_event == "DEAT":
                    if ln.tag == "DATE" and not cur_indi.deat_date:
                        cur_indi.deat_date = ln.value
                    elif ln.tag == "PLAC" and not cur_indi.deat_place:
                        cur_indi.deat_place = ln.value
            continue

        if cur_fam is not None:
            if ln.level == 1:
                cur_event = ln.tag
                if ln.tag == "HUSB" and ln.value:
                    cur_fam.husb = ln.value.strip()
                elif ln.tag == "WIFE" and ln.value:
                    cur_fam.wife = ln.value.strip()
                elif ln.tag == "CHIL" and ln.value:
                    cur_fam.chil.append(ln.value.strip())
            elif ln.level >= 2 and cur_event == "MARR":
                if ln.tag == "DATE" and not cur_fam.marr_date:
                    cur_fam.marr_date = ln.value
                elif ln.tag == "PLAC" and not cur_fam.marr_place:
                    cur_fam.marr_place = ln.value
            continue

    return indis, fams


# --------------------------------------------------------------------------- #
# Utilidades de data e nome                                                     #
# --------------------------------------------------------------------------- #

def parse_year(date_value: str) -> Optional[int]:
    """Extrai o ano (int) de uma DATE GEDCOM, tolerando qualificadores."""
    if not date_value:
        return None
    m = YEAR_RE.search(date_value)
    return int(m.group(1)) if m else None


def parse_full_date(date_value: str) -> Optional[tuple[int, int, int]]:
    """(ano, mes, dia) quando completa; senao None. Para comparacao fina."""
    if not date_value:
        return None
    v = date_value.upper()
    for q in DATE_QUALIFIERS:
        v = re.sub(rf"\b{q}\b", " ", v)
    year = parse_year(v)
    if year is None:
        return None
    mon = 0
    mm = MONTH_RE.search(v)
    if mm and mm.group(1) in MONTHS:
        mon = MONTHS[mm.group(1)]
    day = 0
    dm = DAY_RE.search(v.strip())
    if dm:
        d = int(dm.group(1))
        if 1 <= d <= 31:
            day = d
    return (year, mon, day)


def clean_name(name: str) -> str:
    """Remove as barras do apelido GEDCOM e normaliza espacos."""
    return re.sub(r"\s+", " ", name.replace("/", " ")).strip()


# nomes que sao na verdade lembretes/lixo, nao pessoas
JUNK_NAME_RE = re.compile(
    r"(\?{2,}|^\s*\?+\s*$|\bver\b|\bvide\b|\bconfirm|\bcheck\b|"
    r"\bduplicad|\bdup\b|\bcorrigir\b|\bfixme\b|\btodo\b|\bunknown\b|"
    r"\bdesconhec|\bsem\s+nome\b|\bliving\b|\bn/?a\b|\bxxx+\b|\btest[ae]\b)",
    re.IGNORECASE,
)


def looks_like_junk_name(name: str) -> bool:
    n = clean_name(name)
    if not n:
        return False  # vazio e tratado a parte
    if JUNK_NAME_RE.search(n):
        return True
    # so pontuacao / sem letras
    if not re.search(r"[A-Za-zÀ-ɏ]", n):
        return True
    return False


# --------------------------------------------------------------------------- #
# Auditoria                                                                     #
# --------------------------------------------------------------------------- #

MAX_PLAUSIBLE_AGE = 115
MAX_PARENT_AGE = 70   # idade max plausivel de um pai/mae ao ter um filho
MIN_PARENT_AGE = 11   # idade min plausivel


def audit(indis: dict[str, Indi], fams: dict[str, Fam], encoding: str) -> dict:
    report: dict = {
        "summary": {
            "individuals": len(indis),
            "families": len(fams),
            "encoding": encoding,
        },
        "walls": [],
        "impossible_dates": [],
        "birt_as_death": [],
        "mojibake": [],
        "junk_nodes": [],
        "duplicates": [],
        "ancestry_loops": [],
        "empty": {"no_name": [], "date_without_place": []},
    }

    # --- muros: sem FAMC valida (sem pais conhecidos) ---
    for xref, ind in indis.items():
        has_parents = False
        for fc in ind.famc:
            fam = fams.get(fc)
            if fam and (fam.husb or fam.wife):
                has_parents = True
                break
        if not has_parents:
            report["walls"].append({
                "id": xref,
                "name": clean_name(ind.name) or "(sem nome)",
                "birth_date": ind.birt_date,
                "birth_place": ind.birt_place,
                "place_missing": not bool(ind.birt_place),
                "line": ind.lineno,
            })

    # --- datas impossiveis ---
    for xref, ind in indis.items():
        by = parse_year(ind.birt_date)
        dy = parse_year(ind.deat_date)
        if by is not None and dy is not None:
            if by > dy:
                report["impossible_dates"].append({
                    "id": xref, "name": clean_name(ind.name),
                    "issue": "nascimento depois do obito",
                    "birth": ind.birt_date, "death": ind.deat_date,
                    "line": ind.birt_lineno or ind.lineno,
                })
            else:
                age = dy - by
                if age < 0 or age > MAX_PLAUSIBLE_AGE:
                    report["impossible_dates"].append({
                        "id": xref, "name": clean_name(ind.name),
                        "issue": f"idade ao morrer implausivel ({age} anos)",
                        "birth": ind.birt_date, "death": ind.deat_date,
                        "line": ind.deat_lineno or ind.lineno,
                    })

    # filho mais velho que (ou implausivelmente proximo de) pai/mae
    for fam in fams.values():
        for parent_xref in (fam.husb, fam.wife):
            if not parent_xref:
                continue
            parent = indis.get(parent_xref)
            if not parent:
                continue
            py = parse_year(parent.birt_date)
            if py is None:
                continue
            for child_xref in fam.chil:
                child = indis.get(child_xref)
                if not child:
                    continue
                cy = parse_year(child.birt_date)
                if cy is None:
                    continue
                gap = cy - py
                if gap < MIN_PARENT_AGE:
                    report["impossible_dates"].append({
                        "id": child_xref, "name": clean_name(child.name),
                        "issue": (
                            f"filho nasce {gap} anos depois do pai/mae "
                            f"{parent_xref} (implausivel)"
                        ),
                        "birth": child.birt_date,
                        "parent_birth": parent.birt_date,
                        "line": child.birt_lineno or child.lineno,
                    })

    # --- BIRT que parece ser uma data de OBITO ---
    # Erro comum de digitacao/extracao: a data do obito acaba lancada no campo
    # BIRT. Sinais: (a) o "nascimento" do pai/mae e POSTERIOR ao do filho mais
    # velho; (b) o "nascimento" cai depois (ou quase em cima) do obito da
    # propria pessoa. Em ambos os casos o ano do BIRT costuma bater com um
    # obito real. So-sinalizar; o humano confirma no assento.
    earliest_child_year: dict[str, int] = {}
    for fam in fams.values():
        years = [
            parse_year(indis[c].birt_date)
            for c in fam.chil
            if c in indis and parse_year(indis[c].birt_date) is not None
        ]
        if not years:
            continue
        first = min(years)  # type: ignore[type-var]
        for parent_xref in (fam.husb, fam.wife):
            if parent_xref and parent_xref in indis:
                prev = earliest_child_year.get(parent_xref)
                earliest_child_year[parent_xref] = (
                    first if prev is None else min(prev, first)
                )

    flagged_birt_as_death: set[str] = set()
    for xref, ind in indis.items():
        by = parse_year(ind.birt_date)
        if by is None:
            continue
        reasons: list[str] = []
        # (a) nasce depois do proprio filho mais velho -> BIRT e provavel obito
        ecy = earliest_child_year.get(xref)
        if ecy is not None and by > ecy + MIN_PARENT_AGE:
            reasons.append(
                f"BIRT ({by}) posterior ao filho mais velho ({ecy}); "
                f"a data parece ser de obito"
            )
        # (b) nasce depois/quase em cima do proprio obito
        dy = parse_year(ind.deat_date)
        if dy is not None and by >= dy:
            reasons.append(
                f"BIRT ({by}) >= DEAT ({dy}); campos possivelmente trocados"
            )
        if reasons:
            flagged_birt_as_death.add(xref)
            report["birt_as_death"].append({
                "id": xref,
                "name": clean_name(ind.name),
                "birth": ind.birt_date,
                "death": ind.deat_date,
                "earliest_child_birth": ecy,
                "reasons": reasons,
                "line": ind.birt_lineno or ind.lineno,
            })

    # --- mojibake ---
    for xref, ind in indis.items():
        for label, val in (("name", ind.name),
                           ("birth_place", ind.birt_place),
                           ("death_place", ind.deat_place)):
            if val and MOJIBAKE_RE.search(val):
                report["mojibake"].append({
                    "id": xref, "field": label,
                    "raw": val, "suggested": fix_mojibake(val),
                    "line": ind.lineno,
                })

    # --- nos-lixo ---
    for xref, ind in indis.items():
        if looks_like_junk_name(ind.name):
            report["junk_nodes"].append({
                "id": xref, "name": ind.name,
                "reason": "nome parece lembrete/lixo", "line": ind.lineno,
            })
            continue
        orphan = (
            not clean_name(ind.name)
            and not ind.birt_date and not ind.deat_date
            and not ind.famc and not ind.fams
        )
        if orphan:
            report["junk_nodes"].append({
                "id": xref, "name": ind.name,
                "reason": "INDI orfao (sem nome/datas/familia)", "line": ind.lineno,
            })

    # --- duplicados candidatos (assinatura nome + ano de nascimento) ---
    sig_map: dict[tuple[str, Optional[int]], list[str]] = {}
    for xref, ind in indis.items():
        name = clean_name(fix_mojibake(ind.name)).lower()
        if not name:
            continue
        sig = (name, parse_year(ind.birt_date))
        if sig[1] is None:
            continue  # sem data, assinatura fraca demais: nao agrupa
        sig_map.setdefault(sig, []).append(xref)
    for (name, year), ids in sig_map.items():
        if len(ids) > 1:
            report["duplicates"].append({
                "name": name, "birth_year": year, "ids": ids,
            })

    # --- loops de ascendencia ---
    def parents_of(xref: str) -> list[str]:
        ind = indis.get(xref)
        if not ind:
            return []
        out: list[str] = []
        for fc in ind.famc:
            fam = fams.get(fc)
            if not fam:
                continue
            if fam.husb:
                out.append(fam.husb)
            if fam.wife:
                out.append(fam.wife)
        return out

    seen_loops: set[frozenset] = set()
    for start in indis:
        stack = [(start, [start])]
        visited_local: set[str] = set()
        while stack:
            node, path = stack.pop()
            for p in parents_of(node):
                if p == start or p in path:
                    cycle = frozenset(path + [p])
                    if cycle not in seen_loops:
                        seen_loops.add(cycle)
                        report["ancestry_loops"].append({
                            "cycle": path + [p],
                            "note": "ancestral aponta de volta (ligacao errada?)",
                        })
                elif p not in visited_local:
                    visited_local.add(p)
                    stack.append((p, path + [p]))

    # --- vazios ---
    for xref, ind in indis.items():
        if not clean_name(ind.name):
            report["empty"]["no_name"].append({"id": xref, "line": ind.lineno})
        if ind.birt_date and not ind.birt_place:
            report["empty"]["date_without_place"].append({
                "id": xref, "event": "BIRT", "date": ind.birt_date,
                "line": ind.birt_lineno or ind.lineno,
            })
        if ind.deat_date and not ind.deat_place:
            report["empty"]["date_without_place"].append({
                "id": xref, "event": "DEAT", "date": ind.deat_date,
                "line": ind.deat_lineno or ind.lineno,
            })

    return report


# --------------------------------------------------------------------------- #
# Apresentacao                                                                  #
# --------------------------------------------------------------------------- #

def print_human(report: dict, walls_only: bool = False) -> None:
    s = report["summary"]
    if walls_only:
        print(f"# Muros (sem pais conhecidos): {len(report['walls'])}")
        for w in report["walls"]:
            place = w["birth_place"] or ("(LUGAR EM FALTA)" if w["place_missing"] else "")
            date = w["birth_date"] or "s/d"
            print(f"  {w['id']:<10} {w['name']:<40} n. {date}  {place}")
        return

    print("=" * 64)
    print("AUDITORIA GEDCOM")
    print("=" * 64)
    print(f"  Individuos (INDI): {s['individuals']}")
    print(f"  Familias  (FAM):   {s['families']}")
    print(f"  Encoding detetado: {s['encoding']}")
    print()

    def section(title: str, items: list, fmt) -> None:
        print(f"--- {title}: {len(items)} ---")
        for it in items[:200]:
            print("  " + fmt(it))
        if len(items) > 200:
            print(f"  ... (+{len(items) - 200} mais; use --json para tudo)")
        print()

    section(
        "MUROS (sem pais conhecidos = alvos de pesquisa)",
        report["walls"],
        lambda w: (
            f"{w['id']:<10} {w['name']:<36} n. {w['birth_date'] or 's/d'} "
            f"{w['birth_place'] or ('[LUGAR EM FALTA]' if w['place_missing'] else '')}"
        ),
    )
    section(
        "DATAS IMPOSSIVEIS",
        report["impossible_dates"],
        lambda d: f"{d['id']:<10} {d.get('name','')[:30]:<30} {d['issue']} (linha {d['line']})",
    )
    section(
        "BIRT QUE PARECE OBITO (data de obito lancada no nascimento?)",
        report["birt_as_death"],
        lambda b: (
            f"{b['id']:<10} {b.get('name','')[:30]:<30} "
            f"{'; '.join(b['reasons'])} (linha {b['line']})"
        ),
    )
    section(
        "MOJIBAKE (encoding partido)",
        report["mojibake"],
        lambda m: f"{m['id']:<10} {m['field']:<12} {m['raw']!r} -> {m['suggested']!r}",
    )
    section(
        "NOS-LIXO (rever)",
        report["junk_nodes"],
        lambda j: f"{j['id']:<10} {j['reason']:<40} {j['name']!r} (linha {j['line']})",
    )
    section(
        "DUPLICADOS CANDIDATOS",
        report["duplicates"],
        lambda d: f"{d['name']} ({d['birth_year']}): {', '.join(d['ids'])}",
    )
    section(
        "LOOPS DE ASCENDENCIA",
        report["ancestry_loops"],
        lambda c: " -> ".join(c["cycle"]),
    )
    section(
        "INDIVIDUOS SEM NOME",
        report["empty"]["no_name"],
        lambda e: f"{e['id']} (linha {e['line']})",
    )
    section(
        "EVENTOS COM DATA E SEM LUGAR",
        report["empty"]["date_without_place"],
        lambda e: f"{e['id']:<10} {e['event']} {e['date']} (linha {e['line']})",
    )

    print("Nota: este auditor NAO corrige nada. Volte ao assento original")
    print("(SOUR/imagem) para decidir cada correcao. Ver references/07-gedcom.md.")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Audita um ficheiro GEDCOM (.ged). So-leitura."
    )
    ap.add_argument("gedcom", help="caminho para o ficheiro .ged")
    ap.add_argument("--json", action="store_true", help="saida em JSON")
    ap.add_argument("--walls", action="store_true",
                    help="listar so os muros (sem pais conhecidos)")
    args = ap.parse_args(argv)

    try:
        text, encoding = read_gedcom(args.gedcom)
    except OSError as e:
        print(f"erro a abrir {args.gedcom!r}: {e}", file=sys.stderr)
        return 2

    indis, fams = parse(text)
    report = audit(indis, fams, encoding)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report, walls_only=args.walls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
