
import json
from config import ANTHROPIC_API_KEY, SYSTEM_PROMPT, TOOLS
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from loguru import logger
from function import run_command, save_code, search, fetch_page, validate_project, validate_yaml, validate_terraform, lint_dockerfile
from anthropic import AsyncAnthropic

app = FastAPI()

anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


@app.get("/")
async def index():
    with open("index.html", "r", encoding="UTF-8") as f:
        html = f.read()
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = []
    
    # Функция для ограничения истории чата
    def trim_chat_history(history, max_messages=20):
        """
        Умно обрезает историю, сохраняя связи tool_use -> tool_result
        """
        if len(history) <= max_messages:
            return history
        
        # Оставляем последние сообщения
        trimmed = history[-max_messages:]
        
        # Проверяем первое сообщение - если это tool_result, удаляем его
        while trimmed and trimmed[0].get("role") == "user":
            content = trimmed[0].get("content", [])
            # Если это список с tool_result, удаляем
            if isinstance(content, list) and any(
                isinstance(item, dict) and item.get("type") == "tool_result" 
                for item in content
            ):
                trimmed.pop(0)
            else:
                break
        
        return trimmed

    try:
        while True:
            data_frontend = await websocket.receive_text()
            user_input = data_frontend.strip()
            logger.debug(f"Сообщение от фронта: {user_input}")

            chat_history.append({
                "role": "user",
                "content": user_input
            })

            while True:
                try:
                    # Ограничиваем историю перед запросом
                    trimmed_history = trim_chat_history(chat_history, max_messages=10)
                    
                    # Логируем для отладки
                    logger.debug(f"История содержит {len(trimmed_history)} сообщений")
                    for i, msg in enumerate(trimmed_history):
                        logger.debug(f"  [{i}] role={msg.get('role')}, content_type={type(msg.get('content'))}")
                    
                    ai_response = await anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=3000,
                        system=SYSTEM_PROMPT,
                        messages=trimmed_history,
                        tools=TOOLS,
                        tool_choice={"type": "auto"}  # Явно указываем auto без parallel
                    )

                    # Добавляем ответ ассистента в историю
                    assistant_message = {
                        "role": "assistant",
                        "content": ai_response.content
                    }
                    chat_history.append(assistant_message)

                    # Проверяем, есть ли вызовы инструментов
                    tool_calls = [block for block in ai_response.content if block.type == "tool_use"]

                    if not tool_calls:
                        # Если нет вызовов инструментов, отправляем текстовый ответ
                        text_content = next((block.text for block in ai_response.content if hasattr(block, 'text')), "")
                        if text_content:
                            await websocket.send_text(json.dumps({
                                "role": "assistant",
                                "content": text_content
                            }))
                        break

                    # Уведомляем пользователя о выполнении функций
                    tool_names = [tc.name for tc in tool_calls]
                    await websocket.send_text(json.dumps({
                        "role": "system",
                        "content": f"⚙️ Выполняю действия: {', '.join(tool_names)}..."
                    }))

                    # Выполняем все вызовы инструментов
                    tool_results = []
                    for tool_call in tool_calls:
                        func_name = tool_call.name
                        args = tool_call.input

                        # Подробное логирование аргументов
                        logger.info(f"Вызов функции: {func_name}")
                        logger.debug(f"  Аргументы: {args}")
                        logger.debug(f"  Тип аргументов: {type(args)}")
                        logger.debug(f"  Ключи: {list(args.keys()) if isinstance(args, dict) else 'N/A'}")

                        result = ""

                        try:

                            if func_name == "run_command":
                                if "command" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'command'"
                                else:
                                    input_str = args.get("input_str", "")
                                    result = run_command(args["command"], input_str)
                            elif func_name == "save_code":
                                if "code" not in args or "filename" not in args:
                                    missing = []
                                    if "code" not in args:
                                        missing.append("code (содержимое файла)")
                                    if "filename" not in args:
                                        missing.append("filename (путь к файлу)")
                                    result = f"❌ КРИТИЧЕСКАЯ ОШИБКА: Пропущены обязательные параметры: {', '.join(missing)}. Получены только: {list(args.keys())}. ВСЕГДА передавай ОБА параметра в save_code!"
                                else:
                                    result = save_code(args["code"], args["filename"])
                                    # Уведомляем о создании файла с эмодзи прогресса
                                    file_type = "📄"
                                    if args["filename"].endswith(".py"):
                                        file_type = "🐍"
                                    elif args["filename"].endswith("README.md"):
                                        file_type = "📖"
                                    elif args["filename"].endswith("Dockerfile"):
                                        file_type = "🐳"
                                    elif args["filename"].endswith(".gitignore") or args["filename"].endswith(".dockerignore") or args["filename"].endswith(".terraformignore"):
                                        file_type = "🚫"
                                    elif args["filename"].endswith("requirements.txt"):
                                        file_type = "📦"
                                    elif args["filename"].endswith((".yaml", ".yml")):
                                        file_type = "⚙️"
                                    elif args["filename"].endswith(".tf") or args["filename"].endswith(".tfvars"):
                                        file_type = "🔧"
                                    elif args["filename"].endswith((".sh", ".bash")):
                                        file_type = "📜"
                                    elif args["filename"].endswith(".json"):
                                        file_type = "🔧"
                                    
                                    await websocket.send_text(json.dumps({
                                        "role": "system",
                                        "content": f"{file_type} Создан файл: {args['filename']}"
                                    }))
                            elif func_name == "validate_project":
                                if "project_name" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'project_name'"
                                else:
                                    result = validate_project(args["project_name"])
                                    # Отправляем отчёт валидации пользователю
                                    await websocket.send_text(json.dumps({
                                        "role": "system",
                                        "content": f"📋 Валидация проекта {args['project_name']}"
                                    }))
                            elif func_name == "search":
                                if "query" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'query'"
                                else:
                                    result = search(args["query"])
                            elif func_name == "fetch_page":
                                if "url" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'url'"
                                else:
                                    result = await fetch_page(args["url"])
                            elif func_name == "validate_yaml":
                                if "filepath" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'filepath'"
                                else:
                                    result = validate_yaml(args["filepath"])
                                    await websocket.send_text(json.dumps({
                                        "role": "system",
                                        "content": f"📋 Валидация YAML: {args['filepath']}"
                                    }))
                            elif func_name == "validate_terraform":
                                if "project_path" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'project_path'"
                                else:
                                    result = validate_terraform(args["project_path"])
                                    await websocket.send_text(json.dumps({
                                        "role": "system",
                                        "content": f"🔧 Валидация Terraform: {args['project_path']}"
                                    }))
                            elif func_name == "lint_dockerfile":
                                if "filepath" not in args:
                                    result = "❌ Ошибка: отсутствует параметр 'filepath'"
                                else:
                                    result = lint_dockerfile(args["filepath"])
                                    await websocket.send_text(json.dumps({
                                        "role": "system",
                                        "content": f"🐳 Линтинг Dockerfile: {args['filepath']}"
                                    }))
                            else:
                                result = f"Неизвестная функция {func_name}"

                        except Exception as e:
                            logger.error(f"Ошибка вызова функции {func_name}: {str(e)}")
                            result = f"Ошибка вызова функции {func_name}: {str(e)[:2000]}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": result
                        })

                    # Добавляем результаты инструментов в историю
                    chat_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Ошибка при обработке запроса: {error_message}")
                    
                    # Специальная обработка rate limit
                    if "rate_limit_error" in error_message or "429" in error_message:
                        await websocket.send_text(json.dumps({
                            "role": "assistant",
                            "content": "⏳ Достигнут лимит запросов API. Подождите 1 минуту и попробуйте снова."
                        }))
                    # Обработка ошибок валидации (tool_use/tool_result)
                    elif "invalid_request_error" in error_message or "tool_use_id" in error_message:
                        logger.warning("Сброс истории из-за ошибки валидации")
                        # Очищаем историю, оставляя только последнее сообщение пользователя
                        user_messages = [msg for msg in chat_history if msg.get("role") == "user" and isinstance(msg.get("content"), str)]
                        if user_messages:
                            chat_history = [user_messages[-1]]
                        else:
                            chat_history = []
                        
                        await websocket.send_text(json.dumps({
                            "role": "assistant",
                            "content": "🔄 История чата сброшена из-за ошибки. Повторите ваш запрос."
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "role": "assistant",
                            "content": f"❌ Произошла ошибка: {error_message[:500]}"
                        }))
                    break

    except WebSocketDisconnect:
        logger.error("Клиент отсоединился")
    except Exception as e:
        logger.error(f"Критическая ошибка в WebSocket: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)