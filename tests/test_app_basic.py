import pytest
from playwright.sync_api import sync_playwright

def test_youtube_url_input_and_info():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.fill('input[placeholder^="https://www.youtube.com"]', "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        page.click('button:has-text("Fetch Video Info")')
        try:
            # Wait up to 30 seconds for the actual video title to appear
            page.wait_for_selector('text=Never Gonna Give You Up', timeout=30000)
            assert page.query_selector('text=Never Gonna Give You Up') is not None
        except Exception as e:
            print(page.content())
            page.screenshot(path='test_failure.png')
            raise e
        finally:
            browser.close()

def test_direct_download_flow():
    from playwright.sync_api import sync_playwright
    import time

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        # Step 1: Enter a valid YouTube URL
        page.fill('input[placeholder^="https://www.youtube.com"]', "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        # Step 2: Click Fetch Video Info
        page.click('button:has-text("Fetch Video Info")')
        # Step 3: Wait for video info and Download button
        page.wait_for_selector('button:has-text("Download")', timeout=30000)
        # Step 4: Click Download
        page.click('button:has-text("Download")')
        # Step 5: Wait for download to complete
        page.wait_for_selector('text=Download completed successfully!', timeout=120000)
        # Step 6: Assert file path and preview are present
        assert "Download completed successfully!" in page.content()
        assert "Preview" in page.content() or "Audio Preview" in page.content()
        browser.close()

def test_end_to_end_audio_download_flow():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        # Enter a valid YouTube URL
        page.fill('input[placeholder^="https://www.youtube.com"]', "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        # Select "Audio Only"
        page.click('label:has-text("Audio Only")')
        # Click Fetch Video Info
        page.click('button:has-text("Fetch Video Info")')
        # Wait for Download button
        page.wait_for_selector('button:has-text("Download")', timeout=30000)
        # Click Download
        page.click('button:has-text("Download")')
        # Wait for download to complete
        page.wait_for_selector('text=Download completed successfully!', timeout=120000)
        # Assert Audio Preview is present
        assert "Audio Preview" in page.content()
        browser.close()


def test_youtube_search_results():
    from playwright.sync_api import sync_playwright
    import time

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        # Wait for the search bar to appear by label
        page.get_by_label("Search for a video").wait_for(timeout=10000)
        # Enter a search query
        page.get_by_label("Search for a video").fill("lofi hip hop")
        # Click the Search button
        page.click('button:has-text("Search")')
        # Wait for results to load (results should have thumbnails and URLs)
        page.wait_for_selector('img[src*="ytimg.com"]', timeout=20000)
        # Assert at least one result is present
        thumbnails = page.query_selector_all('img[src*="ytimg.com"]')
        assert len(thumbnails) > 0, "No search result thumbnails found."
        # Wait for at least one code block to appear
        page.wait_for_selector('div[data-testid="stCode"]', timeout=20000)
        url_code = page.query_selector('div[data-testid="stCode"]')
        assert url_code is not None, "No code block found in search results."

        # Hover to reveal the copy button
        url_code.hover()
        # Wait for the copy button to appear
        page.wait_for_selector('button[data-testid="stCodeCopyButton"]', timeout=5000)
        copy_btn = page.query_selector('button[data-testid="stCodeCopyButton"]')
        assert copy_btn is not None, "Copy button not visible on code block hover."
        browser.close()
