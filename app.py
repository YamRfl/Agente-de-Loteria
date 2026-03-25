import streamlit as st
import pandas as pd
import time
import hashlib
import plotly.express as px
import io  

from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco, limpar_apostas_banco
from src.collector import atualizar_resultados
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas

def gerar_hash_sha256(dados_bytes):
    return hashlib.sha256(dados_bytes).hexdigest()

# --- FUNÇÕES DE CACHE PARA ALTA PERFORMANCE ---
@st.cache_data(show_spinner=False)
def carregar_estatisticas_cacheadas(loteria):
    return obter_estatisticas_completas(loteria)

@st.cache_data(show_spinner=False)
def carregar_historico_cacheados(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT id_concurso as Concurso, data_sorteio as Data, dezenas as Números FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC", conn, params=(loteria,))
    conn.close()
    return df

@st.cache_data(show_spinner=False)
def carregar_apostas_cacheadas(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT concurso_alvo as Concurso, dezenas_jogadas as 'Suas Dezenas' FROM apostas_usuario WHERE loteria = ? ORDER BY id DESC", conn, params=(loteria,))
    conn.close()
    return df

st.set_page_config(page_title="Agente IA Loterias", layout="wide", page_icon="🍀")
inicializar_bd()

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("🍀 Agente de IA - Analista de Loterias")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Controle")
    loteria = st.selectbox(
        "Loteria:", 
        ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania"],
        help="Selecione a loteria que pretende analisar ou para a qual deseja gerar apostas."
    )
    
    st.divider()
    with st.expander("💰 Ajustar Preços e Limites"):
        conn = obter_conexao()
        dados_t = conn.execute("SELECT preco_base, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
        conn.close()
        
        if dados_t:
            novo_preco = st.number_input(
                "Preço Aposta Simples:", 
                value=float(dados_t[0]), step=0.50,
                help="Defina o valor atual cobrado pela aposta mínima."
            )
            nova_dez_max = st.number_input(
                "Limite de Dezenas:", 
                value=int(dados_t[1]), step=1,
                help="Número máximo de dezenas permitidas num único bilhete."
            )
            
            if st.button("Salvar Tarifas", use_container_width=True, help="Grava as novas configurações de preço no sistema."):
                atualizar_preco_banco(loteria, novo_preco, nova_dez_max)
                st.cache_data.clear() 
                st.toast("Tarifas atualizadas com segurança! ✅", icon="✅")
                time.sleep(1)
                st.rerun()

    st.divider()
    
    st.markdown(
        '<p style="text-align: justify; font-size: 0.85em; color: gray;">'
        '⚠️ <b>Aviso:</b> Se interromper uma atualização em curso, o ecrã poderá ficar em branco. '
        'Basta recarregar a página (F5) para voltar ao normal.</p>', 
        unsafe_allow_html=True
    )
    
    prog_place = st.empty()
    if st.button("🔄 Atualizar Resultados", use_container_width=True, type="primary", help="Descarrega os últimos resultados oficiais da API da Caixa."):
        barra = prog_place.progress(0, text="A sincronizar...")
        atualizar_resultados(loteria, barra_progresso=barra)
        st.cache_data.clear() 
        prog_place.empty()
        st.toast("Resultados sincronizados com sucesso! 🔄", icon="🔄")
        time.sleep(1)
        st.rerun()
        
    st.info(f"Último Concurso: **{obter_ultimo_concurso_db(loteria)}**")

# --- DEFINIÇÃO DOS 4 SEPARADORES (ABAS) ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Gerador", "📊 Histórico", "🏆 Conferência", "📈 Estatísticas"])

# SEPARADOR 1: GERADOR & CARRINHO 
with tab1:
    conn = obter_conexao()
    lim = conn.execute("SELECT dez_min, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
    conn.close()
    m_min, m_max = (lim[0], lim[1]) if lim else (6, 20)
    
    c1, c2 = st.columns(2)
    with c1: 
        qtd_j = st.number_input("Qtd. Jogos:", 1, 100, 1, help="Quantidade de jogos distintos que deseja gerar.")
    with c2: 
        qtd_d = st.number_input(f"Dezenas ({m_min}-{m_max}):", m_min, m_max, m_min, help="Quantidade de números a marcar em cada jogo.")
    
    # --- PAINEL DE FILTROS MANUAIS COM TOOLTIPS DE ACESSIBILIDADE ---
    with st.expander("🛠️ Filtros Matemáticos Manuais (Avançado)"):
        st.caption("⚠️ Atenção: Combinar muitos filtros rígidos em simultâneo forçará o sistema a ignorar regras para evitar bloqueios. Deixe os limites abertos naquilo que não deseja filtrar.")
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            limite_soma = st.slider("Soma das Dezenas", 0, 800, (0, 800), 1, help="Filtra jogos cuja soma de todos os números esteja neste intervalo.")
            limite_fibo = st.slider("Qtd. Fibonacci", 0, m_max, (0, m_max), 1, help="Define quantos números da sequência de Fibonacci (1, 2, 3, 5, 8, 13...) o jogo deve conter.")
            limite_repetidas = st.slider("Repetidas (Últ. Sorteio)", 0, m_max, (0, m_max), 1, help="Quantidade de números que se devem repetir em relação ao concurso imediatamente anterior.")
        with cf2:
            limite_pares = st.slider("Qtd. de Pares", 0, m_max, (0, m_max), 1, help="Intervalo aceitável de números pares no jogo.")
            limite_mult3 = st.slider("Qtd. Múltiplos de 3", 0, m_max, (0, m_max), 1, help="Intervalo de números divisíveis por 3 no jogo.")
            max_linha = st.number_input("Máx. dezenas por Linha", 1, 10, 10, help="Evita jogos com demasiados números concentrados na mesma linha horizontal do bilhete.")
        with cf3:
            limite_primos = st.slider("Qtd. de Primos", 0, m_max, (0, m_max), 1, help="Intervalo aceitável de números primos (2, 3, 5, 7, 11...) no jogo.")
            limite_moldura = st.slider("Qtd. na Moldura", 0, m_max, (0, m_max), 1, help="Números localizados na borda externa do bilhete (a moldura).")
            max_coluna = st.number_input("Máx. dezenas por Coluna", 1, 10, 10, help="Evita a concentração excessiva de números na mesma coluna vertical.")
    
    usar_ia = st.toggle("🧠 Ativar Filtro de Inteligência Artificial (K-Means)", value=False, help="Treina um modelo na hora para sugerir jogos com o mesmo perfil matemático dos sorteios mais frequentes do passado.")
    
    if st.button("➕ Gerar e Adicionar ao Carrinho", use_container_width=True, type="primary", help="Cria as apostas aplicando todas as regras e filtros configurados acima."):
        jogos = sugerir_jogo(
            loteria, qtd_j, qtd_d, 
            usar_ia=usar_ia,
            filtro_soma=limite_soma,
            filtro_pares=limite_pares,
            filtro_primos=limite_primos,
            filtro_fibo=limite_fibo,
            filtro_mult3=limite_mult3,
            filtro_moldura=limite_moldura,
            filtro_repetidas=limite_repetidas,
            limite_linha=max_linha,
            limite_coluna=max_coluna
        )
        
        custo_uni = calcular_custo_jogos(loteria, qtd_j, qtd_d) / qtd_j
        for j in jogos:
            st.session_state.carrinho.append({
                "Loteria": loteria.upper(), 
                "Dezenas": ", ".join(map(str, sorted(j))), 
                "Custo Unitário": custo_uni,
                "IA": "🤖 Sim" if usar_ia else "Aleatório"
            })
        st.toast("Jogos gerados e adicionados ao carrinho! 🛒", icon="🛒")
        st.rerun()

    if st.session_state.carrinho:
        st.divider()
        df_c = pd.DataFrame(st.session_state.carrinho)
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            st.metric("Total", f"R$ {df_c['Custo Unitário'].sum():.2f}")
        with col_c2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_c.to_excel(writer, index=False, sheet_name='Meus Jogos')
            excel_dados = buffer.getvalue()
            
            st.download_button(
                label="📥 Descarregar Lista (Excel)", 
                data=excel_dados, 
                file_name="meus_jogos.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True,
                help="Guarda a sua lista de apostas num ficheiro Excel seguro e assinado digitalmente."
            )
            
            if st.button("🗑️ Limpar Carrinho", use_container_width=True, help="Remove todos os jogos não guardados da lista atual."):
                st.session_state.carrinho = []
                st.toast("Carrinho esvaziado! 🧹", icon="🧹")
                st.rerun()
                
        if st.button("💾 CONFIRMAR E GUARDAR NO BANCO", use_container_width=True, help="Regista permanentemente as apostas no sistema para conferência futura."):
            conn = obter_conexao(); prox = obter_ultimo_concurso_db(loteria) + 1
            for _, r in df_c.iterrows():
                conn.execute("INSERT INTO apostas_usuario (loteria, concurso_alvo, dezenas_jogadas) VALUES (?,?,?)", (r["Loteria"].lower(), prox, r["Dezenas"].replace(" ", "")))
            conn.commit(); conn.close()
            st.cache_data.clear() 
            st.session_state.carrinho = []
            st.toast("Apostas guardadas com segurança! 💾", icon="💾")
            time.sleep(1)
            st.rerun()

# SEPARADOR 2: HISTÓRICO
with tab2:
    df_h = carregar_historico_cacheados(loteria)
    if not df_h.empty: st.dataframe(df_h, use_container_width=True, hide_index=True)

# SEPARADOR 3: CONFERÊNCIA 
with tab3:
    df_p = carregar_apostas_cacheadas(loteria)
    
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        
        c_conf1, c_conf2 = st.columns(2)
        with c_conf1:
            if st.button("🔍 Conferir Acertos", use_container_width=True, type="primary", help="Verifica se os seus jogos guardados ganharam algum prémio no último concurso."):
                res = conferir_resultados(loteria)
                if res is not None and not res.empty: 
                    st.table(res)
                    # Celebração Visual (Gamificação)
                    st.balloons()
                elif res is not None:
                    st.table(res)
                
        with c_conf2:
            if st.button("🗑️ Apagar Histórico de Jogos", use_container_width=True, help="Apaga permanentemente as suas apostas antigas do sistema."):
                limpar_apostas_banco(loteria)
                st.cache_data.clear() 
                st.toast("Histórico de jogos apagado com sucesso! 🗑️", icon="🗑️")
                time.sleep(1)
                st.rerun()
    else:
        st.info("Ainda não tem jogos guardados para esta loteria. Vá até ao separador 'Gerador' para adicionar e guardar apostas!")

# SEPARADOR 4: ESTATÍSTICAS COM CORES ACESSÍVEIS (DALTONISMO)
with tab4:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_freq, df_atraso = carregar_estatisticas_cacheadas(loteria)
    
    if df_freq is not None:
        modo_visao = st.radio(
            "Modo de Exibição:", 
            ["📊 Gráficos Interativos (Top 20)", "📝 Tabelas Completas"], 
            horizontal=True,
            label_visibility="collapsed",
            help="Alterne entre a visualização gráfica resumida e a grelha de dados completa."
        )
        
        st.divider()
        c1, c2 = st.columns(2)
        
        if "Gráficos" in modo_visao:
            top_freq = df_freq.head(20).copy()
            top_atraso = df_atraso.head(20).copy()
            top_freq['Número'] = top_freq['Número'].astype(str)
            top_atraso['Número'] = top_atraso['Número'].astype(str)

            with c1:
                st.subheader("🔥 Top 20 - Mais Sorteados")
                # Mudança de escala de cor para Blues (Maior Contraste)
                fig_freq = px.bar(
                    top_freq, x='Número', y='Sorteios', 
                    text='Sorteios', color='Sorteios', 
                    color_continuous_scale='Blues'
                )
                fig_freq.update_layout(xaxis_type='category', showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                fig_freq.update_traces(textposition='outside')
                st.plotly_chart(fig_freq, use_container_width=True)

            with c2:
                st.subheader("⏳ Top 20 - Maiores Atrasos")
                # Mudança de escala de cor para Oranges (Contraste complementar ao Azul)
                fig_atraso = px.bar(
                    top_atraso, x='Número', y='Atraso', 
                    text='Atraso', color='Atraso', 
                    color_continuous_scale='Oranges'
                )
                fig_atraso.update_layout(xaxis_type='category', showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                fig_atraso.update_traces(textposition='outside')
                st.plotly_chart(fig_atraso, use_container_width=True)
                
        else:
            with c1:
                st.subheader("🔥 Frequência Completa")
                # Atualização do CSS das tabelas para tons de azul e laranja acessíveis
                st.dataframe(df_freq.style.format(precision=2).bar(subset=['Sorteios'], color='#1f77b4'), use_container_width=True, hide_index=True)

            with c2:
                st.subheader("⏳ Atrasos Completos")
                st.dataframe(df_atraso.style.format(precision=2).background_gradient(subset=['Atraso'], cmap='Oranges'), use_container_width=True, hide_index=True)

    else:
        st.warning("Atualize os resultados na barra lateral para gerar os gráficos estatísticos.")