"""
OMEGA de UMA PORTA em alumina, com ALIMENTACAO POR TAP (derivacao) no laco,
para ressoar em 2.87 GHz com S11 < -5 dB (alvo: ~ -20 a -30 dB).

POR QUE A TOPOLOGIA ANTERIOR (omega_alumina_1port.py) NAO PODIA CASAR
  A perna de alimentacao entrava numa ponta do laco e a outra ponta ia a
  curto. Vista pela porta, isso e uma linha em curto: Zin = jZc*tan(bl),
  puramente reativa. Sem perda relevante (PEC, tan_d = 1e-4) o modulo de
  S11 fica ~1 (-0.02 dB) em QUALQUER frequencia e QUALQUER R_loop - por
  isso o sweep e a otimizacao nunca acharam mergulho. Nao e problema de
  ajuste fino, e de topologia: a resistencia de entrada na ressonancia e
  ou ~0 (serie) ou ~milhares de ohms (paralelo), nunca ~50 ohm.

O QUE MUDA AQUI
  1. Laco ABERTO (fenda do gap em +x), sem curto: ressonador de meia onda
     aberto-aberto. A ressonancia e ajustada por R_loop.
  2. Alimentacao por TAP no lado oposto (-x), deslocada y_tap do eixo.
     Em y_tap = 0 o tap cai no no de tensao do modo (acoplamento nulo);
     quanto maior y_tap, menor a resistencia vista -> y_tap ajusta o
     acoplamento ate ~50 ohm (acoplamento critico = S11 mais fundo).
  3. Condutor e plano de terra em COBRE (condutividade finita, 5.8e7 S/m)
     em vez de PEC: sem perda nao existe absorcao e S11 nunca cai.
     Q do cobre ~ centenas -> mergulho com largura de dezenas de MHz.

  Regra dos 0.5 mm mantida (gap, w_tr, Wf, r_hole).
"""

from ansys.aedt.core import Hfss

PROJECT_NAME = "Omega_Alumina_Tapped_2p87GHz"
DESIGN_NAME = "Omega_Alumina_Tapped"
F0_GHZ = 2.87
MIN_FEATURE_MM = 0.5

H_SUB = 0.67
EPS_SUB = 9.8
TAND_SUB = 1e-4
SIGMA_CU = 5.8e7

L_SUB = 18.0
W_SUB = 16.0
L_GND = 26.0
W_GND = 24.0

R_HOLE = 0.55
R_LOOP = 3.0
W_TR = 1.50
GAP_LEG = 0.60          # fenda do laco (em +x)
Y_TAP = 1.0             # deslocamento do tap em relacao ao eixo x
WF = 0.70

AIRGAP = 27.0           # > lambda0/4 = 26.11 mm
F_START, F_STOP, F_STEP = 2.7, 3.1, 0.005
TOP_CLEARANCE = H_SUB + 1.0 + 5.0


def check_geometry(r_loop=R_LOOP, y_tap=Y_TAP, w_tr=W_TR):
    problems = []
    feats = dict(r_hole=R_HOLE, gap=GAP_LEG, w_tr=w_tr, Wf=WF)
    for name, val in feats.items():
        if val <= MIN_FEATURE_MM:
            problems.append(f"{name}={val}mm <= {MIN_FEATURE_MM}mm")
    if r_loop - w_tr / 2 <= R_HOLE:
        problems.append("trilha invade a abertura")
    if 2 * (r_loop + w_tr / 2) >= min(L_SUB, W_SUB):
        problems.append("laco nao cabe no substrato")
    # o canto externo do tap tem que ficar dentro da faixa do anel, senao
    # o feed nao fecha contato / sobra ponta solta fora do anel
    r_out = (r_loop ** 2 + (y_tap + WF / 2) ** 2) ** 0.5
    r_in = (r_loop ** 2 + max(y_tap - WF / 2, 0) ** 2) ** 0.5
    if r_out > r_loop + w_tr / 2:
        problems.append(f"canto externo do tap (r={r_out:.2f}) fora do anel")
    if r_in < r_loop - w_tr / 2:
        problems.append("tap invade a abertura")
    if y_tap + WF / 2 >= W_SUB / 2:
        problems.append("feed sai da placa")
    if problems:
        raise SystemExit("VERIFICACAO FALHOU:\n  - " + "\n  - ".join(problems))


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


