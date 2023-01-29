"""Command line interface."""

from __future__ import annotations

from math import sqrt, degrees, radians, cos, acos, sin, asin, tan ,atan2, copysign, pi
import pyperclip
import time
import datetime
import tkinter as tk
import tkinter.ttk as ttk
import json
import os
import csv
import sys
import requests
import webbrowser
import argparse

from .compute import compute_planetary_nav
from .db import getDatabase, getSettings
from .types import Location, Vector
from .utils import get_local_coordinates_from_latlon


def checkUpdate():
    Local_version =  "2.1.1"

    release_request_url = "https://api.github.com/repos/Valalol/Star-Citizen-Navigation/releases"


    r = requests.get(release_request_url)
    content = r.json()

    Status_code = r.status_code
    Github_version = content[0]['tag_name']
    Download_URL = content[0]['html_url']
    Release_content = content[0]['name']

    if Status_code == 200 :
        if Github_version.replace(".", "") > Local_version.replace(".", ""):
            print("New version available")
            sys.stdout.flush()
            def Go_to_release_func():
                webbrowser.open(Download_URL)
                root.destroy()
                raise SystemExit("Opened the new release page in your browser")

            def Next_time_func():
                root.destroy()

            root = tk.Tk()
            root.title("Update Checker")

            MainWindow = tk.Frame(root)
            MainWindow.configure(borderwidth='0', height='200', relief='flat', width='200')
            MainWindow.pack(expand='true', fill='both', side='left')

            Update_Text = tk.Label(MainWindow, text=f"A new release is available !\n\nNew content :\n{Release_content}\n\nWould you like to go to the release page ?")
            Update_Text.grid(row='0', column='0', padx='40', pady='3')

            Button_Frame = tk.Frame(MainWindow)
            Button_Frame.configure(borderwidth='0', height='200', relief='flat', width='200')
            Button_Frame.grid(row='1', column='0', pady='6')

            Go_to_release_Button = tk.Button(Button_Frame, text="Go to release", command=Go_to_release_func)
            Next_time_Button = tk.Button(Button_Frame, text="Next time", command=Next_time_func)

            Go_to_release_Button.grid(row='0', column='0', padx='10', pady='2')
            Next_time_Button.grid(row='0', column='1', padx='10', pady='2')

            root.mainloop()


SETTINGS = getSettings()
DATABASE = getDatabase()

if SETTINGS["update_checker"] == True:
    checkUpdate()

Container_list = []
for i in DATABASE["Containers"]:
    Container_list.append(DATABASE["Containers"][i].name)

Space_POI_list = []
for poi in DATABASE["Space_POI"]:
    Space_POI_list.append(poi)

Planetary_POI_list = {}
for container_name in DATABASE["Containers"]:
    Planetary_POI_list[container_name] = []
    for poi in DATABASE["Containers"][container_name].pois:
        Planetary_POI_list[container_name].append(poi)


def main():
    parser = argparse.ArgumentParser(description='Command line interface to Star Citizen Navigation library.')

    parser.add_argument("mode", choices=["planetary_nav", "space_nav", "companion"])
    parser.add_argument("--container", type=str)
    parser.add_argument("--known", type=str)
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

    # print(args)

    Mode = args.mode

    if Mode == "planetary_nav":
        arg_container = args.container
        arg_known = args.known
        if arg_known == "true":
            arg_target = args.target
            Target = DATABASE["Containers"][arg_container].pois[arg_target]

        else :
            arg_entry_type = args.entry_type
            if arg_entry_type == "xyz":
                arg_x = args.x
                arg_y = args.y
                arg_z = args.z
                Target = Location('Custom POI', arg_container, Vector(arg_x, arg_y, arg_z), None, False)
                # Target = {
                #     'Name': 'Custom POI',
                #     'Container': arg_container,
                #     'X': arg_x,
                #     'Y': arg_y,
                #     'Z': arg_z,
                #     "QTMarker": "FALSE"
                # }

            elif arg_entry_type == "oms":
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
                local_coordinates = get_local_coordinates_from_latlon(args.lat, args.long, args.height, DATABASE["Containers"][arg_container])
                Target = Location('Custom POI', arg_container, local_coordinates, None, False)
                # Target = {
                #     'Name': 'Custom POI',
                #     'Container': arg_container,
                #     'X': local_coordinates['X'],
                #     'Y': local_coordinates['Y'],
                #     'Z': local_coordinates['Z'],
                #     "QTMarker": "FALSE"
                # }

    elif Mode == "space_nav":
        arg_known = args.known
        if arg_known == "true":
            arg_target = args.target
            Target = DATABASE["Space_POI"][arg_target]
        else:
            arg_x = args.x
            arg_y = args.y
            arg_z = args.z
            Target = Location('Custom POI', None, Vector(arg_x, arg_y, arg_z), None, False)
            # Target = {
            #     'Name': 'Custom POI',
            #     'X': arg_x,
            #     'Y': arg_y,
            #     'Z': arg_z,
            #     "QTMarker": "FALSE"
            # }

    elif Mode == "companion":
        pass

    else:
        raise SystemExit("Program mode not selected")


    logs_enabled = SETTINGS["logs_enabled"]

    print("Python script ready to start !")
    print("Mode: " + Mode)



    try :
        import ntplib
        c = ntplib.NTPClient()
        response = c.request('us.pool.ntp.org', version=3)
        server_time = response.tx_time
        time_offset = response.offset
    except:
        print("Error: Could not get time from NTP server")
        sys.stdout.flush()
        time_offset = 0

    print('Time_offset:', time_offset)
    sys.stdout.flush()

    #Sets some variables
    Reference_time_UTC = datetime.datetime(2020, 1, 1)
    Epoch = datetime.datetime(1970, 1, 1)
    Reference_time = (Reference_time_UTC - Epoch).total_seconds()


    if logs_enabled == True:
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




    Old_clipboard = ""

    #Reset the clipboard content
    pyperclip.copy("")

    while True:

        #Get the new clipboard content
        new_clipboard = pyperclip.paste()

        #If clipboard content hasn't changed
        if new_clipboard == Old_clipboard or new_clipboard == "":
            #Wait some time
            time.sleep(1/5)

        #If clipboard content has changed
        else :

            #update the memory with the new content
            Old_clipboard = new_clipboard

            New_time = time.time() + time_offset

            #If it contains some coordinates
            if new_clipboard.startswith("Coordinates:"):


                #split the clipboard in sections
                new_clipboard_splitted = new_clipboard.replace(":", " ").split(" ")


                #get the 3 new XYZ coordinates
                New_Player_Global_coordinates = Vector(
                    float(new_clipboard_splitted[3])/1000,
                    float(new_clipboard_splitted[5])/1000,
                    float(new_clipboard_splitted[7])/1000
                )

                # for debugging with saved data, manually specify the time
                if len(new_clipboard_splitted) == 10:
                    New_time = float(new_clipboard_splitted[9])



                #-----------------------------------------------------planetary_nav--------------------------------------------------------------
                # If the target is within the attraction of a planet
                if Mode == "planetary_nav":
                    new_data = compute_planetary_nav(New_Player_Global_coordinates, Target, New_time)
                    print("New data :", json.dumps(new_data))
                    sys.stdout.flush()

                    #-------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    main()


# Coordinates: x:22461530483.272205 y:37185370964.916862 z:744834.745993 T:1674866002.708849
# Coordinates: x:22461531168.923325 y:37185369949.868736 z:744834.745993 T:1674866006.975523
# Coordinates: x:22461531891.279739 y:37185368884.797295 z:744834.745993 T:1674866011.4724286
