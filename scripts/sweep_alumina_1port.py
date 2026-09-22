"""
Varredura de R_loop no Omega_Alumina_1Port (1 porta, substrato de
alumina), TUDO em UMA sessao continua do HFSS (evita o bug de reabrir
projeto salvo, ver historico em omega_alumina_1port.py).

A estimativa analitica (R_loop=3.1mm) NAO ressoou: dB(S11)@2.87GHz =
-0.023 dB, minimo global do sweep so -0.099 dB em 3.87 GHz - ou seja, a
formula de eps_eff simples errou a escala. Varredura ampla para achar
a janela real, igual ao que foi feito para o RO5880 (ver README/
memoria do projeto: levou 5 rodadas la).

Le dB(S11) EXATAMENTE em 2.87 GHz a cada ponto, no CSV/solution_data
exportado - nunca so o "vale mais fundo" (pode ser outro modo).
"""

from ansys.aedt.core import Hfss

import omega_alumina_1port as base

F0_GHZ = base.F0_GHZ

# faixa ampla: do minimo que ainda respeita r_hole+w_tr/2 folga ate um
# raio que ainda cabe na placa 18x16mm com margem
R_LOOP_VALUES = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

if __name__ == "__main__":
    base.check_geometry()

    hfss = Hfss(project=base.PROJECT_NAME, design="Omega_Alumina_1Port",
               solution_type="DrivenModal", new_desktop=True,
               non_graphical=True)
    base.build_omega_1port(hfss)
    hfss.save_project()
    print("Modelo base construido. Iniciando varredura de R_loop...\n")

    results = []
    for r in R_LOOP_VALUES:
        hfss["R_loop"] = f"{r}mm"
        print(f"--- R_loop = {r} mm ---")
        try:
            hfss.analyze_setup("Setup1")
            sol = hfss.post.get_solution_data(
                expressions="dB(S(Port1,Port1))",
                setup_sweep_name="Setup1 : Sweep1")
            freqs = sol.primary_sweep_values
            mag_db = sol.full_matrix_real_imag[0][
                "dB(S(Port1,Port1))"][:, -1]
            closest_idx = min(range(len(freqs)),
                              key=lambda i: abs(freqs[i] - F0_GHZ))
            min_idx = min(range(len(mag_db)), key=lambda i: mag_db[i])
            at_f0 = mag_db[closest_idx]
            min_val = mag_db[min_idx]
            min_freq = freqs[min_idx]
            print(f"  dB(S11)@{F0_GHZ}GHz = {at_f0:.3f} dB   "
                  f"| minimo real = {min_val:.3f} dB em {min_freq:.3f} GHz")
            results.append((r, at_f0, min_val, min_freq))
        except Exception as e:
            print(f"  FALHOU: {e}")
            results.append((r, None, None, None))

    print("\n===== RESUMO =====")
    print(f"{'R_loop(mm)':>10} | {'dB(S11)@2.87':>13} | "
          f"{'min_dB':>8} | {'freq_min(GHz)':>13}")
    for r, at_f0, min_val, min_freq in results:
        if at_f0 is None:
            print(f"{r:>10.2f} | FALHOU")
        else:
            print(f"{r:>10.2f} | {at_f0:>13.3f} | {min_val:>8.3f} | "
                  f"{min_freq:>13.3f}")

    hfss.save_project()
    hfss.release_desktop(close_projects=False, close_desktop=False)
    print("\nOK.")
