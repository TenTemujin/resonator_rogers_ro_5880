# Ressoador de micro-ondas para ODMR de centros NV — 2,87 GHz

Documento de contexto. Objetivo: qualquer pessoa (ou sessão nova do Claude
Code) consegue retomar o projeto lendo só este arquivo.

---

## 0. ⚠️ MUDANÇA DE REQUISITOS DO ORIENTADOR (2026-09-18) — LEIA PRIMEIRO

Repassado por Thiago Ferreira após conversa com o Dr. Achiles Fontana em
17–18/09/2026. **Isso invalida a topologia de dois portos (seção 3) como
candidata final** — todo o trabalho de tuning do `Omega_RO5880` (seção 5)
fica como histórico/referência de metodologia, não como design a fabricar.

1. **O ressoador precisa ser de UM PORTO, não dois.** A ômega de Opaluch
   et al. (2021), usada até aqui, é de dois portos por natureza da
   topologia (linha entra, contorna a abertura, sai). Não dá para
   simplesmente "tirar uma porta" dela sem reprojetar (ver seção 7 item 3
   — uma tentativa anterior de ômega de um porto com perna em curto já
   falhou, mas por causa de dimensionamento errado do gap, não por
   impossibilidade da ideia de 1 porto em si).
2. **Dimensões mínimas de fabricação: 0,5 mm.** As dimensões usadas até
   aqui (`g_w = 0,150mm`, `r_ap = 0,345mm` no `Omega_RO5880`) estão
   abaixo do que dá para fabricar — Achiles pediu explicitamente **mínimo
   de 0,5 mm** em qualquer feição crítica (gap, largura de trilha
   estreita). Isso é uma restrição NOVA e MAIOR que a antiga (que
   assumia LPKF, ~100–150 µm de corrosão — ver seção 4, também
   desatualizada agora).
3. **Processo de fabricação mudou: não é mais LPKF.** Entendimento do
   Thiago: o grupo vai **cortar a placa de RO5880 no tamanho certo**
   (isso, sozinho, é o que está acontecendo "hoje" segundo a conversa) e
   a **deposição do condutor E o plano de terra serão feitos em São
   Carlos** — ou seja, o padrão de trilha (o desenho fino da antena) NÃO
   é definido pelo corte de hoje, só o tamanho do substrato. Isso reduz a
   urgência de ter a geometria final fechada hoje, mas não elimina —
   o substrato cortado hoje precisa ser grande o suficiente para caber
   o design final, que ainda não foi re-otimizado (ver seção 3 e 6).
4. **Alumina: confirmar o tipo/permissividade com o Achiles.** Existem
   vários tipos de alumina comercial com εr diferente; o valor usado
   aqui (εr≈9,8, alumina 99,5%) é uma suposição, não confirmado.
5. **Pendência não resolvida:** nenhuma simulação nova foi rodada ainda
   para a topologia de um porto com mínimo de 0,5 mm — este ambiente de
   trabalho não tem AEDT/pyaedt instalados (ver seção 6). A seção 3
   abaixo já foi atualizada para apontar a candidata mais provável
   (anel fendido / split-ring, já existente em código), mas os
   parâmetros geométricos precisam ser re-otimizados antes de fabricar.

---

## 1. Objetivo

Projetar e simular no Ansys HFSS um ressoador planar de micro-ondas para
**ODMR de centros NV⁻ em diamante**, operando em **2,87 GHz** (zero-field
splitting do NV⁻).

**A figura de mérito NÃO é o S11.** É o campo magnético **B₁ perpendicular
ao plano da antena**, dentro da abertura óptica: intensidade (frequência de
Rabi por watt) e **uniformidade** sobre a área do diamante. Uniformidade
ruim causa alargamento inhomogêneo da linha de ODMR e derruba a
sensibilidade.

Requisito de banda: o campo estático B₀ separa as transições
m_s = 0 ↔ −1 e 0 ↔ +1 por efeito Zeeman. Em ~4,7 mT elas ficam em ~2,74 e
~3,00 GHz. A antena precisa cobrir **as duas** sem retuning ⇒ banda de pelo
menos ~250 MHz. Ressoador de alto Q não serve.

## 2. Materiais disponíveis (restrição fixa)

