from croniter import croniter, CroniterBadCronError

def validate_cron_expression(cron):
    try:
        croniter(cron)
        return True
    except CroniterBadCronError:
        return False