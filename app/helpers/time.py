from time import gmtime, strftime


def get_current_time() -> str:
    """
    day-month-year hour:minute:second
    22-01-2025 09:53:46
    """
    return str(strftime("%d-%m-%Y %H:%M:%S", gmtime()))