def build(hfss):
    hfss["h_sub"] = f"{H_SUB}mm"
    hfss["L_sub"] = f"{L_SUB}mm"
    hfss["W_sub"] = f"{W_SUB}mm"
    hfss["L_gnd"] = f"{L_GND}mm"
    hfss["W_gnd"] = f"{W_GND}mm"
    hfss["R_loop"] = f"{R_LOOP}mm"
    hfss["w_tr"] = f"{W_TR}mm"
    hfss["gap"] = f"{GAP_LEG}mm"
    hfss["y_tap"] = f"{Y_TAP}mm"
    hfss["Wf"] = f"{WF}mm"
    hfss["airgap"] = f"{AIRGAP}mm"

    sub = get_or_create_material(hfss, "Alumina_995", EPS_SUB, TAND_SUB)
    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"], name="Substrate", material=sub)

    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_gnd/2", "-W_gnd/2", "0mm"],
        sizes=["L_gnd", "W_gnd"], name="Ground")
    hfss.assign_finite_conductivity(
        ground.name, conductivity=SIGMA_CU, is_two_side=True, name="Cu_gnd")

    # anel com fenda em +x
    outer = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop + w_tr/2", name="Omega_outer")
    inner = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_loop - w_tr/2", name="Omega_inner")
    hfss.modeler.subtract(outer, [inner], keep_originals=False)
    opening = hfss.modeler.create_rectangle(
        orientation="XY", origin=["R_loop - w_tr", "-gap/2", "h_sub"],
        sizes=["2*w_tr", "gap"], name="Omega_opening")
    hfss.modeler.subtract(outer, [opening], keep_originals=False)

    # feed horizontal em y = y_tap, do borda -x ate x = -R_loop (dentro da
    # faixa do anel enquanto y_tap + Wf/2 <= ~1.9 mm p/ R_loop ~ 3 mm)
    feed = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "y_tap - Wf/2", "h_sub"],
        sizes=["L_sub/2 - R_loop", "Wf"], name="Omega_feed")
    hfss.modeler.unite([outer, feed])
    outer.name = "Conductor"
    hfss.assign_finite_conductivity(
        outer.name, conductivity=SIGMA_CU, is_two_side=True, name="Cu_trace")

    port = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "y_tap - Wf/2", "0mm"],
        sizes=["Wf", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=port.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")

    try:
        reg = hfss.modeler.create_box(
            origin=["R_loop - w_tr - 0.5mm", "-2*gap", "h_sub - 0.001mm"],
            sizes=["2*w_tr + 1mm", "4*gap", "0.001mm"],
            name="Mesh_Region_Gap", material="vacuum")
        reg.is_model = False
        hfss.mesh.assign_length_mesh(
            [reg.name], maximum_length="gap/4", name="Mesh_Gap")
    except Exception as e:
        print(f"  aviso: malha do gap nao criada ({e})")

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


def read_s11(hfss):
    sol = hfss.post.get_solution_data(
        expressions="dB(S(Port1,Port1))", setup_sweep_name="Setup1 : Sweep1")
    freqs = list(sol.primary_sweep_values)
    db = list(sol.full_matrix_real_imag[0]["dB(S(Port1,Port1))"][:, -1])
    return freqs, db


def summarize(freqs, db):
    i0 = min(range(len(freqs)), key=lambda i: abs(freqs[i] - F0_GHZ))
    im = min(range(len(db)), key=lambda i: db[i])
    return db[i0], db[im], freqs[im]
