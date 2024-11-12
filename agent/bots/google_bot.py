import time
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from .base_bot import BaseBot
from .utils.navigation import safe_navigate_to
from .utils.performance import measure_step
from .utils.data_extractors import extract_text_from_element

class GoogleBot(BaseBot):
    async def run(self):
        try:
            await self.perform_steps()
        except Exception as e:
            await self.handle_error(e)

    async def perform_steps(self):
        await self.step_load_google_homepage()
        await self.step_verify_search_bar()
        await self.step_execute_searches()
        await self.step_extract_search_results()

    @measure_step
    async def step_load_google_homepage(self):
        await self.send_run_log("Loading Google homepage...")
        await safe_navigate_to(self.driver, 'https://www.google.com', self.send_run_log)
        await self.send_run_log("Google homepage loaded.")

    @measure_step
    async def step_verify_search_bar(self):
        await self.send_run_log("Verifying search bar presence...")
        search_box = await self.wait_for_element_presence((By.NAME, 'q'))
        if search_box:
            await self.send_run_log("Search bar is present.")
        else:
            raise NoSuchElementException("Search bar not found.")

    @measure_step
    async def step_execute_searches(self):
        search_terms = ['OpenAI', 'Python programming', 'Selenium WebDriver']
        await self.send_run_log("Executing Google searches.")
        for term in search_terms:
            await self.search_term(term)
            await asyncio.sleep(2)

    @measure_step
    async def search_term(self, term):
        await self.send_run_log(f"Searching for: {term}")
        await self.wait_and_input_text((By.NAME, 'q'), term)
        await self.wait_and_click((By.NAME, 'btnK'))
        await asyncio.sleep(2)
        results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
        if not results:
            raise NoSuchElementException(f"No results found for '{term}'")
        await self.send_run_log(f"Search results retrieved for '{term}'.")

    @measure_step
    async def step_extract_search_results(self):
        await self.send_run_log("Extracting search results...")
        results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
        for index, result in enumerate(results[:5], start=1):
            title_element = result.find_element(By.TAG_NAME, 'h3')
            title = extract_text_from_element(title_element)
            await self.send_run_log(f"Result {index}: {title}")
        await self.send_run_log("Search results extraction complete.")
