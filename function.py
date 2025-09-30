import os
import subprocess
import requests
from loguru import logger
from config import SERPER_API_KEY
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup


def save_code(code: str, filename: str) -> str:
    logger.info("Cоздаю þайл в директории {filename}")
    try:
        os.makedirs("./ai", exist_ok=True)
        filepath = os.path.join("./ai", filename)

        with open(filepath, "w", encoding="UTF-8") as f:
            f.write(code)
        return f"Файл {filename} успешно был создан"
    except Exception as e:
        logger.error(f"какая-то ошибка: {str(e)}")
        return f"Ошибка создания файла: {str(e)[:5000]}"



def run_command(command: str, input_str: str | None = None) -> str:
    logger.info(f"Выполняю команду: {command}, входные данные: {str(input_str)}")
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

        return (stdout or stderr)[:16000]

    except Exception as e:
        logger.error(f"Ошибка при выполнении команды: {str(e)}")
        return f"Ошибка при выполнении команды: {str(e)[:5000]}"

def search(query: str) -> str:
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
            return data

        return f"Ошибка: код ответа {response.status_code}, тело: {response.text[:1000]}"

    except Exception as e:
        logger.error(f"Ошибка при поиске в интернете: {str(e)}")
        return f"Ошибка при поиске в интернете: {str(e)[:5000]}"

async def fetch_page(url: str) -> str:
    logger.info(f"Получаю исходный код страницы: {url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/132.0.0.0 Safari/537.3"
                ),
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            await stealth_async(page)

            await page.goto(url, wait_until="networkidle")

            page_content = await page.content()

            await page.screenshot(path="screenshot.png")

            soup = BeautifulSoup(page_content, "html.parser")

            for tag in soup(["script", "style", "svg", "iframe"]):
                tag.decompose()

            for tag in soup.find_all(style=True):
                del tag["style"]

            return str(soup.body)[:25000] if soup.body else page_content[:25000]

    except Exception as e:
        logger.error(f"Ошибка при посещении веб-сайта: {str(e)}")
        return f"Ошибка при посещении веб-сайта: {str(e)[:5000]}"

import asyncio




async def main():
        page = await fetch_page("https://example.com")
        logger.debug(page)


if __name__ == "__main__":
        asyncio.run(main())

