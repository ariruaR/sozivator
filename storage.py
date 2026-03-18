# Активные сессии рассылки: {user_id: True/False/None}
ACTIVE_SESSION: dict[int, bool | None] = {}

# Хранилище голосов: {poll_id: {user_id: [option_ids]}}
poll_storage: dict[str, dict[int, list[int]]] = {}

# Метаданные опросов: {poll_id: {question, options, chat_id}}
poll_meta: dict[str, dict] = {}