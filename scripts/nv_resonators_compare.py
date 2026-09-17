"""
ESTUDO COMPARATIVO DE TOPOLOGIAS - ressoador de micro-ondas para ODMR
de centros NV em diamante.  f0 = 2.87 GHz (zero-field splitting do NV-)
Substrato: Rogers RT/duroid 5880, 0.75 mm.

Constroi DUAS topologias no MESMO projeto, com placa, airbox, setup e
varredura identicos, para que qualquer diferenca observada venha da
topologia e nao das condicoes de simulacao.

  (A) ANEL FENDIDO  (split-ring / loop-gap)
      Anel condutor continuo com furo central e UMA fenda radial.
      Circuito LC serie: L do laco, C da fenda.
      Alimentacao: microfita de 50 ohm encostando na borda externa.
      Referencia: Sasaki et al., Rev. Sci. Instrum. 87, 053904 (2016);
      parametros em Misonou et al., RSI 91, 023703 (2020) [arXiv:2002.02113]
      (Antena #1: f=2.790 GHz, r=0.5, R+s=10.9, g=0.1 mm, em FR4 1.6 mm)

  (B) OMEGA
      Laco NAO fechado: abre-se em duas pernas paralelas que saem para -x.
      Uma perna e a propria linha de 50 ohm (alimentacao);
      a outra vai a CURTO para o plano de terra (folha PEC vertical,
      equivalente a uma via metalizada).
      Laco em curto -> ressonancia quando o perimetro ~ meio comprimento
      de onda guiado. Com eps_eff ~ 1.8 em RO5880/0.75mm:
          lambda_g ~ 78 mm  ->  2*pi*R_loop ~ 39 mm  ->  R_loop ~ 6 mm
      (ponto de partida; o valor final sai da varredura)

EM AMBAS o campo util e B1 PERPENDICULAR ao plano dentro do furo central,
que e o que gira o spin do NV. O S11 sozinho NAO valida o projeto - e
preciso inspecionar o campo (ver secao 6).

AVISO SOBRE A OMEGA: diferente do anel fendido, nao encontrei um projeto
publicado com dimensoes tabeladas em 2.87 GHz que eu pudesse transferir.
A geometria abaixo e uma implementacao parametrica consistente com a
descricao da topologia, a ser dimensionada por varredura. Trate-a como
candidata a comparar, nao como reproducao de um resultado da literatura.

Requisitos: AEDT 2022 R2+ e pyaedt >= 1.0 (import via ansys.aedt.core).
Uso: python nv_resonators_compare.py
"""

from ansys.aedt.core import Hfss

# ---------------------------------------------------------------
# 1. Parametros comuns (mm)
# ---------------------------------------------------------------
PROJECT_NAME = "NV_Resonators_Ring_vs_Omega_2p87GHz"
F0_GHZ = 2.87

H_SUB = 0.75
EPS_SUB = 2.20
TAND_SUB = 0.0009

L_SUB = 70.0          # placa fixa, comum as duas topologias
W_SUB = 60.0

WF = 2.3              # microfita de 50 ohm em RO5880 / 0.75 mm
R_HOLE = 0.5          # raio do furo (acesso optico) - comum as duas

AIRGAP = 28.0         # > lambda0/4 = 26.1 mm
F_START, F_STOP, F_STEP = 2.5, 3.3, 0.002

# --- (A) anel fendido ---
R_OUT = 13.0          # raio externo        <-- varrer 8..18 mm
G_SLOT = 0.1          # largura da fenda radial
FEED_OVERLAP = 0.5    # penetracao da linha no anel

# --- (B) omega ---
R_LOOP = 6.0          # raio medio do laco  <-- varrer 3..12 mm
W_TR = 1.5            # largura da trilha do laco
GAP_LEG = 0.5         # separacao entre as duas pernas
W_LEG = 1.5           # largura da perna em curto
LEG_LEN = 6.0         # comprimento da perna em curto

# --- alumina (opcional; deixe False na primeira rodada) ---
BUILD_ALUMINA = False
EPS_AL = 9.8
TAND_AL = 0.0001
ALUMINA_CASES = {
    "Al25x25x0p67": dict(La=25.0, Wa=25.0, ha=0.67),
    "Al25x50x1p3":  dict(La=25.0, Wa=50.0, ha=1.30),
    # a placa de 50x50 cobre parte da microfita em qualquer posicao que
    # caiba na placa; incluir so se voce aceitar esse efeito no S11
}
X_ALUMINA = 0.0

