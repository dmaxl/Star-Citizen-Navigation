from __future__ import annotations

import datetime
from math import sqrt, degrees, radians, cos, acos, sin, asin, tan ,atan2, copysign, pi
import time

from .db import getDatabase
from .types import Location, OrbitalBody, Vector
from .utils import get_local_rotated_coordinates, get_lat_long_height, get_closest_POI, get_closest_oms, get_sunset_sunrise_predictions


DATABASE = getDatabase()

Reference_time_UTC = datetime.datetime(2020, 1, 1)
Epoch = datetime.datetime(1970, 1, 1)
Reference_time = (Reference_time_UTC - Epoch).total_seconds()

Old_player_Global_coordinates = Vector(0, 0, 0)
Old_player_local_rotated_coordinates = Vector(0, 0, 0)
Old_Distance_to_POI = Vector(0, 0, 0)
Old_container = None
Old_time = time.time()


def get_current_container(global_coordinate : Vector):
    for name, orbitalbody in DATABASE["Containers"].items():
        relative_vector = orbitalbody.coords - global_coordinate
        if relative_vector.magnitude() <= 3 * orbitalbody.om_radius:
            Actual_Container = orbitalbody
    return Actual_Container

def compute_planetary_nav(New_Player_Global_coordinates: Vector, Target: Location, timestamp: float):

    global Old_player_Global_coordinates
    global Old_player_local_rotated_coordinates
    global Old_Distance_to_POI
    global Old_container
    global Old_time

    #Time passed since the start of game simulation
    Time_passed_since_reference_in_seconds = timestamp - Reference_time

    #---------------------------------------------------Actual Container----------------------------------------------------------------
    #search in the Databse to see if the player is ina Container
    Actual_Container = get_current_container(New_Player_Global_coordinates)


    #---------------------------------------------------New player local coordinates----------------------------------------------------
    New_player_local_rotated_coordinates = get_local_rotated_coordinates(Time_passed_since_reference_in_seconds, New_Player_Global_coordinates, Actual_Container)


    #---------------------------------------------------New target local coordinates----------------------------------------------------
    #Get the actual rotation tate in degrees using the rotation speed of the container, the actual time and a rotational adjustment value
    target_Rotation_state_in_degrees = DATABASE["Containers"][Target.parent].rotation_at_time(Time_passed_since_reference_in_seconds)

    #get the new player rotated coordinates
    target_rotated_coordinates = Target.coords.rotateZ(radians(target_Rotation_state_in_degrees))


    #-------------------------------------------------player local Long Lat Height--------------------------------------------------
    if Actual_Container.name != "None":
        player_Latitude, player_Longitude, player_Height = get_lat_long_height(New_player_local_rotated_coordinates, Actual_Container)

    #-------------------------------------------------target local Long Lat Height--------------------------------------------------
    target_Latitude, target_Longitude, target_Height = get_lat_long_height(Target.coords, DATABASE["Containers"][Target.parent])


    #---------------------------------------------------Distance to POI-----------------------------------------------------------------
    if Actual_Container == Target.parent:
        New_Distance_to_POI = Target.coords - New_player_local_rotated_coordinates
    else:
        New_Distance_to_POI = target_rotated_coordinates + DATABASE["Containers"][Target.parent].coords - New_Player_Global_coordinates

    #get the real new distance between the player and the target
    New_Distance_to_POI_Total = New_Distance_to_POI.magnitude()

    if New_Distance_to_POI_Total <= 100:
        New_Distance_to_POI_Total_color = "#00ff00"
    elif New_Distance_to_POI_Total <= 1000:
        New_Distance_to_POI_Total_color = "#ffd000"
    else :
        New_Distance_to_POI_Total_color = "#ff3700"


    #---------------------------------------------------Delta Distance to POI-----------------------------------------------------------
    #get the real distance travelled since last update
    Delta_Distance_to_POI_Total = New_Distance_to_POI_Total - Old_Distance_to_POI.magnitude()

    if Delta_Distance_to_POI_Total <= 0:
        Delta_distance_to_poi_color = "#00ff00"
    else:
        Delta_distance_to_poi_color = "#ff3700"


    #---------------------------------------------------Estimated time of arrival to POI------------------------------------------------
    #get the time between the last update and this update
    Delta_time = timestamp - Old_time

    #get the time it would take to reach destination using the same speed
    try :
        Estimated_time_of_arrival = (Delta_time*New_Distance_to_POI_Total)/abs(Delta_Distance_to_POI_Total)
    except ZeroDivisionError:
        Estimated_time_of_arrival = 0.00


    #----------------------------------------------------Closest Quantumable POI--------------------------------------------------------
    if not Target.qtmarker:
        Target_to_POIs_Distances_Sorted = get_closest_POI(Target.coords, DATABASE["Containers"][Target.parent], True)
    else:
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
    #Vector AB (Previous -> Current)
    previous_to_current = New_player_local_rotated_coordinates - Old_player_local_rotated_coordinates

    #Vector AC (C = center of the planet, Previous -> Center)
    previous_to_center = Vector(0, 0, 0) - Old_player_local_rotated_coordinates

    #Vector BD (Current -> Target)
    current_to_target = Target.coords - New_player_local_rotated_coordinates

    #Vector BC (C = center of the planet, Current -> Center)
    current_to_center = Vector(0, 0, 0) - New_player_local_rotated_coordinates


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

    #---------------------------------------------------Update coordinates for the next update------------------------------------------
    Old_player_Global_coordinates = New_Player_Global_coordinates

    Old_player_local_rotated_coordinates = New_player_local_rotated_coordinates

    Old_Distance_to_POI = New_Distance_to_POI

    Old_time = timestamp

    #------------------------------------------------------------Backend to Frontend------------------------------------------------------------
    return {
        "updated" : f"{time.strftime('%H:%M:%S', time.localtime(timestamp))}",
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
        "player_next_event_time" : f"{time.strftime('%H:%M:%S', time.localtime(timestamp + player_next_event_time*60))}",
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
        "target_next_event_time" : f"{time.strftime('%H:%M:%S', time.localtime(timestamp + target_next_event_time*60))}",
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
