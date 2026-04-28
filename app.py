import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
import time
import plotly.express as px
import io  

from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco, limpar_apostas_banco
from src.collector import atualizar_resultados, sincronizar_todas_loterias
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas
from src.auth import (inicializar_bd_auth, registrar_usuario, autenticar_usuario, 
                      simular_pagamento_e_liberar_licenca, listar_todos_usuarios,
                      alterar_senha_usuario, solicitar_token_recuperacao, redefinir_senha_com_token,
                      resetar_senha_por_admin)

st.set_page_config(page_title="Agente IA Loterias - SaaS", layout="wide", page_icon="🍀")

# ==========================================
# INJEÇÃO ESTÉTICA (CSS) - REDUÇÃO DE ESPAÇOS
# ==========================================
st.markdown("""
<style>
    /* Reduz o topo da barra lateral */
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Encolhe os botões globalmente */
    .stButton>button {
        min-height: 2rem;
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }
    /* Reduz o espaçamento do divisor (hr) em 30% */
    [data-testid="stSidebar"] hr {
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }
    /* Garante barra de rolagem visual caso a tela seja muito pequena */
    [data-testid="stSidebar"] > div:first-child {
        overflow-y: auto !important;
    }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {
        width: 6px;
        background-color: transparent;
    }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {
        background-color: rgba(120, 120, 120, 0.4);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

inicializar_bd()
inicializar_bd_auth()

if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

@st.cache_data(show_spinner=False)
def carregar_estatisticas_cacheadas(loteria): return obter_estatisticas_completas(loteria)

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

# ==========================================
# CABEÇALHO COM BOTÃO "SAIR" NO CANTO SUPERIOR DIREITO
# ==========================================
col_titulo, col_sair = st.columns([8, 2])
with col_titulo:
    st.title("🍀 Agente de IA - Analista de Loterias")
with col_sair:
    if st.session_state.logged_in:
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair da Conta", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

with st.sidebar:
    # ==========================================
    # 1. CONTROLE GLOBAL (Topo)
    # ==========================================
    st.subheader("⚙️ Seleção de Loteria")
    loteria = st.selectbox("Modalidade", ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania", "maismilionaria", "diadesorte"], label_visibility="collapsed", help="Escolha a loteria.")
    
    prog_place = st.empty()
    status_text = st.empty()
    
    col_sync1, col_sync2 = st.columns(2)
    with col_sync1:
        if st.button("🔄 Atual", type="primary", use_container_width=True, help="Sincroniza apenas a loteria selecionada na caixa acima."):
            try:
                atualizar_resultados(loteria, barra_progresso=prog_place.progress(0))
                st.cache_data.clear(); prog_place.empty()
                st.toast(f"Resultados da {loteria.upper()} atualizados!", icon="✅")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("Conexão interrompida.")
                
    with col_sync2:
        if st.button("⚡ TODAS", type="secondary", use_container_width=True, help="Baixa todas as 8 loterias em Lote."):
            try:
                sincronizar_todas_loterias(barra_progresso=prog_place.progress(0), texto_status=status_text)
                st.cache_data.clear(); prog_place.empty(); status_text.empty()
                st.toast("Banco de dados sincronizado!", icon="🚀")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("Conexão interrompida.")
            
    st.caption(f"Último Concurso Sincronizado: **{obter_ultimo_concurso_db(loteria)}**")
    
    st.divider()

    # ==========================================
    # 2. ÁREA DO USUÁRIO (Base)
    # ==========================================
    st.subheader("🔐 Área do Usuário")
    
    if not st.session_state.logged_in:
        tab_log, tab_cad, tab_rec = st.tabs(["Entrar", "Criar Conta", "Recuperar"])
        
        with tab_log:
            with st.form("form_login"):
                log_email = st.text_input("E-mail", placeholder="E-mail de acesso", label_visibility="collapsed")
                log_senha = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")
                submit_log = st.form_submit_button("Acessar Plataforma", type="primary", use_container_width=True)
                if submit_log:
                    sucesso, resposta = autenticar_usuario(log_email, log_senha)
                    if sucesso:
                        st.session_state.logged_in = True
                        st.session_state.user = resposta
                        st.rerun()
                    else: 
                        st.error(resposta)
                    
        with tab_cad:
            with st.form("form_cadastro", clear_on_submit=True):
                cad_nome = st.text_input("Nome Completo", placeholder="Nome Completo", label_visibility="collapsed")
                cad_email = st.text_input("E-mail", placeholder="E-mail (ex: nome@dominio.com)", label_visibility="collapsed")
                cad_senha = st.text_input("Senha", type="password", placeholder="Senha Forte (Mín. 8 chars)", label_visibility="collapsed")
                submit_cad = st.form_submit_button("Cadastrar Conta", use_container_width=True)
                if submit_cad:
                    sucesso, msg = registrar_usuario(cad_nome, cad_email, cad_senha)
                    if sucesso:
                        st.success(msg)
                    else:
                        st.error(msg)
                    
        with tab_rec:
            with st.form("form_pedir_token"):
                st.caption("1º Passo: Solicite o código")
                req_email = st.text_input("E-mail", placeholder="Digite seu e-mail", label_visibility="collapsed")
                submit_req = st.form_submit_button("✉️ Receber Código", use_container_width=True)
                if submit_req:
                    with st.spinner("Enviando..."):
                        suc_req, msg_req = solicitar_token_recuperacao(req_email)
                        if suc_req:
                            st.success(msg_req)
                        else:
                            st.error(msg_req)
            
            with st.form("form_redefinir_senha", clear_on_submit=True):
                st.caption("2º Passo: Digite o código e a senha")
                rec_email = st.text_input("Confirmar E-mail", placeholder="Confirme seu e-mail", label_visibility="collapsed")
                rec_token = st.text_input("Código", placeholder="Código de 6 dígitos", label_visibility="collapsed")
                rec_senha = st.text_input("Nova Senha", type="password", placeholder="Nova Senha Forte", label_visibility="collapsed")
                submit_rec = st.form_submit_button("Salvar Nova Senha", type="primary", use_container_width=True)
                if submit_rec:
                    suc_rec, msg_rec = redefinir_senha_com_token(rec_email, rec_token, rec_senha)
                    if suc_rec:
                        st.success(msg_rec)
                    else:
                        st.error(msg_rec)
    else:
        st.success(f"Olá, {st.session_state.user['nome'].split()[0]}!")
        is_premium = st.session_state.user.get('licenca') is not None
        
        if is_premium:
            st.info("💎 Status: **Assinante VIP**")
        else:
            st.warning("Plano: **Gratuito**")
            if st.button("💳 Simular Pagamento", type="primary", use_container_width=True):
                with st.spinner("Processando..."):
                    time.sleep(2)
                    st.session_state.user['licenca'] = simular_pagamento_e_liberar_licenca(st.session_state.user['email'])
                st.balloons()
                st.rerun()
                
        # Bloqueia configurações se houver pendência de troca
        if not st.session_state.user.get('trocar_senha'):
            with st.expander("👤 Configurações da Conta"):
                with st.form("form_alt_senha", clear_on_submit=True):
                    alt_senha_antiga = st.text_input("Senha Atual", type="password", placeholder="Senha atual", label_visibility="collapsed")
                    alt_senha_nova = st.text_input("Nova Senha", type="password", placeholder="Nova senha forte", label_visibility="collapsed")
                    submit_alt = st.form_submit_button("Atualizar Senha", use_container_width=True)
                    if submit_alt:
                        suc, msg_alt = alterar_senha_usuario(st.session_state.user['email'], alt_senha_antiga, alt_senha_nova)
                        if suc:
                            st.success(msg_alt)
                        else:
                            st.error(msg_alt)

        if st.button("Sair (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    with st.expander("♿ Acessibilidade e Ajuda"):
        st.markdown("""
        * **Contraste:** O sistema se adapta ao tema do Windows.
        * **Dicas:** Passe o mouse sobre os ícones `?`.
        * **Zoom:** Utilize `Ctrl +` ou `Ctrl -` no teclado.
        """)

# --- FIREWALL: TROCA DE SENHA OBRIGATÓRIA ---
if st.session_state.logged_in and st.session_state.user.get('trocar_senha'):
    st.warning("🛡️ **Segurança Crítica:** Sua senha foi resetada. Por favor, defina uma nova senha pessoal para continuar.")
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("f_troca_obrigatoria"):
            s_temp = st.text_input("Senha Temporária Recebida", type="password")
            s_nova = st.text_input("Nova Senha Forte", type="password")
            s_conf = st.text_input("Confirme a Nova Senha", type="password")
            if st.form_submit_button("Atualizar e Acessar Sistema", type="primary", use_container_width=True):
                if s_nova != s_conf: st.error("As senhas não coincidem.")
                else:
                    sucesso, msg = alterar_senha_usuario(st.session_state.user['email'], s_temp, s_nova)
                    if sucesso:
                        st.success("Senha protegida com sucesso!"); st.session_state.user['trocar_senha'] = 0
                        time.sleep(1.5); st.rerun()
                    else: st.error(msg)
    st.stop()

# ==========================================
# ABAS PRINCIPAIS DO SISTEMA
# ==========================================
tabs_names = ["🎯 Gerador (Free/VIP)", "📊 Histórico", "🏆 Conferência", "📈 Estatísticas"]
is_admin = st.session_state.logged_in and st.session_state.user['role'] == 'admin'
if is_admin: tabs_names.append("🛡️ Painel Admin")

tabs = st.tabs(tabs_names)

with tabs[0]:
    conn = obter_conexao()
    lim = conn.execute("SELECT dez_min, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
    conn.close()
    m_min, m_max = (lim[0], lim[1]) if lim else (6, 20)
    
    c1, c2 = st.columns(2)
    with c1: qtd_j = st.number_input("Qtd. Jogos:", 1, 100, 1, help="Número de bilhetes a serem gerados.")
    with c2: qtd_d = st.number_input(f"Dezenas ({m_min}-{m_max}):", m_min, m_max, m_min, help="Quantidade de números marcados em cada bilhete.")
    
    usuario_premium = st.session_state.logged_in and st.session_state.user.get('licenca') is not None
    
    if usuario_premium:
        with st.expander("🛠️ Filtros Matemáticos e IA"):
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                limite_soma = st.slider("Soma das Dezenas", 0, 800, (0, 800), 1)
                limite_fibo = st.slider("Qtd. Fibonacci", 0, m_max, (0, m_max), 1)
                limite_repetidas = st.slider("Repetidas (Últ. Sorteio)", 0, m_max, (0, m_max), 1)
            with cf2:
                limite_pares = st.slider("Qtd. de Pares", 0, m_max, (0, m_max), 1)
                limite_mult3 = st.slider("Qtd. Múlt. de 3", 0, m_max, (0, m_max), 1)
                max_linha = st.number_input("Máx. Linha", 1, 10, 10)
            with cf3:
                limite_primos = st.slider("Qtd. de Primos", 0, m_max, (0, m_max), 1)
                limite_moldura = st.slider("Qtd. Moldura", 0, m_max, (0, m_max), 1)
                max_coluna = st.number_input("Máx. Coluna", 1, 10, 10)
        
        usar_ia = st.toggle("🧠 Ativar IA (K-Means)", value=False, help="Filtra os jogos para corresponder ao cluster matemático mais provável.")
    else:
        st.error("🔒 **Premium Bloqueado** - Adquira uma licença para destravar Filtros e Machine Learning.")
        limite_soma = (0, 800); limite_fibo = (0, m_max); limite_repetidas = (0, m_max)
        limite_pares = (0, m_max); limite_mult3 = (0, m_max); limite_primos = (0, m_max)
        limite_moldura = (0, m_max); max_linha = 10; max_coluna = 10; usar_ia = False

    custo_previsto = calcular_custo_jogos(loteria, qtd_j, qtd_d)
    st.markdown(f"💰 **Custo Estimado da Aposta:** R$ {custo_previsto:.2f}")

    if st.button("➕ Adicionar ao Carrinho", type="primary", use_container_width=True):
        jogos = sugerir_jogo(loteria, qtd_j, qtd_d, usar_ia=usar_ia, filtro_soma=limite_soma, 
                             filtro_pares=limite_pares, filtro_primos=limite_primos, filtro_fibo=limite_fibo, 
                             filtro_mult3=limite_mult3, filtro_moldura=limite_moldura, filtro_repetidas=limite_repetidas, 
                             limite_linha=max_linha, limite_coluna=max_coluna)
        custo_uni = custo_previsto / qtd_j if qtd_j > 0 else 0
        for j in jogos:
            st.session_state.carrinho.append({"Loteria": loteria.upper(), "Dezenas": ", ".join(map(str, sorted(j))), "Custo Unitário": custo_uni, "IA / Filtros": "💎 VIP" if usar_ia or usuario_premium else "Aleatório (Free)"})
        st.rerun()

    if st.session_state.carrinho:
        st.divider()
        df_c = pd.DataFrame(st.session_state.carrinho)
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            st.metric("Total do Carrinho", f"R$ {df_c['Custo Unitário'].sum():.2f}")
        with col_c2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_c.to_excel(writer, index=False, sheet_name='Meus Jogos')
            excel_dados = buffer.getvalue()
            
            if usuario_premium:
                st.download_button(
                    label="📥 Baixar Excel", data=excel_dados, 
                    file_name="meus_jogos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )
            else:
                st.button("🔒 Baixar Excel (VIP)", disabled=True, use_container_width=True)
            
            if st.button("🗑️ Limpar Carrinho", use_container_width=True): 
                st.session_state.carrinho = []
                st.rerun()
                
        if st.button("💾 SALVAR NO BANCO PARA CONFERÊNCIA", use_container_width=True):
            conn = obter_conexao()
            prox = obter_ultimo_concurso_db(loteria) + 1
            for _, r in df_c.iterrows():
                conn.execute("INSERT INTO apostas_usuario (loteria, concurso_alvo, dezenas_jogadas) VALUES (?,?,?)", (r["Loteria"].lower(), prox, r["Dezenas"].replace(" ", "")))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.session_state.carrinho = []
            st.toast("Apostas guardadas com segurança no banco de dados!", icon="💾")
            time.sleep(1)
            st.rerun()

with tabs[1]:
    df_h = carregar_historico_cacheados(loteria)
    if not df_h.empty: 
        st.dataframe(df_h, use_container_width=True, hide_index=True)

with tabs[2]:
    df_p = carregar_apostas_cacheadas(loteria)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        c_conf1, c_conf2 = st.columns(2)
        with c_conf1:
            if st.button("🔍 Conferir Acertos com Sorteio Oficial", use_container_width=True, type="primary"):
                res = conferir_resultados(loteria)
                if res is not None:
                    st.table(res)
                    if res["Qtd. Acertos"].astype(str).str.isnumeric().any() and res[res["Qtd. Acertos"] != '-']["Qtd. Acertos"].astype(int).max() > 3:
                        st.balloons()
        with c_conf2:
            if st.button("🗑️ Apagar Histórico de Apostas", use_container_width=True):
                limpar_apostas_banco(loteria)
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Você ainda não tem jogos salvos para esta loteria.")

with tabs[3]:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_freq, df_atraso = carregar_estatisticas_cacheadas(loteria)
    if df_freq is not None:
        modo_visao = st.radio("Visão:", ["📊 Gráficos (Top 20)", "📝 Tabelas Completas"], horizontal=True, label_visibility="collapsed")
        c_est1, c_est2 = st.columns(2)
        if "Gráficos" in modo_visao:
            with c_est1: 
                st.plotly_chart(px.bar(df_freq.head(20).astype({'Número': str}), x='Número', y='Sorteios', title="Frequência (Mais Sorteados)", color='Sorteios', color_continuous_scale='Blues'), use_container_width=True)
            with c_est2: 
                st.plotly_chart(px.bar(df_atraso.head(20).astype({'Número': str}), x='Número', y='Atraso', title="Atrasos (Mais Tempo Sem Sair)", color='Atraso', color_continuous_scale='Oranges'), use_container_width=True)
        else:
            with c_est1: 
                st.dataframe(df_freq.style.format(precision=2).bar(subset=['Sorteios'], color='#1f77b4'), use_container_width=True, hide_index=True)
            with c_est2: 
                st.dataframe(df_atraso.style.format(precision=2).background_gradient(subset=['Atraso'], cmap='Oranges'), use_container_width=True, hide_index=True)

if is_admin:
    with tabs[4]:
        st.header("🛡️ Centro de Comando Admin")
        st.subheader("Base de Clientes")
        u_list = listar_todos_usuarios()
        st.dataframe(pd.DataFrame(u_list, columns=["ID", "Nome", "E-mail", "Cargo", "Licença", "Troca Pendente"]), use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🔑 Reset de Segurança (Senha Temporária)")
        st.info("Gera uma senha aleatória e força a troca no próximo login do utilizador.")
        with st.form("f_adm_reset"):
            email_target = st.text_input("E-mail do Usuário")
            if st.form_submit_button("Gerar Senha Temporária", type="primary", use_container_width=True):
                status, p_temp = resetar_senha_por_admin(email_target)
                if status:
                    st.success(f"Resetado! Senha: **{p_temp}**")
                    st.warning("⚠️ Forneça esta senha ao usuário. Ela expira após a troca.")
                else: st.error(p_temp)

        st.divider()
        st.subheader("Configurações Globais de Tarifas")
        conn = obter_conexao()
        dados_t = conn.execute("SELECT preco_base, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
        conn.close()
        
        if dados_t:
            ca1, ca2 = st.columns(2)
            with ca1: novo_preco = st.number_input("Alterar Preço da Aposta Base:", value=float(dados_t[0]), step=0.50)
            with ca2: nova_dez_max = st.number_input("Alterar Limite Máximo de Dezenas:", value=int(dados_t[1]), step=1)
            
            if st.button("💾 Salvar Novas Tarifas no Banco", type="primary"):
                atualizar_preco_banco(loteria, novo_preco, nova_dez_max)
                st.cache_data.clear() 
                st.success("Tarifas do sistema atualizadas e aplicadas para todos os usuários!")
                time.sleep(1) 
                st.rerun()