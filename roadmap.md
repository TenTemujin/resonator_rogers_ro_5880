# Roadmap — Ressoador de 1 porto (anel fendido) para ODMR de NV⁻ em 2,87 GHz

Documento standalone: escrito para ser colado em outra IA (ChatGPT ou
qualquer outra) sem contexto prévio da conversa. Cobre só a linha de
trabalho ATIVA (anel fendido de 1 porto, iniciada em 2026-09-18). O
histórico anterior (antena ômega de 2 portos) está congelado e
documentado em `README.md` seções 0, 3, 5 e 6 — não é mais candidata a
fabricar, mas a metodologia de lá (como validar contra a literatura,
como não confiar em "vale mais fundo do gráfico") continua valendo.

Script de trabalho: `scripts/nv_resonators_compare.py`. Ambiente: Ansys
Electronics Desktop (AEDT) 2025 R2 **Student**, via `pyaedt` 1.6.0
(`import ansys.aedt.core`), Python 3.14.

---

## 0. ⚠️ CORREÇÃO CRÍTICA (2026-09-19) — LEIA PRIMEIRO

**A geometria de "anel fino" descrita nas seções 4/5 abaixo (histórico
até a v4) está sendo abandonada.** Um diagnóstico externo (revisão por
outra IA, depois **verificado por mim direto no texto extraído dos
PDFs originais** de Sasaki et al. 2016 e Misonou et al. 2020 — não é
suposição) mostrou que a interpretação da geometria da literatura
estava errada desde o início desta linha de trabalho.

**Geometria real (confirmada na Fig. 1(b) de Sasaki et al., Rev. Sci.
Instrum. 87, 053904 (2016), texto extraído diretamente do PDF):**

> "R (= 7.0 mm): ring radius, r (= 0.5 mm): hole radius, s (= 3.9 mm):
> distance between the ring and hole centers, g (= 0.1 mm): gap [...]
> To impedance-match with instrumental 50 Ω, the width of the
> 23-mm-long feed line is consecutively varied from 3.3 mm (SMA
> connector side) to 0.54 mm (ring edge)."

Ou seja, a estrutura real é um **disco quase sólido de raio R=7mm**,
com um **furo pequeno (r=0,5mm) DESLOCADO do centro** por uma distância
s=3,9mm (não concêntrico!), e uma **linha de alimentação AFUNILADA**
(3,3mm → 0,54mm ao longo de 23mm), não uma linha de largura constante
com um "tap" angular.

Modelo LC do próprio artigo (também extraído do texto original):
`L₀ ∝ r` (indutância vem do furo pequeno) · `C₀ ∝ (R+s−r)/g`
(capacitância do gap, com "largura de placa" R+s−r — a região LARGA de
conductor entre o furo deslocado e o gap) · `R₀ ∝ (R−s−r)⁻¹`
(resistência da **constrição estreita** entre o furo, empurrado para
perto da borda, e a borda do disco, do lado oposto ao gap).

**Isso resolve um mistério do código antigo**: o comentário herdado
`"R+s=10.9"` (em `nv_resonators_compare.py`, nunca decomposto
corretamente) era literalmente R=7,0 + s=3,9 = 10,9 — dois parâmetros
diferentes (raio do disco e deslocamento do furo), não uma largura de
anel único.

**Conclusão prática**: o que a seção 5 abaixo chama de "bug do disco
quase sólido" (5.1) **não era bug de arquitetura** — a estrutura
sólida estava estruturalmente mais perto do artigo do que o "anel
fino" que a substituiu. O erro real era (1) o furo estar CENTRADO em
vez de DESLOCADO, e (2) a linha de alimentação ter largura constante em
vez de afunilada. A hipótese de `gap_rotation` (rotação angular como
"tap" de casamento, seção 5.6/5.7) **fica pausada** — não é sustentada
pela literatura; o casamento real na literatura vem da geometria
excêntrica + do taper da linha, não de um ângulo de tap.

**Plano imediato (nada disso foi executado ainda — aguardando decisão
de prosseguir):**
1. Validar a linha de microfita/porta isoladamente (linha reta, 2
   portos, mesma pilha de materiais) antes de confiar em qualquer
   resultado do ressoador.
