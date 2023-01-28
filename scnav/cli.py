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

from .db import getDatabase, getSettings
from .types import *
from .utils import *


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
                local_coordinates = get_local_vector_from_latlon(args.lat, args.long, args.height, DATABASE["Containers"][arg_container])
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

    Old_player_Global_coordinates = Vector(0, 0, 0)

    Old_player_local_rotated_coordinates = Vector(0, 0, 0)

    Old_Distance_to_POI = Vector(0, 0, 0)

    Old_container = None


    Old_time = time.time()


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



                    #---------------------------------------------------Actual Container----------------------------------------------------------------
                    #search in the Databse to see if the player is ina Container
                    Actual_Container = get_current_container(New_Player_Global_coordinates)



                    #---------------------------------------------------New player local coordinates----------------------------------------------------
                    #Time passed since the start of game simulation
                    Time_passed_since_reference_in_seconds = New_time - Reference_time

                    New_player_local_rotated_coordinates = get_local_rotated_coordinates(Time_passed_since_reference_in_seconds, New_Player_Global_coordinates, Actual_Container)


                    #---------------------------------------------------New target local coordinates----------------------------------------------------
                    #Grab the rotation speed of the container in the Database and convert it in degrees/s
                    target_Rotation_speed_in_hours_per_rotation = DATABASE["Containers"][Target.parent].rotation_speed
                    try:
                        target_Rotation_speed_in_degrees_per_second = 0.1 * (1/target_Rotation_speed_in_hours_per_rotation)
                    except ZeroDivisionError:
                        target_Rotation_speed_in_degrees_per_second = 0

                    #Get the actual rotation state in degrees using the rotation speed of the container, the actual time and a rotational adjustment value
                    target_Rotation_state_in_degrees = ((target_Rotation_speed_in_degrees_per_second * Time_passed_since_reference_in_seconds) + DATABASE["Containers"][Target.parent].rotation_adjust) % 360

                    #get the new player rotated coordinates
                    target_rotated_coordinates = Target.coords.rotateZ(radians(target_Rotation_state_in_degrees))




                    #-------------------------------------------------player local Long Lat Height--------------------------------------------------

                    if Actual_Container.name != "None":
                        player_Latitude, player_Longitude, player_Height = get_lat_long_height(New_player_local_rotated_coordinates, Actual_Container)

                    #-------------------------------------------------target local Long Lat Height--------------------------------------------------
                    target_Latitude, target_Longitude, target_Height = get_lat_long_height(Target.coords, DATABASE["Containers"][Target.parent])



                    #---------------------------------------------------Distance to POI-----------------------------------------------------------------
                    New_Distance_to_POI = {}

                    if Actual_Container == Target.parent:
                        New_Distance_to_POI = Target.coords - New_player_local_rotated_coordinates
                    else:
                        New_Distance_to_POI = target_rotated_coordinates + DATABASE["Containers"][Target.parent].coord - New_Player_Global_coordinates

                    #get the real new distance between the player and the target
                    New_Distance_to_POI_Total = New_Distance_to_POI.magnitude()

                    if New_Distance_to_POI_Total <= 100:
                        New_Distance_to_POI_Total_color = "#00ff00"
                    elif New_Distance_to_POI_Total <= 1000:
                        New_Distance_to_POI_Total_color = "#ffd000"
                    else :
                        New_Distance_to_POI_Total_color = "#ff3700"


                    #---------------------------------------------------Delta Distance to POI-----------------------------------------------------------
                    #get the real old distance between the player and the target
                    Old_Distance_to_POI_Total = Old_Distance_to_POI.magnitude()




                    #get the 3 XYZ distance travelled since last update
                    Delta_Distance_to_POI = New_Distance_to_POI - Old_Distance_to_POI

                    #get the real distance travelled since last update
                    Delta_Distance_to_POI_Total = New_Distance_to_POI_Total - Old_Distance_to_POI_Total

                    if Delta_Distance_to_POI_Total <= 0:
                        Delta_distance_to_poi_color = "#00ff00"
                    else:
                        Delta_distance_to_poi_color = "#ff3700"



                    #---------------------------------------------------Estimated time of arrival to POI------------------------------------------------
                    #get the time between the last update and this update
                    Delta_time = New_time - Old_time


                    #get the time it would take to reach destination using the same speed
                    try :
                        Estimated_time_of_arrival = (Delta_time*New_Distance_to_POI_Total)/abs(Delta_Distance_to_POI_Total)
                    except ZeroDivisionError:
                        Estimated_time_of_arrival = 0.00



                    #----------------------------------------------------Closest Quantumable POI--------------------------------------------------------
                    if not Target.qtmarker:
                        Target_to_POIs_Distances_Sorted = get_closest_POI(Target.coords, DATABASE["Containers"][Target.parent], True)

                    else :
                        Target_to_POIs_Distances_Sorted = [{
                            "Name" : "POI itself",
                            "Distance" : 0
                        }]


                    #----------------------------------------------------Player Closest POI--------------------------------------------------------
                    Player_to_POIs_Distances_Sorted = get_closest_POI(New_player_local_rotated_coordinates, Actual_Container, False)


                    #-------------------------------------------------------3 Closest OMs to player---------------------------------------------------------------
                    player_Closest_OM = get_closest_oms(New_player_local_rotated_coordinates, Actual_Container)



                    #-------------------------------------------------------3 Closest OMs to target---------------------------------------------------------------
                    target_Closest_OM = get_closest_oms(Target.coords, DATABASE["Containers"][Target.parent])



                    #----------------------------------------------------Course Deviation to POI--------------------------------------------------------
                    #get the vector between current_pos and previous_pos
                    Previous_current_pos_vector = New_player_local_rotated_coordinates - Old_player_local_rotated_coordinates


                    #get the vector between current_pos and target_pos
                    Current_target_pos_vector = Target.coords - New_player_local_rotated_coordinates


                    #get the angle between the current-target_pos vector and the previous-current_pos vector
                    Total_deviation_from_target = degrees(Previous_current_pos_vector.angle_between(Current_target_pos_vector))


                    if Total_deviation_from_target <= 10:
                        Total_deviation_from_target_color = "#00ff00"
                    elif Total_deviation_from_target <= 20:
                        Total_deviation_from_target_color = "#ffd000"
                    else:
                        Total_deviation_from_target_color = "#ff3700"


                    #----------------------------------------------------------Flat_angle--------------------------------------------------------------
                    previous = Old_player_local_rotated_coordinates
                    current = New_player_local_rotated_coordinates


                    #Vector AB (Previous -> Current)
                    previous_to_current = current - previous

                    #Vector AC (C = center of the planet, Previous -> Center)
                    previous_to_center = Vector(0, 0, 0) - previous

                    #Vector BD (Current -> Target)
                    current_to_target = Target.coords - current

                    #Vector BC (C = center of the planet, Current -> Center)
                    current_to_center = Vector(0, 0, 0) - current



                    #Normal vector of a plane:
                    #abc : Previous/Current/Center
                    n1 = previous_to_current.cross(previous_to_center)

                    #acd : Previous/Center/Target
                    n2 = current_to_target.cross(current_to_center)

                    Flat_angle = degrees(n1.angle_between(n2))


                    if Flat_angle <= 10:
                        Flat_angle_color = "#00ff00"
                    elif Flat_angle <= 20:
                        Flat_angle_color = "#ffd000"
                    else:
                        Flat_angle_color = "#ff3700"




                    #----------------------------------------------------------Heading--------------------------------------------------------------

                    bearingX = cos(radians(target_Latitude)) * sin(radians(target_Longitude) - radians(player_Longitude))
                    bearingY = cos(radians(player_Latitude)) * sin(radians(target_Latitude)) - sin(radians(player_Latitude)) * cos(radians(target_Latitude)) * cos(radians(target_Longitude) - radians(player_Longitude))

                    Bearing = (degrees(atan2(bearingX, bearingY)) + 360) % 360




                    #-------------------------------------------------Sunrise Sunset Calculation----------------------------------------------------
                    JulianDate = Time_passed_since_reference_in_seconds/(24*60*60)

                    player_state_of_the_day, player_next_event, player_next_event_time = get_sunset_sunrise_predictions(
                        player_Latitude,
                        player_Longitude,
                        player_Height,
                        Actual_Container,
                        DATABASE["Containers"]["Stanton"],
                        JulianDate
                    )

                    target_state_of_the_day, target_next_event, target_next_event_time = get_sunset_sunrise_predictions(
                        target_Latitude,
                        target_Longitude,
                        target_Height,
                        DATABASE["Containers"][Target.parent],
                        DATABASE["Containers"]["Stanton"],
                        JulianDate
                    )


                    #------------------------------------------------------------Backend to Frontend------------------------------------------------------------
                    new_data = {
                        "updated" : f"{time.strftime('%H:%M:%S', time.localtime(New_time))}",
                        "target" : Target.name,
                        "player_actual_container" : Actual_Container.name,
                        "target_container" : Target.parent,
                        "player_x" : round(New_player_local_rotated_coordinates.x, 3),
                        "player_y" : round(New_player_local_rotated_coordinates.y, 3),
                        "player_z" : round(New_player_local_rotated_coordinates.z, 3),
                        "player_long" : f"{round(player_Longitude, 2)}°",
                        "player_lat" : f"{round(player_Latitude, 2)}°",
                        "player_height" : f"{round(player_Height, 1)} km",
                        "player_OM1" : f"{player_Closest_OM['Z']['OM'].name} : {round(player_Closest_OM['Z']['Distance'], 3)} km",
                        "player_OM2" : f"{player_Closest_OM['Y']['OM'].name} : {round(player_Closest_OM['Y']['Distance'], 3)} km",
                        "player_OM3" : f"{player_Closest_OM['X']['OM'].name} : {round(player_Closest_OM['X']['Distance'], 3)} km",
                        "player_closest_poi" : f"{Player_to_POIs_Distances_Sorted[0]['Name']} : {round(Player_to_POIs_Distances_Sorted[0]['Distance'], 3)} km",
                        "player_state_of_the_day" : f"{player_state_of_the_day}",
                        "player_next_event" : f"{player_next_event}",
                        "player_next_event_time" : f"{time.strftime('%H:%M:%S', time.localtime(New_time + player_next_event_time*60))}",
                        "target_x" : Target.coords.x,
                        "target_y" : Target.coords.y,
                        "target_z" : Target.coords.z,
                        "target_long" : f"{round(target_Longitude, 2)}°",
                        "target_lat" : f"{round(target_Latitude, 2)}°",
                        "target_height" : f"{round(target_Height, 1)} km",
                        "target_OM1" : f"{target_Closest_OM['Z']['OM'].name} : {round(target_Closest_OM['Z']['Distance'], 3)} km",
                        "target_OM2" : f"{target_Closest_OM['Y']['OM'].name} : {round(target_Closest_OM['Y']['Distance'], 3)} km",
                        "target_OM3" : f"{target_Closest_OM['X']['OM'].name} : {round(target_Closest_OM['X']['Distance'], 3)} km",
                        "target_closest_QT_beacon" : f"{Target_to_POIs_Distances_Sorted[0]['Name']} : {round(Target_to_POIs_Distances_Sorted[0]['Distance'], 3)} km",
                        "target_state_of_the_day" : f"{target_state_of_the_day}",
                        "target_next_event" : f"{target_next_event}",
                        "target_next_event_time" : f"{time.strftime('%H:%M:%S', time.localtime(New_time + target_next_event_time*60))}",
                        "distance_to_poi" : f"{round(New_Distance_to_POI_Total, 3)} km",
                        "distance_to_poi_color" : New_Distance_to_POI_Total_color,
                        "delta_distance_to_poi" : f"{round(abs(Delta_Distance_to_POI_Total), 3)} km",
                        "delta_distance_to_poi_color" : Delta_distance_to_poi_color,
                        "total_deviation" : f"{round(Total_deviation_from_target, 1)}°",
                        "total_deviation_color" : Total_deviation_from_target_color,
                        "horizontal_deviation" : f"{round(Flat_angle, 1)}°",
                        "horizontal_deviation_color" : Flat_angle_color,
                        "heading" : f"{round(Bearing, 1)}°",
                        "ETA" : f"{str(datetime.timedelta(seconds=round(Estimated_time_of_arrival, 0)))}"
                    }
                    print("New data :", json.dumps(new_data))
                    sys.stdout.flush()


                    #------------------------------------------------------------Logs update------------------------------------------------------------
                    if logs_enabled == True:
                        if Actual_Container.name and Actual_Container.name != "None":
                            fields = [
                                'None',
                                'Stanton',
                                str(New_player_local_rotated_coordinates.x*1000),
                                str(New_player_local_rotated_coordinates.y*1000),
                                str(New_player_local_rotated_coordinates.z*1000),
                                str(Actual_Container.name),
                                str(New_player_local_rotated_coordinates.x),
                                str(New_player_local_rotated_coordinates.y),
                                str(New_player_local_rotated_coordinates.z),
                                str(player_Longitude),
                                str(player_Latitude),
                                str(player_Height*1000),
                                str(New_time),
                                time.strftime('%d %b %Y %H:%M:%S', time.gmtime(New_time)),
                                "",
                                ""
                            ]
                            # field = [
                            #     'Key',
                            #     'System',
                            #     'Global_X',
                            #     'Global_Y',
                            #     'Global_Z',
                            #     'Container',
                            #     'Local_X',
                            #     'Local_Y',
                            #     'Local_Z',
                            #     'Longitude',
                            #     'Latitude',
                            #     'Height',
                            #     'Time',
                            #     'Readable_Time',',
                            #     'Player',
                            #     'Comment'
                            # ]

                            with open(r'Logs/Logs.csv', 'a', newline='') as csv_file:
                                writer = csv.writer(csv_file)
                                writer.writerow(fields)



                    #---------------------------------------------------Update coordinates for the next update------------------------------------------
                    Old_player_Global_coordinates = New_Player_Global_coordinates

                    Old_player_local_rotated_coordinates = New_player_local_rotated_coordinates

                    Old_Distance_to_POI = New_Distance_to_POI

                    Old_time = New_time

                    #-------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    main()


# Coordinates: x:22461530483.272205 y:37185370964.916862 z:744834.745993 T:1674866002.708849
# Coordinates: x:22461531168.923325 y:37185369949.868736 z:744834.745993 T:1674866006.975523
# Coordinates: x:22461531891.279739 y:37185368884.797295 z:744834.745993 T:1674866011.4724286
