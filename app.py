import asyncio
from playwright.async_api import async_playwright
import random
import os
from urllib.parse import urlparse, urljoin

URL_TO_VISIT = os.environ.get("TARGET_URL", "https://colle-pedia.blogspot.com/")
RUNNER_ID = os.environ.get("RUNNER_ID", "1")
TOR_SOCKS5 = os.environ.get("PROXY_URL", "socks5://127.0.0.1:9050")
PROXY_URL = TOR_SOCKS5
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = ""

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
    # ---  الجديد: قراءة الروابط من الملف الجاهز ---
    try:
        with open("links.txt", "r") as f:
            all_links = [line.strip() for line in f.readlines()]
        if not all_links:
            print("❗️ links.txt is empty. Exiting.")
            return
    except FileNotFoundError:
        print("❗️ links.txt not found. Cannot perform visits. Exiting.")
        return

    proxy_config = {"server": PROXY_URL} if PROXY_URL else None
    
    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(headless=True, proxy=proxy_config, args=['--no-sandbox'])
            context = await browser.new_context(
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.{random.randint(0,9999)} Safari/537.36"
            )
            page = await context.new_page()

            # زيارة الصفحة الرئيسية أولاً
            print(f"[Runner {RUNNER_ID}] Visiting main page: {URL_TO_VISIT}")
            await page.goto(URL_TO_VISIT, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(5, 10))

            # اختيار وزيارة 3 مقالات عشوائية من القائمة
            pages_to_visit = random.sample(all_links, min(3, len(all_links)))
            print(f"[Runner {RUNNER_ID}] Will visit {len(pages_to_visit)} random articles from the list.")
            
            for i, link in enumerate(pages_to_visit):
                print(f"[Runner {RUNNER_ID}] Visiting article {i+1}/{len(pages_to_visit)}: {link}")
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(15, 30))

            print(f"✅ [Runner {RUNNER_ID}] Visit cycle complete.")
        except Exception as e:
            print(f"❗️ [Runner {RUNNER_ID}] An error occurred: {e}")
        finally:
            if browser:
                await browser.close()

async def main():
    while True:
        await visit_with_browser()
        await signal_newnym()  # بعد كل زيارة + 3 صفحات، يغير IP

if __name__ == "__main__":
    asyncio.run(main())
