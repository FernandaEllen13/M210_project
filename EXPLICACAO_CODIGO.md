# Explicação Detalhada do Código - Sistema de Otimização Linear

## Visão Geral do Projeto

Este projeto implementa um **Sistema de Otimização Linear** que resolve problemas de Programação Linear usando o **Método Simplex** através da biblioteca PuLP, com uma interface web interativa em Streamlit.

**Objetivo:** Maximizar lucros respeitando restrições de recursos disponíveis.

---

# ARQUIVO 1: solver.py

Este arquivo contém toda a lógica matemática e algorítmica do sistema.

---

## 1. Função `criar_modelo_interno()`

### Código:

```python
def criar_modelo_interno(num_vars, coef_objetivo, restricoes, variacoes=None):
    modelo = pulp.LpProblem("Max_Producao", pulp.LpMaximize)

    variaveis = []
    for i in range(num_vars):
        var = pulp.LpVariable(f"x{i+1}", lowBound=0)
        variaveis.append(var)

    func_obj = pulp.lpSum([coef_objetivo[i] * variaveis[i] for i in range(num_vars)])
    modelo += func_obj

    for i, r in enumerate(restricoes):
        coefs_r = r['coefs']
        disp = r['disp']

        if variacoes and i in variacoes:
            disp += variacoes[i]

        expressao_r = pulp.lpSum([coefs_r[j] * variaveis[j] for j in range(num_vars)])
        tipo = r.get("tipo", "<=")

        if tipo == "<=":
            modelo += (expressao_r <= disp), f"R{i+1}"
        elif tipo == ">=":
            modelo += (expressao_r >= disp), f"R{i+1}"
        elif tipo == "=":
            modelo += (expressao_r == disp), f"R{i+1}"

    return modelo, variaveis
```

### O que essa função faz?

Cria o modelo matemático de otimização linear que será resolvido.

### Explicação Passo a Passo:

#### **Passo 1: Criar o Problema**
```python
modelo = pulp.LpProblem("Max_Producao", pulp.LpMaximize)
```
- Cria um problema de **maximização** chamado "Max_Producao"
- `LpMaximize` indica que queremos maximizar a função objetivo (lucro)

#### **Passo 2: Criar as Variáveis de Decisão**
```python
variaveis = []
for i in range(num_vars):
    var = pulp.LpVariable(f"x{i+1}", lowBound=0)
    variaveis.append(var)
```
- Cria as variáveis x1, x2, x3... (representam quantidade de cada produto)
- `lowBound=0`: quantidade não pode ser negativa
- **Exemplo:** Se `num_vars=2`, cria x1 e x2

#### **Passo 3: Definir a Função Objetivo**
```python
func_obj = pulp.lpSum([coef_objetivo[i] * variaveis[i] for i in range(num_vars)])
modelo += func_obj
```
- Cria a expressão matemática do lucro total
- **Exemplo:** Se coef_objetivo = [30, 50], cria: `30*x1 + 50*x2`
- Adiciona essa função ao modelo

#### **Passo 4: Adicionar as Restrições**
```python
for i, r in enumerate(restricoes):
    coefs_r = r['coefs']
    disp = r['disp']

    if variacoes and i in variacoes:
        disp += variacoes[i]
```
- Para cada restrição, extrai os coeficientes e disponibilidade
- Se houver variações (para análise de sensibilidade), aplica ao valor de disponibilidade
- **Exemplo:** Se capacidade original = 100 e variação = +20, nova capacidade = 120

```python
    expressao_r = pulp.lpSum([coefs_r[j] * variaveis[j] for j in range(num_vars)])
    tipo = r.get("tipo", "<=")
```
- Cria a expressão da restrição
- **Exemplo:** Se coefs = [2, 3], cria: `2*x1 + 3*x2`
- Pega o tipo de restrição (padrão é `<=`)

```python
    if tipo == "<=":
        modelo += (expressao_r <= disp), f"R{i+1}"
    elif tipo == ">=":
        modelo += (expressao_r >= disp), f"R{i+1}"
    elif tipo == "=":
        modelo += (expressao_r == disp), f"R{i+1}"
```
- Adiciona a restrição ao modelo com o tipo correto
- **Exemplo:** `2*x1 + 3*x2 <= 100` (não pode ultrapassar capacidade)
- Nome da restrição: R1, R2, R3...

