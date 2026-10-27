class StepError(Exception):
    """Ошибка шага с текстом для репетитора. retry=False — повторять бессмысленно (например, неверный ключ)."""

    def __init__(self, message_ru: str, retry: bool = True):
        super().__init__(message_ru)
        self.message_ru = message_ru
        self.retry = retry
