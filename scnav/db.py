"""Location database."""

import json
import logging
from pathlib import Path
import sqlite3
from typing import Mapping

from .types import Vector, Quaternion, Location, OrbitalBody


DEFAULT_DB_FILE = Path(__file__).resolve().parent / 'verse.db'

_DICT_DATABASE: Mapping[str, Mapping[str, OrbitalBody]] = None

logger = logging.getLogger(__name__)


def make_location_kwargs(data: dict):
    return {
        'name': data['Name'],
        'parent': data['Container'] if 'Container' in data else None,
        'coords': Vector(data['X'], data['Y'], data['Z']),
        'rotation': Quaternion(data['qw'], data['qx'], data['qy'], data['qz']),
        'qtmarker': True if data['QTMarker'] == 'TRUE' else False,
    }

def getDatabase():
    global _DICT_DATABASE
    if _DICT_DATABASE is None:
        with open('Database.json') as f:
            data = json.load(f)

        _DICT_DATABASE = {
            'Containers': dict(),
            'Space_POI': dict(),
        }

        for orbitalbodyname, orbitalbody in data['Containers'].items():
            pois = dict()
            for poiname, poi in orbitalbody['POI'].items():
                kwargs = make_location_kwargs(poi)
                pois[poiname] = Location(**kwargs)

            kwargs = make_location_kwargs(orbitalbody)
            for key in ('OM Radius', 'Body Radius', 'Arrival Radius',
                'Time Lines', 'Rotation Speed', 'Rotation Adjust',
                'Orbital Radius', 'Orbital Speed', 'Orbital Angle', 'Grid Radius'):
                kwargs[key.lower().replace(' ', '_')] = orbitalbody[key]
            kwargs['pois'] = pois

            _DICT_DATABASE['Containers'][orbitalbodyname] = OrbitalBody(**kwargs)

    return _DICT_DATABASE

def getSettings() -> dict:
    with open("settings.json", "r") as f:
        settings = json.load(f)
    return settings

######

# class Database:
#     def __init__(self, dbfile=DEFAULT_DB_FILE):
#         self.dbfile = dbfile
#         self.dbcon = sqlite3.connect(self.dbfile)

#     def __del__(self):
#         if self.dbcon:
#             self.dbcon.close()

# def yield_pois(pois, parent_id):
#     for key, poi in pois.items():
#         yield (poi['Name'], parent_id,
#             poi['X'], poi['Y'], poi['Z'],
#             poi['qw'], poi['qx'], poi['qy'], poi['qz'],
#             poi['QTMarker'])

# def init_database_from_json(jsonfile, dbfile):
#     with open(jsonfile) as f:
#         data = json.load(f)

#     con = sqlite3.connect(dbfile)
#     con.execute("PRAGMA foreign_keys = ON")

#     con.execute("""CREATE TABLE orbital_body (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL,
#         x REAL NOT NULL,
#         y REAL NOT NULL,
#         z REAL NOT NULL,
#         qw REAL NOT NULL,
#         qx REAL NOT NULL,
#         qy REAL NOT NULL,
#         qz REAL NOT NULL,
#         qtmarker BOOL NOT NULL,
#         om_radius REAL NOT NULL,
#         body_radius REAL NOT NULL,
#         arrival_radius REAL NOT NULL,
#         time_lines REAL NOT NULL,
#         rotation_speed REAL NOT NULL,
#         rotation_adjust REAL NOT NULL,
#         orbital_radius REAL NOT NULL,
#         orbital_speed REAL NOT NULL,
#         orbital_angle REAL NOT NULL,
#         grid_radius REAL NOT NULL
# )""")

#     con.execute("""CREATE TABLE poi (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL,
#         parent INTEGER NOT NULL REFERENCES orbital_body(id) ON DELETE RESTRICT,
#         x REAL NOT NULL,
#         y REAL NOT NULL,
#         z REAL NOT NULL,
#         qw REAL NOT NULL,
#         qx REAL NOT NULL,
#         qy REAL NOT NULL,
#         qz REAL NOT NULL,
#         qtmarker BOOL NOT NULL
# )""")

#     for key, container in data['Containers'].items():
#         name = key
#         if 'Name' in container and container['Name'] != name:
#             logger.warning("Container name attribute differs from key: %s != %s",
#                 container['Name'], key)
#             name = container['Name']

#         cur = con.cursor()
#         cur.execute(
#             "INSERT INTO orbital_body VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
#             container['Name'],
#             container['X'], container['Y'], container['Z'],
#             container['qw'], container['qx'], container['qy'], container['qz'],
#             container['QTMarker'], container['OM Radius'], container['Body Radius'], container['Arrival Radius'],
#             container['Time Lines'], container['Rotation Speed'], container['Rotation Adjust'], container['Orbital Radius'],
#             container['Orbital Speed'], container['Orbital Angle'], container['Grid Radius']
#         )
