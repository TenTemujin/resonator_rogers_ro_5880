"""
ANTENA OMEGA DE UMA PORTA em substrato de ALUMINA, para ODMR de centros
NV em diamante (2.87 GHz).

MUDANCA DE ESPECIFICACAO (2026-09-18) em relacao a omega_antenna_nv.py:
  * 1 PORTA, nao 2. A perna que antes ia a um segundo porto agora vai a
    CURTO com o plano de terra (folha PEC vertical, equivalente a uma
    via metalizada) - so sobra UMA perna de alimentacao real (Port1).
    Topologia identica ao build_omega() de nv_resonators_compare.py,
    que ja implementava esse "uma perna + curto".
  * SUBSTRATO = ALUMINA (eps_r=9.8, tan_delta=1e-4), RO5880 fora do
    projeto inteiramente - nao e superstrato, e o substrato principal.
  * SEM superstrato de nenhum tipo (nem alumina em cima, nem outra
    camada) - so alumina embaixo do condutor, ar em cima.
  * TODAS as medidas de fabricacao (gap entre pernas, largura de
    trilhas) tem que ficar ACIMA de 0.5 mm - processo sem LPKF
    (corrosao/fabricacao simples, nao litografia). r_hole (abertura
    para a amostra) tambem >= 0.5 mm.

ESTIMATIVA ANALITICA DE PARTIDA (nv_resonators_compare.py usa a mesma
logica para RO5880): ressonancia de laco em curto quando o PERIMETRO
~ meio comprimento de onda guiado.
    lambda0 @ 2.87 GHz = 104.46 mm
    trilha de laco ~1.5mm em alumina 0.67mm -> eps_eff ~ 7.14
    lambda_g = lambda0/sqrt(eps_eff) ~ 39.1 mm
    perimetro ~ lambda_g/2 ~ 19.5 mm  ->  R_loop ~ 3.11 mm
Ou seja, em alumina o laco fica MUITO menor que em RO5880 (~6 mm la),
porque eps_eff e quase 4x maior. Ponto de partida: R_loop = 3.1 mm.

Verificacao de compatibilidade com a regra dos 0.5 mm (ver
check_geometry abaixo, roda antes de abrir o AEDT):
    r_hole   = 0.55 mm  (> 0.5)
    gap_leg  = 0.60 mm  (> 0.5, separacao entre as duas pernas)
    w_tr     = 1.50 mm  (trilha do laco, bem acima de 0.5)
    w_leg    = 1.00 mm  (perna curta, bem acima de 0.5)
    Wf       = 0.70 mm  (linha de alimentacao; ~50 ohm em alumina/0.67mm
               fica perto de W=h=0.67mm por formula de microfita simples
               -> arredondado para 0.70mm, ainda > 0.5mm)
Nenhuma medida fica abaixo de 0.5 mm nos valores de partida. A
otimizacao abaixo mantem essas variaveis dentro de faixas que
preservam essa margem (minimo absoluto 0.5mm com folga).

Requisitos: AEDT 2022 R2+ e pyaedt >= 1.0 (ansys.aedt.core).
Uso: python omega_alumina_1port.py
"""

from ansys.aedt.core import Hfss

PROJECT_NAME = "Omega_Alumina_1Port_2p87GHz"
F0_GHZ = 2.87
MIN_FEATURE_MM = 0.5   # piso de fabricacao (sem LPKF)

H_SUB = 0.67
EPS_SUB = 9.8
TAND_SUB = 1e-4

L_SUB = 18.0
W_SUB = 16.0
L_GND = 26.0            # plano de terra = porta-amostra, maior que o substrato
W_GND = 24.0

R_HOLE = 0.55            # raio da abertura (regiao de campo util)
R_LOOP = 3.10             # raio medio do laco (estimativa analitica)
W_TR = 1.50               # largura da trilha do laco
GAP_LEG = 0.60            # separacao entre as duas pernas (> 0.5mm)
W_LEG = 1.00              # largura da perna em curto
LEG_LEN = 2.50            # comprimento da perna em curto
WF = 0.70                 # largura da linha de alimentacao (~50 ohm)

AIRGAP = 27.0             # > lambda0/4 = 26.11 mm
F_START, F_STOP, F_STEP = 2.0, 4.0, 0.01
TOP_CLEARANCE = H_SUB + 1.0 + 5.0


