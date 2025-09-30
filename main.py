import json
from config import HELICONE_API_KEY, SYSTEM_PROMPT
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from loguru import logger
#from function import run_command, save_code, search, fetch_page
from openai import AsyncOpenAI

app = FastAPI()


openai_client = AsyncOpenAI(
    base_url="https://oai.helicone.ai/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {HELICONE_API_KEY}"
    }
)

@app.get("/")
async def index():
    with open("index.html", "r", encoding="UTF-8") as f:
        html = f.read()

    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = [{
        "role": "system",
        "content": SYSTEM_PROMPT,

    }]

    try:
        while True:
            data_frontend = await websocket.receive_text()
            user_input = data_frontend.strip()
            logger.debug(f"Сообщение от фронта: {user_input}")

            chat_history.append({
                "role": "user",
                "content": user_input
            })


            ai_response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_history,
                )

            ai_message = ai_response.choices[0].message

            chat_history.append(ai_response.to_dict())

            await websocket.send_text(json.dumps({
                "role": "assistant",
                "content": ai_message.content
            }))


    except WebSocketDisconnect:
        logger.error("Клиент отсоединился")


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)


