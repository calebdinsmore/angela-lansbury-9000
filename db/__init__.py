"""
Alembic wrapper lives here. When adding a new table to the bot, ensure you import the model here,
otherwise the DB CLI won't pick it up as a DB model when running a migration/create all command.
"""
from sqla_wrapper import Alembic

from db.model import DB
from db.model.activity_module_settings import *
from db.model.auto_delete_channel_config import *
from db.model.image_message_to_delete import *
from db.model.rolling_message_log import *
from db.model.user_activity import *
from db.model.santa_participant import *

alembic = Alembic(DB, 'db/migrations')
