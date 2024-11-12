import asyncio
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .utils.performance import measure_step

from .base_bot import BaseBot
from .utils.navigation import safe_navigate_to

class ComplexBot(BaseBot):
    async def run(self):
        try:
            await self.perform_steps()
        except Exception as e:
            await self.handle_error(e)

    async def perform_steps(self):
        await self.step_load_login_page()
        await self.step_login()
        await self.step_navigate_and_perform_actions()
        await self.step_logout()
        await self.send_run_log("Finished perform_steps method.")

    @measure_step
    async def step_load_login_page(self):
        await safe_navigate_to(self.driver, 'https://www.saucedemo.com', self.send_run_log)

    @measure_step
    async def step_login(self):
        await self.wait_and_input_text((By.ID, 'user-name'), 'standard_user')
        await self.wait_and_input_text((By.ID, 'password'), 'secret_sauce')
        await self.wait_and_click((By.ID, 'login-button'))

    @measure_step
    async def step_navigate_and_perform_actions(self):
        await self.wait_and_click((By.ID, 'add-to-cart-sauce-labs-backpack'))
        await self.wait_and_click((By.ID, 'add-to-cart-sauce-labs-bike-light'))

    @measure_step
    async def step_logout(self):
        await self.wait_and_click((By.ID, 'react-burger-menu-btn'))
        await self.wait_and_click((By.ID, 'logout_sidebar_link'))