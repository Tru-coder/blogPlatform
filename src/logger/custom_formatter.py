import logging


class CustomFormatter(logging.Formatter):
    green: str = "\x1b[32m"
    grey: str = "\x1b[38;21m"
    cyan: str = "\x1b[36m"
    yellow: str = "\x1b[33;21m"
    red: str = "\x1b[31;21m"
    bold_red: str = "\x1b[31;1m"
    magenta_purple: str = "\x1b[35m"

    reset: str = "\x1b[0m"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS: dict[int, str] = {
        logging.DEBUG: green + log_format + reset,
        logging.INFO: cyan + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: magenta_purple + log_format + reset
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)