import os
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import Groq

load_dotenv()

API_GROQ = os.getenv("GROQ_API_KEY")

if not API_GROQ:
    raise RuntimeError(
        "GROQ_API_KEY não foi encontrada no arquivo .env"
    )

client = Groq(api_key=API_GROQ)
MODELO = "openai/gpt-oss-120b"

app = FastAPI(
    title="Kamba IA API",
    description="Backend do Kamba IA para o KwanzaMeter",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

SYSTEM_PROMPT = """
Tu és o Kamba IA, o assistente financeiro integrado
numa aplicação chama KwanzaMeter.

REGRAS:
-Responde sempre em português.
-Usa linguagem simples, clara e natural, como angolano.
-Explica assuntos financeiros de forma fácil.
-Ajuda principalmente com finanças pessoais.
-Podes explicar:
    -poupança;
    -orçamento;
    -receitas;
    -despesas;
    -transações;
    -saldo;
    -metas financeiras;
    -câmbio;
    -organização financeira;
-Quando não souberes alguma informação, diz claramente que não sabes.
-Não inventes valores, taxas ou informações.
-Mantém o contexto da conversa.
-Responde de forma útil e relativamente curta.
-Quando o utilizador perguntar algo que não esteja relacionado a finanças,
diz que não foste programado para isso e lembra que o teu principal objetivo
é ajudar com finanças pessoais.
"""

Role = Literal["user", "assistant"]

class Mensagem(BaseModel):
    role: Role
    content: str = Field(
        min_length=1,
        max_length=10000
    )

class KambaRequest(BaseModel):
    conversa_id: str = Field(
        min_length=1,
        max_length=100
    )
    
    mensagem: str = Field(
        min_length=1,
        max_length=100000
    )

class KambaResponse(BaseModel):
    conversa_id: str
    resposta: str

# Historico das conversas

conversas: dict[str, List[dict]] = {}

def criar_conversa(conversa_id: str):
    """
    Criar uma conversa quando ela ainda não existe.
    """
    
    if conversa_id not in conversas:

        conversas[conversa_id] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

def limpar_conversa(conversa_id: str):
    """
    Remove uma conversa do histórico.
    """
    if conversa_id in conversas:
        del conversas[conversa_id]

def pergunta_groq(
    historico: List[dict]
) -> str:
    
    try:
        resposta = client.chat.completions.create(
            model=MODELO,
            messages=historico,
            temperature=0.7,
            max_completion_tokens=2048
        )
        
        texto = resposta.choices[0].message.content
        
        if not texto:
            return "Não coonsegui gerar um resposta."
        return texto.strip()
    except Exception as erro:
        print("ERRO GROQ:", erro)
        
        raise HTTPException(
            status_code=502,
            detail="Não foi possível obter resposta do Kamba IA."
        )

@app.post(
    "/kamba",
    response_model=KambaResponse
)

async def kamba(request: KambaRequest):
    conversa_id = request.conversa_id
    
    criar_conversa(conversa_id)
    historico = conversas[conversa_id]
    
    historico.append(
        {
            "role": "user",
            "content": request.mensagem
        }
    )
    
    resposta = pergunta_groq(historico)
    
    historico.append(
        {
            "role": "assistant",
            "content": resposta
        }
    )
    
    return KambaResponse(
        conversa_id=conversa_id,
        resposta=resposta
    )
    
@app.delete("/kamba/{conversa_id}")
async def apagar_conversa(conversa_id: str):
    if conversa_id in conversas:
        limpar_conversa(conversa_id)
        
        return{
            "sucesso": True,
            "mensagem": "Conversa apagada."
        }
    
    return {
        "sucesso": True,
        "mensagem": "A conversa não existia."
    }

@app.get("/")
async def inicio():
    
    return {
        "app": "Kamba IA",
        "status": "online",
        "modelo": MODELO
    }

@app.get("/health")
async def health():
    
    return {
        "status": "ok"
    }