import streamlit as st
import pandas as pd
from solver import base_solver_tableau

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
        
    /* Cor dos Números (Métricas) */
    [data-testid="stMetricValue"] { color: #1E90FF; }
    
    /* Bordas nas tabelas para melhor visualização */
    div[data-testid="stTable"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 5px;

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
        
        with cols[-2]:
            tipo = st.selectbox(
                "Tipo",
                ["<=", ">=", "="],
                key=f"tipo_{r}"
            )
        
        with cols[-1]:
            disp_val = st.number_input(f"Capacidade R{r+1}", value=0.0, key=f"disp_{r}")
        
        inputs_restricoes.append({'coefs': coefs_linha, 'disp': disp_val,'tipo': tipo})
        st.write("---")
        

if 'resultado_otimo' not in st.session_state:
    st.session_state.resultado_otimo = None
    st.session_state.saved_inputs_obj = []
    st.session_state.saved_inputs_rest = []

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Calcular ponto ótimo"):
    resultado = base_solver_tableau(num_vars, inputs_objetivo, inputs_restricoes)
    st.session_state.resultado_otimo = resultado  
    st.session_state.saved_inputs_obj = inputs_objetivo
    st.session_state.saved_inputs_rest = inputs_restricoes
    
if st.session_state.resultado_otimo is not None:
    resultado = st.session_state.resultado_otimo
    saved_obj = st.session_state.saved_inputs_obj
    saved_rest = st.session_state.saved_inputs_rest
    
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
            st.subheader("Variáveis:")
            df_res = pd.DataFrame.from_dict(resultado['variaveis'], orient='index', columns=['Qtd. Otimizada'])
            df_res.index.name = 'Produto'
            st.table(df_res)
        
        with col_tabela2:
            st.subheader("Preços-Sombra:")
            if 'precos_sombra' in resultado:
                df_shadow = pd.DataFrame.from_dict(resultado['precos_sombra'], orient='index', columns=['Valor Sombra'])
                df_shadow.index.name = 'Restrição'
                st.table(df_shadow)
            else:
                st.info("Preços-sombra não disponíveis.")    
        
        st.markdown("---")
        st.header("Condições de Viabilidade")
        st.info("Intervalos onde o Preço Sombra permanece válido:")
        
        if resultado.get('viabilidade'):
            dados_viabilidade = []
            for nome, dados in resultado['viabilidade'].items():
                
                aum = dados['Aumento Permitido']
                red = dados['Redução Permitida']
                cap_atual = dados['Capacidade Atual'] 
                preco_sombra = resultado['precos_sombra'].get(nome, 0)
                
                if isinstance(aum, (int, float)):
                    str_aum = f"+ {aum:.2f}"
                    max_cap_val = cap_atual + aum
                    max_cap_str = f"{max_cap_val:.2f}"
                else:
                    str_aum = str(aum) 
                    max_cap_str = "+Inf"

                if isinstance(red, (int, float)):
                    str_red = f"- {red:.2f}"
                    min_cap_val = cap_atual - red
                    min_cap_str = f"{min_cap_val:.2f}"
                else:
                    str_red = str(red) 
                    min_cap_str = "-Inf"
                
                dados_viabilidade.append({
                    "Restrição": str(nome),
                    "Capacidade Atual": f"{cap_atual:.2f}", 
                    "Preço Sombra": f"{preco_sombra:.4f}",
                    "Aumento Permitido": str_aum,
                    "Redução Permitida": str_red,
                    "Intervalo Viável": f"[{min_cap_str} ; {max_cap_str}]"
                })
                

            df_viab = pd.DataFrame(dados_viabilidade)
            st.dataframe(df_viab, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.header("Viabilidade: ")
        st.caption("Digite as variações(Deltas). O sistema verificará se são viáveis e calculará o novo lucro.")
        
        col_sim_inputs, col_sim_res = st.columns([1, 2])
        
        deltas = {}
        with col_sim_inputs:
            st.subheader("Variações")
            for r in range(num_restricoes):
                nr = f"R{r+1}"
                deltas[r] = st.number_input(f"Delta em {nr}", value=0.0, step=10.0, key=f"d_{r}")
        
        with col_sim_res:
            st.subheader("Resultados da Análise:")
            if st.button("Testar Variações"):
                
                lucro_base = resultado['lucro_maximo']
                impacto_total = 0
                todas_viaveis = True
                detalhes = []
                
                for idx, delta in deltas.items():
                    if delta != 0:
                        nr = f"R{idx+1}"
                        viab_dados = resultado['viabilidade'][nr]
                        preco_sombra = resultado['precos_sombra'].get(nr, 0)
                        
                        lim_aumento = viab_dados['Aumento Permitido']
                        lim_reducao = viab_dados['Redução Permitida']
                        
                        esta_viavel = False
                        if delta > 0:
                            if isinstance(lim_aumento, str) or delta <= (lim_aumento + 1e-5):
                                esta_viavel = True
                        else: 
                            if isinstance(lim_reducao, str) or abs(delta) <= (lim_reducao + 1e-5):
                                esta_viavel = True
                        
                        status_msg = "Viável (OK)"
                        if not esta_viavel:
                            todas_viaveis = False
                            status_msg = "Inviável (Fora do Limite)"

                        impacto = preco_sombra * delta
                        impacto_total += impacto
                        
                        detalhes.append({
                            "Restrição": nr,
                            "Variação": delta,
                            "Status": status_msg,
                            "Impacto no Lucro": f"{impacto:+.2f} ({preco_sombra:.2f} * {delta:.2f})"
                        })
                
                if detalhes:
                    st.dataframe(pd.DataFrame(detalhes), hide_index=True, use_container_width=True)
                    
                    st.markdown("#### Conclusão Global:")
                    novo_lucro = lucro_base + impacto_total
                    
                    if todas_viaveis:
                        st.success("Todas as alterações estão dentro dos limites de viabilidade.")
                        st.metric("Novo Lucro Estimado", f"$ {novo_lucro:.2f}", delta=f"{impacto_total:.2f}")
                        st.latex(r"Z_{novo} = Z_{atual} + \sum (\text{Sombra} \times \Delta)")
                        st.write(f"$ {novo_lucro:.2f} = {lucro_base:.2f} + ({impacto_total:.2f}) $")
                    else:
                        st.error("Uma ou mais alterações violam os limites de viabilidade. Não é viável.")
                else:
                    st.info("Digite alguma variação diferente de zero.")

    else:
        st.error(f"Erro: Status '{resultado['status']}'.")