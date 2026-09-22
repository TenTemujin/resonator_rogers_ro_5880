"""
Gera, a partir da geometria REAL extraida do HFSS (geometry.json,
produzido por export_geometry_views.py - leitura pura, projeto nunca
alterado/salvo):

  1. Desenho de engenharia cotado (para o datasheet em LaTeX):
     aedt_project/datasheet_figs/fig_drawing_top.png
     - vista de cima com cobre (espiral + trilha de alimentacao) e
       substrato em escala correta, com linhas de cota (mm) para todas
       as dimensoes relevantes de fabricacao.

  2. Artes de fabricacao em ESCALA REAL 1:1 (para imprimir e
     transferir ao substrato antes de corroer com percloreto/cloreto
     de ferro):
     aedt_project/fabrication/mask_top_normal.pdf   (como desenhado)
     aedt_project/fabrication/mask_top_mirrored.pdf (espelhada em X -
         necessaria no metodo de transferencia a ferro de passar/
         laser, onde o toner fica voltado para o cobre)
     Ambas com marcas de corte nos 4 cantos da placa (55 x 50 mm) e
     uma barra de calibracao de 20,00 mm para conferir se a
     impressora nao alterou a escala (imprimir sempre em "tamanho
     real" / "100%", nunca em "ajustar a pagina").
     A camada inferior (ground) e cobre solido continuo - NAO precisa
     de mascara de corrosao, e mencionado no rodape da mascara.

Uso:
    .venv\\Scripts\\python.exe scripts\\make_fabrication_drawings.py
"""

import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

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
sx0, sy0, _, sx1, sy1, _ = geo["Square_Spiral"]["bounding_box"]
fx0, fy0, _, fx1, fy1, _ = geo["Feedline"]["bounding_box"]

COPPER = "#b87333"
COPPER_DARK = "#8a5a2b"
SUBSTRATE_GREEN = "#4a7a4a"

# =================================================================
# 1. Desenho de engenharia cotado (para o corpo do datasheet)
# =================================================================
fig, ax = plt.subplots(figsize=(6.4, 5.6))
ax.add_patch(mpatches.Rectangle((sub_x0, sub_y0), board_w, board_h,
             facecolor=SUBSTRATE_GREEN, edgecolor="black", linewidth=1.0,
             alpha=0.55, zorder=1))
ax.add_patch(Polygon(spiral_outline, closed=True, facecolor=COPPER,
             edgecolor=COPPER_DARK, linewidth=0.6, zorder=3))
ax.add_patch(Polygon(feed_outline, closed=True, facecolor=COPPER,
             edgecolor=COPPER_DARK, linewidth=0.6, zorder=3))

pad = 6


def dim_h(y, x0, x1, text, offset=2.2):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", linewidth=0.8, color="#222"))
    ax.text((x0 + x1) / 2, y + offset * (1 if offset > 0 else -1) * 0.15 + 0.3,
            text, ha="center", va="bottom" if offset > 0 else "top", fontsize=7.5)


def dim_v(x, y0, y1, text, offset=2.2):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", linewidth=0.8, color="#222"))
    ax.text(x + offset, (y0 + y1) / 2, text, ha="left", va="center",
            fontsize=7.5, rotation=90)


# Cota geral da placa
dim_h(sub_y0 - 3.5, sub_x0, sub_x1, f"L_sub = {board_w:.1f} mm")
dim_v(sub_x1 + 3.0, sub_y0, sub_y1, f"W_sub = {board_h:.1f} mm")

# Cota da espiral (footprint real)
dim_h(sy1 + 2.0, sx0, sx1, f"{sx1 - sx0:.2f} mm", offset=1.0)
dim_v(sx1 + 1.2, sy0, sy1, f"{sy1 - sy0:.2f} mm", offset=1.0)

# Trilha de alimentacao (largura, w_feed) - cotada a esquerda da espiral
dim_v(fx0 - 2.0, fy0, fy1, f"w_feed = {fy1 - fy0:.2f} mm", offset=-1.6)

# Gap de acoplamento feed-espiral (cotado a esquerda, longe do callout)
ax.annotate("", xy=(sx0 + 0.6, fy1), xytext=(sx0 + 0.6, sy0),
            arrowprops=dict(arrowstyle="<->", linewidth=0.8, color="#c1121f"))
ax.text(sx0 - 1.4, (fy1 + sy0) / 2, f"g_cpl = {sy0 - fy1:.2f} mm",
        color="#c1121f", fontsize=7.5, va="center", ha="right")

# Callout: largura de trilha da espiral (w_spiral)
ax.annotate("w_spiral = 0.50 mm", xy=(3.5, 3.3), xytext=(9, 14),
            fontsize=7.5, arrowprops=dict(arrowstyle="->", linewidth=0.8))

