"""Teste LIVE contra os servidores reais da Hemeroteca Digital Brasileira. Desligado
por omissao.

Existe porque o resto da suite nao pode provar o que importa: que
`ListaPastaOcor.aspx` continua a responder a frio com a tabela neste formato, que
`%20` continua a ser o que torna a busca por frase, e que `hemeroteca-pdf.bn.gov.br`
continua a servir o PDF da edicao sem CAPTCHA. Os testes com substitutos pressupoem
esse contrato; se ele mudar, ficam verdes e a producao quebra em silencio.

Nao corre no CI, de proposito: servico publico nao leva pedidos a cada push, e um
teste que depende de rede transforma falha da BN em build vermelho. Corra a mao
antes de mexer no hemeroteca_bn.py e antes de uma release:

    HEMEROTECA_BN_LIVE=1 pytest -q -m live tests/test_hemeroteca_bn_live.py

Custo: 4 pedidos de lista e 1 PDF de cerca de 8 MB, com pausa entre eles. O termo
e o de uma figura publica (Rui Barbosa, 1849-1923) num bloco da Gazeta de
Noticias: nao ha ligacao a familia alguma (excecao admitida no CONTRIBUTING.md).

Contrato verificado a mao em 15/09/2026. Se este teste falhar, DIAGNOSTIQUE antes
de mexer: pode ser rede, dependencia em falta (truststore, PyMuPDF) ou regressao
local. So depois de excluir isso e que a falha significa que o servidor mudou, e
ai actualiza-se o codigo E a data em references/18-hemeroteca-bn.md.
"""
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hemeroteca_bn as hb  # noqa: E402

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("HEMEROTECA_BN_LIVE") != "1",
                       reason="teste live: defina HEMEROTECA_BN_LIVE=1 para o correr"),
]

BIB = "103730_05"          # Gazeta de Noticias (RJ), bloco 1920-1929
TERMO = "Rui Barbosa"
# Edicao que a lista devolvia em 15/09/2026 e cujo PDF tinha o termo na pagina 2,
# e uma edicao com PREFIXO DE LETRA que a mesma lista trazia.
ANO, EDICAO, PAGINA = "1921", "00193", 2
EDICAO_COM_PREFIXO = ("1922", "a00165")


def test_lista_responde_a_frio_com_a_tabela_e_com_a_edicao_prefixada():
    eds, nota = hb.listar_edicoes(hb._sessao(), BIB, TERMO, delay=2.0)
    assert nota == "" and eds, "a lista veio vazia: termo, bloco ou formato mudaram"
    pares = {(e["ano"], e["edicao"]) for e in eds}
    assert (ANO, EDICAO) in pares
    assert EDICAO_COM_PREFIXO in pares, "a edicao com prefixo de letra deixou de vir"
    assert all(e["ocorrencias"] >= 1 for e in eds)


def test_so_pct20_entre_aspas_da_a_busca_por_frase():
    """
    A trava do encoding, com os tres controles medidos em 15/09/2026: %20 entre
    aspas (frase) e estreito; `+` entre aspas e sem aspas sao largos e iguais entre
    si. Se isto deixar de valer, `url_lista` pode voltar a `urlencode`.
    """
    s = hb._sessao()
    url = hb.url_lista(BIB, TERMO)
    with hb._get(s, url, delay=2.0) as r:
        frase = hb.analisar_lista(r.text)
    with hb._get(s, url.replace("%20", "+"), delay=2.0) as r:
        com_mais = hb.analisar_lista(r.text)
    with hb._get(s, url.replace("%22", ""), delay=2.0) as r:
        sem_aspas = hb.analisar_lista(r.text)
    assert 0 < len(frase) < len(com_mais), (len(frase), len(com_mais))
    assert abs(len(com_mais) - len(sem_aspas)) <= 2, (len(com_mais), len(sem_aspas))


def test_pdf_publico_da_edicao_a_frio_tem_o_termo_na_pagina_esperada(tmp_path):
    """Sessao NOVA, sem cookie da lista: prova que o PDF e servido a frio de verdade."""
    time.sleep(2)
    destino = tmp_path / "edicao.pdf"
    r = hb.baixar_edicao(hb._sessao(), BIB, ANO, EDICAO, str(destino), delay=0)
    assert r["bytes"] > 1_000_000, "PDF suspeitamente pequeno"
    achado = hb.paginas_com_termo(str(destino), TERMO)
    assert achado["termo_usado"] == TERMO
    assert PAGINA in [p["pagina"] for p in achado["paginas"]]
    dpi = hb.medir_dpi(str(destino), PAGINA)[0]["dpi"]
    assert dpi is not None and 60 <= dpi <= 400
