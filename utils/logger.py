from loguru import logger


def setup_logger():
    """Настраивает loguru: убирает стандартный вывод, добавляет кастомный формат.

    Returns:
        Настроенный экземпляр loguru.logger.
    """
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), format="{level}: {message}")
    return logger
