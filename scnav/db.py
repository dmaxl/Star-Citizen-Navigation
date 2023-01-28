"""Location database."""

import json


_DATABASE = None


def getDatabase() -> dict:
    global _DATABASE
    if _DATABASE is None:
        with open('Database.json') as f:
            _DATABASE = json.load(f)
    return _DATABASE

def getSettings() -> dict:
    with open("settings.json", "r") as f:
        settings = json.load(f)
    return settings
