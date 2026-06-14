#!/usr/bin/env python3
"""image_tools.py - ferramentas de imagem para leitura paleografica de assentos.

Usa Pillow (PIL). Serve para tratar fotogramas de livros paroquiais / notariais /
Inquisicao baixados de arquivos digitais (DigitArq, FamilySearch, ADs, etc.) e
deixar a tinta esmaecida legivel para transcricao manual ou OCR.

Funcoes / sub-comandos:
  download     baixa um fileId do DigitArq (dissemination) ou um URL qualquer
  crop         recorta uma regiao (caixa relativa 0..1) e aplica zoom
  folio        recorta o canto superior-direito (onde costuma estar o numero do folio)
  enhance      grayscale + autocontrast (+ threshold opcional) para tinta fraca
  split        divide uma abertura de duas paginas em "left" / "right"

Caixa relativa (box_rel): (esquerda, topo, direita, baixo) em fracao 0..1 do
tamanho da imagem. Ex.: "0,0,0.5,1" = metade esquerda.

NB: o codigo-fonte e ASCII de proposito (sem acentos); os dados/ficheiros tratados
nao tem qualquer ligacao a uma pessoa ou familia especifica.

Exemplos:
    python image_tools.py download --file-id 12345 -o folio.jpg
    python image_tools.py download --url https://exemplo/arquivo.jpg -o folio.jpg
    python image_tools.py enhance entrada.jpg --threshold 135 --zoom 6 -o saida.png
    python image_tools.py crop entrada.jpg --box 0.1,0.2,0.6,0.45 --zoom 4 -o trecho.png
    python image_tools.py folio entrada.jpg --zoom 8 -o numero.png
    python image_tools.py split abertura.jpg --side right -o pagina_dir.png
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - mensagem amigavel
    sys.stderr.write(
        "Pillow nao esta instalado. Instale com:  pip install Pillow\n"
    )
    raise

# urllib e da biblioteca-padrao; so e usado no sub-comando 'download'.
import urllib.request

# DigitArq / Torre do Tombo: endpoint de imagem em alta resolucao (sem login).
DIGITARQ_DISSEMINATION = "https://digitarq.arquivos.pt/rdigital/dissemination?fileId={fid}"
DIGITARQ_THUMB = "https://digitarq.arquivos.pt/rdigital/thumb?fileId={fid}"

# User-Agent neutro: alguns arquivos recusam o default do urllib.
_USER_AGENT = "ancestry-research-skill/1.0 (+image_tools.py)"

BoxRel = Tuple[float, float, float, float]


# --------------------------------------------------------------------------- #
# Utilitarios                                                                  #
# --------------------------------------------------------------------------- #

def _eprint(msg: str) -> None:
    sys.stderr.write(msg.rstrip("\n") + "\n")


def parse_box(text: str) -> BoxRel:
    """Converte "l,t,r,b" (fracoes 0..1) numa tupla validada.

    Aceita espacos. Garante 0 <= l < r <= 1 e 0 <= t < b <= 1.
    """
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip() != ""]
    if len(parts) != 4:
        raise ValueError(
            "box precisa de 4 valores 'esq,topo,dir,baixo' (fracoes 0..1), "
            "ex.: 0.1,0.2,0.6,0.45"
        )
    try:
        l, t, r, b = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError("box: todos os valores tem de ser numeros") from exc
    box = (l, t, r, b)
    for v in box:
        if not (0.0 <= v <= 1.0):
            raise ValueError("box: cada valor tem de estar entre 0 e 1")
    if not (l < r):
        raise ValueError("box: esquerda tem de ser menor que direita")
    if not (t < b):
        raise ValueError("box: topo tem de ser menor que baixo")
    return box


def load_image(img: "Image.Image | str") -> "Image.Image":
    """Aceita um caminho ou um objeto Image e devolve um Image carregado.

    Faz .load() para nao deixar o ficheiro aberto e aplica a orientacao EXIF.
    """
    if isinstance(img, Image.Image):
        im = img
    else:
        im = Image.open(img)
        im.load()
    # Respeita a rotacao gravada no EXIF (fotos de telemovel/scanner).
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:  # EXIF partido nao deve derrubar o pipeline
        pass
    return im


def save_image(im: "Image.Image", out: str) -> str:
    """Grava a imagem inferindo o formato pela extensao; cria a pasta se preciso.

    PNG/TIFF nao aceitam modo de cor com alfa em alguns casos; aqui convertemos
    para RGB quando o destino for JPEG e a imagem tiver alfa/paleta.
    """
    out = os.path.abspath(out)
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    ext = os.path.splitext(out)[1].lower()
    save_im = im
    if ext in (".jpg", ".jpeg") and im.mode in ("RGBA", "LA", "P"):
        save_im = im.convert("RGB")
    params = {}
    if ext in (".jpg", ".jpeg"):
        params["quality"] = 95
    save_im.save(out, **params)
    return out


def _abs_box(im: "Image.Image", box_rel: BoxRel) -> Tuple[int, int, int, int]:
    """Converte caixa relativa (0..1) em pixels inteiros, com clamp aos limites."""
    w, h = im.size
    l, t, r, b = box_rel
    left = max(0, min(w, int(round(l * w))))
    top = max(0, min(h, int(round(t * h))))
    right = max(0, min(w, int(round(r * w))))
    bottom = max(0, min(h, int(round(b * h))))
    # Garante pelo menos 1 px em cada eixo.
    if right <= left:
        right = min(w, left + 1)
    if bottom <= top:
        bottom = min(h, top + 1)
    return (left, top, right, bottom)


def _apply_zoom(im: "Image.Image", zoom: float) -> "Image.Image":
    """Amplia por um fator (>1). zoom<=1 ou ~1 nao faz nada. Usa LANCZOS."""
    if zoom is None or zoom <= 1.0001:
        return im
    w, h = im.size
    new_size = (max(1, int(round(w * zoom))), max(1, int(round(h * zoom))))
    return im.resize(new_size, Image.LANCZOS)


# --------------------------------------------------------------------------- #
# Operacoes                                                                    #
# --------------------------------------------------------------------------- #

def download(source: str, out: str, *, is_file_id: bool = False,
             thumb: bool = False, timeout: float = 60.0) -> str:
    """Baixa uma imagem.

    source: um fileId numerico do DigitArq (quando is_file_id=True) ou um URL.
    thumb : se True e for fileId, usa o endpoint de miniatura em vez do de alta-res.
    Devolve o caminho gravado.
    """
    if is_file_id:
        fid = str(source).strip()
        if not fid.isdigit():
            raise ValueError("file-id tem de ser numerico (ex.: 12345)")
        url = (DIGITARQ_THUMB if thumb else DIGITARQ_DISSEMINATION).format(fid=fid)
    else:
        url = str(source).strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("url tem de comecar por http:// ou https://")

    out = os.path.abspath(out)
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    if not data:
        raise RuntimeError("download vazio (0 bytes) - verifique o fileId/url")
    with open(out, "wb") as fh:
        fh.write(data)
    # Validacao leve: confirma que o que veio e mesmo uma imagem.
    try:
        with Image.open(out) as probe:
            probe.verify()
    except Exception as exc:
        raise RuntimeError(
            "o conteudo baixado nao e uma imagem valida (talvez HTML de erro)"
        ) from exc
    return out


def crop_region(img: "Image.Image | str", box_rel: BoxRel,
                zoom: float = 1.0) -> "Image.Image":
    """Recorta uma regiao (caixa relativa) e aplica zoom opcional."""
    im = load_image(img)
    abs_box = _abs_box(im, box_rel)
    cropped = im.crop(abs_box)
    return _apply_zoom(cropped, zoom)


def folio_corner(img: "Image.Image | str", zoom: float = 6.0,
                 frac: float = 0.18) -> "Image.Image":
    """Recorta o canto superior-direito, onde costuma vir o numero do folio.

    frac: fracao da largura/altura usada para o canto (default 18%).
    """
    frac = max(0.02, min(0.5, float(frac)))
    box_rel: BoxRel = (1.0 - frac, 0.0, 1.0, frac)
    return crop_region(img, box_rel, zoom=zoom)


def enhance(img: "Image.Image | str", threshold: Optional[int] = None,
            zoom: float = 1.0, autocontrast: bool = True,
            invert: bool = False) -> "Image.Image":
    """Realca tinta esmaecida.

    Passos: grayscale -> autocontrast (opcional) -> threshold (opcional, 0..255).
    threshold=None mantem tons de cinza; com valor, binariza (preto/branco) o que
    ajuda OCR em tinta fraca. invert pode ajudar quando o fundo e mais escuro.
    O zoom e aplicado no fim para ampliar o trecho.
    """
    im = load_image(img).convert("L")
    if autocontrast:
        # cutoff=1 ignora 1% dos extremos (manchas/furos) ao esticar o histograma.
        im = ImageOps.autocontrast(im, cutoff=1)
    if threshold is not None:
        thr = int(threshold)
        if not (0 <= thr <= 255):
            raise ValueError("threshold tem de estar entre 0 e 255")
        im = im.point(lambda px, t=thr: 255 if px > t else 0, mode="L")
    if invert:
        im = ImageOps.invert(im.convert("L"))
    return _apply_zoom(im, zoom)


def split_page(img: "Image.Image | str", side: str,
               zoom: float = 1.0) -> "Image.Image":
    """Divide uma abertura de duas paginas e devolve a metade pedida.

    side: "left" ou "right".
    """
    side = (side or "").strip().lower()
    if side in ("left", "esq", "esquerda", "l"):
        box_rel: BoxRel = (0.0, 0.0, 0.5, 1.0)
    elif side in ("right", "dir", "direita", "r"):
        box_rel = (0.5, 0.0, 1.0, 1.0)
    else:
        raise ValueError("side tem de ser 'left' ou 'right'")
    return crop_region(img, box_rel, zoom=zoom)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def _add_common_out(p: argparse.ArgumentParser, default: str) -> None:
    p.add_argument("-o", "--out", default=default,
                   help="caminho de saida (default: %(default)s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_tools.py",
        description="Ferramentas de imagem para leitura paleografica de assentos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # download
    pd = sub.add_parser("download", help="baixa um fileId do DigitArq ou um URL")
    grp = pd.add_mutually_exclusive_group(required=True)
    grp.add_argument("--file-id", help="fileId numerico do DigitArq (dissemination)")
    grp.add_argument("--url", help="URL direto de uma imagem")
    pd.add_argument("--thumb", action="store_true",
                    help="com --file-id, baixa a miniatura em vez da alta-res")
    pd.add_argument("--timeout", type=float, default=60.0,
                    help="timeout em segundos (default: 60)")
    _add_common_out(pd, "imagem.jpg")

    # crop
    pc = sub.add_parser("crop", help="recorta uma regiao (caixa relativa) + zoom")
    pc.add_argument("input", help="imagem de entrada")
    pc.add_argument("--box", required=True,
                    help="caixa relativa 'esq,topo,dir,baixo' (0..1)")
    pc.add_argument("--zoom", type=float, default=1.0, help="fator de zoom (>1)")
    _add_common_out(pc, "recorte.png")

    # folio
    pf = sub.add_parser("folio", help="recorta o canto sup-direito (numero do folio)")
    pf.add_argument("input", help="imagem de entrada")
    pf.add_argument("--frac", type=float, default=0.18,
                    help="fracao do canto (default: 0.18)")
    pf.add_argument("--zoom", type=float, default=6.0, help="fator de zoom (>1)")
    _add_common_out(pf, "folio.png")

    # enhance
    pe = sub.add_parser("enhance", help="grayscale + autocontrast (+threshold)")
    pe.add_argument("input", help="imagem de entrada")
    pe.add_argument("--threshold", type=int, default=None,
                    help="binariza em 0..255 (omitido = mantem cinza)")
    pe.add_argument("--no-autocontrast", action="store_true",
                    help="nao aplicar autocontrast")
    pe.add_argument("--invert", action="store_true",
                    help="inverte (util com fundo escuro)")
    pe.add_argument("--zoom", type=float, default=1.0, help="fator de zoom (>1)")
    _add_common_out(pe, "realcada.png")

    # split
    ps = sub.add_parser("split", help="divide abertura de 2 paginas (left/right)")
    ps.add_argument("input", help="imagem de entrada")
    ps.add_argument("--side", required=True, choices=["left", "right"],
                    help="metade a manter")
    ps.add_argument("--zoom", type=float, default=1.0, help="fator de zoom (>1)")
    _add_common_out(ps, "pagina.png")

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.cmd == "download":
            if args.file_id is not None:
                out = download(args.file_id, args.out, is_file_id=True,
                               thumb=args.thumb, timeout=args.timeout)
            else:
                out = download(args.url, args.out, is_file_id=False,
                               timeout=args.timeout)
            print(out)
            return 0

        if args.cmd == "crop":
            box = parse_box(args.box)
            im = crop_region(args.input, box, zoom=args.zoom)
            print(save_image(im, args.out))
            return 0

        if args.cmd == "folio":
            im = folio_corner(args.input, zoom=args.zoom, frac=args.frac)
            print(save_image(im, args.out))
            return 0

        if args.cmd == "enhance":
            im = enhance(
                args.input,
                threshold=args.threshold,
                zoom=args.zoom,
                autocontrast=not args.no_autocontrast,
                invert=args.invert,
            )
            print(save_image(im, args.out))
            return 0

        if args.cmd == "split":
            im = split_page(args.input, args.side, zoom=args.zoom)
            print(save_image(im, args.out))
            return 0
    except (ValueError, RuntimeError, OSError) as exc:
        _eprint("ERRO: " + str(exc))
        return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
