"""
Lançamento de moeda: Lei dos Grandes Números (abordagem frequentista)
Semana de Ciência, Tecnologia e Inovação, UEPB, Campus I.

Como rodar:  streamlit run app.py

Organização do arquivo:
  1. Configurações e constantes
  2. Estilo (CSS da página)
  3. Formatação (padrão brasileiro)
  4. Estatística (funções pequenas e puras)
  5. Gráficos e HTML (convergência, binomial, moeda + contadores)
  6. Estado e ações (callbacks dos botões)
  7. Interface (painel principal)
"""

import math
import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES
# =============================================================================
st.set_page_config(layout="wide", page_title="Lançamento de moeda", page_icon="🪙")

# Cores (valem para tema claro e escuro; os fundos vêm do tema do Streamlit).
AZUL = "#1E88E5"             # destaque: números, linha, barra destacada
AZUL_ESCURO = "#1565C0"      # hover/clique do botão
AZUL_FOCO = "rgba(30, 136, 229, 0.35)"
CINZA = "rgba(128, 128, 128, 0.45)"        # barras comuns, bordas
CINZA_GRADE = "rgba(128, 128, 128, 0.18)"  # grade dos gráficos
CINZA_REF = "rgba(128, 128, 128, 0.95)"    # linha de referência em 0,5
MOEDA = "#FFD54F"
MOEDA_BORDA = "#F9A825"
MOEDA_TEXTO = "#7A4F00"

TETO_LANCAMENTOS = 100_000  # máximo de lançamentos acumulados
OPCOES_SIMULACAO = [10, 100, 1_000, 10_000]
PONTOS_COMPLETOS = 100      # até aqui, plota todos os pontos (com bolinhas)
MAX_PONTOS = 400            # depois, plota no máximo ~400 pontos
JANELA_DESVIOS = 4          # janela da binomial: média ± 4 desvios padrão
ALTURA_GRAFICO = 300        # px
ALTURA_PLACAR = 300         # px (moeda + espaço do pulinho + contadores)
DIAMETRO_MOEDA = 120        # px
DURACAO_GIRO = 0.55         # s (animação da moeda)
ALTURA_PULO = 50            # px
VOLTAS = 3                  # voltas completas no giro

# Preencha com os nomes da equipe (aparece no rodapé da página).
INTEGRANTES = "Apollo Borges, Felipe Ferreira e Leonardo Alexandre"

# Anti-spam no servidor (segunda linha de defesa, além do bloqueio por CSS).
# LANÇAR e SIMULAR compartilham a mesma trava: um clique logo após o outro é ignorado.
INTERVALO_LANCAR = DURACAO_GIRO   # s
INTERVALO_SIMULAR = 0.3           # s

# Plotly sem barra de ferramentas (não "rouba" o toque no celular)
CONFIG_PLOTLY = {"displayModeBar": False}


def preencher(modelo, **valores):
    """Troca os marcadores __CHAVE__ do modelo pelos valores informados."""
    for chave, valor in valores.items():
        modelo = modelo.replace(f"__{chave}__", str(valor))
    return modelo


