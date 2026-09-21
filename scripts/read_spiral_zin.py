"""Diagnostico do design da espiral (build_spiral, RING_MODE=
"build_spiral_single") CONECTANDO na sessao do AEDT que JA ESTA
ABERTA (a mesma janela onde o solve acabou de rodar) - mesmo padrao
de scripts/read_live_stub_results.py, adaptado para nao depender de
copiar/colar o terminal (usuario relatou sessao remota com renderizacao
bugada - nem o terminal nem a visualizacao 3D estao confiaveis para
ele agora) nem da visualizacao 3D do modelo.

O resultado do plot dB(S11) rodado (1-5GHz) veio praticamente PLANO,
perto de 0dB (~-0.01 a -0.12dB), SEM nenhum vale de ressonancia - nao
e o esperado para uma espiral de 6 voltas (deveria ter varios modos
nessa faixa). Duas hipoteses a descartar aqui, sem precisar da GUI:

  1. O uniao (unite) entre Spiral_trace e Feed_line pode ter falhado
     silenciosamente (mesma armadilha ja documentada no roadmap.md
     5.1 para o disco+furo do Sasaki - uma fresta de poucos
     micrometros pode nao acusar erro no unite mas deixar dois
     pedacos desconectados). Se isso aconteceu, a porta estaria
     vendo so um coto de linha, nao a espiral inteira.
  2. Mesmo com a uniao OK, a ressonancia pode simplesmente estar fora
     da faixa 1-5GHz escaneada (o comprimento total da trilha, bem
     maior que os ~19mm de um quarto de onda em 2.87GHz, sugere um
     modo fundamental de linha de transmissao bem abaixo de 1GHz).

Este script (sem reabrir nem re-resolver nada):
  a) lista os nomes de objetos no modelador - se "Feed_line" ou
     "Spiral_trace" ainda aparecerem separados (em vez de terem virado
     "Conductor"), a uniao NAO funcionou - hipotese 1 confirmada.
  b) roda hfss.validate_full_design() - confere portas/excitacoes sem
     precisar abrir nenhuma janela.
  c) imprime a tabela COMPLETA de Zin (Re/Im) no sweep ja resolvido -
     mesmo com dB(S11) raso, um cruzamento de Im(Zin) por zero ainda
     aponta onde a ressonancia real esta.

Tudo (sucesso OU erro, com traceback completo) e sempre gravado em
resultado_spiral_zin.txt, alem de impresso no terminal - para o caso
do terminal tambem estar bugado na sessao remota.

Uso: python scripts/read_spiral_zin.py
"""
import sys
import traceback

sys.path.insert(0, r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\scripts")

OUT_FILE = r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\resultado_spiral_zin.txt"

PROJECT_PATH = (r"C:\Users\João Victor\Documents\Ansoft\\"
                r"NV_Resonators_Ring_vs_Omega_2p87GHz.aedt")

lines = []


def log(msg):
    print(msg)
    lines.append(str(msg))


hfss = None
try:
    from ansys.aedt.core import Hfss
    import nv_resonators_compare as nvr

    log("Tentando conectar na sessao do AEDT ja aberta (new_desktop=False)...")
    try:
        hfss = Hfss(project=PROJECT_PATH, new_desktop=False,
                    non_graphical=False)
    except Exception as e:
        log(f"  nao havia sessao aberta pra conectar ({type(e).__name__}: "
            f"{e}). Abrindo uma sessao NOVA (new_desktop=True) direto do "
            f"arquivo salvo em disco...")
        hfss = Hfss(project=PROJECT_PATH, new_desktop=True,
                    non_graphical=False)

    log(f"Designs no projeto: {hfss.design_list}")
    candidates = [d for d in hfss.design_list if "Spiral" in d]
    design_name = candidates[-1] if candidates else hfss.design_list[-1]
    log(f"Usando design: '{design_name}'")
    if hfss.design_name != design_name:
        hfss.set_active_design(design_name)

    log("\n--- (a) objetos no modelador ---")
    obj_names = hfss.modeler.object_names
    log(f"Objetos: {obj_names}")
    # 2026-09-21: apos a mudanca para acoplamento capacitivo
    # (feed_gap>0, ver build_spiral), 'Feed_line' e 'Spiral_conductor'
    # SEPARADOS agora e o esperado (o gap e proposital, nao um bug de
    # unite) - so 'Conductor' unico (nome do modo antigo, feed_gap=0)
    # ou nomes totalmente diferentes dos dois e que indicam problema.
    if "Spiral_conductor" in obj_names and "Feed_line" in obj_names:
        log("OK (modo gap capacitivo): 'Spiral_conductor' e 'Feed_line' "
            "SEPARADOS - e o esperado agora (feed_gap>0, acoplamento por "
            "gap, nao uniao). O gap em si so se confirma medindo a "
            "distancia real (Modeler > Measure entre as duas bordas) ou "
            "olhando se ha ressonancia com casamento melhor no S11.")
    elif "Conductor" in obj_names:
        log("Modo uniao galvanica direta (feed_gap=0, comportamento "
            "antigo) - so existe 'Conductor', sem 'Feed_line'/"
            "'Spiral_trace' soltos. Isso NAO e o modo ativo agora "
            "(SPIRAL_MODEL usa feed_gap=0.5mm) - confirme qual dict foi "
            "usado nessa rodada se nao era essa a intencao.")
    else:
        log("*** Nao achei nem 'Conductor' nem 'Spiral_conductor'+"
            "'Feed_line' - nomes inesperados, ver lista completa acima. ***")

    log("\n--- (b) validate_full_design (portas/excitacoes) ---")
    try:
        val_list, val_ok = hfss.validate_full_design(ports=1)
        log(f"Validacao OK? {val_ok}")
        for v in val_list:
            log(f"  {v}")
    except Exception as e:
        log(f"  nao consegui rodar validate_full_design ({e})")

    log("\n--- (c) tabela completa de Zin no sweep ja resolvido ---")
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nvr.print_zin_table(hfss, target_freq=2.87, compact=False)
    captured = buf.getvalue()
    print(captured)
    lines.append(captured)

except Exception:
    tb = traceback.format_exc()
    log("\n===== ERRO (traceback completo abaixo) =====")
    log(tb)

finally:
    try:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n(resultado completo salvo em: {OUT_FILE})")
    except Exception:
        print("\n(NAO consegui salvar o arquivo de resultado - "
              "veja o traceback acima na tela mesmo)")
