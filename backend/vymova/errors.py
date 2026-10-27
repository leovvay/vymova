class StepError(Exception):
    """Ошибка шага с текстом для репетитора."""

    def __init__(self, message_ru: str):
        super().__init__(message_ru)
        self.message_ru = message_ru
