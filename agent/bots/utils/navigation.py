from selenium.common.exceptions import TimeoutException

def safe_navigate_to(driver, url, log_func, max_retries=3):
    """Navigate to a URL with retries in case of failure."""
    retries = 0
    while retries < max_retries:
        try:
            driver.get(url)
            return True
        except TimeoutException as e:
            log_func({
                'action': 'navigation_retry',
                'url': url,
                'retries': retries + 1,
                'error': str(e)
            })
            retries += 1
    raise Exception(f"Failed to navigate to {url} after {max_retries} retries.")
