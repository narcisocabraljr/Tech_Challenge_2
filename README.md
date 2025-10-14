# Python Pandas Application

Este projeto é uma aplicação Python que utiliza a biblioteca pygame para carregar e visualizar as rotas geradas pelo nosso código de algoritmo genético, que por sua vez utiliza várias outras bibliotecas para fazer os cálculos de crossover e gerar rotas otimizadas para o problema apresentado na proposta do projeto.

## Estrutura do Projeto

```
Tech_Challenge_2
├── llm_integration
│   └── llm_integration.py
├── notebooks
│   └── vrp_chat_notebook.ipynb
├── caixeiro_viajante.py
├── melhor_solucao.json
├── requirements.txt
└── README.md
```

## Requisitos

- Instalar as bibliotecas do Python do arquivo 'requirements.txt'.

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/narcisocabraljr/Tech_Challenge_2.git
   cd TechChallenge
   ```

## Geração de rotas
Execute o arquivo 'caixeiro_viajante.py' para executar o código principal. Uma janela será exibida ao final do processamento com a melhor rota encontrada, e um arquivo 'json' será gerado para alimentar a LLM.

## Executando o Jupyter Notebook

Para executar a LLM do notebook, é necessário o arquivo 'melhor_solucao.json', que é gerado após a execução do 'caixeiro_viajante.py'. Também é necessário uma chave da API da OpenAI, contida em um arquivo '.env'. Com o arquivo 'json' localizado no caminho correto e o arquivo 'env' contendo a chave, o notebook pode ser executado para a utilização da LLM


## Observações

- Não execute arquivos `.ipynb` diretamente com `python`. Use o Jupyter Notebook para abrir e executar os notebooks.
- Certifique-se de que o arquivo `melhor_solucao.json` está presente na raiz do projeto
- Uma chave da API da OpenAI é necessária para executar a LLM, com os créditos necessários para requisições.