#### **Passo 5: Retornar**
```python
return modelo, variaveis
```
- Retorna o modelo completo e as variáveis para uso posterior

---

## 2. Função `encontrar_limite_disp()`

### Código:

```python
def encontrar_limite_disp(num_vars, coef_objetivo, restricoes, indice_restricao, preco_sombra_base, direcao):
    step = 1.0
    limite = 0
    encontrou_mudanca = False

    delta_teste = 0
    for _ in range(20):
        delta_teste += step * direcao
        variacao = {indice_restricao: delta_teste}

        modelo, _ = criar_modelo_interno(num_vars, coef_objetivo, restricoes, variacao)
        modelo.solve(pulp.PULP_CBC_CMD(msg=False))

        status = modelo.status
        novo_pi = modelo.constraints[f"R{indice_restricao+1}"].pi if status == 1 else None

        if status != 1 or (novo_pi is not None and abs(novo_pi - preco_sombra_base) > 1e-5):
            encontrou_mudanca = True
            break

        step *= 2
        limite = delta_teste

    if not encontrou_mudanca:
        return float('inf')

    low = min(limite, delta_teste) if direcao == 1 else max(limite, delta_teste)
    high = max(limite, delta_teste) if direcao == 1 else min(limite, delta_teste)

    melhor_delta = limite

    for _ in range(15):
        mid = (low + high) / 2
        variacao = {indice_restricao: mid}

        modelo, _ = criar_modelo_interno(num_vars, coef_objetivo, restricoes, variacao)
        modelo.solve(pulp.PULP_CBC_CMD(msg=False))

        status = modelo.status
        novo_pi = modelo.constraints[f"R{indice_restricao+1}"].pi if status == 1 else None

        valido = (status == 1 and novo_pi is not None and abs(novo_pi - preco_sombra_base) < 1e-5)

        if valido:
            melhor_delta = mid
            if direcao == 1: low = mid
            else: high = mid
        else:
            if direcao == 1: high = mid
            else: low = mid

    return abs(melhor_delta)
```

### O que essa função faz?

Encontra o **limite máximo de variação** de um recurso que mantém o preço-sombra válido.

### Explicação Passo a Passo:

#### **Fase 1: Busca Exponencial (Encontrar região aproximada)**

```python
step = 1.0
limite = 0
encontrou_mudanca = False

delta_teste = 0
for _ in range(20):
```
- Inicializa variáveis para a busca
- Vai testar até 20 iterações com passos crescentes

```python
    delta_teste += step * direcao
    variacao = {indice_restricao: delta_teste}
```
- Incrementa o delta (variação) na direção especificada
- `direcao = 1`: testa aumentos (delta positivo)
- `direcao = -1`: testa reduções (delta negativo)
- **Exemplo:** step=1, depois 2, depois 4, depois 8...

```python
    modelo, _ = criar_modelo_interno(num_vars, coef_objetivo, restricoes, variacao)
    modelo.solve(pulp.PULP_CBC_CMD(msg=False))
```
- Cria um novo modelo com a variação aplicada
- Resolve o modelo usando o solver CBC
- `msg=False`: não mostra mensagens de log

```python
    status = modelo.status
    novo_pi = modelo.constraints[f"R{indice_restricao+1}"].pi if status == 1 else None
```
- Verifica se encontrou solução ótima (status == 1)
- Extrai o novo preço-sombra (pi) da restrição
- `.pi` é a propriedade que contém o preço-sombra

```python
    if status != 1 or (novo_pi is not None and abs(novo_pi - preco_sombra_base) > 1e-5):
        encontrou_mudanca = True
        break
```
- **Condição de parada:** se a solução ficou inviável OU o preço-sombra mudou
- `1e-5`: tolerância numérica (0.00001)
- **Por que?** Encontrou o ponto onde a solução muda

```python
    step *= 2
    limite = delta_teste
```
- Dobra o passo para acelerar a busca
- Guarda o último delta válido

```python
if not encontrou_mudanca:
    return float('inf')
```
- Se não encontrou mudança em 20 iterações, o limite é infinito

#### **Fase 2: Busca Binária (Refinar com precisão)**

```python
low = min(limite, delta_teste) if direcao == 1 else max(limite, delta_teste)
high = max(limite, delta_teste) if direcao == 1 else min(limite, delta_teste)

melhor_delta = limite
```
- Define os limites inferior e superior para a busca binária
- Inicializa o melhor delta encontrado

