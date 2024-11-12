from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import asyncio

async def safe_navigate_to(driver, url, log_func, max_retries=3, wait_time=10):
    """Navigate to a URL with retries and wait for page to load."""
    retries = 0
    while retries < max_retries:
        try:
            driver.get(url)
            # Wait for the page to fully load
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            return True
        except TimeoutException:
            await log_func(f"Failed to load {url}. Retrying ({retries + 1}/{max_retries})...")
            retries += 1
            await asyncio.sleep(2 ** retries)  # Exponential backoff
    raise Exception(f"Failed to navigate to {url} after {max_retries} retries.")

async def click_element(driver, locator, timeout=10):
    """Click an element specified by a locator."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        return True
    except TimeoutException:
        return False

async def input_text(driver, locator, text, timeout=10):
    """Input text into an element specified by a locator."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        element.clear()
        element.send_keys(text)
        return True
    except TimeoutException:
        return False

async def wait_for_element(driver, locator, timeout=10):
    """Wait for an element to be present on the page."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        return None

async def scroll_to_element(driver, element):
    """Scroll to bring the element into view."""
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)

async def handle_modal(driver, accept=True, timeout=5):
    """Handle modals or alerts."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        if accept:
            alert.accept()
        else:
            alert.dismiss()
        return True
    except TimeoutException:
        return False
