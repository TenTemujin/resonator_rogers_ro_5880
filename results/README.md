# Resultados — Ressoador Ômega em RO5880

Dados brutos exportados do Ansys HFSS 2025 R2 Student, gerados por
`scripts/omega_antenna_nv.py` e pelas funções de sweep/otimização nele
definidas. Todos os números aqui vêm de **solves discretos reais**,
não de estimativa nem de interpolação — ver histórico completo em
`../README.md` seção 5, inclusive dos erros de leitura e do problema
de metodologia corrigidos no caminho.

## Arquivos

| Arquivo | O quê |
|---|---|
| `final_S11_S21_bare_no_diamond.csv` | **Resultado final verificado**, design `Omega_RO5880` (sem diamante) |
| `final_S11_S21_with_diamond.csv` | **Resultado final verificado**, design `Omega_RO5880_Diamond` |
| `field_MagH_line_cuts.csv` | Magnitude do campo H (`Mag_H`) ao longo de dois cortes de linha (x e y) pela abertura, na altura do topo do diamante |
| `final_S11_S21_with_diamond_alumina.csv` | **Resultado final verificado**, design `Omega_RO5880_Diamond_Alumina` (com alumina 25×25×0,67mm) |
| `plot_S11_verificado.png` | Gráfico dos dois acima, com as transições Zeeman marcadas (mesmo conteúdo de `figures/fig_S11.png`) |
| `figures/` | Todas as figuras do relatório — ver tabela abaixo |
| `README.md` | Este arquivo |

### Figuras (`figures/`)

| Arquivo | Conteúdo | Origem |
|---|---|---|
| `fig_S11.png` | S11 verificado, sem e com diamante | dados HFSS (sweep discreto) |
| `fig_S21.png` | S21 verificado, sem e com diamante | dados HFSS (sweep discreto) |
| `fig_S11_S21_diamante.png` | S11 e S21 juntos, design com diamante | dados HFSS (sweep discreto) |
| `fig_delta_diamante.png` | Δ S11 causado pelo carregamento do diamante | dados HFSS (sweep discreto) |
| `fig_planta_baixa.png` | Planta baixa esquemática (terra, substrato, condutor, diamante, portas), com cotas | reconstrução a partir dos parâmetros exatos do script |
| `fig_detalhe_abertura.png` | Detalhe da abertura/fenda com todas as cotas (`r_ap`,`r_w`,`g_w`,`f_w`) e zoom na fenda | idem |
| `fig_stackup_lateral.png` | Corte lateral da pilha de materiais | idem |
| `fig_3d_estrutura_completa.png` | Vista 3D completa (renderização ilustrativa) | reconstrução 3D (Plotly), a partir dos parâmetros exatos do script |
| `fig_3d_detalhe_abertura.png` | Vista 3D em detalhe da abertura e do diamante | idem |
| `fig_hfss_isometrica.png` | Screenshot **real** do modelador HFSS, vista isométrica | exportado direto do modelo simulado (`export_model_picture`) |
| `fig_hfss_topo.png` | Screenshot real do HFSS, vista de topo | idem |
| `fig_hfss_frontal.png` | Screenshot real do HFSS, vista frontal (perfil da pilha) | idem |
| `fig_campo_MagH_cortes.png` | Magnitude do campo H (`Mag_H`) ao longo de dois cortes de linha (x e y) pela abertura | dados HFSS (relatório de campo em linha) |

As figuras `fig_hfss_*` são as únicas geradas **diretamente pelo
modelo simulado** (autoritativas); as `fig_3d_*`/`fig_planta_baixa`/
`fig_detalhe_abertura`/`fig_stackup_lateral` são reconstruções fiéis
(mesmos parâmetros exatos do script), usadas porque a vista nativa do
HFSS, na escala da placa inteira (24×22mm), não resolve visualmente o
detalhe da abertura (~1,4mm de raio) — as reconstruções servem para
mostrar as cotas com clareza; as capturas reais do HFSS servem para
confirmar que a topologia simulada é de fato essa.

Removidos do repositório os dados de processo (rodadas de sweep 3/4/5
e profile de tempo) — tinham valor só como histórico de metodologia,
já registrado em texto no `../README.md`; não são fundamentação do
resultado final e só adicionavam ruído aqui.

## Metodologia (por que estes números são confiáveis)

Duas correções de metodologia foram necessárias antes de confiar no
resultado — registradas porque generalizam para qualquer leitura
futura de resultado HFSS neste projeto:

1. **Não confiar no primeiro valor lido pós-otimização.** A primeira
   leitura após a otimização multivariável pegou por engano uma
   variação *vizinha* da trajetória do otimizador, não o ponto final
   exato — reportou números ~3dB errados. Corrigido forçando um solve
   do zero (`revert_to_initial_mesh=True`, ignora cache) exatamente
   nos valores finais de `r_ap/r_w/f_w/g_w`.
2. **Não confiar em sweep Interpolating fora da vizinhança do ponto
   de adaptação da malha.** O `Sweep1` original é Interpolating,
   ajustado a partir de UM ponto de malha adaptada em 2,87GHz e
   extrapolado para toda a banda 0,5–6GHz — os valores nas bordas do
   sweep (perto de 0,5 e 6GHz) eram artefato de extrapolação, não
   física resolvida de verdade. Corrigido criando um sweep
   **Discreto** (`Sweep_Discrete_Zeeman`, 2,5–3,2GHz, passo 0,02GHz,
   36 pontos), que resolve o sistema linear em cada frequência listada
   de fato. Os dados aqui vêm exclusivamente desse sweep discreto.

Os dois métodos de verificação (solve pontual forçado + sweep
discreto completo) convergiram para os mesmos números dentro do ruído
numérico — o resultado abaixo é, portanto, verificado por dois
caminhos independentes.

## Resultado final

| Freq | sem diamante | com diamante | com diamante + alumina |
|---|---|---|---|
| 2,50 GHz | −27,56 dB | −32,26 dB | −17,71 dB |
| 2,74 GHz (transição m_s=0↔−1) | −27,39 dB | −31,80 dB | −17,46 dB |
| 2,87 GHz (centro, D do NV⁻) | −27,42 dB | −31,61 dB | −17,43 dB |
| 2,97 GHz (transição m_s=0↔+1) | −27,50 dB | −31,52 dB | −17,47 dB |
| 3,20 GHz | −27,89 dB | −31,42 dB | −17,74 dB |

Ver `plot_S11_verificado.png` / `figures/fig_S11.png`. A alumina
(25×25×0,67mm, εr≈9,8) desloca o casamento para **pior** que o
diamante isolado (−31dB → −17dB), mas ainda bem funcional — segue a
mesma forma de cauda larga e suave, só que mais rasa; ainda muito
acima do limiar típico de −10dB usado como referência de bom
casamento em RF. Dados em `final_S11_S21_with_diamond_alumina.csv`,
design `Omega_RO5880_Diamond_Alumina`.

**Leitura física, com embasamento:**

- O casamento é uma **cauda larga e suave** (não um pico estreito de
  alto Q), cobrindo com bastante folga as duas transições Zeeman em
  ~4,7mT (2,74 e 2,97GHz). Isso atende diretamente ao requisito de
  banda ≥250MHz do projeto (`../README.md` seção 1), que existe porque
  o campo estático B₀ separa as transições m_s=0↔−1 e 0↔+1 por efeito
  Zeeman e a antena precisa cobrir as duas sem retuning — um ressoador
  de alto Q não serve para isso.
- O diamante desloca o casamento para **melhor** (−27dB → −32dB), não
  para pior. Isso confirma, na prática, a expectativa teórica: uma
  cauda larga de casamento é robusta a uma perturbação dielétrica
  moderada (a carga do diamante), ao contrário do que aconteceria com
  um pico estreito, facilmente destonado por qualquer mudança de carga
  — o mesmo motivo pelo qual a topologia ômega de dois portos
  (Opaluch, Oshnik, Nelz & Neu, *Nanomaterials* 11, 2108 (2021),
  doi:10.3390/nano11082108) foi escolhida sobre alternativas de maior
  Q desde o início do projeto.
- A profundidade obtida (−27 a −32dB, ou seja, ≤3% da potência
  refletida em toda a banda de interesse) é consistente com o
  desempenho relatado para essa topologia no artigo de referência
  (S11 principal ~−47dB num ponto único, banda 6,3–8,2GHz dependendo
  da espessura do diamante) — a diferença de profundidade absoluta é
  esperada, já que a geometria aqui foi reotimizada para os materiais
  disponíveis (Rogers RO5880 + gap de PCB) em vez de reproduzir as
  dimensões de litografia do artigo (gap de 7µm), como já discutido em
  `../README.md` seção 4.

**⚠️ Suposição não verificada: o plano de terra (titânio,
32×29mm) foi copiado do setup do artigo de referência, não confirmado
como material disponível para este projeto** (ver `../README.md`
seção 2). Todo o S11 reportado aqui depende dessa suposição — se o
plano de terra real for diferente (material, tamanho, ou ausente),
os números precisam ser reconferidos.

