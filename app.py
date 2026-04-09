import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import numpy as np

# =====================================================================
# CONFIGURAÇÃO DA PÁGINA E CSS PREMIUM
# =====================================================================
st.set_page_config(page_title="Crypto Elite Terminal", layout="wide", page_icon="⚡")

DARK_BLUE_BUY = '#1D4ED8' 
NEON_SELL = '#FF00FF' 
GOLDEN_POCKET = '#F59E0B' 

st.markdown(f"""
<style>
.main {{background-color: #0d1117;}}
h1, h2, h3, h4, p, li {{color: #e6edf3; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}}
.metric-card {{background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}}
.sinal-card {{background-color: #161b22; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}}
.risk-card {{background-color: #161b22; padding: 20px; border-radius: 12px; border-left: 4px solid #8b5cf6; border-top: 1px solid #30363d; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}}
.vip-card {{background-color: #10151d; padding: 25px; border-radius: 12px; border: 1px solid #f59e0b; box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); margin-bottom: 20px;}}
.macro-card {{background-color: #0d1117; padding: 25px; border-radius: 12px; border: 1px solid #0ea5e9; box-shadow: 0 0 15px rgba(14, 165, 233, 0.1); margin-bottom: 20px;}}
.fib-card {{background-color: #161b22; padding: 20px; border-radius: 12px; border-left: 4px solid {GOLDEN_POCKET}; border-top: 1px solid #30363d; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d;}}
.guia-card {{background-color: #0d1117; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px;}}
.valor-box {{padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #30363d; background: #161b22; box-shadow: 0 2px 4px rgba(0,0,0,0.2);}}

@keyframes blinker_buy {{ 50% {{ opacity: 0.5; box-shadow: 0 0 20px {DARK_BLUE_BUY}; }} }}
@keyframes blinker_sell {{ 50% {{ opacity: 0.5; box-shadow: 0 0 20px {NEON_SELL}; }} }}

.piscar-compra {{ animation: blinker_buy 2s linear infinite; color: #60A5FA; font-weight: bold; background-color: rgba(29, 78, 216, 0.15); padding: 10px; border-radius: 8px; border: 1px solid {DARK_BLUE_BUY}; text-align: center; text-shadow: 0 0 5px {DARK_BLUE_BUY};}}
.piscar-venda {{ animation: blinker_sell 2s linear infinite; color: #F9A8D4; font-weight: bold; background-color: rgba(255, 0, 255, 0.1); padding: 10px; border-radius: 8px; border: 1px solid {NEON_SELL}; text-align: center; text-shadow: 0 0 5px {NEON_SELL};}}
.neutro-padrao {{ color: #8b949e; padding: 10px; background-color: #21262d; border-radius: 8px; text-align: center; border: 1px solid #30363d;}}
.badge-vip {{ background-color: #f59e0b; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; vertical-align: middle; margin-left: 10px; }}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# MENU DE NAVEGAÇÃO
# =====================================================================
st.sidebar.title("🧭 Módulos do Terminal")
pagina_atual = st.sidebar.radio("Selecione a Estratégia:", [
    "📊 1. Análise Quantitativa", 
    "🦅 2. Setup Augusto Backes", 
    "💎 3. Setup Sniper (Alta Precisão)",
    "🤖 4. Radar Automático",
    "🔥 5. Alpha VIP / Sinais",
    "🌍 6. Macro & Geopolítica",
    "📐 7. Análise Fibonacci (Confluência)"
])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configurações do Ativo")

lista_moedas = {
    "Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", 
    "Solana (SOL)": "SOL-USD", "Monad (MON)": "MON-USD", "Virtuals (VIRTUAL)": "VIRTUAL-USD"
}
ativo_selecionado = st.sidebar.selectbox("Ativo Base", list(lista_moedas.keys()))
ticker = lista_moedas[ativo_selecionado]

setups_ideais = {
    "⚡ Scalping Extreme (5 Minutos)": {"period": "5d", "interval": "5m"},
    "🚀 Day Trade Rápido (15 Minutos)": {"period": "60d", "interval": "15m"},
    "🎯 Day Trade (1 Hora)": {"period": "60d", "interval": "1h"},
    "🌊 Swing Trade (Diário)": {"period": "1y", "interval": "1d"},
    "🏛️ Position (Semanal)": {"period": "3y", "interval": "1wk"}
}
setup_escolhido = st.sidebar.selectbox("Estratégia / Timeframe", list(setups_ideais.keys()), index=2)
periodo = setups_ideais[setup_escolhido]["period"]
timeframe = setups_ideais[setup_escolhido]["interval"]

st.sidebar.markdown("---")
st.sidebar.header("📊 Estilo do Gráfico")
escala_log = st.sidebar.checkbox('Escala Logarítmica', value=False)
mostrar_grade = st.sidebar.checkbox('Mostrar Grade de Fundo', value=False)

# =====================================================================
# PROCESSAMENTO CENTRAL DE DADOS
# =====================================================================
@st.cache_data(ttl=150)
def processar_dados(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty or len(df) < 50: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
    C, H, L, O, V = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
    
    # Médias, Volume e Quantitativo
    df['EMA_9'], df['EMA_21'] = ta.trend.EMAIndicator(C, 9).ema_indicator(), ta.trend.EMAIndicator(C, 21).ema_indicator()
    df['EMA_50'], df['EMA_200'] = ta.trend.EMAIndicator(C, 50).ema_indicator(), ta.trend.EMAIndicator(C, 200).ema_indicator()
    df['VWAP'] = ta.volume.VolumeWeightedAveragePrice(H, L, C, V).volume_weighted_average_price()
    df['Volume_SMA'] = V.rolling(20).mean() 
    df['RSI'] = ta.momentum.RSIIndicator(C, 14).rsi()
    macd_obj = ta.trend.MACD(C)
    df['MACD_Line'], df['MACD_Signal'], df['MACD_Hist'] = macd_obj.macd(), macd_obj.macd_signal(), macd_obj.macd_diff()
    df['ATR'] = ta.volatility.AverageTrueRange(H, L, C, 14).average_true_range()
    
    df['Sinal_Compra_Quant'] = (df['EMA_9'] > df['EMA_21']) & (df['EMA_9'].shift(1) <= df['EMA_21'].shift(1)) & (C > df['VWAP'])
    df['Sinal_Venda_Quant'] = (df['EMA_9'] < df['EMA_21']) & (df['EMA_9'].shift(1) >= df['EMA_21'].shift(1))

    # Augusto Backes & Price Action
    df['EMA_8'] = ta.trend.EMAIndicator(C, 8).ema_indicator()
    corpo = abs(C - O)
    filtro_ruido = corpo > (C * 0.001)
    df['Engolfo_C'] = (C > O) & (C.shift(1) < O.shift(1)) & (C >= O.shift(1)) & (O <= C.shift(1)) & filtro_ruido
    df['Martelo_C'] = (2 * corpo < (np.minimum(C, O) - L)) & ((H - np.maximum(C, O)) < corpo) & (C > O) & filtro_ruido
    df['PFR_C'] = (L < L.shift(1)) & (L < L.shift(2)) & (C > C.shift(1)) & (C > O) & filtro_ruido
    df['Backes_Compra'] = (df['Engolfo_C'] | df['Martelo_C'] | df['PFR_C']) & (O > df['EMA_8'])
    df['Backes_Venda'] = ((C < O) & (C.shift(1) > O.shift(1)) & (C <= O.shift(1)) & (O >= C.shift(1)) & filtro_ruido) & (O < df['EMA_8'])
    
    # Sniper
    df['Sniper_Compra'] = (df['MACD_Line'] > df['MACD_Signal']) & (df['MACD_Line'].shift(1) <= df['MACD_Signal'].shift(1)) & (C > df['EMA_200']) 
    df['Sniper_Venda'] = (df['MACD_Line'] < df['MACD_Signal']) & (df['MACD_Line'].shift(1) >= df['MACD_Signal'].shift(1)) & (C < df['EMA_200'])

    return df

df = processar_dados(ticker, periodo, timeframe)

if df is not None:
    ult = df.iloc[-1]
    preco_atual, atr_atual = float(ult['Close']), float(ult['ATR'])
    sl, tp = preco_atual - (1.5 * atr_atual), preco_atual + (3.0 * atr_atual)
    
    y_max, y_min = df['High'].quantile(0.999) * 1.05, df['Low'].quantile(0.001) * 0.95  
    escala_y_tipo = "log" if escala_log else "linear"

    def criar_layout_premium(figura, altura):
        figura.update_layout(height=altura, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, bgcolor='rgba(0,0,0,0)'), hovermode="x unified")
        figura.update_yaxes(type=escala_y_tipo, range=[y_min, y_max], showgrid=mostrar_grade, gridwidth=1, gridcolor='#21262d', zeroline=False, row=1, col=1)
        figura.update_xaxes(showgrid=False, zeroline=False)
        return figura

    # =====================================================================
    # PÁGINAS DE 1 A 6
    # =====================================================================
    if pagina_atual == "📊 1. Análise Quantitativa":
        st.title(f"📊 Análise Quantitativa: {ativo_selecionado}")
        col_m, col1, col2 = st.columns([1, 2, 1])
        with col_m: st.markdown(f"<div class='metric-card'><b>Preço Atual</b><br><span style='font-size:24px;'>${preco_atual:,.4f}</span></div>", unsafe_allow_html=True)
        with col1:
            if float(ult['EMA_9']) > float(ult['EMA_21']) and float(ult['RSI']) < 65 and float(ult['MACD_Hist']) > 0: acao_q, cor_q = "🟢 TENDÊNCIA DE ALTA", "#10b981"
            elif float(ult['EMA_9']) < float(ult['EMA_21']): acao_q, cor_q = "🔴 TENDÊNCIA DE BAIXA", "#ef4444"
            else: acao_q, cor_q = "⚪ ZONA NEUTRA", "#8b949e"
            st.markdown(f"<div class='sinal-card' style='border: 1px solid {cor_q};'><h4 style='margin:0; color:#8b949e;'>Direção Geral</h4><h2 style='margin:10px 0 0 0; color:{cor_q};'>{acao_q}</h2></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='risk-card'><h4 style='margin-top:0; color:#a78bfa;'>Risco ATR</h4>🎯 Alvo: <span style='color:#10b981;'>${tp:,.4f}</span><br>🛑 Stop: <span style='color:#ef4444;'>${sl:,.4f}</span></div>", unsafe_allow_html=True)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#089981', decreasing_line_color='#f23645', increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='#38bdf8', width=1.5), name='EMA 9'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='#fb7185', width=1.5), name='EMA 21'), row=1, col=1)
        cq, vq = df[df['Sinal_Compra_Quant']], df[df['Sinal_Venda_Quant']]
        fig.add_trace(go.Scatter(x=cq.index, y=cq['Low'] - (cq['ATR'] * 0.3), mode='markers', marker=dict(symbol='arrow-up', size=16, color=DARK_BLUE_BUY, line=dict(width=1, color='white')), name='Compra'), row=1, col=1)
        fig.add_trace(go.Scatter(x=vq.index, y=vq['High'] + (vq['ATR'] * 0.3), mode='markers', marker=dict(symbol='arrow-down', size=16, color=NEON_SELL, line=dict(width=1, color='white')), name='Venda'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=['#089981' if v > 0 else '#f23645' for v in df['MACD_Hist']], name='MACD'), row=2, col=1)
        st.plotly_chart(criar_layout_premium(fig, 750), use_container_width=True, config={'displayModeBar': False})

    elif pagina_atual == "🦅 2. Setup Augusto Backes":
        st.title(f"🦅 Setup Augusto Backes: {ativo_selecionado}")
        col_m, col1, col2 = st.columns([1, 2, 1])
        with col_m: st.markdown(f"<div class='metric-card'><b>Preço Atual</b><br><span style='font-size:24px;'>${preco_atual:,.4f}</span></div>", unsafe_allow_html=True)
        with col1:
            if bool(ult['Backes_Compra']): st.markdown(f"""<div class="sinal-card" style="border: 1px solid {DARK_BLUE_BUY};"><h4 style="margin:0; color:#8b949e;">Setup EMA 8</h4><div class="piscar-compra" style="margin-top: 15px;">🔼 SINAL RARO DE COMPRA!</div></div>""", unsafe_allow_html=True)
            elif bool(ult['Backes_Venda']): st.markdown(f"""<div class="sinal-card" style="border: 1px solid {NEON_SELL};"><h4 style="margin:0; color:#8b949e;">Setup EMA 8</h4><div class="piscar-venda" style="margin-top: 15px;">🔽 SINAL RARO DE VENDA!</div></div>""", unsafe_allow_html=True)
            else: st.markdown("""<div class="sinal-card"><h4 style="margin:0; color:#8b949e;">Setup EMA 8</h4><div class="neutro-padrao" style="margin-top: 15px;">Aguardando padrão no momento...</div></div>""", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='risk-card'><h4 style='margin-top:0; color:#a78bfa;'>Risco ATR</h4>🎯 Alvo: <span style='color:#10b981;'>${tp:,.4f}</span><br>🛑 Stop: <span style='color:#ef4444;'>${sl:,.4f}</span></div>", unsafe_allow_html=True)

        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#089981', decreasing_line_color='#f23645', increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_8'], line=dict(color='#eab308', width=2), name='EMA 8'))
        cb, vb = df[df['Backes_Compra']], df[df['Backes_Venda']]
        fig.add_trace(go.Scatter(x=cb.index, y=cb['Low'] - (cb['ATR'] * 0.3), mode='markers', marker=dict(symbol='arrow-up', size=18, color=DARK_BLUE_BUY, line=dict(width=1, color='white')), name='Compra Backes'))
        fig.add_trace(go.Scatter(x=vb.index, y=vb['High'] + (vb['ATR'] * 0.3), mode='markers', marker=dict(symbol='arrow-down', size=18, color=NEON_SELL, line=dict(width=1, color='white')), name='Venda Backes'))
        st.plotly_chart(criar_layout_premium(fig, 700), use_container_width=True, config={'displayModeBar': False})

    elif pagina_atual == "💎 3. Setup Sniper (Alta Precisão)":
        st.title(f"💎 Setup Institucional Sniper: {ativo_selecionado}")
        col_m, col1, col2 = st.columns([1, 2, 1])
        with col_m: st.markdown(f"<div class='metric-card'><b>Preço Atual</b><br><span style='font-size:24px;'>${preco_atual:,.4f}</span></div>", unsafe_allow_html=True)
        with col1:
            if bool(ult['Sniper_Compra']): st.markdown(f"""<div class="sinal-card" style="border: 1px solid {DARK_BLUE_BUY};"><h4 style="margin:0; color:#8b949e;">Setup Sniper (EMA 200)</h4><div class="piscar-compra" style="margin-top: 15px;">💎 ENTRADA SNIPER COMPRA!</div></div>""", unsafe_allow_html=True)
            elif bool(ult['Sniper_Venda']): st.markdown(f"""<div class="sinal-card" style="border: 1px solid {NEON_SELL};"><h4 style="margin:0; color:#8b949e;">Setup Sniper (EMA 200)</h4><div class="piscar-venda" style="margin-top: 15px;">💥 ENTRADA SNIPER VENDA!</div></div>""", unsafe_allow_html=True)
            else: st.markdown(f"""<div class="sinal-card"><h4 style="margin:0; color:#8b949e;">Filtro Institucional (EMA 200)</h4><div class="neutro-padrao" style="margin-top: 15px;">Aguardando gatilho do MACD...</div></div>""", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='risk-card'><h4 style='margin-top:0; color:#a78bfa;'>Risco ATR</h4>🎯 Alvo: <span style='color:#10b981;'>${tp:,.4f}</span><br>🛑 Stop: <span style='color:#ef4444;'>${sl:,.4f}</span></div>", unsafe_allow_html=True)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#089981', decreasing_line_color='#f23645', increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#ffffff', width=3), name='EMA 200 (Macro)'), row=1, col=1)
        cs, vs = df[df['Sniper_Compra']], df[df['Sniper_Venda']]
        fig.add_trace(go.Scatter(x=cs.index, y=cs['Low'] - (cs['ATR'] * 0.4), mode='markers', marker=dict(symbol='arrow-up', size=18, color=DARK_BLUE_BUY, line=dict(width=1, color='white')), name='Compra Sniper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=vs.index, y=vs['High'] + (vs['ATR'] * 0.4), mode='markers', marker=dict(symbol='arrow-down', size=18, color=NEON_SELL, line=dict(width=1, color='white')), name='Venda Sniper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='#3b82f6', width=1.5), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#f59e0b', width=1.5), name='Sinal MACD'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=['rgba(8,153,129,0.5)' if v > 0 else 'rgba(242,54,69,0.5)' for v in df['MACD_Hist']], name='Histograma'), row=2, col=1)
        st.plotly_chart(criar_layout_premium(fig, 800), use_container_width=True, config={'displayModeBar': False})

    elif pagina_atual == "🤖 4. Radar Automático":
        st.title("🤖 Radar de Oportunidades")
        dados_screener = []
        for nome, tick in lista_moedas.items():
            df_temp = processar_dados(tick, periodo, timeframe)
            if df_temp is not None:
                p = float(df_temp['Close'].iloc[-1])
                e9, e21 = float(df_temp['EMA_9'].iloc[-1]), float(df_temp['EMA_21'].iloc[-1])
                status_q = "🟢 ALTA" if e9 > e21 else "🔴 BAIXA"
                status_b = "🔥 COMPRA" if bool(df_temp['Backes_Compra'].iloc[-1]) else ("🚨 VENDA" if bool(df_temp['Backes_Venda'].iloc[-1]) else "Aguardando")
                status_s = "💎 COMPRA" if bool(df_temp['Sniper_Compra'].iloc[-1]) else ("💥 VENDA" if bool(df_temp['Sniper_Venda'].iloc[-1]) else "Aguardando MACD")
                dados_screener.append({"Ativo": nome, "Preço": f"${p:.4f}", "Direção": status_q, "Backes": status_b, "Sniper": status_s})
        st.dataframe(pd.DataFrame(dados_screener), use_container_width=True, height=400)

    elif pagina_atual == "🔥 5. Alpha VIP / Sinais":
        st.markdown(f"<h1>🔥 Relatório Alpha Premium <span class='badge-vip'>VIP ONLY</span></h1>", unsafe_allow_html=True)
        direcao = "LONG 🟢" if float(ult['EMA_9']) > float(ult['EMA_21']) else "SHORT 🔴"
        cor_dir = "#10b981" if direcao == "LONG 🟢" else "#ef4444"
        
        if direcao == "LONG 🟢":
            entry_zone = f"${preco_atual * 0.995:,.4f} - ${preco_atual * 1.005:,.4f}"
            tp1, tp2, tp3 = preco_atual + (1.5 * atr_atual), preco_atual + (3.0 * atr_atual), preco_atual + (5.0 * atr_atual)
            sl_vip = preco_atual - (2.0 * atr_atual)
        else:
            entry_zone = f"${preco_atual * 0.995:,.4f} - ${preco_atual * 1.005:,.4f}"
            tp1, tp2, tp3 = preco_atual - (1.5 * atr_atual), preco_atual - (3.0 * atr_atual), preco_atual - (5.0 * atr_atual)
            sl_vip = preco_atual + (2.0 * atr_atual)

        razoes = []
        if float(ult['Close']) > float(ult['EMA_200']): razoes.append("Preço acima da EMA 200 (Macro Forte).")
        else: razoes.append("Preço perdendo a EMA 200 (Fraqueza Estrutural).")
        if float(ult['MACD_Hist']) > 0: razoes.append("Momentum positivo no Histograma MACD.")
        elif float(ult['MACD_Hist']) < 0: razoes.append("Momentum vendedor dominando no MACD.")
        razao_str = "<br>".join([f"✔️ {r}" for r in razoes])

        st.markdown(f"""
<div class="vip-card" style="border-left: 5px solid {cor_dir};">
<h2 style="margin-top: 0;">Análise Técnica: {ativo_selecionado}</h2>
<h3 style="color: {cor_dir};">DIREÇÃO RECOMENDADA: {direcao}</h3>
<hr style="border-color: #334155;">
<div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
<div style="flex: 1; min-width: 200px;">
<p>📍 <b>Entry Zone:</b> <span style="color: #38bdf8;">{entry_zone}</span></p>
<p>🛑 <b>Stop Loss:</b> <span style="color: #ef4444; font-weight: bold;">${sl_vip:,.4f}</span></p>
</div>
<div style="flex: 1; min-width: 200px;">
<p>🎯 <b>TP1:</b> <span style="color: #10b981;">${tp1:,.4f}</span></p>
<p>🎯 <b>TP2:</b> <span style="color: #10b981;">${tp2:,.4f}</span></p>
<p>🎯 <b>TP3:</b> <span style="color: #10b981;">${tp3:,.4f}</span></p>
</div>
</div>
<hr style="border-color: #334155;">
<h4 style="color: #a78bfa;">🧠 Razão Técnica</h4>
<p style="color: #cbd5e1; font-size: 15px;">{razao_str}</p>
</div>
""", unsafe_allow_html=True)

    elif pagina_atual == "🌍 6. Macro & Geopolítica":
        st.markdown(f"<h1>🌍 Daily Market Analysis & Geopolítica</h1>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown("""
<div class="macro-card">
<h3 style="color: #0ea5e9; margin-top: 0;">🌐 Análise Macro</h3>
<p style="color: #cbd5e1; font-size: 15px;">O mercado cripto encontra-se altamente correlacionado com os recentes choques de oferta globais.</p>
<ul style="color: #cbd5e1; font-size: 15px;"><li>🛢️ <b>Petróleo:</b> Brent pivotando. Resistência crítica em US$ 115.</li><li>🏦 <b>FED:</b> Discursos hawkish travando liquidez.</li></ul>
</div>
""", unsafe_allow_html=True)
        with c2:
            st.markdown("""
<div class="macro-card">
<h3 style="color: #0ea5e9; margin-top: 0;">🎯 Early Narratives</h3>
<ul style="color: #cbd5e1; font-size: 15px;"><li>🛡️ <b>DeFi & Stablecoins:</b> <span style="color: #10b981;">Fluxo Forte Ingressando</span></li><li>🤖 <b>AI (Inteligência Artificial):</b> Mantém força relativa.</li></ul>
</div>
""", unsafe_allow_html=True)

    # =====================================================================
    # PÁGINA 7: FIBONACCI E CONFLUÊNCIA COM CÓDIGO HTML BLINDADO (FLUSH LEFT)
    # =====================================================================
    elif pagina_atual == "📐 7. Análise Fibonacci (Confluência)":
        st.markdown(f"<h1>📐 Análise Fibonacci & Setup Institucional</h1>", unsafe_allow_html=True)
        
        swing_high, swing_low = df['High'].max(), df['Low'].min()
        diff = swing_high - swing_low
        
        fib_0, fib_236, fib_382, fib_500, fib_618, fib_786, fib_100 = swing_high, swing_high - 0.236*diff, swing_high - 0.382*diff, swing_high - 0.500*diff, swing_high - 0.618*diff, swing_high - 0.786*diff, swing_low
        fib_ext_127, fib_ext_161, fib_ext_261 = swing_high + 0.272 * diff, swing_high + 0.618 * diff, swing_high + 1.618 * diff

        tabelas_vip_html = f"""
<div style="display: flex; gap: 20px; flex-wrap: wrap;">
<div style="flex: 1; min-width: 300px;">
<div class="vip-card" style="padding: 15px; height: 100%;">
<h4 style="color: #38bdf8; margin-top: 0;">📉 Fibonacci Retracement (Suportes no Pullback)</h4>
<table style="width: 100%; border-collapse: collapse; color: #cbd5e1; font-size: 13px;">
<tr style="border-bottom: 1px solid #334155; color: #94a3b8; text-align: left;">
<th style="padding: 8px;">Nível Fib</th><th style="padding: 8px;">Preço Aprox.</th><th style="padding: 8px;">Interpretação Profissional</th><th style="padding: 8px;">Força</th>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #ef4444;"><b>0% (Topo)</b></td><td style="padding: 8px;">${fib_0:,.4f}</td><td style="padding: 8px;">Resistência imediata / alvo de realização</td><td style="padding: 8px;">—</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #f87171;"><b>23.6%</b></td><td style="padding: 8px;">${fib_236:,.4f}</td><td style="padding: 8px;">Zona de teste imediata</td><td style="padding: 8px; color: #f59e0b;">Média</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #a3e635;"><b>38.2%</b></td><td style="padding: 8px;">${fib_382:,.4f}</td><td style="padding: 8px;">Primeiro suporte forte – deve segurar</td><td style="padding: 8px; color: #10b981;">Alta</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b; background-color: rgba(255,255,255,0.05);">
<td style="padding: 8px; color: #38bdf8;"><b>50.0%</b></td><td style="padding: 8px;">${fib_500:,.4f}</td><td style="padding: 8px;">Suporte psicológico – <b>Início da Acumulação</b></td><td style="padding: 8px; color: #10b981;">Alta</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b; background-color: rgba(245, 158, 11, 0.1);">
<td style="padding: 8px; color: {GOLDEN_POCKET};"><b>61.8%</b></td><td style="padding: 8px;">${fib_618:,.4f}</td><td style="padding: 8px;">Golden Pocket – zona de compra ideal</td><td style="padding: 8px; color: #10b981;"><b>Muito Alta</b></td>
</tr>
<tr>
<td style="padding: 8px; color: #c084fc;"><b>78.6%</b></td><td style="padding: 8px;">${fib_786:,.4f}</td><td style="padding: 8px;">Suporte profundo – último antes de reverter</td><td style="padding: 8px; color: #f59e0b;">Média</td>
</tr>
</table>
<p style="font-size: 13px; color: #94a3b8; margin-top: 15px;"><b>Interpretação Atual:</b> Se segurar acima de 38.2% (${fib_382:,.4f}), o movimento altista continua forte. Uma perda limpa de 38.2% abre caminho para o Golden Pocket (${fib_618:,.4f}–${fib_500:,.4f}) – região excelente para entrada longa.</p>
</div>
</div>
<div style="flex: 1; min-width: 300px;">
<div class="vip-card" style="padding: 15px; height: 100%;">
<h4 style="color: #a3e635; margin-top: 0;">🚀 Fibonacci Extension (Alvos de Take-Profit)</h4>
<table style="width: 100%; border-collapse: collapse; color: #cbd5e1; font-size: 13px;">
<tr style="border-bottom: 1px solid #334155; color: #94a3b8; text-align: left;">
<th style="padding: 8px;">Nível Fib</th><th style="padding: 8px;">Preço Alvo</th><th style="padding: 8px;">Interpretação (Alvos de Alta)</th>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #ef4444;"><b>100% (High)</b></td><td style="padding: 8px;">${fib_0:,.4f}</td><td style="padding: 8px;">Breakout (rompimento) confirmado</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #10b981;"><b>127.2%</b></td><td style="padding: 8px;">${fib_ext_127:,.4f}</td><td style="padding: 8px;">Primeiro alvo realista pós-rompimento</td>
</tr>
<tr style="border-bottom: 1px solid #1e293b;">
<td style="padding: 8px; color: #10b981;"><b>161.8%</b></td><td style="padding: 8px;">${fib_ext_161:,.4f}</td><td style="padding: 8px;">Alvo médio – forte extensão de tendência</td>
</tr>
<tr>
<td style="padding: 8px; color: #10b981;"><b>261.8%</b></td><td style="padding: 8px;">${fib_ext_261:,.4f}</td><td style="padding: 8px;">Extensão máxima / Rally histórico</td>
</tr>
</table>
<h4 style="color: #f59e0b; margin-top: 20px; border-top: 1px solid #334155; padding-top: 15px;">⚡ Resumo Estratégico (Institucional)</h4>
<ul style="font-size: 13px; color: #cbd5e1; padding-left: 20px; line-height: 1.8;">
<li><b style="color:#10b981;">Cenário Bullish:</b> Hold acima de ${fib_382:,.4f} → mira ${fib_ext_127:,.4f} e depois ${fib_ext_161:,.4f}.</li>
<li><b style="color:#38bdf8;">Zona de Compra Segura:</b> ${fib_618:,.4f} – ${fib_500:,.4f} (Faixa Cinza no Gráfico).</li>
<li><b style="color:#ef4444;">Stop Loss Sugerido:</b> Abaixo de ${fib_786:,.4f} ou ${fib_100:,.4f} (invalidação total).</li>
</ul>
</div>
</div>
</div>
"""
        st.markdown(tabelas_vip_html, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.markdown(f"""
<div class="metric-card" style="text-align: center; border-left: 4px solid {GOLDEN_POCKET}; height: 100%;">
<h4 style="color: #94a3b8; margin:0;">ZONA GOLDEN POCKET</h4>
<h3 style="color: {GOLDEN_POCKET}; margin:5px 0;">${fib_618:,.4f}</h3>
<p style="font-size:13px; color:#cbd5e1; margin-top: 15px;">A Proporção Áurea (61.8%). A base principal da <b>Zona Cinza de Acumulação</b> no gráfico.</p>
</div>
""", unsafe_allow_html=True)

        with c2:
            rsi_val, macd_hist = float(ult['RSI']), float(ult['MACD_Hist'])
            rsi_stat = f"<span style='color:#10b981;'>Saindo de Oversold ({rsi_val:.1f}) - Divergência Bullish Forte</span>" if rsi_val < 45 else (f"<span style='color:#ef4444;'>Overbought ({rsi_val:.1f})</span>" if rsi_val > 65 else f"<span style='color:#8b949e;'>Neutro ({rsi_val:.1f})</span>")
            macd_stat = "<span style='color:#10b981;'>Bullish Crossover no Histograma. Momentum altista.</span>" if macd_hist > 0 else "<span style='color:#ef4444;'>Histograma Negativo. Momentum vendedor.</span>"
            ema50 = float(ult['EMA_50'])
            ema_stat = f"<span style='color:#10b981;'>Testando EMA 50 + Fib. <b>Confluência Poderosa</b></span>" if abs(preco_atual - ema50)/preco_atual < 0.02 else ("<span style='color:#38bdf8;'>Preço sustentando acima da EMA 50.</span>" if preco_atual > ema50 else "<span style='color:#ef4444;'>Abaixo da EMA 50 (Resistência).</span>")
            vol_stat = "<span style='color:#10b981;'>Alto Volume acima da VWAP. Compra Institucional confirmada.</span>" if float(ult['Volume']) > (float(ult['Volume_SMA']) * 1.5) and preco_atual > float(ult['VWAP']) else "<span style='color:#8b949e;'>Volume mediano na zona.</span>"
            pa_stat = "<span style='color:#10b981;'>🔥 Bullish Engulfing/Hammer detectado!</span>" if bool(ult['Engolfo_C']) or bool(ult['Martelo_C']) else "<span style='color:#8b949e;'>Nenhum padrão de reversão claro neste candle.</span>"

            st.markdown(f"""
<div class="fib-card" style="height: 100%;">
<h3 style="margin-top:0; color: #e6edf3;">Muralha de Confluência (Cruzamento de Indicadores)</h3>
<ul style="color: #cbd5e1; font-size: 14px; line-height: 1.8;">
<li><b>1ª - RSI:</b> {rsi_stat}</li><li><b>2ª - MACD:</b> {macd_stat}</li><li><b>3ª - EMAs 50/200:</b> {ema_stat}</li><li><b>4ª - Volume/VWAP:</b> {vol_stat}</li><li><b>5ª - Price Action:</b> {pa_stat}</li>
</ul>
</div>
""", unsafe_allow_html=True)

        st.subheader("Gráfico de Retração Institucional")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço', increasing_line_color='#089981', decreasing_line_color='#f23645', increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#8b5cf6', width=2), name='EMA 50'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#ffffff', width=2), name='EMA 200'), row=1, col=1)

        # Linhas de Fibonacci no Gráfico
        fib_colors = {fib_0: '#ef4444', fib_236: '#f87171', fib_382: '#a3e635', fib_500: '#38bdf8', fib_618: GOLDEN_POCKET, fib_786: '#c084fc', fib_100: '#059669'}
        fib_names = {fib_0: '0%', fib_236: '23.6%', fib_382: '38.2%', fib_500: '50%', fib_618: '61.8% (GP)', fib_786: '78.6%', fib_100: '100%'}
        for level, color in fib_colors.items():
            fig.add_hline(y=level, line_dash="dash", line_color=color, line_width=1, annotation_text=f"{fib_names[level]}", annotation_position="top left", annotation_font_color=color, row=1, col=1)
            
        # ZONA DE ACUMULAÇÃO EM CINZA
        fig.add_hrect(y0=fib_500, y1=fib_618, fillcolor="lightgray", opacity=0.15, line_width=0, annotation_text="ZONA DE ACUMULAÇÃO", annotation_position="inside top left", annotation_font_color="white", row=1, col=1)

        # Extensões (Take Profits) no gráfico
        fig.add_hline(y=fib_ext_127, line_dash="dot", line_color="#10b981", line_width=1, annotation_text="Alvo 127.2%", annotation_position="top left", annotation_font_color="#10b981", row=1, col=1)
        fig.add_hline(y=fib_ext_161, line_dash="dot", line_color="#10b981", line_width=1, annotation_text="Alvo 161.8%", annotation_position="top left", annotation_font_color="#10b981", row=1, col=1)

        # RSI no rodapé
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#c084fc', width=2), name='RSI'), row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#10b981", row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=2, col=1)
        
        st.plotly_chart(criar_layout_premium(fig, 850), use_container_width=True, config={'displayModeBar': False})

else:
    st.error("Erro ao puxar dados. Verifique sua conexão.")