from ansys.aedt.core import Desktop

PROJECT_PATH = r"D:\Ansys HFSS\Projects\Omega_Alumina_1Port_2p87GHz.aedt"

d = Desktop(non_graphical=True, new_desktop=True)
oProject = d.odesktop.OpenProject(PROJECT_PATH)
print("Project:", oProject.GetName())
print("Designs:", list(oProject.GetTopDesignList()))
d.release_desktop(close_projects=False, close_desktop=False)