def check_geometry():
    problems = []
    feats = dict(r_hole=R_HOLE, gap_leg=GAP_LEG, w_tr=W_TR,
                 w_leg=W_LEG, Wf=WF, leg_len=LEG_LEN)
    for name, val in feats.items():
        if val <= MIN_FEATURE_MM:
            problems.append(f"{name}={val}mm <= piso de fabricacao "
                             f"{MIN_FEATURE_MM}mm")

    if 2 * (R_LOOP + W_TR) >= min(L_SUB, W_SUB):
        problems.append("laco nao cabe no substrato")
    if R_LOOP - W_TR / 2 <= R_HOLE:
        problems.append(f"trilha invade a abertura "
                         f"(R_in={R_LOOP - W_TR/2:.2f} <= r_hole={R_HOLE})")
    x_short = -(R_LOOP - W_TR) - LEG_LEN
    if x_short <= -L_SUB / 2 + 1.0:
        problems.append(f"curto em x={x_short:.2f} cai fora do substrato "
                         f"(borda em x={-L_SUB/2:.2f})")
    y_feed_max = GAP_LEG / 2 + WF
    if y_feed_max >= W_SUB / 2:
        problems.append("linha de alimentacao sai da placa em y")
    c = 299.792458
    if AIRGAP < c / F0_GHZ / 4:
        problems.append(f"airgap {AIRGAP} < lambda0/4 = {c/F0_GHZ/4:.2f} mm")

    if problems:
        raise SystemExit("VERIFICACAO FALHOU:\n  - " + "\n  - ".join(problems))

    print("Verificacao geometrica OK - todas as medidas > "
          f"{MIN_FEATURE_MM} mm")
    for name, val in feats.items():
        print(f"  {name:8s} = {val} mm")
    print(f"  substrato  : {L_SUB} x {W_SUB} x {H_SUB} mm, alumina "
          f"eps_r={EPS_SUB}")
    print(f"  laco       : R_loop={R_LOOP} mm, w_tr={W_TR} mm -> "
          f"raio interno {R_LOOP - W_TR/2:.2f} mm")
    print(f"  curto em x = {x_short:.2f} mm")
    print()


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


