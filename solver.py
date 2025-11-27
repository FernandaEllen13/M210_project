import pulp

#modelo de recursão para achar o limite de validade do preço-sombra
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

#busca para achar onde o preço-sombra muda:
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
            "Capacidade Atual": r['disp'] # Adicionei para facilitar exibição no app
        }
        
    return relatorio

#função principal:
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