| Item | Especificação |
|---|---|
| Substrato | **Rogers RT/duroid 5880**, εr = 2,20, tanδ = 0,0009, **h = 0,75 mm** |
| Alumina | 25×25 mm e 50×50 mm @ 0,67 mm; 25×50 mm @ 1,3 mm. εr ≈ 9,8, tanδ ≈ 1e−4 |
| Software | Ansys Electronics Desktop **2025 R2 Student** |
| Python | pyaedt **1.6.0** (import via `ansys.aedt.core`), Python 3.14 |

**Papel da alumina: ainda não definido.** O usuário afirmou que é "amostra",
mas no contexto de NV isso não ficou claro. Pendência a confirmar com o
orientador (Dr. Achiles Fontana). Nos scripts ela entra como superstrato
paramétrico, desativável.

**⚠️ Plano de terra de titânio: NÃO é material confirmado como
disponível.** O porta-amostra de titânio usado como plano de terra em
todos os designs (`L_gnd`/`W_gnd`, seção 3) foi copiado do **setup do
artigo de referência** (Fig. 1a de Opaluch et al. 2021 — sample holder
do scanner piezo confocal deles), não da lista de materiais
confirmados acima. Não sabemos se o grupo tem acesso a titânio nessa
forma, nem se o plano de terra real será titânio, cobre de PCB comum,
ou outra coisa. Isso é uma suposição de projeto carregada sem
verificação — ver pendência correspondente na lista de perguntas
abaixo. Se o plano de terra real for diferente (material ou tamanho),
o resultado de S11 precisa ser reconferido.

## 3. Topologia escolhida

**⚠️ SUPERADO em 2026-09-18 — ver seção 0.** A antena ômega de dois
portos abaixo foi a topologia trabalhada até 17/09, mas o Achiles pediu
**um porto só** e feições mínimas de 0,5 mm. Ela fica documentada porque
(a) toda a metodologia de validação/otimização/leitura de resultado
(seção 5, 7, 8) continua válida para qualquer topologia nova, e (b) o
histórico de erros (seção 7) é reaproveitável.

**Candidata mais provável para substituir: anel fendido (split-ring
resonator), UM PORTO**, já implementado em
`scripts/nv_resonators_compare.py` (função `build_ring`), baseado em:
> Sasaki et al., *Rev. Sci. Instrum.* **87**, 053904 (2016) — 2,87 GHz,
> banda 400 MHz, uniforme no furo de 1 mm de diâmetro.
> Misonou et al., *Rev. Sci. Instrum.* **91**, 023703 (2020),
> arXiv:2002.02113 — Tabela I: Antena #1, f=2,790 GHz, r=0,5,
> R+s=10,9, g=0,1 mm, em FR4 1,6 mm; modelo LC série.

Circuito LC série: o laço é o indutor, a fenda radial (`g_slot`) é o
capacitor, alimentado por UMA microfita de 50 Ω encostando na borda
externa do anel — sem segunda porta, sem perna em curto. **`g_slot`
precisa subir para ≥0,5 mm** (hoje está em 0,1 mm no script, copiado
do valor de referência de Misonou, que também é sub-PCB) e os raios
(`R_out`, `r_hole`) precisam ser re-otimizados para RO5880/0,75mm nessa
folga maior — capacitância menor por causa do gap maior tende a exigir
laço maior (mais indutância) para compensar e voltar a 2,87 GHz; ordem
de grandeza ainda não determinada por simulação real (ver seção 6).
Vantagem adicional para o requisito de fabricação: sem a alimentação
"em duas pernas longas até a borda" do design ômega, o anel de um porto
provavelmente não precisa de um substrato tão grande quanto os
24×22 mm do `Omega_RO5880` (que cresceram em boa parte por causa do
comprimento das pernas, não do laço em si) — mas isso também precisa
ser confirmado por simulação, não é garantido.

### Topologia antiga (ômega de DOIS PORTOS) — histórico, não mais alvo

Baseada em:
> O. R. Opaluch, N. Oshnik, R. Nelz, E. Neu,
> *"Optimized Planar Microwave Antenna for Nitrogen Vacancy Center Based
> Sensing Applications"*, **Nanomaterials 11, 2108 (2021)**.
> doi:10.3390/nano11082108 · arXiv:2108.09122

Pontos essenciais dessa topologia:

- **Dois portos.** A microfita entra, contorna a abertura e sai. NÃO é
  ressoador de um porto. Por isso a banda é enorme e o **S21 é alto**
  (a maior parte da potência atravessa) — isso é normal, não defeito.
