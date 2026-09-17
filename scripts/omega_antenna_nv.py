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

import copy

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
    # plano de terra = porta-amostra de titanio, MAIOR que o substrato
    # e sob ele (Fig. 1a do artigo). Sem isso a validacao dessintoniza.
    L_gnd=24.0, W_gnd=15.0,
    # diamante IIa (300 um), usado experimentalmente pelos autores;
    # eps_r ~ 5.7, tan_delta muito baixo (diamante CVD de baixa perda)
    diamond=dict(enable=True, L=3.0, W=3.0, h=0.300, eps=5.7, tand=1e-5),
    # alumina fora deste design: o artigo nao usa alumina, e ela so
    # entra depois de validar (passo D do README)
    alumina=dict(enable=False, L=25.0, W=25.0, h=0.67, eps=9.8, tand=1e-4),
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
    # placa aumentada de 16x11 para 24x22 mm (2026-09-17): as 2 rodadas
    # de sweep anteriores (g_w 0.02-0.40mm x r_w 1-4mm, incluindo faixa
    # sub-PCB de g_w) nao chegaram perto de 2.87 GHz - o piso ficou em
    # ~4.2-4.5 GHz mesmo nos extremos. r_w e a alavanca mais forte, mas
    # precisa de mais espaco pra crescer. Estimativa fisica independente
    # (nv_resonators_compare.py, laco simples): R_loop ~6mm para
    # ressoar perto de 2.87 GHz nesse substrato - da a escala certa.
    # 24x22mm cabe r_w at 9mm com margem (ver add_ro5880_sweep).
    L_sub=24.0, W_sub=22.0,
    # TUNADO (2026-09-17) por Optimetrics > Optimization multivariavel
    # (add_ro5880_optimization_multivar), rodado de verdade no AEDT
    # instalado nesta maquina. Resultado (numero CORRIGIDO apos
    # revalidacao com solve forcado do zero, revert_to_initial_mesh -
    # a leitura inicial pos-otimizacao tinha pego uma variacao vizinha
    # da trajetoria do otimizador por engano, nao o ponto nominal exato
    # - ver README secao 5 "Nota de revalidacao"): dB(S11) entre
    # -27.4 e -27.9 dB em TODA a faixa 2.5-3.2 GHz (nao um pico estreito
    # em 2.87 - uma cauda larga de ressonancia mais baixa, o que e
    # exatamente o que o projeto pede: banda >=250MHz cobrindo as duas
    # transicoes Zeeman, ver README secao 1 "ressoador de alto Q nao
    # serve").
    #   2.74 GHz (transicao 0<->-1): -27.41 dB
    #   2.87 GHz (centro):           -27.44 dB
    #   2.97 GHz (transicao 0<->+1): -27.51 dB
    r_ap=0.345,
    r_w=1.077,
    g_w=0.150,        # minimo de PCB - nao entrou na otimizacao
    f_w=1.700,        # movido de 2.3 (50 ohm nominal) pela otimizacao
    # mesmo porta-amostra assumido para o design de referencia; sem dado
    # proprio ainda (ver pendencia no README sobre o suporte da amostra).
    # Aumentada na mesma proporcao da placa.
    L_gnd=32.0, W_gnd=29.0,
    # diamante AINDA desligado: passo 2 (tunar bare) esta concluido,
    # mas passo 3 (avaliacao do campo, README) precisa do diamante
    # presente. Antes de ir direto pros plots de campo, ligar
    # enable=True aqui e RECONFERIR o S11 na faixa 2.5-3.2 GHz - o
    # diamante carrega a abertura e pode deslocar o casamento. Dado que
    # o casamento atual e uma cauda LARGA (nao um pico estreito), e
    # razoavel esperar que sobreviva a um deslocamento pequeno, mas
    # isso e uma expectativa, nao um resultado confirmado ainda.
    diamond=dict(enable=False, L=3.0, W=3.0, h=0.300, eps=5.7, tand=1e-5),
    # alumina: mesma logica, so que depois do diamante confirmado.
    # ligar enable=True aqui para medir o deslocamento de f0 com a
    # placa de alumina 25x25x0.67 mm por cima.
    alumina=dict(enable=False, L=25.0, W=25.0, h=0.67, eps=9.8, tand=1e-4),
)

