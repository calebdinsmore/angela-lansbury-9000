from typing import Dict, Optional


class ParsedValue:
    def __init__(self, json: Dict):
        self.json = json

    @property
    def time_value(self):
        if self.value:
            return self.value
        if self.json.get('to'):
            return self.json['from']['value']

    @property
    def values(self):
        return [ParsedValue(json) for json in self.json.get('values', [])]

    @property
    def value(self) -> str:
        return self.json.get('value', '')

    @property
    def grain(self) -> str:
        return self.json.get('grain', '')

    @property
    def type(self) -> str:
        return self.json.get('type', '')


class ParsedValues:
    def __init__(self, json: Dict):
        self.json = json

    @property
    def body(self) -> str:
        return self.json.get('body', '')

    @property
    def start(self) -> Optional[int]:
        return self.json.get('start')

    @property
    def value(self) -> ParsedValue:
        return ParsedValue(self.json.get('value', {}))

    @property
    def end(self) -> Optional[int]:
        return self.json.get('end')

    @property
    def dim(self) -> str:
        return self.json.get('dim', '')

    @property
    def latent(self) -> bool:
        return self.json.get('latent', False)

