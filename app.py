import asyncio
from playwright.async_api import async_playwright
import random
import os
from urllib.parse import urlparse, urljoin

# -------- الإعدادات --------
URL_TO_VISIT = os.environ.get("TARGET_URL", "https://colle-pedia.blogspot.com/")
RUNNER_ID = os.environ.get("RUNNER_ID", "1")

async def visit_with_browser():
    # استخراج اسم النطاق الأساسي للمقارنة
    base_netloc = urlparse(URL_TO_VISIT).netloc
    
    async with async_playwright() as p:
        browser = None
        try:
            print(f"[Runner {RUNNER_ID}] Launching browser...")
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
            
            context = await browser.new_context(
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.{random.randint(0,9999)} Safari/537.36"
            )
            page = await context.new_page()

            # --- 1. زيارة الصفحة الرئيسية ---
            print(f"[Runner {RUNNER_ID}] Visiting main page: {URL_TO_VISIT}")
            await page.goto(URL_TO_VISIT, wait_until="domcontentloaded", timeout=60000)
            
            # --- 2. البحث عن كل الروابط في الصفحة ---
            # نبحث عن الروابط التي تحتوي على .html، وهي غالبًا روابط المقالات
            link_locators = page.locator('a[href*=".html"]')
            all_links = await link_locators.all()
            
            if not all_links:
                print(f"❗️ [Runner {RUNNER_ID}] No article links found on the main page.")
                await browser.close()
                return False

            # --- 3. استخراج وفلترة الروابط الداخلية فقط ---
            internal_article_links = []
            for link_locator in all_links:
                href = await link_locator.get_attribute('href')
                if href:
                    # تحويل الرابط النسبي إلى رابط كامل
                    absolute_url = urljoin(URL_TO_VISIT, href)
                    # التأكد من أن الرابط يتبع نفس النطاق الأساسي
                    if urlparse(absolute_url).netloc == base_netloc:
                        internal_article_links.append(absolute_url)

            if not internal_article_links:
                print(f"❗️ [Runner {RUNNER_ID}] No valid internal article links found.")
                await browser.close()
                return False

            # --- 4. اختيار رابط عشوائي وزيارته ---
            random_article_url = random.choice(internal_article_links)
            print(f"[Runner {RUNNER_ID}] Found {len(internal_article_links)} links. Randomly visiting: {random_article_url}")
            await page.goto(random_article_url, wait_until="domcontentloaded", timeout=60000)

            # --- 5. محاكاة البقاء في الصفحة ---
            wait_time = random.uniform(15, 45)
            print(f"[Runner {RUNNER_ID}] In article page. Waiting for {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
            
            print(f"✅ [Runner {RUNNER_ID}] Visit complete. Closing browser.")
            await browser.close()
            return True

        except Exception as e:
            print(f"❗️ [Runner {RUNNER_ID}] An error occurred: {e}")
            if browser:
                await browser.close()
            return False

if __name__ == "__main__":
    asyncio.run(visit_with_browser())
