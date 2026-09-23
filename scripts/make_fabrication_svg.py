"""
Gera as mascaras de fabricacao do RessoadorQuadrado em SVG, a partir da
geometria REAL ja extraida do HFSS (aedt_project/datasheet_figs/geometry.json,
produzido por export_geometry_views.py - este script nao toca no AEDT).

Por que SVG em vez de so PDF/PNG (que ja existem em make_fabrication_drawings.py):
  - SVG declara o tamanho fisico da pagina em milimetros de forma explicita
    (atributos width="...mm" height="...mm" + viewBox numericamente igual),
    o que a maioria dos visualizadores/RIPs de papel fotografico/transfer
    respeita literalmente ao imprimir em "tamanho real / 100%". Isso evita
    a ambiguidade de DPI que as vezes aparece em PNG raster.
  - Formato vetorial: nao ha serrilhado nas bordas do cobre nem no fotolito,
    o que da uma transferencia com bordas mais nitidas.

Gera em aedt_project/fabrication/:
  mask_top_normal.svg    (como desenhado, para conferencia/fotolito)
  mask_top_mirrored.svg  (espelhada em X - para transferencia a ferro de
                          passar/laser, onde o toner fica voltado para o
                          cobre)

Ambas em escala real 1:1, com marcas de corte nos 4 cantos da placa e uma
barra de calibracao de 20,00 mm para conferir se a impressora nao alterou
a escala (imprimir sempre em "tamanho real" / "100%", nunca "ajustar a
pagina"). A camada inferior (ground) e cobre solido continuo - mencionado
no rodape da mascara.

Uso:
    .venv\\Scripts\\python.exe scripts\\make_fabrication_svg.py
"""

import json
from pathlib import Path

BASE = Path(r"D:\my_projects\resonator_rogers_ro_5880\aedt_project")
FIG_DIR = BASE / "datasheet_figs"
FAB_DIR = BASE / "fabrication"
FAB_DIR.mkdir(exist_ok=True)

with open(FIG_DIR / "geometry.json") as f:
    geo = json.load(f)

sub_x0, sub_y0, _, sub_x1, sub_y1, _ = geo["Substrate_RO5880"]["bounding_box"]
board_w, board_h = sub_x1 - sub_x0, sub_y1 - sub_y0
spiral_outline = geo["Square_Spiral"]["top_face_outline_xy_mm"]
feed_outline = geo["Feedline"]["top_face_outline_xy_mm"]

MARGIN = 16.0  # mm de margem para marcas de corte + barra de escala + textos
page_w = board_w + 2 * MARGIN
page_h = board_h + 2 * MARGIN


def make_mask_svg(mirror: bool, out_path: Path) -> None:
    """SVG em mm reais (1 unidade de usuario = 1 mm). Eixo Y do SVG cresce
    para baixo, entao inverte-se o Y de cada ponto (svg_y = -y_real) para
    que "para cima" no desenho corresponda a "para cima" na placa real."""

    def sx(x_real: float) -> float:
        return -x_real if mirror else x_real

    def sy(y_real: float) -> float:
        return -y_real

    def pt(p):
        x, y = p
        return f"{sx(x):.4f},{sy(y):.4f}"

    def polygon(points, **attrs):
        pts_str = " ".join(pt(p) for p in points)
        attr_str = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        return f'<polygon points="{pts_str}" {attr_str} />'

    view_x0 = sub_x0 - MARGIN
    view_y0 = -(sub_y1 + MARGIN)  # topo real -> y svg minimo

    bx0, bx1 = sorted((sx(sub_x0), sx(sub_x1)))

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{page_w:.4f}mm" height="{page_h:.4f}mm" '
        f'viewBox="{view_x0:.4f} {view_y0:.4f} {page_w:.4f} {page_h:.4f}">'
    )
    parts.append(f'<rect x="{view_x0:.4f}" y="{view_y0:.4f}" '
                 f'width="{page_w:.4f}" height="{page_h:.4f}" fill="white" />')

    # cobre (espiral + trilha de alimentacao)
    parts.append(polygon(spiral_outline, fill="black", stroke="none"))
    parts.append(polygon(feed_outline, fill="black", stroke="none"))

    # contorno de corte da placa (linha fina tracejada, nao e cobre)
    parts.append(
        f'<rect x="{bx0:.4f}" y="{sy(sub_y1):.4f}" '
        f'width="{(bx1 - bx0):.4f}" height="{board_h:.4f}" '
        f'fill="none" stroke="black" stroke-width="0.1" stroke-dasharray="1.2,0.9" />'
    )

    # marcas de registro nos 4 cantos (cruzes de 3 mm)
    for cx in (bx0, bx1):
        for cy_real in (sub_y0, sub_y1):
            cy = sy(cy_real)
            parts.append(f'<line x1="{cx - 1.5:.4f}" y1="{cy:.4f}" '
                         f'x2="{cx + 1.5:.4f}" y2="{cy:.4f}" '
                         f'stroke="black" stroke-width="0.15" />')
            parts.append(f'<line x1="{cx:.4f}" y1="{cy - 1.5:.4f}" '
                         f'x2="{cx:.4f}" y2="{cy + 1.5:.4f}" '
                         f'stroke="black" stroke-width="0.15" />')

    # barra de calibracao de 20,00 mm (fora da placa, na margem inferior)
    bar_y = sy(sub_y0 - 6.0)
    bar_x0 = bx0
    parts.append(f'<line x1="{bar_x0:.4f}" y1="{bar_y:.4f}" '
                 f'x2="{bar_x0 + 20:.4f}" y2="{bar_y:.4f}" '
                 f'stroke="black" stroke-width="0.25" />')
    for x_end in (bar_x0, bar_x0 + 20):
        parts.append(f'<line x1="{x_end:.4f}" y1="{bar_y - 0.6:.4f}" '
                     f'x2="{x_end:.4f}" y2="{bar_y + 0.6:.4f}" '
                     f'stroke="black" stroke-width="0.25" />')
    parts.append(
        f'<text x="{bar_x0 + 10:.4f}" y="{bar_y + 2.2:.4f}" '
        f'font-family="sans-serif" font-size="1.8" text-anchor="middle">'
        f'20,00 mm - confira apos imprimir a 100% (sem ajustar a pagina)</text>'
    )

    label = ("MASCARA CAMADA SUPERIOR - ESPELHADA (transferencia a ferro)"
              if mirror else
              "MASCARA CAMADA SUPERIOR - NORMAL (referencia / fotolito)")
    parts.append(
        f'<text x="{(bx0 + bx1) / 2:.4f}" y="{sy(sub_y1 + 5.5):.4f}" '
        f'font-family="sans-serif" font-size="2.0" text-anchor="middle">{label}</text>'
    )
    parts.append(
        f'<text x="{(bx0 + bx1) / 2:.4f}" y="{sy(sub_y0 - 10.0):.4f}" '
        f'font-family="sans-serif" font-size="1.8" text-anchor="middle">'
        f'Camada inferior (ground) = cobre solido continuo, sem corrosao.</text>'
    )

    parts.append("</svg>")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"Salvo: {out_path}")


make_mask_svg(mirror=False, out_path=FAB_DIR / "mask_top_normal.svg")
make_mask_svg(mirror=True, out_path=FAB_DIR / "mask_top_mirrored.svg")

print("\nGeometria de fabricacao (camada superior, mm):")
print(f"  Placa: {board_w:.2f} x {board_h:.2f} mm")
print(f"  Pagina SVG (com margem p/ marcas de corte): {page_w:.2f} x {page_h:.2f} mm")