# ---------------------------------------------------------------
# DESIGN C - mesma geometria tunada do RO, mas com o diamante
# ---------------------------------------------------------------
# Design SEPARADO (nao sobrescreve Omega_RO5880) para poder comparar
# bare vs carregado lado a lado no mesmo projeto. Passo 3 do README:
# antes dos plots de campo, precisa reconferir se o casamento (que e
# uma cauda larga, nao um pico estreito) sobrevive ao carregamento
# dieletrico do diamante sobre a abertura.
RO_DIAMOND = copy.deepcopy(RO)
RO_DIAMOND["name"] = "Omega_RO5880_Diamond"
RO_DIAMOND["diamond"]["enable"] = True

# ---------------------------------------------------------------
# DESIGN D - geometria tunada + diamante + alumina (25x25x0.67mm)
# ---------------------------------------------------------------
# Design SEPARADO tambem, para poder comparar os tres lado a lado
# (bare / +diamante / +diamante+alumina). Alumina 25x25mm e MAIOR que
# o substrato (24x22mm) - cabe dentro da pegada do terra (32x29mm) com
# folga (ver footprint_L/W em build_omega, que ja usa max() entre
# todas as camadas, incluindo alumina).
RO_DIAMOND_ALUMINA = copy.deepcopy(RO_DIAMOND)
RO_DIAMOND_ALUMINA["name"] = "Omega_RO5880_Diamond_Alumina"
RO_DIAMOND_ALUMINA["alumina"]["enable"] = True


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
    hfss["L_gnd"] = f"{p['L_gnd']}mm"
    hfss["W_gnd"] = f"{p['W_gnd']}mm"

    sub = get_or_create_material(hfss, f"sub_{p['name']}",
                                 p["eps_sub"], p["tand_sub"])

    # substrato
    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=sub)

    # plano de terra = porta-amostra de titanio (Fig. 1a do artigo):
    # MAIOR que o substrato e centrado nele, nao do tamanho do substrato
    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_gnd/2", "-W_gnd/2", "0mm"],
        sizes=["L_gnd", "W_gnd"], name="Ground")
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

    # --- diamante, centrado sobre a abertura, em cima do condutor ---
    dia = p["diamond"]
    stack_h = p["h_sub"]     # topo da pilha construida ate agora (mm)
    if dia["enable"]:
        dia_mat = get_or_create_material(
            hfss, f"diamond_{p['name']}", dia["eps"], dia["tand"])
        hfss[f"dia_L_{p['name']}"] = f"{dia['L']}mm"
        hfss[f"dia_W_{p['name']}"] = f"{dia['W']}mm"
        hfss[f"dia_h_{p['name']}"] = f"{dia['h']}mm"
        hfss.modeler.create_box(
            origin=[f"-dia_L_{p['name']}/2", f"-dia_W_{p['name']}/2",
                    "h_sub"],
            sizes=[f"dia_L_{p['name']}", f"dia_W_{p['name']}",
                   f"dia_h_{p['name']}"],
            name=f"Diamond_{p['name']}", material=dia_mat)
        stack_h += dia["h"]

    # --- alumina, superstrato opcional em cima de tudo (passo D do
    # README - so ligar depois que o design estiver validado/tunado) ---
    al = p["alumina"]
    if al["enable"]:
        al_mat = get_or_create_material(
            hfss, f"alumina_{p['name']}", al["eps"], al["tand"])
        hfss[f"al_L_{p['name']}"] = f"{al['L']}mm"
        hfss[f"al_W_{p['name']}"] = f"{al['W']}mm"
        hfss[f"al_h_{p['name']}"] = f"{al['h']}mm"
        hfss.modeler.create_box(
            origin=[f"-al_L_{p['name']}/2", f"-al_W_{p['name']}/2",
                    f"{stack_h}mm"],
            sizes=[f"al_L_{p['name']}", f"al_W_{p['name']}",
                   f"al_h_{p['name']}"],
            name=f"Alumina_{p['name']}", material=al_mat)
        stack_h += al["h"]

    # --- malha local restrita ao GAP, nao ao condutor inteiro ---
    # Refinar a folha de 16 mm inteira no tamanho do gap (7 um) explode
    # a contagem de celulas (razao 2286:1, ver README). Em vez disso,
    # cria-se uma caixa de ar pequena so em volta do gap e refina-se a
    # malha dentro dela — o resto do condutor usa a malha padrao do HFSS.
    gap_margin = max(p["g_w"] * 6, 0.05)
    try:
        # mesma pegada da fenda "Gap" (r_ap+r_w+0.5 de comprimento em x),
        # so um pouco mais alta em y, para pegar as bordas do condutor.
        # IMPORTANTE em z: a caixa fica INTEIRAMENTE DENTRO do Substrate
        # (toca a face de cima em h_sub, nao ultrapassa). Testado no
        # HFSS: uma caixa que so ATRAVESSA parcialmente outro objeto -
        # nem contida nem fora - da erro de malha "Parts ... intersect".
        # Contencao TOTAL e o padrao seguro (como toda caixa de ar
        # aninhada dentro de outra no HFSS). Fica dentro do Substrate
        # (sempre maior que r_ap+r_w+0.5, em qualquer design) em vez do
        # Diamond porque o Diamond (3x3mm fixo) e mais estreito que o
        # comprimento da fenda quando r_w cresce, e deixaria parte da
        # caixa de fora dele - o mesmo problema de novo.
        gap_region = hfss.modeler.create_box(
            origin=["-(r_ap + r_w + 0.5mm)", f"-(g_w/2 + {gap_margin}mm)",
                    "h_sub - 0.001mm"],
            sizes=["r_ap + r_w + 0.5mm", f"g_w + {2*gap_margin}mm",
                   "0.001mm"],
            name="Mesh_Region_Gap", material="vacuum")
        # atributo correto e "is_model", NAO "model" (esse ultimo so
        # cria um atributo Python solto e nao muda nada no HFSS - a
        # caixa ficaria um solido real de vacuo por cima/dentro do
        # Substrate, causando conflito de malha ou alterando a fisica).
        gap_region.is_model = False
        # inside_selection=True e o default (restringe a malha DENTRO da
        # caixa, nao nas faces dela) - omitido para nao depender do nome
        # exato do kwarg entre versoes do pyaedt (era isinside antes).
        # "g_w/3" e uma EXPRESSAO da variavel de projeto, nao um numero
        # fixo - se nao fosse, o Optimetrics mudaria g_w em cada
        # variacao do sweep mas a malha ficaria travada no g_w do
        # dict Python (0.150mm por default aqui), grossa demais pros
        # pontos do sweep com g_w bem menor (ate 0.02mm nesta rodada).
        hfss.mesh.assign_length_mesh(
            [gap_region.name], maximum_length="g_w/3", name="Mesh_Gap")
    except Exception as e:
        print("  aviso: nao consegui criar a operacao de malha do gap "
              f"automaticamente ({e}).")
        print("  Crie manualmente: HFSS > Mesh Operations > Assign >")
        print("  On Selection > Length Based, numa caixa em volta do Gap.")

    # --- airbox e setup ---
    # a pegada tem que cobrir o MAIOR entre substrato, terra, diamante
    # e alumina; a altura tem que sobrar espaco acima de toda a pilha
    top_clear = stack_h + 2
    footprint_L = max(p["L_sub"], p["L_gnd"],
                      dia["L"] if dia["enable"] else 0,
                      al["L"] if al["enable"] else 0)
    footprint_W = max(p["W_sub"], p["W_gnd"],
                      dia["W"] if dia["enable"] else 0,
                      al["W"] if al["enable"] else 0)
    airbox = hfss.modeler.create_box(
        origin=[f"-{footprint_L}mm/2-airgap", f"-{footprint_W}mm/2-airgap",
                "-airgap"],
        sizes=[f"{footprint_L}mm+2*airgap", f"{footprint_W}mm+2*airgap",
               f"{top_clear}mm+2*airgap"],
        name="Airbox", material="air")
    hfss.assign_radiation_boundary_to_objects(airbox.name)

    hfss.create_setup(name="Setup1", setup_type="HFSSDriven",
                      Frequency=f"{F0_GHZ}GHz",
                      MaximumPasses=20, MaxDeltaS=0.02)
    hfss.create_linear_step_sweep(
        setup="Setup1", unit="GHz",
        start_frequency=F_START, stop_frequency=F_STOP, step_size=F_STEP,
        name="Sweep1", sweep_type="Interpolating")