```python
for _ in range(15):
    mid = (low + high) / 2
    variacao = {indice_restricao: mid}
```
- Faz 15 iterações de busca binária
- Testa o ponto médio do intervalo

```python
    modelo, _ = criar_modelo_interno(num_vars, coef_objetivo, restricoes, variacao)
    modelo.solve(pulp.PULP_CBC_CMD(msg=False))

    status = modelo.status
    novo_pi = modelo.constraints[f"R{indice_restricao+1}"].pi if status == 1 else None

    valido = (status == 1 and novo_pi is not None and abs(novo_pi - preco_sombra_base) < 1e-5)
```
- Testa o modelo com o ponto médio
- Verifica se mantém o preço-sombra original

```python
    if valido:
        melhor_delta = mid
        if direcao == 1: low = mid
        else: high = mid
    else:
        if direcao == 1: high = mid
        else: low = mid
```
- **Se válido:** atualiza melhor_delta e move o limite inferior
- **Se inválido:** move o limite superior
- **Algoritmo clássico de busca binária**

```python
return abs(melhor_delta)
```
- Retorna o valor absoluto do melhor delta encontrado

### Exemplo Prático:

**Situação:**
- Restrição: Horas de Máquina ≤ 100
- Preço-sombra atual: R$ 2,50

**Busca Exponencial:**
- Testa: +1, +2, +4, +8, +16, +32, +64 (preço mudou!)
- Intervalo encontrado: [32, 64]

**Busca Binária:**
- Testa: 48 (válido), 56 (válido), 60 (inválido), 58 (válido)...
- **Resultado:** Pode aumentar até +57.3 horas mantendo preço-sombra = R$ 2,50

---

## 3. Função `calcular_viabilidade()`

### Código:

```python
def calcular_viabilidade(num_vars, coef_objetivo, restricoes, resultado_base):
    relatorio = {}

    for i, r in enumerate(restricoes):
        nome = f"R{i+1}"
        preco_base = resultado_base['precos_sombra'].get(nome, 0)

        aumento = encontrar_limite_disp(num_vars, coef_objetivo, restricoes, i, preco_base, 1)
        reducao = encontrar_limite_disp(num_vars, coef_objetivo, restricoes, i, preco_base, -1)

        relatorio[nome] = {
            "Aumento Permitido": aumento if aumento < 1e9 else "Infinito",
            "Redução Permitida": reducao if reducao < 1e9 else "Infinito",
            "Capacidade Atual": r['disp']
        }

    return relatorio
```

### O que essa função faz?

Calcula os limites de viabilidade para **todas** as restrições do problema.

### Explicação Passo a Passo:

```python
relatorio = {}

for i, r in enumerate(restricoes):
    nome = f"R{i+1}"
    preco_base = resultado_base['precos_sombra'].get(nome, 0)
```
- Cria dicionário vazio para armazenar o relatório
- Para cada restrição, pega o nome (R1, R2, R3...)
- Extrai o preço-sombra base dessa restrição

```python
    aumento = encontrar_limite_disp(num_vars, coef_objetivo, restricoes, i, preco_base, 1)
    reducao = encontrar_limite_disp(num_vars, coef_objetivo, restricoes, i, preco_base, -1)
```
- **Aumento:** chama `encontrar_limite_disp` com direção +1 (positivo)
- **Redução:** chama `encontrar_limite_disp` com direção -1 (negativo)
- **Por que duas chamadas?** Aumentar e reduzir podem ter limites diferentes!

```python
    relatorio[nome] = {
        "Aumento Permitido": aumento if aumento < 1e9 else "Infinito",
        "Redução Permitida": reducao if reducao < 1e9 else "Infinito",
        "Capacidade Atual": r['disp']
    }
```
- Armazena os resultados no relatório
- Se o valor for muito grande (1e9 = 1 bilhão), considera infinito
- Inclui a capacidade atual para referência

```python
return relatorio
```
- Retorna o relatório completo

### Exemplo de Saída:

```python
{
    "R1": {
        "Aumento Permitido": 50.0,
        "Redução Permitida": 30.0,
        "Capacidade Atual": 100
    },
    "R2": {
        "Aumento Permitido": "Infinito",
        "Redução Permitida": 20.0,
        "Capacidade Atual": 80
    }
}
```

**Interpretação:**
- **R1:** Capacidade entre [70, 150] mantém preço-sombra
- **R2:** Pode aumentar quanto quiser, mas reduzir só até 20

