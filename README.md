# Claude Agent SDK · Proyecto de ejemplo (Python)

Proyecto mínimo para aprender a crear agentes con el [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) en Python. Incluye tres ejemplos de consola y un pequeño servidor web con FastAPI para conectar los agentes a una interfaz propia.

| Archivo | Qué hace |
| --- | --- |
| `agente_basico.py` | Tres ejemplos que se eligen por argumento (1, 2 o 3) |
| `server.py` | API con FastAPI y un endpoint `POST /chat` |
| `requirements.txt` | Dependencias |
| `.env.example` | Plantilla para tu clave de API |

## Los tres ejemplos

1. **Agente simple**: un `system_prompt` y ninguna herramienta.
2. **Agente con herramienta propia**: `hora_actual`, creada con el decorador `@tool` y servida con `create_sdk_mcp_server`. El nombre que se permite en `allowed_tools` sigue el formato `mcp__<servidor>__<herramienta>`, en este caso `mcp__utilidades__hora_actual`.
3. **Director con subagentes**: un agente principal que solo tiene la herramienta `Agent` y delega en dos subagentes definidos con `AgentDefinition`: un **redactor**, que propone eslóganes, y un **revisor**, que elige el mejor.

> **Nota:** en versiones antiguas del SDK, la herramienta para invocar subagentes se llamaba `Task`. Ahora se llama `Agent`, y es la que usa este proyecto.

Todos usan `query()`, `ClaudeAgentOptions`, `AssistantMessage`, `TextBlock` y `ResultMessage`, y muestran solo el texto del agente.

## Requisitos

- Python 3.10 o superior
- Una clave de API de Anthropic ([console.anthropic.com](https://console.anthropic.com/))

No hace falta instalar Node ni Claude Code: el paquete `claude-agent-sdk` ya incluye todo lo que necesita.

## Instalación

```bash
git clone https://github.com/yaizaibs-ship-it/claude-agent-sdk-ejemplo.git
cd claude-agent-sdk-ejemplo

python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Configurar la clave de API

```bash
cp .env.example .env
```

Abre `.env` y pega tu clave:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Los scripts cargan el `.env` automáticamente con `python-dotenv`. El `.gitignore` ya excluye `.env`, así que tu clave no se subirá a GitHub.

## Ejecutar los ejemplos

```bash
python agente_basico.py 1   # Agente simple
python agente_basico.py 2   # Herramienta hora_actual
python agente_basico.py 3   # Director + redactor + revisor
```

## Servidor web (FastAPI)

```bash
uvicorn server:app --reload
```

Prueba el endpoint:

```bash
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"mensaje": "¿Qué hora es en Madrid?", "ejemplo": 2}'
```

Respuesta:

```json
{
  "respuesta": "Ahora mismo en Madrid son las ...",
  "texto_completo": ["..."],
  "coste_usd": 0.01
}
```

`ejemplo` puede ser `1`, `2` o `3` y elige qué agente responde. Con el servidor en marcha, la documentación interactiva está en http://localhost:8000/docs.

## Sala de agentes (interfaz web)

En `docs/index.html` hay una interfaz lista para usar: una sala isométrica con los cinco agentes del proyecto. Está publicada con GitHub Pages en:

**https://yaizaibs-ship-it.github.io/claude-agent-sdk-ejemplo/**

| Agente | Qué hace | Ejemplo |
| --- | --- | --- |
| Sol | Asistente sin herramientas | 1 |
| Tic | Usa la herramienta `hora_actual` | 2 |
| Dora | Directora: delega con la herramienta `Agent` | 3 |
| Remo y Vera | Subagentes de Dora (redactor y revisora) | 3 |

- **Sin servidor**, la sala funciona en modo demo: las animaciones son reales, pero las respuestas son de ejemplo.
- **Con el servidor encendido** en tu ordenador (`uvicorn server:app`), la sala detecta `http://localhost:8000` y las respuestas vienen de Claude. La dirección del servidor se puede cambiar en la barra lateral.
- Chrome puede pedirte permiso para que la página acceda a dispositivos de tu red local: acéptalo, porque así la web publicada puede hablar con tu `localhost`.

## Conectarlo a una interfaz propia

Tu interfaz (una web en HTML/JS, React, una app no-code, etc.) solo tiene que hacer un `POST` a `/chat` y mostrar el campo `respuesta`:

```js
const res = await fetch("http://localhost:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ mensaje: "Hola", ejemplo: 1 }),
});
const data = await res.json();
console.log(data.respuesta);
```

Si la interfaz se sirve desde otro puerto o dominio, añádelo a `allow_origins` en `server.py` (CORS). La clave de API vive siempre en el servidor, nunca en el navegador.

## Documentación

- [Visión general del Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)
- [Referencia de Python](https://code.claude.com/docs/en/agent-sdk/python)
- [Subagentes](https://code.claude.com/docs/en/agent-sdk/subagents)
