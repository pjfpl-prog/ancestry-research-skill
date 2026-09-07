"""Higiene do repositorio: nada de dado pessoal nem credencial no que e versionado.

Este e o teste mais barato e o que evita o erro mais caro. O `.gitignore` impede
que um ficheiro de pesquisa entre por acidente; este teste olha para DENTRO do
que ja esta versionado.

Limites, ditos aqui para nao serem confundidos com garantia:
  * so ve o que `git ls-files` devolve AGORA. Um segredo introduzido num commit e
    removido no seguinte continua no historico e passa por aqui;
  * so apanha os padroes escritos abaixo. Nao substitui o `secret scanning` com
    push protection do GitHub, que deve ficar ligado quando o repo for publico;
  * nao deteta genealogia real escrita em prosa.
"""
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

# Extensoes que faz sentido ler como texto.
TEXTO = {".py", ".md", ".js", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ""}

PADROES = [
    ("caminho absoluto de Windows", re.compile(r"[A-Za-z]:\\+Users\\+", re.IGNORECASE)),
    ("caminho absoluto de utilizador Unix", re.compile(r"/(?:home|Users)/[a-z][a-z0-9._-]+/")),
    ("token de bot do Telegram", re.compile(r"\b\d{8,}:[A-Za-z0-9_-]{30,}\b")),
    ("chave de API da OpenAI", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("chave de API do Google", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("token do GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("cabecalho de chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("endereco de e-mail", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]

# Excecoes deliberadas, com motivo. Qualquer acrescimo aqui tem de vir com motivo.
PERMITIDO = {
    # o proprio teste descreve os padroes que caca
    "tests/test_repo_hygiene.py",
    # o token de teste vive nos testes do notificador, e e inventado
    "tests/test_notify.py",
}
EMAILS_PERMITIDOS = re.compile(
    r"noreply@example\.com|users\.noreply\.github\.com|"
    r"[a-z_]+@(?:exemplo|example)\.(?:com|org|pt)"
)


def ficheiros_versionados():
    saida = subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ,
                           capture_output=True, check=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in saida.split(b"\0") if p]


@pytest.mark.parametrize("rel", ficheiros_versionados())
def test_ficheiro_versionado_esta_limpo(rel):
    if rel in PERMITIDO:
        pytest.skip("excecao declarada em PERMITIDO")
    caminho = RAIZ / rel
    if caminho.suffix.lower() not in TEXTO or not caminho.is_file():
        pytest.skip("nao e ficheiro de texto")
    conteudo = caminho.read_text(encoding="utf-8", errors="replace")
    for nome, padrao in PADROES:
        for achado in padrao.finditer(conteudo):
            trecho = achado.group(0)
            if nome == "endereco de e-mail" and EMAILS_PERMITIDOS.search(trecho):
                continue
            linha = conteudo[:achado.start()].count("\n") + 1
            pytest.fail("%s:%d contem %s" % (rel, linha, nome))


def test_nenhum_gedcom_versionado():
    """Um .ged e a arvore de alguem. Os testes geram os seus em tmp_path."""
    assert [f for f in ficheiros_versionados() if f.lower().endswith(".ged")] == []


def test_nenhuma_imagem_versionada():
    """Digitalizacao de arquivo tem licenca propria e costuma vir de pesquisa real."""
    exts = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf")
    assert [f for f in ficheiros_versionados() if f.lower().endswith(exts)] == []


def test_licenca_esta_versionada():
    """A MIT exige preservar o aviso; o README manda copiar a skill para outro sitio."""
    assert "LICENSE" in ficheiros_versionados()


def test_readme_nao_manda_copiar_pasta_inexistente():
    """O comando de instalacao tem de funcionar para quem clona, nao so aqui."""
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    for linha in readme.splitlines():
        if linha.strip().startswith("cp -r "):
            for item in linha.split()[2:]:
                if item.startswith("~") or item.startswith(".claude"):
                    continue
                alvo = RAIZ / item
                assert alvo.exists(), "README manda copiar %r, que nao existe" % item
                if alvo.is_dir():
                    versionados = [f for f in ficheiros_versionados()
                                   if f.startswith(item.rstrip("/") + "/")]
                    assert versionados, (
                        "%r existe aqui mas nao tem nada versionado: nao chega a quem clonar"
                        % item)


def test_identidade_do_commit_nao_expoe_email_pessoal():
    """Num repo publico o autor do commit fica gravado para sempre."""
    saida = subprocess.run(["git", "log", "--format=%ae%n%ce"], cwd=RAIZ,
                           capture_output=True, text=True)
    if saida.returncode != 0:
        pytest.skip("sem historico git")
    for email in {e.strip() for e in saida.stdout.splitlines() if e.strip()}:
        assert EMAILS_PERMITIDOS.search(email), (
            "commit assinado com %r: use o noreply do GitHub" % email)