- As partes **lineares** (pernas paralelas separadas pelo gap) são o
  elemento **capacitivo**; a parte **radial** (o laço) é o **indutivo**.
  Juntas determinam a ressonância.
- Plano de terra: no artigo é o **porta-amostra de titânio (24×15 mm)**
  sob o substrato — **maior que o substrato** (16×11 mm) e separado dele.

### Parâmetros publicados (substrato de vidro borossilicato)

| Parâmetro | Valor |
|---|---|
| Substrato | vidro, εr = 4,82, h = 1 mm, 16 × 11 mm |
| Condutor | 20 nm Cr + 100 nm Au |
| Raio da abertura `r_ap` | **0,300 mm** |
| Largura radial `r_w` | **1,151 mm** |
| Largura do gap `g_w` | **0,007 mm (7 µm)** |
| Largura da linha `f_w` | **1,851 mm** |

### Resultados de referência (alvo de validação)

- Ressonâncias em **0,7 / 2,6 / 5,5 GHz**; S11 = **−47 dB** na principal
- Banda: 8,2 GHz (diamante 50 µm) / 6,3 GHz (diamante 300 µm)
- Campo majoritariamente **perpendicular** dentro de raio de 260 µm
- |B| > 170 A/m no centro, até 280 A/m perto da circunferência (1 W)
- Sensibilidade: **−50 MHz/µm** no gap; **−20 MHz/µm** na largura radial

## 4. ⚠️ Restrição de fabricação (crítica, não resolvida)

O gap de **7 µm** foi feito por **litografia UV** em filme de ouro sobre
vidro. **Não é processo de PCB.** Corrosão de placa convencional chega a
100–150 µm no melhor caso.

Somado a isso, a sensibilidade de −50 MHz/µm significa que ±1 µm de
tolerância já desloca 50 MHz. Inatingível em PCB.

**Consequência:** portar para Rogers 5880 com gap de PCB **não é
reescalonamento linear — é reotimização numérica completa.** Extrapolar
−50 MHz/µm para 150 µm daria −7 GHz, o que é absurdo (a sensibilidade vale
só localmente).

**Pendência:** confirmar com o professor se o grupo tem acesso a litografia.
Se só houver PCB convencional, a viabilidade da ômega nessa forma precisa
ser reavaliada.

## 5. Estado atual

Arquivo principal: `omega_antenna_nv.py` (dois designs no mesmo projeto).

### `Omega_Ref_Glass` — reprodução do artigo
Existe para **validar o modelo HFSS contra um resultado conhecido** antes de
confiar em qualquer extrapolação.

| | Artigo | Simulado (2026-09-17, pós-correção) |
|---|---|---|
| Profundidade do vale | −47 dB | **−54 dB** ✅ ordem certa, até mais fundo |
| Ressonâncias | 0,7 / 2,6 / 5,5 GHz | **3,55 GHz apenas** ❌ (era 3,8 GHz antes) |
| S21 | (alto, elemento em linha) | 0 a −1,9 dB, ~0 dB no vale ✅ coerente |

**Validação parcial, aceita como suficiente por ora.** As 3 correções
(terra 24×15 mm, diamante, malha do gap — ver histórico abaixo) rodaram
no HFSS sem erro e moveram a ressonância na direção certa (3,8 → 3,55
GHz), mas só 1 de 3 modos aparece. Suspeita: o `Setup1` converge a malha
numa única frequência (2,87 GHz) e usa isso para interpolar a banda
inteira 0,5–6 GHz — pode não resolver bem modos tão espalhados (0,7 e
5,5 GHz) mesmo com a malha do gap ok. **Decisão (2026-09-17): não vale a
pena perseguir isso agora** — o ponto de adaptação já é 2,87 GHz nos
dois designs, que é exatamente onde precisamos de precisão para o
`Omega_RO5880`. Retomar essa investigação só se o resultado do RO5880
em 2,87 GHz parecer suspeito.

