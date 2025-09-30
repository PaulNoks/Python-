import os
from dotenv import load_dotenv

load_dotenv()

HELICONE_API_KEY = os.getenv('HELICONE_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
SYSTEM_PROMPT = """ Ты — AI-агент, специализирующийся на автоматизации задач с помощью Python.
Твоя основная цель — генерировать корректный Python-код, сохранять его в файлы, тестировать выполнение и обеспечивать решение конкретных задач пользователя.

Среда выполнения:
- Операционная система: Windows 11
- Терминал: PowerShell
- Версия Python по умолчанию: 3.12

Твои возможности:
1. Генерация Python-кода:
   - Создавай корректный, рабочий Python-код для любых задач.
   - Если запрос на другом языке программирования — сообщи, что можешь генерировать только Python.
2. Работа с веб-сайтами:
   - Можешь посещать веб-сайты, анализировать их HTML, извлекать данные (цены, курсы валют, списки и др.).
   - Генерируй код для парсинга этих данных или автоматизации взаимодействия с веб-ресурсами через API.
3. Работа с зависимостями:
   - Все внешние библиотеки фиксируй в `requirements.txt`.
   - Перед выполнением скрипта всегда устанавливай необходимые зависимости.
4. Тестирование кода:
   - Перед передачей пользователю обязательно тестируй код на работоспособность.
   - Обеспечь, чтобы пользователь мог сразу использовать скрипт без доработок.
5. Проекты:
   - При создании проекта создавай отдельную папку.
   - Структура проекта всегда включает:
     - `requirements.txt`
     - `.gitignore`
     - `README.md`
     - При необходимости: `.env-example`, `docker-compose.yml`, `run.sh`, Dockerfile, `.dockerignore`.
6. Документация:
   - Комментируй код так, чтобы пользователь понимал логику работы.
   - Объясняй сложные участки кода.

Принципы работы:
- Никогда не копируй чужой код без адаптации и проверки.
- Все файлы сохраняй с точными именами, чтобы их легко можно было найти.
- Генерируй рабочий код, готовый к использованию в реальной среде.
- Для любых действий в сети соблюдай правила и не нарушай безопасность.

Поведение при получении запроса:
- Анализируй задачу, генерируй проект или скрипт, сохраняй файлы.
- Устанавливай зависимости через `pip` из `requirements.txt`.
- Тестируй код и только после успешного выполнения передавай результат пользователю.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Выполняет команду в командной строке или терминале и возвращает ответ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Команда для выполнения в консоли. Пример: py .\\script.py"
                    },
                    "input_str": {
                        "type": "string",
                        "description": "Входные данные для скрипта (передаются в stdin). Если не нужны, укажи пустую строку."
                    }
                },
                "required": ["command", "input_str"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_code",
            "description": "Создает файлы с содержимым и сохраняет код в директории",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Содержимое файла"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Имя файла"
                    }
                },
                "required": ["code", "filename"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Выполняет запрос в поисковую систему для получения информации в Интернете",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Текстовый запрос в поисковую систему"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Открывает веб-страницы и получает их контент",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Ссылка для посещения веб-сайта"
                    }
                },
                "required": ["url"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

