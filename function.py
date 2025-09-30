import os
import subprocess
import requests
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

        logger.success(f"Файл {filename} успешно создан")
        return f"✅ Файл {filename} успешно создан"
    except Exception as e:
        logger.error(f"Ошибка создания файла {filename}: {str(e)}")
        return f"❌ Ошибка создания файла: {str(e)[:5000]}"


def run_command(command: str, input_str: str | None = None) -> str:
    """
    Выполняет команду в терминале PowerShell
    """
    logger.info(f"Выполняю команду: {command}")
    if input_str:
        logger.debug(f"Входные данные: {input_str[:100]}...")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="./ai/"
        )

        if input_str:
            stdout, stderr = process.communicate(input=input_str)
        else:
            stdout, stderr = process.communicate()

        output = (stdout or stderr)[:16000]
        logger.debug(f"Результат выполнения: {output[:200]}...")
        return output

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
            json={"q": query}
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
            await page.screenshot(path="screenshot.png")

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


# Тестирование
import asyncio


async def main():
    # Тест save_code с вложенными директориями
    result = save_code("print('Hello')", "test_project/src/main.py")
    print(result)

    # Тест fetch_page
    # page = await fetch_page("https://example.com")
    # print(page[:500])


if __name__ == "__main__":
    asyncio.run(main())