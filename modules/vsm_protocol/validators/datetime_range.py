from datetime import datetime


def validate_datetime_range(dt_from, dt_to):
    """
    Проверка временного диапазона
    """

    if dt_from is None or dt_to is None:
        return False, "Дата и время не могут быть пустыми"

    if dt_from > dt_to:
        return False, (
            "Начальная дата/время "
            "не может быть позже конечной"
        )

    if dt_to > datetime.now():
        return False, (
            "Конечная дата/время "
            "не может быть в будущем"
        )

    return True, ""