def add_discrete_zeeman_sweep(hfss):
    """Sweep DISCRETO (nao interpolado) na faixa das transicoes Zeeman.

    Por que: o "Sweep1" e Interpolating, ajustado a partir de UM ponto
    de malha adaptada em 2.87 GHz (Setup1) e interpolado pra banda
    inteira 0.5-6 GHz. Valores longe de 2.87 GHz - especialmente nas
    BORDAS do sweep (0.5 e 6 GHz) - podem ser artefato de extrapolacao
    da interpolacao, nao fisica resolvida de verdade (2026-09-17: o
    "vale mais fundo em 0.5 GHz" que apareceu em varias analises
    anteriores era suspeito por exatamente esse motivo). Um sweep
    Discrete resolve o sistema linear em CADA frequencia listada
    (reaproveitando a malha adaptada de Setup1, sem remalhar) - mais
    caro que Interpolating, mas cada ponto e real, nao extrapolado.

    Faixa 2.5-3.2 GHz, passo 0.02 GHz (36 pontos) - cobre com folga as
    duas transicoes Zeeman (2.74 e 2.97 GHz @ ~4.7 mT) e o centro
    (2.87 GHz), que e a faixa que realmente importa para o projeto.
    """
    return hfss.create_linear_step_sweep(
        setup="Setup1", unit="GHz",
        start_frequency=2.5, stop_frequency=3.2, step_size=0.02,
        name="Sweep_Discrete_Zeeman", sweep_type="Discrete")


