"""Testes das ferramentas de imagem."""
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import image_tools as it  # noqa: E402


@pytest.fixture
def img():
    return Image.new("RGB", (200, 100), "white")


@pytest.mark.parametrize("box,esperado", [
    ((0.0, 0.0, 0.5, 1.0), (100, 100)),
    ((0.5, 0.0, 1.0, 1.0), (100, 100)),
    ((0.999, 0.0, 1.0, 1.0), (1, 100)),   # cai na borda direita
    ((0.0, 0.999, 1.0, 1.0), (200, 1)),   # cai na borda inferior
    ((0.9999, 0.9999, 1.0, 1.0), (1, 1)),
])
def test_recorte_nunca_sai_com_zero_pixeis(img, box, esperado):
    """O docstring promete "pelo menos 1 px"; a versao anterior devolvia 0x100."""
    assert it.crop_region(img, box).size == esperado


def test_split_divide_ao_meio(img):
    assert it.split_page(img, "left").size == (100, 100)
    assert it.split_page(img, "right").size == (100, 100)


def test_split_recusa_lado_invalido(img):
    with pytest.raises(ValueError):
        it.split_page(img, "meio")


@pytest.mark.parametrize("texto", ["0.6,0,0.5,1", "0,0.9,1,0.2", "1,2,3", "a,b,c,d", "0,0,2,1"])
def test_parse_box_recusa_caixa_invalida(texto):
    with pytest.raises(ValueError):
        it.parse_box(texto)


def test_parse_box_aceita_ponto_e_virgula():
    assert it.parse_box("0.1; 0.2; 0.6; 0.45") == (0.1, 0.2, 0.6, 0.45)


def test_folio_recorta_o_canto_superior_direito(img):
    out = it.folio_corner(img, zoom=1.0, frac=0.2)
    assert out.size == (40, 20)


def test_enhance_binariza(img):
    out = it.enhance(img, threshold=128)
    assert out.mode == "L"


def test_zoom_amplia(img):
    assert it._apply_zoom(img, 3).size == (600, 300)


# --------------------------------------------------------------------------- #
# download
# --------------------------------------------------------------------------- #
class RespostaFalsa:
    def __init__(self, corpo):
        self._corpo = corpo

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_html_de_erro_nao_destroi_ficheiro_existente(monkeypatch, tmp_path):
    """A versao anterior gravava PRIMEIRO e so depois validava com o PIL."""
    destino = tmp_path / "folio.jpg"
    Image.new("RGB", (10, 10), "blue").save(destino)
    antes = destino.read_bytes()
    monkeypatch.setattr(it.urllib.request, "urlopen",
                        lambda *a, **k: RespostaFalsa(b"<html>erro</html>"))
    with pytest.raises(RuntimeError) as e:
        it.download("https://exemplo/x.jpg", str(destino))
    assert "nao e uma imagem valida" in str(e.value)
    assert destino.read_bytes() == antes, "o ficheiro bom tem de sobreviver"


def test_imagem_valida_e_gravada(monkeypatch, tmp_path):
    import io as _io
    buf = _io.BytesIO()
    Image.new("RGB", (5, 5), "red").save(buf, format="JPEG")
    corpo = buf.getvalue()
    destino = tmp_path / "sub" / "folio.jpg"
    monkeypatch.setattr(it.urllib.request, "urlopen", lambda *a, **k: RespostaFalsa(corpo))
    it.download("https://exemplo/x.jpg", str(destino))
    assert destino.read_bytes() == corpo
    assert list(destino.parent.glob(".dl_*")) == [], "temporario tem de sumir"


def test_download_vazio_falha(monkeypatch, tmp_path):
    monkeypatch.setattr(it.urllib.request, "urlopen", lambda *a, **k: RespostaFalsa(b""))
    with pytest.raises(RuntimeError):
        it.download("https://exemplo/x.jpg", str(tmp_path / "a.jpg"))


@pytest.mark.parametrize("fid", ["abc", "12a", ""])
def test_file_id_tem_de_ser_numerico(fid, tmp_path):
    with pytest.raises(ValueError):
        it.download(fid, str(tmp_path / "a.jpg"), is_file_id=True)


def test_url_tem_de_ser_http(tmp_path):
    with pytest.raises(ValueError):
        it.download("ftp://exemplo/x.jpg", str(tmp_path / "a.jpg"))
