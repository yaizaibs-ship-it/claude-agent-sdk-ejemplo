"""
Servidor web mínimo con FastAPI para usar los agentes desde una interfaz propia.

Arranque:
    uvicorn server:app --reload

Prueba:
    curl -X POST http://localhost:8000/chat \
         -H "Content-Type: application/json" \
         -d '{"mensaje": "¿Qué hora es en Madrid?", "ejemplo": 2}'
"""

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query

# Reutilizamos la configuración de los ejemplos (también carga el .env)
from agente_basico import opciones_ejemplo_1, opciones_ejemplo_2, opciones_ejemplo_3

app = FastAPI(title="Agente Claude - ejemplo")

# Permite llamar a la API desde una web local (ajusta los orígenes en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yaizaibs-ship-it.github.io",  # la sala de agentes publicada en GitHub Pages
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

OPCIONES = {1: opciones_ejemplo_1, 2: opciones_ejemplo_2, 3: opciones_ejemplo_3}


class ChatRequest(BaseModel):
    mensaje: str
    ejemplo: Literal[1, 2, 3] = 1


class ChatResponse(BaseModel):
    respuesta: str
    texto_completo: list[str]
    coste_usd: float | None = None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    textos: list[str] = []
    resultado = ""
    coste = None
    try:
        async for message in query(prompt=req.mensaje, options=OPCIONES[req.ejemplo]()):
            if isinstance(message, AssistantMessage) and not message.parent_tool_use_id:
                textos.extend(b.text for b in message.content if isinstance(b, TextBlock))
            elif isinstance(message, ResultMessage):
                resultado = message.result or ""
                coste = message.total_cost_usd
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el agente: {e}")
    return ChatResponse(respuesta=resultado or "\n".join(textos), texto_completo=textos, coste_usd=coste)


@app.get("/")
async def estado() -> dict:
    return {"estado": "ok", "endpoint": "POST /chat"}