def add_ro5880_sweep(hfss):
    """Optimetrics parametric no Omega_RO5880, mirando 2.87 GHz.

    HISTORICO (2026-09-17):
    - 1a rodada (g_w 0.10-0.40mm x r_w 1.0-3.5mm, placa 16x11mm): piso
      em ~4.3-4.5 GHz no extremo mais favoravel.
    - 2a rodada (g_w 0.02-0.14mm x r_w 1.0-4.0mm, mesma placa, testando
      g_w bem abaixo do minimo de PCB): NAO melhorou o piso de forma
      relevante. g_w nao e o gargalo.
    - 3a rodada (g_w 0.10-0.15mm x r_w 4.0-9.0mm, placa aumentada para
      24x22mm): analisando o CSV exportado (nao so o grafico) apareceu
      um problema serio - dB(S11) EXATAMENTE em 2.87 GHz ficou entre
      -0.3 e -3 dB em TODAS as 12 combinacoes (nenhuma chegou perto).
      E o "vale mais profundo" de cada r_w pulou de forma
      NAO-monotonica (r_w=8 deu 5.5 GHz, r_w=9 deu 4.65 GHz, r_w=7 caiu
      na BORDA do sweep em 6 GHz) - exatamente a armadilha do README
      secao 7 item 5 (XAtYMin/vale mais fundo pula entre MODOS
      DIFERENTES, nao e a mesma ressonancia continuando a baixar).
      Extrapolar r_w grande estava perseguindo modos errados.
      Achado util: com r_w=1.151mm (padrao, sem variar) NESSA placa
      grande, o vale ficou em 3.965 GHz - bem mais perto de 2.87 GHz
      que qualquer coisa com r_w grande. Sugere que so aumentar a placa
      ja ajudou, e que r_w grande estava pulando pra outro modo.
    - 4a rodada (g_w fixo 0.15mm, r_w 1.0-4.0mm passo 0.5mm, mesma
      placa): desta vez a analise foi pelo CSV exportado direto (nao
      pelo grafico), lendo dB(S11) EXATO em 2.87 GHz por r_w:
        r_w=1.0  -> -16.06 dB (vale real em 3.875 GHz)
        r_w=1.151-> -16.48 dB (vale real em 3.965 GHz) - melhor ate aqui
        r_w=1.5  -> -14.22 dB (vale em 4.670 GHz - quebra a suavidade,
                    provavelmente um modo secundario aparecendo)
        r_w=2.0  -> -11.50 dB (vale ja abaixo de 0.5 GHz - fora da banda)
        r_w=2.5 a 4.0 -> piora progressiva (vale cada vez mais fora,
                    abaixo de 0.5 GHz)
      CONCLUSAO: a ressonancia real cruza 2.87 GHz exatamente entre
      r_w=1.151mm (3.965 GHz) e r_w=2.0mm (<0.5 GHz) - janela estreita
      e agora bem localizada. E a lista de "min_S11/at_freq" deixa
      claro que "vale mais profundo" so serve pra achar a janela, nao
      pra tunar direto - o numero que decide e dB(S11) NO PONTO EXATO
      de 2.87 GHz, sempre lido do CSV exportado.

    - 5a rodada (esta): varredura fina dentro da janela identificada,
      r_w de 1.2 a 1.9mm passo 0.1mm, ainda g_w=0.15mm fixo. Objetivo:
      achar o r_w onde dB(S11) em 2.87 GHz e mais profundo (nao onde
      "o vale" esta, onde o VALOR EM 2.87 GHz e melhor).

    f_w fica de fora por enquanto: no artigo so ajusta o casamento em
    50 ohm, pouco a frequencia - tunar a mao depois de achar g_w/r_w.

    Grid: 1 (g_w) x 8 (r_w) = 8 combinacoes.

    So CRIA o setup (Optimetrics > Parametric fica visivel na arvore);
    NAO chama .analyze() - rodar e uma decisao de tempo/maquina que
    fica com quem esta na frente do HFSS.
    """
    setup = hfss.parametrics.add(
        "r_w", start_point="1.2mm", end_point="1.9mm", step="0.1mm",
        variation_type="LinearStep", name="Sweep_rw_2p87GHz_v5")
    # g_w fixo (nao varia nesta rodada) - so precisa ter o valor certo
    # na variacao, nao precisa de add_variation pra isso
    setup.add_calculation(
        calculation="dB(S(Port1,Port1))", ranges={"Freq": f"{F0_GHZ}GHz"})
    return setup


