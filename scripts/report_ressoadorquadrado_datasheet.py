"""
DATASHEET - RessoadorQuadrado (espiral quadrada acoplada, RO5880)

Gera um PDF multi-pagina tipo "datasheet" de projeto, reunindo:
  1. Capa com parametros de projeto (geometria, material, setup HFSS)
     e figuras de merito extraidas do S11 medido/simulado.
  2. Curva completa de S11 (2-4 GHz) com f0 e faixa de -10dB marcadas.
  3. VSWR (escala log) na mesma faixa.
  4. Zoom em torno da ressonancia + foto do modelo (se disponivel).

SOMENTE LEITURA em relacao ao projeto AEDT: os parametros de projeto
sao extraidos por parsing de texto do arquivo .aedt (VariableProp,
blocos de Setup/Sweep/Boundaries), sem abrir o projeto no HFSS/pyaedt
e sem escrever nada nele. Os dados de S11 vem do CSV ja exportado
(aedt_project/ressoadorquadrado.csv). Nada no projeto e alterado.

Uso:
    .venv\\Scripts\\python.exe scripts\\report_ressoadorquadrado_datasheet.py
"""

import csv
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

BASE = Path(r"D:\my_projects\resonator_rogers_ro_5880\aedt_project")
AEDT_FILE = BASE / "RessoadorQuadrado.aedt"
S11_CSV = BASE / "ressoadorquadrado.csv"
MODEL_JPG = BASE / "ressoadorquadrado.jpg"
OUT_PDF = BASE / "datasheet_ressoadorquadrado.pdf"

TARGET_FREQ_GHZ = 2.87  # zero-field splitting do NV- em diamante
RL_THRESHOLD_DB = -10.0  # referencia usual de "bom casamento"


# ---------------------------------------------------------------
# 1. Parametros de projeto - extraidos do .aedt por parsing de texto
#    (read-only: nenhuma escrita no arquivo, projeto nao e aberto)
# ---------------------------------------------------------------
def load_aedt_text():
    return AEDT_FILE.read_text(errors="ignore")


def extract_variables(text):
    """VariableProp('nome', 'UD', '', 'valor') -> dict nome: valor (str)."""
    out = {}
    for name, value in re.findall(r"VariableProp\('([A-Za-z0-9_]+)',\s*'UD',\s*'',\s*'([^']*)'\)", text):
        out[name] = value
    return out


def extract_setup_info(text):
    info = {}
    m = re.search(r"\$begin 'Setup1'.*?SolveType='([^']*)'.*?Frequency='([^']*)'.*?"
                   r"MaxDeltaS=([\d.]+).*?MaximumPasses=(\d+)", text, re.S)
    if m:
        info["solve_type"] = m.group(1)
        info["adaptive_freq"] = m.group(2)
        info["max_delta_s"] = m.group(3)
        info["max_passes"] = m.group(4)
    m = re.search(r"\$begin 'Sweep'.*?RangeType='([^']*)'.*?RangeStart='([^']*)'.*?"
                   r"RangeEnd='([^']*)'.*?RangeCount=(\d+).*?Type='([^']*)'", text, re.S)
    if m:
        info["sweep_type"] = m.group(1)
        info["sweep_start"] = m.group(2)
        info["sweep_end"] = m.group(3)
        info["sweep_count"] = m.group(4)
        info["sweep_kind"] = m.group(5)
    return info


def extract_materials(text):
    mats = sorted(set(re.findall(r"MaterialValue='\"([^\"]+)\"'", text)))
    return [m for m in mats if m]


def extract_port_info(text):
    ports = sorted(set(re.findall(r"\$begin '(Port\d+)'", text)))
    port_type = "Lumped Port" if "'Lumped Port'" in text else "?"
    network = "HFSS Terminal Network" if "HFSS Terminal Network" in text else "?"
    return ports, port_type, network


aedt_text = load_aedt_text()
variables = extract_variables(aedt_text)
setup_info = extract_setup_info(aedt_text)
materials = extract_materials(aedt_text)
ports, port_type, network_type = extract_port_info(aedt_text)


# ---------------------------------------------------------------
# 2. Dados S11 (curva completa 2-4 GHz, exportada do HFSS)
# ---------------------------------------------------------------
freqs, s11_db = [], []
with open(S11_CSV, newline="") as f:
    reader = csv.reader(f)
    next(reader)  # header
    for row in reader:
        freqs.append(float(row[0]))
        s11_db.append(float(row[1]))

