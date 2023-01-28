"""Calculation and utility functions."""

from __future__ import annotations

import logging
from math import sqrt, degrees, radians, cos, acos, sin, asin, tan ,atan2, copysign, pi
import sys

from .db import getDatabase

logger = logging.getLogger(__name__)


def get_local_xyz(lat : float, long : float, height : float, Container : dict):
    lat_rad = radians(lat)
    long_rad = radians(-1*long)

    Radius = Container["Body Radius"]
    Radial_Distance = Radius + height

    local_coordinates = {
        "X": Radial_Distance * cos(lat_rad) * sin(long_rad),
        "Y": Radial_Distance * cos(lat_rad) * cos(long_rad),
        "Z": Radial_Distance * sin(lat_rad),
    }

    return local_coordinates

def vector_norm(a):
    """Returns the norm of a vector"""
    return sqrt(a["X"]**2 + a["Y"]**2 + a["Z"]**2)

def vector_product(a, b):
    """Returns the dot product of two vectors"""
    return a["X"]*b["X"] + a["Y"]*b["Y"] + a["Z"]*b["Z"]

def angle_between_vectors(a, b):
    """Function that returns an angle in degrees between 2 vectors"""
    try :
        angle = degrees(acos(vector_product(a, b) / (vector_norm(a) * vector_norm(b))))
    except ZeroDivisionError:
        angle = 0.0
    return angle

def rotate_point_2D(Unrotated_coordinates, angle):
    Rotated_coordinates = {}
    Rotated_coordinates["X"] = Unrotated_coordinates["X"] * cos(angle) - Unrotated_coordinates["Y"]*sin(angle)
    Rotated_coordinates["Y"] = Unrotated_coordinates["X"] * sin(angle) + Unrotated_coordinates["Y"]*cos(angle)
    Rotated_coordinates["Z"] = Unrotated_coordinates["Z"]
    return (Rotated_coordinates)


def get_current_container(X : float, Y : float, Z : float):
    Database = getDatabase()
    Actual_Container = {
        "Name": "None",
        "X": 0,
        "Y": 0,
        "Z": 0,
        "Rotation Speed": 0,
        "Rotation Adjust": 0,
        "OM Radius": 0,
        "Body Radius": 0,
        "POI": {}
    }
    for i in Database["Containers"] :
        Container_vector = {"X" : Database["Containers"][i]["X"] - X, "Y" : Database["Containers"][i]["Y"] - Y, "Z" : Database["Containers"][i]["Z"] - Z}
        if vector_norm(Container_vector) <= 3 * Database["Containers"][i]["OM Radius"]:
            Actual_Container = Database["Containers"][i]
    return Actual_Container


def get_local_rotated_coordinates(Time_passed : float, X : float, Y : float, Z : float, Actual_Container : dict):

    try:
        Rotation_speed_in_degrees_per_second = 0.1 * (1/Actual_Container["Rotation Speed"])
    except ZeroDivisionError:
        Rotation_speed_in_degrees_per_second = 0

    Rotation_state_in_degrees = ((Rotation_speed_in_degrees_per_second * Time_passed) + Actual_Container["Rotation Adjust"]) % 360

    local_unrotated_coordinates = {
        "X": X - Actual_Container["X"],
        "Y": Y - Actual_Container["Y"],
        "Z": Z - Actual_Container["Z"]
    }

    local_rotated_coordinates = rotate_point_2D(local_unrotated_coordinates, radians(-1*Rotation_state_in_degrees))

    return local_rotated_coordinates


def get_lat_long_height(X : float, Y : float, Z : float, Container : dict):
    Radius = Container["Body Radius"]

    Radial_Distance = sqrt(X**2 + Y**2 + Z**2)

    Height = Radial_Distance - Radius

    #Latitude
    try :
        Latitude = degrees(asin(Z/Radial_Distance))
    except :
        Latitude = 0

    try :
        Longitude = -1*degrees(atan2(X, Y))
    except :
        Longitude = 0

    return [Latitude, Longitude, Height]


