import time
import functools
from typing import Callable, TypeVar, Any
from ..base_bot import BaseBot

T = TypeVar('T', bound=BaseBot)

def measure_step(func: Callable[[T, Any], Any]) -> Callable[[T, Any], Any]:
    """Decorator to measure execution time and log detailed performance data."""
    @functools.wraps(func)
    async def wrapper(self: T, *args: Any, **kwargs: Any) -> Any:
        step_name = func.__name__
        start_time = time.time()

        try:
            result = await func(self, *args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            screenshot_base64 = await self.capture_screenshot()
            message = f"Step {step_name} completed in {duration:.2f} seconds."
            metrics = await self.capture_system_metrics()
            payload = {
                'step_name': step_name,
                'duration': duration,
                'metrics': metrics
            }
            await self.send_run_event(message=message, screenshot=screenshot_base64, payload=payload)

            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            await self.handle_error(e)
            raise e
    return wrapper