def build_omega_1port(hfss):
    """Omega de UMA PORTA: uma perna alimenta (Port1), a outra vai a curto."""

    hfss["h_sub"] = f"{H_SUB}mm"
    hfss["L_sub"] = f"{L_SUB}mm"
    hfss["W_sub"] = f"{W_SUB}mm"
    hfss["L_gnd"] = f"{L_GND}mm"
    hfss["W_gnd"] = f"{W_GND}mm"
    hfss["r_hole"] = f"{R_HOLE}mm"
    hfss["R_loop"] = f"{R_LOOP}mm"
    hfss["w_tr"] = f"{W_TR}mm"
    hfss["gap_leg"] = f"{GAP_LEG}mm"
    hfss["w_leg"] = f"{W_LEG}mm"
    hfss["leg_len"] = f"{LEG_LEN}mm"
    hfss["Wf"] = f"{WF}mm"
    hfss["airgap"] = f"{AIRGAP}mm"

    sub = get_or_create_material(hfss, "Alumina_995", EPS_SUB, TAND_SUB)

    # substrato de alumina
    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=sub)

    # plano de terra = porta-amostra, maior que o substrato
    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_gnd/2", "-W_gnd/2", "0mm"],
        sizes=["L_gnd", "W_gnd"], name="Ground")
    hfss.assign_perfecte_to_sheets(ground.name)

    # --- laco: anel de (R_loop - w_tr/2) ate (R_loop + w_tr/2) ---
    outer = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop + w_tr/2", name="Omega_outer")
    inner = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop - w_tr/2", name="Omega_inner")
    hfss.modeler.subtract(outer, [inner], keep_originals=False)

    # abertura para a amostra: o raio interno do laco (R_loop - w_tr/2)
    # JA e a regiao vazia de acesso optico/de campo - r_hole so
    # documenta esse valor (checado em check_geometry), nao precisa de
    # geometria propria.

    # --- gap: separa o laco em -x nas duas pernas ---
    opening = hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-(R_loop + w_tr)", "-gap_leg/2", "h_sub"],
        sizes=["w_tr + 1mm", "gap_leg"], name="Omega_opening")
    hfss.modeler.subtract(outer, [opening], keep_originals=False)

    # perna SUPERIOR = linha de alimentacao, ate a borda do substrato
    hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "gap_leg/2", "h_sub"],
        sizes=["L_sub/2 - R_loop + w_tr", "Wf"], name="Omega_feed")

    # perna INFERIOR = trecho curto ate o plano de terra
    hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-(R_loop - w_tr) - leg_len", "-gap_leg/2 - w_leg", "h_sub"],
        sizes=["leg_len", "w_leg"], name="Omega_leg")

    hfss.modeler.unite([outer, hfss.modeler["Omega_feed"],
                        hfss.modeler["Omega_leg"]])
    outer.name = "Conductor"
    hfss.assign_perfecte_to_sheets(outer.name)

    # CURTO da perna inferior para o terra (via equivalente)
    short = hfss.modeler.create_rectangle(
        orientation="YZ",
        origin=["-(R_loop - w_tr) - leg_len", "-gap_leg/2 - w_leg", "0mm"],
        sizes=["w_leg", "h_sub"], name="Short_sheet")
    hfss.assign_perfecte_to_sheets(short.name)

    # UNICA porta, alinhada com a perna de alimentacao
    port = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "gap_leg/2", "0mm"],
        sizes=["Wf", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=port.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")

    # malha local restrita ao gap (mesma logica do RO5880: nao refinar
    # o condutor inteiro, so uma caixa em volta do gap)
    gap_margin = max(GAP_LEG * 2, 0.3)
    try:
        gap_region = hfss.modeler.create_box(
            origin=["-(R_loop + w_tr + 0.5mm)",
                    f"-(gap_leg/2 + {gap_margin}mm)", "h_sub - 0.001mm"],
            sizes=["R_loop + w_tr + 0.5mm",
                   f"gap_leg + {2*gap_margin}mm", "0.001mm"],
            name="Mesh_Region_Gap", material="vacuum")
        gap_region.is_model = False
        hfss.mesh.assign_length_mesh(
            [gap_region.name], maximum_length="gap_leg/4", name="Mesh_Gap")
    except Exception as e:
        print(f"  aviso: malha do gap nao criada automaticamente ({e}).")

    # --- airbox e setup ---
    airbox = hfss.modeler.create_box(
        origin=["-L_gnd/2-airgap", "-W_gnd/2-airgap", "-airgap"],
        sizes=["L_gnd+2*airgap", "W_gnd+2*airgap",
               f"{TOP_CLEARANCE}mm+2*airgap"],
        name="Airbox", material="air")
    hfss.assign_radiation_boundary_to_objects(airbox.name)

    hfss.create_setup(name="Setup1", setup_type="HFSSDriven",
                      Frequency=f"{F0_GHZ}GHz",
                      MaximumPasses=20, MaxDeltaS=0.02)
    hfss.create_linear_step_sweep(
        setup="Setup1", unit="GHz",
        start_frequency=F_START, stop_frequency=F_STOP, step_size=F_STEP,
        name="Sweep1", sweep_type="Interpolating")


def add_optimization(hfss):
    """Otimizacao continua (Quasi-Newton) em torno da estimativa analitica.

    R_loop e a alavanca dominante (mesmo padrao observado no RO5880:
    o raio do laco domina a frequencia). w_tr entra tambem por dar
    folga extra ao otimizador. gap_leg e Wf ficam FIXOS pois ja estao
    perto do piso de 0.5mm - nao ha margem segura para deixa-los livres
    sem risco de cruzar o piso de fabricacao durante a busca.
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["R_loop", "w_tr"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-20,
        goal_weight=1,
        name="Opt_1port_alumina_2p87GHz")
    setup.add_variation(
        "R_loop", min_value=2.0, max_value=4.5, starting_point=R_LOOP)
    setup.add_variation(
        "w_tr", min_value=1.0, max_value=2.0, starting_point=W_TR)
    return setup


if __name__ == "__main__":
    import csv

    check_geometry()

    hfss = Hfss(project=PROJECT_NAME, design="Omega_Alumina_1Port",
               solution_type="DrivenModal", new_desktop=True,
               non_graphical=True)
    build_omega_1port(hfss)
    add_optimization(hfss)
    hfss.save_project()
    print("Projeto criado em:", hfss.project_file)

    # solve + extracao, na MESMA sessao (evita o bug de persistencia
    # entre sessoes gRPC separadas observado ao reabrir o projeto salvo
    # de um script diferente - o design as vezes nao sobrevive ao
    # fechamento da sessao)
    print("\nAnalisando Setup1 (malha adaptada + sweep)...")
    hfss.analyze_setup("Setup1")

    sol_db = hfss.post.get_solution_data(
        expressions="dB(S(Port1,Port1))",
        setup_sweep_name="Setup1 : Sweep1")
    freqs = sol_db.primary_sweep_values
    mag_db = sol_db.full_matrix_real_imag[0]["dB(S(Port1,Port1))"][:, -1]

    sol_phase = hfss.post.get_solution_data(
        expressions="ang_deg(S(Port1,Port1))",
        setup_sweep_name="Setup1 : Sweep1")
    phase_deg = sol_phase.full_matrix_real_imag[0][
        "ang_deg(S(Port1,Port1))"][:, -1]

    out_csv = (r"D:\my_projects\resonator_rogers_ro_5880\aedt_project"
               r"\S11_alumina_1port.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Freq_GHz", "dB_S11", "Phase_S11_deg", "VSWR"])
        for fr, db, ph in zip(freqs, mag_db, phase_deg):
            gamma = 10 ** (db / 20)
            vswr = (1 + gamma) / (1 - gamma) if gamma < 1 else float("inf")
            w.writerow([fr, db, ph, vswr])
    print(f"CSV salvo em {out_csv}")

    closest_idx = min(range(len(freqs)),
                      key=lambda i: abs(freqs[i] - F0_GHZ))
    print(f"\nFreq mais proxima de {F0_GHZ} GHz: "
          f"{freqs[closest_idx]:.4f} GHz")
    print(f"dB(S11) nesse ponto: {mag_db[closest_idx]:.3f} dB")

    min_idx = min(range(len(mag_db)), key=lambda i: mag_db[i])
    print(f"\nMinimo global do sweep: {mag_db[min_idx]:.3f} dB em "
          f"{freqs[min_idx]:.4f} GHz")

    hfss.save_project()
    hfss.release_desktop(close_projects=False, close_desktop=False)
    print("\nOK.")
    print("Rode o Setup1 (S11 em torno de 2.0-4.0 GHz) e depois o "
          "Optimetrics 'Opt_1port_alumina_2p87GHz' para convergir em "
          "2.87 GHz mantendo gap_leg/Wf fixos acima do piso de 0.5mm.")