s11_lin = [10 ** (v / 20.0) for v in s11_db]
vswr = [((1 + g) / (1 - g)) if g < 1 else float("inf") for g in s11_lin]

# f0 = ponto de minimo (melhor casamento) na faixa medida
i_min = min(range(len(s11_db)), key=lambda i: s11_db[i])
f0 = freqs[i_min]
s11_at_f0 = s11_db[i_min]

# valor no ponto alvo (2.87 GHz) - o ponto que realmente importa para NV
i_target = min(range(len(freqs)), key=lambda i: abs(freqs[i] - TARGET_FREQ_GHZ))
f_target = freqs[i_target]
s11_at_target = s11_db[i_target]
vswr_at_target = vswr[i_target]

# banda onde S11 <= -10dB (banda de "bom casamento")
below = [f for f, v in zip(freqs, s11_db) if v <= RL_THRESHOLD_DB]
if below:
    bw_lo, bw_hi = min(below), max(below)
    bw_mhz = (bw_hi - bw_lo) * 1000
    q_loaded = f0 / ((bw_hi - bw_lo) if bw_hi > bw_lo else float("nan"))
else:
    bw_lo = bw_hi = bw_mhz = q_loaded = float("nan")


# ---------------------------------------------------------------
# 3. Figuras
# ---------------------------------------------------------------
def page_cover(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle("DATASHEET DE PROJETO\nRessoadorQuadrado (espiral quadrada acoplada)",
                 fontsize=14, fontweight="bold", y=0.97)

    lines = []
    lines.append("GEOMETRIA (variaveis de projeto no HFSS)")
    geo_labels = [
        ("a_spiral", "Lado externo da espiral"),
        ("w_spiral", "Largura da trilha"),
        ("g_spiral", "Espacamento entre voltas"),
        ("p_spiral", "Passo (pitch = w+g)"),
        ("z_spiral", "Deslocamento vertical / offset"),
        ("t_cu", "Espessura do cobre"),
        ("L_sub", "Lado do substrato"),
        ("h_sub", "Espessura do substrato"),
        ("w_feed", "Largura da linha de alimentacao"),
        ("g_cpl", "Gap de acoplamento (feed-espiral)"),
        ("L_cpl", "Comprimento de acoplamento"),
    ]
    for key, desc in geo_labels:
        if key in variables:
            lines.append(f"  {key:10s} = {variables[key]:12s}  ({desc})")

    lines.append("")
    lines.append("MATERIAIS")
    for m in materials:
        lines.append(f"  - {m}")

    lines.append("")
    lines.append("PORTA / EXCITACAO")
    lines.append(f"  Porta(s): {', '.join(ports) if ports else '?'}")
    lines.append(f"  Tipo de porta: {port_type}")
    lines.append(f"  Tipo de rede: {network_type}")

    lines.append("")
    lines.append("SETUP DE SOLUCAO (HFSS)")
    if setup_info:
        lines.append(f"  Solve type: {setup_info.get('solve_type', '?')}")
        lines.append(f"  Freq. adaptativa: {setup_info.get('adaptive_freq', '?')}")
        lines.append(f"  Max Delta S: {setup_info.get('max_delta_s', '?')}")
        lines.append(f"  Max. passes: {setup_info.get('max_passes', '?')}")
        lines.append(f"  Sweep: {setup_info.get('sweep_start', '?')} - "
                     f"{setup_info.get('sweep_end', '?')}, "
                     f"{setup_info.get('sweep_count', '?')} pontos "
                     f"({setup_info.get('sweep_kind', '?')})")

    lines.append("")
    lines.append("FIGURAS DE MERITO (extraidas de ressoadorquadrado.csv)")
    lines.append(f"  Faixa medida: {freqs[0]:.3f} - {freqs[-1]:.3f} GHz "
                 f"({len(freqs)} pontos)")
    lines.append(f"  f0 (minimo de S11 na faixa): {f0:.4f} GHz  "
                 f"-> S11 = {s11_at_f0:.3f} dB")
    lines.append(f"  S11 em {TARGET_FREQ_GHZ:.2f} GHz (alvo NV-): "
                 f"{s11_at_target:.3f} dB  (freq. real lida: {f_target:.3f} GHz)")
    lines.append(f"  VSWR em {TARGET_FREQ_GHZ:.2f} GHz: {vswr_at_target:.2f}")
    if below:
        lines.append(f"  Banda com S11 <= {RL_THRESHOLD_DB:.0f} dB: "
                     f"{bw_lo:.3f} - {bw_hi:.3f} GHz "
                     f"(BW = {bw_mhz:.1f} MHz, Q_loaded ~ {q_loaded:.0f})")
    else:
        lines.append(f"  Nenhum ponto da faixa atinge S11 <= {RL_THRESHOLD_DB:.0f} dB "
                     "(casamento ainda fraco nesta faixa).")

    fig.text(0.08, 0.90, "\n".join(lines), family="monospace", fontsize=8.3,
             va="top", ha="left")
    pdf.savefig(fig)
    plt.close(fig)


def page_s11_vswr(pdf):
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 11), sharex=True)

    axes[0].plot(freqs, s11_db, color="tab:blue", linewidth=1.2)
    axes[0].axvline(TARGET_FREQ_GHZ, color="gray", linestyle="--", linewidth=1,
                    label=f"{TARGET_FREQ_GHZ:.2f} GHz (alvo NV-)")
    axes[0].axhline(RL_THRESHOLD_DB, color="tab:red", linestyle=":", linewidth=1,
                    label=f"{RL_THRESHOLD_DB:.0f} dB (ref. bom casamento)")
    axes[0].plot(f0, s11_at_f0, "v", color="black", markersize=8,
                 label=f"f0 = {f0:.3f} GHz ({s11_at_f0:.2f} dB)")
    axes[0].set_ylabel("dB(S11)")
    axes[0].set_title("RessoadorQuadrado - S11 vs frequencia (varredura completa)")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)

    axes[1].plot(freqs, vswr, color="tab:green", linewidth=1.2)
    axes[1].axvline(TARGET_FREQ_GHZ, color="gray", linestyle="--", linewidth=1)
    axes[1].set_ylabel("VSWR (escala log)")
    axes[1].set_xlabel("Frequencia (GHz)")
    axes[1].set_yscale("log")
    axes[1].grid(alpha=0.3, which="both")

    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def page_zoom_and_model(pdf):
    fig = plt.figure(figsize=(8.5, 11))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])

    ax = fig.add_subplot(gs[0])
    lo, hi = TARGET_FREQ_GHZ - 0.3, TARGET_FREQ_GHZ + 0.3
    mask = [i for i, f in enumerate(freqs) if lo <= f <= hi]
    fz = [freqs[i] for i in mask]
    sz = [s11_db[i] for i in mask]
    ax.plot(fz, sz, color="tab:blue", linewidth=1.4)
    ax.axvline(TARGET_FREQ_GHZ, color="gray", linestyle="--", linewidth=1,
              label=f"{TARGET_FREQ_GHZ:.2f} GHz (alvo)")
    ax.axhline(RL_THRESHOLD_DB, color="tab:red", linestyle=":", linewidth=1,
              label=f"{RL_THRESHOLD_DB:.0f} dB")
    ax.plot(f0, s11_at_f0, "v", color="black", markersize=8)
    ax.set_xlabel("Frequencia (GHz)")
    ax.set_ylabel("dB(S11)")
    ax.set_title(f"Zoom em torno da ressonancia ({lo:.2f} - {hi:.2f} GHz)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    if MODEL_JPG.exists():
        img = plt.imread(MODEL_JPG)
        ax2.imshow(img)
        ax2.set_title("Vista do modelo / plot exportado do HFSS", fontsize=9)
    else:
        ax2.text(0.5, 0.5, "(imagem do modelo nao encontrada)",
                 ha="center", va="center")

    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


with PdfPages(OUT_PDF) as pdf:
    page_cover(pdf)
    page_s11_vswr(pdf)
    page_zoom_and_model(pdf)

print(f"Datasheet salvo em: {OUT_PDF}")
print(f"f0 = {f0:.4f} GHz | S11@f0 = {s11_at_f0:.3f} dB | "
      f"S11@{TARGET_FREQ_GHZ}GHz = {s11_at_target:.3f} dB | VSWR@alvo = {vswr_at_target:.2f}")
