import os
import subprocess
import requests
import yaml
from loguru import logger
from config import SERPER_API_KEY
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


def save_code(code: str, filename: str) -> str:
    """
    Сохраняет код в файл с поддержкой вложенных директорий.
    Например: save_code(code, "project/src/main.py")
    """
    logger.info(f"Создаю файл: {filename}")
    try:
        # Формируем полный путь относительно папки ai
        filepath = os.path.join("./ai", filename)

        # Создаём все необходимые директории
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Создана директория: {directory}")

        # Сохраняем файл
        with open(filepath, "w", encoding="UTF-8") as f:
            f.write(code)

        # Получаем размер файла
        file_size = os.path.getsize(filepath)

        logger.success(f"Файл {filename} успешно создан ({file_size} байт)")
        return f"✅ Файл {filename} успешно создан ({file_size} байт)"
    except Exception as e:
        logger.error(f"Ошибка создания файла {filename}: {str(e)}")
        return f"❌ Ошибка создания файла: {str(e)[:5000]}"


def run_command(command: str, input_str: str | None = None) -> str:
    """
    Выполняет команду в терминале PowerShell
    Специальная обработка для mkdir и cd команд
    """
    logger.info(f"Выполняю команду: {command}")
    if input_str:
        logger.debug(f"Входные данные: {input_str[:100]}...")

    try:
        # Специальная обработка для mkdir
        if command.strip().startswith("mkdir "):
            folder_name = command.strip()[6:].strip().strip('"').strip("'")
            folder_path = os.path.join("./ai/", folder_name)
            os.makedirs(folder_path, exist_ok=True)
            logger.success(f"Папка создана: {folder_name}")
            return f"✅ Папка '{folder_name}' успешно создана"
        
        # Специальная обработка для cd
        if command.strip().startswith("cd "):
            folder_name = command.strip()[3:].strip().strip('"').strip("'")
            folder_path = os.path.join("./ai/", folder_name)
            if os.path.exists(folder_path):
                logger.success(f"Переход в папку: {folder_name}")
                return f"✅ Переход в папку '{folder_name}' (примечание: команда cd не меняет рабочую директорию между вызовами)"
            else:
                return f"❌ Папка '{folder_name}' не существует"
        
        # Для остальных команд используем PowerShell
        full_command = ["powershell.exe", "-Command", command]
        
        process = subprocess.Popen(
            full_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="./ai/"
        )

        if input_str:
            stdout, stderr = process.communicate(input=input_str, timeout=30)
        else:
            stdout, stderr = process.communicate(timeout=30)

        # Объединяем stdout и stderr
        output = stdout if stdout else stderr
        if not output:
            output = "✅ Команда выполнена успешно (без вывода)"
        
        result = output[:16000]
        logger.debug(f"Результат выполнения: {result[:200]}...")
        return result

    except subprocess.TimeoutExpired:
        logger.error("Команда превысила время ожидания (30 секунд)")
        process.kill()
        return "❌ Ошибка: команда превысила время ожидания (30 секунд)"
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды: {str(e)}")
        return f"❌ Ошибка при выполнении команды: {str(e)[:5000]}"


def search(query: str) -> str:
    """
    Выполняет поиск в Google через Serper API
    """
    logger.info(f"Ищу в интернете: {query}")
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-type": "application/json"
            },
            json={"q": query},
            timeout=10
        )

        if response.status_code in [200, 201]:
            data_json = response.json()
            data = "\n".join(
                f"{item['title']}: {item['snippet']}"
                for item in data_json.get("organic", [])[:3]
            )
            logger.success("Поиск выполнен успешно")
            return data

        logger.warning(f"Ошибка поиска: {response.status_code}")
        return f"❌ Ошибка: код ответа {response.status_code}, тело: {response.text[:1000]}"

    except Exception as e:
        logger.error(f"Ошибка при поиске в интернете: {str(e)}")
        return f"❌ Ошибка при поиске в интернете: {str(e)[:5000]}"