# =============================================================================
# 2. ESTILO (CSS DA PÁGINA)
# =============================================================================
ESTILO_CSS = """
<style>
/* ---- Compactação da página ---- */
.block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem;
    padding-bottom: 0.5rem;
}
header[data-testid="stHeader"] { display: none; }
div[data-testid="stVerticalBlock"] { gap: 0.6rem; }

/* ---- Abertura (<div>, porque o Streamlit põe margem em <p>) ---- */
.titulo   { font-size: 2rem; font-weight: 800; line-height: 1.2; }
.pergunta { font-size: 1.25rem; margin-top: 0.25rem; }
.pergunta b { color: __AZUL__; }
.apoio    { font-size: 0.95rem; margin-top: 0.25rem; opacity: 0.7; }
.rodape   { font-size: 0.85rem; margin-top: 0.4rem; opacity: 0.65; }

/* ---- Botões ---- */
.stButton > button, [data-testid="stButton"] button {
    min-height: 2.8rem;
    font-weight: 700;
    border-radius: 8px;
    transition: none;
}
[data-testid="stBaseButton-primary"] {
    min-height: 3.4rem;
    font-size: 1.15rem;
    letter-spacing: 0.05em;
    background-color: __AZUL__;
    border-color: __AZUL__;
    color: #FFFFFF;
}
[data-testid="stBaseButton-primary"]:hover:not(:disabled),
[data-testid="stBaseButton-primary"]:focus:not(:disabled),
[data-testid="stBaseButton-primary"]:active:not(:disabled) {
    background-color: __AZUL_ESCURO__ !important;
    border-color: __AZUL_ESCURO__ !important;
    color: #FFFFFF !important;
}
[data-testid="stBaseButton-primary"]:focus-visible {
    box-shadow: 0 0 0 0.2rem __AZUL_FOCO__ !important;
}
[data-testid="stBaseButton-primary"]:disabled { opacity: 0.55; }

/* Botões secundários: hover/foco em azul (e não vermelho) */
[data-testid="stBaseButton-secondary"]:hover:not(:disabled),
[data-testid="stBaseButton-secondary"]:focus:not(:disabled),
[data-testid="stBaseButton-secondary"]:active:not(:disabled) {
    border-color: __AZUL__ !important;
    color: __AZUL__ !important;
}
[data-testid="stBaseButton-secondary"]:focus-visible {
    box-shadow: 0 0 0 0.2rem __AZUL_FOCO__ !important;
}

/* ---- Seletor "Simular N lançamentos" ---- */
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child {
    background-color: __AZUL__ !important;
    border-color: __AZUL__ !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"]:hover:not(:has(input:disabled)) > div:first-child {
    border-color: __AZUL__ !important;
}

/* ---- Bloqueio + spinner enquanto o app processa um clique ---- */
/* O Streamlit marca o app com data-test-script-state="running" durante a execução.
   Aí acontecem duas coisas:
   1) ::before = camada transparente sobre a tela toda: NADA recebe clique/toque
      (vale para Simular, Resetar, seletor, toggle, gráfico...). Isso entra na hora.
   2) ::after = spinner azul no centro. Os dois efeitos visuais (véu e spinner)
      só aparecem depois de 0,15 s, então cliques rápidos não fazem a tela piscar. */
[data-test-script-state="running"]::before {
    content: "";
    position: fixed; inset: 0; z-index: 999998;
    cursor: progress;
    background: rgba(128, 128, 128, 0);
    animation: pl-veu 0.01s linear 0.15s forwards;
}
[data-test-script-state="running"]::after {
    content: "";
    position: fixed; top: 50%; left: 50%; z-index: 999999;
    width: 44px; height: 44px; margin: -22px 0 0 -22px;
    box-sizing: border-box;
    border: 4px solid rgba(128, 128, 128, 0.3);
    border-top-color: __AZUL__;
    border-radius: 50%;
    pointer-events: none;
    opacity: 0;
    animation:
        pl-gira 0.8s linear infinite,
        pl-aparecer 0.01s linear 0.15s forwards;
}
@keyframes pl-gira     { to { transform: rotate(360deg); } }
@keyframes pl-aparecer { to { opacity: 1; } }
@keyframes pl-veu      { to { background: rgba(128, 128, 128, 0.18); } }
@media (prefers-reduced-motion: reduce) {
    [data-test-script-state="running"]::after { animation-duration: 2.4s, 0.01s; }
}
</style>
"""

ABERTURA_HTML = """
<div class="titulo">Lançamento de moeda</div>
<div class="pergunta">Quantas vezes é preciso lançar uma moeda para ter <b>certeza</b> de que ela é justa?</div>
<div class="apoio">Simule lançamentos, compare os resultados com as probabilidades teóricas e observe a Lei dos Grandes Números em ação!</div>
"""


def html_rodape():
    equipe = f" Equipe: {INTEGRANTES}." if INTEGRANTES.strip() else ""
    return (
        '<div class="rodape">'
        'Projeto desenvolvido por alunos do 2º período de Estatística e Ciência de Dados da UEPB para a II SECT-CCT, '
        'utilizando NumPy, Plotly e Streamlit.<br>'
        f"{equipe}"
        '</div>'
    )


def injetar_css():
    st.markdown(
        preencher(ESTILO_CSS, AZUL=AZUL, AZUL_ESCURO=AZUL_ESCURO, AZUL_FOCO=AZUL_FOCO),
        unsafe_allow_html=True,
    )


# =============================================================================
# 3. FORMATAÇÃO (padrão brasileiro: vírgula decimal, ponto de milhar)
# =============================================================================
def fmt_int(x):
    """12345 -> '12.345'"""
    return f"{int(x):,}".replace(",", ".")


