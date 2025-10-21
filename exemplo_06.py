from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

mcp = FastMCP("Teste")

verifier = StaticTokenVerifier(
    tokens={
        "tk-abcdef123456": {
            "client_id": "lorem_ipsum"
        }
    },
)

mcp = FastMCP(name="Teste", auth=verifier, stateless_http=True)

@mcp.tool
def cotacao(ticker: str) -> float:
    """Retorna a cotação da ação (ticker) informada"""
    return 250.00  # Valor fixo para fins de exemplo 

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)