# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание проекта

AI SRE-DevOps Agent - это веб-приложение на базе FastAPI и WebSocket, которое взаимодействует с Anthropic Claude API для автоматизации SRE и DevOps задач. Агент создаёт инфраструктурные проекты (Kubernetes, Terraform, Ansible, CI/CD), автоматизирует развёртывание, настраивает мониторинг и валидирует конфигурации.

## Основные команды

### Запуск сервера

```bash
# Запуск с автоперезагрузкой (для разработки)
python main.py

# Запуск без автоперезагрузки (для стабильного WebSocket соединения)
python run.py

# Или через uvicorn напрямую
uvicorn main:app --host localhost --port 8000 --reload
```

### Установка зависимостей

```bash
# Основной проект
pip install -r requirements.txt

# Подпроект support-agent
pip install -r ai/support-agent/requirements.txt
```

### Переменные окружения

Создайте файл `.env` в корне проекта со следующими переменными:
```
ANTHROPIC_API_KEY=your_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

## Архитектура проекта

### Основные модули

**main.py** - Основной сервер FastAPI:
- WebSocket endpoint на `/ws` для чата с AI агентом
- Роутер `/` для веб-интерфейса (index.html)
- Управление историей чата с ограничением до 10 сообщений
- Обработка вызовов инструментов (tools) и их результатов
- Логика обрезки истории для избежания ошибок связи `tool_use` -> `tool_result`

**config.py** - Конфигурация:
- Загрузка переменных окружения (API ключи)
- Системный промпт для Claude с поддержкой DevOps задач:
  - 7 типов проектов (Kubernetes, Terraform, Ansible, Мониторинг, CI/CD, Docker Compose, Автоматизация)
  - Шаблоны для всех типов конфигураций
  - Best practices для безопасности и производительности
- Определение доступных инструментов (tools):
  - `run_command` - выполнение команд в PowerShell
  - `save_code` - сохранение файлов с отображением размера
  - `validate_project` - проверка наличия обязательных файлов
  - `validate_yaml` - проверка синтаксиса YAML файлов (NEW!)
  - `validate_terraform` - валидация Terraform конфигурации (NEW!)
  - `lint_dockerfile` - проверка Dockerfile на best practices (NEW!)
  - `search` - поиск через Serper API
  - `fetch_page` - парсинг веб-страниц через Playwright

**function.py** - Реализация инструментов:
- `save_code()` - создаёт файлы в директории `./ai/` с отображением размера файла
  - Автоматически создаёт нужные папки
  - Возвращает размер созданного файла для контроля
- `validate_project()` - НОВАЯ ФУНКЦИЯ для валидации проектов
  - Проверяет наличие всех 8 обязательных файлов
  - Отображает размер каждого файла
  - Выдаёт детальный отчёт с указанием отсутствующих файлов
- `run_command()` - выполняет команды в PowerShell с рабочей директорией `./ai/`
  - Специальная обработка `mkdir` и `cd` через Python
- `search()` - интеграция с Google Serper API для поиска
- `fetch_page()` - использует Playwright для парсинга страниц с обходом детектирования ботов
  - Сохраняет скриншоты в `./ai/screenshot.png`
  - Удаляет script, style, svg теги для чистого контента

**index.html** - Веб-интерфейс:
- WebSocket клиент для общения с сервером на `ws://localhost:8000/ws`
- Автоматическое переподключение при разрыве соединения
- Индикаторы статуса подключения и печати

### Директории

- `./ai/` - Рабочая директория для создаваемых агентом проектов
- `./ai/support-agent/` - Подпроект телеграм-бота (отдельные зависимости)
- `__pycache__/` - Кэш Python

### Особенности реализации

1. **Управление историей чата**: функция `trim_chat_history()` в main.py умно обрезает историю, сохраняя связи между вызовами инструментов и их результатами

2. **Обработка инструментов**: все вызовы инструментов выполняются последовательно, результаты группируются и отправляются одним сообщением обратно в Claude

3. **Работа с файлами**: все пути относительно директории `./ai/`, автоматическое создание вложенных директорий

4. **Обход детектирования**: Playwright настроен с кастомным user-agent и скриптами для обхода обнаружения автоматизации

5. **Обработка ошибок**: специальная обработка rate limit ошибок (429) и ошибок валидации tool_use/tool_result

## Требования к окружению

- **ОС**: Windows 11
- **Shell**: PowerShell
- **Python**: 3.13.7
- **Модель Claude**: claude-sonnet-4-20250514

## Структура проектов, создаваемых агентом

Агент следует строгому шаблону при создании новых проектов:
```
project_name/
├── src/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
├── .gitignore
├── .dockerignore
├── Dockerfile
├── .env.example
└── README.md
```

Все файлы создаются через `save_code()` по одному, затем устанавливаются зависимости через `run_command()`.

## Последние обновления (02.10.2025)

### Обновление: Переход к SRE-DevOps помощнику

Проект был полностью переделан из Python-помощника в SRE-DevOps помощника.

### Внесённые изменения:

#### 1. Новый SYSTEM_PROMPT (config.py) для DevOps задач
- ✅ 7 типов проектов: Kubernetes, Terraform, Ansible, Мониторинг, CI/CD, Docker Compose, Автоматизация
- ✅ Шаблоны конфигураций для каждого типа проекта
- ✅ Best practices для безопасности (secret management, RBAC)
- ✅ Акцент на production-ready конфигурации

#### 2. Новые DevOps инструменты (function.py)
- ✅ `validate_yaml()` - проверка синтаксиса YAML файлов (K8s манифесты, Ansible playbooks)
- ✅ `validate_terraform()` - валидация Terraform с использованием terraform fmt и terraform validate
- ✅ `lint_dockerfile()` - проверка Dockerfile на соответствие best practices

#### 3. Расширенная поддержка файлов (main.py)
- ✅ Эмодзи для DevOps файлов: ⚙️ YAML, 🔧 Terraform, 📜 Shell scripts
- ✅ Обработка всех новых инструментов в WebSocket
- ✅ Улучшенные уведомления о процессе валидации

#### 4. Обновлённая функция validate_project (function.py)
- ✅ Сохранена для обратной совместимости с Python проектами
- ✅ Может быть адаптирована под разные типы проектов

### Возможности SRE-DevOps Agent:

**Kubernetes:**
- Создание Deployments, Services, ConfigMaps, Secrets
- Ingress конфигурации
- Kustomization файлы
- Валидация YAML синтаксиса

**Terraform:**
- Создание модулей инфраструктуры
- Variables, outputs, providers
- Валидация синтаксиса и форматирования
- Проверка terraform validate

**Ansible:**
- Плейбуки и роли
- Inventory файлы
- Ansible.cfg конфигурация
- Валидация YAML

**Мониторинг:**
- Prometheus конфигурации и правила алертов
- Grafana dashboards
- Docker Compose для стека мониторинга

**CI/CD:**
- GitHub Actions workflows
- GitLab CI/CD pipelines
- Jenkins файлы
- Скрипты сборки и развёртывания

**Безопасность:**
- Только .example файлы для секретов
- RBAC конфигурации
- Следование best practices

### Как работает DevOps Agent:

1. Определяет тип проекта (или спрашивает у пользователя)
2. Создаёт файлы в соответствии с шаблоном проекта
3. Валидирует конфигурации (YAML, Terraform, Dockerfile)
4. Предоставляет инструкции по развёртыванию
5. Следует принципам Infrastructure as Code

### Требования для полной функциональности:

- **Terraform** (опционально) - для валидации Terraform проектов
- **PyYAML** - для валидации YAML файлов (добавить в requirements.txt)