def fmt_dec(x, casas=2):
    """0.4312 -> '0,43'"""
    return f"{x:.{casas}f}".replace(".", ",")


def casas_para(n):
    """Mais lançamentos => mais casas decimais para enxergar a diferença."""
    if n < 1_000:
        return 2
    if n < 10_000:
        return 3
    return 4


def fmt_pct(p):
    """Probabilidade (0 a 1) -> texto legível em %, sem notação científica."""
    pct = p * 100
    if pct >= 99.95:
        return "100%"
    if pct >= 1:
        return f"{pct:.1f}".replace(".", ",") + "%"
    if pct >= 0.01:
        return f"{pct:.2f}".replace(".", ",") + "%"
    return "menos de 0,01%"


def plural(qtd, singular, plural_):
    return singular if qtd == 1 else plural_


# =============================================================================
# 4. ESTATÍSTICA (funções pequenas e puras)
# =============================================================================
def lancar_uma_vez():
    """Um lançamento: 1 = cara, 0 = coroa."""
    return int(np.random.default_rng().integers(0, 2))


def simular_lote(qtd):
    """Vários lançamentos de uma vez (vetorizado). Retorna array int8 de 0/1."""
    return np.random.default_rng().integers(0, 2, size=qtd, dtype=np.int8)


def frequencia_relativa(resultados, indices):
    """Frequência relativa de caras após cada lançamento em `indices` (base 1)."""
    acumulado = np.cumsum(resultados, dtype=np.int64)  # int64 evita overflow do int8
    return acumulado[indices - 1] / indices


def amostrar_indices(n):
    """
    Quais lançamentos vão para o gráfico (downsampling).
    n pequeno: todos. n grande: ~400 pontos espaçados geometricamente,
    sempre incluindo o último.
    """
    if n <= PONTOS_COMPLETOS:
        return np.arange(1, n + 1)
    indices = np.rint(np.geomspace(1, n, MAX_PONTOS)).astype(int)
    return np.unique(np.append(indices, n))


def prob_binomial(n, k):
    """P(X = k) para X ~ Binomial(n, 0,5), calculada em log (sem estourar)."""
    log_p = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        - n * math.log(2)
    )
    return math.exp(log_p)


@st.cache_data(max_entries=128)
def janela_binomial(n, k):
    """
    Valores de k e probabilidades a plotar: média ± 4 desvios padrão
    (dp = sqrt(n)/2), sempre incluindo o k da pessoa.
    """
    media = n / 2
    dp = math.sqrt(n) / 2
    k_min = max(0, math.floor(media - JANELA_DESVIOS * dp))
    k_max = min(n, math.ceil(media + JANELA_DESVIOS * dp))
    k_min, k_max = min(k_min, k), max(k_max, k)
    ks = list(range(k_min, k_max + 1))
    probs = [prob_binomial(n, kk) for kk in ks]
    return ks, probs


# =============================================================================
# 5. GRÁFICOS E HTML
# =============================================================================
def aplicar_layout_base(fig):
    """Visual comum aos dois gráficos. Cores de texto/fundo vêm do tema."""
    fig.update_layout(
        height=ALTURA_GRAFICO,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        separators=",.",  # vírgula decimal e ponto de milhar
        dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        uirevision="fixo",  # o Plotly não reseta o estado entre atualizações
    )
    # fixedrange evita o gráfico "roubar" o scroll/zoom no celular.
    fig.update_xaxes(fixedrange=True, automargin=True, gridcolor=CINZA_GRADE,
                     zeroline=False)
    fig.update_yaxes(fixedrange=True, automargin=True, gridcolor=CINZA_GRADE,
                     zeroline=False)