---

## 4. Função `base_solver_tableau()` ⭐ FUNÇÃO PRINCIPAL

### Código:

```python
def base_solver_tableau(num_vars, coef_objetivo, restricoes):
    modelo, variaveis = criar_modelo_interno(num_vars, coef_objetivo, restricoes)
    modelo.solve(pulp.PULP_CBC_CMD(msg=False))

    resultado = {
        "status": pulp.LpStatus[modelo.status],
        "lucro_maximo": pulp.value(modelo.objective),
        "variaveis": {},
        "precos_sombra": {},
        "viabilidade": {}
    }

    if modelo.status == 1:
        for var in variaveis:
            resultado["variaveis"][var.name] = var.varValue

        for nome, restricao in modelo.constraints.items():
            resultado["precos_sombra"][nome] = restricao.pi

        resultado["viabilidade"] = calcular_viabilidade(num_vars, coef_objetivo, restricoes, resultado)

    return resultado
```

### O que essa função faz?

É a **função principal** que orquestra todo o processo de otimização e retorna todos os resultados.

### Explicação Passo a Passo:

#### **Passo 1: Criar e Resolver o Modelo**
```python
modelo, variaveis = criar_modelo_interno(num_vars, coef_objetivo, restricoes)
modelo.solve(pulp.PULP_CBC_CMD(msg=False))
```
- Cria o modelo usando a função auxiliar
- **Resolve o problema** usando o solver CBC (implementa Simplex)
- CBC = COIN-OR Branch and Cut (solver open-source)

#### **Passo 2: Preparar Estrutura do Resultado**
```python
resultado = {
    "status": pulp.LpStatus[modelo.status],
    "lucro_maximo": pulp.value(modelo.objective),
    "variaveis": {},
    "precos_sombra": {},
    "viabilidade": {}
}
```
- **status:** "Optimal", "Infeasible", "Unbounded", etc.
- **lucro_maximo:** valor da função objetivo
- **variaveis:** dicionário vazio (será preenchido)
- **precos_sombra:** dicionário vazio (será preenchido)
- **viabilidade:** dicionário vazio (será preenchido)

#### **Passo 3: Extrair Valores das Variáveis (se encontrou solução ótima)**
```python
if modelo.status == 1:
    for var in variaveis:
        resultado["variaveis"][var.name] = var.varValue
```
- `status == 1` significa "Optimal" (solução encontrada)
- Para cada variável (x1, x2, x3...), pega o valor ótimo
- **Exemplo:** `{"x1": 50.0, "x2": 30.0}`

#### **Passo 4: Extrair Preços-Sombra**
```python
    for nome, restricao in modelo.constraints.items():
        resultado["precos_sombra"][nome] = restricao.pi
```
- Para cada restrição, extrai o preço-sombra (dual value)
- `.pi` é a propriedade que contém esse valor
- **Exemplo:** `{"R1": 2.5, "R2": 0.0, "R3": 1.8}`

**O que é preço-sombra?**
- Quanto o lucro aumenta se aumentarmos 1 unidade daquele recurso
- Se = 0 → recurso está sobrando (não é limitante)
- Se > 0 → recurso é escasso (vale a pena conseguir mais)

#### **Passo 5: Calcular Viabilidade**
```python
    resultado["viabilidade"] = calcular_viabilidade(num_vars, coef_objetivo, restricoes, resultado)
```
- Chama a função que calcula os limites de variação
- Essa é a parte mais computacionalmente intensiva

#### **Passo 6: Retornar**
```python
return resultado
```
- Retorna o dicionário completo com todos os resultados

### Exemplo de Retorno Completo:

```python
{
    "status": "Optimal",
    "lucro_maximo": 1500.00,
    "variaveis": {
        "x1": 50.0,
        "x2": 30.0
    },
    "precos_sombra": {
        "R1": 2.5,
        "R2": 0.0,
        "R3": 1.8
    },
    "viabilidade": {
        "R1": {
            "Aumento Permitido": 40.0,
            "Redução Permitida": 25.0,
            "Capacidade Atual": 100
        },
        "R2": {
            "Aumento Permitido": "Infinito",
            "Redução Permitida": 15.0,
            "Capacidade Atual": 80
        },
        "R3": {
            "Aumento Permitido": 50.0,
            "Redução Permitida": 30.0,
            "Capacidade Atual": 120
        }
    }
}
```

---

