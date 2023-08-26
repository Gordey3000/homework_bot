class HTTPRequestError(Exception):
    """Проверка на HTTPStatus.OK."""
    ...


class ResponseApiError(Exception):
    """Проверка на доступность ENDPOINT."""
    ...


class KeyApiError(Exception):
    """Отсутствует ключ API."""
    ...


class StatusHomeworkError(Exception):
    """Неожиданный статус домашней работы."""
    ...