def montar_fig_convergencia(resultados, escala_log):
    """Frequência relativa de caras x número de lançamentos."""
    n = len(resultados)
    fig = go.Figure()

    if n > 0:
        indices = amostrar_indices(n)
        fig.add_trace(
            go.Scatter(
                x=indices,
                y=frequencia_relativa(resultados, indices),
                mode="lines+markers" if n <= PONTOS_COMPLETOS else "lines",
                line=dict(color=AZUL, width=2.5),
                marker=dict(color=AZUL, size=6),
                hovertemplate="Lançamento %{x:,d}<br>Frequência %{y:.3f}<extra></extra>",
            )
        )

    # Linha de referência em 0,5
    fig.add_hline(y=0.5, line_dash="dash", line_color=CINZA_REF, line_width=1.5)

    aplicar_layout_base(fig)
    fig.update_yaxes(range=[0, 1], dtick=0.25, title="Frequência de caras")

    # Faixa do eixo x calculada (nunca "autorange"): o eixo cresce junto com n,
    # sem saltos com 1 ou 2 pontos e sem trocar de tipo no meio do caminho.
    x_max = max(n, 10)
    if escala_log:
        faixa = [-0.05, math.log10(x_max) + 0.02]  # em log10
        tipo = "log"
    else:
        faixa = [0, x_max * 1.02]
        tipo = "linear"
    fig.update_xaxes(
        title="Número de lançamentos",
        type=tipo,
        range=faixa,
        tickformat=",d",
    )
    return fig


def montar_fig_binomial(ks, probs, k_destaque):
    """Barras da binomial (n, 0,5) com a barra do resultado da pessoa em azul."""
    cor_barras = [AZUL if kk == k_destaque else CINZA for kk in ks]
    fig = go.Figure(
        go.Bar(
            x=ks,
            y=[p * 100 for p in probs],
            marker=dict(color=cor_barras, line=dict(width=0)),
            hovertemplate="%{x:,d} caras: %{y:.3g}%<extra></extra>",
        )
    )
    aplicar_layout_base(fig)
    fig.update_layout(bargap=0.1)
    fig.update_xaxes(title="Número de caras", tickformat=",d")
    if len(ks) <= 21:
        fig.update_xaxes(dtick=1)
    fig.update_yaxes(ticksuffix="%")
    return fig


# Moeda + contadores via st.html (herda cor e fonte do tema; sem iframe, sem piscar).
# Só CSS, sem JavaScript. Classes com prefixo "pl-" para não colidir com o Streamlit.
MODELO_PLACAR = """
<!-- lançamento número __ID__ -->
<style>
  .pl-placar { height: __ALTURA__px; display: flex; flex-direction: column; gap: 8px; }
  .pl-palco {
    position: relative; flex: 1; padding-bottom: 12px;
    display: flex; align-items: flex-end; justify-content: center;
  }
  .pl-sombra {
    position: absolute; bottom: 0; left: 50%; margin-left: -45px;
    width: 90px; height: 9px; border-radius: 50%;
    background: rgba(128,128,128,0.6); __ANIM_SOMBRA__
  }
  .pl-salto { perspective: 900px; will-change: transform; __ANIM_SALTO__ }
  .pl-moeda {
    position: relative; width: __DIAM__px; height: __DIAM__px;
    transform-style: preserve-3d; will-change: transform;
    transform: rotateX(__FINAL__deg);
    __ANIM_GIRO__
  }
  .pl-face {
    position: absolute; inset: 0; border-radius: 50%; box-sizing: border-box;
    border: 6px solid __MOEDA_BORDA__; background: __MOEDA__; color: __MOEDA_TEXTO__;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 21px; letter-spacing: 2px;
    backface-visibility: hidden; -webkit-backface-visibility: hidden;
  }
  .pl-face::after {
    content: ""; position: absolute; inset: 5px; border-radius: 50%;
    border: 2px solid __MOEDA_BORDA__;
  }
  .pl-verso { transform: rotateX(180deg); }

  .pl-contadores { display: flex; gap: 8px; }
  .pl-contador {
    flex: 1; min-width: 0; padding: 6px 8px; text-align: center;
    border: 1px solid __CINZA__; border-radius: 8px; box-sizing: border-box;
  }
  .pl-rotulo { display: block; font-size: 14px; }
  .pl-numero {
    display: block; line-height: 1.2; font-weight: 800; color: __AZUL__;
    font-size: clamp(18px, 5vw, 26px);
  }
  .pl-freq { display: block; font-size: 14px; opacity: 0.7; }

  @media (prefers-reduced-motion: reduce) {
    .pl-moeda, .pl-salto, .pl-sombra { animation: none !important; }
  }
  __KEYFRAMES__
</style>
<div class="pl-placar">
  <div class="pl-palco">
    <div class="pl-sombra"></div>
    <div class="pl-salto"><div class="pl-moeda">
      <div class="pl-face">__FRENTE__</div>
      <div class="pl-face pl-verso">__VERSO__</div>
    </div></div>
  </div>
  __CONTADORES__
</div>
"""


