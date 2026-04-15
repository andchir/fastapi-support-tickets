from fastapi import Request

SUPPORTED_LANGUAGES = {"en", "ru"}
DEFAULT_LANGUAGE = "en"

VALID_STATUSES = {"new", "in_progress", "answered", "closed", "deferred"}
VALID_STATUSES_RU = {"Новый", "В процессе", "Получен ответ", "Закрыт", "Отложен"}

# Canonical status name → localized value
_STATUS_I18N: dict[str, dict[str, str]] = {
    "en": {
        "new": "new",
        "in_progress": "in_progress",
        "answered": "answered",
        "closed": "closed",
        "deferred": "deferred",
    },
    "ru": {
        "new": "Новый",
        "in_progress": "В процессе",
        "answered": "Получен ответ",
        "closed": "Закрыт",
        "deferred": "Отложен",
    },
}


def get_status(canonical: str, lang: str) -> str:
    """Return the localized status value for *canonical* in *lang*."""
    return _STATUS_I18N.get(lang, _STATUS_I18N[DEFAULT_LANGUAGE]).get(canonical, canonical)

# Keys are used both for HTTPException details (raised in routers/auth)
# and for Pydantic v2 validation error types.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # ── HTTP exception messages ────────────────────────────────────────
        "ticket_not_found": "Ticket not found",
        "only_image_video_allowed": "Only image and video files are allowed",
        "topic_uuid_required": "topic_uuid is required",
        "invalid_status": "Invalid status. Valid values: {values}",
        "invalid_api_key": "Invalid API key",
        "admin_api_key_required": "Admin API key required",
        "owner_not_found": "Technical support department not found",

        # ── Pydantic v2 validation error types ────────────────────────────
        "missing": "Field required",
        "string_too_long": "String should have at most {max_length} characters",
        "string_too_short": "String should have at least {min_length} characters",
        "string_type": "Input should be a valid string",
        "int_type": "Input should be a valid integer",
        "int_parsing": "Input should be a valid integer, unable to parse string as an integer",
        "float_type": "Input should be a valid number",
        "float_parsing": "Input should be a valid number, unable to parse string as a number",
        "bool_type": "Input should be a valid boolean",
        "bool_parsing": "Input should be a valid boolean, unable to interpret input",
        "datetime_type": "Input should be a valid datetime",
        "datetime_parsing": "Input should be a valid datetime, {error}",
        "date_type": "Input should be a valid date",
        "date_parsing": "Input should be a valid date in the format YYYY-MM-DD, {error}",
        "value_error": "Value error, {error}",
        "literal_error": "Input should be {expected_literal}",
        "greater_than_equal": "Input should be greater than or equal to {ge}",
        "less_than_equal": "Input should be less than or equal to {le}",
        "greater_than": "Input should be greater than {gt}",
        "less_than": "Input should be less than {lt}",
        "url_type": "URL input should be a string or URL",
        "url_parsing": "Input should be a valid URL, {error}",
        "email_type": "Value is not a valid email address",
        "json_invalid": "JSON decode error, {error}",
        "json_type": "JSON input should be string, bytes or bytearray",
        "extra_forbidden": "Extra inputs are not permitted"
    },
    "ru": {
        # ── HTTP exception messages ────────────────────────────────────────
        "ticket_not_found": "Тикет не найден",
        "only_image_video_allowed": "Разрешены только файлы изображений и видео",
        "topic_uuid_required": "Параметр topic_uuid обязателен",
        "invalid_status": "Недопустимый статус. Допустимые значения: {values}",
        "invalid_api_key": "Неверный API-ключ",
        "admin_api_key_required": "Требуется API-ключ администратора",
        "owner_not_found": "Отдел технической поддержки не найден",

        # ── Pydantic v2 validation error types ────────────────────────────
        "missing": "Обязательное поле",
        "string_too_long": "Строка должна содержать не более {max_length} символов",
        "string_too_short": "Строка должна содержать не менее {min_length} символов",
        "string_type": "Значение должно быть строкой",
        "int_type": "Значение должно быть целым числом",
        "int_parsing": "Не удалось преобразовать значение в целое число",
        "float_type": "Значение должно быть числом",
        "float_parsing": "Не удалось преобразовать значение в число",
        "bool_type": "Значение должно быть булевым",
        "bool_parsing": "Не удалось интерпретировать значение как булево",
        "datetime_type": "Значение должно быть датой и временем",
        "datetime_parsing": "Не удалось разобрать дату и время: {error}",
        "date_type": "Значение должно быть датой",
        "date_parsing": "Значение должно быть датой в формате ГГГГ-ММ-ДД: {error}",
        "value_error": "Ошибка значения: {error}",
        "literal_error": "Ожидается одно из значений: {expected_literal}",
        "greater_than_equal": "Значение должно быть не менее {ge}",
        "less_than_equal": "Значение должно быть не более {le}",
        "greater_than": "Значение должно быть больше {gt}",
        "less_than": "Значение должно быть меньше {lt}",
        "url_type": "Ожидается строка или URL",
        "url_parsing": "Некорректный URL: {error}",
        "email_type": "Некорректный адрес электронной почты",
        "json_invalid": "Ошибка разбора JSON: {error}",
        "json_type": "JSON-данные должны быть строкой, байтами или массивом байтов",
        "extra_forbidden": "Дополнительные поля не допускаются"
    },
}


def get_language(request: Request) -> str:
    """Extract preferred supported language from the Accept-Language header."""
    header = request.headers.get("Accept-Language", "")
    for part in header.replace(",", " ").split():
        lang = part.split(";")[0].strip().lower()[:2]
        if lang in SUPPORTED_LANGUAGES:
            return lang
    return DEFAULT_LANGUAGE


def translate(key: str, lang: str, **ctx: object) -> str:
    """Return a translated string for *key* in *lang*, interpolating *ctx*."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = lang_dict.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if ctx:
        try:
            return template.format(**ctx)
        except (KeyError, IndexError):
            return template
    return template


def translate_http_detail(detail: object, lang: str) -> object:
    """Translate an HTTPException detail value if it is a known message key.

    Routers raise HTTPException with either:
    - a plain string key  →  ``raise HTTPException(detail="ticket_not_found")``
    - a dict with ``key`` and optional ``ctx``  →  for messages with dynamic parts
    """
    if isinstance(detail, str):
        if detail in TRANSLATIONS[DEFAULT_LANGUAGE]:
            return translate(detail, lang)
    elif isinstance(detail, dict) and "key" in detail:
        key = detail["key"]
        ctx = detail.get("ctx", {})
        return translate(key, lang, **ctx)
    return detail


def translate_validation_errors(errors: list[dict], lang: str) -> list[dict]:
    """Translate *msg* in each Pydantic v2 validation error using the error *type*."""
    result: list[dict] = []
    en_dict = TRANSLATIONS[DEFAULT_LANGUAGE]
    for error in errors:
        error_copy = dict(error)
        error_type = error.get("type", "")
        if error_type in en_dict:
            ctx = error.get("ctx", {})
            # Only scalar values are safe to forward as format arguments.
            safe_ctx = {k: v for k, v in ctx.items() if isinstance(v, (str, int, float, bool))}
            error_copy["msg"] = translate(error_type, lang, **safe_ctx)
        result.append(error_copy)
    return result
