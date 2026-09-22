"""
Plota os resultados ja obtidos para o Omega_Alumina_1Port (1 porta,
substrato de alumina, sem superstrato, piso de fabricacao 0.5mm):

  1. S11 (mag dB, fase, VSWR) vs frequencia - ponto inicial R_loop=3.1mm
     (dados salvos em aedt_project/S11_alumina_1port.csv)
  2. Resumo da varredura de R_loop (10 pontos, 1.5-6.0mm) - dB(S11) em
     2.87GHz e minimo real do sweep, por R_loop (dados transcritos do
     log da varredura, nao ha CSV bruto salvo desses pontos)

APENAS 1 PORTA -> so existe S11 (S(Port1,Port1)). Nao ha S21 porque a
perna 2 foi trocada por um curto para o terra (nao ha segundo porto).
"""

import csv

import matplotlib.pyplot as plt

BASE = r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"

# ---------------------------------------------------------------
# 1. Curva completa S11 (ponto inicial R_loop=3.1mm, w_tr=1.5mm)
# ---------------------------------------------------------------
freqs, mags, phases, vswrs = [], [], [], []
with open(f"{BASE}\\S11_alumina_1port.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        freqs.append(float(row["Freq_GHz"]))
        mags.append(float(row["dB_S11"]))
        phases.append(float(row["Phase_S11_deg"]))
        v = row["VSWR"]
        vswrs.append(float(v) if v != "inf" else float("nan"))

fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

axes[0].plot(freqs, mags, color="tab:blue")
axes[0].axvline(2.87, color="gray", linestyle="--", linewidth=1,
                label="2.87 GHz (alvo)")
axes[0].set_ylabel("dB(S11)")
axes[0].set_title("Omega_Alumina_1Port - R_loop=3.1mm, w_tr=1.5mm "
                  "(ponto de partida)")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(freqs, phases, color="tab:orange")
axes[1].axvline(2.87, color="gray", linestyle="--", linewidth=1)
axes[1].set_ylabel("Fase S11 (graus)")
axes[1].grid(alpha=0.3)

axes[2].plot(freqs, vswrs, color="tab:green")
axes[2].axvline(2.87, color="gray", linestyle="--", linewidth=1)
axes[2].set_ylabel("VSWR (escala log)")
axes[2].set_xlabel("Frequencia (GHz)")
axes[2].set_yscale("log")
axes[2].grid(alpha=0.3, which="both")

fig.tight_layout()
fig.savefig(f"{BASE}\\plot_S11_full_sweep.png", dpi=150)
print(f"Salvo: {BASE}\\plot_S11_full_sweep.png")

# ---------------------------------------------------------------
# 2. Resumo da varredura de R_loop (transcrito do log real do HFSS)
# ---------------------------------------------------------------
r_loop_sweep = [1.50, 2.00, 2.50, 3.00, 3.50, 4.00, 4.50, 5.00, 5.50, 6.00]
at_2p87 = [-0.012, -0.023, -0.023, -0.021, -0.030, -0.036, -0.041,
          -0.026, -0.020, -0.022]
min_db = [-0.089, -0.079, -0.088, -0.097, -0.093, -0.058, -0.083,
         -0.176, -0.312, -0.296]

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.plot(r_loop_sweep, at_2p87, "o-", color="tab:blue",
        label="dB(S11) @ 2.87 GHz")
ax2.plot(r_loop_sweep, min_db, "s--", color="tab:red",
        label="minimo real do sweep (qualquer freq)")
# ponto pos-otimizacao (Quasi-Newton, 27min, R_loop=3.654mm)
ax2.plot([3.654], [-0.032], "*", color="black", markersize=16,
        label="pos-otimizacao (R_loop=3.65, w_tr=1.29mm)")
ax2.axhline(-10, color="gray", linestyle=":", linewidth=1,
           label="-10 dB (referencia de bom casamento)")
ax2.set_xlabel("R_loop (mm)")
ax2.set_ylabel("dB(S11)")
ax2.set_title("Varredura de R_loop - nenhum ponto testado casa "
              "(escala note: eixo em dB, valores entre -0.01 e -0.3)")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3)
fig2.tight_layout()
fig2.savefig(f"{BASE}\\plot_Rloop_sweep_summary.png", dpi=150)
print(f"Salvo: {BASE}\\plot_Rloop_sweep_summary.png")