TOP_CLEARANCE = H_SUB + 1.3 + 5.0


# ---------------------------------------------------------------
# 2. Verificacao geometrica (roda ANTES de abrir o AEDT)
# ---------------------------------------------------------------
def check_geometry():
    c = 299.792458
    p = []

    # --- anel ---
    if 2 * 18.0 >= min(L_SUB, W_SUB):
        p.append("anel: R_out=18mm (topo da varredura) nao cabe na placa")
    feed_ring = L_SUB / 2 - 18.0 + FEED_OVERLAP
    if feed_ring <= 1.0:
        p.append(f"anel: microfita curta demais ({feed_ring:.1f} mm)")
    if R_OUT <= R_HOLE + 5 * G_SLOT:
        p.append("anel: R_out pequeno demais em relacao ao furo/fenda")

    # --- omega ---
    r_ext = R_LOOP + W_TR / 2
    if 2 * 12.0 + W_TR >= min(L_SUB, W_SUB):
        p.append("omega: R_loop=12mm (topo da varredura) nao cabe na placa")
    if R_LOOP - W_TR / 2 <= R_HOLE:
        p.append(f"omega: trilha invade o furo "
                 f"(R_in={R_LOOP - W_TR/2:.2f} <= r_hole={R_HOLE})")
    x_short = -(R_LOOP - W_TR) - LEG_LEN
    if x_short <= -L_SUB / 2 + 2.0:
        p.append(f"omega: curto em x={x_short:.1f} cai sobre a porta "
                 f"(x={-L_SUB/2:.1f})")
    y_feed_max = GAP_LEG / 2 + WF
    if y_feed_max >= W_SUB / 2:
        p.append("omega: linha de alimentacao fora da placa em y")

    # --- comum ---
    if AIRGAP < c / F0_GHZ / 4:
        p.append(f"airgap {AIRGAP} < lambda0/4 = {c/F0_GHZ/4:.1f} mm")

    if BUILD_ALUMINA:
        for n, d in ALUMINA_CASES.items():
            x0 = X_ALUMINA - d["La"] / 2
            if x0 <= -L_SUB / 2 + 2.0:
                p.append(f"{n}: alcanca a regiao da porta")
            if (X_ALUMINA + d["La"] / 2 > L_SUB / 2
                    or d["Wa"] / 2 > W_SUB / 2):
                p.append(f"{n}: transborda a placa")

    if p:
        raise SystemExit("VERIFICACAO FALHOU:\n  - " + "\n  - ".join(p))

    print("Verificacao geometrica OK")
    print(f"  placa      : {L_SUB} x {W_SUB} x {H_SUB} mm  (comum)")
    print(f"  (A) anel   : r_hole={R_HOLE} R_out={R_OUT} g={G_SLOT}")
    print(f"               microfita = {L_SUB/2-R_OUT+FEED_OVERLAP:.1f} mm")
    print(f"  (B) omega  : R_loop={R_LOOP} w_tr={W_TR} gap={GAP_LEG} "
          f"leg={LEG_LEN}")
    print(f"               furo efetivo = {R_LOOP - W_TR/2:.2f} mm de raio")
    print(f"               curto em x = {x_short:.1f} mm")
    print(f"  alumina    : {'SIM' if BUILD_ALUMINA else 'nao (1a rodada)'}")
    print()


# ---------------------------------------------------------------
# 3. Blocos comuns
# ---------------------------------------------------------------
def get_or_create_material(hfss, name, eps_r, tand):
    try:
        mat = hfss.materials[name]
    except Exception:
        mat = None
    if mat is None:
        mat = hfss.materials.add_material(name)
        mat.permittivity = str(eps_r)
        mat.dielectric_loss_tangent = str(tand)
        mat.update()
    return mat.name


def common_variables(hfss):
    hfss["h_sub"] = f"{H_SUB}mm"
    hfss["L_sub"] = f"{L_SUB}mm"
    hfss["W_sub"] = f"{W_SUB}mm"
    hfss["Wf"] = f"{WF}mm"
    hfss["r_hole"] = f"{R_HOLE}mm"
    hfss["airgap"] = f"{AIRGAP}mm"


def build_substrate_and_ground(hfss):
    ro5880 = get_or_create_material(hfss, "RO5880_custom", EPS_SUB, TAND_SUB)
    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=ro5880)
    ground = hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub"], name="Ground")
    hfss.assign_perfecte_to_sheets(ground.name)


