"""
Abre o projeto Omega_Alumina_1Port_2p87GHz ja construido, roda o Setup1
(malha adaptada + sweep) e le dB(S11) EXATAMENTE em 2.87 GHz a partir da
solucao exportada - nao do "vale mais fundo" (pode ser outro modo, ja
visto no RO5880). Salva CSV com mag(dB), fase e VSWR para plot depois.

Design de 1 PORTA: so existe S11 (S(Port1,Port1)). Nao ha S21 porque
nao ha segundo porto - foi removido a pedido, a perna 2 vai a curto
para o terra.
"""

import csv

from ansys.aedt.core import Hfss

PROJECT_PATH = r"D:\Ansys HFSS\Projects\Omega_Alumina_1Port_2p87GHz.aedt"
DESIGN_NAME = "Omega_Alumina_1Port"
F0_GHZ = 2.87
OUT_CSV = (r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"
           r"\S11_alumina_1port.csv")

hfss = Hfss(project=PROJECT_PATH,
           non_graphical=True, new_desktop=True, remove_lock=True)
print("Design ativo:", hfss.design_name)

print("Analisando Setup1 (malha adaptada + sweep)...")
hfss.analyze_setup("Setup1")

sol_db = hfss.post.get_solution_data(
    expressions="dB(S(Port1,Port1))", setup_sweep_name="Setup1 : Sweep1")
freqs = sol_db.primary_sweep_values
mag_db = sol_db.data_real()

sol_phase = hfss.post.get_solution_data(
    expressions="ang_deg(S(Port1,Port1))",
    setup_sweep_name="Setup1 : Sweep1")
phase_deg = sol_phase.data_real()

with open(OUT_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Freq_GHz", "dB_S11", "Phase_S11_deg", "VSWR"])
    for fr, db, ph in zip(freqs, mag_db, phase_deg):
        gamma = 10 ** (db / 20)
        vswr = (1 + gamma) / (1 - gamma) if gamma < 1 else float("inf")
        w.writerow([fr, db, ph, vswr])
print(f"CSV salvo em {OUT_CSV}")

closest_idx = min(range(len(freqs)), key=lambda i: abs(freqs[i] - F0_GHZ))
print(f"\nFreq mais proxima de {F0_GHZ} GHz: {freqs[closest_idx]:.4f} GHz")
print(f"dB(S11) nesse ponto: {mag_db[closest_idx]:.3f} dB")

min_idx = min(range(len(mag_db)), key=lambda i: mag_db[i])
print(f"\nMinimo global do sweep: {mag_db[min_idx]:.3f} dB em "
      f"{freqs[min_idx]:.4f} GHz")

hfss.save_project()
hfss.release_desktop(close_projects=False, close_desktop=False)
print("\nOK.")
