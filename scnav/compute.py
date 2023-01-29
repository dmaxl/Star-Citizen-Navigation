from __future__ import annotations

import datetime
import logging
from math import degrees, radians, cos, sin, atan2
import time

from .db import getDatabase
from .types import Location, Vector
from .utils import get_local_rotated_coordinates, get_lat_long_height, get_closest_POI, get_closest_oms, get_sunset_sunrise_predictions


DATABASE = getDatabase()

STAR_CITIZEN_REF_TIME_UTC = datetime.datetime(2020, 1, 1)
EPOCH = datetime.datetime(1970, 1, 1)
STAR_CITIZEN_REF_SECONDS = (STAR_CITIZEN_REF_TIME_UTC - EPOCH).total_seconds()

_old_player_Global_coordinates = Vector(0, 0, 0)
_old_player_local_rotated_coordinates = Vector(0, 0, 0)
_old_Distance_to_POI = Vector(0, 0, 0)
_old_container = None
_old_time = time.time()

logger = logging.getLogger(__name__)


def get_current_container(global_coordinate : Vector):
    for name, orbitalbody in DATABASE["Containers"].items():
        relative_vector = orbitalbody.coords - global_coordinate
        if relative_vector.magnitude() <= 3 * orbitalbody.om_radius:
            return orbitalbody
    return None