def add_airbox_and_setup(hfss):
    airbox = hfss.modeler.create_box(
        origin=["-L_sub/2-airgap", "-W_sub/2-airgap", "-airgap"],
        sizes=["L_sub+2*airgap", "W_sub+2*airgap",
               f"{TOP_CLEARANCE}mm+2*airgap"],
        name="Airbox", material="air")
    hfss.assign_radiation_boundary_to_objects(airbox.name)
    hfss.create_setup(
        name="Setup1", setup_type="HFSSDriven",
        Frequency=f"{F0_GHZ}GHz", MaximumPasses=15, MaxDeltaS=0.01)
    hfss.create_linear_step_sweep(
        setup="Setup1", unit="GHz",
        start_frequency=F_START, stop_frequency=F_STOP, step_size=F_STEP,
        name="Sweep1", sweep_type="Interpolating")


def add_alumina(hfss, La, Wa, ha, tag):
    alumina = get_or_create_material(hfss, "Alumina_995_custom",
                                     EPS_AL, TAND_AL)
    hfss[f"La_{tag}"] = f"{La}mm"
    hfss[f"Wa_{tag}"] = f"{Wa}mm"
    hfss[f"ha_{tag}"] = f"{ha}mm"
    hfss[f"xal_{tag}"] = f"{X_ALUMINA}mm"
    hfss.modeler.create_box(
        origin=[f"xal_{tag} - La_{tag}/2", f"-Wa_{tag}/2", "h_sub"],
        sizes=[f"La_{tag}", f"Wa_{tag}", f"ha_{tag}"],
        name=f"Alumina_{tag}", material=alumina)