Histórico da correção (2026-09-17): terra 24×15 mm (porta-amostra de
titânio do artigo, antes era PerfE do tamanho do substrato), diamante
IIa 3×3×0,300 mm (εr=5,7) sobre o condutor, e malha local no gap via
caixa não-modelo (`Mesh_Region_Gap`, `assign_length_mesh` com
`maximum_length = g_w/3`) em vez de refinar a folha `Conductor`
inteira. Essa caixa deu dois bugs reais antes de rodar limpo: (1)
`gap_region.model = False` é o nome de propriedade ERRADO do pyaedt —
o certo é `.is_model`; `.model` só cria um atributo Python solto e não
muda nada no AEDT, então a caixa ficava um sólido real de vácuo
conflitando com o `Substrate` ("Parts ... intersect"); (2) mesmo
corrigido, a caixa cruzava parcialmente a interface Substrate/ar em z —
teve que ficar **inteiramente contida** dentro do `Substrate` (nunca
atravessando outro objeto) para o HFSS aceitar.

### `Omega_RO5880` — portado para os materiais disponíveis
Parâmetros iniciais (ponto de partida do artigo, não otimizados):
`r_ap` = 0,300 · `r_w` = 1,151 · `g_w` = 0,150 · `f_w` = 2,300 mm.
Resultado: vale de −45 dB em ~5,2 GHz — longe de 2,87 GHz, como esperado.

**Histórico do sweep automatizado** (`add_ro5880_sweep()` no código,
todas as rodadas no HFSS em 2026-09-17):

| Rodada | Placa | `g_w` | `r_w` | Resultado |
|---|---|---|---|---|
| 1ª | 16×11mm | 0,10–0,40mm | 1,0–3,5mm | piso ~4,3–4,5 GHz |
| 2ª | 16×11mm | 0,02–0,14mm (sub-PCB) | 1,0–4,0mm | ~4,2–5,2 GHz, não melhorou |
| 3ª | 24×22mm | 0,10–0,15mm | 4,0–9,0mm | ver análise abaixo — **enganosa** |
| 4ª | 24×22mm | 0,15mm (fixo) | 1,0–4,0mm | ver tabela abaixo — janela localizada |
| 5ª (atual) | 24×22mm | 0,15mm (fixo) | **1,2–1,9mm**, passo 0,1 | rodando |

**Lição da 3ª rodada (2026-09-17): não confiar em "vale mais fundo do
gráfico".** Exportando o CSV completo (não só olhando o gráfico) e
lendo o valor exato de `dB(S11)` em 2,87 GHz — que é o que importa, não
onde quer que o vale mais profundo esteja — nenhuma das 12 combinações
passou de −3 dB em 2,87 GHz. E o vale mais profundo de cada `r_w` pulou
de forma **não-monotônica** entre frequências bem diferentes (`r_w=7`→
6 GHz na borda do sweep, `r_w=8`→5,5 GHz, `r_w=9`→4,65 GHz) — exatamente
a armadilha já registrada na seção 7 item 5: o "vale mais fundo" pula
entre **modos diferentes**, não é a mesma ressonância continuando a
baixar. Toda a extrapolação de tendência feita nas rodadas 1–3 baseada
em "qual r_w deu o vale mais baixo" estava, no mínimo em parte,
perseguindo modos diferentes a cada ponto, não uma tendência física
real de um único modo.

**Achado que sobreviveu à correção:** com `r_w=1,151mm` (padrão, sem
variar) nesta placa 24×22mm, o vale ficou em **3,965 GHz** — mais perto
de 2,87 GHz que qualquer coisa testada com `r_w` grande. Sugere que só
aumentar a placa (16×11→24×22) já ajudou bastante nesse modo específico,
e que valores grandes de `r_w` estavam pulando para outro modo, não
continuando a baixar este. A 4ª rodada testa `r_w` numa faixa modesta
(1,0–4,0mm, a mesma escala da 1ª rodada) na placa grande, para tentar
seguir esse MESMO modo (3,965 GHz) continuamente até 2,87 GHz — e ao
analisar o resultado, ler o CSV completo (`dB(S11)` exato em 2,87 GHz
por `r_w`, mais a curva inteira para confirmar que é o mesmo modo se
deslocando, não um salto), nunca só o gráfico.

**Resultado da 4ª rodada (lido do CSV, não do gráfico):**

| `r_w` | `dB(S11)` em 2,87 GHz | vale real | onde |
|---|---|---|---|
| 1,0mm | −16,06 dB | −46,47 dB | 3,875 GHz |
| 1,151mm | **−16,48 dB** (melhor) | −49,44 dB | 3,965 GHz |
| 1,5mm | −14,22 dB | −36,48 dB | 4,670 GHz (quebra a suavidade) |
| 2,0mm | −11,50 dB | −24,43 dB | **< 0,5 GHz** (fora da banda!) |
| 2,5–4,0mm | piora progressiva | — | < 0,5 GHz |