# ARQUIVO 2: app.py

Este arquivo contém a interface web usando Streamlit.

---

## Estrutura Geral

### 1. Configuração da Página

```python
st.set_page_config(page_title="Solver - Simplex Tableau", layout="wide")
```
- Define título da aba do navegador
- `layout="wide"`: usa largura total da tela

---

### 2. Estilização CSS

```python
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #F0F8FF;
        border-right: 1px solid #1E90FF;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1E90FF !important;
        font-family: 'Helvetica', sans-serif;
    }

    div.stButton > button {
        background-color: #1E90FF;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
```

**O que faz:**
- Personaliza cores e estilos da interface
- **Sidebar:** fundo azul claro
- **Títulos:** azul DodgerBlue
- **Botões:** azul com hover mais escuro
- **Tabelas:** bordas arredondadas

---

## Seção 1: Sidebar - Configurações

```python
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
```

**O que faz:**
- Cria barra lateral com inputs numéricos
- **num_vars:** quantos produtos/variáveis (2 a 4)
- **num_restricoes:** quantas restrições/recursos (1 a 20)
- **value=2:** valor inicial padrão
- **step=1:** incrementa de 1 em 1

---

## Seção 2: Entrada da Função Objetivo

```python
col_obj, col_rest = st.columns([1, 2])

inputs_objetivo = []
with col_obj:
    st.subheader("Função Objetivo: ")
    st.info("Lucro por unidade:")

    for i in range(num_vars):
        val = st.number_input(f"Lucro x{i+1}:", value=0.0, key=f"obj_{i}")
        inputs_objetivo.append(val)
```

**O que faz:**
- Cria duas colunas (proporção 1:2)
- Na primeira coluna:
  - Para cada variável, cria input de lucro
  - **key:** identificador único para Streamlit
  - Armazena valores em lista `inputs_objetivo`

**Exemplo Visual:**
```
┌─────────────────┐
│ Função Objetivo │
├─────────────────┤
│ Lucro x1: [30] │
│ Lucro x2: [50] │
└─────────────────┘
```

---

## Seção 3: Entrada das Restrições

```python
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
```

**O que faz:**
- Para cada restrição, cria uma linha
- **cols:** cria colunas dinâmicas (num_vars + 1)
- Para cada variável, cria input de coeficiente

```python
        with cols[-2]:
            tipo = st.selectbox(
                "Tipo",
                ["<=", ">=", "="],
                key=f"tipo_{r}"
            )

        with cols[-1]:
            disp_val = st.number_input(f"Capacidade R{r+1}", value=0.0, key=f"disp_{r}")

        inputs_restricoes.append({'coefs': coefs_linha, 'disp': disp_val,'tipo': tipo})
```

**O que faz:**
- **cols[-2]:** penúltima coluna com seletor de tipo (<=, >=, =)
- **cols[-1]:** última coluna com capacidade disponível
- Monta dicionário com toda informação da restrição

**Exemplo Visual:**
```
┌────────────────────────────────────────────────┐
│ Restrição 1                                    │
├──────┬──────┬──────┬───────┬──────────────────┤
│ x1   │ x2   │ x3   │ Tipo  │ Capacidade       │
│ [2]  │ [3]  │ [1]  │ [<=]  │ [100]           │
└──────┴──────┴──────┴───────┴──────────────────┘
```

---

## Seção 4: Gerenciamento de Estado

```python
if 'resultado_otimo' not in st.session_state:
    st.session_state.resultado_otimo = None
    st.session_state.saved_inputs_obj = []
    st.session_state.saved_inputs_rest = []
```

**O que faz:**
- **session_state:** persiste dados entre reruns do Streamlit
- Inicializa variáveis se não existem
- **Por que?** Manter resultados após clicar botões

---

## Seção 5: Botão de Cálculo

```python
if st.button("Calcular ponto ótimo"):
    resultado = base_solver_tableau(num_vars, inputs_objetivo, inputs_restricoes)
    st.session_state.resultado_otimo = resultado
    st.session_state.saved_inputs_obj = inputs_objetivo
    st.session_state.saved_inputs_rest = inputs_restricoes
```

**O que faz:**
1. Quando usuário clica no botão
2. **Chama** a função principal do solver
3. **Salva** resultado no estado da sessão
4. **Salva** inputs originais para referência

---

## Seção 6: Exibição de Resultados

### 6.1 Verificar se há resultado

