"""
ANTENA OMEGA DE DOIS PORTOS para ODMR de centros NV em diamante (2.87 GHz)

BASEADO EM (dimensoes publicadas):
  O. R. Opaluch, N. Oshnik, R. Nelz, E. Neu,
  "Optimized Planar Microwave Antenna for Nitrogen Vacancy Center Based
   Sensing Applications", Nanomaterials 11, 2108 (2021).
  doi:10.3390/nano11082108  |  arXiv:2108.09122

  Parametros otimizados no artigo (substrato de vidro borossilicato,
  eps_r = 4.82, espessura 1 mm; condutor: 20 nm Cr + 100 nm Au):
      raio da abertura  r_ap = 0.300 mm
      largura radial    r_w  = 1.151 mm
      largura do gap    g_w  = 0.007 mm   (7 micrometros!)
      largura da linha  f_w  = 1.851 mm
      substrato          16 mm x 11 mm
      porta-amostra de titanio 24 x 15 mm atuando como PLANO DE TERRA
  Resultados de referencia (para validar o modelo):
      ressonancias em 0.7, 2.6 e 5.5 GHz ; S11 = -47 dB na principal
      banda 8.2 GHz (diamante 50 um) / 6.3 GHz (diamante 300 um)
      campo majoritariamente perpendicular dentro de raio de 260 um
      |B| > 170 A/m no centro, ate 280 A/m perto da circunferencia (1 W)
      sensibilidade: -50 MHz/um no gap ; -20 MHz/um na largura radial

TOPOLOGIA (o que eu tinha errado antes):
  * DOIS PORTOS. A microfita entra, contorna a abertura e sai. Nao e um
    ressoador de um porto com perna em curto. Por isso a banda e enorme.
  * As partes LINEARES (as duas pernas paralelas separadas por g_w) sao
    o elemento CAPACITIVO; a parte RADIAL (o laco) e o INDUTIVO.
    Juntas determinam a ressonancia.
  * O campo util e B1 perpendicular ao plano, dentro da abertura.

>>> RESTRICAO DE FABRICACAO - LEIA ANTES DE SIMULAR <<<
  O gap de 7 um foi obtido por LITOGRAFIA UV em filme de ouro, nao por
  processo de PCB. Corrosao de placa convencional faz, no melhor caso,
  100-150 um. Alem disso os autores mediram -50 MHz/um de deslocamento
  por micrometro de gap: com 7 um nominal, +-1 um ja desloca 50 MHz.
  Essa tolerancia e inatingivel em PCB.
  => Portar para Rogers 5880 com gap de PCB NAO e um reescalonamento
     linear: exige reotimizacao numerica completa. O design B abaixo e
     o ponto de partida dessa reotimizacao, nao uma solucao pronta.

ESTRATEGIA DESTE SCRIPT - dois designs:
  (A) Omega_Ref_Glass : reproduz o artigo (vidro 1 mm, eps_r 4.82,
      dimensoes publicadas). Serve para VALIDAR o seu modelo HFSS
      contra um resultado conhecido antes de confiar em qualquer
      extrapolacao. Se o seu HFSS reproduzir ~-47 dB e as ressonancias
      em 0.7/2.6/5.5 GHz, o modelo esta correto.
  (B) Omega_RO5880    : mesma topologia nos SEUS materiais
      (Rogers 5880, 0.75 mm) com gap compativel com PCB, a ser
      otimizado por varredura.

Requisitos: AEDT 2022 R2+ e pyaedt >= 1.0 (ansys.aedt.core).
Uso: python omega_antenna_nv.py
"""

from ansys.aedt.core import Hfss

PROJECT_NAME = "Omega_Antenna_NV_Opaluch2021"
F0_GHZ = 2.87
AIRGAP = 26.0                 # ~lambda0/4, como no artigo
F_START, F_STOP, F_STEP = 0.5, 6.0, 0.005   # banda larga: ha varios modos

# ---------------------------------------------------------------
# DESIGN A - reproducao do artigo (vidro)
# ---------------------------------------------------------------
REF = dict(
    name="Omega_Ref_Glass",
    eps_sub=4.82, tand_sub=0.005, h_sub=1.0,   # vidro borossilicato
    L_sub=16.0, W_sub=11.0,
    r_ap=0.300,       # raio da abertura
    r_w=1.151,        # largura radial (indutivo)
    g_w=0.007,        # gap entre as pernas (capacitivo)  <-- 7 um
    f_w=1.851,        # largura da linha
)

