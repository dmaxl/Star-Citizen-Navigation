"""Command line interface."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import pyperclip
import sys
import time

from . import BASE_LOGGER
from .compute import compute_planetary_nav, compute_space_nav, compute_companion
from .db import getDatabase, getSettings
from .types import Location, Vector
from .utils import get_local_coordinates_from_latlon


logger = logging.getLogger(__name__)


def str_true_false(s):
    if not isinstance(s, str):
        raise TypeError(f"Expected string, not {type(s)}")

    s_lower = s.lower()

    if s_lower == "true":
        return True
    elif s_lower == "false":
        return False
    else:
        return ValueError(f"Expected true or false, not '{s}'")

def main():
    SETTINGS = getSettings()
    DATABASE = getDatabase()

    # if SETTINGS["update_checker"] == True:
    #     checkUpdate()

    parser = argparse.ArgumentParser(description='Command line interface to Star Citizen Navigation library.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    parser.add_argument("mode", choices=["planetary_nav", "space_nav", "companion"])
    parser.add_argument("--container", type=str)
    parser.add_argument("--known", type=str_true_false)
    parser.add_argument("--target", type=str)
    parser.add_argument("--entry_type", type=str, choices=["xyz", "oms", "longlatheight"])
    parser.add_argument("--x", type=float)
    parser.add_argument("--y", type=float)
    parser.add_argument("--z", type=float)
    parser.add_argument("--OM1_name", type=str)
    parser.add_argument("--OM1_value", type=float)
    parser.add_argument("--OM2_name", type=str)
    parser.add_argument("--OM2_value", type=float)
    parser.add_argument("--OM3_name", type=str)
    parser.add_argument("--OM3_value", type=float)
    parser.add_argument("--height", type=float)
    parser.add_argument("--lat", type=float)
    parser.add_argument("--long", type=float)

    args = parser.parse_args()

    loglvls = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    BASE_LOGGER.setLevel(loglvls[min(args.verbose, len(loglvls)-1)])
    logger.setLevel(loglvls[min(args.verbose, len(loglvls)-1)])

    if args.mode == "planetary_nav":
        if args.container is None:
            parser.print_usage("--container required for planetary_nav", file=sys.stderr)
            sys.exit(2)

        if not args.container in DATABASE['Containers']:
            print(f"Unknown container: '{args.container}'", file=sys.stderr)
            sys.exit(2)

        if args.known:
            if args.target is None:
                parser.print_usage("--target required for known target", file=sys.stderr)
                sys.exit(2)

            if not args.target in DATABASE["Containers"][args.container].pois:
                print(f"Unknown target '{args.target}' for container '{args.container}'", file=sys.stderr)
                sys.exit(2)

            Target = DATABASE["Containers"][args.container].pois[args.target]
        else :
            if args.entry_type == "xyz":
                if args.x is None or args.y is None or args.z is None:
                    parser.print_usage("X Y and Z coordinates required", file=sys.stderr)
                    sys.exit(2)

                Target = Location('Custom POI', args.container, Vector(args.x, args.y, args.z), None, False)

            elif args.entry_type == "oms":
                arg_OM1_name = args.OM1_name
                arg_OM1_value = args.OM1_value
                arg_OM2_name = args.OM2_name
                arg_OM2_value = args.OM2_value
                arg_OM3_name = args.OM3_name
                arg_OM3_value = args.OM3_value
                #
                # add some things here
                #

            else:
                if args.lat is None or args.long is None or args.height is None:
                    parser.print_usage("Latitude, longitude, and height required", file=sys.stderr)
                    sys.exit(2)

                local_coordinates = get_local_coordinates_from_latlon(args.lat, args.long, args.height, DATABASE["Containers"][args.container])
                Target = Location('Custom POI', args.container, local_coordinates, None, False)

    elif args.mode == "space_nav":
        if args.known:
            if args.target is None:
                parser.print_usage("--target required for known target", file=sys.stderr)
                sys.exit(2)

            if not args.target in DATABASE["Space_POI"]:
                print(f"Unknown target '{args.target}'", file=sys.stderr)
                sys.exit(2)

            Target = DATABASE["Space_POI"][args.target]
        else:
            if args.x is None or args.y is None or args.z is None:
                parser.print_usage("X Y and Z coordinates required", file=sys.stderr)
                sys.exit(2)

            Target = Location('Custom POI', None, Vector(args.x, args.y, args.z), None, False)

    elif args.mode == "companion":
        pass

    else:
        raise SystemExit("Program mode not selected")

    logger.info("Python script ready to start !")
    logger.info("Mode: %s", args.mode)

    try :
        import ntplib
        c = ntplib.NTPClient()
        response = c.request('us.pool.ntp.org', version=3)
        server_time = response.tx_time
        time_offset = response.offset
    except:
        logger.warning("Could not get time offset from NTP server, assuming 0. Navigation may be inaccurate.")
        time_offset = 0

    logger.info('Time_offset: %f', time_offset)

    if SETTINGS["logs_enabled"] == True:
        if not os.path.isdir('Logs'):
            os.mkdir('Logs')

        if not os.path.isfile('Logs/Logs.csv'):
            field = ['Key', 'System' ,'Global_X', 'Global_Y', 'Global_Z', 'Container', 'Local_X', 'Local_Y', 'Local_Z', 'Longitude', 'Latitude', 'Height', 'Time', 'Readable_Time', 'Player', 'Comment']
            with open("Logs/Logs.csv","w+", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(field)

        New_run_field = ['New_Run']
        with open(r'Logs/Logs.csv', 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(New_run_field)

    #Reset the clipboard content
    pyperclip.copy("")
    old_clipboard = ""

    while True:
        #Get the new clipboard content
        new_clipboard = pyperclip.paste()

        #If clipboard content hasn't changed
        if new_clipboard == old_clipboard or new_clipboard == "":
            #Wait some time
            time.sleep(1/5)
            continue

        #If clipboard content has changed
        #update the memory with the new content
        old_clipboard = new_clipboard
        new_time = time.time() + time_offset

        if not new_clipboard.startswith("Coordinates:"):
            continue

        #If it contains some coordinates
        #split the clipboard in sections
        new_clipboard_splitted = new_clipboard.replace(":", " ").split(" ")

        #get the 3 new XYZ coordinates
        new_player_global_coordinates = Vector(
            float(new_clipboard_splitted[3])/1000,
            float(new_clipboard_splitted[5])/1000,
            float(new_clipboard_splitted[7])/1000
        )

        # for debugging with saved data, manually specify the time
        if len(new_clipboard_splitted) == 10:
            new_time = float(new_clipboard_splitted[9])

        #-----------------------------------------------------planetary_nav--------------------------------------------------------------
        # If the target is within the attraction of a planet
        if args.mode == "planetary_nav":
            new_data = compute_planetary_nav(new_player_global_coordinates, Target, new_time)
            print("New data :", json.dumps(new_data), flush=True)

        #-----------------------------------------------------space_nav------------------------------------------------------------------
        #If the target is within the attraction of a planet
        elif args.mode == "space_nav":
            new_data = compute_space_nav(new_player_global_coordinates, Target, new_time)
            print("New data :", json.dumps(new_data), flush=True)

        #-----------------------------------------------------companion------------------------------------------------------------------
        elif args.mode == "companion":
            new_data = compute_companion(new_player_global_coordinates, new_time)
            print("New data :", json.dumps(new_data), flush=True)

        else:
            raise NotImplementedError("Mode not implemented")


if __name__ == '__main__':
    main()


# Coordinates: x:22461530483.272205 y:37185370964.916862 z:744834.745993 T:1674866002.708849
# Coordinates: x:22461531168.923325 y:37185369949.868736 z:744834.745993 T:1674866006.975523
# Coordinates: x:22461531891.279739 y:37185368884.797295 z:744834.745993 T:1674866011.4724286