2. Reproduzir o dispositivo publicado (Antena #1 de Sasaki/Misonou) em
   **FR4** (εr=4,3, tanδ=0,03, h=1,6mm — não em RO5880ainda) com os
   parâmetros exatos acima, para validar contra um resultado conhecido
   (~2,79-2,87GHz, banda ~400MHz, Q~7).
3. Só depois, migrar UMA variável de cada vez para os materiais/
   restrições do projeto (RO5880, gap mínimo de 0,5mm, etc.),
   registrando o efeito de cada mudança isoladamente.
4. Reavaliar o resultado sempre pelo campo/corrente também, não só
   pelo vale do S11 (ver seção 6 abaixo, item "Avaliação de campo").

O histórico completo da linha de trabalho anterior (seções 4 e 5) fica
mantido abaixo **como registro do que já foi tentado e por que não
funcionou** — não é mais o plano ativo.

**Status (2026-09-19, rodado de verdade, várias iterações):**

1. Geometria construída e corrigida (2 bugs reais de API pyaedt
   encontrados e corrigidos: `create_circle` com nome de variável
   reservado `"R"` — renomeado para `R_disk`; e falta da variável
   `airgap`, que normalmente vem de `common_variables()`).
2. **Bug geométrico real encontrado e corrigido**: a ponta estreita da
   linha de alimentação, deslocada em y para não cair na fenda,
   ficava com uma fresta de poucos micrômetros sem sobreposição real
   com o disco (círculo é curvo) — a união não acusava erro, mas
   `Conductor` corria o risco de virar dois pedaços desconectados.
   Corrigido com uma folga extra (`feed_overlap_margin=0.3mm`).
3. **Validação em FR4 aceita**: primeira rodada (sem camada de
   resist) deu ressonância em ~3,48GHz; adicionando a camada de
   resist do artigo (εr=4,3, 0,03mm, cobrindo toda a face de cima)
   deslocou para ~3,28GHz — mais perto do ~2,79GHz esperado, mas
   ainda ~500MHz de diferença. **Extraí a foto real da Fig. 1(a) do
   PDF** (não só o texto) e confirmei que a topologia (linha e fenda
   entrando pelo mesmo lado do disco, colineares, furo do lado oposto)
   bate com o que foi construído — a diferença residual provavelmente
   vem de simplificações menores (cobre como folha ideal em vez de
   espessura real de 0,018mm, resolução de malha), **aceita como
   validação suficiente por ora** (mesmo padrão usado antes com a
   ômega).
4. **Refatorado para dict parametrizado** (`SASAKI_VALIDATION`,
   mesmo padrão REF/RO do `omega_antenna_nv.py`), função renomeada
   para `build_disk_hole_resonator(hfss, p)` — permite migrar uma
   variável de cada vez sem duplicar código.
5. **Passo 1 da migração ativo agora**: `RO5880_STEP1_MATERIAL` —
   troca só o substrato (FR4 εr=4,3/tanδ=0,03/1,6mm →  RO5880
   εr=2,20/tanδ=0,0009/0,75mm, o único disponível no projeto).
   `R`, `r`, `s`, `g` e o taper continuam iguais ao artigo por
   enquanto — isolando o efeito do substrato sozinho. **Resultado
   ainda não visto** — acabou de ser configurado.

**Lembrete do usuário (2026-09-19): o piso de fabricação é 0,5mm — não
dá pra conseguir mais precisão que isso.** ~~O gap `g=0,1mm` (valor do
artigo) precisa subir para 0,5mm~~ — feito no Passo 2 do plano abaixo
(`RO5880_STEP2_GAP`), `g=0,5mm` em todos os passos desde então.

**Plano de migração (ver `SASAKI_MODEL` no topo do script para trocar
de passo) — atualizado 2026-09-19/20, todos os passos abaixo já
rodados de verdade:**

1. ~~Trocar FR4 por RO5880 (material + espessura)~~ — `RO5880_STEP1_MATERIAL`.
   Resultado: ressonância subiu de ~3,28GHz para ~4,23GHz (esperado,
   RO5880 tem εr menor). Profundidade caiu de −7,3dB para −1,1dB
   (esperado, taper ainda dimensionado para FR4).
2. ~~Aumentar o gap de 0,1mm para 0,5mm~~ — `RO5880_STEP2_GAP`.
   Resultado: ressonância desceu um pouco (4,23→4,13GHz) — **contra**
   a expectativa da fórmula "ingênua" do artigo (que previa subir mais
   com gap maior). Lição repetida: não confiar em fórmula/extrapolação,
   só no resultado real simulado.
3. ~~Reotimizar `R_disk` e `s_off`~~ — `RO5880_STEP3_REOPT`
   (`add_disk_optimization`, Optimetrics). **Sucesso**: convergiu em
   `R_disk≈11,1mm`, `s_off≈4,3-4,4mm`, ressonância bem em cima de
   2,87GHz (dB(S11)≈−0,73dB — frequência certa, profundidade ainda
   limitada pelo taper).
4. ~~Recalcular a linha afunilada~~ — `RO5880_STEP4_TAPER`
   (`add_taper_optimization`, `feed_w_narrow`/`feed_len` livres,
   `R_disk`/`s_off` travados no valor do passo 3, `feed_w_wide=WF=
   2,3mm` o valor de 50Ω já estabelecido para RO5880/0,75mm).
   **Resultado inesperado: PIOROU** (~−0,5dB, pior que os −0,73dB do
   passo 3) — sinal de que travar `R_disk`/`s_off` não era mais o
   ideal depois que a largura larga da linha mudou de 3,3mm (FR4) para
   2,3mm (RO5880). As 4 variáveis interagem mais do que o esperado
   para uma abordagem sequencial "uma de cada vez".
5. ~~Otimização CONJUNTA das 4 variáveis juntas~~ —
   `RO5880_STEP5_JOINT`/`add_joint_optimization`. **PIOROU ainda
   mais**: melhor caso ~−0,65dB, pior que qualquer passo anterior.
   Com 4 graus de liberdade travado num teto tão raso — sinal de
   problema estrutural, não falta de ajuste fino.
6. ~~Diagnóstico: remover a camada de resist~~ (suspeita do usuário —
   ela cobre a linha inteira e podia estar mudando a impedância
   característica de `WF=2,3mm`) — `RO5880_STEP6_NO_RESIST` (`tr=0`).
   **PIOROU ainda mais** (~−0,42dB). Descarta o resist como causa
   principal.
7. ~~Validação de porta/linha em isolamento~~ (`TEST_LINE_2PORT`,
   `build_straight_line_2port`, `RING_MODE="test_line_2port"`). Depois
   de 4 tentativas de migração travadas perto de −0,5dB mesmo com
   várias variáveis livres, ficou claro que o problema podia não estar
   na geometria do ressoador — é o passo de validação que a análise
   externa recomendou originalmente (seção 0, "4.1 Validar primeiro a
   linha de microfita e as portas") e que **nunca tinha sido feito**:
   pulamos direto para validar o disco (que deu certo em FR4, mas
   usando a largura *do artigo*, 3,3mm — nunca confirmamos
   independentemente que `WF=2,3mm` é realmente 50Ω em RO5880/0,75mm).
   Linha reta de microfita, 2 portos, sem ressoador nenhum.
   **CONFIRMADO: S11 < −28dB, S21 ~0dB em toda a faixa** — a porta e a
   largura de 2,3mm estão corretas. **O problema não é a porta/linha —
   é mesmo a geometria do disco+furo.**
8. ~~Hipótese da constrição larga demais~~. A otimização do Passo 3
   (que só mirava frequência, não profundidade) convergiu em
   `R_disk=11,1mm`/`s_off=4,4mm`, dando uma **constrição** (a "ponte"
   indutiva entre o furo e a borda, `R−s−r`) de 6,2mm — 56% do raio do
   disco, bem mais larga proporcionalmente que a do artigo original
   validado em FR4 (`R=7/s=3,9/r=0,5` → constrição de 2,6mm, só 37% de
   R). Teste (`RO5880_STEP8_NARROW_NECK`): mesma "largura de placa do
   capacitor" (`R+s−r≈15mm`) mas com `R=9,3mm`/`s=6,2mm`, mesma
   constrição estreita do artigo (2,6mm). **PIOROU** (~−0,36dB,
   ressonância bem em 2,87-2,9GHz mas ainda mais rasa) — descarta
   também a largura da constrição como causa.
9. ~~Diagnóstico: a malha adaptativa está convergindo?~~ Encontrada
   no Message Manager: **"Adaptive Passes did not converge based on
   specified criteria"** em uma das rodadas do Passo 8. Adicionado
   refinamento de malha local no gap (`Mesh_Region_Gap`, mesma técnica
   já usada em `omega_antenna_nv.py` — caixa de ar fina em volta do
   gap com malha forçada a `g/3`, em vez de refinar o disco inteiro) e
   `MaximumPasses` subido de 15 para 25. Resultado da nova rodada:
   **idêntico, pixel a pixel**, ao anterior — muito suspeito.
10. **Bug real encontrado: cache de design por nome repetido.** Cada
    passo da migração reusava o mesmo nome de design entre rodadas
    (ex.: `RO5880_Step8_NarrowNeck_Unloaded`, repetido sempre que o
    mesmo passo era rodado de novo) — o AEDT reabria o design já
    existente e já resolvido em vez de reconstruir do zero, **mascarando
    silenciosamente qualquer mudança de código** (geometria, malha,
    setup) entre reruns do mesmo passo. Confirmado pelo Message
    Manager mostrando só o sweep de frequência direto, sem nenhuma
    mensagem de malha adaptativa, na rodada que deveria ter testado a
    correção de malha. **Corrigido**: nome do design agora leva um
    sufixo único por execução (`time.strftime("%H%M%S")`), garantindo
    que cada rodada do script sempre constrói e resolve do zero.
11. **Resultado após a correção do cache: idêntico de novo** (mesmo
    design, agora com nome `..._223237`, confirmado como rodada nova
    de verdade). Ou seja, o resultado raso (~−0,36 a −0,73dB
    dependendo do passo) **não era artefato de cache nem de malha não
    convergida** — é a resposta física real do modelo para essas
    geometrias.
12. **Status (2026-09-20): 4 hipóteses testadas e descartadas** com
    evidência real — resist, porta/largura da linha, largura da
    constrição, e cache/convergência de malha. Nenhuma explica a
    profundidade rasa. Análise externa (segunda opinião, 2026-09-20)
    apontou o motivo estrutural provável: um taper linear só transforma
    a parte REAL da impedância, não cancela reatância — sem nunca
    termos olhado a impedância complexa (`Zin`), estávamos ajustando
    largura/comprimento às cegas.
13. ~~Extrair `Zin=R+jX` de verdade~~ (`RO5880_STEP9_ZIN_PROBE`,
    `RING_MODE="extract_zin"`) — linha SEM afunilar (largura constante
    `WF=2,3mm`) na geometria do Passo 8, pra medir a carga "crua" sem
    misturar com a transformação do taper. `Zin` calculado direto do
    `S11` complexo (`Zin=50(1+S11)/(1-S11)`), impresso no terminal via
    `pyaedt` (sem precisar de Smith Chart na GUI — importante, usuário
    ficou sem mouse/botão direito numa sessão remota).
    **RESULTADO DECISIVO: em f=2,87GHz, `Zin = 0,55 + 0,60j Ω`.**
    Isso é **quase um curto-circuito** — a razão de transformação
    necessária pra chegar em 50Ω é de quase **91:1**. Isso explica
    completamente por que nenhum ajuste de taper (largura, comprimento,
    isolado ou junto com `R_disk`/`s_off`) jamais funcionou: um taper
    linear não consegue fazer uma transformação dessa magnitude de
    forma robusta, e muito menos cancelar a reatância junto.
    Explicação física: a linha está conectada bem perto da fenda — o
    lado de baixa impedância de um laço ressonante em série (equivalente
    a alimentar um tanque LC bem no nó de "terra" dele). **Isso
    reabilita a hipótese do TAP ANGULAR** (`gap_rotation`, pausada na
    seção 0 por não ser a explicação da *literatura*, mas nunca
    descartada por evidência própria) — mudar ONDE ao redor do disco a
    linha se conecta deve mudar bastante essa impedância, já que
    pontos diferentes do laço ressonante têm impedâncias locais
    diferentes.
14. ~~Testar o tap angular com dado real~~ (`ANGLE_TEST_MODELS`,
    `RING_MODE="test_feed_angles"`) — 3 designs, ponto de conexão da
    linha girado 45°/90°/135° ao redor do disco (fenda e furo
    mantidos nas posições de sempre). **Resultado (2026-09-20/21):**

    | Ângulo | Zin |
    |---|---|
    | 45° | 0,48 − 0,73j Ω |
    | 90° | 0,50 + 2,63j Ω |
    | 135° | 0,99 + 19,61j Ω |

    **A parte REAL fica travada perto de 0,5-1Ω em TODOS os ângulos**
    — só a reatância muda. **Descarta o tap angular**: não é "achar o
    lugar certo na borda" que resolve — a resistência baixa é uma
    característica intrínseca do modo (provável Q alto, baixa perda/
    acoplamento à radiação em qualquer ponto do laço), não um efeito
    de posição de conexão galvânica.
15. **Status (2026-09-21): 5 hipóteses testadas e descartadas** —
    resist, porta/largura da linha, largura da constrição, cache/
    convergência de malha, e agora tap angular. A razão de
    transformação necessária (~50-100:1, dependendo do ponto) é grande
    demais para qualquer tap galvânico direto resolver sozinho.
    **Próximo passo em aberto**: projetar uma rede de casamento de
    verdade a partir do `Zin` já medido — as opções, em ordem de
    robustez para uma razão tão grande: (a) stub aberto em derivação
    (recomendado pela análise externa, calculável agora que se conhece
    o alvo exato); (b) acoplamento indutivo (laço pequeno próximo ao
    ressoador, sem conexão galvânica — comum em ressoadores de EPR/
    ODMR reais, permite ajustar o acoplamento pela distância/tamanho do
    laço); (c) acoplamento capacitivo (gap pequeno entre a linha e o
    disco em vez de união direta). Qualquer uma dessas terá banda
    estreita, por causa da própria magnitude da razão de transformação
    — isso é esperado, não é sinal de erro adicional.
16. **EM ANDAMENTO — stub aberto em derivação** (`RO5880_STEP16_STUB`,
    `build_disk_hole_resonator` com suporte a `stub_distance`/
    `stub_length`/`stub_width`). Escolhido entre as 3 opções do item 15
    por ser o mais robusto para fabricação em camada única (sem via).
    **Calculado analiticamente** (teoria de linha de transmissão, não
    tentativa e erro) a partir de `Zin=0,55+0,60j Ω` (Passo 13,
    `feed_angle=0`):
    - Normalizado: `zL=ZL/Z0=0,011+0,0120j`
    - Resolvendo `Re(Yin(d))=Y0` (equação quadrática em
      `t=tan(β·d)`): raízes `t=-0,11702` ou `t=+0,09275`. Escolhida a
      que dá a distância MAIOR (mais longe de efeitos de campo
      próximo da borda do disco): `d≈0,4815·λg`.
    - Nesse ponto, `Im(Yin)≈+9,43` (normalizado) — o stub aberto
      cancela isso: `tan(β·l)=-9,43` → `l≈0,2670·λg`.
    - `λg≈76,4mm` (fórmula padrão de εeff de microfita, RO5880/
      0,75mm, trilha 2,3mm, 2,87GHz).
    - Resultado: `stub_distance≈36,6mm`, `stub_length≈20,3mm`,
      largura do stub = `WF=2,3mm` (mesma da linha principal).
    Placa aumentada para 118×52mm (porta e stub ficam bem mais longe
    do disco agora) — risco de esbarrar no limite de malha do Student
    de novo (~1077cm³ de airbox estimado, mais apertado que os casos
    que já funcionaram antes); se der erro de malha, é só encolher a
    placa mais (`L_sub`/`W_sub` de `RO5880_STEP16_STUB`).
    **RESULTADO: FUNCIONOU DE VERDADE.** Vale de **−6,94dB em
    2,37GHz** — de longe o melhor resultado já obtido em RO5880 (tudo
    antes disso ficou entre −0,3 e −0,75dB). O conceito do stub está
    provado; a única discrepância é a frequência (500MHz abaixo do
    alvo) — o `λg` estimado à mão não bateu exato, ou a impedância do
    disco muda o suficiente fora de 2,87GHz para deslocar o ponto de
    casamento.
17. **EM ANDAMENTO — otimização fina do stub** (`RO5880_STEP17_STUB_OPT`,
    `add_stub_optimization`, `RING_MODE="optimize_stub"`). Só 2
    variáveis (`stub_distance`, `stub_length`), `R_disk`/`s_off`/`g`/`r`
    travados (a frequência natural do disco já foi resolvida no Passo
    3 — o stub só precisa alinhar o PRÓPRIO ponto de casamento com
    ela, não redefini-la). Chute inicial escalado pela razão de
    frequência (2,87/2,37≈1,211): `stub_distance≈30,2mm`,
    `stub_length≈16,8mm`, faixa de busca ±8mm em volta disso.
    Diferente de todas as tentativas anteriores de casamento (taper,
    Passos 4/5), esta otimização parte de um vale que **já existe e já
    é fundo** — não está mais procurando às cegas.

    A otimização em si rodou e terminou (~30min, design
    `RO5880_Step17_StubOpt_Unloaded_094713`), mas a primeira leitura
    rápida (`-0,06dB` em 2,87GHz) é suspeita de ter pego a variação
    "nominal" errada, não o melhor ponto testado — mesma pegadinha já
    documentada no README para a omega. Ao tentar ler TODAS as
    variações via script separado (`scripts/read_stub_opt_results.py`,
    reabrindo o projeto já resolvido sem reotimizar), dois bugs de
    script (não de física) apareceram e foram corrigidos em
    2026-09-21: (a) `Hfss(project=...)` recebia só o *nome* do
    projeto, não o caminho completo do `.aedt` — numa sessão AEDT nova
    (`new_desktop=True`) sem nada aberto ainda, isso arriscava não
    achar o projeto certo; (b) `setup_sweep_name="Setup1 : Sweep1"`
    hardcoded deu `KeyError` ("Setup Setup1 not available in current
    design") ao reabrir o projeto do zero — corrigido para descobrir
    dinamicamente via `hfss.existing_analysis_sweeps` em vez de
    adivinhar o nome; (c) `release_desktop(close_on_exit=...)` — kwarg
    não existe, é `close_desktop`.

    Reotimizado do zero em 2026-09-21 (`RO5880_Step17_StubOpt_Unloaded_111943`,
    projeto salvo de verdade desta vez — 129KB, contra ~4KB de uma
    tentativa anterior que tinha ficado vazia). **Causa raiz real do
    "-0,06dB sempre igual" finalmente encontrada**: o AEDT salva cada
    variação testada pelo Optimetrics como um sweep próprio dentro do
    mesmo Setup, com o nome literal contendo os valores das variáveis
    (ex.: `"Setup1 - stub_distance='30.1mm' stub_length='16.8mm' :
    Table"`), separado de `"Setup1 : Sweep1"` genérico e de `"Setup1 :
    LastAdaptive"` (só a variação nominal, 1 ponto). As duas leituras
    anteriores (`get_solution_data` sem variação, depois
    `set_active_variation(i)` sobre `"Setup1 : Sweep1"`) caíam sempre
    no ponto nominal — por isso o valor nunca mudava. `print_all_optimetrics_variations`
    foi reescrita para extrair essas variações via regex nos nomes dos
    sweeps e ler cada uma individualmente.

    Ainda não estava certo: usar o nome do sweep direto como
    `setup_sweep_name` quebra (`get_solution_data` faz um
    `split(":")` ingênuo nele, vê um "nome de setup" absurdo e dá
    `KeyError`, deixando a sessão gRPC instável para as chamadas
    seguintes — foi o que gerou "Failed to execute gRPC AEDT command:
    GetSetups" nas variações [1]-[7] numa tentativa). A forma certa
    (documentada no próprio pyaedt) é `setup_sweep_name="Setup1 :
    Sweep1"` normal + `variations={...}` — mas passando só as 2
    variáveis otimizadas nesse dict, a chamada ignorava o filtro
    silenciosamente e devolvia sempre o ponto nominal (as 8 variações
    voltaram com dB(S11)=-0,06 **idêntico**, fisicamente implausível
    para pontos diferentes testados por um otimizador). Corrigido
    passando o dict **completo** de variáveis (todas as extraídas do
    nome do sweep via regex, não só as 2 de interesse), igual ao
    exemplo oficial do pyaedt (`variations =
    hfss.available_variations.nominal_values`, só substituindo as
    chaves de interesse). **Resultado numérico final ainda não
    confirmado** — rodando a versão corrigida.
18. Introduzir o diamante (3×3×0,300mm) — pendente, só depois do
    casamento resolvido (senão não dá pra saber se um desvio veio da
    geometria ou do diamante).
19. Introduzir a alumina, se confirmado que faz parte da montagem —
    pendente.
20. Desenhar o lançamento do SMA com plano de terra realista —
    pendente.
21. Avaliar B₁z e sua uniformidade sobre a abertura (a figura de
    mérito real do projeto) — pendente.

---

## 1. Objetivo e por que essa geometria

Ressoador planar de micro-ondas para **ODMR de centros NV⁻ em
diamante**, em **2,87 GHz** (zero-field splitting do NV⁻). A figura de
mérito real é o campo magnético B₁ **perpendicular ao plano**, dentro
da abertura óptica (onde fica o diamante) — intensidade e
**uniformidade**. O S11 (casamento de impedância) importa porque sem
casamento não entra potência de RF no sistema para gerar campo, mas
S11 sozinho não prova que o campo é bom (isso ainda não foi avaliado
nesta topologia — ver seção 6, "em aberto").

**Requisito de banda:** o campo estático B₀ separa as transições
mₛ=0↔−1 e 0↔+1 por efeito Zeeman. Em ~4,7 mT elas ficam em ~2,74 GHz e
~3,00 GHz. A antena precisa cobrir as duas sem retuning ⇒ banda de
pelo menos ~250 MHz. Por isso as simulações usam uma faixa de
2,5–3,2 GHz ao redor do alvo, não um único ponto.

## 2. Mudança de requisitos que iniciou esta linha de trabalho (2026-09-18)

Repassado pelo colega de projeto (Thiago Ferreira) após conversa com o
orientador (Dr. Achiles Fontana):

1. **Ressoador de UM PORTO, não dois.** A topologia anterior (ômega,
   baseada em Opaluch et al. 2021) é de dois portos por natureza —
   inválida para o pedido atual.
2. **Feição mínima de fabricação: 0,5 mm** (gap e trilha estreita).
   Bem maior que os ~0,15 mm usados antes (que assumiam corte a laser
   LPKF).
3. **Processo de fabricação mudou.** Não é mais LPKF. Entendimento
   atual: corta-se o substrato de RO5880 no tamanho certo; a
   **deposição do condutor e o plano de terra são feitos em São
   Carlos** (fora do controle direto deste projeto/script).
4. **Feed final:** conector **SMA soldado** na borda da placa,
   alimentando uma linha de microfita de 50 Ω que leva ao ressoador.
5. Papel exato da alumina (tipo/permissividade) e do plano de terra
   ainda não confirmados — ver seção 6.

## 3. Materiais e restrições físicas (fixos)

| Item | Valor | Status |
|---|---|---|
| Substrato | **Rogers RT/duroid 5880** | fixo, material disponível |
| εr (substrato) | 2,20 | fixo |
| tanδ (substrato) | 0,0009 | fixo |
| Espessura do substrato (`h_sub`) | 0,75 mm | fixo |
| Feição mínima de fabricação | 0,5 mm (gap E trilha estreita) | fixo, pedido do orientador |
| Frequência alvo | 2,87 GHz (centro), banda 2,5–3,2 GHz simulada | fixo |
| Portas | **1** (um porto, feed único) | fixo, pedido do orientador |
| Conector final | SMA soldado na borda | fixo |
| Alumina (tipo/εr exato) | ainda não confirmado | **em aberto** |
| Plano de terra (material/tamanho) | ainda não confirmado (suposição antiga: porta-amostra de titânio, copiada do artigo de referência, nunca validada) | **em aberto** |
| Airgap mínimo (regra HFSS) | λ₀/4 = 26,1 mm em 2,87 GHz | fixo, restrição física |

## 4. Topologia: anel fendido (split-ring resonator) de 1 porto

Baseado conceitualmente em:
- Sasaki et al., *Rev. Sci. Instrum.* **87**, 053904 (2016) — anel
  fendido em 2,87 GHz, banda 400 MHz.
- Misonou et al., *Rev. Sci. Instrum.* **91**, 023703 (2020),
  arXiv:2002.02113 — parâmetros tabelados (r, R, s, g) para split-ring
  resonators de 1 porto, modelo LC série.

Circuito equivalente: **LC série**. O laço condutor é o **indutor**; a
fenda radial (gap) que interrompe o laço é o **capacitor**. Uma única
microfita de 50 Ω se conecta ao laço (feed direto, sem segunda porta).

### 4.1 Geometria exata (variáveis do modelo HFSS)

Todas as variáveis abaixo são "design variables" paramétricas dentro
do HFSS (não valores fixos no desenho — podem ser reotimizadas sem
reconstruir a geometria do zero).

| Variável HFSS | Significado | Valor atual (nominal) | Fórmula/relação |
|---|---|---|---|
| `R_out` | Raio externo do anel | 16,3 mm | livre, otimizado |
| `W_ring` | Largura radial da trilha do anel | 2,0 mm | **fixo** (ver seção 5) |
| `R_in` | Raio interno do anel = raio da abertura óptica (onde fica o diamante) | 14,3 mm | `R_in = R_out - W_ring` |
| `g_slot` | Largura da fenda radial (capacitor) | 0,5 mm | **fixo** no piso de fabricação |
| `feed_overlap_frac` | Fração (0–1) de quanto a linha de alimentação penetra RADIALMENTE dentro da largura do anel, no ponto onde toca | 0,5 (50%) | livre, mas **baixa sensibilidade** (ver seção 5) |
| `feed_overlap` | Penetração radial em mm (derivado) | 1,0 mm | `feed_overlap = feed_overlap_frac × W_ring` |
| `gap_rotation` | Ângulo (graus) de rotação da fenda em torno do centro do anel, relativo à posição default (fenda oposta à entrada da linha) | 0° (default) | livre, **candidato a ser o lever real de casamento** — ver seção 5 |
| `Wf` | Largura da linha de alimentação de 50 Ω | 2,3 mm | fixo (calculado para 50 Ω em RO5880/0,75mm) |
| `L_sub`, `W_sub` | Tamanho da placa de simulação | 55 × 50 mm | fixo por limite de malha da versão Student (ver seção 5) — **não é necessariamente o tamanho final de fabricação** |
| `AIRGAP` | Folga de ar ao redor da estrutura até o contorno de radiação | 26,5 mm | perto do mínimo físico (26,1mm) de propósito, para economizar malha |

### 4.2 Como a geometria é construída (ordem das operações)

1. Substrato: caixa de RO5880, `L_sub × W_sub × h_sub`, centrada na
   origem.
2. Plano de terra: retângulo do tamanho do substrato (**⚠️ isso ainda
   não reflete a suposição antiga de porta-amostra de titânio maior
   que o substrato — precisa reconfirmar o plano de terra real, ver
   seção 6**), atribuído como Perfect E.
3. Anel: círculo de raio `R_out` menos círculo de raio `R_in` (anel
   fino de verdade — ver nota histórica na seção 5 sobre um bug de
   geometria já corrigido).
4. Fenda: retângulo de largura `g_slot`, criado por padrão apontando
   em +x (lado oposto à entrada da linha, que fica em −x), depois
   **rotacionado** em torno do centro do anel por `gap_rotation` graus
   (eixo Z) antes de ser subtraído do anel.
5. Linha de alimentação: retângulo de largura `Wf`, entrando pela
   borda da placa em −x, indo até `feed_overlap` mm dentro da largura
   do anel. Unida (`unite`) ao anel — vira um único condutor PEC
   (`Conductor`).
6. Porta: folha vertical (plano YZ) na borda externa da linha de
   alimentação, **porta do tipo lumped port, 50 Ω, 1 porto só**
   (`Port1`). É essa porta que, na fabricação real, corresponde ao
   ponto onde o **conector SMA** é soldado.
7. Airbox + contorno de radiação + `Setup1` (HFSSDriven, malha
   adaptada em 2,87 GHz) + sweep de frequência.

### 4.3 Por que existe abertura óptica separada do "furo"

Numa versão antiga (já corrigida — ver seção 5), havia um raio de furo
fixo (`R_HOLE`) de 0,5 mm dentro de um disco quase sólido. Isso estava
ERRADO: a abertura óptica de verdade é simplesmente `R_in` (o raio
interno do próprio anel fino), sem precisar de um furo extra separado.

## 5. Histórico de testes reais (tudo rodado de verdade no HFSS, não simulado/hipotético)

Ordem cronológica, 2026-09-18/19. **Cada item abaixo foi efetivamente
executado no Ansys** pelo usuário, não é previsão.

### 5.1 Bug de geometria: "disco quase sólido" em vez de anel fino

Implementação inicial tinha `R_HOLE = 0,5mm` fixo e usava `R_out` como
raio de um DISCO praticamente inteiro (só com um furinho de 0,5mm no
meio) — não um anel de trilha fina. Sintomas observados que revelaram
o bug:
- Precisou de `R_out ≈ 20mm` para ressoar perto de 2,87GHz (escala
  suspeita, bem maior que a literatura de referência ~10mm).
- Casamento (profundidade do S11) ficou raso: só **−2dB** no melhor
  caso, quando o esperado é −10 a −20dB+.

**Corrigido**: geometria virou anel fino de verdade (`R_in = R_out −
W_ring`), como descrito na seção 4.

### 5.2 Diagnóstico de banda larga (0,5–6GHz), geometria já corrigida

Com `R_out=20mm` fixo (herdado do bug anterior), `W_ring=2mm`,
`g_slot=0,5mm`: resolvido em 0,5–6GHz. Resultado: **um único vale
claro em ~0,85GHz** (quase −2dB), resto da faixa 1–6GHz praticamente
plano. Ou seja, esse anel de 20mm ressoa bem abaixo de 2,87GHz — anel
grande demais.

### 5.3 Varredura de R_out (5 a 20mm, passo 2,5mm), ainda banda larga

7 pontos, mesma faixa 0,5–6GHz. Achado:
- `R_out=20mm` → ressonância em ~0,85GHz.
- `R_out=15mm` → ressonância já deslocada para ~4–5GHz (a curva não
  fechava um vale completo dentro do gráfico de 6GHz).
- **Conclusão**: a ressonância de 2,87GHz cai entre `R_out=15` e
  `R_out=20mm` — sensibilidade bem alta nessa faixa estreita.

### 5.4 Otimização v2 — 2 variáveis (R_out, feed_overlap em mm absoluto), faixa estreita 2,5–3,2GHz

`W_ring` fixo em 2mm. Convergiu para **`R_out≈16,3–16,4mm`** — bem
perto de 2,87GHz de verdade (não é mais suposição, é resultado
convergido). Profundidade do casamento: só **−0,63dB**. `feed_overlap`
ficou perto de 1mm (~50% de W_ring) na maioria das variações testadas.

**Este é o valor de R_out mais confiável até agora** — repetido/
consistente em duas rodadas diferentes.

### 5.5 Otimização v3 — 3 variáveis (R_out, W_ring livre 0,5–4mm, feed_overlap_frac)

Ideia: dar mais espaço para o "tap" variando também a largura do anel.
Resultado: **PIOROU** — profundidade caiu para **−0,25 a −0,28dB**.
`R_out` foi empurrado para perto do piso da faixa (~13,2–13,5mm) e
`W_ring` para perto do teto (~3,7–4,0mm), sem melhorar o casamento.
`feed_overlap_frac` ficou travado em exatamente 0,5 (não se moveu do
ponto de partida) em todas as variações mostradas.

**Conclusão**: `W_ring` não é o parâmetro que controla o casamento de
impedância. Revertido para fixo em 2mm.

### 5.6 Correção conceitual (2026-09-19): qual é o "tap" de verdade

`feed_overlap_frac` controla só a penetração RADIAL da linha, sempre
no MESMO ponto angular (diametralmente oposto à fenda). Isso é um
detalhe local da junção, não o mecanismo clássico de casamento de
ressoador em laço. O tap de verdade em ressoadores desse tipo é a
**posição angular** onde a linha se conecta em relação à fenda —
rotacionar esse ponto ao redor do laço amostra pontos diferentes da
onda estacionária de tensão/corrente, o que de fato transforma a
impedância vista pela linha de 50Ω. A baixa sensibilidade observada em
5.4/5.5 (feed_overlap_frac não saindo de 0,5) é evidência a favor
dessa hipótese.

**Ação**: nova variável `gap_rotation` introduzida (ângulo de rotação
da fenda em torno do centro do anel). `W_ring` mantido fixo em 2mm (o
valor que já deu a melhor combinação frequência+profundidade, seção
5.4).

### 5.7 Otimização v4 — 3 variáveis (R_out, feed_overlap_frac, gap_rotation) — EM ANDAMENTO

Ainda **não concluída com sucesso**. Primeira tentativa falhou por um
bug de API do pyaedt (não de física/geometria): o código chamou
`objeto.rotate(cs_axis="Z", angle="gap_rotation")`, mas o parâmetro
correto na versão instalada (pyaedt 1.6.0) é `axis`, não `cs_axis`.
**Confirmado direto no código-fonte** da biblioteca instalada
(`Object3d.rotate(self, axis, angle=90.0, units="deg")`), não por
tentativa e erro. Corrigido para
`objeto.rotate(axis="Z", angle="gap_rotation")`. Aguardando nova
rodada do usuário para confirmar se resolve e se `gap_rotation` de
fato melhora a profundidade do casamento — **este é o próximo
resultado pendente**.

### 5.8 Limite de malha da versão Student (efeito colateral, não é sobre a física do ressoador)

Ao tentar dar mais espaço para `R_out` grande, o tamanho da placa de
simulação foi aumentado (70×60 → 90×80mm) e o AEDT recusou rodar:
`"Mesh size (64539 volume elements) is greater than the limit for
simulation in Ansys Electronics Desktop Student."` — é um teto da
versão gratuita, não um erro de projeto. Corrigido reduzindo a placa
de simulação para **55×50mm** e o `AIRGAP` para 26,5mm (perto do
mínimo físico de 26,1mm) — ambos só para caber no limite de malha,
**não representam necessariamente o tamanho final da placa a
fabricar**.

## 6. O que está definitivo vs. o que está em aberto

**⚠️ Ver seção 0 primeiro.** A lista abaixo reflete o estado ANTES da
correção crítica de 2026-09-19. Itens marcados com [SUPERADO] não são
mais considerados confiáveis à luz da geometria correta (excêntrica +
taper), mesmo que tenham sido resultados reais na época.

### Definitivo (resultado real, verificado, improvável de mudar)

- Topologia: ressoador de laço com furo e gap, 1 porto (não a ômega de
  2 portos antiga) — a FORMA exata do laço (excêntrico, tipo
  disco-com-furo-deslocado) é a correção da seção 0, não muda o fato
  de ser 1 porto.
- Substrato do projeto final: Rogers RT/duroid 5880, εr=2,20,
  tanδ=0,0009, h=0,75mm (mas a VALIDAÇÃO agora deve ser feita primeiro
  em FR4, replicando a literatura — ver seção 0).
- Feição mínima de fabricação: 0,5mm (gap) — continua valendo como
  restrição para a versão final em RO5880, mas o modelo de validação
  em FR4 deve usar g=0,1mm (valor real do artigo) para poder comparar
  com o resultado publicado.
- Bug de API pyaedt identificado e corrigido: `Object3d.rotate()`
  usa `axis=`, não `cs_axis=` (continua válido/reaproveitável se a
  rotação for necessária em algum outro contexto).
- **[SUPERADO]** `R_out≈16,3mm` para anel fino concêntrico — não se
  aplica à geometria corrigida (excêntrica); pode servir só como
  referência de ordem de grandeza.
- **[SUPERADO]** `W_ring` e `feed_overlap_frac` como não-relevantes —
  essas variáveis nem existem na geometria corrigida (não há mais
  "largura de anel" nem "tap radial"; os parâmetros agora são R, r, s,
  g, e o perfil do taper da linha).

### Em aberto (ainda não resolvido / pode mudar)

1. **Casamento de impedância** — o problema central, ainda não
   resolvido. Melhor resultado até agora com a geometria de anel fino
   (agora superada): apenas −0,63dB. **Hipótese ativa agora**: o
   casamento real vem da excentricidade do furo (r, s) e do afunilamento
   da linha de alimentação (não de um ângulo de tap) — ver seção 0.
   Ainda não implementado nem testado.
2. **Implementar a geometria corrigida** (disco de raio R, furo
   excêntrico de raio r deslocado por s, gap g, linha afunilada de
   3,3mm a 0,54mm em 23mm) — ainda não escrita em código. Primeiro
   passo: validar em FR4 com os parâmetros exatos do artigo antes de
   portar para RO5880.
3. **Plano de terra**: ainda usando suposição herdada do projeto
   antigo (porta-amostra de titânio do artigo de referência Opaluch et
   al. 2021) — nunca confirmada como material real disponível, e
   sequer foi reconstruída corretamente na topologia atual (o código
   atual usa plano de terra do TAMANHO DO SUBSTRATO, não o porta-
   amostra maior — precisa decidir/confirmar antes de qualquer
   resultado final).
4. **Alumina**: tipo comercial exato e εr não confirmados com o
   orientador. Ainda nem foi reintroduzida no modelo desta topologia
   (só existia no modelo antigo da ômega).
5. **Avaliação de campo** (a figura de mérito real do projeto — B₁
   perpendicular, uniformidade sobre a abertura): **não foi feita
   nesta topologia ainda**. Só foi feita na ômega antiga (dados em
   `results/README.md`), que não é mais válida para este design.
6. **Tamanho final do substrato para corte físico**: a placa de
   55×50mm usada agora é só para a simulação caber no limite de malha
   da versão Student — não é necessariamente o tamanho certo para
   fabricação. Ainda não há uma recomendação final de corte.
7. **Diamante presente**: esta topologia ainda não foi testada com o
   diamante (IIa, 3×3×0,300mm, εr=5,7) carregando a abertura — só a
   estrutura "bare" (sem carga) foi simulada até agora.
8. **Layout do conector SMA**: footprint de solda, stitching de vias
   de terra ao redor do lançamento — detalhe de layout final, ainda
   não desenhado (a simulação representa o SMA de forma idealizada,
   como uma porta lumped de 50Ω).
9. Perguntas ainda pendentes com o orientador (herdadas do projeto
   anterior, continuam válidas): tamanho do diamante/área que precisa
   de B₁ uniforme; faixa real de B₀; tipo exato de alumina; se o plano
   de terra será mesmo titânio ou outro material/tamanho agora que a
   deposição é feita em São Carlos.

## 7. Notas técnicas / armadilhas já descobertas nesta linha de trabalho

- **API pyaedt**: `Object3d.rotate(self, axis, angle=90.0,
  units="deg")` — o parâmetro é `axis`, não `cs_axis`. `angle` aceita
  uma string com o nome de uma variável de projeto HFSS (ex.:
  `"gap_rotation"`), não precisa ser um número Python — nesse caso a
  rotação fica paramétrica e pode ser reotimizada sem reconstruir a
  geometria.
- **Não confiar em "onde o vale mais fundo está"** ao ler resultado de
  S11 — pode ser um modo diferente aparecendo, não a mesma ressonância
  continuando a se mover (lição herdada do projeto da ômega, seção 5/7
  do `README.md`, e que se repetiu aqui: a varredura banda-larga foi
  necessária justamente por causa disso).
- **Limite de malha da versão Student**: ao aumentar o tamanho da
  placa/airbox para dar espaço a uma geometria maior, cuidado com o
  volume total de malha. Reduzir `AIRGAP` até perto do mínimo físico
  (λ₀/4) e/ou reduzir a placa são as duas alavancas disponíveis.
- **`feed_overlap` como variável derivada**: é calculado dentro do
  HFSS como `feed_overlap_frac × W_ring` (não é ele mesmo uma
  variável livre de Optimetrics) — isso garante, por construção, que a
  penetração da linha nunca ultrapassa a largura real do anel, mesmo
  que `W_ring` mude durante uma otimização.
- **⚠️ CACHE DE DESIGN POR NOME REPETIDO (2026-09-20, custou várias
  rodadas perdidas).** Rodar o script de novo usando o MESMO nome de
  design entre execuções (ex.: reusar `SASAKI_MODEL["name"]` sem
  variar) faz o AEDT reabrir/reaproveitar o design já existente e já
  resolvido, em vez de reconstruir do zero — **mascarando
  silenciosamente qualquer mudança de código** (geometria nova, malha
  nova, setup novo) feita entre uma rodada e outra. Sintoma: resultado
  idêntico pixel a pixel a uma rodada anterior, mesmo depois de mudar
  o código; no Message Manager, a rodada "fantasma" mostra só o sweep
  de frequência direto, sem nenhuma mensagem de malha adaptativa (sinal
  de que não remalhou nem resolveu de novo). **Correção**: gerar um
  sufixo único por execução (`time.strftime("%H%M%S")`) e usá-lo no
  nome do design a cada rodada do `__main__`, garantindo que o AEDT
  sempre constrói e resolve um design novo.
- **Malha adaptativa pode não convergir silenciosamente** — vale
  sempre checar o Message Manager por "Adaptive Passes did not
  converge based on specified criteria" antes de confiar num resultado
  de S11. Nem sempre é a causa do problema (neste projeto, corrigir a
  malha do gap + subir `MaximumPasses` de 15 para 25 não mudou o
  resultado — o problema era outro), mas é barato de checar e deveria
  ser o primeiro passo de diagnóstico sempre que um resultado parecer
  raso/estranho sem explicação geométrica óbvia.
- **Descartar hipóteses com teste isolado, não só ajuste fino.** Neste
  projeto, testar a linha de microfita sozinha (2 portos, sem
  ressoador) resolveu de vez a dúvida sobre porta/largura em 1 rodada
  rápida — muito mais eficiente do que continuar ajustando parâmetros
  do ressoador inteiro esperando que o problema "resolvesse sozinho".
  Sempre que uma hipótese permitir um teste isolado e mais simples,
  preferir isso a mais uma rodada de otimização no sistema completo.

## 8. Arquivos relevantes

- `scripts/nv_resonators_compare.py` — script ativo. Geometria ATIVA
  agora: `build_disk_hole_resonator(hfss, p)` (disco + furo excêntrico,
  parametrizado por dict — `SASAKI_VALIDATION`, `RO5880_STEP1..8_*`),
  `build_straight_line_2port(hfss, p)` (validação de porta/linha,
  `TEST_LINE_2PORT`), `add_disk_optimization`/`add_taper_optimization`/
  `add_joint_optimization` (Optimetrics). `build_ring()`/
  `add_ring_wideband_scan()`/`add_ring_optimization_multivar()` são o
  anel fino, PAUSADO (seção 0) — mantido no arquivo só como histórico.
  `SASAKI_MODEL` (qual dict usar) e `RING_MODE` (qual ação rodar) no
  topo do arquivo controlam o que o `__main__` executa.
- `scripts/omega_antenna_nv.py` — topologia antiga (ômega, 2 portos),
  congelada, não mais candidata a fabricar, mas com metodologia de
  validação reaproveitável.
- `README.md` — documento de contexto completo do projeto, seções 0
  (mudança de requisitos), 3 (topologias) e 5/6 (histórico da ômega).
- `results/` — resultados finais da topologia antiga (ômega); não se
  aplicam a este anel de 1 porto.

## 9. Referências (geometria verificada direto na fonte, 2026-09-19)

- Sasaki, Monnai, Saijo, Fujita, Watanabe, Ishi-Hayase, Itoh & Abe,
  *"Broadband, large-area microwave antenna for optically detected
  magnetic resonance of nitrogen-vacancy centers in diamond"*,
  Rev. Sci. Instrum. **87**, 053904 (2016).
  https://www.appi.keio.ac.jp/Itoh_group/publications/pdf/RevSciInst_Sasaki.pdf
  — fonte primária da geometria (Fig. 1b): R, r, s, g, taper da linha,
  materiais e espessuras exatas. Texto extraído diretamente do PDF
  (via `pypdf`) para esta correção — não é resumo de segunda mão.
- Misonou, Sasaki, Ishizu, Monnai, Itoh & Abe, *"Construction and
  operation of a tabletop system for nanoscale magnetometry with
  single nitrogen-vacancy centers in diamond"*, arXiv:2002.02113
  (2020) — Seção II C e Tabela I (Antenas #1 e #2, mesma geometria de
  Sasaki 2016, parâmetros para B₀ mais alto).
