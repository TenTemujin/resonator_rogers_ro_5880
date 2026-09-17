# Ressoador de micro-ondas para ODMR de centros NV — 2,87 GHz

Documento de contexto. Objetivo: qualquer pessoa (ou sessão nova do Claude
Code) consegue retomar o projeto lendo só este arquivo.

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

## 3. Topologia escolhida

**Antena ômega de DOIS PORTOS**, recomendada pelo professor.

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

| | Artigo | Simulado |
|---|---|---|
| Profundidade do vale | −47 dB | **−52 dB** ✅ ordem certa |
| Ressonâncias | 0,7 / 2,6 / 5,5 GHz | **3,8 GHz apenas** ❌ |
| S21 | (alto, elemento em linha) | 0 a −1,1 dB ✅ coerente |

**Validação parcial.** Profundidade e comportamento de dois portos batem;
as frequências não. É dessintonia sistemática.

**Causas prováveis, em ordem de suspeita — atacar uma por vez:**
1. **Plano de terra.** No script está PerfE do tamanho do substrato
   (16×11 mm). No artigo é titânio 24×15 mm, **maior** e separado.
   → teste mais rápido: mudar `Ground` para 24×15 mm.
2. **O diamante não está no modelo.** εr ≈ 5,7, carrega justamente a
   abertura. O artigo mostra que importa (banda 8,2 vs 6,3 GHz conforme a
   espessura).
3. **Malha no gap de 7 µm.** Razão placa/gap = 2286:1. Conferir
   convergência e refinar a operação de malha no `Conductor`.

### `Omega_RO5880` — portado para os materiais disponíveis
Parâmetros: `r_ap` = 0,300 · `r_w` = 1,151 · `g_w` = **0,150** (mínimo PCB)
· `f_w` = 2,300 mm (≈50 Ω em RO5880/0,75 mm).

Resultado: S11 abaixo de −15 dB em toda a banda, vale de **−33,6 dB em
5,5 GHz**. S21 entre 0 e −0,38 dB.

Interessante: 5,5 GHz **coincide com um dos modos publicados**. Mas está
longe de 2,87 GHz (fator 1,9). Ajustes na direção certa: aumentar `r_w`
(indutivo) e/ou reduzir `g_w` / alongar as pernas (capacitivo).

## 6. Próximos passos

1. **Fechar a validação do `Omega_Ref_Glass`** (bloqueia o resto).
   Ordem: terra 24×15 mm → incluir o diamante → refinar malha.
2. Com o modelo validado, **varrer o `Omega_RO5880`** para 2,87 GHz.
   Ordem de influência: `g_w` → `r_w` → `f_w`.
   Objetivo duplo, como no artigo: minimizar S11 em 2,87 GHz **e** na faixa
   2,77–2,97 GHz com pesos iguais, maximizando |B| ao mesmo tempo.
3. **Avaliar o campo** (o que realmente decide): plotar H no plano da
   abertura, confirmar predominância de Hz, medir uniformidade sobre a área
   do diamante, comparar com 170–280 A/m @ 1 W.
4. **Alumina** por último, como superstrato, para quantificar o
   deslocamento de f₀.

### Perguntas em aberto para o orientador
- Tamanho do diamante e área que precisa de B₁ uniforme? (define `r_ap`)
- Faixa de B₀ pretendida? (define a banda necessária)
- Acesso a litografia ou só PCB? (define a viabilidade do gap)
- Papel exato da alumina?
- A recomendação de ômega veio deste artigo ou de outro trabalho do grupo?

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