def html_contadores(n, caras, coroas):
    """Caixinhas com caras, coroas, total e frequências relativas."""
    casas = casas_para(n)
    f_cara = fmt_dec(caras / n, casas) if n else "—"
    f_coroa = fmt_dec(coroas / n, casas) if n else "—"

    def caixa(rotulo, numero, rodape):
        return (
            f'<div class="pl-contador"><span class="pl-rotulo">{rotulo}</span>'
            f'<span class="pl-numero">{numero}</span>'
            f'<span class="pl-freq">{rodape}</span></div>'
        )

    return (
        '<div class="pl-contadores">'
        + caixa("Caras", fmt_int(caras), f"freq. {f_cara}")
        + caixa("Coroas", fmt_int(coroas), f"freq. {f_coroa}")
        + caixa("Total", fmt_int(n), f"de {fmt_int(TETO_LANCAMENTOS)}")
        + "</div>"
    )


def html_placar(face, animar, id_acao, n, caras):
    """
    HTML da moeda + contadores.
      face:    1 (cara), 0 (coroa) ou None (nenhum lançamento ainda: moeda neutra).
      animar:  True só no clique de LANÇAR.
      id_acao: número único do lançamento; entra nos nomes das animações para que
               dois resultados iguais seguidos ainda reanimem a moeda.
    O Python já sorteou a face; o CSS só anima até ela.
    """
    if face is None:
        frente = verso = "?"
        angulo_base = 0
    else:
        frente, verso = "CARA", "COROA"
        angulo_base = 0 if face == 1 else 180  # 180 mostra o verso (COROA)

    if animar and face is not None:
        angulo_final = 360 * VOLTAS + angulo_base
        keyframes = (
            f"@keyframes giro_{id_acao} {{ from {{ transform: rotateX(0deg); }} "
            f"to {{ transform: rotateX({angulo_final}deg); }} }} "
            f"@keyframes salto_{id_acao} {{ "
            f"0% {{ transform: translateY(0); animation-timing-function: ease-out; }} "
            f"50% {{ transform: translateY(-{ALTURA_PULO}px); animation-timing-function: ease-in; }} "
            f"100% {{ transform: translateY(0); }} }} "
            f"@keyframes sombra_{id_acao} {{ "
            f"0% {{ transform: scale(1); opacity: 0.6; animation-timing-function: ease-out; }} "
            f"50% {{ transform: scale(0.6); opacity: 0.3; animation-timing-function: ease-in; }} "
            f"100% {{ transform: scale(1); opacity: 0.6; }} }}"
        )
        # Enquanto a moeda gira, o botão LANÇAR fica bloqueado e esmaecido.
        keyframes += (
            f" @keyframes bloqueio_{id_acao} {{ from, to {{ pointer-events: none; opacity: 0.55; }} }} "
            f'[data-testid="stBaseButton-primary"] '
            f"{{ animation: bloqueio_{id_acao} {DURACAO_GIRO}s linear; }}"
        )
        anim_giro = f"animation: giro_{id_acao} {DURACAO_GIRO}s ease-out forwards;"
        anim_salto = f"animation: salto_{id_acao} {DURACAO_GIRO}s linear forwards;"
        anim_sombra = f"animation: sombra_{id_acao} {DURACAO_GIRO}s linear forwards;"
    else:
        angulo_final = angulo_base
        keyframes = anim_giro = anim_salto = anim_sombra = ""

    return preencher(
        MODELO_PLACAR,
        ID=id_acao,
        ALTURA=ALTURA_PLACAR,
        DIAM=DIAMETRO_MOEDA,
        FINAL=angulo_final,
        ANIM_GIRO=anim_giro,
        ANIM_SALTO=anim_salto,
        ANIM_SOMBRA=anim_sombra,
        KEYFRAMES=keyframes,
        FRENTE=frente,
        VERSO=verso,
        CONTADORES=html_contadores(n, caras, n - caras),
        AZUL=AZUL,
        CINZA=CINZA,
        MOEDA=MOEDA,
        MOEDA_BORDA=MOEDA_BORDA,
        MOEDA_TEXTO=MOEDA_TEXTO,
    )


