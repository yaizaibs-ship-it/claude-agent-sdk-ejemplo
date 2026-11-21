"""
Ejemplos básicos con el Claude Agent SDK (Python).

Uso:
    python agente_basico.py 1   # Agente simple con system_prompt, sin herramientas
    python agente_basico.py 2   # Agente con una herramienta propia (hora_actual)
    python agente_basico.py 3   # Director que delega en dos subagentes (redactor y revisor)
"""

import asyncio
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

# Carga ANTHROPIC_API_KEY desde el archivo .env (si existe)
load_dotenv()


# ---------------------------------------------------------------------------
# Utilidad común: ejecuta el agente e imprime SOLO el texto que escribe
# ---------------------------------------------------------------------------
async def ejecutar(prompt: str, options: ClaudeAgentOptions) -> str:
    """Lanza el agente, imprime su texto y devuelve el resultado final."""
    resultado = ""
    async for message in query(prompt=prompt, options=options):
        # Los mensajes del asistente contienen bloques; solo nos interesan los de texto.
        # parent_tool_use_id indica que el mensaje viene de dentro de un subagente:
        # lo saltamos para mostrar únicamente lo que dice el agente principal.
        if isinstance(message, AssistantMessage) and not message.parent_tool_use_id:
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        # El ResultMessage llega al final con el resultado y el coste.
        elif isinstance(message, ResultMessage):
            resultado = message.result or ""
            if message.is_error:
                print(f"\n[Error del agente: {message.subtype}]")
    return resultado


# ---------------------------------------------------------------------------
# Ejemplo 1: agente simple con system_prompt, sin herramientas
# ---------------------------------------------------------------------------
def opciones_ejemplo_1() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=(
            "Eres un asistente creativo que responde en español, "
            "de forma breve y con un toque cercano."
        ),
        allowed_tools=[],  # sin herramientas
        max_turns=1,
    )


async def ejemplo_1() -> None:
    await ejecutar(
        "Dame tres ideas de nombre para una tienda de ropa vintage de fútbol.",
        opciones_ejemplo_1(),
    )


# ---------------------------------------------------------------------------
# Ejemplo 2: agente con una herramienta propia creada con @tool
# ---------------------------------------------------------------------------
@tool(
    "hora_actual",
    "Devuelve la fecha y la hora actuales en una zona horaria (por defecto, Europe/Madrid).",
    {"zona_horaria": str},
)
async def hora_actual(args: dict) -> dict:
    zona = args.get("zona_horaria") or "Europe/Madrid"
    try:
        ahora = datetime.now(ZoneInfo(zona))
    except Exception:
        return {
            "content": [{"type": "text", "text": f"Zona horaria no válida: {zona}"}],
            "is_error": True,
        }
    texto = ahora.strftime(f"%d/%m/%Y %H:%M:%S ({zona})")
    return {"content": [{"type": "text", "text": texto}]}


# Servidor MCP en el propio proceso que expone la herramienta.
servidor_utilidades = create_sdk_mcp_server(
    name="utilidades",
    version="1.0.0",
    tools=[hora_actual],
)


def opciones_ejemplo_2() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="Eres un asistente que responde en español. Usa tus herramientas cuando las necesites.",
        mcp_servers={"utilidades": servidor_utilidades},
        # Formato del nombre permitido: mcp__<servidor>__<herramienta>
        allowed_tools=["mcp__utilidades__hora_actual"],
        max_turns=3,
    )


async def ejemplo_2() -> None:
    await ejecutar(
        "¿Qué hora es ahora en Madrid y en Nueva York?",
        opciones_ejemplo_2(),
    )


# ---------------------------------------------------------------------------
# Ejemplo 3: un "director" que delega en dos subagentes
# ---------------------------------------------------------------------------
# Nota: en las versiones actuales del SDK la herramienta para invocar subagentes
# se llama "Agent" (antes se llamaba "Task").
def opciones_ejemplo_3() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=(
            "Eres el director de un pequeño equipo creativo. No escribes tú el eslogan: "
            "primero pides al subagente 'redactor' que proponga eslóganes, después pasas "
            "esas propuestas al subagente 'revisor' y esperas su informe. Termina mostrando "
            "el eslogan final elegido y una frase explicando por qué. Responde en español."
        ),
        allowed_tools=["Agent"],
        agents={
            "redactor": AgentDefinition(
                description="Redactor publicitario. Úsalo para escribir propuestas de eslogan.",
                prompt=(
                    "Eres un redactor publicitario. Escribe 3 eslóganes cortos (máximo 8 palabras), "
                    "memorables y en español para el producto que te indiquen."
                ),
                tools=[],
                background=False,  # el director espera su respuesta
            ),
            "revisor": AgentDefinition(
                description="Revisor creativo. Úsalo para evaluar eslóganes y elegir el mejor.",
                prompt=(
                    "Eres un director creativo exigente. Revisa los eslóganes que recibes, "
                    "corrige errores, elige el mejor y explica brevemente por qué."
                ),
                tools=[],
                background=False,
            ),
        },
        max_turns=10,
    )


async def ejemplo_3() -> None:
    await ejecutar(
        "Crea y revisa un eslogan para una cafetería de especialidad en el centro de Valencia.",
        opciones_ejemplo_3(),
    )


# ---------------------------------------------------------------------------
EJEMPLOS = {"1": ejemplo_1, "2": ejemplo_2, "3": ejemplo_3}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in EJEMPLOS:
        print(__doc__)
        sys.exit(1)
    asyncio.run(EJEMPLOS[sys.argv[1]]())


if __name__ == "__main__":
    main()
