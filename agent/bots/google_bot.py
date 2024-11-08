import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from .base_bot import BaseBot
from .utils.navigation import safe_navigate_to
from .utils.performance import measure_step


class GoogleBot(BaseBot):
    async def run(self):
        """Execute the main bot workflow."""
        try:
            await self.perform_steps()
        except Exception as e:
            await self.handle_error(e)

    @measure_step
    async def perform_steps(self):
        """Perform a sequence of granular steps to conduct Google searches."""
        try:
            # Step 1: Load Google Homepage
            await self.step_load_google_homepage()

            # Step 2: Confirm Search Bar is Present
            await self.step_verify_search_bar()

            # Step 3: Execute Searches
            await self.step_execute_searches()

        except WebDriverException as e:
            self.handle_error(e)

    async def step_load_google_homepage(self):
        """Step 1: Load Google homepage."""
        try:
            await self.send_run_log("Step 1: Loading Google homepage...")
            safe_navigate_to(self.driver, 'https://www.google.com', await self.send_run_log)
            await self.send_run_log("Step 1: Successfully loaded Google homepage.")
        except Exception as e:
            self.handle_error(f"Step 1 Failed: Unable to load Google homepage. Error: {e}")
            raise

    async def step_verify_search_bar(self):
        """Step 2: Verify that the search bar is present."""
        try:
            await self.send_run_log("Step 2: Verifying search bar is present on the homepage...")
            search_box = self.driver.find_element(By.NAME, 'q')
            if search_box:
                await self.send_run_log("Step 2: Search bar found successfully.")
            else:
                raise NoSuchElementException("Search bar not found on Google homepage.")
        except NoSuchElementException as e:
            self.handle_error(f"Step 2 Failed: {e}")
            raise

    async def step_execute_searches(self):
        """Step 3: Execute a sequence of Google searches."""
        search_terms = ['OpenAI', 'Python programming', 'Selenium WebDriver']
        await self.send_run_log("Step 3: Starting Google searches for predefined terms.")

        for term in search_terms:
            try:
                self.search_term(term)
                await self.send_run_log(f"Step 3: Search completed successfully for term '{term}'.")
                time.sleep(2)
            except Exception as e:
                self.handle_error(f"Step 3 Failed during search term '{term}': {e}")
                raise

    @measure_step
    async def search_term(self, term):
        """Search a term on Google."""
        try:
            await self.send_run_log(f"Searching for term: {term}")
            search_box = self.driver.find_element(By.NAME, 'q')
            search_box.clear()
            search_box.send_keys(term)
            search_box.send_keys(Keys.RETURN)

            time.sleep(2)  # Wait for the results to load

            results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
            if not results:
                raise NoSuchElementException(f"No results found for '{term}'")
            await self.send_run_log(f"Results found for term: '{term}'")
        except Exception as e:
            self.handle_error(f"Failed to search term '{term}': {e}")
            raise
