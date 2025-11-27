import pulp


def solver_tableau(num_vars, coef_objetivo, restricoes):
    modelo = pulp.LpProblem("Max_Producao",pulp.LpMaximize)     #cria o modelo
    variaveis = []
    for i in range(num_vars):
        var = pulp.LpVariable(f"x{i+1}", lowBound=0)
        variaveis.append(var)       # cria as variáveis - x1,x2,etc
        
    func_obj = pulp.lpSum([coef_objetivo[i] * variaveis[i] for i in range(num_vars)])    
    modelo += func_obj              # criação func objetivo
    
    for i,r in enumerate(restricoes):
        coefs_r = r['coefs']
        disp = r['disp']
        expressao_r = pulp.lpSum([coefs_r[i] * variaveis[i] for i in range(num_vars)])
        modelo += (expressao_r <= disp), f"R{i+1}"     #criação restrições
        
    modelo.solve(pulp.PULP_CBC_CMD())     #resolução
    
    resultado = {
        "status": pulp.LpStatus[modelo.status],
        "lucro_maximo": pulp.value(modelo.objective),
        "variaveis": {},
        "precos_sombra": {}
    }
    
    for var in variaveis:
        resultado["variaveis"][var.name] = var.varValue
    
    for nome, restricao in modelo.constraints.items():
            resultado["precos_sombra"][nome] = restricao.pi
    
    return resultado