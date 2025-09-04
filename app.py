import asyncio
from playwright.async_api import async_playwright
import random
import os
from urllib.parse import urlparse, urljoin

URL_TO_VISIT = os.environ.get("TARGET_URL", "https://colle-pedia.blogspot.com/")
RUNNER_ID = os.environ.get("RUNNER_ID", "1")
TOR_SOCKS5 = os.environ.get("PROXY_URL", "socks5://127.0.0.1:9050")
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = ""  # لو محدد كلمة مرور للTor Control

async def signal_newnym():
    """يبعت أمر NEWNYM للـ Tor Controller لتغيير الـ IP"""
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', TOR_CONTROL_PORT)
        writer.write(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
        await writer.drain()
        resp = await reader.readline()
        if b'250' not in resp:
            print(f"[Runner {RUNNER_ID}] Tor AUTH failed: {resp}")
            writer.close()
            await writer.wait_closed()
            return
        writer.write(b'SIGNAL NEWNYM\r\n')
        await writer.drain()
        resp = await reader.readline()
        if b'250' in resp:
            print(f"[Runner {RUNNER_ID}] Tor NEWNYM signal sent successfully.")
        writer.write(b'QUIT\r\n')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        await asyncio.sleep(5)  # وقت قصير لتغيير IP
    except Exception as e:
        print(f"[Runner {RUNNER_ID}] Tor NEWNYM error: {e}")

async def visit_with_browser():
    base_netloc = urlparse(URL_TO_VISIT).netloc
    proxy_config = {"server": TOR_SOCKS5}

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                 user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.{random.randint(0,9999)} Safari/537.36"
            )
            page = await context.new_page()

            # زيارة الصفحة الرئيسية
            print(f"[Runner {RUNNER_ID}] Visiting main page: {URL_TO_VISIT}")
            await page.goto(URL_TO_VISIT, wait_until="domcontentloaded", timeout=60000)

            await page.wait_for_selector('a[href*=".html"]', timeout=20000)
            link_locators = page.locator('a[href*=".html"]')
            all_links = await link_locators.all()
            internal_links = [
                urljoin(URL_TO_VISIT, await link.get_attribute('href'))
                for link in all_links
                if await link.get_attribute('href') and urlparse(urljoin(URL_TO_VISIT, await link.get_attribute('href'))).netloc == base_netloc
            ]

            if not internal_links:
                print(f"[Runner {RUNNER_ID}] No valid internal links, closing browser.")
                await browser.close()
                return

            # زيارة 3 صفحات فرعية عشوائية
            pages_to_visit = random.sample(internal_links, min(3, len(internal_links)))
            for link in pages_to_visit:
                print(f"[Runner {RUNNER_ID}] Visiting: {link}")
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(1,3))

            print(f"[Runner {RUNNER_ID}] Done visiting 3 pages. Closing browser to change IP...")
            await browser.close()
        except Exception as e:
            print(f"[Runner {RUNNER_ID}] Error: {e}")
            if browser:
                await browser.close()

async def main():
    while True:
        await visit_with_browser()
        await signal_newnym()  # بعد كل زيارة + 3 صفحات، يغير IP

if __name__ == "__main__":
    asyncio.run(main())
