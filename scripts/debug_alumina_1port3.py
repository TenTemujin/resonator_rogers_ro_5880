from ansys.aedt.core import Hfss

import omega_alumina_1port as base

hfss = Hfss(project=base.PROJECT_NAME, design="Omega_Alumina_1Port",
           solution_type="DrivenModal", new_desktop=True,
           non_graphical=True)
base.build_omega_1port(hfss)
hfss.save_project()

hfss.modeler.fit_all()

# vista de cima, so os condutores relevantes (sem airbox/substrate)
pic_path = (r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"
            r"\model_top_zoom.jpg")
hfss.post.export_model_picture(
    full_name=pic_path, show_axis=True, show_grid=False,
    show_ruler=True, orientation="top",
    selections=["Conductor", "Short_sheet", "Port1_sheet", "Ground"])
print("Screenshot salvo em", pic_path)

hfss.release_desktop(close_projects=False, close_desktop=False)
print("OK")
