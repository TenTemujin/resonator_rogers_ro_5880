"""Le o resultado da otimizacao do stub CONECTANDO na sessao do AEDT
que JA ESTA ABERTA (a mesma janela onde a otimizacao acabou de rodar)
- em vez de abrir uma segunda copia do projeto, o que da erro de lock
porque a primeira janela ainda esta com o arquivo aberto.

Uso: python scripts/read_live_stub_results.py
"""
import sys
import traceback

sys.path.insert(0, r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\scripts")

OUT_FILE = r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\resultado_variacoes.txt"

PROJECT_PATH = (r"C:\Users\João Victor\Documents\Ansoft\\"
                r"NV_Resonators_Ring_vs_Omega_2p87GHz.aedt")

lines = []


def log(msg):
    print(msg)
    lines.append(str(msg))


try:
    from ansys.aedt.core import Hfss
    import nv_resonators_compare as nvr

    log("Conectando na sessao do AEDT ja aberta (new_desktop=False)...")
    hfss = Hfss(project=PROJECT_PATH, new_desktop=False,
                non_graphical=False)

    log(f"Designs no projeto: {hfss.design_list}")

    candidates = [d for d in hfss.design_list if "StubOpt" in d]
    design_name = candidates[-1] if candidates else hfss.design_list[-1]
    log(f"Usando design: '{design_name}'")
    if hfss.design_name != design_name:
        hfss.set_active_design(design_name)

    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nvr.print_all_optimetrics_variations(
            hfss, ["stub_distance", "stub_length"])
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
