import time
import functools

def measure_step(func):
    """Decorator to measure the execution time of a function and log it."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        step_name = func.__name__
        start_time = time.time()

        # Log start of step
        self.send_log(f"Started step: {step_name}")
        self.send_event({
            "step": step_name,
            "status": "started",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })

        try:
            result = func(self, *args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            # Log end of step
            self.send_log(f"Completed step: {step_name} in {duration:.2f} seconds")
            self.send_event({
                "step": step_name,
                "status": "completed",
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # Log error during step
            self.send_log(f"Error in step: {step_name}")
            self.send_event({
                "step": step_name,
                "status": "error",
                "error": str(e),
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            raise e

    return wrapper
