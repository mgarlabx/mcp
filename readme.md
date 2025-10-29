# MCP - O Guia Definitivo

## Hello World

### Funcionamento

MCP é um protocolo de comunicação. Ele permite que uma aplicação de IA ("client") tenha acesso a outra aplicação ("server") em uma mesma chamada ("inference"). Antes do MCP, esse processo tinha que ser feito em pelo menos duas etapas, ou seja, a aplicação "client" primeiro acessava o "server", pegava o resultado e depois fazia a chamada da IA.

O MCP foi criado pela Anthropic e anunciado em [25/11/2024](https://www.anthropic.com/news/model-context-protocol). Desde então, vem ganhando tração e foi adotado inclusive pelos concorrentes, como a [OpenAI](https://platform.openai.com/docs/mcp) e a Google, bem como pelos frameworks como [Langchain](https://docs.langchain.com/oss/python/langchain/mcp), entre outros.

Vamos ver no código como isso funciona. Nesse texto usaremos o framework da OpenAI, por que é um dos mais populares, mas o mesmo raciocínio serve para outros tantos.

Uma chamada de IA ("inference") é feita assim

```python
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input="Qual a cotação atual da ação NVDA?"
)
print(response.output_text)
```

(ver [exemplo_01.ipynb](exemplo_01.ipynb))

Obviamente, o script acima não irá retornar a cotação, pois o modelo não tem como acessar o valor atual da ação solicitada.

Antes do MCP, era necessário fazer essa consulta em duas etapas. O script abaixo consulta o serviço da [Alpha Vantage](https://www.alphavantage.co), fazendo um `request` e depois injeta o resultado no prompt da chamada da IA (para obter uma chave de API da Alpha Vantage, clique [aqui](https://www.alphavantage.co/support/#api-key). A versão gratuita permite 25 chamadas por dia).

```python
from openai import OpenAI
import os
import requests

url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=NVDA&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
r = requests.get(url)
data = r.json()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input=f"Qual a cotação atual da ação NVDA? {data}"
)
print(response.output_text)
```

(ver [exemplo_02.ipynb](exemplo_02.ipynb))

Já no exemplo abaixo, ao invés de usar a API da Alpha Vantage, o script usa o seu MCP, incluindo os parâmetros na própria chamada da IA, reduzindo o processo para apenas uma etapa.

```python
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input="Qual a cotação atual da ação NVDA?",
    tools=[
        {
            "type": "mcp",
            "server_label": "alphavantage",
            "server_url": f"https://mcp.alphavantage.co/mcp?apikey={os.getenv('ALPHAVANTAGE_API_KEY')}",
            "require_approval": "never"
        }
    ]
)
print(response.output_text)
```

(ver [exemplo_03.ipynb](exemplo_03.ipynb))

### Postman

O Postman agora possui suporte também para MCP. Ou seja, além de servir para testar endpoints de APIs, ele consegue também conectar em servidores de MCP para testar.

Para tanto, clique em "File" > "New" e escolha a opção "MCP". Então, é só informar o endpoint do MCP.

Escolha o tipo "HTTP" para servidores MCP remotos e "STDIO" para servidores MCP locais. Falarei mais adiante sobre o servidores MCP locais, já que os exemplos citados lidam com servidores remotos.

## MCP Servers

### FastMCP Server

Até esse ponto, vimos como consumir um MCP, ou seja, vimos o código do lado do "client". Agora vamos ver um código do lado do "server", ou seja, vamos criar um servidor MCP. Para tanto, usaremos um framework popular, o [FastMCP](https://gofastmcp.com/).

Antes de iniciar, é importante explicar as versões 1.0 e 2.0. O FastMCP foi pioneiro na implementação Python de servidores MCP, de tal forma que em 2024 a versão 1.0 foi incorporada no [SDK oficial](https://github.com/modelcontextprotocol/python-sdk) do MCP. O que será apresentado aqui é a versão 2.0, que inclui várias funcionalidades adicionais à 1.0.

Um código simples de um servidor MCP é esse:

```python
from fastmcp import FastMCP
import os
import requests

mcp = FastMCP("Teste")

@mcp.tool
def cotacao(ticker: str) -> float:
    """Retorna a cotação da ação (ticker) informada"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
    r = requests.get(url)
    data = r.json()
    return float(data["Global Quote"]["05. price"])

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

(ver [exemplo_04.ipynb](exemplo_04.ipynb))

Observe que é uma sintaxe parecida com a "FastAPI", havendo um "decorator" `@mcp.tool` antes da função.

Ao executar esse script, será criado um servidor local na porta informado, no caso `http://127.0.0.1:8000`.

Esse endereço poderá ser testado inicialmente no Postman, conforme explicado anteriormente (acrescente `/mcp` no final do endereço).

### Ngrok

O Postman consegue se conectar no endereço `http://127.0.0.1:8000/mcp` sem problemas.

Porém, esse endereço não vai funcionar em uma chamada `responses` da OpenAI, vai dar esse erro:

`Error retrieving tool list from MCP server: 'alphavantage'. Http status code: 424 (Failed Dependency)`

Isso ocorre por que a execução do servidor do MCP pelo `responses` se dá remotamente, no ambiente da OpenAI e, obviamente, ele não tem como acessar um localhost. É preciso publicar esse código em um servidor (em um docker, por exemplo) e usar esse endereço na chamada do `responses`.

Para fins de testes, porém, uma alternativa é criar um "tunnel" usando o [Ngrok](https://ngrok.com/). É um recurso gratuito e, uma vez instalado, basta rodar esse comando em outra sessão:

`ngrok http 8000`

Ele irá gerar um endpoint web, algo como `https://a092444f0de5.ngrok-free.app`.

Veja como fica o script do "client":

```python
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input="Qual a cotação atual da ação NVDA?",
    tools=[
        {
            "type": "mcp",
            "server_label": "cotacao",
            "server_url": "https://a092444f0de5.ngrok-free.app/mcp",
            "require_approval": "never"
        }
    ]
)
print(response.output_text)
```

(ver [exemplo_05.ipynb](exemplo_05.ipynb))

### Autenticação

É possível implementar um protocolo de autenticação. A FastMCP tem vários [recursos](https://gofastmcp.com/servers/auth/authentication) para isso, o script a seguir é o mais [simples](https://gofastmcp.com/servers/auth/token-verification#static-token-verification):

```python
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
```

(ver [exemplo_06.ipynb](exemplo_06.ipynb))

Para testar esse servidor no Postman, é preciso incluir nos "Headers":

`Authorization | Bearer tk-abcdef123456`

No `responses` o script fica assim:

```python
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input="Qual a cotação atual da ação NVDA?",
    tools=[
        {
            "type": "mcp",
            "server_label": "cotacao",
            "server_url": "https://a092444f0de5.ngrok-free.app/mcp",
            "require_approval": "never",
            "headers": {
                 "Authorization": "Bearer tk-abcdef123456"
            }
        }
    ]
)
print(response.output_text)
```

(ver [exemplo_07.ipynb](exemplo_07.ipynb))

### NPX

Mostramos como rodar um servidor local com o FastMCP e como chamá-lo com o Ngrok.

Há também inúmeros MCPs prontos para baixar e rodar localmente. O [MCP Servers](https://mcpservers.org) tem uma enorme coleção deles, não apenas em Python, mas também em outras linguagens como o Node. Assim, é possível baixar os códigos, rodar localmente e criar um "tunnel" com o Ngrok, da mesma forma que fizemos com o FastMCP.

No exemplo abaixo, vamos inicialmente baixar e rodar o MCP do [Playwright](https://mcpservers.org/servers/microsoft/playwright-mcp), que é um conhecido framework para se fazer webscrap. Para tanto, basta executar esse comando (é preciso ter o Node instalado na máquina):

`npx @playwright/mcp@latest --port 8931`

Pronto, é apenas isso! E já dá para testar no Postman pelo endereço `http://localhost:8931/sse`.

Para criar o "tunnel" no Ngrok, é preciso passar uma instrução adicional:

`ngrok http --host-header=rewrite 8931`

O script do client fica dessa forma:

```python
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.responses.create(
    model="gpt-5-nano",
    input="Qual a cotação atual da ação NVDA?",
    tools=[
        {
            "type": "mcp",
            "server_label": "playwright",
            "server_url": "https://a092444f0de5.ngrok-free.app/sse",
            "require_approval": "never"
        }
    ]
)
print(response.output_text)
```

(ver [exemplo_08.ipynb](exemplo_08.ipynb))

### Docker

Para os que estão habituados a trabalhar com o Docker, há uma interessante opção para centralizar servidores MCP em um único ponto, o **Docker MCP Gateway**.

O processo é muito simples, basta selecionar os servidores desejados na interface do Docker Desktop e depois executar esse comando:

`docker mcp gateway run`

Outras opções estão disponíveis, ver [aqui](https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md) a documentação.

Esse [vídeo](https://www.youtube.com/watch?v=-gpVCg_ButA) tem uma boa explicação desse recurso.

## MCP Clients

### FastMCP Client

Até aqui, mostramos como acessar servidores MCP usando o `responses` da OpenAI. Todavia, há várias outras formas de acessar servidores MCP.

O script abaixo mostra como acessar um servidor MCP (no caso, o `exemplo_04.py`):

```python
import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def main():
    async with client:
        result = await client.call_tool("cotacao", {"ticker": "NVDA"})
        print(result)

await main()
```

(ver [exemplo_09.ipynb](exemplo_09.ipynb))

### IDE Client

Praticamente todas as IDEs ("Integrated Development Environment") criaram recursos para conectar MCPs. A principal utilidade disso é permitir que o programador possa interagir com os agentes de desenvolvimento ("vibe coding") em contextos mais especializados. Por exemplo, é possível instalar um MCP do MySQL no VS Code e interagir com as tabelas do banco usando linguagem natural. O programador não precisa sair da IDE para tirar dúvidas sobre o nome das tabelas, das colunas, etc.

Há inúmeros servidores MCP para os programadores, tais como Github, Postgres, Jira, e muito mais. A forma de acesso a esses servidores varia, alguns são remotos (há uma URL), outros devem ser baixados e instalados localmente.

### ChatGPT, Claude

Os bots como o ChatGPT, Claude, etc., em suas versões "client" (baixadas) podem se conectar a servidores MCPs, tanto remotos, quanto locais. Assim, é possível criar um servidor MCP e permitir que as pessoas interajam com eles usando os seus próprios chatbots. Isso cria um novo paradigma de programação, em que aplicações podem ser distribuídas sem front end. Basta desenvolver o servidor MCP e as pessoas usam os chatbots como front end, interagindo em linguagem natural.

## Dicas finais

### OpenAI API

Dois detalhes importantes ao se usar a API da OpenAI para desenvolver clients de MCPs:

1. Apenas `responses` tem suporte para MCP. Não dá para usar `chat.completion` e tampouco `assistants`.
2. `responses` suporta apenas "tools". O protocolo MCP tem também "resources" e "prompts", mas não dá para usar com `responses`.

### Indo além

Servidores MCP, como o nome diz ("Model Context Protocol") foram concebidos para adicionar mais contexto às chamadas de IA. Ou seja, foram concebidos na visão "READ", qual seja, ler dados em determinados serviço e adicionar esses dados no contexto do LLM.

Todavia, servidores MCP podem também ser concebidos na visão "WRITE". Eles podem, por exemplo, gravar dados em um banco de dados, alterar registros, mover recursos e realizar qualquer tipo de ação a critério do programador.

Um servidor MCP pode também executar um outro agente de IA. Ou seja, um agente de IA pode ser distribuído para consumo de outros agentes de IA através do MCP.

Essas visões vão muito além do que simplesmente adicionar contexto e permitem cenários de uso altamente complexos e sofisticados.

### Saiba mais

[https://mcpservers.org](https://mcpservers.org)
[https://remote-mcp.com](https://remote-mcp.com)
[https://mcpmarket.com](https://mcpmarket.com)
[https://pulsemcp.com](https://pulsemcp.com)
[https://smithery.ai](https://smithery.ai)

[https://docs.claude.com/en/docs/agents-and-tools/remote-mcp-servers](https://docs.claude.com/en/docs/agents-and-tools/remote-mcp-servers)
[https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
[https://github.com/jaw9c/awesome-remote-mcp-servers](https://github.com/jaw9c/awesome-remote-mcp-servers)

.