# ---------------------------------------------------------------
# DESIGN B - portado para os materiais disponiveis
# ---------------------------------------------------------------
# g_w = 0.15 mm e o minimo realista de PCB. r_w e f_w sao chutes
# iniciais: f_w ~ 2.3 mm da ~50 ohm em RO5880/0.75mm. TUDO deve ser
# reotimizado; ver secao "DEPOIS" no rodape.
RO = dict(
    name="Omega_RO5880",
    eps_sub=2.20, tand_sub=0.0009, h_sub=0.75,  # Rogers RT/duroid 5880
    L_sub=16.0, W_sub=11.0,
    r_ap=0.300,
    r_w=1.151,        # <-- varrer
    g_w=0.150,        # <-- minimo de PCB
    f_w=2.300,        # 50 ohm em RO5880 / 0.75 mm
)


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


def build_omega(hfss, p):
    """Omega de dois portos: leito de entrada -> laco -> leito de saida."""

    hfss["h_sub"] = f"{p['h_sub']}mm"
    hfss["L_sub"] = f"{p['L_sub']}mm"
    hfss["W_sub"] = f"{p['W_sub']}mm"
    hfss["r_ap"] = f"{p['r_ap']}mm"
    hfss["r_w"] = f"{p['r_w']}mm"
    hfss["g_w"] = f"{p['g_w']}mm"
    hfss["f_w"] = f"{p['f_w']}mm"
    hfss["airgap"] = f"{AIRGAP}mm"

    sub = get_or_create_material(hfss, f"sub_{p['name']}",
                                 p["eps_sub"], p["tand_sub"])

    # substrato
    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=sub)

    # plano de terra (no artigo: porta-amostra de titanio sob o substrato)
    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub"], name="Ground")
    hfss.assign_perfecte_to_sheets(ground.name)

    # --- laco: anel de r_ap ate r_ap + r_w ---
    loop = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="r_ap + r_w", name="Loop")
    ap = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="r_ap", name="Aperture")
    hfss.modeler.subtract(loop, [ap], keep_originals=False)

    # --- gap: fenda de largura g_w abrindo o laco para -x ---
    # (elemento CAPACITIVO, junto com o trecho paralelo das pernas)
    gap = hfss.modeler.create_rectangle(
        orientation="XY",
        origin=["-(r_ap + r_w + 0.5mm)", "-g_w/2", "h_sub"],
        sizes=["r_ap + r_w + 0.5mm", "g_w"], name="Gap")
    hfss.modeler.subtract(loop, [gap], keep_originals=False)

    # --- duas pernas paralelas, separadas por g_w, ate a borda ---
    hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "g_w/2", "h_sub"],
        sizes=["L_sub/2 - r_ap", "f_w"], name="Lead_top")
    hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-g_w/2 - f_w", "h_sub"],
        sizes=["L_sub/2 - r_ap", "f_w"], name="Lead_bot")

    hfss.modeler.unite([loop, hfss.modeler["Lead_top"],
                        hfss.modeler["Lead_bot"]])
    loop.name = "Conductor"
    hfss.assign_perfecte_to_sheets(loop.name)

    # --- DOIS PORTOS, um na extremidade de cada perna ---
    p1 = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "g_w/2", "0mm"],
        sizes=["f_w", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=p1.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")

    p2 = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "-g_w/2 - f_w", "0mm"],
        sizes=["f_w", "h_sub"], name="Port2_sheet")
    hfss.lumped_port(assignment=p2.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port2")

    # --- malha local: sem isto o HFSS NAO resolve o gap ---
    # (critico no design de referencia, onde o gap tem 7 micrometros)
    try:
        hfss.mesh.assign_length_mesh(
            [loop.name], maximum_length=f"{max(p['g_w']*2, 0.02)}mm",
            name="Mesh_conductor")
    except Exception as e:
        print("  aviso: nao consegui criar a operacao de malha "
              f"automaticamente ({e}).")
        print("  Crie manualmente: HFSS > Mesh Operations > Assign >")
        print("  On Selection > Length Based, no objeto Conductor.")

    # --- airbox e setup ---
    airbox = hfss.modeler.create_box(
        origin=["-L_sub/2-airgap", "-W_sub/2-airgap", "-airgap"],
        sizes=["L_sub+2*airgap", "W_sub+2*airgap",
               f"{p['h_sub'] + 2}mm+2*airgap"],
        name="Airbox", material="air")
    hfss.assign_radiation_boundary_to_objects(airbox.name)

    hfss.create_setup(name="Setup1", setup_type="HFSSDriven",
                      Frequency=f"{F0_GHZ}GHz",
                      MaximumPasses=20, MaxDeltaS=0.02)
    hfss.create_linear_step_sweep(
        setup="Setup1", unit="GHz",
        start_frequency=F_START, stop_frequency=F_STOP, step_size=F_STEP,
        name="Sweep1", sweep_type="Interpolating")


def report(p):
    R_o = p["r_ap"] + p["r_w"]
    print(f"  {p['name']}")
    print(f"     substrato  eps_r={p['eps_sub']}  h={p['h_sub']} mm")
    print(f"     abertura   raio {p['r_ap']} mm (diametro "
          f"{2*p['r_ap']*1000:.0f} um)")
    print(f"     laco       raio externo {R_o:.3f} mm")
    print(f"     gap        {p['g_w']*1000:.0f} um")
    print(f"     pernas     largura {p['f_w']} mm")
    if p["g_w"] < 0.1:
        print("     >>> gap sub-100um: exige LITOGRAFIA, nao PCB <<<")
    print()


if __name__ == "__main__":

    print("Designs a construir:\n")
    report(REF)
    report(RO)

    hfss = Hfss(project=PROJECT_NAME, design=REF["name"],
                solution_type="DrivenModal", new_desktop=True,
                non_graphical=False)
    build_omega(hfss, REF)

    hfss.insert_design(name=RO["name"], solution_type="DrivenModal")
    build_omega(hfss, RO)

    hfss.save_project()
    print("Projeto criado em:", hfss.project_file)

    # hfss.release_desktop()


# ---------------------------------------------------------------
# DEPOIS, NO HFSS
# ---------------------------------------------------------------
# ORDEM IMPORTA. Rode A antes de B.
#
# (A) VALIDAR O MODELO contra a literatura - Omega_Ref_Glass
#     Rode e compare com Opaluch et al. 2021:
#       ressonancias esperadas em ~0.7, ~2.6 e ~5.5 GHz
#       S11 da ressonancia principal ~ -47 dB
#     Se voce NAO reproduzir isso, o problema esta no modelo
#     (malha no gap de 7 um, portas, plano de terra) e nao adianta
#     seguir para B. Suspeito numero um: malha. Refine a operacao
#     de malha no Conductor ate o resultado estabilizar.
#
#     Note que sao DOIS portos: olhe S11 E S21. Um elemento em linha
#     bem casado tem S21 alto fora das ressonancias.
#
# (B) PORTAR - Omega_RO5880
#     So depois que A validar. Varra, nesta ordem de influencia:
#       1. g_w   : 0.10 a 0.40 mm   (capacitivo - maior efeito)
#       2. r_w   : 0.5 a 3.0 mm     (indutivo)
#       3. f_w   : ajusta o casamento em 50 ohm
#     Optimetrics > Parametric, "Copy geometrically equivalent meshes".
#     Objetivo duplo, como no artigo: minimizar S11 em 2.87 GHz E na
#     faixa 2.77-2.97 GHz, com pesos iguais, maximizando |B| ao mesmo
#     tempo. Isso favorece banda larga em vez de um vale estreito.
#
# (C) O CAMPO, que e a figura de merito real
#     Plano XY na altura do diamante, HFSS > Fields > Plot Fields > H
#     Verificar que B1 e perpendicular (Hz) dentro da abertura e medir
#     a uniformidade. Referencia: campo majoritariamente perpendicular
#     dentro de raio de 260 um, |B| de 170 a 280 A/m para 1 W.
#
# (D) ALUMINA
#     So no fim, como superstrato, para quantificar o deslocamento.
