import asyncio
from playwright.async_api import async_playwright
import os

URL_TO_SCRAPE = os.environ.get("TARGET_URL", "https://colle-pedia.blogspot.com/")

async def scrape_all_links():
    print("Starting the link scraping process...")
    all_article_links = set() # نستخدم set لمنع تكرار الروابط

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()

        await page.goto(URL_TO_SCRAPE, wait_until="networkidle", timeout=90000)
        print(f"Loaded main page: {URL_TO_SCRAPE}")

        # ---  الجديد: التمرير لأسفل حتى نهاية الصفحة ---
        last_height = await page.evaluate("document.body.scrollHeight")
        while True:
            print(f"Scrolling down... Current links found: {len(all_article_links)}")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3) # انتظر لتحميل المحتوى الجديد
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("Reached the bottom of the page.")
                break
            last_height = new_height
        
        # --- جمع كل الروابط بعد تحميل الصفحة بالكامل ---
        link_locators = page.locator('a[href*=".html"]')
        all_link_elements = await link_locators.all()
        
        for link_element in all_link_elements:
            href = await link_element.get_attribute('href')
            # ---  الجديد: فلترة الروابط التي تحتوي على /p/ ---
            if href and 'colle-pedia.blogspot.com' in href and '/p/' not in href:
                all_article_links.add(href)
        
        await browser.close()

    # --- حفظ الروابط في ملف نصي ---
    if all_article_links:
        with open("links.txt", "w") as f:
            for link in all_article_links:
                f.write(link + "\n")
        print(f"✅ Successfully scraped and saved {len(all_article_links)} unique links to links.txt")
    else:
        print("❗️ No links were found to save.")

if __name__ == "__main__":
    asyncio.run(scrape_all_links())
