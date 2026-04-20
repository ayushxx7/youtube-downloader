import asyncio
from playwright.async_api import async_playwright
import os

async def capture_youtube_downloader_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        print("Navigating to YouTube Downloader UI...")
        try:
            await page.goto("http://localhost:8501", wait_until="networkidle")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="showcase/landing.png")
            print("Captured landing.png")
            
            # Simulate a URL input
            url_input = await page.query_selector('input[aria-label="Enter YouTube URL..."]')
            if url_input:
                await url_input.fill("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
                await page.screenshot(path="showcase/metadata_preview.png")
                print("Captured metadata_preview.png")
        except Exception as e:
            print(f"Failed to capture UI: {e}")

        await browser.close()

if __name__ == "__main__":
    if not os.path.exists("showcase"):
        os.makedirs("showcase")
    asyncio.run(capture_youtube_downloader_ui())
