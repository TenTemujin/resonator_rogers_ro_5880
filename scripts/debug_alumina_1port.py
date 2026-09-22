"""
Diagnostico do Omega_Alumina_1Port: por que dB(S11) fica preso perto de
0 dB em qualquer geometria/frequencia. Roda tudo em UMA sessao.

Verifica:
  1. Lista de boundaries (PerfE / Lumped Port / Radiation) e a quais
     objetos/faces estao atribuidas.
  2. Convergencia do Setup1 (numero de passes, delta S por pass) -
     se convergiu em 1-2 passes, e sinal de mesh trivial/insuficiente,
     nao de fisica real resolvida.
  3. Screenshot do modelo (para inspecao visual das conexoes porta/
     curto) salvo em aedt_project/.
"""

from ansys.aedt.core import Hfss

import omega_alumina_1port as base

hfss = Hfss(project=base.PROJECT_NAME, design="Omega_Alumina_1Port",
           solution_type="DrivenModal", new_desktop=True,
           non_graphical=True)
base.build_omega_1port(hfss)
hfss.save_project()

print("\n===== OBJETOS NO MODELO =====")
for name in hfss.modeler.object_names:
    obj = hfss.modeler[name]
    print(f"  {name:20s} material={getattr(obj, 'material_name', None)} "
          f"model={obj.is_model} faces={len(obj.faces)}")

print("\n===== BOUNDARIES =====")
for b in hfss.boundaries:
    print(f"  {b.name:20s} type={b.type} props={b.props}")

print("\n===== ANALISANDO (R_loop=6mm, melhor ponto ate agora) =====")
hfss["R_loop"] = "6.0mm"
hfss.analyze_setup("Setup1")

try:
    profile = hfss.setups[0].get_profile()
    print("\n===== PERFIL DE CONVERGENCIA (Setup1) =====")
    print(profile)
except Exception as e:
    print(f"Nao consegui ler o profile: {e}")

pic_path = (r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"
            r"\model_debug.jpg")
try:
    hfss.post.export_model_picture(full_name=pic_path, show_axis=True,
                                   show_grid=False, show_ruler=True)
    print(f"\nScreenshot salvo em {pic_path}")
except Exception as e:
    print(f"Nao consegui exportar screenshot: {e}")

hfss.save_project()
hfss.release_desktop(close_projects=False, close_desktop=False)
print("\nOK.")
