"""
Roda de verdade a otimizacao Quasi-Newton (R_loop, w_tr) do
Omega_Alumina_1Port, numa unica sessao continua (build + optimize +
verificacao com solve fresco no ponto otimo, ver README/memoria do
projeto sobre nao confiar na leitura pos-otimizacao sem revalidar).
"""

from ansys.aedt.core import Hfss

import omega_alumina_1port as base

hfss = Hfss(project=base.PROJECT_NAME, design="Omega_Alumina_1Port",
           solution_type="DrivenModal", new_desktop=True,
           non_graphical=True)
base.build_omega_1port(hfss)
opt_setup = base.add_optimization(hfss)
hfss.save_project()

print("Rodando otimizacao Quasi-Newton (R_loop, w_tr) -> "
      "dB(S11)@2.87GHz <= -20 ...")
opt_setup.analyze()

print("\nOtimizacao terminou. Lendo variaveis de projeto pos-otimizacao...")
r_loop_opt = hfss["R_loop"]
w_tr_opt = hfss["w_tr"]
print(f"  R_loop = {r_loop_opt}")
print(f"  w_tr   = {w_tr_opt}")

# VERIFICACAO: solve fresco no ponto nominal, revertendo a malha, para
# nao pegar uma variacao vizinha da trajetoria do otimizador por engano
# (armadilha ja documentada no README do projeto para o RO5880)
print("\nRevalidando com solve fresco no ponto nominal...")
hfss.setups[0].analyze(revert_to_initial_mesh=True)

sol_db = hfss.post.get_solution_data(
    expressions="dB(S(Port1,Port1))", setup_sweep_name="Setup1 : Sweep1")
freqs = sol_db.primary_sweep_values
mag_db = sol_db.full_matrix_real_imag[0]["dB(S(Port1,Port1))"][:, -1]

closest_idx = min(range(len(freqs)), key=lambda i: abs(freqs[i] - base.F0_GHZ))
min_idx = min(range(len(mag_db)), key=lambda i: mag_db[i])
print(f"\ndB(S11) @ {base.F0_GHZ} GHz (ponto exato): "
      f"{mag_db[closest_idx]:.3f} dB")
print(f"Minimo real do sweep: {mag_db[min_idx]:.3f} dB em "
      f"{freqs[min_idx]:.4f} GHz")

hfss.save_project()
hfss.release_desktop(close_projects=False, close_desktop=False)
print("\nOK.")