def compute_planetary_nav(player_global_coordinates: Vector, target: Location, timestamp: float):
    global _old_player_Global_coordinates
    global _old_player_local_rotated_coordinates
    global _old_Distance_to_POI
    global _old_container
    global _old_time

    #Time passed since the start of game simulation
    Time_passed_since_reference_in_seconds = timestamp - STAR_CITIZEN_REF_SECONDS

    #---------------------------------------------------Actual Container----------------------------------------------------------------
    #search in the Databse to see if the player is ina Container
    actual_container = get_current_container(player_global_coordinates)

    if actual_container is None:
        logger.error("Player not in sphere of influence of an orbital body. Planetary navigation not possible.")
        return None
    elif actual_container.name != target.parent:
        logger.error("Player not in same sphere of influence as target. Planetary navigation not possible.")
        return None


    #---------------------------------------------------New player local coordinates----------------------------------------------------
    player_local_rotated_coordinates = get_local_rotated_coordinates(Time_passed_since_reference_in_seconds, player_global_coordinates, actual_container)


    #---------------------------------------------------New target local coordinates----------------------------------------------------
    #Get the actual rotation tate in degrees using the rotation speed of the container, the actual time and a rotational adjustment value
    target_Rotation_state_in_degrees = DATABASE["Containers"][target.parent].rotation_at_time(Time_passed_since_reference_in_seconds)

    #get the new player rotated coordinates
    target_rotated_coordinates = target.coords.rotateZ(radians(target_Rotation_state_in_degrees))


    #-------------------------------------------------player local Long Lat Height--------------------------------------------------
    player_Latitude, player_Longitude, player_Height = get_lat_long_height(player_local_rotated_coordinates, actual_container)

    #-------------------------------------------------target local Long Lat Height--------------------------------------------------
    target_Latitude, target_Longitude, target_Height = get_lat_long_height(target.coords, DATABASE["Containers"][target.parent])


    #---------------------------------------------------Distance to POI-----------------------------------------------------------------
    # if actual_container.name == target.parent:
    New_Distance_to_POI = target.coords - player_local_rotated_coordinates
    # else:
        # New_Distance_to_POI = target_rotated_coordinates + DATABASE["Containers"][target.parent].coords - player_global_coordinates

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
    Delta_Distance_to_POI_Total = New_Distance_to_POI_Total - _old_Distance_to_POI.magnitude()

    if Delta_Distance_to_POI_Total <= 0:
        Delta_distance_to_poi_color = "#00ff00"
    else:
        Delta_distance_to_poi_color = "#ff3700"


    #---------------------------------------------------Estimated time of arrival to POI------------------------------------------------
    #get the time between the last update and this update
    Delta_time = timestamp - _old_time

    #get the time it would take to reach destination using the same speed
    try :
        Estimated_time_of_arrival = (Delta_time*New_Distance_to_POI_Total)/abs(Delta_Distance_to_POI_Total)
    except ZeroDivisionError:
        Estimated_time_of_arrival = 0.00


    #----------------------------------------------------Closest Quantumable POI--------------------------------------------------------
    if not target.qtmarker:
        Target_to_POIs_Distances_Sorted = get_closest_POI(target.coords, DATABASE["Containers"][target.parent], True)
    else:
        Target_to_POIs_Distances_Sorted = [{
            "Name" : "POI itself",
            "Distance" : 0
        }]


    #----------------------------------------------------Player Closest POI--------------------------------------------------------
    Player_to_POIs_Distances_Sorted = get_closest_POI(player_local_rotated_coordinates, actual_container, False)


    #-------------------------------------------------------3 Closest OMs to player---------------------------------------------------------------
    player_Closest_OM = get_closest_oms(player_local_rotated_coordinates, actual_container)


    #-------------------------------------------------------3 Closest OMs to target---------------------------------------------------------------
    target_Closest_OM = get_closest_oms(target.coords, DATABASE["Containers"][target.parent])


    #----------------------------------------------------Course Deviation to POI--------------------------------------------------------
    #get the vector between current_pos and previous_pos
    Previous_current_pos_vector = player_local_rotated_coordinates - _old_player_local_rotated_coordinates

    #get the vector between current_pos and target_pos
    Current_target_pos_vector = target.coords - player_local_rotated_coordinates

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
    previous_to_current = player_local_rotated_coordinates - _old_player_local_rotated_coordinates

    #Vector AC (C = center of the planet, Previous -> Center)
    previous_to_center = Vector(0, 0, 0) - _old_player_local_rotated_coordinates

    #Vector BD (Current -> Target)
    current_to_target = target.coords - player_local_rotated_coordinates

    #Vector BC (C = center of the planet, Current -> Center)
    current_to_center = Vector(0, 0, 0) - player_local_rotated_coordinates


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
        actual_container,
        DATABASE["Containers"]["Stanton"],
        JulianDate
    )

    target_state_of_the_day, target_next_event, target_next_event_time = get_sunset_sunrise_predictions(
        target_Latitude,
        target_Longitude,
        target_Height,
        DATABASE["Containers"][target.parent],
        DATABASE["Containers"]["Stanton"],
        JulianDate
    )


    #---------------------------------------------------Update coordinates for the next update------------------------------------------
    _old_player_Global_coordinates = player_global_coordinates
    _old_player_local_rotated_coordinates = player_local_rotated_coordinates
    _old_Distance_to_POI = New_Distance_to_POI
    _old_container = actual_container
    _old_time = timestamp


    return {
        "updated" : f"{time.strftime('%H:%M:%S', time.localtime(timestamp))}",
        "target" : target.name,
        "player_actual_container" : actual_container.name,
        "target_container" : target.parent,
        "player_x" : round(player_local_rotated_coordinates.x, 3),
        "player_y" : round(player_local_rotated_coordinates.y, 3),
        "player_z" : round(player_local_rotated_coordinates.z, 3),
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
        "target_x" : target.coords.x,
        "target_y" : target.coords.y,
        "target_z" : target.coords.z,
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

def compute_space_nav(player_global_coordinates: Vector, target: Location, timestamp: float):
    global _old_player_Global_coordinates
    global _old_player_local_rotated_coordinates
    global _old_Distance_to_POI
    global _old_container
    global _old_time

    #-----------------------------------------------------Distance to POI---------------------------------------------------------------
    New_Distance_to_POI = target.coords - player_global_coordinates

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
    Delta_Distance_to_POI_Total = New_Distance_to_POI_Total - _old_Distance_to_POI.magnitude()

    if Delta_Distance_to_POI_Total <= 0:
        Delta_distance_to_poi_color = "#00ff00"
    else:
        Delta_distance_to_poi_color = "#ff3700"


    #-----------------------------------------------Estimated time of arrival-----------------------------------------------------------
    #get the time between the last update and this update
    Delta_time = timestamp - _old_time

    #get the time it would take to reach destination using the same speed
    try :
        Estimated_time_of_arrival = (Delta_time*New_Distance_to_POI_Total)/abs(Delta_Distance_to_POI_Total)
    except ZeroDivisionError:
        Estimated_time_of_arrival = 0.00


    #----------------------------------------------------Course Deviation---------------------------------------------------------------
    #get the vector between current_pos and previous_pos
    Previous_current_pos_vector = player_global_coordinates - _old_player_Global_coordinates

    #get the vector between current_pos and target_pos
    Current_target_pos_vector = target.coords - player_global_coordinates

    #get the angle between the current-target_pos vector and the previous-current_pos vector
    Course_Deviation = degrees(Previous_current_pos_vector.angle_between(Current_target_pos_vector))

    if Course_Deviation <= 10:
        Total_deviation_from_target_color = "#00ff00"
    elif Course_Deviation <= 20:
        Total_deviation_from_target_color = "#ffd000"
    else:
        Total_deviation_from_target_color = "#ff3700"


    #-------------------------------------------Update coordinates for the next update--------------------------------------------------
    _old_player_Global_coordinates = player_global_coordinates
    _old_Distance_to_POI = New_Distance_to_POI
    _old_time = timestamp


    return {
        "updated" : f"Updated : {time.strftime('%H:%M:%S', time.localtime(timestamp))}",
        "target" : target.name,
        "player_x" : round(player_global_coordinates.x, 3),
        "player_y" : round(player_global_coordinates.y, 3),
        "player_z" : round(player_global_coordinates.z, 3),
        "target_x" : round(target.coords.x, 3),
        "target_y" : round(target.coords.y, 3),
        "target_z" : round(target.coords.z, 3),
        "distance_to_poi" : f"{round(New_Distance_to_POI_Total, 3)} km",
        "distance_to_poi_color" : New_Distance_to_POI_Total_color,
        "delta_distance_to_poi" : f"{round(abs(Delta_Distance_to_POI_Total), 3)} km",
        "delta_distance_to_poi_color" : Delta_distance_to_poi_color,
        "total_deviation" : f"{round(Course_Deviation, 1)}°",
        "total_deviation_color" : Total_deviation_from_target_color,
        "ETA" : f"{str(datetime.timedelta(seconds=round(Estimated_time_of_arrival, 0)))}"
    }

def compute_companion(player_global_coordinates: Vector, timestamp: float):
    global _old_player_Global_coordinates
    global _old_player_local_rotated_coordinates
    global _old_Distance_to_POI
    global _old_container
    global _old_time

    Actual_Container = get_current_container(player_global_coordinates)

    data = {
        "updated" : f"Updated : {time.strftime('%H:%M:%S', time.localtime(timestamp))}",
        "player_global_x" : f"Global X : {round(player_global_coordinates.x, 3)}",
        "player_global_y" : f"Global Y : {round(player_global_coordinates.y, 3)}",
        "player_global_z" : f"Global Z : {round(player_global_coordinates.z, 3)}",
    }

    if Actual_Container is None:
        Distance_since_last_update = _old_player_Global_coordinates - player_global_coordinates
        data.update({
            "distance_change" : f"Distance since last update : {round(Distance_since_last_update.magnitude(), 3)} km",
            "actual_container" : "None",
            "player_local_x" : "",
            "player_local_y" : "",
            "player_local_z" : "",
            "player_long" : "",
            "player_lat" : "",
            "player_height" : "",
            "player_OM1" : "",
            "player_OM2" : "",
            "player_OM3" : "",
            "closest_poi" : ""
        })
    else:
        Time_passed_since_reference_in_seconds = timestamp - STAR_CITIZEN_REF_SECONDS
        New_player_local_rotated_coordinates = get_local_rotated_coordinates(Time_passed_since_reference_in_seconds, player_global_coordinates, Actual_Container)

        if Actual_Container == _old_container:
            Distance_since_last_update = _old_player_local_rotated_coordinates - New_player_local_rotated_coordinates
        else:
            Distance_since_last_update = _old_player_Global_coordinates - player_global_coordinates

        # Lattitude, Longitude, Height
        Latitude, Longitude, Height = get_lat_long_height(New_player_local_rotated_coordinates, Actual_Container)

        # 3 closest OMs
        Closest_OM = get_closest_oms(New_player_local_rotated_coordinates, Actual_Container)

        # 2 Closest POIs
        Player_to_POIs_Distances_Sorted = get_closest_POI(New_player_local_rotated_coordinates, Actual_Container, False)

        data.update({
            "distance_change" : f"Distance since last update : {round(Distance_since_last_update.magnitude(), 3)} km",
            "actual_container" : f"Actual Container : {Actual_Container.name}",
            "player_local_x" : f"Local X : {round(New_player_local_rotated_coordinates.x, 3)}",
            "player_local_y" : f"Local Y : {round(New_player_local_rotated_coordinates.y, 3)}",
            "player_local_z" : f"Local Z : {round(New_player_local_rotated_coordinates.z, 3)}",
            "player_long" : f"Longitude : {round(Longitude, 2)}°",
            "player_lat" : f"Latitude : {round(Latitude, 2)}°",
            "player_height" : f"Height : {round(Height, 1)} km",
            "player_OM1" : f"{Closest_OM['Z']['OM'].name} : {round(Closest_OM['Z']['Distance'], 3)} km",
            "player_OM2" : f"{Closest_OM['Y']['OM'].name} : {round(Closest_OM['Y']['Distance'], 3)} km",
            "player_OM3" : f"{Closest_OM['X']['OM'].name} : {round(Closest_OM['X']['Distance'], 3)} km",
            "closest_poi" : f"Closest POI : \n{Player_to_POIs_Distances_Sorted[0]['Name']} ({round(Player_to_POIs_Distances_Sorted[0]['Distance'], 3)} km) \n{Player_to_POIs_Distances_Sorted[1]['Name']} ({round(Player_to_POIs_Distances_Sorted[1]['Distance'], 3)} km)",
        })

        _old_player_local_rotated_coordinates = New_player_local_rotated_coordinates

    _old_player_Global_coordinates = player_global_coordinates
    _old_container = Actual_Container
    _old_time = timestamp

    return data