A partir de `r_w=2mm` a ressonância real já passou para abaixo de
0,5 GHz — confirma que `r_w` maior baixa a frequência, só que **a
ressonância cruza exatamente 2,87 GHz entre `r_w=1,151mm` (3,965 GHz)
e `r_w=2,0mm` (<0,5 GHz)**. Janela estreita e agora bem localizada. A
5ª rodada varre fino dentro dela (`r_w` 1,2–1,9mm, passo 0,1mm),
mirando o valor de `dB(S11)` exatamente em 2,87 GHz — não "onde está
o vale", que é a lição de novo.

**Resultado da 5ª rodada — a grade discreta parou de convergir.** O
melhor ponto ficou em `r_w=1,2mm` (−17,11 dB), e dali pra frente (até
1,9mm) o valor só **piorou** progressivamente — contradiz a expectativa
da 4ª rodada (que apontava a ressonância baixando e cruzando 2,87GHz
perto de `r_w=2mm`). Sinal de que há vários modos próximos nessa banda
e uma grade 1D não vai convergir cortando o intervalo manualmente.

**Mudança de estratégia: Otimização contínua, não mais grade discreta.**
`add_ro5880_optimization()` no código cria um setup de Optimetrics >
Optimization (Quasi-Newton) com `r_w` livre entre 1,0–2,0mm, partindo
do melhor ponto conhecido (1,2mm), meta `dB(S11)` em 2,87GHz `<= -40`.
`g_w` fica fixo (0,15mm) — seu efeito já foi medido como fraco.
**Resultado (rodado de verdade neste ambiente, que tem AEDT instalado
em `D:\Ansys HFSS`):** convergiu em `r_w=1,1mm`, `dB(S11)@2,87GHz =
-17,93dB` — só uma leve melhora, travou num platô, ressonância real
ainda em ~4,02GHz. Variar só `r_w` não bastou.

**Otimização multivariável (`r_ap`, `r_w`, `f_w`) — sucesso.**
`add_ro5880_optimization_multivar()` abriu `r_ap` (0,2–0,6mm) e `f_w`
(1,5–3,5mm) como variáveis livres também, além de `r_w` (1,0–2,5mm).
Convergiu em ~9,6 min para **`r_ap=0,345mm`, `r_w=1,077mm`,
`f_w=1,700mm`** (g_w continua 0,150mm, seguro para PCB).

