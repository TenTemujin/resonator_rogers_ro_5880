from ansys.aedt.core import Hfss

import omega_alumina_1port as base

hfss = Hfss(project=base.PROJECT_NAME, design="Omega_Alumina_1Port",
           solution_type="DrivenModal", new_desktop=True,
           non_graphical=True)
base.build_omega_1port(hfss)
hfss["R_loop"] = "6.0mm"
hfss.save_project()

hfss.modeler["Airbox"].display_wireframe = True
hfss.modeler.set_object_visibility = None  # no-op guard, real call below
try:
    hfss.odesign.SetObjectsVisibility(["NAME:VisibleObjects", "Conductor",
                                       "Short_sheet", "Port1_sheet",
                                       "Substrate"], False)
except Exception as e:
    print("SetObjectsVisibility falhou:", e)

# esconder Airbox e Ground via API de alto nivel do pyaedt
try:
    hfss.modeler.objects_by_name["Airbox"].display_wireframe = True
except Exception as e:
    print("wireframe airbox falhou:", e)

pic_path = (r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"
            r"\model_debug_zoom.jpg")
hfss.post.export_model_picture(
    full_name=pic_path, show_axis=True, show_grid=False,
    show_ruler=True, selections=["Conductor", "Short_sheet",
                                 "Port1_sheet", "Ground"])
print("Screenshot salvo em", pic_path)

hfss.release_desktop(close_projects=False, close_desktop=False)
print("OK")