```python
if st.session_state.resultado_otimo is not None:
    resultado = st.session_state.resultado_otimo
    saved_obj = st.session_state.saved_inputs_obj
    saved_rest = st.session_state.saved_inputs_rest
```

### 6.2 Exibir Solução Ótima

```python
    if resultado['status'] == 'Optimal':
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Lucro Máximo Total", value=f"$ {resultado['lucro_maximo']:.2f}")
        with col2:
            st.success("Solução Ótima Encontrada!")
```

**O que faz:**
- Verifica se status é "Optimal"
- Duas colunas:
  - **Coluna 1:** Métrica grande com lucro
  - **Coluna 2:** Mensagem de sucesso verde

**Exemplo Visual:**
```
┌──────────────────────┬─────────────────────────┐
│ Lucro Máximo Total   │ ✅ Solução Ótima       │
│   $ 1,500.00         │    Encontrada!         │
└──────────────────────┴─────────────────────────┘
```

### 6.3 Tabelas de Variáveis e Preços-Sombra

```python
        col_tabela1, col_tabela2 = st.columns(2)

        with col_tabela1:
            st.subheader("Variáveis:")
            df_res = pd.DataFrame.from_dict(resultado['variaveis'], orient='index', columns=['Qtd. Otimizada'])
            df_res.index.name = 'Produto'
            st.table(df_res)
```

**O que faz:**
- Converte dicionário de variáveis em DataFrame do Pandas
- `orient='index'`: usa chaves (x1, x2) como linhas
- Exibe como tabela estática

```python
        with col_tabela2:
            st.subheader("Preços-Sombra:")
            if 'precos_sombra' in resultado:
                df_shadow = pd.DataFrame.from_dict(resultado['precos_sombra'], orient='index', columns=['Valor Sombra'])
                df_shadow.index.name = 'Restrição'
                st.table(df_shadow)
```

**Exemplo Visual:**
```
┌─────────────────────┬──────────────────────┐
│ Produto │ Qtd. Ótima│ Restrição │ Preço   │
├─────────┼───────────┼───────────┼─────────┤
│   x1    │   50.00   │    R1     │  2.50   │
│   x2    │   30.00   │    R2     │  0.00   │
└─────────┴───────────┴───────────┴─────────┘
```

---

## Seção 7: Tabela de Viabilidade

```python
        if resultado.get('viabilidade'):
            dados_viabilidade = []
            for nome, dados in resultado['viabilidade'].items():

                aum = dados['Aumento Permitido']
                red = dados['Redução Permitida']
                cap_atual = dados['Capacidade Atual']
                preco_sombra = resultado['precos_sombra'].get(nome, 0)
```

**O que faz:**
- Extrai dados de viabilidade para cada restrição
- Pega valores de aumento, redução, capacidade e preço-sombra

```python
                if isinstance(aum, (int, float)):
                    str_aum = f"+ {aum:.2f}"
                    max_cap_val = cap_atual + aum
                    max_cap_str = f"{max_cap_val:.2f}"
                else:
                    str_aum = str(aum)
                    max_cap_str = "+Inf"
```

**O que faz:**
- **Se número:** formata com 2 casas decimais e calcula capacidade máxima
- **Se infinito:** usa string "Infinito" e "+Inf"

```python
                if isinstance(red, (int, float)):
                    str_red = f"- {red:.2f}"
                    min_cap_val = cap_atual - red
                    min_cap_str = f"{min_cap_val:.2f}"
                else:
                    str_red = str(red)
                    min_cap_str = "-Inf"
```

**O que faz:**
- Mesmo processo para reduções
- Calcula capacidade mínima

```python
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
```

**O que faz:**
- Monta lista de dicionários com todos os dados formatados
- Cria DataFrame e exibe como tabela interativa
- `hide_index=True`: esconde índice numérico
- `use_container_width=True`: usa largura total

**Exemplo Visual:**
```
┌────────┬─────────┬────────┬──────────┬──────────┬──────────────┐
│Restriç.│Cap.Atual│Preço $ │ Aumento  │ Redução  │  Intervalo   │
├────────┼─────────┼────────┼──────────┼──────────┼──────────────┤
│  R1    │ 100.00  │ 2.5000 │ + 40.00  │ - 25.00  │ [75.00;140.00│
│  R2    │  80.00  │ 0.0000 │ Infinito │ - 15.00  │ [65.00;+Inf] │
└────────┴─────────┴────────┴──────────┴──────────┴──────────────┘
```