def get_closest_POI(X : float, Y : float, Z : float, Container : dict, Quantum_marker : bool = False):

    Distances_to_POIs = []

    for POI in Container["POI"]:
        Vector_POI = {
            "X": abs(X - Container["POI"][POI]["X"]),
            "Y": abs(Y - Container["POI"][POI]["Y"]),
            "Z": abs(Z - Container["POI"][POI]["Z"])
        }

        Distance_POI = vector_norm(Vector_POI)

        if Quantum_marker and Container["POI"][POI]["QTMarker"] == "TRUE" or not Quantum_marker:
            Distances_to_POIs.append({"Name" : POI, "Distance" : Distance_POI})

    Target_to_POIs_Distances_Sorted = sorted(Distances_to_POIs, key=lambda k: k['Distance'])
    return Target_to_POIs_Distances_Sorted



def get_closest_oms(X : float, Y : float, Z : float, Container : dict):
    Closest_OM = {}

    if X >= 0:
        Closest_OM["X"] = {"OM" : Container["POI"]["OM-5"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-5"]["X"], "Y" : Y - Container["POI"]["OM-5"]["Y"], "Z" : Z - Container["POI"]["OM-5"]["Z"]})}
    else:
        Closest_OM["X"] = {"OM" : Container["POI"]["OM-6"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-6"]["X"], "Y" : Y - Container["POI"]["OM-6"]["Y"], "Z" : Z - Container["POI"]["OM-6"]["Z"]})}
    if Y >= 0:
        Closest_OM["Y"] = {"OM" : Container["POI"]["OM-3"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-3"]["X"], "Y" : Y - Container["POI"]["OM-3"]["Y"], "Z" : Z - Container["POI"]["OM-3"]["Z"]})}
    else:
        Closest_OM["Y"] = {"OM" : Container["POI"]["OM-4"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-4"]["X"], "Y" : Y - Container["POI"]["OM-4"]["Y"], "Z" : Z - Container["POI"]["OM-4"]["Z"]})}
    if Z >= 0:
        Closest_OM["Z"] = {"OM" : Container["POI"]["OM-1"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-1"]["X"], "Y" : Y - Container["POI"]["OM-1"]["Y"], "Z" : Z - Container["POI"]["OM-1"]["Z"]})}
    else:
        Closest_OM["Z"] = {"OM" : Container["POI"]["OM-2"], "Distance" : vector_norm({"X" : X - Container["POI"]["OM-2"]["X"], "Y" : Y - Container["POI"]["OM-2"]["Y"], "Z" : Z - Container["POI"]["OM-2"]["Z"]})}

    return Closest_OM



def get_sunset_sunrise_predictions(
    X : float, Y : float, Z : float,
    Latitude : float, Longitude : float, Height : float,
    Container : dict, Star : dict,
    JulianDate : float):
    try :
        # Stanton X Y Z coordinates in refrence of the center of the system
        sx, sy, sz = Star["X"], Star["Y"], Star["Z"]

        # Container X Y Z coordinates in refrence of the center of the system
        bx, by, bz = Container["X"], Container["Y"], Container["Z"]

        # Rotation speed of the container
        rotation_speed = Container["Rotation Speed"]

        # Container qw/qx/qy/qz quaternion rotation
        qw, qx, qy, qz = Container["qw"], Container["qx"], Container["qy"], Container["qz"]

        # Stanton X Y Z coordinates in refrence of the center of the container
        bsx = ((1-(2*qy**2)-(2*qz**2))*(sx-bx))+(((2*qx*qy)-(2*qz*qw))*(sy-by))+(((2*qx*qz)+(2*qy*qw))*(sz-bz))
        bsy = (((2*qx*qy)+(2*qz*qw))*(sx-bx))+((1-(2*qx**2)-(2*qz**2))*(sy-by))+(((2*qy*qz)-(2*qx*qw))*(sz-bz))
        bsz = (((2*qx*qz)-(2*qy*qw))*(sx-bx))+(((2*qy*qz)+(2*qx*qw))*(sy-by))+((1-(2*qx**2)-(2*qy**2))*(sz-bz))

        # Solar Declination of Stanton
        Solar_declination = degrees(acos((((sqrt(bsx**2+bsy**2+bsz**2))**2)+((sqrt(bsx**2+bsy**2))**2)-(bsz**2))/(2*(sqrt(bsx**2+bsy**2+bsz**2))*(sqrt(bsx**2+bsy**2)))))*copysign(1,bsz)

        # Radius of Stanton
        StarRadius = Star["Body Radius"] # OK

        # Apparent Radius of Stanton
        Apparent_Radius = degrees(asin(StarRadius/(sqrt((bsx)**2+(bsy)**2+(bsz)**2))))

        # Length of day is the planet rotation rate expressed as a fraction of a 24 hr day.
        LengthOfDay = 3600*rotation_speed/86400



        # A Julian Date is simply the number of days and fraction of a day since a specific event. (01/01/2020 00:00:00)
        #JulianDate = Time_passed_since_reference_in_seconds/(24*60*60) # OK
        # passed in to function

        # Determine the current day/night cycle of the planet.
        # The current cycle is expressed as the number of day/night cycles and fraction of the cycle that have occurred
        # on that planet since Jan 1, 2020 given the length of day. While the number of sunrises that have occurred on the
        # planet since Jan 1, 2020 is interesting, we are really only interested in the fractional part.
        try :
            CurrentCycle = JulianDate/LengthOfDay
        except ZeroDivisionError :
            CurrentCycle = 1


        # The rotation correction is a value that accounts for the rotation of the planet on Jan 1, 2020 as we don’t know
        # exactly when the rotation of the planet started.  This value is measured and corrected during a rotation
        # alignment that is performed periodically in-game and is retrieved from the navigation database.
        RotationCorrection = Container["Rotation Adjust"]

        # CurrentRotation is how far the planet has rotated in this current day/night cycle expressed in the number of
        # degrees remaining before the planet completes another day/night cycle.
        CurrentRotation = (360-(CurrentCycle%1)*360-RotationCorrection)%360


        # Meridian determine where the star would be if the planet did not rotate.
        # Between the planet and Stanton there is a plane that contains the north pole and south pole
        # of the planet and the center of Stanton. Locations on the surface of the planet on this plane
        # experience the phenomenon we call noon.
        Meridian = degrees( (atan2(bsy,bsx)-(pi/2)) % (2*pi) )

        # Because the planet rotates, the location of noon is constantly moving. This equation
        # computes the current longitude where noon is occurring on the planet.
        SolarLongitude = CurrentRotation-(0-Meridian)%360
        if SolarLongitude>180:
            SolarLongitude = SolarLongitude-360
        elif SolarLongitude<-180:
            SolarLongitude = SolarLongitude+360



        # The difference between Longitude and Longitude360 is that for Longitude, Positive values
        # indicate locations in the Eastern Hemisphere, Negative values indicate locations in the Western
        # Hemisphere.
        # For Longitude360, locations in longitude 0-180 are in the Eastern Hemisphere, locations in
        # longitude 180-359 are in the Western Hemisphere.
        Longitude360 = Longitude%360 # OK

        # Determine correction for location height
        ElevationCorrection = degrees(acos(Container["Body Radius"]/(Container["Body Radius"]))) if Height<0 else degrees(acos(Container["Body Radius"]/(Container["Body Radius"]+Height)))

        # Determine Rise/Set Hour Angle
        # The star rises at + (positive value) rise/set hour angle and sets at - (negative value) rise/set hour angle
        # Solar Declination and Apparent Radius come from the first set of equations when we determined where the star is.
        RiseSetHourAngle = degrees(acos(-tan(radians(Latitude))*tan(radians(Solar_declination))))+Apparent_Radius+ElevationCorrection

        # Determine the current Hour Angle of the star

        # Hour Angles between 180 and the +Rise Hour Angle are before sunrise.
        # Between +Rise Hour angle and 0 are after sunrise before noon. 0 noon,
        # between 0 and -Set Hour Angle is afternoon,
        # between -Set Hour Angle and -180 is after sunset.

        # Once the current Hour Angle is determined, we now know the actual angle (in degrees)
        # between the position of the star and the +rise hour angle and the -set hour angle.
        HourAngle = (CurrentRotation-(Longitude360-Meridian)%360)%360
        if HourAngle > 180:
            HourAngle = HourAngle - 360


        # Determine the planet Angular Rotation Rate.
        # Angular Rotation Rate is simply the Planet Rotation Rate converted from Hours into degrees per minute.
        # The Planet Rotation Rate is datamined from the game files.
        try :
            AngularRotationRate = 6/rotation_speed # OK
        except ZeroDivisionError :
            AngularRotationRate = 0


        if AngularRotationRate != 0 :
            midnight = (HourAngle + 180) / AngularRotationRate

            morning = (HourAngle - (RiseSetHourAngle+12)) / AngularRotationRate
            if HourAngle <= RiseSetHourAngle+12:
                morning = morning + LengthOfDay*24*60

            sunrise = (HourAngle - RiseSetHourAngle) / AngularRotationRate
            if HourAngle <= RiseSetHourAngle:
                sunrise = sunrise + LengthOfDay*24*60

            noon = (HourAngle - 0) / AngularRotationRate
            if HourAngle <= 0:
                noon = noon + LengthOfDay*24*60

            sunset = (HourAngle - -1*RiseSetHourAngle) / AngularRotationRate
            if HourAngle <= -1*RiseSetHourAngle:
                sunset = sunset + LengthOfDay*24*60

            evening = (HourAngle - (-1*RiseSetHourAngle-12)) / AngularRotationRate
            if HourAngle <= -1*(RiseSetHourAngle-12):
                evening = evening + LengthOfDay*24*60
        else :
            midnight = 0
            morning = 0
            sunrise = 0
            noon = 0
            sunset = 0
            evening = 0




        if 180 >= HourAngle > RiseSetHourAngle+12:
            state_of_the_day = "After midnight"
            next_event = "Sunrise"
            next_event_time = sunrise
        elif RiseSetHourAngle+12 >= HourAngle > RiseSetHourAngle:
            state_of_the_day = "Morning Twilight"
            next_event = "Sunrise"
            next_event_time = sunrise
        elif RiseSetHourAngle >= HourAngle > 0:
            state_of_the_day = "Morning"
            next_event = "Sunset"
            next_event_time = sunset
        elif 0 >= HourAngle > -1*RiseSetHourAngle:
            state_of_the_day = "Afternoon"
            next_event = "Sunset"
            next_event_time = sunset
        elif -1*RiseSetHourAngle >= HourAngle > -1*RiseSetHourAngle-12:
            state_of_the_day = "Evening Twilight"
            next_event = "Sunrise"
            next_event_time = sunrise
        elif -1*RiseSetHourAngle-12 >= HourAngle >= -180:
            state_of_the_day = "Before midnight"
            next_event = "Sunrise"
            next_event_time = sunrise

        if AngularRotationRate == 0 :
            next_event = "N/A"

        return [state_of_the_day, next_event, next_event_time]

    except Exception as e:
        print(f"Error in sunrise/sunset calculations: \n{e}\nValues were:\n-X : {X}\n-Y : {Y}\n-Z : {Z}\n-Latitude : {Latitude}\n-Longitude : {Longitude}\n-Height : {Height}\n-Container : {Container['Name']}\n-Star : {Star['Name']}", file=sys.stderr)
        return ["Unknown", "Unknown", 0]
