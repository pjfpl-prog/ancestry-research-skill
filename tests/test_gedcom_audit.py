"""Testes do auditor de GEDCOM.

Os ficheiros de teste sao ESCRITOS EM TEMPO DE EXECUCAO, nunca versionados: um
`.ged` no repositorio e o caminho mais curto para a arvore de alguem acabar
publica. Todos os nomes aqui sao inventados ou placeholders.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import gedcom_audit as ga  # noqa: E402


def escrever(tmp_path, texto, nome="t.ged", encoding="utf-8"):
    p = tmp_path / nome
    p.write_text(texto, encoding=encoding)
    return str(p)


def auditar(tmp_path, texto, **kw):
    caminho = escrever(tmp_path, texto, **kw)
    texto_lido, enc = ga.read_gedcom(caminho)
    indis, fams, dup = ga.parse(texto_lido)
    return ga.audit(indis, fams, enc, dup)


# --------------------------------------------------------------------------- #
# Reconciliacao FAMC / CHIL
# --------------------------------------------------------------------------- #
CHIL_SEM_FAMC = """0 HEAD
0 @I1@ INDI
1 NAME Pai /Placeholder/
1 BIRT
2 DATE 1700
1 FAMS @F1@
0 @I2@ INDI
1 NAME Filho /Placeholder/
1 BIRT
2 DATE 1730
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
"""


def test_chil_sem_famc_nao_gera_muro_falso(tmp_path):
    """O defeito central da versao anterior.

    A familia declara @I2@ como filho, mas o INDI nao tem o FAMC reciproco. Antes,
    o teste de muros lia so FAMC (logo: "sem pais") e o teste de idade lia so CHIL
    (logo: "nasceu antes do pai"). O mesmo relatorio afirmava as duas coisas.
    """
    rep = auditar(tmp_path, CHIL_SEM_FAMC)
    muros = {w["id"] for w in rep["walls"]}
    assert "@I2@" not in muros, "quem tem pai declarado por CHIL nao e um muro"
    assert "@I1@" in muros, "o pai, esse, nao tem pais: continua muro"


def test_chil_sem_famc_e_reportado_como_assimetria(tmp_path):
    """Reconciliar nao pode APAGAR o defeito: o ficheiro continua partido."""
    rep = auditar(tmp_path, CHIL_SEM_FAMC)
    tipos = [i["tipo"] for i in rep["link_inconsistencies"]]
    assert "FAM.CHIL sem FAMC reciproco no INDI" in tipos
    assert "HUSB sem FAMS reciproco no INDI" not in tipos  # @I1@ tem FAMS


def test_ponteiros_para_registos_inexistentes(tmp_path):
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME A /B/
1 FAMC @FNAOEXISTE@
0 @F1@ FAM
1 CHIL @INAOEXISTE@
0 TRLR
""")
    tipos = [i["tipo"] for i in rep["link_inconsistencies"]]
    assert "FAMC aponta para FAM inexistente" in tipos
    assert "CHIL aponta para INDI inexistente" in tipos


def test_stat_disproven_nao_conta_como_ascendencia(tmp_path):
    """O ficheiro diz que a ligacao foi REFUTADA. Usa-la seria inventar linhagem."""
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME Suposto Pai /Placeholder/
1 FAMS @F1@
0 @I2@ INDI
1 NAME Refutado /Placeholder/
1 FAMC @F1@
2 STAT disproven
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
""")
    assert "@I2@" in {w["id"] for w in rep["walls"]}


def test_pedi_adotado_fica_fora_do_teste_biologico(tmp_path):
    """Pai adotivo pode ser mais novo que o filho. Nao e data trocada."""
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME Adotante /Placeholder/
1 BIRT
2 DATE 1700
1 FAMS @F1@
0 @I2@ INDI
1 NAME Adotado /Placeholder/
1 BIRT
2 DATE 1660
1 FAMC @F1@
2 PEDI adopted
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
""")
    assert rep["impossible_dates"] == []
    assert rep["birt_as_death"] == []
    assert "@I2@" not in {w["id"] for w in rep["walls"]}, "adotado tem pais, so nao biologicos"


# --------------------------------------------------------------------------- #
# Nomes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("nome", [
    "Manuel /Testa/",      # apelido portugues real; a regex antiga marcava como lixo
    "Maria /Vide/",        # idem
    "Vide /Silva/",        # e mesmo em primeiro lugar
    "Joao /Vera/",
    "王小明",                # a versao antiga exigia letra latina
    "Иван /Петров/",
    "Δημήτριος /Παπαδόπουλος/",
])
def test_nomes_reais_nao_sao_lixo(nome):
    assert ga.looks_like_junk_name(nome) is False


@pytest.mark.parametrize("nome", [
    "??", "???", "teste", "N/A", "Living", "xxxx", "sem nome", "desconhecido",
    "ver livro 2", "ver fl. 34", "a confirmar", "FIXME", "duplicado", "12345",
])
def test_lembretes_continuam_a_ser_lixo(nome):
    assert ga.looks_like_junk_name(nome) is True


