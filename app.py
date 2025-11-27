import streamlit as st
import pandas as pd
from solver import solver_tableau

st.set_page_config(page_title="Solver - Simplex Tableau", layout="wide")

st.markdown("""
    <style>
    /* --- SIDEBAR (Barra Lateral) --- */
    [data-testid="stSidebar"] {
        background-color: #F0F8FF; /* Azul 'AliceBlue' bem clarinho */
        border-right: 1px solid #1E90FF; /* Borda fina para separar */
    }
    
    /* Títulos e Cabeçalhos em Azul */
    h1, h2, h3, h4, h5, h6 {
        color: #1E90FF !important; /* Azul DodgerBlue */
        font-family: 'Helvetica', sans-serif;
    }
    
    /* Texto normal */
    .stMarkdown p {
        color: #2C3E50;
    }
    
    /* Botões personalizados */
    div.stButton > button {
        background-color: #1E90FF;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        width: 100%; /* Botão ocupa largura total */
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #104E8B; /* Azul mais escuro no hover */
        color: white;
    }
    
    /* Caixas de métricas (Números grandes) */
    [data-testid="stMetricValue"] {
        color: #1E90FF;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.header("Configurações")
    
    num_vars = st.number_input(
        "Número de Variáveis:", 
        min_value=2, max_value=4, value=2, step=1,
    )
    
    num_restricoes = st.number_input(
        "Número de Restrições:", 
        min_value=1, max_value=20, value=2, step=1,
    )
    
    st.markdown("---")


st.title("Solver - Simplex Tableau")
st.markdown("---")
st.header("Parâmetros do Problema: ")


col_obj, col_rest = st.columns([1, 2])

inputs_objetivo = []
with col_obj:
    st.subheader("Função Objetivo: ")
    st.info("Lucro por unidade:")
    
    for i in range(num_vars):
        val = st.number_input(f"Lucro x{i+1}:", value=0.0, key=f"obj_{i}")
        inputs_objetivo.append(val)


inputs_restricoes = []
with col_rest:
    st.subheader("Restrições: ")
    st.info("Digite o consumo de recursos e suas capacidades totais:")
    
    for r in range(num_restricoes):
        st.markdown(f"**Restrição {r+1}**")
        cols = st.columns(num_vars + 1) 
        
        coefs_linha = []
        for v in range(num_vars):
            with cols[v]:
                val = st.number_input(f"x{v+1} em R{r+1}", value=0.0, key=f"rest_{r}_{v}")
                coefs_linha.append(val)
        
        with cols[-1]:
            disp_val = st.number_input(f"Capacidade R{r+1}", value=0.0, key=f"disp_{r}")
        
        inputs_restricoes.append({'coefs': coefs_linha, 'disp': disp_val})
        st.write("---")
        

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Calcular ponto ótimo"):
    resultado = solver_tableau(num_vars, inputs_objetivo, inputs_restricoes)
    
    st.markdown("---")
    st.header("Resultados: ")
    
    if resultado['status'] == 'Optimal':
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Lucro Máximo Total", value=f"$ {resultado['lucro_maximo']:.2f}")
        with col2:
            st.success("Solução Ótima Encontrada!")
        
        col_tabela1, col_tabela2 = st.columns(2)
        
        with col_tabela1:
            st.subheader("Variáveis (Produção):")
            df_res = pd.DataFrame.from_dict(resultado['variaveis'], orient='index', columns=['Qtd. Otimizada'])
            df_res.index.name = 'Produto'
            st.table(df_res)
        
        with col_tabela2:
            st.subheader("Preços Sombra (Dual):")
            if 'precos_sombra' in resultado:
                df_shadow = pd.DataFrame.from_dict(resultado['precos_sombra'], orient='index', columns=['Valor Sombra'])
                df_shadow.index.name = 'Restrição'
                st.table(df_shadow)
            else:
                st.info("Preços sombra não disponíveis.")
        
        st.subheader("Variáveis:")
        df_res = pd.DataFrame.from_dict(resultado['variaveis'], orient='index', columns=['Qtd. Otimizada'])
        df_res.index.name = 'Produto'
        st.table(df_res)
        
    
        
    else:
        st.error(f"Erro: O solver retornou status '{resultado['status']}'. Verifique se as restrições são possíveis.")
        
        