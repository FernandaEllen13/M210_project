import pulp
import sys

class AnalisadorSimplex:
    def __init__(self):
        self.modelo = None
        self.variaveis = {}
        self.restricoes = {} 
        self.rhs_originais = {} #
        self.lucro_base = 0
        self.precos_sombra_base = {}
        self.resolvido = False

    def definir_problema(self):
        print("\n--- DEFINIÇÃO DO PROBLEMA ---")
        self.modelo = pulp.LpProblem("Maximizacao_Lucro", pulp.LpMaximize)
        self.variaveis = {}
        self.restricoes = {}
        self.rhs_originais = {}
        self.resolvido = False

        try:
            num_vars = int(input("Quantas variáveis de decisão (2, 3 ou 4)? "))
            if num_vars < 2 or num_vars > 4:
                print("Por favor, escolha entre 2 e 4 variáveis para este exemplo.")
                return
        except ValueError:
            print("Entrada inválida.")
            return

        print("\nDefinindo Função Objetivo (Max Z = c1*x1 + ...)")
        expressao_obj = 0
        for i in range(1, num_vars + 1):
            nome = f"x{i}"
            var = pulp.LpVariable(nome, lowBound=0, cat='Continuous')
            self.variaveis[nome] = var
            
            coef = float(input(f"  Digite o coeficiente para {nome}: "))
            expressao_obj += coef * var
        
        self.modelo += expressao_obj, "Funcao_Objetivo"

        print("\nDefinindo Restrições")
        print("Digite os coeficientes")
        
        contador_rest = 1
        while True:
            print(f"\n--- Restrição R{contador_rest} ---")
            expressao_rest = 0
            
            for i in range(1, num_vars + 1):
                nome_var = f"x{i}"
                coef_r = float(input(f"  Coeficiente de {nome_var} na restrição: "))
                expressao_rest += coef_r * self.variaveis[nome_var]
            
            rhs = float(input(f" Capacidade: "))
            
            nome_rest = f"Restricao_{contador_rest}"
            constraint = (expressao_rest <= rhs)
            
            self.modelo += constraint, nome_rest
            self.restricoes[nome_rest] = constraint
            self.rhs_originais[nome_rest] = rhs
            
            contador_rest += 1
            continuar = input("Deseja adicionar outra restrição? (s/n): ").lower()
            if continuar != 's':
                break
            
        
        print("\nProblema configurado com sucesso!")
        self.resolver_base()

    def resolver_base(self):
        status = self.modelo.solve(pulp.PULP_CBC_CMD(msg=False))
        self.lucro_base = pulp.value(self.modelo.objective)
        
        self.precos_sombra_base = {}
        for nome, restricao in self.modelo.constraints.items():
            self.precos_sombra_base[nome] = restricao.pi

        self.resolvido = True

    def mostrar_resultados(self):
        if not self.resolvido:
            print("Erro: Defina o problema primeiro.")
            return

        print("\n" + "="*40)
        print(" RESULTADOS DO CENÁRIO BASE")
        print("="*40)
        print(f"Status: {pulp.LpStatus[self.modelo.status]}")
        print(f"Lucro Máximo (Z): {self.lucro_base:.2f}")
        
        print("\n--- Ponto Ótimo ---")
        for nome, var in self.variaveis.items():
            print(f"  {nome} = {var.varValue:.2f}")
            
        print("\n--- Preços Sombra (Shadow Prices) ---")
        print(f"  {'Restrição':<15} | {'RHS Original':<12} | {'Preço Sombra':<12}")
        for nome in self.restricoes.keys():
            print(f"  {nome:<15} | {self.rhs_originais[nome]:<12} | {self.precos_sombra_base[nome]:.4f}")
        print("="*40)

    def analisar_viabilidade(self):
        if not self.resolvido:
            print("Erro: Defina o problema primeiro.")
            return

        print("\n--- ANÁLISE DE viabilidade (SIMULAÇÃO) ---")
        print("Escolha qual restrição deseja alterar:")
        
        lista_rest = list(self.restricoes.keys())
        for idx, nome in enumerate(lista_rest):
            print(f"  {idx + 1}. {nome} (RHS Atual: {self.rhs_originais[nome]})")
            
        try:
            escolha = int(input("Digite o número da restrição: ")) - 1
            if escolha < 0 or escolha >= len(lista_rest):
                print("Opção inválida.")
                return
            
            nome_alvo = lista_rest[escolha]
            variacao = float(input(f"Digite a variação desejada para {nome_alvo} (ex: 2 ou -5): "))
        except ValueError:
            print("Entrada inválida.")
            return

        rhs_atual = self.rhs_originais[nome_alvo]
        novo_rhs = rhs_atual + variacao
        preco_sombra = self.precos_sombra_base[nome_alvo]
        lucro_estimado = self.lucro_base + (preco_sombra * variacao)

        print(f"\n--- Análise para {nome_alvo} ---")
        print(f"Alteração: RHS de {rhs_atual} para {novo_rhs} (Delta: {variacao})")
        print(f"Preço Sombra Base: {preco_sombra:.4f}")
        print(f"Lucro Estimado (Teoria): {lucro_estimado:.4f}")

        constraint_obj = self.modelo.constraints[nome_alvo]
        constraint_obj.changeRHS(novo_rhs) # Aplica mudança
        
        self.modelo.solve(pulp.PULP_CBC_CMD(msg=False)) # Resolve
        lucro_real = pulp.value(self.modelo.objective)
        
        constraint_obj.changeRHS(rhs_atual) 
        self.modelo.solve(pulp.PULP_CBC_CMD(msg=False)) 

        print(f"Lucro Real (Simulação):  {lucro_real:.4f}")

        diferenca = abs(lucro_real - lucro_estimado)
        print("\n>>> CONCLUSÃO:")
        if diferenca < 1e-4:
            print("VIÁVEL")
            print(f"   O novo lucro será exatamente {lucro_real:.2f}.")
        else:
            print("NÃO VIÁVEL")
        input("\nPressione Enter para voltar ao menu...")

def main():
    app = AnalisadorSimplex()
    
    while True:
        print("\n" + "#"*30)
        print("   SIMPLEX TABLEAU ANALYZER")
        print("#"*30)
        print("1. Definir Novo Problema")
        print("2. Mostrar Resultado Atual (Ponto Ótimo e Preços Sombra)")
        print("3. Simular Alteração em Restrição")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção: ")

        if opcao == '1':
            app.definir_problema()
        elif opcao == '2':
            app.mostrar_resultados()
            input("\nPressione Enter para continuar...")
        elif opcao == '3':
            app.analisar_viabilidade()
        elif opcao == '4':
            print("Finalizando...")
            sys.exit()
        else:
            print("Opção inválida, tente novamente.")

if __name__ == "__main__":
    main()