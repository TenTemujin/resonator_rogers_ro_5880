"""Le o resultado da otimizacao do stub (Opt_stub_2p87GHz) que JA
FOI RODADA - NAO reconstroi nada, NAO otimiza de novo, so abre o
projeto ja existente (numa sessao NOVA do AEDT) e lista todas as
variacoes testadas com dB(S11) em 2.87GHz.

IMPORTANTE: use este script so se NAO houver nenhuma janela do AEDT
aberta com este projeto (senao da erro de "Project is locked" - nesse
caso use scripts/read_live_stub_results.py, que conecta na janela ja
aberta em vez de abrir uma segunda copia).

2026-09-21: reescrito para NUNCA depender do usuario conseguir ver ou
copiar um erro da tela - tudo (sucesso OU excecao/traceback completo)
e sempre gravado em scripts/../resultado_variacoes.txt, alem de
tambem ser impresso no terminal. Se aparecer "erro" na tela e nao der
para copiar, o conteudo estara integralmente no .txt.

2026-09-21: nome do design nao e mais fixo - descoberto que cada
rodada do script principal usa um sufixo de horario novo
(RO5880_Step17_StubOpt_Unloaded_HHMMSS), entao um nome hardcoded fica
desatualizado a cada nova rodada. Agora pega o ultimo design cujo
nome contem "StubOpt" na lista de designs do projeto.

Uso: python scripts/read_stub_opt_results.py
"""
import sys
import traceback

sys.path.insert(0, r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\scripts")

OUT_FILE = r"C:\Users\João Victor\Documents\Ressoador\resonator_rogers_ro_5880\resultado_variacoes.txt"

# caminho COMPLETO do arquivo, nao so o nome - com new_desktop=True nao
# ha nenhum projeto ja aberto para o pyaedt "achar" pelo nome; sem o
# caminho completo ele provavelmente cria um projeto vazio novo em vez
# de abrir o .aedt que ja existe em disco (visto nos logs anteriores,
# ex.: "Parsing C:\...\Documents\Ansoft\NV_Resonators_...aedt")
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

    log(f"Abrindo projeto existente ({PROJECT_PATH})...")
    hfss = Hfss(project=PROJECT_PATH, new_desktop=True,
                non_graphical=False)

    log(f"Projeto aberto. Designs disponiveis: {hfss.design_list}")
    candidates = [d for d in hfss.design_list if "StubOpt" in d]
    design_name = candidates[-1] if candidates else hfss.design_list[-1]
    log(f"Usando design: '{design_name}'")
    if hfss.design_name != design_name:
        hfss.set_active_design(design_name)

    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nvr.print_all_optimetrics_variations(hfss, ["stub_distance", "stub_length"])
    captured = buf.getvalue()
    print(captured)
    lines.append(captured)

except Exception:
    tb = traceback.format_exc()
    log("\n===== ERRO (traceback completo abaixo) =====")
    log(tb)

finally:
    if hfss is not None:
        try:
            hfss.release_desktop(close_projects=False, close_desktop=False)
        except Exception:
            log("\n(aviso: falha ao liberar o desktop no final, ignorando)")
            log(traceback.format_exc())

    try:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n(resultado completo salvo em: {OUT_FILE})")
    except Exception:
        print("\n(NAO consegui salvar o arquivo de resultado - "
              "veja o traceback acima na tela mesmo)")