# =============================================================================
# 6. ESTADO E AÇÕES (callbacks)
# =============================================================================
# Estado em st.session_state (independente para cada visitante):
#   resultados       array NumPy int8 (1 = cara, 0 = coroa)
#   id_acao          contador que aumenta a cada lançamento (para reanimar a moeda)
#   animar           True só na execução logo após um clique em LANÇAR
#   mostrar_binomial True quando a revelação da binomial está aberta
#   aviso            mensagem simples para o usuário (ou None)
#   escala_log       escala logarítmica no eixo x (desligada por padrão)
def iniciar_estado():
    padroes = {
        "resultados": np.zeros(0, dtype=np.int8),
        "id_acao": 0,
        "animar": False,
        "mostrar_binomial": False,
        "aviso": None,
        "escala_log": False,
    }
    for chave, valor in padroes.items():
        st.session_state.setdefault(chave, valor)


def muito_rapido(chave, intervalo):
    """True se o último clique com essa chave foi há menos de `intervalo` segundos."""
    agora = time.monotonic()
    if agora - st.session_state.get(chave, -1e9) < intervalo:
        return True
    st.session_state[chave] = agora
    return False


def acao_lancar():
    # Mesma chave "t_acao" em lançar e simular: um não passa por cima do outro.
    if muito_rapido("t_acao", INTERVALO_LANCAR):
        return
    st.session_state["mostrar_binomial"] = False
    st.session_state["aviso"] = None
    resultados = st.session_state["resultados"]
    if len(resultados) >= TETO_LANCAMENTOS:
        return
    novo = np.array([lancar_uma_vez()], dtype=np.int8)
    st.session_state["resultados"] = np.concatenate([resultados, novo])
    st.session_state["id_acao"] += 1
    st.session_state["animar"] = True


def acao_simular():
    if muito_rapido("t_acao", INTERVALO_SIMULAR):
        return
    st.session_state["mostrar_binomial"] = False
    st.session_state["aviso"] = None
    resultados = st.session_state["resultados"]
    pedido = st.session_state["n_simular"]
    qtd = min(pedido, TETO_LANCAMENTOS - len(resultados))
    if qtd <= 0:
        return
    if qtd < pedido:
        st.session_state["aviso"] = (
            f"Para não passar do limite de {fmt_int(TETO_LANCAMENTOS)} lançamentos, "
            f"foram simulados só {fmt_int(qtd)}."
        )
    st.session_state["resultados"] = np.concatenate([resultados, simular_lote(qtd)])


def acao_resetar():
    st.session_state["resultados"] = np.zeros(0, dtype=np.int8)
    st.session_state["mostrar_binomial"] = False
    st.session_state["aviso"] = None
    st.session_state["animar"] = False


def acao_abrir_binomial():
    st.session_state["mostrar_binomial"] = True


def acao_fechar_binomial():
    st.session_state["mostrar_binomial"] = False


def acao_trocar_escala():
    # O toggle só existe na tela de convergência. O Streamlit apaga o estado de
    # widgets que somem da tela, então copiamos o valor para outra chave.
    st.session_state["escala_log"] = st.session_state["escala_log_widget"]


