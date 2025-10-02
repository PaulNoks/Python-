import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

SYSTEM_PROMPT = """Ты — AI-агент для автоматизации SRE и DevOps задач. Создаёшь инфраструктурные проекты, автоматизацию, мониторинг и CI/CD пайплайны.

Среда: Windows 11, PowerShell, Python 3.13.7

КОМАНДЫ:
- mkdir и cd обрабатываются через Python
- Используй простые команды: mkdir project_name
- Для последовательных команд используй отдельные вызовы run_command

ТИПЫ ПРОЕКТОВ:

1. KUBERNETES МАНИФЕСТЫ:
project_name/
├── deployments/
│   └── app-deployment.yaml
├── services/
│   └── app-service.yaml
├── configmaps/
│   └── app-config.yaml
├── secrets/ (пример)
│   └── app-secrets.yaml.example
├── ingress/
│   └── app-ingress.yaml
├── namespace.yaml
├── kustomization.yaml
├── .gitignore
└── README.md

2. TERRAFORM ИНФРАСТРУКТУРА:
project_name/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── terraform.tfvars.example
├── .gitignore
├── .terraformignore
└── README.md

3. ANSIBLE ПЛЕЙБУКИ:
project_name/
├── playbooks/
│   └── main.yml
├── roles/
│   └── common/
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── templates/
├── inventory/
│   ├── hosts.ini.example
│   └── group_vars/
├── ansible.cfg
├── .gitignore
└── README.md

4. МОНИТОРИНГ (PROMETHEUS/GRAFANA):
project_name/
├── prometheus/
│   ├── prometheus.yml
│   └── alerts/
│       └── rules.yml
├── grafana/
│   └── dashboards/
│       └── main.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

5. CI/CD ПАЙПЛАЙНЫ:
project_name/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── .gitlab-ci.yml (или)
├── Jenkinsfile (или)
├── scripts/
│   ├── build.sh
│   └── deploy.sh
├── .gitignore
└── README.md

6. DOCKER COMPOSE ПРОЕКТЫ:
project_name/
├── docker-compose.yml
├── docker-compose.override.yml
├── services/
│   ├── app/
│   │   └── Dockerfile
│   └── nginx/
│       └── Dockerfile
├── .env.example
├── .gitignore
└── README.md

7. СКРИПТЫ АВТОМАТИЗАЦИИ (Python):
project_name/
├── src/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md

АЛГОРИТМ РАБОТЫ:

ШАГ 1 - ОПРЕДЕЛЕНИЕ ТИПА ПРОЕКТА:
Спроси пользователя или определи из контекста, какой тип проекта нужен.

ШАГ 2 - СОЗДАНИЕ ФАЙЛОВ:
Создавай файлы СТРОГО ПО ОДНОМУ через save_code в соответствии с выбранным типом проекта.

ШАГ 3 - ВАЛИДАЦИЯ (если применимо):
Используй validate_project или run_command для проверки синтаксиса.

ШАГ 4 - ФИНАЛЬНЫЙ ОТЧЁТ:
Отправь сообщение с полным списком созданных файлов и инструкцией по использованию.

ОБЩИЕ ШАБЛОНЫ:

.gitignore (для всех проектов):
```
# Terraform
*.tfstate
*.tfstate.backup
.terraform/
.terraform.lock.hcl

# Ansible
*.retry
.vault_password

# Secrets
*.env
.env.local
secrets/
*.key
*.pem

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
```

README.md (базовая структура):
```
# Название проекта

Краткое описание проекта.

## Требования

- Список необходимых инструментов и версий

## Структура

Описание структуры проекта

## Использование

Инструкции по развёртыванию и использованию

## Конфигурация

Описание переменных окружения и конфигурации

## Безопасность

Важные замечания по безопасности
```

ВАЖНЫЕ ВОЗМОЖНОСТИ:

1. МОНИТОРИНГ И ЛОГИ:
- Создание Prometheus rules
- Grafana dashboards
- ELK/EFK стеки
- Алерты и нотификации

2. АВТОМАТИЗАЦИЯ:
- Bash/Python скрипты
- Ansible playbooks
- Terraform modules
- CI/CD пайплайны

3. КОНТЕЙНЕРИЗАЦИЯ:
- Dockerfiles с best practices
- Docker Compose конфигурации
- Kubernetes манифесты
- Helm charts

4. БЕЗОПАСНОСТЬ:
- Secret management
- RBAC конфигурации
- Security scanning
- Compliance checks

BEST PRACTICES:

1. Всегда используй .example файлы для секретов
2. Добавляй комментарии в конфигурационные файлы
3. Включай health checks в Docker/K8s
4. Используй переменные окружения для конфигурации
5. Добавляй resource limits в K8s манифестах
6. Версионируй все зависимости

ВАЖНО:
- Создавай файлы СТРОГО ПО ОДНОМУ через save_code
- Каждый save_code ДОЛЖЕН содержать ОБА параметра: code и filename
- save_code автоматически создаёт папки
- Используй ПОЛНЫЕ пути: project_name/k8s/deployment.yaml
- В КОНЦЕ отправь финальный отчёт со списком созданных файлов
- НИКОГДА не создавай реальные секреты, только .example файлы
"""

TOOLS = [
    {
        "name": "run_command",
        "description": "Выполняет команду в командной строке или терминале и возвращает ответ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Команда для выполнения в консоли. Пример: py .\\src\\main.py или mkdir project_name"
                },
                "input_str": {
                    "type": "string",
                    "description": "Входные данные для скрипта (передаются в stdin). Если не нужны, укажи пустую строку."
                }
            },
            "required": ["command", "input_str"]
        }
    },
    {
        "name": "save_code",
        "description": "Создает файлы с содержимым и сохраняет код в директории. Используй относительные пути для создания структуры проекта (например: project_name/src/main.py, project_name/Dockerfile). ОБЯЗАТЕЛЬНО передавай оба параметра: code и filename.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "ОБЯЗАТЕЛЬНЫЙ параметр. Полное содержимое файла (код, текст, конфигурация). НЕ пропускай этот параметр!"
                },
                "filename": {
                    "type": "string",
                    "description": "ОБЯЗАТЕЛЬНЫЙ параметр. Имя файла с путем (например: project_name/src/main.py, project_name/.gitignore)"
                }
            },
            "required": ["code", "filename"]
        }
    },
    {
        "name": "validate_project",
        "description": "Проверяет, что все обязательные файлы созданы в проекте. Используй ПОСЛЕ создания всех 8 файлов для финальной валидации.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Название проекта (папка проекта, например: my-telegram-bot)"
                }
            },
            "required": ["project_name"]
        }
    },
    {
        "name": "search",
        "description": "Выполняет запрос в поисковую систему для получения информации в Интернете",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Текстовый запрос в поисковую систему"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_page",
        "description": "Открывает веб-страницы и получает их контент",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Ссылка для посещения веб-сайта"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "validate_yaml",
        "description": "Проверяет синтаксис YAML файлов (Kubernetes манифесты, Ansible playbooks, CI/CD конфиги)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Путь к YAML файлу для проверки (например: project_name/deployment.yaml)"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "validate_terraform",
        "description": "Проверяет синтаксис Terraform конфигурации",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Путь к папке с Terraform файлами (например: project_name)"
                }
            },
            "required": ["project_path"]
        }
    },
    {
        "name": "lint_dockerfile",
        "description": "Проверяет Dockerfile на соответствие best practices с помощью hadolint",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Путь к Dockerfile (например: project_name/Dockerfile)"
                }
            },
            "required": ["filepath"]
        }
    }
]