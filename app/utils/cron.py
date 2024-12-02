from croniter import croniter, CroniterBadCronError

def validate_cron_expression(cron: str) -> bool:
    try:
        croniter(cron)
        return True
    except CroniterBadCronError:
        return False