async def fetch_page(url: str) -> str:
    """
    Получает HTML-контент страницы через Playwright
    """
    logger.info(f"Получаю исходный код страницы: {url}")
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage"
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/132.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )

            # Ручной обход детектирования
            await context.add_init_script('''
                // Скрываем webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Добавляем реалистичные плагины
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Языки
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'ru']
                });

               // Chrome runtime
                window.chrome = {
                    runtime: {}
                };

                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            ''')

            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=30000)
            page_content = await page.content()
            
            # Сохраняем скриншот в папку ai
            screenshot_path = os.path.join("./ai", "screenshot.png")
            await page.screenshot(path=screenshot_path)

            soup = BeautifulSoup(page_content, "html.parser")
            for tag in soup(["script", "style", "svg", "iframe"]):
                tag.decompose()
            for tag in soup.find_all(style=True):
                del tag["style"]

            await browser.close()

            result = str(soup.body)[:25000] if soup.body else page_content[:25000]
            logger.success("Страница успешно получена")
            return result

    except Exception as e:
        logger.error(f"Ошибка при получении страницы: {str(e)}")
        if browser:
            try:
                await browser.close()
            except:
                pass
        return f"❌ Ошибка: {str(e)[:5000]}"


def validate_project(project_name: str) -> str:
    """
    Проверяет, что все обязательные файлы созданы в проекте
    """
    logger.info(f"Валидация проекта: {project_name}")

    required_files = [
        f"{project_name}/src/__init__.py",
        f"{project_name}/src/main.py",
        f"{project_name}/requirements.txt",
        f"{project_name}/.gitignore",
        f"{project_name}/.dockerignore",
        f"{project_name}/Dockerfile",
        f"{project_name}/.env.example",
        f"{project_name}/README.md"
    ]

    missing_files = []
    created_files = []

    for file in required_files:
        filepath = os.path.join("./ai", file)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            created_files.append(f"[OK] {file} ({size} байт)")
        else:
            missing_files.append(f"[MISSING] {file}")

    result = "=== ОТЧЁТ О ВАЛИДАЦИИ ПРОЕКТА ===\n\n"
    result += f"Проект: {project_name}\n\n"

    if created_files:
        result += "Созданные файлы:\n" + "\n".join(created_files) + "\n\n"

    if missing_files:
        result += "!!! ОТСУТСТВУЮЩИЕ ОБЯЗАТЕЛЬНЫЕ ФАЙЛЫ:\n" + "\n".join(missing_files) + "\n\n"
        result += "ПРОЕКТ НЕПОЛНЫЙ! Создайте недостающие файлы."
        logger.error(f"Проект {project_name} неполный: отсутствуют {len(missing_files)} файлов")
    else:
        result += "[OK] ВСЕ ОБЯЗАТЕЛЬНЫЕ ФАЙЛЫ СОЗДАНЫ!"
        logger.success(f"Проект {project_name} успешно создан")

    return result


def validate_yaml(filepath: str) -> str:
    """
    Проверяет синтаксис YAML файла
    """
    logger.info(f"Валидация YAML: {filepath}")
    try:
        full_path = os.path.join("./ai", filepath)

        if not os.path.exists(full_path):
            return f"❌ Файл {filepath} не найден"

        with open(full_path, "r", encoding="UTF-8") as f:
            yaml_content = yaml.safe_load(f)

        logger.success(f"YAML файл {filepath} валиден")
        return f"✅ YAML файл {filepath} валиден\n\nСтруктура:\n{yaml.dump(yaml_content, allow_unicode=True, default_flow_style=False)[:1000]}"

    except yaml.YAMLError as e:
        logger.error(f"Ошибка синтаксиса YAML в {filepath}: {str(e)}")
        return f"❌ Ошибка синтаксиса YAML в {filepath}:\n{str(e)}"
    except Exception as e:
        logger.error(f"Ошибка при валидации {filepath}: {str(e)}")
        return f"❌ Ошибка при валидации: {str(e)[:5000]}"