def add_ro5880_optimization(hfss):
    """Otimizacao (nao DOE) no Omega_RO5880, mirando 2.87 GHz.

    HISTORICO: as rodadas 1-5 de Optimetrics > Parametric (varredura em
    grade, ver add_ro5880_sweep) mostraram que este laco tem VARIOS
    modos proximos na banda 0.5-6 GHz, e uma grade 1D em r_w fica
    pulando entre eles de forma nao-monotonica a cada passo pequeno -
    tentar cortar o intervalo pela metade manualmente parou de
    convergir (ver README secao 5). A 5a rodada, lida pelo CSV, achou
    o melhor ponto em r_w=1.2mm (dB(S11)@2.87GHz = -17.11 dB) dentro de
    uma varredura fina 1.2-1.9mm - mas o valor SO piorou dali para
    frente, contrariando a expectativa de cruzamento perto de r_w=2mm
    da 4a rodada. Sinal de que uma grade discreta nao vai convergir
    aqui: precisa de uma OTIMIZACAO continua de verdade.

    Esta funcao cria um setup de Optimizacao (Quasi-Newton, o motor
    padrao do HFSS para variavel continua) com r_w livre entre 1.0 e
    2.0mm (a janela ja bem localizada pelas rodadas 4-5), partindo do
    melhor ponto conhecido (1.2mm), com meta dB(S11) em 2.87GHz <= -40
    (agressiva de proposito, para o otimizador continuar melhorando em
    vez de parar num minimo local raso).

    g_w fica FIXO no valor atual do design (0.15mm, seguro para PCB) -
    nao entra na otimizacao porque as rodadas 1-2 (add_ro5880_sweep)
    mostraram que seu efeito e fraco comparado a r_w.

    So CRIA o setup; NAO chama .analyze() - rodar e decisao de quem
    esta na frente do HFSS. Assinaturas confirmadas contra a doc oficial
    do pyaedt (aedt.docs.pyansys.com) antes de escrever, ja que nao ha
    AEDT instalado neste ambiente para testar diretamente:
      hfss.optimizations.add(calculation, ranges, variables=None,
        optimization_type='Optimization', condition='<=', goal_value=1,
        goal_weight=1, solution=None, name=None, ...)
      SetupOpti.add_variation(variable_name, min_value, max_value,
        starting_point=None, min_step=None, max_step=None, ...)
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["r_w"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-40,
        goal_weight=1,
        name="Opt_rw_2p87GHz")
    setup.add_variation(
        "r_w", min_value=1.0, max_value=2.0, starting_point=1.2)
    return setup


# RESULTADO (2026-09-17, rodado de verdade - AEDT esta instalado nesta
# maquina em D:\Ansys HFSS\ANSYS Inc\ANSYS Student\v252, entao esta
# rodada foi executada e nao so codificada): convergiu em r_w=1.1mm em
# ~9 min, mas dB(S11)@2.87GHz = -17.93 dB - so uma leve melhora sobre
# o -17.11 dB manual, longe da meta de -40. A ressonancia real continua
# em ~4.02 GHz. O otimizador ficou preso num plato de gradiente quase
# zero: variar SO r_w nao abre espaco suficiente. Ver
# add_ro5880_optimization_multivar abaixo, que soma r_ap e f_w como
# variaveis livres tambem.


def add_ro5880_optimization_multivar(hfss):
    """Otimizacao multivariavel (r_ap, r_w, f_w) no Omega_RO5880.

    Por que: add_ro5880_optimization (so r_w, 1 variavel) convergiu
    para um plato em dB(S11)@2.87GHz = -17.93 dB, com a ressonancia
    real travada em ~4.02 GHz - nao alcancavel variando so r_w dentro
    de faixas razoaveis. r_ap nunca foi variado em nenhuma rodada
    anterior; abrir essa dimensao (junto com r_w e f_w) da ao
    otimizador mais espaco pra escapar desse plato.

    r_ap fica limitado a uma faixa estreita (0.2-0.6mm) de proposito:
    e o raio da abertura que define a area de campo uniforme sobre o
    diamante - o artigo original explicitamente MINIMIZA r_ap (mais
    campo, area menor), entao nao faz sentido deixar o otimizador
    aumentar isso livremente so para achar frequencia; melhor manter
    pequeno e deixar r_w/f_w fazerem o trabalho principal.

    f_w entra numa faixa moderada (1.5-3.5mm) - no artigo so ajusta o
    casamento em 50 ohm e tem pouco efeito na frequencia, mas dar essa
    liberdade extra ao otimizador multivariavel e barato (mais uma
    dimensao) e pode ajudar a escapar do plato de r_w sozinho.

    r_w continua na mesma janela ja bem explorada (1.0-2.5mm, um pouco
    mais larga que antes), partindo do melhor ponto conhecido (1.1mm).

    ATENCAO: com 3 variaveis, o Quasi-Newton precisa de mais avaliacoes
    por iteracao (gradiente por diferencas finitas ~ n+1 por passo) -
    espere um tempo de execucao bem maior que a rodada de 1 variavel
    (~9 min). So CRIA o setup, nao chama .analyze().
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["r_ap", "r_w", "f_w"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-30,
        goal_weight=1,
        name="Opt_multivar_2p87GHz")
    setup.add_variation(
        "r_ap", min_value=0.2, max_value=0.6, starting_point=0.3)
    setup.add_variation(
        "r_w", min_value=1.0, max_value=2.5, starting_point=1.1)
    setup.add_variation(
        "f_w", min_value=1.5, max_value=3.5, starting_point=2.3)
    return setup