**Resultado (CORRIGIDO em 2026-09-17 após revalidação — ver nota
abaixo): `dB(S11)` entre −27,4 e −27,9 dB em TODA a faixa 2,5–3,2 GHz**
— não é um pico estreito em 2,87GHz, é a cauda larga de uma ressonância
mais baixa (o vale real está perto de 0,5GHz ou abaixo). Isso é
exatamente o que o projeto pede (seção 1: banda ≥250MHz, "ressoador de
alto Q não serve"), então a cauda larga serve melhor que um pico
estreito serviria:

| Freq | `dB(S11)` |
|---|---|
| 2,50 GHz | −27,57 dB |
| 2,74 GHz (transição 0↔−1) | −27,41 dB |
| 2,87 GHz (centro) | −27,44 dB |
| 2,97 GHz (transição 0↔+1) | −27,51 dB |
| 3,20 GHz | −27,89 dB |

Os parâmetros `RO["r_ap"]`, `RO["r_w"]` e `RO["f_w"]` no código já
foram atualizados para esses valores.

**Nota de revalidação (2026-09-17):** a primeira leitura deste
resultado (logo após a otimização) reportou por engano −27 a −34 dB
(com o valor central de −30,53 dB em 2,87GHz). Ao tentar reabrir o
projeto depois para uma segunda checagem independente, dois processos
do AEDT ficaram travados (`ansysedtsv.exe` órfãos) e precisaram ser
finalizados manualmente — nesse processo, a leitura passou a retornar
consistentemente ~−27dB, e o setup `Opt_multivar_2p87GHz` desapareceu
da árvore de Optimetrics (embora as variáveis otimizadas tenham
sobrevivido). Um diagnóstico mostrou que a "variação nominal" exata
(`r_ap=0,345 · r_w=1,077 · f_w=1,700`) não tinha uma solução resolvida
própria — só variações vizinhas da trajetória do otimizador. Um solve
forçado do zero (`revert_to_initial_mesh=True`, ignorando qualquer
cache) nesses valores exatos confirmou **−27,4 a −27,9 dB** como o
número real e verificado. A tabela acima já reflete isso.

**Segunda correção de metodologia (2026-09-17): sweep Interpolating
não é confiável fora da vizinhança de 2,87GHz.** O `Sweep1` usado até
aqui é do tipo Interpolating, ajustado a partir de UM ponto de malha
adaptada em 2,87GHz e extrapolado para toda a banda 0,5–6GHz — os
valores nas bordas do sweep (perto de 0,5 e 6GHz, que apareceram em
análises anteriores como "vale mais fundo fora da banda de interesse")
podiam ser artefato de extrapolação, não física resolvida de verdade.
Criado `add_discrete_zeeman_sweep()`: um sweep **Discreto**
(`Sweep_Discrete_Zeeman`, 2,5–3,2GHz, passo 0,02GHz, 36 pontos) que
resolve o sistema linear em cada frequência de fato. Rodado nos dois
designs (bare e diamante) — os valores no centro da banda bateram com
o solve pontual forçado dentro do ruído numérico (dois métodos
independentes convergindo), então **os números da tabela acima e do
`results/` estão duplamente verificados**. Ver `results/README.md`
para a tabela final completa e o gráfico (`plot_S11_verificado.png`).

## 6. Próximos passos

**Ordem de prioridade mudou em 2026-09-18 (ver seção 0) — os itens 1–4
abaixo são o histórico da ômega de dois portos e ficam CONGELADOS
(não bloqueiam mais nada, não são mais o alvo de fabricação). O plano
ativo agora é a lista "Plano ativo" logo abaixo.**

### Plano ativo (a partir de 2026-09-18)

1. **Re-projetar como UM PORTO com feições ≥0,5mm.** Candidata: anel
   fendido (`build_ring` em `scripts/nv_resonators_compare.py`) — ver
   seção 3. Subir `G_SLOT` de 0,1mm para ≥0,5mm e rodar otimização
   (Optimetrics, mesmo método multivariável já usado com sucesso na
   ômega — ver `add_ro5880_optimization_multivar` como modelo) variando
   `R_out` (e possivelmente `r_hole`, dentro do limite de 0,5mm) até
   casar em 2,87GHz. **Ainda não rodado.**
2. **Definir tamanho de substrato para fabricação** a partir do
   resultado do item 1 — hoje (18/09) só se sabe que precisa ser maior
   que o laço final + margem; ver recomendação provisória de corte
   abaixo, mas ela é uma estimativa de segurança, não um resultado
   simulado.
3. Repetir os passos já validados como metodologia para a topologia
   nova: validar malha do gap, sweep discreto na faixa 2,5–3,2GHz
   (não confiar em Interpolating fora do ponto de adaptação — seção 5),
   reconferir com diamante presente, avaliar uniformidade de campo,
   só then testar alumina.
4. **Confirmar com o Achiles:** tipo exato de alumina/εr, e se o plano
   de terra continua sendo a suposição do porta-amostra de titânio do
   artigo (nunca confirmada) ou muda com o processo de São Carlos.

### Recomendação provisória para o corte de hoje (18/09/2026)

**Sem simulação nova rodada ainda para o anel de um porto com gap
≥0,5mm — isto é uma estimativa de segurança por raciocínio físico, não
um resultado validado.** Gap maior (0,5mm vs 0,1–0,15mm testado antes)
reduz a capacitância do laço, o que tende a EXIGIR um laço maior
(mais indutância) para voltar a ressoar em 2,87GHz — na ômega de dois
portos, o laço otimizado (`r_ap+r_w`) ficou perto de 1,4mm de raio com
gap de 0,15mm; um laço de anel único porto com gap de 0,5mm pode
plausivelmente precisar de um raio de laço da ordem de poucos mm
(uma estimativa física independente já registrada em
`nv_resonators_compare.py`, para um mecanismo de ressonância diferente
— laço em curto de meia-onda —, aponta ~6mm de raio como ordem de
grandeza nesse substrato; não é o mesmo circuito, mas dá uma noção de
escala).

Se o corte de hoje for **só o substrato em branco** (RO5880 cru, sem
padrão de trilha — que segundo o Thiago será depositado depois em São
Carlos), a recomendação é cortar com folga generosa em vez de ajustar
fino agora, já que dá para cortar/aparar depois mas não para alargar:
- **Sugestão: pelo menos 40×40mm por peça** (dá margem confortável para
  um laço de até ~15mm de raio + linha de alimentação + borda), ou
  **50×50mm** se quiser alinhar com o tamanho de alumina já disponível
  (seção 2) para facilitar o alinhamento de amostra depois.
- Cortar **mais de uma peça** no mesmo tamanho, se o material permitir
  — cobre o risco de a otimização pedir algo ligeiramente diferente
  sem precisar de um novo corte depois.
- **Não cortar mais fino que isso sem rodar a otimização primeiro** —
  se o laço final precisar de mais espaço que o cortado, a peça vira
  sucata.

**Bloqueio de execução:** este ambiente de trabalho não tem o Ansys
Electronics Desktop / pyaedt instalados — todo o trabalho aqui é edição
de código, sem rodar HFSS. O item 1 do plano ativo precisa rodar numa
máquina com AEDT 2025 R2 Student + pyaedt 1.6.0 (a mesma usada nas
otimizações da seção 5) antes de qualquer corte fino de trilha.

### Perguntas em aberto para o orientador
- **[NOVO] Confirmar o mínimo de 0,5mm**: vale para toda feição crítica
  (gap E largura de trilha estreita), ou só para o gap? Afeta quanto
  espaço sobra para o `r_hole`/abertura óptica.
- **[NOVO] O corte de hoje é só o substrato em branco, ou já inclui
  algum padrão?** Confirmar antes de considerar a peça "gasta".
- Tamanho do diamante e área que precisa de B₁ uniforme? (define o raio
  do furo/abertura)
- Faixa de B₀ pretendida? (define a banda necessária)
- Papel exato da alumina, e qual tipo/εr exato (pedido explícito do
  Thiago em 18/09 — existem vários tipos de alumina comercial).
- **O plano de terra vai ser mesmo titânio, do tamanho do porta-amostra
  do artigo (24×15mm no artigo, 32×29mm no design tunado)? Ou é cobre
  de PCB comum, outro metal, outro tamanho, agora que a deposição e o
  terra serão feitos em São Carlos?** Essa suposição nunca foi
  confirmada — foi só copiada do setup do artigo de referência. Todo o
  S11 reportado depende dela; se mudar, precisa reconferir.

### Histórico congelado (ômega de dois portos, superado 2026-09-18)

1. ~~Fechar a validação do `Omega_Ref_Glass`~~ — aceito como validação
   parcial suficiente (ver seção 5); não bloqueia mais o resto.
2. ~~Tunar o `Omega_RO5880` para 2,87 GHz~~ — **concluído**: `r_ap=0,345
   · r_w=1,077 · f_w=1,700 · g_w=0,150mm`, S11 entre −27,4 e −27,9dB em
   toda a faixa 2,5–3,2GHz (número verificado, ver nota de revalidação).
2b. ~~Reconferir com o diamante presente~~ — **concluído** (2026-09-17).
   Novo design `Omega_RO5880_Diamond` (mesma geometria, diamante IIa
   3×3×0,300mm sobre a abertura), resolvido do zero (design novo, sem
   ambiguidade de cache). **O casamento sobreviveu e até melhorou:**
   S11 entre −31,4 e −32,4dB em toda a faixa 2,5–3,2GHz (era −27,4 a
   −27,9dB sem o diamante). Confirma a expectativa: a cauda larga é
   robusta ao carregamento dielétrico.
3. Avaliar o campo — não chegou a ser feito nesta topologia (superada
   antes de chegar nesse passo).
4. Alumina — implementado e testado (ver `results/README.md`), mas na
   topologia agora superada.

## 7. Lições do que já deu errado

Registrado porque custou várias horas e não deve se repetir.

1. **Patch retangular** — topologia errada desde o início. Patch irradia em
   campo distante; NV precisa de B₁ de campo próximo uniforme. Erro de
   origem: não perguntei para que servia o ressoador antes de dimensionar.
2. **Anel fendido com gap de 0,1 mm** — nenhuma ressonância. Capacitância
   subdimensionada e/ou malha não resolvia o gap.
3. **Ômega de um porto com perna em curto** — nenhuma ressonância.
   Topologia errada: a ômega da literatura é de dois portos, e as pernas
   paralelas (que eu fiz curtas e afastadas) *são* o capacitor.
4. **Ler geometria por screenshot não funciona** para detalhes de 0,1 mm em
   estruturas de 16 mm. Use a árvore do modelo: contar folhas Perfect E e
   conferir o histórico de operações (`Subtract`, `Unite`) é conclusivo.
5. **`XAtYMin` engana quando há dois mínimos** — ele reporta o global e
   salta entre modos, produzindo curvas descontínuas sem significado.
6. **S11 profundo não prova nada sozinho.** No caso do patch, o vale mais
   fundo não era o modo desejado — só o plot de corrente revelou isso.
   Sempre confirmar pelo campo.

**Regra geral: validar o modelo contra um resultado publicado antes de
otimizar.** Sem referência, otimização vira tentativa e erro.

## 8. Armadilhas da API pyaedt 1.6.0

Todas verificadas contra a documentação oficial e testadas nesta versão.

| Não funciona | Correto |
|---|---|
| `from pyaedt import Hfss` | `from ansys.aedt.core import Hfss` |
| `materials.checkifmaterialexists(n)` | `materials[n]` em try/except |
| `mat.permittivity = 2.2` | `= "2.2"` (string) **+ `mat.update()`** |
| `hfss.AxisDir.ZNeg` | `hfss.axis_directions.ZNeg` |
| `solution_type="Modal"` | `solution_type="DrivenModal"` |
| `create_linear_step_sweep(sweep_name=)` | `name=` |
| `setup.props["Frequency"] = ...` | passar como kwarg em `create_setup()` |
| `duplicate_design(name, label)` | não deixa escolher o nome → use `insert_design()` |
| `unite()` retorna o objeto | retorna nome/bool; o objeto sobrevivente é o 1º da lista |

Outras notas:
- `create_setup(name, setup_type="HFSSDriven", Frequency=, MaximumPasses=, MaxDeltaS=)`
- `modeler.subtract(blank, tool_list, keep_originals=False)`
- `modeler.create_circle(orientation, origin, radius, name=)`
- Sempre rodar uma **verificação geométrica antes de abrir o AEDT**
  (função `check_geometry()`) — falhar cedo com mensagem clara.

## 9. Notas sobre a versão Student

- Limite de malha. Airbox de ~920 cm³ já é pesado; se travar, reduzir o
  airgap (mínimo λ₀/4 = 26,1 mm em 2,87 GHz) ou a placa.
- O aviso *"Renormalizing the port impedance will not impact the field
  results..."* é informativo e **não é problema** para leitura de S11.
  Só importa se for ler valores absolutos de campo — aí habilitar
  "Include Port Post Processing Effects" em HFSS → Fields → Edit Sources.

## 10. Referências

**Principal (ômega, dimensões publicadas)**
- Opaluch, Oshnik, Nelz & Neu, *Nanomaterials* **11**, 2108 (2021).
  doi:10.3390/nano11082108 · arXiv:2108.09122

**Anel planar (topologia alternativa, parâmetros tabelados)**
- Sasaki et al., *Rev. Sci. Instrum.* **87**, 053904 (2016).
  2,87 GHz, banda 400 MHz, uniforme no furo de 1 mm de diâmetro.
- Misonou et al., *Rev. Sci. Instrum.* **91**, 023703 (2020).
  arXiv:2002.02113 — Tabela I traz r, R, s, g das Antenas #1 e #2 e o
  modelo LC série.

**Outras topologias (comparação)**
- Bayat et al., *Nano Lett.* **14**, 1208 (2014) — duplo split-ring;
  5,59 G a 0,5 W, inhomogeneidade RMS 4,4 % sobre 1 mm².
- CPW com fenda / notch — arXiv:2205.02970; discute limitações de fio
  fino (S11 ~ −3 dB), bobinas e ômegas ressonantes vs não ressonantes.
- Ressoador dielétrico (DRA) — arXiv:1805.05441; única topologia com
  uniformidade **3D**; as planares decaem forte na perpendicular.

**Contexto de NV**
- Barry et al., *Rev. Mod. Phys.* **92**, 015004 (2020) — otimização de
  sensibilidade em magnetometria NV.
- Abe & Sasaki, *J. Appl. Phys.* **123**, 161101 (2018) — tutorial de
  engenharia de micro-ondas para NV.
