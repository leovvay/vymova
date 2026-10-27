class StepError(Exception):
    """A step error with text for the tutor. retry=False — retrying is pointless (e.g. wrong key)."""

    def __init__(self, message_ru: str, retry: bool = True):
        super().__init__(message_ru)
        self.message_ru = message_ru
        self.retry = retry