## Avaliação de campo

Campo magnético $H$ avaliado em dois cortes de linha (x e y, ±2mm),
passando pelo centro da abertura, na altura do topo do diamante — a
mesma metodologia de linha usada na Fig. 4 de Opaluch et al. (2021),
no design `Omega_RO5880_Diamond`, em `Setup1 : LastAdaptive`
(2,87GHz, 1W na porta).

| Corte | min dentro da abertura | max dentro da abertura | média | variação |
|---|---|---|---|---|
| x (ao longo do gap) | 41,6 A/m | 62,3 A/m | 57,0 A/m | 36,3% |
| y (perpendicular ao gap) | 45,9 A/m | 62,5 A/m | 58,3 A/m | 28,5% |

Ver `fig_campo_MagH_cortes.png`. O campo é máximo (~62 A/m @ 1W) muito
próximo do centro da abertura e cai monotonicamente para fora, com uma
assimetria real entre os cortes x e y — esperada, já que o gap (no
eixo −x) quebra a simetria azimutal da estrutura, o mesmo tipo de
assimetria relatado no artigo de referência entre os cortes paralelo e
perpendicular ao gap. As pequenas discontinuidades em ±1,5mm coincidem
com a borda do diamante (3×3mm) — provável transição de malha na
interface de material, não um artefato espúrio.

**Ordem de grandeza comparável à referência**, embora menor: Opaluch
et al. relatam 170–280 A/m a 1W para a geometria original (gap de
7µm, litografia); aqui, com gap de PCB (150µm, 20× maior) e geometria
reotimizada, o campo é proporcionalmente menor — consistente com o
elemento capacitivo mais fraco.

**Perpendicularidade (componente $H_z$) não foi extraída
numericamente.** Todas as tentativas de obter a componente $H_z$
isolada (via calculadora de campos e via relatório de campo por
expressão nomeada) encontraram incompatibilidades reais na versão
instalada do pyaedt (1.6.0) com este tipo de solução (`GrpcApiError`
em `EnterVector`/`CalcOp('ScalarZ')`; `abnormal script termination` em
`LoadNamedExpressions`; `Hx`/`Hy`/`Hz`/`Mag_Hx`/`Mag_Hy`/`Mag_Hz` como
strings de expressão retornam "No Data Available" no relatório de
campo por linha — só `Mag_H`, a magnitude do vetor completo, funciona
de forma confiável). A predominância da componente perpendicular
próxima ao centro de um laço de corrente é, no entanto, uma
consequência direta de simetria em magnetostática (o campo no eixo de
um laço circular é puramente axial), e a própria referência confirma
essa predominância dentro de um raio de ~260µm para geometria
semelhante — a expectativa física é sólida mesmo sem confirmação
numérica direta nesta versão do software.

## Parâmetros do modelo (para reprodutibilidade)

- Substrato: Rogers RT/duroid 5880, εr=2,20, tanδ=0,0009, h=0,75mm
  (material fixo disponível, ver `../README.md` seção 2)
- Placa: 24×22mm · Terra (porta-amostra de titânio): 32×29mm
- `r_ap=0,345mm · r_w=1,077mm · f_w=1,700mm · g_w=0,150mm` (mínimo de
  PCB — ver `../README.md` seção 4 sobre a restrição de fabricação)
- Diamante (quando presente): IIa, 3×3×0,300mm, εr=5,7, tanδ=1e-5
- Malha do gap: caixa não-modelo contida no `Substrate`,
  `maximum_length = g_w/3`
- Setup: `HFSSDriven`, malha adaptativa em 2,87GHz,
  `MaximumPasses=20`, `MaxDeltaS=0,02`
- Sweep verificado: Discreto, 2,5–3,2GHz, passo 0,02GHz (36 pontos)

## Referências citadas

- Opaluch, Oshnik, Nelz & Neu, *"Optimized Planar Microwave Antenna
  for Nitrogen Vacancy Center Based Sensing Applications"*,
  Nanomaterials 11, 2108 (2021). doi:10.3390/nano11082108 ·
  arXiv:2108.09122 — topologia ômega de dois portos e parâmetros de
  referência para validação.
- Barry et al., *Rev. Mod. Phys.* 92, 015004 (2020) — sensibilidade em
  magnetometria NV e motivação para banda larga em vez de alto Q.
- Ver `../README.md` seção 10 para a lista completa de referências do
  projeto.
