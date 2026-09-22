"""
Grade (R_loop x y_tap) do Omega_Alumina_Tapped, tudo numa sessao HFSS.
Salva cada curva S11 em aedt_project/tapped_sweep/ e imprime, por ponto:
dB(S11) exatamente em 2.87 GHz E o minimo real (frequencia do vale).
Uso: python sweep_alumina_tapped.py [R1,R2,...] [Y1,Y2,...]
"""
import csv
import os
import sys

from ansys.aedt.core import Hfss

import omega_alumina_tapped as base

OUT = r"D:\my_projects\resonator_rogers_ro_5880\aedt_project\tapped_sweep"
os.makedirs(OUT, exist_ok=True)

R_VALUES = [float(v) for v in sys.argv[1].split(",")] if len(sys.argv) > 1 \
    else [2.7, 3.0, 3.3]
Y_VALUES = [float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 \
    else [0.5, 1.0, 1.5]

if __name__ == "__main__":
    hfss = Hfss(project=base.PROJECT_NAME, design=base.DESIGN_NAME,
               solution_type="DrivenModal", new_desktop=True,
               non_graphical=True)
    base.build(hfss)
    hfss.save_project()
    print("modelo construido", flush=True)

    rows = []
    for r in R_VALUES:
        for y in Y_VALUES:
            try:
                base.check_geometry(r_loop=r, y_tap=y)
            except SystemExit as e:
                print(f"R={r} y={y}: PULADO ({e})", flush=True)
                continue
            hfss["R_loop"] = f"{r}mm"
            hfss["y_tap"] = f"{y}mm"
            try:
                hfss.analyze_setup("Setup1")
                f, db = base.read_s11(hfss)
            except Exception as e:
                print(f"R={r} y={y}: FALHOU {e}", flush=True)
                continue
            at, mn, fmn = base.summarize(f, db)
            rows.append((r, y, at, mn, fmn))
            print(f"R={r:.2f} y_tap={y:.2f} | S11@2.87={at:8.3f} dB | "
                  f"min={mn:8.3f} dB @ {fmn:.3f} GHz", flush=True)
            with open(os.path.join(OUT, f"S11_R{r}_y{y}.csv"), "w",
                      newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["Freq_GHz", "dB_S11"])
                w.writerows(zip(f, db))

    hfss.save_project()
    hfss.release_desktop(close_projects=True, close_desktop=True)
    print("OK", flush=True)
