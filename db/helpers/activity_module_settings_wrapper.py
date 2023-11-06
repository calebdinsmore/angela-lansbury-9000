from db import DB
from db.model.activity_module_settings import ActivityModuleSettings


class ActivityModuleSettingsWrapper:
    def __init__(self, model: ActivityModuleSettings):
        self.model = model
        excluded_channels = model.excluded_channels.split(',') if model.excluded_channels else []
        excluded_channels = [int(c) for c in excluded_channels]
        self._excluded_channels = set(excluded_channels) if excluded_channels else set()

    @property
    def excluded_channels(self):
        return self._excluded_channels

    def add_excluded_channel(self, channel_id: int):
        self._excluded_channels.add(channel_id)
        self.model.excluded_channels = ','.join([str(e) for e in self._excluded_channels])
        DB.s.commit()

    def remove_excluded_channel(self, channel_id: int):
        self._excluded_channels.remove(channel_id)
        self.model.excluded_channels = ','.join([str(e) for e in self._excluded_channels])
        DB.s.commit()
