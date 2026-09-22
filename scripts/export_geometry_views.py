"""
Exporta dados e imagens REAIS do modelo 3D do RessoadorQuadrado (projeto
ja aberto no AEDT em execucao) para uso no datasheet em LaTeX.

SOMENTE LEITURA no sentido que importa: conecta na sessao do AEDT ja
aberta, NUNCA chama save_project(), e qualquer alteracao cosmetica de
display (cor/wireframe, so para a foto ficar limpa em vez de aparecer
com o flag "Wireframe" salvo no objeto Square_Spiral) e restaurada ao
valor original antes do script terminar. Nao roda solve, nao cria
setup, nao edita geometria/variaveis.

Gera em aedt_project/datasheet_figs/:
  - view_iso.png        isometrica do board completo (copper solido)
  - view_iso_zoom.png   isometrica com zoom no resonador
  - view_top.png        vista de cima do board completo
  - view_top_zoom.png   vista de cima com zoom no resonador
  - geometry.json       vertices/bboxes reais (mm) para desenho
                         dimensionado de fabricacao (gerado em outro
                         script a partir deste JSON)

Uso:
    .venv\\Scripts\\python.exe scripts\\export_geometry_views.py
"""

import json
from pathlib import Path

from ansys.aedt.core import Desktop, Hfss

BASE = Path(r"D:\my_projects\resonator_rogers_ro_5880\aedt_project")
OUT_DIR = BASE / "datasheet_figs"
OUT_DIR.mkdir(exist_ok=True)

COPPER = "(184 115 51)"  # cor de exibicao "cobre" so para a foto

d = Desktop(new_desktop=False, student_version=True, close_on_exit=False)

try:
    hfss = Hfss(project=str(BASE / "RessoadorQuadrado.aedt"), design="HFSSDesign1")
    mod = hfss.modeler

    objs = {
        "Substrate_RO5880": mod["Substrate_RO5880"],
        "Square_Spiral": mod["Square_Spiral"],
        "Feedline": mod["Feedline"],
        "Port_Sheet": mod["Port_Sheet"],
        "ground": mod["ground"],
    }

    def top_face_outline(obj, z_hint=None):
        """Contorno 2D (x,y) ordenado da face planar de maior Z (face de
        cima real da placa de cobre) - usa a topologia da face (nao a
        nuvem de vertices do solido) para preservar a ordem do polígono,
        essencial numa espiral (forma nao-convexa)."""
        best = None
        for face in obj.faces:
            zs = {round(v.position[2], 6) for v in face.vertices}
            if len(zs) != 1:
                continue
            z = next(iter(zs))
            if z_hint is not None and abs(z - z_hint) > 1e-6:
                continue
            if best is None or z > best[0]:
                best = (z, [list(v.position)[:2] for v in face.vertices])
        return best  # (z, [[x,y], ...]) ou None

    # --- 1. Extrai geometria real (read-only) para o desenho de fabricacao ---
    geometry = {}
    for name, obj in objs.items():
        z_top, outline = top_face_outline(obj) or (None, None)
        geometry[name] = {
            "bounding_box": obj.bounding_box,
            "vertices": [list(v.position) for v in obj.vertices],
            "top_face_z_mm": z_top,
            "top_face_outline_xy_mm": outline,
        }
    with open(OUT_DIR / "geometry.json", "w") as f:
        json.dump(geometry, f, indent=2)
    print(f"Geometria salva em: {OUT_DIR / 'geometry.json'}")

    # --- 2. Override cosmetico temporario (restaurado no finally) ---
    spiral = objs["Square_Spiral"]
    feed = objs["Feedline"]
    original = {
        "spiral_wireframe": spiral.display_wireframe,
        "spiral_color": spiral.color,
        "feed_color": feed.color,
    }

    spiral.display_wireframe = False
    spiral.color = COPPER
    feed.color = COPPER

    # --- 3. Screenshots em alta resolucao ---
    mod.fit_all()
    hfss.post.export_model_picture(
        full_name=str(OUT_DIR / "view_iso.png"), orientation="isometric",
        show_axis=True, show_grid=False, show_ruler=True,
        width=2400, height=2400,
    )
    hfss.post.export_model_picture(
        full_name=str(OUT_DIR / "view_top.png"), orientation="top",
        show_axis=True, show_grid=False, show_ruler=True,
        width=2400, height=2400,
    )
    hfss.post.export_model_picture(
        full_name=str(OUT_DIR / "view_iso_zoom.png"), orientation="isometric",
        show_axis=True, show_grid=False, show_ruler=True,
        selections=["Square_Spiral", "Feedline", "Substrate_RO5880"],
        width=2400, height=2400,
    )
    hfss.post.export_model_picture(
        full_name=str(OUT_DIR / "view_top_zoom.png"), orientation="top",
        show_axis=True, show_grid=False, show_ruler=True,
        selections=["Square_Spiral", "Feedline"],
        width=2400, height=2400,
    )
    print(f"Imagens salvas em: {OUT_DIR}")

finally:
    # --- 4. Restaura o display original (nada fica alterado no projeto) ---
    try:
        spiral.display_wireframe = original["spiral_wireframe"]
        spiral.color = original["spiral_color"]
        feed.color = original["feed_color"]
    except Exception as e:
        print(f"AVISO: falha ao restaurar display original: {e}")
    d.release_desktop(close_projects=False, close_on_exit=False)