# ---------------------------------------------------------------
# 4A. Topologia A - anel fendido
# ---------------------------------------------------------------
def build_ring(hfss):
    common_variables(hfss)
    hfss["R_out"] = f"{R_OUT}mm"
    hfss["g_slot"] = f"{G_SLOT}mm"
    build_substrate_and_ground(hfss)

    ring = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_out", name="Ring_disc")
    hole = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="r_hole", name="Hole")
    hfss.modeler.subtract(ring, [hole], keep_originals=False)

    # fenda radial: interrompe o anel de lado a lado, em +x
    slot = hfss.modeler.create_rectangle(
        orientation="XY", origin=["0mm", "-g_slot/2", "h_sub"],
        sizes=["R_out + 1mm", "g_slot"], name="Slot")
    hfss.modeler.subtract(ring, [slot], keep_originals=False)

    # microfita de 50 ohm entrando por -x (oposto a fenda)
    hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-Wf/2", "h_sub"],
        sizes=[f"L_sub/2 - R_out + {FEED_OVERLAP}mm", "Wf"],
        name="Feed_line")
    hfss.modeler.unite([ring, hfss.modeler["Feed_line"]])
    ring.name = "Conductor"
    hfss.assign_perfecte_to_sheets(ring.name)

    port = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "-Wf/2", "0mm"],
        sizes=["Wf", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=port.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")


# ---------------------------------------------------------------
# 4B. Topologia B - omega
# ---------------------------------------------------------------
def build_omega(hfss):
    common_variables(hfss)
    hfss["R_loop"] = f"{R_LOOP}mm"
    hfss["w_tr"] = f"{W_TR}mm"
    hfss["gap_leg"] = f"{GAP_LEG}mm"
    hfss["w_leg"] = f"{W_LEG}mm"
    hfss["leg_len"] = f"{LEG_LEN}mm"
    build_substrate_and_ground(hfss)

    # anel (trilha de largura w_tr, raio medio R_loop)
    outer = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop + w_tr/2", name="Omega_outer")
    inner = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop - w_tr/2", name="Omega_inner")
    hfss.modeler.subtract(outer, [inner], keep_originals=False)

    # abertura em -x: separa o laco em duas extremidades
    opening = hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-(R_loop + w_tr)", "-gap_leg/2", "h_sub"],
        sizes=["w_tr + 1mm", "gap_leg"], name="Omega_opening")
    hfss.modeler.subtract(outer, [opening], keep_originals=False)

    # perna SUPERIOR = propria linha de 50 ohm, ate a borda da placa
    hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-L_sub/2", "gap_leg/2", "h_sub"],
        sizes=["L_sub/2 - R_loop + w_tr", "Wf"], name="Omega_feed")

    # perna INFERIOR = trecho curto que vai ao terra
    hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-(R_loop - w_tr) - leg_len", "-gap_leg/2 - w_leg", "h_sub"],
        sizes=["leg_len", "w_leg"], name="Omega_leg")

    hfss.modeler.unite([outer, hfss.modeler["Omega_feed"],
                        hfss.modeler["Omega_leg"]])
    outer.name = "Conductor"
    hfss.assign_perfecte_to_sheets(outer.name)

    # CURTO da perna inferior para o terra (equivale a uma via)
    short = hfss.modeler.create_rectangle(
        orientation="YZ",
        origin=["-(R_loop - w_tr) - leg_len", "-gap_leg/2 - w_leg", "0mm"],
        sizes=["w_leg", "h_sub"], name="Short_sheet")
    hfss.assign_perfecte_to_sheets(short.name)

    # porta na borda, alinhada com a perna alimentada
    port = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "gap_leg/2", "0mm"],
        sizes=["Wf", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=port.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")


# ---------------------------------------------------------------
# 5. Execucao
# ---------------------------------------------------------------
TOPOLOGIES = {"Ring": build_ring, "Omega": build_omega}

if __name__ == "__main__":

    check_geometry()

    first = True
    hfss = None
    for topo, builder in TOPOLOGIES.items():
        if first:
            hfss = Hfss(project=PROJECT_NAME, design=f"{topo}_Unloaded",
                        solution_type="DrivenModal", new_desktop=True,
                        non_graphical=False)
            first = False
        else:
            hfss.insert_design(name=f"{topo}_Unloaded",
                               solution_type="DrivenModal")
        builder(hfss)
        add_airbox_and_setup(hfss)

        if BUILD_ALUMINA:
            for case, d in ALUMINA_CASES.items():
                hfss.insert_design(name=f"{topo}_{case}",
                                   solution_type="DrivenModal")
                builder(hfss)
                add_alumina(hfss, d["La"], d["Wa"], d["ha"], case)
                add_airbox_and_setup(hfss)

    hfss.save_project()
    print("Projeto criado em:", hfss.project_file)
    print("Designs:", list(hfss.design_list))

    # hfss.release_desktop()


# ---------------------------------------------------------------
# 6. PROTOCOLO DE COMPARACAO (no HFSS)
# ---------------------------------------------------------------
# PASSO 0 - INSPECAO VISUAL, antes de qualquer analise.
#   Esconda Airbox e Substrate. Confirme:
#     Ring  : a fenda interrompe o anel de lado a lado (senao nao ha C)
#     Omega : as duas pernas estao separadas pelo gap e NAO se tocam;
#             a folha de curto liga a perna inferior ao terra
#
# PASSO 1 - dimensionar cada topologia para 2.87 GHz (separadamente):
#   Ring : Optimetrics > Parametric, R_out  de  8 a 18 mm, passo 0.5
#   Omega: Optimetrics > Parametric, R_loop de  3 a 12 mm, passo 0.25
#   Relatorio: Primary Sweep = variavel, Y = XAtYMin(dB(S(Port1,Port1)))
#   Marque "Copy geometrically equivalent meshes" na aba Options.
#
# PASSO 2 - comparar as duas em pe de igualdade, com 4 metricas:
#   (i)   f0 e profundidade do S11 (casamento)
#   (ii)  LARGURA DE BANDA a -10 dB  -> precisa cobrir o desdobramento
#         Zeeman; em 4.7 mT as transicoes ficam em ~2.74 e ~3.00 GHz
#   (iii) |B1| no centro do furo, por watt de entrada
#   (iv)  UNIFORMIDADE de B1 sobre a area do diamante (desvio percentual)
#
# PASSO 3 - o campo, que e a figura de merito real:
#   crie um plano XY na altura do diamante (z = h_sub + folga)
#   HFSS > Fields > Plot Fields > H > Vector_H, Setup1 : LastAdaptive
#   Confirme que H e predominantemente PERPENDICULAR (Hz) no furo.
#   Para quantificar: Fields Calculator > Mag_H > integrar/amostrar sobre
#   a area do diamante e comparar max/min.
#
# PASSO 4 - so entao ative BUILD_ALUMINA = True e reconstrua, para medir
#   o deslocamento de f0 causado pela placa em cada topologia.
#
# NOTA sobre a versao Student: sao 2 designs (ou 6 com alumina) com airbox
# de ~920 cm3. Se bater no limite de malha, reduza AIRGAP para 26.5 mm
# (ainda > lambda0/4) ou a placa para 60x50 mm.
