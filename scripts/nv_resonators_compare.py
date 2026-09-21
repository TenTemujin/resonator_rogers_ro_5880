"""
ESTUDO COMPARATIVO DE TOPOLOGIAS - ressoador de micro-ondas para ODMR
de centros NV em diamante.  f0 = 2.87 GHz (zero-field splitting do NV-)
Substrato: Rogers RT/duroid 5880, 0.75 mm.

>>> ATUALIZACAO 2026-09-18 (ver README.md secao 0) <<<
O orientador (Achiles) pediu: (1) ressoador de UM PORTO, nao dois; (2)
feicoes minimas de fabricacao de 0.5mm (gap e trilha estreita) - MAIOR
que o antigo limite assumido de PCB (~0.1-0.15mm via LPKF, processo que
NAO sera mais usado). Isso invalida a topologia (B) OMEGA deste arquivo
(e o Omega_RO5880 do outro script) como candidata final - ela e de dois
portos por natureza.
A topologia (A) ANEL FENDIDO abaixo, que ja e de UM PORTO, passa a ser a
CANDIDATA PRINCIPAL. G_SLOT foi levantado de 0.1mm (valor de referencia
de Misonou et al. 2020, tambem sub-PCB) para o novo minimo de 0.5mm -
ainda NAO re-otimizada para casar em 2.87GHz nesse gap maior (gap maior
-> capacitancia menor -> tende a exigir R_out maior para compensar).
2026-09-18 (rodado de verdade, nao so codificado): geometria corrigida
para trilha fina de verdade (nao disco quase solido), ressonancia de
2.87GHz localizada perto de R_out~16mm, casamento ainda sendo ajustado
via add_ring_optimization_multivar (R_out, W_ring e feed_overlap_frac -
o tap de impedancia para o futuro conector SMA). Ver README.md secao 0
e 5 para o historico completo e estado atual.

>>> CORRECAO CRITICA 2026-09-19 (ver roadmap.md secao 0) <<<
A geometria "anel fino" (build_ring, acima) esta PAUSADA. Verificado
direto no texto extraido dos PDFs originais (Sasaki et al., Rev. Sci.
Instrum. 87, 053904 (2016); Misonou et al., arXiv:2002.02113 (2020)):
a estrutura real NAO e um anel fino concentrico. E um DISCO quase
solido de raio R=7,0mm com um FURO PEQUENO (r=0,5mm) DESLOCADO do
centro por s=3,9mm (excentrico, nao concentrico), fenda g=0,1mm, e uma
LINHA DE ALIMENTACAO AFUNILADA (3,3mm no lado do SMA ate 0,54mm na
borda do ressoador, ao longo de 23mm) - o afunilamento e o casamento de
impedancia, nao um angulo de tap. O comentario antigo "R+s=10.9" (na
versao anterior deste arquivo) era literalmente R=7,0 + s=3,9 = 10,9 -
dois parametros diferentes, nunca separados corretamente.
Nova funcao: build_disk_hole_resonator(hfss, p) - reproduz o
dispositivo publicado (Antena #1) e tambem serve para a migracao pro
RO5880, um passo por vez, trocando o dict `p` (SASAKI_VALIDATION,
RO5880_STEP1_MATERIAL, ...). Validado em FR4 contra o artigo
(~2,79-2,87GHz esperado, ~3,28GHz obtido - aceito, ver historico em
SASAKI_VALIDATION). Passo 1 da migracao (troca de material pra RO5880)
e o modo ativo agora - ver SASAKI_MODEL. Ver roadmap.md para o plano
completo de migracao.

Constroi DUAS topologias no MESMO projeto, com placa, airbox, setup e
varredura identicos, para que qualquer diferenca observada venha da
topologia e nao das condicoes de simulacao. A topologia (B) fica so
para referencia/comparacao historica - nao e mais candidata a fabricar.

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

import copy
import time

from ansys.aedt.core import Hfss

# ---------------------------------------------------------------
# 1. Parametros comuns (mm)
# ---------------------------------------------------------------
PROJECT_NAME = "NV_Resonators_Ring_vs_Omega_2p87GHz"
F0_GHZ = 2.87

H_SUB = 0.75
EPS_SUB = 2.20
TAND_SUB = 0.0009

# 2026-09-18: REDUZIDA de volta para 55x50mm (havia passado por 70x60
# e depois 90x80mm, tentando dar espaco para R_out grande) - a placa de
# 90x80mm com AIRGAP=28mm estourou o limite de malha da versao Student
# ("Mesh size (64539 volume elements) is greater than the limit"),
# mesmo erro ja documentado na secao 9 do README para o outro design.
# Com a geometria do anel corrigida (trilha fina, nao mais disco quase
# solido - ver comentario no bloco do anel abaixo), as 2 primeiras
# variacoes testadas ja deram R_out~13.6mm e ~15.2mm - bem menor que os
# ~20mm da geometria antiga (errada). Reduzindo a placa e o teto da
# otimizacao (RING_ROUT_MAX) proporcionalmente para caber no limite de
# malha; se a otimizacao pedir mais espaco que isso, sera preciso
# reduzir AIRGAP tambem (minimo fisico: lambda0/4 = 26.1mm) antes de
# aumentar a placa de novo.
L_SUB = 55.0          # placa fixa, comum as duas topologias
W_SUB = 50.0
RING_ROUT_MAX = 20.0  # teto da busca de R_out - mantido em sincronia
                      # manual com add_ring_optimization_multivar

WF = 2.3              # microfita de 50 ohm em RO5880 / 0.75 mm
R_HOLE = 0.5          # raio do furo (acesso optico) - comum as duas

AIRGAP = 26.5         # > lambda0/4 = 26.1 mm - perto do minimo fisico
                      # de proposito, para poupar malha (ver nota acima)

# 2026-09-18: ESTREITADA de volta para perto de 2.87GHz. O diagnostico
# (RING_MODE="diagnostic_grid") testou R_out de 5 a 20mm na faixa larga
# 0.5-6GHz e achou: R_out=20mm ressoa em ~0.85GHz (vale fundo, quase
# -2dB); R_out=15mm ja desloca a ressonancia pra bem mais alto (curva
# descendo forte perto de 4-5GHz, ainda sem fechar um vale completo
# dentro dos 6GHz do grafico). Ou seja, 2.87GHz deve cair ENTRE R_out=15
# e 20mm - faixa bem mais estreita que a usada antes (3-25mm). O
# orientador (Achiles) tambem confirmou o metodo certo aqui: nao ficar
# variando so pra achar onde THE vale esta (isso e a varredura larga,
# so serviu para localizar a vizinhanca) - trava em 2.87GHz e otimiza
# a geometria para casar bem ALI, que e o que add_ring_optimization_multivar
# ja faz.
# 2026-09-19: ESTREITADA de volta para perto de 2.87GHz - ja sabemos
# que a ressonancia dos passos 1/2 da migracao ficou perto de 4.1-4.2
# GHz (achado pela varredura larga usada antes), entao para a
# otimizacao do Passo 3 (add_disk_optimization) nao precisa mais da
# faixa 0.5-6GHz - trava em 2.87GHz e otimiza ali, mesmo metodo
# confirmado pelo Achiles. Faixa mais estreita tambem deixa cada
# iteracao da otimizacao mais rapida (menos pontos de sweep).
# 2026-09-19: alargada um pouco (2.0-4.0GHz) so para o diagnostico do
# Passo 8 (RO5880_STEP8_NARROW_NECK) - R/s novos, nao sabemos ainda
# exatamente onde a ressonancia vai cair (a formula ja se mostrou
# pouco confiavel para prever isso com precisao).
F_START, F_STOP, F_STEP = 2.0, 4.0, 0.01

# 2026-09-18: controla o que o __main__ faz com o design Ring_Unloaded.
#   "diagnostic_single"  : resolve so a geometria nominal (1 solve) na
#       faixa larga - ja rodado, achou vale em ~0.85GHz com R_out=20mm.
#   "diagnostic_grid"    : varredura de R_out (add_ring_wideband_scan),
#       ja rodado - localizou a ressonancia de 2.87GHz entre R_out=15
#       e 20mm (ver nota de F_START/F_STOP acima).
#   "optimize_2p87"       : otimizacao com 2 variaveis (R_out,
#       feed_overlap), ja rodada - achou R_out~16.3mm bem perto de
#       2.87GHz, mas so -0.63dB de profundidade.
#   "optimize_2p87_multivar" (v3, ja rodada): trocou feed_overlap por
#       feed_overlap_frac + abriu W_ring - PIOROU (-0.28dB). W_ring nao
#       era o lever certo (ver historico em add_ring_optimization_multivar).
#   "optimize_2p87_multivar" (v4, gap_rotation): PAUSADA em 2026-09-19
#       - ver roadmap.md secao 0. A hipotese de gap_rotation como "tap"
#       nao e sustentada pela geometria real da literatura.
#   "validate_sasaki_fr4" : constroi build_disk_hole_resonator() com o
#       dict SASAKI_MODEL (disco + furo excentrico + linha afunilada +
#       resist) e roda 1 solve - usado para a validacao em FR4 (feita)
#       e os passos 1/2 da migracao (material, depois gap) - ambos ja
#       rodados, ver historico em RO5880_STEP1_MATERIAL/STEP2_GAP.
#   "optimize_disk_2p87" : roda add_disk_optimization() (R_disk, s_off
#       livres) no dict SASAKI_MODEL - Passo 3 da migracao, ja rodado
#       com sucesso (convergiu R_disk~11.1mm, s_off~4.4mm, ressonancia
#       bem em 2.87GHz - so falta o casamento, que e o Passo 4).
#   "optimize_taper" : roda add_taper_optimization() (feed_w_narrow,
#       feed_len livres, R_disk/s_off travados) - Passo 4, ja rodado.
#       PIOROU (~-0.5dB vs -0.73dB do Passo 3) - sinal de interacao
#       entre as variaveis, nao dava pra tratar em sequencia isolada.
#   "optimize_joint" : roda add_joint_optimization() (R_disk, s_off,
#       feed_w_narrow, feed_len TODOS livres juntos) - Passo 5, ja
#       rodado. So chegou a ~-0.65dB no melhor caso - com 4 graus de
#       liberdade, isso e sinal de problema estrutural, nao falta de
#       ajuste. Ver Passo 6 (diagnostico do resist) abaixo.
#   "validate_sasaki_fr4" (reaproveitado para o Passo 6): 1 solve so,
#       sem otimizar, no ponto ja conhecido (Passo 5) mas SEM a camada
#       de resist (RO5880_STEP6_NO_RESIST) - testa se o resist estava
#       causando descasamento na propria porta. PIOROU AINDA MAIS
#       (~-0.42dB) - descarta a hipotese do resist.
#   "test_line_2port" : Passo 7 (diagnostico) - build_straight_line_
#       2port(), linha reta de microfita com DOIS portos, sem
#       ressoador nenhum, para validar se a largura WF=2.3mm e a
#       modelagem da porta realmente dao 50 ohm em RO5880/0.75mm.
#       CONFIRMADO: S11 < -28dB, S21 ~0dB - porta/linha estao OK, o
#       problema esta na geometria do ressoador.
#   "validate_sasaki_fr4" (reaproveitado para os Passos 8/9): 1 solve
#       so. Passo 8 (RO5880_STEP8_NARROW_NECK): testou constricao
#       estreita - PIOROU (~-0.36dB), descartado.
#   "extract_zin" : Passo 9 - roda 1 solve no dict RO5880_STEP9_ZIN_PROBE
#       (linha SEM afunilar, so pra medir a carga crua) e IMPRIME
#       Re(Zin)/Im(Zin) direto no terminal (sem precisar de Smith Chart
#       na GUI). RESULTADO: Zin=0.55+0.60j ohm em 2.87GHz - quase um
#       curto (~91:1 de razao de transformacao) - explica todo o
#       historico de casamento raso.
#   "test_feed_angles" : Passo 14 - constroi 3 designs (ANGLE_TEST_MODELS,
#       feed_angle=45/90/135 graus) girando SO o ponto de conexao da
#       linha ao redor do disco (nao a fenda/furo) e imprime Zin de
#       cada um no terminal. RESULTADO: parte real de Zin travada em
#       0.5-1 ohm em TODOS os angulos - descarta o tap angular.
#   "extract_zin" (reaproveitado para o Passo 16): 1 solve no dict
#       RO5880_STEP16_STUB (disco + linha reta + STUB ABERTO EM
#       DERIVACAO, calculado analiticamente por teoria de linha de
#       transmissao a partir do Zin medido) - imprime dB(S11) e Zin
#       direto no terminal. MODO ATIVO AGORA.
RING_MODE = "extract_zin"

MIN_FEATURE = 0.5     # mm - piso de fabricacao pedido pelo Achiles em
                      # 18/09/2026 (substitui o limite antigo de PCB via
                      # LPKF, ~0.1-0.15mm); vale para gap E trilha estreita

# --- (A) anel fendido - CANDIDATA PRINCIPAL (um porto) a partir de
#     2026-09-18, ver README.md secao 0 e 3 ---
#
# CORRECAO DE GEOMETRIA (2026-09-18, apos rodada real no HFSS): a versao
# anterior deste bloco tinha um R_HOLE fixo em 0.5mm e usava R_out para
# o raio EXTERNO de um disco praticamente SOLIDO (disco inteiro menos um
# furinho de 0.5mm no centro) - isso NAO e o anel fino da literatura
# (Sasaki 2016 / Misonou 2020, que usam uma TRILHA estreita de largura
# s = R-r). Rodando de verdade no HFSS: precisou de R_out~20mm pra
# ressoar em 2.87GHz (bem mais que o esperado) e o casamento ficou
# raso demais (so -2dB no fundo do vale, longe do -10/-20dB esperado)
# - os dois sintomas batem com "disco solido" em vez de "laco fino".
# Corrigido: agora R_out e R_in (= raio interno do anel = raio da
# abertura optica, substitui o antigo R_HOLE) definem uma trilha anular
# de verdade, largura W_RING = R_out - R_in.
R_OUT = 16.3          # raio externo - ponto da 1a otimizacao bem
                      # sucedida em frequencia (ver historico em
                      # add_ring_optimization_multivar)
W_RING = 2.0          # largura da trilha do anel (R_out - R_in) - o
                      # valor que deu a melhor profundidade ate agora
                      # (-0.63dB); liberar isso como variavel livre
                      # (rodada com W_ring 3.7-4.0mm) so piorou (-0.28dB)
                      # e nao e o lever certo mesmo - ver GAP_ANGLE_DEG

# 2026-09-19: correcao conceitual - FEED_OVERLAP_FRAC (penetracao
# RADIAL da linha dentro da largura do anel, sempre no mesmo ponto
# angular, oposto a fenda) NAO e o "tap" de casamento de impedancia de
# verdade. O tap classico de um ressoador em laco e a posicao ANGULAR
# onde a linha se conecta em relacao a fenda - girando esse ponto ao
# redor do anel, amostra-se pontos diferentes da onda estacionaria de
# tensao/corrente, o que de fato transforma a impedancia. Rodando com
# feed_overlap_frac livre (mantendo o angulo fixo, sempre oposto a
# fenda) o otimizador nem se afastou do ponto de partida (0.5) - sinal
# de baixa sensibilidade, confirma que esse nao e o lever certo.
# GAP_ROTATION_DEG = 0 e o comportamento ORIGINAL (fenda construida em
# +x, diametralmente oposta a entrada da linha em -x, sem rotacao
# nenhuma aplicada) - e o baseline testado ate agora. Variar isso gira
# a fenda ao redor do anel, mudando a posicao angular relativa
# feed-vs-fenda; ainda nao otimizado.
GAP_ROTATION_DEG = 0.0
G_SLOT = MIN_FEATURE  # largura da fenda radial - levantado de 0.1mm
                      # (valor de Misonou et al. 2020, tambem sub-PCB)
                      # para o piso de fabricacao pedido pelo Achiles
# 2026-09-18: FEED_OVERLAP trocado de valor absoluto (mm) para FRACAO
# de W_ring - agora que W_ring vai virar variavel livre tambem (ver
# add_ring_optimization_multivar), um valor absoluto podia ultrapassar
# W_ring conforme o otimizador variasse os dois, quebrando a geometria
# (feed atravessando o anel inteiro). Como fracao (0 a 1), o tap fica
# SEMPRE dentro do anel por construcao, nao importa o W_ring do momento.
# 0.5 = tap na metade da largura do anel (ponto de partida neutro).
FEED_OVERLAP_FRAC = 0.5   # 0 = tap na borda externa, 1 = borda interna

# ---------------------------------------------------------------
# (C) DISCO + FURO EXCENTRICO - modelo de validacao + migracao
# ---------------------------------------------------------------
# 2026-09-19: parametros EXATOS de Sasaki et al., Rev. Sci. Instrum.
# 87, 053904 (2016), Fig. 1(a)/(b) e texto da Sec. II - Antena #1 (ver
# roadmap.md secao 0 e 9). Extraidos diretamente do PDF original
# (texto E a foto real da Fig. 1a, que confirmou a topologia: linha e
# fenda entram pelo mesmo lado do disco, furo do lado oposto).
#
# Validado (2026-09-19, rodado de verdade): ressonancia real em
# ~3.28GHz (com camada de resist) contra ~2.79GHz esperado do artigo -
# ~500MHz de diferenca, ordem de grandeza e topologia corretas
# (confirmadas pela foto), aceito como validacao suficiente por ora
# (mesmo padrao ja usado com a omega, ver README.md secao 5) - a
# diferenca residual provavelmente vem de simplificacoes (cobre como
# folha ideal em vez de espessura real de 0.018mm, malha) que nao vale
# a pena perseguir agora, ja que o proximo passo (migrar pro RO5880)
# vai reotimizar os parametros de qualquer forma.
#
# Estrutura em dict (mesmo padrao ja usado em omega_antenna_nv.py -
# REF/RO/RO_DIAMOND) para migrar UMA variavel de cada vez, mantendo o
# dict anterior intacto para comparacao/re-validacao se precisar.
SASAKI_VALIDATION = dict(
    name="Sasaki_FR4_Validation",
    eps_sub=4.3, tand_sub=0.03, h_sub=1.6,      # FR4, valores do artigo
    R=7.0,      # mm, raio do disco ("ring radius")
    r=0.5,      # mm, raio do furo ("hole radius")
    s=3.9,      # mm, deslocamento do furo - EXCENTRICO, nao concentrico
    g=0.1,      # mm, largura da fenda (litografia/corrosao fina do
                # artigo - NAO e o piso de 0.5mm do Achiles, ver
                # RO5880_STEP2_GAP abaixo)
    feed_len=23.0, feed_w_wide=3.3, feed_w_narrow=0.54,
    # camada de resist (mascara de solda) - cobre toda a face de cima,
    # inclusive por cima da fenda/furo. Sem isso a ressonancia validada
    # ficou em ~3.48GHz em vez de ~3.28GHz - efeito real, mantido em
    # todos os passos seguintes tambem.
    tr=0.03, eps_resist=4.3, tand_resist=0.025,
    # placa de simulacao (nao e R_out/W_ring do anel fino - dimensoes
    # proprias para caber o disco R=7mm + a linha de 23mm + margem)
    L_sub=60.0, W_sub=30.0,
)
# NOTA (ainda valida): a posicao exata da linha de alimentacao em
# relacao ao eixo da fenda foi inferida da FOTO real (Fig. 1a) - linha
# e fenda entram pelo mesmo lado do disco, quase colineares. Ver
# feed_y_off em build_disk_hole_resonator() para o calculo exato.

# ---------------------------------------------------------------
# Passo 1 da migracao (ver roadmap.md secao 0/6): trocar FR4 por
# RO5880 (material E espessura, ja que RO5880 so existe no estoque do
# projeto em 0.75mm - nao faz sentido testar noutra espessura). g, R,
# r, s e o taper ainda NAO mudam nesta rodada - isolando o efeito do
# substrato sozinho antes de mexer em mais nada.
# ---------------------------------------------------------------
RO5880_STEP1_MATERIAL = copy.deepcopy(SASAKI_VALIDATION)
RO5880_STEP1_MATERIAL["name"] = "RO5880_Step1_Material"
RO5880_STEP1_MATERIAL["eps_sub"] = 2.20
RO5880_STEP1_MATERIAL["tand_sub"] = 0.0009
RO5880_STEP1_MATERIAL["h_sub"] = 0.75
# 2026-09-19: rodado - so trocar o material (mantendo g=0.1mm do
# artigo) deslocou a ressonancia de ~3.28GHz para ~4.23GHz (subiu,
# como esperado - RO5880 tem eps_r menor que FR4). Profundidade caiu
# de -7.3dB para -1.1dB - tambem esperado, o taper (3.3/0.54mm) foi
# dimensionado para 50 ohm em FR4/1.6mm, nao vale mais para
# RO5880/0.75mm (isso e o passo 4 do plano, ainda nao chegamos la).

# ---------------------------------------------------------------
# Passo 2 da migracao: aumentar o gap de 0.1mm (litografia) para
# 0.5mm (piso de fabricacao pedido pelo Achiles). Deve EMPURRAR a
# frequencia ainda MAIS pra cima (gap maior = menos capacitancia C0 =
# f0 mais alto, pela propria formula do artigo) - o proximo passo
# (3) vai precisar reotimizar R e s para trazer de volta a 2.87GHz.
# ---------------------------------------------------------------
RO5880_STEP2_GAP = copy.deepcopy(RO5880_STEP1_MATERIAL)
RO5880_STEP2_GAP["name"] = "RO5880_Step2_Gap"
RO5880_STEP2_GAP["g"] = 0.5
# 2026-09-19: rodado - contra a expectativa da formula "ingenua" do
# artigo (C0 ∝ 1/g, esperava subir mais), a frequencia na verdade
# DESCEU um pouco (4.23 -> 4.13GHz). A formula e so uma indicacao de
# tendencia local, nao serve pra extrapolar 5x o gap - mesma licao ja
# registrada varias vezes neste projeto (nao confiar em formula/
# extrapolacao, confiar no resultado real). Profundidade tambem piorou
# um pouco (-0.75dB) - ainda dominado pelo taper descasado (passo 4).

# ---------------------------------------------------------------
# Passo 3 da migracao: reotimizar R e s de verdade (Optimetrics), nao
# mais tentar prever por formula, para trazer a ressonancia de volta a
# 2.87GHz. r e g ficam FIXOS (r=0.5mm pela logica do proprio artigo -
# "limit r to be around 0.5mm and adjust R and s"; g=0.5mm no piso de
# fabricacao). Placa aumentada para caber com folga o pior caso do
# otimizador (R_disk ate 20mm + feed_len 23mm = 43mm so de -x, mais
# margem) - o comprimento da linha agora e calculado a partir de
# R_disk, nao de L_sub (ver correcao 2026-09-19 em
# build_disk_hole_resonator - antes disso, a linha ficava fixa em
# L_sub/2 e quebraria a conexao com o disco assim que R_disk mudasse).
# ---------------------------------------------------------------
RO5880_STEP3_REOPT = copy.deepcopy(RO5880_STEP2_GAP)
RO5880_STEP3_REOPT["name"] = "RO5880_Step3_Reopt"
# 2026-09-19: placa e faixa de busca REDUZIDAS - a 1a tentativa
# (R_disk 8-20mm, placa 100x50mm) estava demorando demais por rodada
# (mesh grande + faixa ampla = otimizador testando pontos longe do
# necessario). Reduzindo para uma faixa mais moderada em torno do
# nominal (R=7, s=3.9) - se bater no teto, alarga de novo, mas comeca
# enxuto.
RO5880_STEP3_REOPT["L_sub"] = 78.0
RO5880_STEP3_REOPT["W_sub"] = 36.0
# 2026-09-19: rodado - convergiu (varias iteracoes proximas e
# consistentes) em R_disk~11.1mm, s_off~4.3-4.45mm, dB(S11) em
# 2.87GHz ~-0.72 a -0.73dB. FREQUENCIA CERTA - sucesso do Passo 3.
# Profundidade continua baixa, mas isso e esperado: o taper ainda usa
# larguras do FR4 (3.3/0.54mm), que nao servem para RO5880/0.75mm -
# e exatamente o Passo 4, a seguir.

# ---------------------------------------------------------------
# Passo 4 da migracao: recalcular a linha afunilada para RO5880/
# 0.75mm. R_disk/s_off FIXOS no ponto que already achou 2.87GHz certo
# (Passo 3) - so a linha muda agora, um problema de cada vez.
# feed_w_wide = WF (2.3mm) - o mesmo valor de 50 ohm em RO5880/0.75mm
# ja usado no resto do projeto (anel fino), nao precisa recalcular.
# feed_w_narrow nao tem uma formula direta (era so uma medida do
# artigo em FR4/1.6mm) - vira variavel livre na otimizacao
# add_taper_optimization, junto com feed_len (pode precisar de um
# comprimento diferente de 23mm tambem).
# ---------------------------------------------------------------
RO5880_STEP4_TAPER = copy.deepcopy(RO5880_STEP3_REOPT)
RO5880_STEP4_TAPER["name"] = "RO5880_Step4_Taper"
RO5880_STEP4_TAPER["R"] = 11.1
RO5880_STEP4_TAPER["s"] = 4.4
RO5880_STEP4_TAPER["feed_w_wide"] = WF
# placa alargada em x: feed_len agora livre ate 30mm (add_taper_
# optimization) + R_disk fixo em 11.1mm = precisa de pelo menos 41mm
# so do lado -x, mais margem
RO5880_STEP4_TAPER["L_sub"] = 90.0
# 2026-09-19: rodado - convergiu em feed_len~18.1mm, feed_w_narrow~
# 0.82mm, mas dB(S11) em 2.87GHz ficou em SO ~-0.5dB - PIOR que os
# -0.73dB do Passo 3 (que ainda usava feed_w_wide=3.3mm do FR4, nao
# 2.3mm). Sinal de que travar R_disk/s_off no ponto do Passo 3 nao e
# mais o ideal agora que a linha mudou - as 4 variaveis interagem mais
# do que o esperado para tratar "uma de cada vez". Proximo passo:
# otimizacao CONJUNTA das 4 variaveis juntas (mesma licao da omega e
# do anel fino - multivariavel escapa de platos que otimizacao
# sequencial nao consegue).

# ---------------------------------------------------------------
# Passo 5 da migracao: otimizacao CONJUNTA de R_disk, s_off,
# feed_w_narrow e feed_len - abandona a abordagem sequencial "uma
# variavel de cada vez" porque os passos 3+4 mostraram que essas 4
# variaveis interagem entre si (o taper otimizado para um R_disk/s_off
# fixo NAO era o mesmo taper otimo depois que a largura larga mudou).
# Comeca a partir do melhor ponto conhecido de cada etapa anterior.
# ---------------------------------------------------------------
RO5880_STEP5_JOINT = copy.deepcopy(RO5880_STEP4_TAPER)
RO5880_STEP5_JOINT["name"] = "RO5880_Step5_Joint"
RO5880_STEP5_JOINT["feed_w_narrow"] = 0.82
RO5880_STEP5_JOINT["feed_len"] = 18.1
# 2026-09-19: rodado - a otimizacao conjunta (4 variaveis) so chegou a
# ~-0.65dB no melhor caso, PIOR do que qualquer coisa desde o Passo 3.
# Com 4 graus de liberdade e ainda travado num teto tao raso, o
# problema provavelmente NAO e falta de ajuste fino - e algo
# estrutural. Suspeita levantada pelo usuario: a camada de RESIST
# (herdada da validacao em FR4, nunca questionada para o RO5880) cobre
# a linha de alimentacao inteira - se isso mudar a impedancia
# caracteristica da linha de 2.3mm (WF, calculado para RO5880 SEM
# resist), o descasamento estaria bem NA PORTA, antes do sinal chegar
# no ressoador - explicando por que nada rio abaixo (R_disk, s_off,
# taper) consegue compensar.

# ---------------------------------------------------------------
# Passo 6 (diagnostico): mesmo ponto do Passo 5 (melhor conhecido),
# mas SEM a camada de resist (tr=0) - testa diretamente a hipotese
# acima. Roda so 1 solve (RING_MODE="validate_sasaki_fr4"), nao uma
# otimizacao - e um teste de diagnostico, nao busca de novos valores.
# ---------------------------------------------------------------
RO5880_STEP6_NO_RESIST = copy.deepcopy(RO5880_STEP5_JOINT)
RO5880_STEP6_NO_RESIST["name"] = "RO5880_Step6_NoResist"
RO5880_STEP6_NO_RESIST["tr"] = 0
# 2026-09-19: rodado - PIOROU ainda mais (~-0.42dB) sem o resist.
# Descarta a hipotese do resist como causa principal. Com isso, 5
# tentativas diferentes (Passos 3/4/5/6) e nenhuma chegou perto de um
# casamento razoavel - sinal forte de que o problema NAO esta em
# nenhum parametro geometrico especifico, e sim em algo mais basico
# nunca validado: a porta/linha de microfita em si. O plano original
# (diagnostico externo, secao 4.1) recomendava validar isso PRIMEIRO,
# com uma linha reta de 2 portos, antes de confiar em qualquer
# resultado do ressoador - passo que foi pulado ate agora porque a
# validacao em FR4 (que usava a largura do ARTIGO, 3.3mm, nao uma
# calculada por nos) deu certo e criou falsa confianca de que a
# porta/linha em geral estava OK.

# ---------------------------------------------------------------
# Passo 7 (diagnostico): validar a porta/linha em isolamento - linha
# reta de microfita, DOIS portos, RO5880/0.75mm, largura WF=2.3mm
# (o valor que estamos assumindo como 50 ohm, nunca confirmado por
# teste direto). Esperado: S11 < -20dB, S21 ~0dB em toda a faixa. Se
# isso falhar, o problema esta na porta ou na largura, nao no
# ressoador - e explicaria por que nada no ressoador ajudou ate agora.
# ---------------------------------------------------------------
TEST_LINE_2PORT = dict(
    name="Test_Line_2Port",
    eps_sub=2.20, tand_sub=0.0009, h_sub=0.75,
    feed_w_wide=WF,
    L_sub=40.0, W_sub=20.0,
)
# 2026-09-19: rodado - S11 < -28dB e S21 ~0dB em toda a faixa
# 2.5-3.2GHz. CONFIRMADO: a porta e a largura WF=2.3mm estao corretas
# em RO5880/0.75mm - o problema NAO esta na porta/linha, esta na
# geometria do ressoador (disco+furo+fenda).

# ---------------------------------------------------------------
# Passo 8 (diagnostico): a otimizacao do Passo 3 (so mirando
# frequencia) convergiu em R_disk=11.1/s_off=4.4, o que da uma
# CONSTRICAO (R-s-r, a "ponte" indutiva entre o furo e a borda) de
# 6.2mm - bem mais LARGA, proporcionalmente ao raio do disco (56%),
# que a do artigo original validado em FR4 (R=7/s=3.9/r=0.5 ->
# constricao 2.6mm, so 37% de R). Hipotese: uma constricao larga
# demais nao concentra corrente como um "gargalo" indutivo de
# verdade - vira mais uma chapa difusa, o que pode impedir o
# casamento independente de como a linha e ajustada.
# Teste: mesma "largura de placa do capacitor" (R+s-r ~ 15mm, a
# quantidade que a formula do artigo liga a frequencia) MAS com uma
# constricao proporcionalmente estreita como a do artigo (~2.6mm) -
# isola se a LARGURA DA CONSTRICAO em si e o problema, independente
# da frequencia exata bater ou nao em 2.87GHz.
# ---------------------------------------------------------------
RO5880_STEP8_NARROW_NECK = copy.deepcopy(RO5880_STEP5_JOINT)
RO5880_STEP8_NARROW_NECK["name"] = "RO5880_Step8_NarrowNeck"
RO5880_STEP8_NARROW_NECK["R"] = 9.3
RO5880_STEP8_NARROW_NECK["s"] = 6.2
# 2026-09-19/20: rodado (2x, confirmado nao ser cache) - PIOROU ainda
# mais (~-0.36dB). Descarta tambem a largura da constricao. Depois de
# 4 hipoteses descartadas (resist, porta/linha, constricao, cache de
# malha - ver roadmap.md secao "Plano de migracao" itens 6-11), analise
# externa (2026-09-20) apontou o motivo provavel: um taper LINEAR so
# transforma a parte REAL da impedancia, nao cancela reatancia. Sem
# nunca termos olhado a impedancia complexa (Zin), estavamos ajustando
# largura/comprimento as cegas contra uma carga que pode ter reatancia
# significativa - nenhum taper resolve isso, precisa de um elemento
# reativo de verdade (stub, por exemplo).

# ---------------------------------------------------------------
# Passo 9 (diagnostico): extrair Zin=R+jX de verdade, nao so dB(S11).
# Mesma geometria do Passo 8 (R=9.3/s=6.2, ja ressoa perto de 2.87GHz),
# mas com a linha de alimentacao SEM afunilar (feed_w_narrow=feed_w_wide
# =WF) - assim medimos a impedancia "crua" que o disco apresenta a uma
# linha de 50 ohm reta, sem misturar isso com a transformacao do taper
# (que vamos substituir por uma rede de casamento com stub de qualquer
# forma). Zin = 50*(1+S11)/(1-S11), calculado direto do S11 complexo
# pelo proprio script Python (nao precisa de Smith Chart na GUI).
# ---------------------------------------------------------------
RO5880_STEP9_ZIN_PROBE = copy.deepcopy(RO5880_STEP8_NARROW_NECK)
RO5880_STEP9_ZIN_PROBE["name"] = "RO5880_Step9_ZinProbe"
RO5880_STEP9_ZIN_PROBE["feed_w_narrow"] = WF
RO5880_STEP9_ZIN_PROBE["feed_len"] = 15.0
# 2026-09-20: rodado - RESULTADO DECISIVO. Em f=2.87GHz,
# Zin = 0.55 + 0.60j ohm - quase um curto (razao de transformacao
# necessaria para 50 ohm: ~91:1). Explica todo o historico de
# casamento raso: nenhum taper linear transforma uma razao dessas de
# forma robusta, e muito menos cancela a reatancia junto. A linha
# conecta perto da fenda, o lado de baixa impedancia de um laco
# ressonante em serie (equivalente a alimentar um tanque LC no no de
# "terra" dele). Ver roadmap.md Passo 13/14.

# ---------------------------------------------------------------
# Passo 14 (diagnostico): mover o PONTO DE CONEXAO da linha para
# outros lugares do perimetro do disco (feed_angle, ver
# build_disk_hole_resonator) e remedir Zin em cada um - procurando um
# ponto onde a impedancia natural ja esteja mais perto de 50 ohm,
# precisando de menos transformacao. 3 designs no mesmo projeto
# (angulos 45/90/135 graus a partir da posicao historica em -x/perto
# da fenda) - evita 0 e 180 graus, onde a fenda e o furo ficam.
# ---------------------------------------------------------------
# placa QUADRADA e generosa (65x65mm) - girar o ponto de conexao move
# a porta para fora do eixo -x original, em qualquer direcao dependendo
# do angulo (para 45/90/135 graus a posicao efetiva fica entre -x/-y e
# +x/-y) - a placa retangular estreita herdada (90x36mm, pensada so
# para a porta em -x) NAO cobriria isso; precisa de raio >= R_disk+
# feed_len+margem (~9.3+15+2=26mm) em QUALQUER direcao a partir da
# origem.
ANGLE_TEST_45 = copy.deepcopy(RO5880_STEP9_ZIN_PROBE)
ANGLE_TEST_45["name"] = "AngleTest_45deg"
ANGLE_TEST_45["feed_angle"] = 45.0
ANGLE_TEST_45["L_sub"] = 65.0
ANGLE_TEST_45["W_sub"] = 65.0

ANGLE_TEST_90 = copy.deepcopy(RO5880_STEP9_ZIN_PROBE)
ANGLE_TEST_90["name"] = "AngleTest_90deg"
ANGLE_TEST_90["feed_angle"] = 90.0
ANGLE_TEST_90["L_sub"] = 65.0
ANGLE_TEST_90["W_sub"] = 65.0

ANGLE_TEST_135 = copy.deepcopy(RO5880_STEP9_ZIN_PROBE)
ANGLE_TEST_135["name"] = "AngleTest_135deg"
ANGLE_TEST_135["feed_angle"] = 135.0
ANGLE_TEST_135["L_sub"] = 65.0
ANGLE_TEST_135["W_sub"] = 65.0

ANGLE_TEST_MODELS = [ANGLE_TEST_45, ANGLE_TEST_90, ANGLE_TEST_135]
# 2026-09-20/21: rodado - a parte REAL de Zin fica travada perto de
# 0.5-1 ohm em TODOS os angulos testados (45/90/135 graus), so a
# reatancia muda. Descarta o tap angular - a resistencia baixa e uma
# caracteristica intrinseca do modo (Q alto), nao um efeito de posicao
# de conexao galvanica. Ver roadmap.md Passo 14.

# ---------------------------------------------------------------
# Passo 16: stub aberto em derivacao, calculado analiticamente por
# teoria de linha de transmissao a partir de Zin=0.55+0.60j ohm
# (Passo 13, feed_angle=0 - o ponto mais bem caracterizado). Deducao
# completa no roadmap.md; resumo:
#   zL = ZL/Z0 = 0.011 + 0.0120j (normalizado)
#   Resolvendo Re(Yin(d))=Y0 (equacao quadratica em t=tan(beta*d)):
#     t = -0.11702 ou +0.09275
#   Escolhida a raiz que da uma distancia maior (mais longe de efeitos
#   de campo proximo/borda do disco, mais facil de construir sem
#   conflito com a malha do gap): d ~ 0.4815*lambda_g
#   Nesse ponto, Im(Yin) ~ +9.43 (normalizado) - o stub aberto precisa
#   cancelar isso: tan(beta*l) = -9.43 -> l ~ 0.2670*lambda_g
#   lambda_g ~76.4mm (formula padrao de eps_eff de microfita, RO5880/
#   0.75mm, trilha 2.3mm, 2.87GHz)
#   => stub_distance ~ 36.6mm, stub_length ~ 20.3mm
# feed_len aumentado para caber o stub + margem ate a porta; placa
# aumentada de acordo (porta e stub ficam bem mais longe do disco
# agora).
# ---------------------------------------------------------------
RO5880_STEP16_STUB = copy.deepcopy(RO5880_STEP9_ZIN_PROBE)
RO5880_STEP16_STUB["name"] = "RO5880_Step16_Stub"
RO5880_STEP16_STUB["stub_distance"] = 36.6
RO5880_STEP16_STUB["stub_length"] = 20.3
RO5880_STEP16_STUB["feed_len"] = 46.6
RO5880_STEP16_STUB["L_sub"] = 118.0
RO5880_STEP16_STUB["W_sub"] = 52.0

# qual dict usar agora - mudar aqui para avancar de passo
SASAKI_MODEL = RO5880_STEP16_STUB

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
    if G_SLOT < MIN_FEATURE:
        p.append(f"anel: G_SLOT={G_SLOT}mm abaixo do minimo de "
                 f"fabricacao ({MIN_FEATURE}mm, pedido do Achiles em "
                 "18/09/2026)")
    if W_RING < MIN_FEATURE:
        p.append(f"anel: W_RING={W_RING}mm abaixo do minimo de "
                 f"fabricacao ({MIN_FEATURE}mm)")
    if not 0.0 < FEED_OVERLAP_FRAC < 1.0:
        p.append(f"anel: FEED_OVERLAP_FRAC={FEED_OVERLAP_FRAC} tem que "
                 "ficar entre 0 e 1 (fracao da largura do anel)")
    if 2 * RING_ROUT_MAX >= min(L_SUB, W_SUB):
        p.append(f"anel: R_out={RING_ROUT_MAX}mm (teto da otimizacao) "
                 "nao cabe na placa")
    feed_overlap_mm = FEED_OVERLAP_FRAC * W_RING
    feed_ring = L_SUB / 2 - RING_ROUT_MAX + feed_overlap_mm
    if feed_ring <= 1.0:
        p.append(f"anel: microfita curta demais ({feed_ring:.1f} mm)")
    if R_OUT - W_RING <= 5 * G_SLOT:
        p.append("anel: R_in pequeno demais em relacao a fenda")

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
    print(f"  (A) anel   : R_in={R_OUT-W_RING:.2f} R_out={R_OUT} "
          f"W_ring={W_RING} g={G_SLOT} "
          f"feed_overlap={feed_overlap_mm:.2f}mm "
          f"({FEED_OVERLAP_FRAC*100:.0f}% da largura)")
    print(f"               microfita = {L_SUB/2-R_OUT+feed_overlap_mm:.1f} mm")
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
    # 2026-09-19: MaximumPasses subido de 15 para 25 - descoberto que
    # "Adaptive Passes did not converge based on specified criteria"
    # em varias rodadas do disco+furo excentrico (Message Manager).
    # Combinado com o refinamento local de malha no gap
    # (Mesh_Region_Gap, ver build_disk_hole_resonator), deve dar
    # espaco suficiente para convergir de verdade.
    hfss.create_setup(
        name="Setup1", setup_type="HFSSDriven",
        Frequency=f"{F0_GHZ}GHz", MaximumPasses=25, MaxDeltaS=0.01)
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
    """Anel fendido de UM PORTO - TRILHA FINA (corrigido 2026-09-18).

    R_out = raio externo do anel; R_in = R_out - W_ring = raio interno
    (tambem o raio da abertura optica, onde o diamante vai ficar por
    cima). ANTES desta correcao, "r_hole" era um furinho de 0.5mm fixo
    dentro de um disco quase solido ate R_out - a trilha nao tinha
    largura definida. Ver comentario no bloco de parametros acima para
    o porque isso importa (dois sintomas ruins na 1a rodada real:
    R_out precisou ficar enorme, e o casamento ficou raso).
    """
    common_variables(hfss)
    hfss["R_out"] = f"{R_OUT}mm"
    hfss["W_ring"] = f"{W_RING}mm"
    hfss["R_in"] = "R_out - W_ring"
    hfss["g_slot"] = f"{G_SLOT}mm"
    # feed_overlap_frac (0..1) garante, por construcao, que o tap nunca
    # ultrapassa a largura do anel - ver nota no bloco de parametros
    hfss["feed_overlap_frac"] = f"{FEED_OVERLAP_FRAC}"
    hfss["feed_overlap"] = "feed_overlap_frac * W_ring"
    build_substrate_and_ground(hfss)

    ring = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_out", name="Ring_outer")
    hole = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_in", name="Ring_inner")
    hfss.modeler.subtract(ring, [hole], keep_originals=False)

    # fenda radial: interrompe o anel de lado a lado. Criada em +x
    # (posicao default, oposta a entrada da linha em -x) e depois GIRADA
    # em torno do centro do anel por gap_rotation - esse angulo, nao a
    # penetracao radial (feed_overlap), e o TAP de casamento de
    # impedancia de verdade (ver nota 2026-09-19 no bloco de parametros:
    # variar so feed_overlap_frac com o angulo fixo nao teve efeito
    # real, o otimizador nem saiu do ponto de partida).
    hfss["gap_rotation"] = f"{GAP_ROTATION_DEG}deg"
    slot = hfss.modeler.create_rectangle(
        orientation="XY", origin=["0mm", "-g_slot/2", "h_sub"],
        sizes=["R_out + 1mm", "g_slot"], name="Slot")
    slot.rotate(axis="Z", angle="gap_rotation")
    hfss.modeler.subtract(ring, [slot], keep_originals=False)

    # microfita de 50 ohm entrando por -x (oposto a fenda), penetrando
    # feed_overlap DENTRO da largura do anel (agora um TAP de verdade,
    # nao so uma sobreposicao de malha - controla o casamento)
    hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-Wf/2", "h_sub"],
        sizes=["L_sub/2 - R_out + feed_overlap", "Wf"],
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
# 4C. Disco com furo excentrico (Sasaki 2016) - validacao + migracao
# ---------------------------------------------------------------
def build_disk_hole_resonator(hfss, p):
    """Disco + furo excentrico + fenda + linha afunilada. Parametrizado
    por dict `p` (ver SASAKI_VALIDATION / RO5880_STEP1_MATERIAL acima)
    para poder migrar UMA variavel de cada vez sem duplicar a funcao -
    mesmo padrao ja usado em omega_antenna_nv.py (dicts REF/RO).

    Geometria (Fig. 1a/b do artigo, confirmada por extracao direta do
    texto E da FOTO real do PDF):
      - Disco condutor de raio p['R'], centrado na origem.
      - Furo de raio p['r'], EXCENTRICO - centro deslocado por p['s']
        ao longo de +x (nao concentrico com o disco). Isso cria uma
        "constricao" estreita de largura (R-s-r) do lado +x (entre o
        furo e a borda do disco) - e o caminho INDUTIVO da ressonancia
        LC serie.
      - Fenda radial de largura p['g'], do lado -x (lado LARGO do
        disco, onde sobra mais condutor entre o furo e a borda:
        R+s-r) - e o CAPACITOR da ressonancia.
      - Linha de alimentacao AFUNILADA (nao largura constante!):
        p['feed_w_wide'] (SMA) ate p['feed_w_narrow'] (ressoador), ao
        longo de p['feed_len']. O afunilamento em si e o casamento de
        impedancia.
      - Camada de resist por cima de tudo (p['tr']/p['eps_resist']) -
        sem ela a ressonancia validada saiu ~200MHz mais alta.

    A linha entra pela borda em -x (mesmo lado da fenda, confirmado
    pela foto real Fig. 1a - linha e fenda praticamente colineares),
    deslocada em y por feed_y_off para nao cair dentro da propria
    fenda.
    """
    hfss["h_sub"] = f"{p['h_sub']}mm"
    hfss["L_sub"] = f"{p['L_sub']}mm"
    hfss["W_sub"] = f"{p['W_sub']}mm"
    # "airgap" e usado por add_airbox_and_setup() - normalmente vem de
    # common_variables(), que nao chamamos aqui (ela tambem definiria
    # Wf/r_hole do anel fino, que nao fazem sentido pra esta geometria)
    hfss["airgap"] = f"{AIRGAP}mm"
    hfss["R_disk"] = f"{p['R']}mm"
    hfss["r_hole"] = f"{p['r']}mm"
    hfss["s_off"] = f"{p['s']}mm"
    hfss["g_gap"] = f"{p['g']}mm"
    hfss["feed_len"] = f"{p['feed_len']}mm"
    hfss["feed_w_wide"] = f"{p['feed_w_wide']}mm"
    hfss["feed_w_narrow"] = f"{p['feed_w_narrow']}mm"
    # deslocamento minimo em y para a linha nao cair dentro da fenda -
    # expressao parametrica (nao numero fixo), acompanha g_gap e
    # feed_w_narrow se algum dos dois mudar numa otimizacao futura
    hfss["feed_y_off"] = "g_gap/2 + feed_w_narrow/2"
    # a ponta estreita da linha precisa de uma folga extra alem da
    # borda nominal do disco (ver historico 2026-09-19: sem isso,
    # sobrava uma fresta de poucos micrometros sem sobreposicao real,
    # porque a linha fica deslocada para y=feed_y_off e a borda do
    # circulo e curva - mesma tecnica ja usada no feed_overlap do
    # anel fino)
    hfss["feed_overlap_margin"] = "0.3mm"
    # 2026-09-20: angulo (graus) de rotacao do PONTO DE CONEXAO da
    # linha ao redor do centro do disco - 0 = posicao historica (-x,
    # perto da fenda). Ver Passo 14 do roadmap.md: medimos Zin=0.55+
    # 0.60j ohm nessa posicao (perto de um curto - o lado de baixa
    # impedancia do laco ressonante em serie). Rotacionar o ponto de
    # conexao para outro lugar do perimetro do disco deve mudar bastante
    # essa impedancia, ja que pontos diferentes do laco tem impedancias
    # locais diferentes. Aplicado so a LINHA/PORTA, nao ao disco (que
    # mantem fenda/furo nas posicoes de sempre).
    hfss["feed_angle"] = f"{p.get('feed_angle', 0.0)}deg"

    sub_mat = get_or_create_material(hfss, f"sub_{p['name']}",
                                     p["eps_sub"], p["tand_sub"])

    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=sub_mat)

    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub"], name="Ground")
    hfss.assign_perfecte_to_sheets(ground.name)

    disk = hfss.modeler.create_circle(
        orientation="XY", origin=["0mm", "0mm", "h_sub"],
        radius="R_disk", name="Disk")
    hole = hfss.modeler.create_circle(
        orientation="XY", origin=["s_off", "0mm", "h_sub"],
        radius="r_hole", name="Hole")
    hfss.modeler.subtract(disk, [hole], keep_originals=False)

    # fenda: do lado -x (largo), comprimento R_disk+s-r (+1mm de folga
    # para garantir que corta a borda do disco por completo)
    gap = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-(R_disk + 1mm)", "-g_gap/2", "h_sub"],
        sizes=["R_disk + s_off - r_hole + 1mm", "g_gap"], name="Gap")
    hfss.modeler.subtract(disk, [gap], keep_originals=False)

    # 2026-09-19: malha local restrita ao GAP - achado que a malha
    # adaptativa NAO estava convergindo ("Adaptive Passes did not
    # converge based on specified criteria", visto no Message Manager
    # apos varias rodadas com S11 raso demais). Mesma tecnica ja usada
    # e documentada em omega_antenna_nv.py (Mesh_Region_Gap): uma
    # caixa de ar fina, restrita a vizinhanca do gap, com malha
    # forcada a g/3 - refinar a folha do disco INTEIRA no tamanho do
    # gap explodiria a contagem de celulas (o disco tem ~20mm, o gap
    # so 0.5mm). O resto do condutor usa a malha padrao do HFSS.
    gap_margin = max(p["g"] * 6, 0.05)
    try:
        gap_region = hfss.modeler.create_box(
            origin=["-(R_disk + 1mm)", f"-(g_gap/2 + {gap_margin}mm)",
                    "h_sub - 0.001mm"],
            sizes=["R_disk + s_off - r_hole + 1mm",
                   f"g_gap + {2*gap_margin}mm", "0.001mm"],
            name="Mesh_Region_Gap", material="vacuum")
        # "is_model" (nao "model") - ver nota identica em
        # omega_antenna_nv.py: "model" so cria atributo Python solto,
        # nao muda nada no AEDT.
        gap_region.is_model = False
        hfss.mesh.assign_length_mesh(
            [gap_region.name], maximum_length="g_gap/3", name="Mesh_Gap")
    except Exception as e:
        print("  aviso: nao consegui criar a operacao de malha do gap "
              f"automaticamente ({e}).")
        print("  Crie manualmente: HFSS > Mesh Operations > Assign >")
        print("  On Selection > Length Based, numa caixa em volta do Gap.")

    # linha de alimentacao afunilada - polígono de 4 pontos (trapezio),
    # nao um retangulo: largura varia de feed_w_wide (lado do SMA) a
    # feed_w_narrow (junto ao disco).
    # 2026-09-19: posicao calculada a partir de R_disk (nao de L_sub) -
    # o comprimento de 23mm (feed_len) e definido no artigo como a
    # linha INTEIRA do SMA ate o ressoador, entao o ponto largo (porta)
    # tem que ficar a feed_len de distancia da BORDA DO DISCO, nao da
    # borda da placa. Antes desta correcao, a porta ficava fixa em
    # "-L_sub/2" - funcionava por coincidencia no modelo de validacao
    # (L_sub foi escolhido especificamente para R=7 bater certinho),
    # mas quebraria a conexao assim que R_disk virasse variavel de
    # otimizacao (L_sub e fixo, R_disk nao - a linha ficaria curta ou
    # sobraria fora do disco). L_sub agora e so o tamanho da placa
    # (com folga), sem relacao direta com o comprimento da linha.
    feed_points = [
        ["-(R_disk + feed_len)", "feed_y_off - feed_w_wide/2", "h_sub"],
        ["-(R_disk + feed_len)", "feed_y_off + feed_w_wide/2", "h_sub"],
        ["-R_disk + feed_overlap_margin",
         "feed_y_off + feed_w_narrow/2", "h_sub"],
        ["-R_disk + feed_overlap_margin",
         "feed_y_off - feed_w_narrow/2", "h_sub"],
    ]
    feed = hfss.modeler.create_polyline(
        points=feed_points, cover_surface=True, close_surface=True,
        name="Feed_taper")
    # gira SO a linha (nao o disco) ao redor do centro, para conectar
    # em outro ponto do perimetro - ver nota de feed_angle acima
    feed.rotate(axis="Z", angle="feed_angle")

    to_unite = [disk, feed]

    # 2026-09-21: stub aberto em derivacao (Passo 16 do roadmap) -
    # casamento calculado analiticamente por teoria de linha de
    # transmissao a partir do Zin medido no Passo 13
    # (Zin=0.55+0.60j ohm em 2.87GHz, feed_angle=0). Formulas de
    # casamento por stub unico (derivacao aberta, sem via - mais
    # robusto para fabricacao em camada unica): a distancia
    # stub_distance (medida a partir da BORDA DO DISCO, ao longo da
    # linha, em direcao a porta) e escolhida para que a admitancia
    # normalizada NESSE PONTO tenha parte real = 1 (Y0); stub_length e
    # o comprimento do stub aberto que cancela a parte imaginaria
    # (susceptancia) que sobra nesse ponto. Ver deducao completa no
    # roadmap.md - resolve a equacao quadratica em t=tan(beta*d) vinda
    # de Re(Yin(d))=Y0, depois tan(beta*l)=-Im(Yin(d))/Y0 para o stub.
    # lambda_g ~76mm estimado p/ RO5880/0.75mm, trilha 2.3mm em
    # 2.87GHz (formula padrao de εeff de microfita) - os valores
    # nominais abaixo sao o ponto de partida do calculo, nao
    # necessariamente o otimo exato (a malha/solver real pode diferir
    # um pouco da formula analitica).
    if p.get("stub_distance") is not None:
        hfss["stub_distance"] = f"{p['stub_distance']}mm"
        hfss["stub_length"] = f"{p['stub_length']}mm"
        hfss["stub_width"] = f"{p.get('stub_width', p['feed_w_wide'])}mm"
        stub = hfss.modeler.create_rectangle(
            orientation="XY",
            origin=["-(R_disk + stub_distance) - stub_width/2",
                    "feed_y_off + feed_w_wide/2", "h_sub"],
            sizes=["stub_width", "stub_length"], name="Stub")
        stub.rotate(axis="Z", angle="feed_angle")
        to_unite.append(stub)

    hfss.modeler.unite(to_unite)
    disk.name = "Conductor"
    hfss.assign_perfecte_to_sheets(disk.name)

    port = hfss.modeler.create_rectangle(
        orientation="YZ",
        origin=["-(R_disk + feed_len)", "feed_y_off - feed_w_wide/2", "0mm"],
        sizes=["feed_w_wide", "h_sub"], name="Port1_sheet")
    # mesma rotacao na porta, para continuar alinhada com a ponta larga
    # da linha ja rotacionada
    port.rotate(axis="Z", angle="feed_angle")
    hfss.lumped_port(assignment=port.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")

    # camada de resist (mascara de solda) - OPCIONAL agora (2026-09-19).
    # So faz sentido para validar contra o artigo (Sasaki usa resist de
    # verdade no dispositivo deles). Para o RO5880 NAO sabemos se o
    # processo de fabricacao real (deposicao em Sao Carlos) vai aplicar
    # algum resist equivalente - suposicao nunca confirmada, herdada
    # sem questionar da validacao em FR4. Alem disso, o resist cobre a
    # linha de alimentacao inteira - se isso mudar a impedancia
    # caracteristica da linha (WF=2.3mm foi calculado para RO5880 SEM
    # resist), pode estar causando um descasamento bem NA PORTA, antes
    # mesmo do sinal chegar no ressoador - o que explicaria por que
    # nenhum ajuste de R_disk/s_off/taper melhorou o casamento (Passos
    # 3-5): a porta em si ja estaria errada, e nada rio abaixo consegue
    # compensar isso.
    if p.get("tr", 0) > 0:
        hfss["h_resist"] = f"{p['tr']}mm"
        resist_mat = get_or_create_material(
            hfss, f"resist_{p['name']}", p["eps_resist"], p["tand_resist"])
        hfss.modeler.create_box(
            origin=["-L_sub/2", "-W_sub/2", "h_sub"],
            sizes=["L_sub", "W_sub", "h_resist"],
            name="Resist", material=resist_mat)


# ---------------------------------------------------------------
# 4D. Linha reta de microfita, DOIS portos - validacao de porta/linha
# ---------------------------------------------------------------
def build_straight_line_2port(hfss, p):
    """Linha de microfita reta, sem ressoador nenhum - so para validar
    que a largura assumida como 50 ohm (p['feed_w_wide']) e a
    modelagem da porta (lumped port, integration_line ZNeg, folha do
    sinal ate o terra) realmente dao um bom casamento neste substrato.

    2026-09-19: nunca foi feito ate agora - o plano original de
    diagnostico (secao 4.1) recomendava isso ANTES de confiar em
    qualquer resultado do ressoador, mas foi pulado porque a validacao
    em FR4 (usando a largura literal do artigo, 3.3mm) deu certo e
    criou falsa confianca de que a porta/linha em geral estava correta.
    Depois de 4 tentativas de migracao (Passos 3-6) travadas todas
    perto de -0.5dB mesmo com 4 variaveis livres, ficou claro que
    precisa validar a porta em isolamento.

    Esperado (regra pratica de RF): S11 < -20dB, S21 ~0dB em toda a
    faixa, para uma linha reta bem dimensionada. Se isso NAO acontecer,
    o problema esta na porta ou na largura da linha, no no ressoador -
    explicaria os resultados ruins de todos os passos anteriores.
    """
    hfss["h_sub"] = f"{p['h_sub']}mm"
    hfss["L_sub"] = f"{p['L_sub']}mm"
    hfss["W_sub"] = f"{p['W_sub']}mm"
    hfss["airgap"] = f"{AIRGAP}mm"
    hfss["wf_test"] = f"{p['feed_w_wide']}mm"

    sub_mat = get_or_create_material(hfss, f"sub_{p['name']}",
                                     p["eps_sub"], p["tand_sub"])

    hfss.modeler.create_box(
        origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub", "h_sub"],
        name="Substrate", material=sub_mat)

    ground = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-W_sub/2", "0mm"],
        sizes=["L_sub", "W_sub"], name="Ground")
    hfss.assign_perfecte_to_sheets(ground.name)

    line = hfss.modeler.create_rectangle(
        orientation="XY", origin=["-L_sub/2", "-wf_test/2", "h_sub"],
        sizes=["L_sub", "wf_test"], name="Line")
    hfss.assign_perfecte_to_sheets(line.name)

    port1 = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["-L_sub/2", "-wf_test/2", "0mm"],
        sizes=["wf_test", "h_sub"], name="Port1_sheet")
    hfss.lumped_port(assignment=port1.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port1")

    port2 = hfss.modeler.create_rectangle(
        orientation="YZ", origin=["L_sub/2", "-wf_test/2", "0mm"],
        sizes=["wf_test", "h_sub"], name="Port2_sheet")
    hfss.lumped_port(assignment=port2.name,
                     integration_line=hfss.axis_directions.ZNeg,
                     impedance=50, name="Port2")


def add_disk_optimization(hfss):
    """Otimizacao (Quasi-Newton) do disco+furo excentrico, mirando
    2.87GHz apos a migracao para RO5880 + gap de 0.5mm (Passo 3).

    r e g ficam FIXOS: r=0.5mm segue a logica do proprio artigo ("we
    thus limit r to be around 0.5mm and adjust the remaining design
    parameters R and s to tune f0") - r define a concentracao de
    campo no furo, nao deve ser deixado livre so para achar frequencia
    (mesma logica ja aplicada a r_ap na omega e ao r_hole/W_ring no
    anel fino). g=0.5mm e o piso de fabricacao, sem motivo pra
    otimizador ir mais fundo.

    R e s livres - pela formula do artigo, C0 ∝ (R+s-r)/g, entao maior
    R+s = mais capacitancia = frequencia mais baixa (na direcao que
    precisamos, ja que o Passo 2 deixou a ressonancia em ~4.13GHz,
    acima do alvo). Faixas largas de proposito, ja que a formula ja
    se mostrou pouco confiavel para extrapolar (ver historico em
    RO5880_STEP2_GAP) - deixa o otimizador achar de verdade.

    Meta de profundidade modesta (-6dB, nao -15/-20dB): o taper ainda
    nao foi redimensionado para RO5880 (Passo 4, depois deste) e
    domina o casamento por enquanto - nao faz sentido perseguir um
    casamento profundo antes de corrigir isso.
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["R_disk", "s_off"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-6,
        goal_weight=1,
        name="Opt_disk_2p87GHz")
    # 2026-09-19: faixa REDUZIDA (era 8-20mm / 2-8mm, placa 100x50mm) -
    # cada iteracao numa placa/faixa tao grande estava lenta demais.
    # Comecando mais perto do nominal (R=7, s=3.9); se bater no teto
    # sem convergir, alarga de novo (mesma logica ja usada varias
    # vezes neste projeto - comecar enxuto, alargar so se precisar).
    setup.add_variation(
        "R_disk", min_value=7.0, max_value=13.0, starting_point=9.0)
    setup.add_variation(
        "s_off", min_value=3.0, max_value=6.0, starting_point=4.0)
    return setup


def add_taper_optimization(hfss):
    """Otimizacao (Quasi-Newton) da linha de alimentacao afunilada,
    mirando 2.87GHz - Passo 4 da migracao (RO5880_STEP4_TAPER).

    R_disk e s_off ficam FIXOS no ponto que ja acertou a frequencia
    (Passo 3: R_disk=11.1, s_off=4.4, dB(S11)~-0.73dB em 2.87GHz) - um
    problema de cada vez. feed_w_wide tambem fica fixo em WF=2.3mm (o
    valor de 50 ohm ja estabelecido para RO5880/0.75mm no resto do
    projeto).

    feed_w_narrow e feed_len ficam livres: nao ha uma formula direta
    para eles (o 0.54mm/23mm do artigo foram obtidos por simulacao 3D
    completa em FR4/1.6mm, nao por uma regra que se possa reescalonar).
    feed_w_narrow tem piso em MIN_FEATURE (0.5mm) - restricao de
    fabricacao do Achiles, nao da pra ir mais fino que isso mesmo que
    o casamento pedisse.

    Meta de profundidade real agora (-10dB, nao mais -6dB): a
    frequencia ja esta resolvida (Passo 3), entao este passo E sobre
    casamento de impedancia de verdade.
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["feed_w_narrow", "feed_len"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-10,
        goal_weight=1,
        name="Opt_taper_2p87GHz")
    setup.add_variation(
        "feed_w_narrow", min_value=MIN_FEATURE, max_value=2.0,
        starting_point=1.0)
    setup.add_variation(
        "feed_len", min_value=10.0, max_value=30.0, starting_point=23.0)
    return setup


def add_joint_optimization(hfss):
    """Otimizacao (Quasi-Newton) CONJUNTA de R_disk, s_off,
    feed_w_narrow e feed_len - Passo 5 da migracao (RO5880_STEP5_JOINT).

    Por que: os Passos 3 (so R_disk/s_off) e 4 (so a linha, com
    R_disk/s_off travados no resultado do Passo 3) foram feitos em
    sequencia, um de cada vez - metodologia que funcionou bem para
    achar a FREQUENCIA certa (Passo 3: sucesso, ~-0.73dB em 2.87GHz),
    mas o Passo 4 mostrou que essas variaveis interagem: o taper
    otimizado para o R_disk/s_off do Passo 3 deu resultado PIOR
    (~-0.5dB) do que o Passo 3 tinha (mesmo mirando casamento
    especificamente). Sinal classico de que fixar variaveis demais
    aprisiona a otimizacao num vale que nao e o melhor global - mesma
    licao ja registrada para a omega e o anel fino (precisaram de
    otimizacao multivariavel para escapar de platos).

    Faixas em torno dos melhores pontos ja encontrados em cada etapa
    anterior (nao mais exploracao ampla - ja sabemos a vizinhanca).

    g, r continuam FIXOS (piso de fabricacao / logica do artigo, ver
    add_disk_optimization). feed_w_wide continua fixo em WF (2.3mm,
    50 ohm em RO5880/0.75mm).
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["R_disk", "s_off", "feed_w_narrow", "feed_len"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-10,
        goal_weight=1,
        name="Opt_joint_2p87GHz")
    setup.add_variation(
        "R_disk", min_value=9.0, max_value=13.0, starting_point=11.1)
    setup.add_variation(
        "s_off", min_value=3.0, max_value=6.0, starting_point=4.4)
    setup.add_variation(
        "feed_w_narrow", min_value=MIN_FEATURE, max_value=2.0,
        starting_point=0.82)
    setup.add_variation(
        "feed_len", min_value=10.0, max_value=25.0, starting_point=18.1)
    return setup


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


def add_ring_wideband_scan(hfss):
    """Varredura (Optimetrics Parametric, NAO Optimization) de R_out na
    faixa larga 0.5-6GHz, so para achar onde a ressonancia real esta
    antes de tentar acertar 2.87GHz.

    2026-09-18: o diagnostico com R_out=20mm (fixo) achou UM vale claro
    em ~0.85GHz (o resto da faixa 0.5-6GHz e praticamente plano) - anel
    grande demais, ressoa baixo demais. Precisamos saber como a
    frequencia desse vale se desloca com R_out menor, para mirar o
    tamanho certo por interpolacao empirica em vez de formula na mao
    (a relacao L(R_out) de um laco fino tem log, nao e proporcional
    simples - nao da pra so escalar 20mm x (0.85/2.87) e confiar nisso).

    So 6 pontos (mais barato que uma otimizacao) - cada um resolve a
    faixa inteira 0.5-6GHz, entao ainda nao e rapido, mas da pontos
    empiricos suficientes pra interpolar.
    """
    setup = hfss.parametrics.add(
        "R_out", start_point="5mm", end_point="20mm", step="2.5mm",
        variation_type="LinearStep", name="Scan_Rout_wideband")
    return setup


def add_ring_optimization_multivar(hfss):
    """Otimizacao (Quasi-Newton) do anel fendido de UM PORTO, mirando
    2.87 GHz com o novo minimo de fabricacao (README secao 0, 2026-09-18).

    HISTORICO (tudo rodado de verdade pelo usuario no HFSS):
    - 1a/2a rodadas: geometria ERRADA (disco quase solido em vez de
      anel fino) - revelou o bug (casamento raso, so -2dB) mas nao a
      frequencia certa.
    - Corrigida a geometria (trilha fina de verdade). Diagnostico de
      varredura larga localizou a ressonancia de 2.87GHz entre R_out=15
      e 20mm.
    - 1a otimizacao com geometria corrigida (R_out + feed_overlap
      livres, W_ring fixo em 2mm): convergiu para R_out~16.3mm, bem
      perto de 2.87GHz, mas SO -0.63dB de profundidade.
    - 2a otimizacao (R_out + W_ring + feed_overlap_frac livres): PIOROU
      (-0.28dB). W_ring foi para perto do teto (3.7-4mm) e R_out perto
      do piso (13mm) sem melhorar a profundidade - sinal de que W_ring
      nao e o lever certo.
    - CORRECAO CONCEITUAL (2026-09-19): feed_overlap_frac controla a
      penetracao RADIAL da linha dentro da largura do anel, sempre no
      MESMO PONTO ANGULAR (oposto a fenda) - isso e so um detalhe local
      da juncao, nao o "tap" de casamento classico. O tap de verdade em
      ressoadores de laco e a POSICAO ANGULAR onde a linha se conecta em
      relacao a fenda: girando esse ponto ao redor do anel, amostra-se
      pontos diferentes da onda estacionaria de tensao/corrente, que e
      o que de fato transforma impedancia. Confirmado pela rodada
      anterior: com o angulo fixo, feed_overlap_frac nem saiu do ponto
      de partida (0.5) - baixa sensibilidade real.
      Trocado: W_ring volta a ser FIXO (2mm, o valor que deu a melhor
      frequencia+profundidade ate agora); a 3a variavel livre agora e
      gap_rotation (angulo de rotacao da fenda ao redor do centro do
      anel, ver build_ring) em vez de W_ring.

    IMPORTANTE para fabricacao: a posicao onde a linha de 50 ohm - que
    vai levar ao conector SMA soldado na placa de verdade - se conecta
    ao anel (definida por gap_rotation, e por feed_overlap_frac em
    escala menor) e o casamento de impedancia. Nao ha ajuste possivel
    depois de fabricado, por isso importa fechar isso bem agora.

    g_slot fica FIXO em MIN_FEATURE (0.5mm) - e o minimo de fabricacao
    pedido pelo Achiles, sem motivo pra otimizador ir mais fundo (nao
    fabricavel) nem pra subir alem disso ainda.
    """
    setup = hfss.optimizations.add(
        calculation="dB(S(Port1,Port1))",
        ranges={"Freq": f"{F0_GHZ}GHz"},
        variables=["R_out", "feed_overlap_frac", "gap_rotation"],
        optimization_type="Optimization",
        condition="<=",
        goal_value=-15,
        goal_weight=1,
        name="Opt_ring_1port_2p87GHz_v4")
    # faixa de R_out em torno da vizinhanca ja localizada (16.3mm), com
    # folga porque gap_rotation pode deslocar um pouco onde a
    # ressonancia cai
    setup.add_variation(
        "R_out", min_value=13.0, max_value=20.0, starting_point=16.3)
    # fracao do tap radial - mantido livre mas com efeito esperado
    # pequeno agora; nao custa deixar
    setup.add_variation(
        "feed_overlap_frac", min_value=0.05, max_value=0.95,
        starting_point=0.5)
    # ANGULO da fenda em torno do centro do anel (graus), relativo a
    # posicao default (+x, oposta a entrada da linha em -x = 0 graus de
    # rotacao). Faixa +-100 graus - evita chegar perto de +-180, onde a
    # fenda rotacionada colidiria com a propria linha de alimentacao
    # (que entra por -x).
    setup.add_variation(
        "gap_rotation", min_value=-100.0, max_value=100.0,
        starting_point=30.0)
    return setup


# ---------------------------------------------------------------
# 5. Execucao
# ---------------------------------------------------------------
# 2026-09-19: quando RING_MODE esta nos modos do disco+furo excentrico,
# constroi build_disk_hole_resonator() com SASAKI_MODEL (troque esse
# dict la em cima para avancar de passo na migracao) em vez do anel
# fino - ver roadmap.md secao 0. Nome do design vem do proprio dict
# (p['name']), um por passo de migracao, para nao misturar resultados
# no mesmo projeto (facilita comparar os passos lado a lado depois).
DISK_MODES = ("validate_sasaki_fr4", "optimize_disk_2p87",
              "optimize_taper", "optimize_joint", "extract_zin")
if RING_MODE in DISK_MODES:
    TOPOLOGIES = {
        SASAKI_MODEL["name"]:
            lambda h: build_disk_hole_resonator(h, SASAKI_MODEL)
    }
elif RING_MODE == "test_line_2port":
    # Passo 7 (diagnostico): linha reta de 2 portos, sem ressoador -
    # ver build_straight_line_2port e TEST_LINE_2PORT acima.
    TOPOLOGIES = {
        TEST_LINE_2PORT["name"]:
            lambda h: build_straight_line_2port(h, TEST_LINE_2PORT)
    }
elif RING_MODE == "test_feed_angles":
    # Passo 14 (diagnostico): 3 designs, um por angulo de conexao da
    # linha (ver ANGLE_TEST_MODELS acima) - usa closure com argumento
    # default (m=m) para nao capturar so a ULTIMA variavel do loop
    # (pegadinha classica de lambda dentro de loop em Python).
    TOPOLOGIES = {
        m["name"]: (lambda h, m=m: build_disk_hole_resonator(h, m))
        for m in ANGLE_TEST_MODELS
    }
else:
    # 2026-09-18: so o Ring por padrao - e a candidata de UM PORTO
    # pedida pelo Achiles (ver README secao 0). A Omega (dois portos)
    # foi deixada de fora daqui para nao gastar tempo/malha com uma
    # topologia que nao vai mais ser fabricada; para comparar as duas
    # de novo (uso historico), descomente a linha de baixo.
    TOPOLOGIES = {"Ring": build_ring}
    # TOPOLOGIES = {"Ring": build_ring, "Omega": build_omega}


def print_zin_table(hfss, target_freq=F0_GHZ, compact=False):
    """Extrai S(Port1,Port1) real/imag do sweep ja resolvido e imprime
    Zin=50*(1+S11)/(1-S11) - Re e Im - direto no terminal, sem precisar
    de Smith Chart na GUI. Se compact=True, imprime so o ponto mais
    proximo de target_freq (para comparar varios designs lado a lado,
    ver RING_MODE="test_feed_angles"); senao imprime a tabela inteira e
    aponta onde Im(Zin) mais se aproxima de zero (a ressonancia real).
    """
    import math
    try:
        sol = hfss.post.get_solution_data(
            expressions=["S(Port1,Port1)"],
            setup_sweep_name="Setup1 : Sweep1")
        freqs, s11_re = sol.get_expression_data(
            "S(Port1,Port1)", formula="real")
        _, s11_im = sol.get_expression_data(
            "S(Port1,Port1)", formula="imag")
        if not compact:
            print(f"\n{'Freq(GHz)':>10} {'dB(S11)':>10} {'Re(Zin)':>10} "
                  f"{'Im(Zin)':>10}")
        best_freq, best_abs_x = None, None
        deepest, deepest_db = None, None
        closest_to_target, closest_dist = None, None
        for f, re_s, im_s in zip(freqs, s11_re, s11_im):
            s = complex(re_s, im_s)
            mag = abs(s)
            db = 20 * math.log10(mag) if mag > 0 else float("-inf")
            denom = 1 - s
            if abs(denom) < 1e-9:
                continue
            zin = 50.0 * (1 + s) / denom
            if not compact:
                print(f"{f:>10.4f} {db:>10.2f} "
                      f"{zin.real:>10.2f} {zin.imag:>10.2f}")
            if best_abs_x is None or abs(zin.imag) < best_abs_x:
                best_abs_x = abs(zin.imag)
                best_freq = (f, zin.real, zin.imag)
            if deepest_db is None or db < deepest_db:
                deepest_db = db
                deepest = (f, db)
            dist = abs(f - target_freq)
            if closest_dist is None or dist < closest_dist:
                closest_dist = dist
                closest_to_target = (f, db, zin.real, zin.imag)
        if compact and closest_to_target:
            print(f"  f={closest_to_target[0]:.4f}GHz -> "
                  f"dB(S11)={closest_to_target[1]:.2f}, "
                  f"Zin={closest_to_target[2]:.2f}"
                  f"{closest_to_target[3]:+.2f}j ohm")
        else:
            if best_freq:
                print(f"\nPonto mais proximo de Im(Zin)=0: "
                      f"f={best_freq[0]:.4f}GHz, "
                      f"Zin={best_freq[1]:.2f}{best_freq[2]:+.2f}j ohm")
            if deepest:
                print(f"Vale mais fundo: f={deepest[0]:.4f}GHz, "
                      f"dB(S11)={deepest[1]:.2f}")
    except Exception as e:
        print(f"  nao consegui extrair Zin ({e}).")


if __name__ == "__main__":

    check_geometry()

    # 2026-09-20: sufixo unico (HHMMSS) no nome do design - descoberto
    # que rodar o script de novo com o MESMO nome de design (ex.:
    # "RO5880_Step8_NarrowNeck_Unloaded", repetido entre rodadas do
    # mesmo passo) fazia o AEDT reabrir/reaproveitar o design ja
    # existente e ja resolvido, em vez de reconstruir do zero -
    # confirmado pelo Message Manager mostrando so o sweep de
    # frequencia direto, SEM as mensagens de malha adaptativa, na
    # rodada que deveria ter testado a nova malha do gap. Isso
    # invalidava silenciosamente qualquer mudanca de codigo entre
    # rodadas (geometria, malha, setup) sempre que o nome nao mudava.
    run_suffix = time.strftime("%H%M%S")

    first = True
    hfss = None
    for topo, builder in TOPOLOGIES.items():
        design_name = f"{topo}_Unloaded_{run_suffix}"
        if first:
            hfss = Hfss(project=PROJECT_NAME, design=design_name,
                        solution_type="DrivenModal", new_desktop=True,
                        non_graphical=False)
            first = False
        else:
            hfss.insert_design(name=design_name,
                               solution_type="DrivenModal")
        builder(hfss)
        add_airbox_and_setup(hfss)

        if BUILD_ALUMINA:
            for case, d in ALUMINA_CASES.items():
                hfss.insert_design(name=f"{topo}_{case}_{run_suffix}",
                                   solution_type="DrivenModal")
                builder(hfss)
                add_alumina(hfss, d["La"], d["Wa"], d["ha"], case)
                add_airbox_and_setup(hfss)

    hfss.save_project()
    print("Projeto criado em:", hfss.project_file)
    print("Designs:", list(hfss.design_list))

    if RING_MODE == "extract_zin":
        print(f"\nRodando Setup1/Sweep1 no modelo "
              f"'{SASAKI_MODEL['name']}'... so 1 solve (pode demorar "
              f"mais que os anteriores - placa maior por causa do "
              f"stub).")
        hfss.analyze_setup("Setup1")
        hfss.save_project()
        print("Solve concluido. Extraindo dB(S11) e Zin direto via "
              "pyaedt (sem precisar de Smith Chart na GUI)...")
        print_zin_table(hfss)
        print("Se o stub funcionou, dB(S11) deve estar bem mais fundo "
              "que -1dB perto de 2.87GHz (o calculo analitico usou uma "
              "estimativa de lambda_g - pode precisar de um ajuste "
              "fino pequeno, nao um redesenho).")

    elif RING_MODE == "test_feed_angles":
        print(f"\nRodando Setup1/Sweep1 nos {len(ANGLE_TEST_MODELS)} "
              f"designs (angulos de conexao 45/90/135 graus)... "
              f"vai demorar mais porque sao varios solves.")
        for m in ANGLE_TEST_MODELS:
            design_full_name = None
            for dn in hfss.design_list:
                if dn.startswith(m["name"]):
                    design_full_name = dn
                    break
            if design_full_name is None:
                print(f"  aviso: nao achei o design de {m['name']}")
                continue
            hfss.set_active_design(design_full_name)
            print(f"\n=== {m['name']} (feed_angle={m['feed_angle']} "
                  f"graus) ===")
            hfss.analyze_setup("Setup1")
            print_zin_table(hfss, compact=True)
        hfss.save_project()
        print("\nCompare os 3 valores de Re(Zin) - o angulo com Re(Zin) "
              "mais perto de 50 (e Im(Zin) mais perto de 0) precisa de "
              "MENOS transformacao de impedancia.")

    elif RING_MODE == "test_line_2port":
        print(f"\nRodando Setup1/Sweep1 na linha reta de 2 portos "
              f"(sem ressoador)... so 1 solve, deve ser rapido.")
        hfss.analyze_setup("Setup1")
        hfss.save_project()
        print("Solve concluido. Va em Results > Modal Solution Data "
              "Report > 2D - dessa vez crie DUAS curvas: "
              "dB(S(Port1,Port1)) e dB(S(Port2,Port1)). Esperado: "
              "S11 < -20dB e S21 perto de 0dB em toda a faixa "
              "2.5-3.2GHz. Manda um print do grafico com as duas "
              "curvas. Se S11 NAO ficar bem fundo aqui (linha reta, "
              "sem ressoador nenhum), o problema esta na porta ou na "
              "largura de 2.3mm, nao no ressoador.")

    elif RING_MODE == "validate_sasaki_fr4":
        print(f"\nRodando Setup1/Sweep1 no modelo "
              f"'{SASAKI_MODEL['name']}'... so 1 solve.")
        hfss.analyze_setup("Setup1")
        hfss.save_project()
        print("Solve concluido. Va em Results > Modal Solution Data "
              "Report > 2D, dB(S(Port1,Port1)) vs Freq. Manda um print "
              "do grafico inteiro.")

    elif RING_MODE == "optimize_disk_2p87":
        print(f"\nCriando e rodando a otimizacao do disco+furo "
              f"excentrico (Opt_disk_2p87GHz - R_disk e s_off livres) "
              f"no modelo '{SASAKI_MODEL['name']}'... pode demorar "
              f"varios minutos. NAO feche a janela do AEDT enquanto "
              f"roda.")
        try:
            opt_setup = add_disk_optimization(hfss)
            opt_setup.analyze()
            hfss.save_project()
            print("Otimizacao concluida e projeto salvo.")
            print("Para ler o resultado: aba Results > Modal Solution "
                  "Data Report > 2D, dB(S(Port1,Port1)) - vai plotar "
                  "todas as variacoes testadas. Manda um print do "
                  "grafico e, se puder, a mensagem final do Message "
                  "Manager (tipo 'Optimization Analysis is done...').")
        except Exception as e:
            print(f"\nNao consegui rodar a otimizacao automaticamente "
                  f"({e}).")
            print("Faca manualmente na janela do AEDT que abriu: na "
                  "arvore do projeto, clique com o botao direito em "
                  "Optimetrics > Opt_disk_2p87GHz > Analyze.")

    elif RING_MODE == "optimize_taper":
        print(f"\nCriando e rodando a otimizacao do taper "
              f"(Opt_taper_2p87GHz - feed_w_narrow e feed_len livres, "
              f"R_disk/s_off fixos no ponto que ja acertou a "
              f"frequencia) no modelo '{SASAKI_MODEL['name']}'... "
              f"pode demorar varios minutos. NAO feche a janela do "
              f"AEDT enquanto roda.")
        try:
            opt_setup = add_taper_optimization(hfss)
            opt_setup.analyze()
            hfss.save_project()
            print("Otimizacao concluida e projeto salvo.")
            print("Para ler o resultado: aba Results > Modal Solution "
                  "Data Report > 2D, dB(S(Port1,Port1)) - vai plotar "
                  "todas as variacoes testadas. Manda um print do "
                  "grafico e, se puder, a mensagem final do Message "
                  "Manager.")
        except Exception as e:
            print(f"\nNao consegui rodar a otimizacao automaticamente "
                  f"({e}).")
            print("Faca manualmente na janela do AEDT que abriu: na "
                  "arvore do projeto, clique com o botao direito em "
                  "Optimetrics > Opt_taper_2p87GHz > Analyze.")

    elif RING_MODE == "optimize_joint":
        print(f"\nCriando e rodando a otimizacao CONJUNTA (R_disk, "
              f"s_off, feed_w_narrow, feed_len - as 4 juntas) no "
              f"modelo '{SASAKI_MODEL['name']}'... com 4 variaveis "
              f"isso deve demorar bem mais que os passos anteriores. "
              f"NAO feche a janela do AEDT enquanto roda.")
        try:
            opt_setup = add_joint_optimization(hfss)
            opt_setup.analyze()
            hfss.save_project()
            print("Otimizacao concluida e projeto salvo.")
            print("Para ler o resultado: aba Results > Modal Solution "
                  "Data Report > 2D, dB(S(Port1,Port1)) - vai plotar "
                  "todas as variacoes testadas. Manda um print do "
                  "grafico e, se puder, a mensagem final do Message "
                  "Manager.")
        except Exception as e:
            print(f"\nNao consegui rodar a otimizacao automaticamente "
                  f"({e}).")
            print("Faca manualmente na janela do AEDT que abriu: na "
                  "arvore do projeto, clique com o botao direito em "
                  "Optimetrics > Opt_joint_2p87GHz > Analyze.")

    elif "Ring" in TOPOLOGIES and RING_MODE == "diagnostic_single":
        print("\nRodando Setup1/Sweep1 (faixa larga 0.5-6GHz) na "
              "geometria nominal, so para achar onde a ressonancia "
              "esta de verdade. Isso NAO e uma otimizacao, e so 1 "
              "solve - deve ser mais rapido que as rodadas anteriores.")
        hfss.analyze_setup("Setup1")
        hfss.save_project()
        print("Solve concluido. Va em Results > Modal Solution Data "
              "Report > 2D, dB(S(Port1,Port1)) vs Freq, e procure ONDE "
              "aparece um vale (nao precisa ser em 2.87GHz ainda) - "
              "manda um print do grafico inteiro (0.5 a 6GHz).")

    elif "Ring" in TOPOLOGIES and RING_MODE == "diagnostic_grid":
        print("\nCriando e rodando a varredura de R_out (5-20mm, passo "
              "2.5mm, 7 pontos) na faixa larga 0.5-6GHz "
              "(Scan_Rout_wideband)... cada ponto resolve a faixa "
              "inteira, entao pode demorar bastante. NAO feche a "
              "janela do AEDT enquanto roda.")
        try:
            scan_setup = add_ring_wideband_scan(hfss)
            scan_setup.analyze()
            hfss.save_project()
            print("Varredura concluida e projeto salvo.")
            print("Para ler o resultado: aba Results > Modal Solution "
                  "Data Report > 2D, dB(S(Port1,Port1)) - vai plotar "
                  "as 7 curvas (uma por R_out) juntas. Manda um print "
                  "do grafico inteiro (0.5 a 6GHz) - vamos ver como o "
                  "vale se desloca com R_out e mirar o tamanho certo "
                  "para 2.87GHz por interpolacao.")
        except Exception as e:
            print(f"\nNao consegui rodar a varredura automaticamente "
                  f"({e}).")
            print("Faca manualmente na janela do AEDT que abriu: na "
                  "arvore do projeto, clique com o botao direito em "
                  "Optimetrics > Scan_Rout_wideband > Analyze.")

    elif "Ring" in TOPOLOGIES and RING_MODE == "optimize_2p87_multivar":
        print("\nCriando e rodando a otimizacao multivariavel do anel "
              "de 1 porto (Opt_ring_1port_2p87GHz_v4 - R_out, "
              "feed_overlap_frac e gap_rotation livres - esse ultimo e "
              "o angulo do tap, o lever de casamento de verdade)... "
              "com 3 variaveis isso deve demorar mais que as rodadas "
              "anteriores. NAO feche a janela do AEDT enquanto roda.")
        try:
            opt_setup = add_ring_optimization_multivar(hfss)
            opt_setup.analyze()
            hfss.save_project()
            print("Otimizacao concluida e projeto salvo.")
            print("Para ler o resultado: aba Results > Modal Solution "
                  "Data Report > 2D, dB(S(Port1,Port1)) - vai plotar "
                  "TODAS as variacoes testadas. NAO confie so no "
                  "grafico - passe o mouse/exporte (botao direito no "
                  "grafico > Export Data) e leia o valor exato em "
                  "2.87GHz da curva mais funda, ver README secao 5 "
                  "sobre esse erro ja cometido antes.")
        except Exception as e:
            print(f"\nNao consegui rodar a otimizacao automaticamente "
                  f"({e}).")
            print("Faca manualmente na janela do AEDT que abriu: na "
                  "arvore do projeto, clique com o botao direito em "
                  "Optimetrics > Opt_ring_1port_2p87GHz_v4 > Analyze.")

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