# --------------------------------------------------------------------------- #
# Datas
# --------------------------------------------------------------------------- #
def test_data_aproximada_nao_vira_impossibilidade(tmp_path):
    """"BEF 1900" contra obito em 1890 e coerente: nasceu antes de 1900."""
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME A /B/
1 BIRT
2 DATE BEF 1900
1 DEAT
2 DATE 1890
0 TRLR
""")
    assert rep["impossible_dates"] == []
    assert len(rep["suspicious_dates"]) == 1
    assert "aproximada" in rep["suspicious_dates"][0]["issue"]


def test_data_exata_impossivel_continua_impossivel(tmp_path):
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME A /B/
1 BIRT
2 DATE 1900
1 DEAT
2 DATE 1890
0 TRLR
""")
    assert len(rep["impossible_dates"]) == 1
    assert rep["suspicious_dates"] == []


def test_pai_velho_demais(tmp_path):
    """MAX_PARENT_AGE existia definido e nunca era usado."""
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME Pai /B/
1 BIRT
2 DATE 1700
1 FAMS @F1@
0 @I2@ INDI
1 NAME Filho /B/
1 BIRT
2 DATE 1790
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 CHIL @I2@
0 TRLR
""")
    assert any("90 anos ao nascer" in d["issue"] for d in rep["impossible_dates"])


def test_data_da_fonte_nao_vira_data_do_nascimento(tmp_path):
    """DATE dentro de SOUR/DATA e a data da FONTE, nao a do evento."""
    caminho = escrever(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME A /B/
1 BIRT
2 DATE 1800
2 SOUR @S1@
3 DATA
4 DATE 1999
0 TRLR
""")
    texto, _ = ga.read_gedcom(caminho)
    indis, _, _ = ga.parse(texto)
    assert indis["@I1@"].birt_date == "1800"


# --------------------------------------------------------------------------- #
# Estrutura do ficheiro
# --------------------------------------------------------------------------- #
def test_conc_e_cont_sao_juntados(tmp_path):
    caminho = escrever(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME Joao Carlos de Menezes Albuquer
2 CONC que e Sousa /Placeholder/
1 BIRT
2 PLAC Freguesia X, Concelho
3 CONC  Y
0 TRLR
""")
    texto, _ = ga.read_gedcom(caminho)
    indis, _, _ = ga.parse(texto)
    assert "Albuquerque e Sousa" in indis["@I1@"].name
    assert indis["@I1@"].birt_place == "Freguesia X, Concelho Y"


def test_xref_duplicado_e_reportado(tmp_path):
    rep = auditar(tmp_path, """0 HEAD
0 @I1@ INDI
1 NAME Primeiro /B/
0 @I1@ INDI
1 NAME Segundo /B/
0 TRLR
""")
    assert len(rep["duplicate_xrefs"]) == 1
    assert rep["duplicate_xrefs"][0]["xref"] == "@I1@"


def test_utf16_e_lido_e_nao_devolve_arvore_vazia(tmp_path):
    p = tmp_path / "u16.ged"
    p.write_text("0 HEAD\n0 @I1@ INDI\n1 NAME Ana /Placeholder/\n0 TRLR\n", encoding="utf-16")
    texto, enc = ga.read_gedcom(str(p))
    indis, _, _ = ga.parse(texto)
    assert enc == "utf-16"
    assert len(indis) == 1


def test_ciclo_reporta_so_os_nos_do_ciclo(tmp_path):
    """D e descendente de A, mas nao faz parte do ciclo A -> B -> A."""
    rep = auditar(tmp_path, """0 HEAD
0 @D@ INDI
1 NAME D /B/
1 FAMC @FD@
0 @A@ INDI
1 NAME A /B/
1 FAMC @FA@
1 FAMS @FD@
1 FAMS @FB@
0 @B@ INDI
1 NAME B /B/
1 FAMC @FB@
1 FAMS @FA@
0 @FD@ FAM
1 HUSB @A@
1 CHIL @D@
0 @FA@ FAM
1 HUSB @B@
1 CHIL @A@
0 @FB@ FAM
1 HUSB @A@
1 CHIL @B@
0 TRLR
""")
    assert len(rep["ancestry_loops"]) == 1
    ciclo = set(rep["ancestry_loops"][0]["cycle"])
    assert ciclo == {"@A@", "@B@"}, "o descendente @D@ nao pertence ao ciclo"


def test_ficheiro_que_nao_e_gedcom_falha_em_vez_de_relatorio_vazio(tmp_path):
    """Relatorio vazio sobre lixo e pior que erro: parece que esta tudo bem."""
    caminho = escrever(tmp_path, "isto nao e um gedcom\nlinha qualquer\n")
    assert ga.main([caminho]) == 2