ax.set_xlim(sub_x0 - 10, sub_x1 + 12)
ax.set_ylim(sub_y0 - 8, sub_y1 + 6)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("RessoadorQuadrado - vista de cima cotada (mm) - camada de cobre superior",
             fontsize=10)
legend_handles = [
    mpatches.Patch(facecolor=COPPER, edgecolor=COPPER_DARK, label="Cobre (mantido)"),
    mpatches.Patch(facecolor=SUBSTRATE_GREEN, alpha=0.55, label="RO5880 (substrato, 0,75 mm)"),
]
ax.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.06),
          ncol=2, fontsize=7.5, frameon=False)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig_drawing_top.png", dpi=300)
print(f"Salvo: {FIG_DIR / 'fig_drawing_top.png'}")


# =================================================================
# 2. Arte de fabricacao 1:1 (mascara de corrosao da camada superior)
# =================================================================
MARGIN = 16.0  # mm de margem para marcas de corte + barra de escala + textos
page_w = board_w + 2 * MARGIN
page_h = board_h + 2 * MARGIN


def make_mask(mirror: bool, out_path: Path):
    fig = plt.figure(figsize=(page_w / 25.4, page_h / 25.4), dpi=600)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(sub_x0 - MARGIN, sub_x1 + MARGIN)
    ax.set_ylim(sub_y0 - MARGIN, sub_y1 + MARGIN)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    def sgn(pt):
        x, y = pt
        return (-x, y) if mirror else (x, y)

    ax.add_patch(Polygon([sgn(p) for p in spiral_outline], closed=True,
                 facecolor="black", edgecolor="none", zorder=3))
    ax.add_patch(Polygon([sgn(p) for p in feed_outline], closed=True,
                 facecolor="black", edgecolor="none", zorder=3))

    # contorno de corte da placa (linha fina, nao e cobre)
    bx0, bx1 = sgn((sub_x0, 0))[0], sgn((sub_x1, 0))[0]
    ax.add_patch(mpatches.Rectangle((min(bx0, bx1), sub_y0),
                 abs(bx1 - bx0), board_h, fill=False,
                 edgecolor="black", linewidth=0.4, linestyle=(0, (4, 3))))

    # marcas de registro nos 4 cantos (cruzes de 3mm)
    for cx in (min(bx0, bx1), max(bx0, bx1)):
        for cy in (sub_y0, sub_y1):
            ax.plot([cx - 1.5, cx + 1.5], [cy, cy], color="black", linewidth=0.5)
            ax.plot([cx, cx], [cy - 1.5, cy + 1.5], color="black", linewidth=0.5)

    # barra de calibracao de 20,00 mm (fora da placa, na margem inferior)
    bar_y = sub_y0 - 6.0
    bar_x0 = min(bx0, bx1)
    ax.plot([bar_x0, bar_x0 + 20], [bar_y, bar_y], color="black", linewidth=1.2)
    ax.plot([bar_x0, bar_x0], [bar_y - 0.6, bar_y + 0.6], color="black",
            linewidth=1.2)
    ax.plot([bar_x0 + 20, bar_x0 + 20], [bar_y - 0.6, bar_y + 0.6], color="black",
            linewidth=1.2)
    ax.text(bar_x0 + 10, bar_y - 1.4,
            "20,00 mm - confira apos imprimir a 100% (sem ajustar a pagina)",
            ha="center", va="top", fontsize=4.6)

    label = ("MASCARA CAMADA SUPERIOR - ESPELHADA (transferencia a ferro)"
              if mirror else
              "MASCARA CAMADA SUPERIOR - NORMAL (referencia / fotolito)")
    ax.text((sub_x0 + sub_x1) / 2, sub_y1 + 7.0, label,
            ha="center", va="bottom", fontsize=5.0)
    ax.text((sub_x0 + sub_x1) / 2, sub_y0 - 11.5,
            "Camada inferior (ground) = cobre solido continuo, sem corrosao.",
            ha="center", va="top", fontsize=4.6)

    fig.savefig(out_path)
    plt.close(fig)
    print(f"Salvo: {out_path}")


make_mask(mirror=False, out_path=FAB_DIR / "mask_top_normal.pdf")
make_mask(mirror=True, out_path=FAB_DIR / "mask_top_mirrored.pdf")
make_mask(mirror=False, out_path=FAB_DIR / "mask_top_normal.png")
make_mask(mirror=True, out_path=FAB_DIR / "mask_top_mirrored.png")

print("\nGeometria de fabricacao (camada superior, mm):")
print(f"  Placa: {board_w:.2f} x {board_h:.2f} mm")
print(f"  Espiral (bbox): {sx1 - sx0:.2f} x {sy1 - sy0:.2f} mm")
print(f"  Trilha alim.: {fx1 - fx0:.2f} x {fy1 - fy0:.2f} mm")
print(f"  Gap acoplamento: {sy0 - fy1:.2f} mm")