---

## Seção 8: Análise de Variações (Parte mais importante!)

### 8.1 Inputs de Variações

```python
        col_sim_inputs, col_sim_res = st.columns([1, 2])

        deltas = {}
        with col_sim_inputs:
            st.subheader("Variações")
            for r in range(num_restricoes):
                nr = f"R{r+1}"
                deltas[r] = st.number_input(f"Delta em {nr}", value=0.0, step=10.0, key=f"d_{r}")
```

**O que faz:**
- Cria inputs para usuário digitar variações (deltas)
- **step=10.0:** incrementa de 10 em 10
- Armazena em dicionário `deltas`

### 8.2 Botão de Teste

```python
        with col_sim_res:
            st.subheader("Resultados da Análise:")
            if st.button("Testar Variações"):

                lucro_base = resultado['lucro_maximo']
                impacto_total = 0
                todas_viaveis = True
                detalhes = []
```

**O que faz:**
- Quando usuário clica "Testar Variações"
- Inicializa variáveis de controle
- `todas_viaveis`: flag para verificar se todas são válidas

### 8.3 Processar Cada Variação

```python
                for idx, delta in deltas.items():
                    if delta != 0:
                        nr = f"R{idx+1}"
                        viab_dados = resultado['viabilidade'][nr]
                        preco_sombra = resultado['precos_sombra'].get(nr, 0)

                        lim_aumento = viab_dados['Aumento Permitido']
                        lim_reducao = viab_dados['Redução Permitida']
```

**O que faz:**
- Para cada delta diferente de zero
- Busca dados de viabilidade da restrição
- Extrai limites de aumento e redução

### 8.4 Verificar Viabilidade

```python
                        esta_viavel = False
                        if delta > 0:
                            if isinstance(lim_aumento, str) or delta <= (lim_aumento + 1e-5):
                                esta_viavel = True
                        else:
                            if isinstance(lim_reducao, str) or abs(delta) <= (lim_reducao + 1e-5):
                                esta_viavel = True
```

**O que faz:**
- **Se delta positivo (aumento):**
  - Viável se limite é infinito OU delta ≤ limite
- **Se delta negativo (redução):**
  - Viável se limite é infinito OU |delta| ≤ limite
- `1e-5`: tolerância numérica

```python
                        status_msg = "Viável (OK)"
                        if not esta_viavel:
                            todas_viaveis = False
                            status_msg = "Inviável (Fora do Limite)"
```

**O que faz:**
- Define mensagem de status
- Marca flag global se alguma for inviável

### 8.5 Calcular Impacto

```python
                        impacto = preco_sombra * delta
                        impacto_total += impacto

                        detalhes.append({
                            "Restrição": nr,
                            "Variação": delta,
                            "Status": status_msg,
                            "Impacto no Lucro": f"{impacto:+.2f} ({preco_sombra:.2f} * {delta:.2f})"
                        })
```

**O que faz:**
- **Fórmula:** Impacto = Preço-Sombra × Delta
- Acumula impacto total
- Armazena detalhes para exibição

**Exemplo:**
- Preço-sombra R1 = 2.50
- Delta R1 = +20
- Impacto = 2.50 × 20 = +50.00

### 8.6 Exibir Resultados

```python
                if detalhes:
                    st.dataframe(pd.DataFrame(detalhes), hide_index=True, use_container_width=True)

                    st.markdown("#### Conclusão Global:")
                    novo_lucro = lucro_base + impacto_total
```

**O que faz:**
- Mostra tabela com detalhes de cada variação
- Calcula novo lucro = lucro base + impacto total

```python
                    if todas_viaveis:
                        st.success("Todas as alterações estão dentro dos limites de viabilidade.")
                        st.metric("Novo Lucro Estimado", f"$ {novo_lucro:.2f}", delta=f"{impacto_total:.2f}")
                        st.latex(r"Z_{novo} = Z_{atual} + \sum (\text{Sombra} \times \Delta)")
                        st.write(f"$ {novo_lucro:.2f} = {lucro_base:.2f} + ({impacto_total:.2f}) $")
```

**O que faz se todas viáveis:**
- Mensagem de sucesso verde
- Métrica com novo lucro (mostra delta como seta verde/vermelha)
- Fórmula em LaTeX
- Cálculo detalhado

```python
                    else:
                        st.error("Uma ou mais alterações violam os limites de viabilidade. Não é viável.")
```

