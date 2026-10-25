from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.core.mail.backends.filebased import EmailBackend as FileEmailBackend


class DevelopmentEmailBackend(BaseEmailBackend):
    """
    Development backend that prints emails to the console and
    also saves them under EMAIL_FILE_PATH for easy inspection.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.console_backend = ConsoleEmailBackend(fail_silently=fail_silently, **kwargs)
        self.file_backend = FileEmailBackend(fail_silently=fail_silently, **kwargs)

    def send_messages(self, email_messages):
        console_count = self.console_backend.send_messages(email_messages)
        self.file_backend.send_messages(email_messages)
        return console_count
