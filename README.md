# Solver - Simplex Tableau

Sistema de otimização linear com interface web para resolver problemas de programação linear usando o método Simplex.

## Sobre o Projeto

Este projeto implementa um solver completo de otimização linear que resolve problemas de maximização, calcula preços-sombra, realiza análise de sensibilidade e permite simulação interativa de variações nos recursos através de uma interface web moderna.

## Como Executar

### Requisitos

- Python 3.8 ou superior
- pip

### Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/FernandaEllen13/M210_project.git
cd M210_project
pip install -r requirements.txt
```

### Executar

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

## Estrutura do Projeto

```
M210_project/
├── app.py                  # Interface web (Streamlit)
├── solver.py              # Motor de otimização (PuLP)
├── requirements.txt       # Dependências
├── EXPLICACAO_CODIGO.md  # Documentação técnica detalhada
└── README.md             # Este arquivo
```

## Arquivos Principais

**solver.py**

Contém a lógica de otimização:
- `criar_modelo_interno()` - Cria o modelo de programação linear
- `encontrar_limite_disp()` - Busca exponencial e binária para encontrar limites
- `calcular_viabilidade()` - Análise de sensibilidade
- `base_solver_tableau()` - Função principal

**app.py**

Interface web com Streamlit para entrada de dados, visualização de resultados e simulação de variações.

## Documentação

Para entender o código em detalhes, consulte o arquivo [EXPLICACAO_CODIGO.md](EXPLICACAO_CODIGO.md) que contém explicação passo a passo de cada função com exemplos práticos.

## Exemplo de Uso

### Problema

Uma fábrica produz 2 produtos (A e B):

**Lucros:**
- Produto A: R$ 30/unidade
- Produto B: R$ 50/unidade

**Restrições:**
- Horas de Máquina: 2A + 3B ≤ 100
- Mão de Obra: 4A + 2B ≤ 120
- Demanda de B: B ≤ 25

### Solução

- Lucro Máximo: R$ 1.650,00
- Produto A: 15 unidades
- Produto B: 25 unidades

**Preços-Sombra:**
- Máquina: R$ 8,00 por hora adicional
- Mão de Obra: R$ 1,00 por hora adicional
- Demanda: R$ 20,00 por unidade adicional de B

## Tecnologias

- Python 3.x
- PuLP 3.3.0 - Solver de otimização linear
- Streamlit 1.51.0 - Framework web
- Pandas 2.3.3 - Manipulação de dados
- NumPy 2.3.5 - Computação numérica

## Funcionalidades

**Resolução de Problemas Lineares**
- Suporta até 4 variáveis de decisão
- Até 20 restrições simultâneas
- Três tipos de restrições: menor ou igual, maior ou igual, igualdade

**Análise Automática**
- Cálculo de preços-sombra (shadow prices)
- Limites de viabilidade para cada restrição
- Identificação de recursos críticos

**Simulação Interativa**
- Teste variações nos recursos
- Validação automática de viabilidade
- Cálculo do impacto no lucro

## Conceitos Implementados

**Programação Linear**
- Otimização de função objetivo linear sujeita a restrições lineares
- Método Simplex implementado via biblioteca PuLP

**Análise de Sensibilidade**
- Preços-Sombra: valor marginal de cada recurso
- Intervalos de Viabilidade: limites onde a solução básica permanece ótima
- Análise de Variações: impacto de mudanças nos recursos

**Algoritmos**
- Busca Exponencial para encontrar região de mudança
- Busca Binária para refinar limites com precisão
- Solver CBC para implementação eficiente do Simplex

## Licença

MIT License
