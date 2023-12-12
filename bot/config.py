import os


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    @property
    def is_prod(self):
        return os.getenv('ENV', 'DEV') == 'PROD'