def report(p):
    R_o = p["r_ap"] + p["r_w"]
    print(f"  {p['name']}")
    print(f"     substrato  eps_r={p['eps_sub']}  h={p['h_sub']} mm")
    print(f"     abertura   raio {p['r_ap']} mm (diametro "
          f"{2*p['r_ap']*1000:.0f} um)")
    print(f"     laco       raio externo {R_o:.3f} mm")
    print(f"     gap        {p['g_w']*1000:.0f} um")
    print(f"     pernas     largura {p['f_w']} mm")
    print(f"     terra      {p['L_gnd']} x {p['W_gnd']} mm "
          f"(porta-amostra, maior que o substrato)")
    dia = p["diamond"]
    if dia["enable"]:
        print(f"     diamante   {dia['L']} x {dia['W']} x "
              f"{dia['h']*1000:.0f} um, eps_r={dia['eps']}")
    else:
        print("     diamante   desativado")
    al = p["alumina"]
    if al["enable"]:
        print(f"     alumina    {al['L']} x {al['W']} x "
              f"{al['h']} mm, eps_r={al['eps']}")
    else:
        print("     alumina    desativada")
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

    # As 5 rodadas de Optimetrics > Parametric (add_ro5880_sweep) ja
    # localizaram a janela (r_w entre 1.0 e 2.0mm) mas uma grade discreta
    # parou de convergir - varios modos proximos, ver docstring de
    # add_ro5880_optimization. Daqui pra frente usa Optimizacao continua
    # (Quasi-Newton) dentro dessa janela. Se voce ja tem o projeto aberto
    # e construido no AEDT (como agora), NAO precisa rodar o script
    # inteiro de novo so por isso - chame add_ro5880_optimization(hfss)
    # direto numa sessao pyaedt conectada ao projeto ja aberto.
    add_ro5880_optimization(hfss)

    hfss.save_project()
    print("Projeto criado em:", hfss.project_file)
    print("Optimetrics 'Opt_rw_2p87GHz' criado em Omega_RO5880 - "
          "revise e rode pelo HFSS (Optimetrics > botao direito > "
          "Analyze).")

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
#       banda ~6.3 GHz (diamante IIa 300 um, ja incluido neste design)
#     Este script ja aplica as 3 causas suspeitas do README (secao 5):
#       terra 24x15 mm, diamante 3x3x0.300 mm (eps_r=5.7) e malha fina
#       (g_w/3) restrita a uma caixa em volta do Gap, nao no Conductor
#       inteiro. Se ainda NAO reproduzir o artigo, ver Mesh_Gap em
#       Optimetrics > Convergence e apertar ainda mais o maximum_length,
#       ou aumentar MaximumPasses no Setup1.
#
#     Note que sao DOIS portos: olhe S11 E S21. Um elemento em linha
#     bem casado tem S21 alto fora das ressonancias.
#
# (B) PORTAR - Omega_RO5880
#     3 rodadas de sweep ja rodadas (2026-09-17), ver add_ro5880_sweep:
#       1a: g_w 0.10-0.40mm x r_w 1.0-3.5mm (placa 16x11mm) -> piso em
#           ~4.3-4.5 GHz, nao chega em 2.87.
#       2a: g_w 0.02-0.14mm x r_w 1.0-4.0mm (mesma placa, testando g_w
#           sub-PCB) -> NAO melhorou (~4.2-5.2 GHz). g_w nao e o
#           gargalo real.
#       3a (atual): placa aumentada para 24x22mm, r_w 4.0-9.0mm (escala
#           motivada por R_loop~6mm do nv_resonators_compare.py),
#           g_w de volta pra faixa segura de PCB (0.10-0.15mm).
#     CONCLUSAO ATE AQUI: r_w (indutivo) e a alavanca dominante, nao
#     g_w. Se a 3a rodada tambem nao chegar em 2.87 GHz, o proximo
#     passo e aumentar r_w/placa ainda mais (nao voltar a reduzir g_w).
#     f_w so ajusta o casamento em 50 ohm depois de achar g_w/r_w.
#     Optimetrics > Parametric, "Copy geometrically equivalent meshes".
#
# (C) O CAMPO, que e a figura de merito real
#     Plano XY na altura do diamante, HFSS > Fields > Plot Fields > H
#     Verificar que B1 e perpendicular (Hz) dentro da abertura e medir
#     a uniformidade. Referencia: campo majoritariamente perpendicular
#     dentro de raio de 260 um, |B| de 170 a 280 A/m para 1 W.
#
# (D) ALUMINA
#     So no fim, como superstrato, para quantificar o deslocamento.
#     Ja implementado (bloco "alumina" em RO, desativado por default):
#     depois que g_w/r_w/f_w estiverem tunados para 2.87 GHz SEM carga,
#     mude RO["alumina"]["enable"] para True e rode de novo para medir
#     o deslocamento de f0 com a placa de 25x25x0.67 mm por cima. Nao
#     ligue isso antes de tunar o design bare - senao voce nao sabe se
#     um desvio veio da geometria ou da alumina.