# =============================================================================
# 7. INTERFACE
# =============================================================================
def texto_esperado(n, k):
    """Segunda frase da revelação: compara o resultado com o mais provável."""
    if n == 1:
        return "Só existem duas possibilidades, cara ou coroa, com 50% de chance cada."

    p_topo = prob_binomial(n, n // 2)
    vezes = fmt_int(round(1 / p_topo))

    if n % 2 == 0:
        meio = n // 2
        if k == meio:
            return (
                "Você caiu justamente no resultado mais provável, e mesmo assim "
                f"ele só acontece cerca de 1 vez em {vezes}."
            )
        return (
            f"E a chance de dar {fmt_int(meio)} caras, o \"esperado\"? "
            f"**{fmt_pct(p_topo)}**. Mesmo o resultado mais provável acontece "
            f"só cerca de 1 vez em {vezes}."
        )

    baixo, alto = n // 2, n // 2 + 1
    return (
        f"Com {fmt_int(n)} lançamentos não existe \"metade exata\". Os resultados "
        f"mais prováveis são {fmt_int(baixo)} e {fmt_int(alto)} caras "
        f"(**{fmt_pct(p_topo)}** cada), e mesmo eles acontecem só cerca de "
        f"1 vez em {vezes}."
    )


def bloco_binomial(n, k):
    """Revelação: chance de ter dado exatamente k caras em n lançamentos."""
    st.markdown(
        f"Com **{fmt_int(n)}** {plural(n, 'lançamento', 'lançamentos')}, "
        f"a chance de dar exatamente **{fmt_int(k)}** {plural(k, 'cara', 'caras')} "
        f"é **{fmt_pct(prob_binomial(n, k))}**."
    )
    st.markdown(texto_esperado(n, k))

    ks, probs = janela_binomial(n, k)
    st.plotly_chart(
        montar_fig_binomial(ks, probs, k), config=CONFIG_PLOTLY, width="stretch"
    )

    st.caption(
        "Curioso: quanto mais lançamentos, MENOS provável é cair exatamente na metade "
        f"(com 100 lançamentos, só {fmt_pct(prob_binomial(100, 50))}). Mesmo assim, "
        "a proporção de caras chega cada vez mais perto de 0,5."
    )


def bloco_convergencia(dados, caras):
    """Status + toggle de escala (na mesma linha) + gráfico de convergência."""
    n = len(dados)
    col_texto, col_toggle = st.columns([3, 2], vertical_alignment="center")
    with col_texto:
        if n == 0:
            st.markdown("Lance a moeda para começar o gráfico.")
        else:
            freq = caras / n
            casas = casas_para(n)
            st.markdown(
                f"Frequência de caras: **{fmt_dec(freq, casas)}** · "
                f"distância de 0,5: **{fmt_dec(abs(freq - 0.5), casas)}**"
            )
    with col_toggle:
        st.toggle(
            "Escala log no eixo x",
            value=st.session_state["escala_log"],
            key="escala_log_widget",
            on_change=acao_trocar_escala,
        )
    st.plotly_chart(
        montar_fig_convergencia(dados, st.session_state["escala_log"]),
        config=CONFIG_PLOTLY,
        width="stretch",
    )


# TUDO que reage a cliques fica no MESMO st.fragment: um clique reexecuta só este
# painel, e moeda, contadores e gráfico nunca ficam dessincronizados.
@st.fragment
def painel():
    resultados = st.session_state["resultados"]
    n = len(resultados)
    caras = int(resultados.sum(dtype=np.int64))
    atingiu_teto = n >= TETO_LANCAMENTOS

    # Consome o sinal: só a execução logo após LANÇAR anima a moeda.
    animar = st.session_state.pop("animar", False)

    col_esq, col_dir = st.columns([5, 6], gap="large")

    # ---------------- Coluna esquerda: moeda, contadores e controles --------
    with col_esq:
        face = int(resultados[-1]) if n > 0 else None
        st.html(html_placar(face, animar, st.session_state["id_acao"], n, caras))

        st.button(
            "LANÇAR",
            key="btn_lancar",
            type="primary",
            on_click=acao_lancar,
            disabled=atingiu_teto,
            width="stretch",
        )
        st.radio(
            "Simular N lançamentos",
            OPCOES_SIMULACAO,
            index=1,
            horizontal=True,
            key="n_simular",
            format_func=fmt_int,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.button(
                "Simular",
                key="btn_simular",
                on_click=acao_simular,
                disabled=atingiu_teto,
                width="stretch",
            )
        with c2:
            st.button(
                "Resetar",
                key="btn_resetar",
                on_click=acao_resetar,
                disabled=n == 0,
                width="stretch",
            )

        if atingiu_teto:
            st.warning(
                f"Chegamos ao limite de {fmt_int(TETO_LANCAMENTOS)} lançamentos. "
                "Clique em Resetar para recomeçar."
            )
        elif st.session_state["aviso"]:
            st.info(st.session_state["aviso"])

    # ---------------- Coluna direita: convergência OU binomial --------------
    with col_dir:
        mostrar_binomial = st.session_state["mostrar_binomial"] and n > 0
        if mostrar_binomial:
            st.button(
                "Voltar ao gráfico de convergência",
                key="btn_voltar",
                on_click=acao_fechar_binomial,
                width="stretch",
            )
            bloco_binomial(n, caras)
        else:
            st.button(
                "E qual a chance de ter dado exatamente esse resultado?",
                key="btn_chance",
                on_click=acao_abrir_binomial,
                disabled=n == 0,
                width="stretch",
            )
            bloco_convergencia(resultados, caras)


def main():
    injetar_css()
    iniciar_estado()
    st.markdown(ABERTURA_HTML, unsafe_allow_html=True)
    painel()
    st.markdown(html_rodape(), unsafe_allow_html=True)


main()