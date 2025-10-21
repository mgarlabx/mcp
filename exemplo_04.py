from fastmcp import FastMCP
import os
import requests

mcp = FastMCP("Teste")

@mcp.tool
def cotacao(ticker: str) -> float:
    """Retorna a cotação da ação (ticker) informada"""
    # url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
    # r = requests.get(url)
    # data = r.json()
    # return float(data["Global Quote"]["05. price"])
    return 250.00  # Valor fixo para fins de exemplo - a API real permite apenas 25 chamadas por dia na versão gratuita

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)