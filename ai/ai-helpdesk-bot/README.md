# AI Helpdesk Telegram Bot

Умный телеграм-бот для службы поддержки с использованием искусственного интеллекта (OpenAI GPT).

## Возможности

- ✅ Автоматические ответы на вопросы пользователей
- ✅ Интеграция с OpenAI GPT для генерации умных ответов
- ✅ Сохранение контекста беседы
- ✅ Отправка в техподдержку сложных вопросов
- ✅ Логирование всех обращений
- ✅ Docker-контейнеризация
- ✅ Простая настройка через переменные окружения

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd ai-helpdesk-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Заполните ваши токены в файле `.env`:
- `TELEGRAM_BOT_TOKEN` - токен вашего бота от @BotFather
- `OPENAI_API_KEY` - ваш API ключ OpenAI

## Настройка

### Получение Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### Получение OpenAI API Key
1. Зарегистрируйтесь на [OpenAI Platform](https://platform.openai.com/)
2. Перейдите в раздел API Keys
3. Создайте новый API ключ
4. Скопируйте ключ в `.env`

## Запуск

### Локальный запуск
```bash
python src/main.py
```

### Запуск в Docker
```bash
# Сборка образа
docker build -t ai-helpdesk-bot .

# Запуск контейнера
docker run -d --env-file .env --name ai-helpdesk-bot ai-helpdesk-bot
```

### Запуск с docker-compose
```bash
docker-compose up -d
```

## Команды бота

- `/start` - Начало работы с ботом
- `/help` - Получить справку
- `/support` - Связаться с технической поддержкой
- `/clear` - Очистить контекст беседы

## Структура проекта

```
ai-helpdesk-bot/
├── src/
│   ├── __init__.py        # Инициализация пакета
│   └── main.py           # Основной код бота
├── requirements.txt      # Зависимости Python
├── .env.example         # Пример настроек окружения
├── .env                 # Ваши настройки (создать самостоятельно)
├── .gitignore          # Исключения для Git
├── .dockerignore       # Исключения для Docker
├── Dockerfile          # Конфигурация Docker
└── README.md           # Этот файл
```

## Кастомизация

Вы можете настроить поведение бота, изменив параметры в файле `.env`:

- `LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `AI_MODEL` - модель OpenAI для использования
- `AI_TEMPERATURE` - температура генерации (0.0-2.0)

## Разработка

Для разработки рекомендуется:

1. Создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Запустить в режиме разработки:
```bash
python src/main.py
```

## Поддержка

Если у вас возникли вопросы или проблемы:
- Создайте issue в репозитории
- Проверьте логи бота
- Убедитесь, что все токены настроены правильно

## Лицензия

MIT License