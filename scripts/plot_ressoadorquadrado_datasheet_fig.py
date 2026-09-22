"""
Gera a FIGURA UNICA de desempenho eletrico do datasheet do
RessoadorQuadrado (S11 + VSWR vs frequencia, com zoom da ressonancia
em inset) - usada uma unica vez no relatorio LaTeX, para evitar
graficos repetidos.

Fonte de dados: aedt_project/ressoadorquadrado.csv (S11 dB, exportado
do HFSS). Somente leitura - nao abre nem altera o projeto AEDT.

Uso:
    .venv\\Scripts\\python.exe scripts\\plot_ressoadorquadrado_datasheet_fig.py
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

BASE = Path(r"D:\my_projects\resonator_rogers_ro_5880\aedt_project")
S11_CSV = BASE / "ressoadorquadrado.csv"
OUT_DIR = BASE / "datasheet_figs"
OUT_DIR.mkdir(exist_ok=True)
OUT_PNG = OUT_DIR / "fig_s11_vswr.png"

TARGET_FREQ_GHZ = 2.87
RL_THRESHOLD_DB = -10.0

freqs, s11_db = [], []
with open(S11_CSV, newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        freqs.append(float(row[0]))
        s11_db.append(float(row[1]))

s11_lin = [10 ** (v / 20.0) for v in s11_db]
vswr = [((1 + g) / (1 - g)) if g < 1 else float("inf") for g in s11_lin]

i_min = min(range(len(s11_db)), key=lambda i: s11_db[i])
f0, s11_f0 = freqs[i_min], s11_db[i_min]
i_target = min(range(len(freqs)), key=lambda i: abs(freqs[i] - TARGET_FREQ_GHZ))
f_target, s11_target = freqs[i_target], s11_db[i_target]

plt.rcParams.update({
    "font.size": 9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
})

fig, ax1 = plt.subplots(figsize=(6.4, 4.0))

l1, = ax1.plot(freqs, s11_db, color="#00296b", linewidth=1.4, label=r"$S_{11}$ (dB)")
ax1.axhline(RL_THRESHOLD_DB, color="#c1121f", linestyle=":", linewidth=1)
ax1.axvline(TARGET_FREQ_GHZ, color="#6c757d", linestyle="--", linewidth=1)
ax1.plot(f0, s11_f0, "v", color="black", markersize=6)
ax1.set_xlabel("Frequência (GHz)")
ax1.set_ylabel(r"$S_{11}$ (dB)", color="#00296b")
ax1.tick_params(axis="y", labelcolor="#00296b")
ax1.set_xlim(freqs[0], freqs[-1])
ax1.grid(alpha=0.25)

ax2 = ax1.twinx()
l2, = ax2.plot(freqs, vswr, color="#2a9d8f", linewidth=1.1, linestyle="--",
               label="VSWR", alpha=0.85)
ax2.set_ylabel("VSWR", color="#2a9d8f")
ax2.tick_params(axis="y", labelcolor="#2a9d8f")
ax2.set_yscale("log")
ax2.set_ylim(1, 1000)

ax1.legend([l1, l2, ax1.lines[1]],
           [r"$S_{11}$ (dB)", "VSWR",
            f"limiar {RL_THRESHOLD_DB:.0f} dB / alvo {TARGET_FREQ_GHZ:.2f} GHz"],
           loc="lower right", fontsize=7.5, framealpha=0.9)

# --- inset: zoom na regiao de ressonancia ---
axins = ax1.inset_axes([0.10, 0.55, 0.38, 0.4])
lo, hi = TARGET_FREQ_GHZ - 0.25, TARGET_FREQ_GHZ + 0.25
mask = [i for i, f in enumerate(freqs) if lo <= f <= hi]
axins.plot([freqs[i] for i in mask], [s11_db[i] for i in mask],
           color="#00296b", linewidth=1.2)
axins.axvline(TARGET_FREQ_GHZ, color="#6c757d", linestyle="--", linewidth=0.8)
axins.axhline(RL_THRESHOLD_DB, color="#c1121f", linestyle=":", linewidth=0.8)
axins.plot(f0, s11_f0, "v", color="black", markersize=5)
axins.set_xlim(lo, hi)
axins.tick_params(labelsize=6.5)
axins.set_title("zoom na ressonância", fontsize=6.5)
axins.grid(alpha=0.25)
ax1.indicate_inset_zoom(axins, edgecolor="#555555")

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300)
print(f"Salvo: {OUT_PNG}")
print(f"f0={f0:.4f} GHz S11@f0={s11_f0:.3f} dB | "
      f"S11@{TARGET_FREQ_GHZ}GHz={s11_target:.3f} dB")
