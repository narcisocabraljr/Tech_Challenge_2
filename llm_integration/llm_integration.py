# llm_integration.py
from openai import OpenAI
import os

# Carrega a API key do ambiente
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Defina a variável de ambiente OPENAI_API_KEY antes de rodar.")

client = OpenAI(api_key=api_key)

def gerar_instrucoes_motorista(best_solution, distancia_total):
    """
    Gera instruções detalhadas para cada veículo com base na melhor solução
    e distância total usando LLM (OpenAI GPT-4o-mini).
    Retorna dicionário {vehicle_id: "instruções..."}
    """
    try:
        # Monta prompt detalhado
        prompt = f"""
        Você é um assistente logístico. 
        Gere instruções passo a passo para cada veículo entregar os itens
        da melhor solução abaixo. 
        Distância total da rota: {distancia_total:.2f} unidades.
        Estrutura de rotas:
        {best_solution}
        """

        # Chamada à API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )

        content = response.choices[0].message.content

        # Converte em dicionário: cada veículo recebe o mesmo texto por padrão
        instrucoes = {}
        for route_info in best_solution["routes"]:
            vid = route_info["vehicle_id"]
            instrucoes[vid] = f"Instruções veículo {vid+1}:\n{content}"

        return instrucoes

    except Exception as e:
        # Fallback seguro caso API falhe
        print(f"[Aviso] LLM falhou: {e}. Usando instruções simuladas.")
        instrucoes = {}
        for route_info in best_solution["routes"]:
            vid = route_info["vehicle_id"]
            instrucoes[vid] = f"Rota simulada para veículo {vid+1}, distância total: {distancia_total:.2f}"
        return instrucoes
