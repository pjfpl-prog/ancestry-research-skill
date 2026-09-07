"""Testes do notificador.

O ponto central: o token do bot viaja NO CAMINHO do URL da Bot API, e as
excecoes do `requests` trazem o URL. Qualquer caminho que deixe a mensagem de
erro chegar ao stderr ou a um log tem de estar redigido.

O token abaixo e inventado e tem a forma de um token do BotFather so para que a
substituicao seja testada a serio.
"""
import sys
import traceback
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import notify  # noqa: E402

TOKEN_FALSO = "123456789:AAFAKE-token-de-teste-NUNCA-real-abcdefghijklmn"


@pytest.fixture
def credenciais(monkeypatch):
    monkeypatch.setenv("NOTIFY_TELEGRAM_TOKEN", TOKEN_FALSO)
    monkeypatch.setenv("NOTIFY_TELEGRAM_CHAT", "1")


def falhar_com_url(*a, **k):
    import requests
    raise requests.exceptions.ConnectionError(
        "HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded "
        "with url: /bot%s/sendMessage (Caused by NewConnectionError)" % TOKEN_FALSO)


def _rastreio(exc):
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def test_send_message_nao_vaza_o_token(credenciais, monkeypatch):
    monkeypatch.setattr(notify.requests, "post", falhar_com_url)
    with pytest.raises(notify.NotifyError) as e:
        notify.send_message("oi")
    assert TOKEN_FALSO not in str(e.value)
    assert TOKEN_FALSO not in _rastreio(e.value)


def test_send_document_nao_vaza_o_token(credenciais, monkeypatch, tmp_path):
    """O caminho que a correcao original tinha esquecido."""
    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    monkeypatch.setattr(notify.requests, "post", falhar_com_url)
    with pytest.raises(notify.NotifyError) as e:
        notify.send_document(str(f))
    assert TOKEN_FALSO not in str(e.value)
    assert TOKEN_FALSO not in _rastreio(e.value)


@pytest.mark.parametrize("fn,args", [("send_message", ("oi",)), ("send_document", None)])
def test_excecao_original_nao_fica_encadeada(credenciais, monkeypatch, tmp_path, fn, args):
    """`from None` limpa `__cause__` mas NAO `__context__`.

    Um logger que percorra `__context__` encontraria a excecao do requests, com o
    URL e o token dentro. Por isso o erro e levantado FORA do bloco except.
    """
    if args is None:
        f = tmp_path / "a.txt"
        f.write_text("x", encoding="utf-8")
        args = (str(f),)
    monkeypatch.setattr(notify.requests, "post", falhar_com_url)
    with pytest.raises(notify.NotifyError) as e:
        getattr(notify, fn)(*args)
    assert e.value.__cause__ is None
    assert e.value.__context__ is None


def test_erro_preserva_o_motivo_da_falha(credenciais, monkeypatch):
    """Redigir nao pode virar mensagem inutil: a classe da excecao tem de sobrar."""
    monkeypatch.setattr(notify.requests, "post", falhar_com_url)
    with pytest.raises(notify.NotifyError) as e:
        notify.send_message("oi")
    assert "ConnectionError" in str(e.value)


def test_corpo_remoto_tambem_e_redigido():
    """Um 502 de intermediario costuma ecoar o URL pedido."""
    class R:
        status_code = 502
        text = ("Bad Gateway while requesting "
                "https://api.telegram.org/bot%s/sendMessage" % TOKEN_FALSO)

        def json(self):
            raise ValueError
    with pytest.raises(notify.NotifyError) as e:
        notify._handle_response(R(), TOKEN_FALSO)
    assert TOKEN_FALSO not in str(e.value)
    assert "<token-redigido>" in str(e.value)


def test_token_percent_encoded_tambem_e_redigido():
    codificado = TOKEN_FALSO.replace(":", "%3A")
    saida = notify._redact("url: /bot%s/x" % codificado, TOKEN_FALSO)
    assert codificado not in saida


def test_credenciais_ausentes_dizem_quais(monkeypatch):
    monkeypatch.delenv("NOTIFY_TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("NOTIFY_TELEGRAM_CHAT", raising=False)
    with pytest.raises(notify.NotifyError) as e:
        notify.send_message("oi")
    assert "NOTIFY_TELEGRAM_TOKEN" in str(e.value)
    assert "NOTIFY_TELEGRAM_CHAT" in str(e.value)


def test_ficheiro_grande_demais_nem_tenta_enviar(credenciais, monkeypatch, tmp_path):
    f = tmp_path / "grande.bin"
    f.write_bytes(b"0")
    monkeypatch.setattr(notify.os.path, "getsize", lambda _p: notify.TELEGRAM_FILE_LIMIT + 1)

    def nao_deve_ser_chamado(*a, **k):
        raise AssertionError("nao devia ter chegado a rede")
    monkeypatch.setattr(notify.requests, "post", nao_deve_ser_chamado)
    with pytest.raises(notify.NotifyError) as e:
        notify.send_document(str(f))
    assert "50 MB" in str(e.value)


@pytest.mark.parametrize("entrada,esperado", [
    ("a -> b", "a -> b"),
    ("Conceicao", "Conceicao"),
    ("acao ção", "acao ção"),
])
def test_strip_emoji_preserva_texto_util(entrada, esperado):
    assert notify.strip_emoji(entrada) == esperado


def test_strip_emoji_remove_pictogramas():
    assert "\U0001F600" not in notify.strip_emoji("ola \U0001F600")