def validate_terraform(project_path: str) -> str:
    """
    Проверяет синтаксис Terraform конфигурации
    """
    logger.info(f"Валидация Terraform: {project_path}")
    try:
        full_path = os.path.join("./ai", project_path)

        if not os.path.exists(full_path):
            return f"❌ Папка {project_path} не найдена"

        # Проверяем наличие terraform
        check_cmd = subprocess.run(
            ["powershell.exe", "-Command", "terraform --version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if check_cmd.returncode != 0:
            return "⚠️ Terraform не установлен. Установите Terraform для валидации: https://www.terraform.io/downloads"

        # Выполняем terraform fmt для проверки форматирования
        fmt_cmd = subprocess.run(
            ["powershell.exe", "-Command", f"terraform fmt -check {full_path}"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="./ai/"
        )

        # Выполняем terraform validate
        validate_cmd = subprocess.run(
            ["powershell.exe", "-Command", f"cd {full_path}; terraform init -backend=false; terraform validate"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="./ai/"
        )

        result = "=== ВАЛИДАЦИЯ TERRAFORM ===\n\n"

        if fmt_cmd.returncode == 0:
            result += "✅ Форматирование: OK\n"
        else:
            result += f"⚠️ Форматирование: требуется исправление\n{fmt_cmd.stdout}\n"

        if validate_cmd.returncode == 0:
            result += f"✅ Валидация: OK\n{validate_cmd.stdout}"
        else:
            result += f"❌ Валидация: ошибки найдены\n{validate_cmd.stderr}"

        logger.success(f"Terraform валидация завершена для {project_path}")
        return result

    except subprocess.TimeoutExpired:
        return "❌ Превышено время ожидания валидации Terraform"
    except Exception as e:
        logger.error(f"Ошибка при валидации Terraform: {str(e)}")
        return f"❌ Ошибка при валидации Terraform: {str(e)[:5000]}"


def lint_dockerfile(filepath: str) -> str:
    """
    Проверяет Dockerfile с помощью базовых правил
    """
    logger.info(f"Линтинг Dockerfile: {filepath}")
    try:
        full_path = os.path.join("./ai", filepath)

        if not os.path.exists(full_path):
            return f"❌ Файл {filepath} не найден"

        with open(full_path, "r", encoding="UTF-8") as f:
            content = f.read()

        issues = []
        recommendations = []

        # Базовые проверки
        lines = content.split('\n')

        # Проверка FROM
        if not any(line.strip().startswith('FROM ') for line in lines):
            issues.append("❌ Отсутствует инструкция FROM")

        # Проверка на использование latest
        if 'FROM' in content and ':latest' in content:
            recommendations.append("⚠️ Рекомендуется избегать тега :latest, используйте конкретные версии")

        # Проверка WORKDIR
        if not any(line.strip().startswith('WORKDIR ') for line in lines):
            recommendations.append("⚠️ Рекомендуется использовать WORKDIR вместо cd")

        # Проверка на apt-get update без clean
        if 'apt-get update' in content and 'apt-get clean' not in content:
            recommendations.append("⚠️ После apt-get update рекомендуется добавить apt-get clean для уменьшения размера образа")

        # Проверка COPY/ADD
        if not any(line.strip().startswith(('COPY ', 'ADD ')) for line in lines):
            recommendations.append("⚠️ Не найдены инструкции COPY или ADD")

        # Проверка CMD/ENTRYPOINT
        if not any(line.strip().startswith(('CMD ', 'ENTRYPOINT ')) for line in lines):
            issues.append("❌ Отсутствует CMD или ENTRYPOINT")

        result = f"=== ЛИНТИНГ DOCKERFILE: {filepath} ===\n\n"

        if not issues and not recommendations:
            result += "✅ Dockerfile выглядит хорошо!\n"
        else:
            if issues:
                result += "Критические проблемы:\n" + "\n".join(issues) + "\n\n"
            if recommendations:
                result += "Рекомендации:\n" + "\n".join(recommendations) + "\n"

        logger.success(f"Линтинг Dockerfile завершён для {filepath}")
        return result

    except Exception as e:
        logger.error(f"Ошибка при линтинге Dockerfile: {str(e)}")
        return f"❌ Ошибка при линтинге: {str(e)[:5000]}"


# Тестирование
import asyncio


async def main():
    # Тест save_code с вложенными директориями
    result = save_code("print('Hello')", "test_project/src/main.py")
    print(result)

    # Тест run_command
    result = run_command('New-Item -ItemType Directory -Name "test_folder"')
    print(result)


if __name__ == "__main__":
    asyncio.run(main())