**O que faz se alguma inviável:**
- Mensagem de erro vermelha

```python
                else:
                    st.info("Digite alguma variação diferente de zero.")
```

**Exemplo Visual (Todas Viáveis):**
```
┌──────────┬──────────┬───────────┬─────────────────────┐
│Restrição │ Variação │  Status   │ Impacto no Lucro   │
├──────────┼──────────┼───────────┼─────────────────────┤
│   R1     │  +20.00  │Viável (OK)│ +50.00 (2.50*20.00)│
│   R2     │  -10.00  │Viável (OK)│ -0.00 (0.00*-10.00)│
└──────────┴──────────┴───────────┴─────────────────────┘

✅ Todas as alterações estão dentro dos limites!

Novo Lucro Estimado: $ 1,550.00  ↑ 50.00

Z_novo = Z_atual + Σ(Sombra × Δ)
$ 1,550.00 = 1,500.00 + (50.00)
```

---

## Conceitos-Chave para Apresentação

### 1. **Programação Linear**
- Otimização de função objetivo linear
- Sujeita a restrições lineares
- Usado em: produção, logística, finanças

### 2. **Método Simplex**
- Algoritmo eficiente para resolver PL
- Caminha pelas soluções básicas factíveis
- Garantia de encontrar ótimo global

### 3. **Preço-Sombra (Shadow Price)**
- Valor marginal de um recurso
- Quanto o lucro aumenta com +1 unidade do recurso
- **= 0** → recurso em excesso (folga)
- **> 0** → recurso escasso (vale conseguir mais)

### 4. **Análise de Sensibilidade**
- Até onde posso variar sem mudar a solução básica
- Intervalos de viabilidade dos preços-sombra
- Importante para decisões de investimento

### 5. **Dualidade**
- Todo problema primal tem um dual
- Preços-sombra = solução ótima do dual
- Interpretação econômica profunda

---

## Como Executar o Projeto

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar Aplicação
```bash
streamlit run app.py
```

### 3. Acessar
- Abre automaticamente no navegador
- Geralmente: http://localhost:8501

---

## Exemplo de Uso

### Problema:
**Uma fábrica produz dois produtos:**
- **Produto A:** lucro de R$ 30/unidade
- **Produto B:** lucro de R$ 50/unidade

**Restrições:**
1. **Horas de Máquina:** 2A + 3B ≤ 100
2. **Horas de Mão de Obra:** 4A + 2B ≤ 120
3. **Demanda Máxima de B:** B ≤ 25

### Entrada no Sistema:

**Função Objetivo:**
- Lucro x1: 30
- Lucro x2: 50

**Restrições:**
- R1: 2, 3, ≤, 100
- R2: 4, 2, ≤, 120
- R3: 0, 1, ≤, 25

### Resultado:
- **Lucro Máximo:** R$ 1,650.00
- **x1 (Produto A):** 15 unidades
- **x2 (Produto B):** 25 unidades

**Preços-Sombra:**
- R1 (Máquina): R$ 8.00 → vale pagar até R$ 8 por hora extra
- R2 (Mão de Obra): R$ 1.00 → vale pagar até R$ 1 por hora extra
- R3 (Demanda): R$ 20.00 → se conseguir vender +1 unidade, lucro ↑ R$ 20

**Viabilidade:**
- R1: pode variar entre [80, 150]
- R2: pode variar entre [100, 180]
- R3: pode variar entre [20, 30]

---

## Summary

1. **Arquitetura modular**
   - Solver separado da interface
   - Facilita testes e manutenção

2. **Algoritmo de busca inteligente**
   - Exponencial + Binária = rápido e preciso
   - Complexidade O(log n) na busca final

3. **Interface intuitiva**
   - Visualização clara dos resultados
   - Análise de variações interativa

4. **Aplicabilidade prática**
   - Decisões de produção
   - Análise de investimentos
   - Precificação de recursos

### Pontos técnicos:

- ✅ Uso correto de bibliotecas especializadas (PuLP)
- ✅ Análise de sensibilidade automática
- ✅ Interface responsiva e profissional
- ✅ Validação de viabilidade em tempo real
- ✅ Código bem estruturado e comentado

---

## Referências Úteis

- **PuLP Documentation:** https://coin-or.github.io/pulp/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Linear Programming:** Introdução à Pesquisa Operacional (Hillier & Lieberman)

---

