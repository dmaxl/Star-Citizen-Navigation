"""Calculation and utility functions."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from math import sqrt, degrees, radians, cos, acos, sin, asin, tan ,atan2, copysign, pi
import sys
from typing import NamedTuple

from . import db

logger = logging.getLogger(__name__)


class Vector(NamedTuple):
    x: float
    y: float
    z: float = 0

    def magnitude(self):
        """Return the magnitude (length) of the vector."""
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def cross(self, b : Vector):
        """Compute the cross product of two vectors."""
        if not isinstance(b, Vector):
            return NotImplemented
        return Vector(
            self.y * b.z - self.z * b.y,
            self.z * b.x - self.x * b.z,
            self.x * b.y - self.y * b.x
        )

    def dot(self, b : Vector):
        """Return the dot product with another vector."""
        return self.x*b.x + self.y*b.y + self.z*b.z

    def angle_between(self, b : Vector):
        """Return the angle (in radians) of another vector to this one."""
        try:
            return acos(self.dot(b) / (self.magnitude() * b.magnitude()))
        except ZeroDivisionError:
            return 0.0

    def rotateZ(self, angle : float):
        """Return this vector rotated around the Z axis by angle radians."""
        x = self.x*cos(angle) - self.y*sin(angle)
        y = self.x*sin(angle) + self.y*cos(angle)
        return Vector(x, y, self.z)

    ### Python data model numeric type methods
    # Note: In the standard signature of these methods the
    # arguments are named 'self' and 'other'. For the sake
    # of clarity and brevity we call them 'a' and 'b'.

    def __add__(a, b):
        if not isinstance(b, Vector):
            return NotImplemented
        return Vector(a.x + b.x, a.y + b.y, a.z + b.z)

    def __sub__(a, b):
        if not isinstance(b, Vector):
            return NotImplemented
        return Vector(a.x - b.x, a.y - b.y, a.z - b.z)


class Quaternion(NamedTuple):
    w: float
    i: float
    j: float
    k: float


@dataclass(frozen=True)
class Location:
    name: str
    parent: str | None
    coord: Vector
    rot: Quaternion
    qtmarker: bool


@dataclass(frozen=True)
class OrbitalBody(Location):
    om_radius: float        # km
    body_radius: float      # km
    arrival_radius: float   # km
    time_lines: float
    rotation_speed: float
    rotation_adjust: float
    orbital_radius: float
    orbital_speed: float
    orbital_angle: float
    grid_radius: float
    pois: dict


def get_local_vector_from_latlon(lat: float, lon: float, height: float, parent: OrbitalBody):
    lat_rad = radians(lat)
    lon_rad = radians(-1*lon)

    radial_dist = parent.body_radius + height

    return Vector(
        radial_dist * cos(lat_rad) * sin(lon_rad),
        radial_dist * cos(lat_rad) * cos(lon_rad),
        radial_dist * sin(lat_rad),
    )

def get_current_container(global_coordinate : Vector):
    Database = db.getDatabase()
    for name, orbitalbody in Database["Containers"].items():
        relative_vector = orbitalbody.coord - global_coordinate
        if relative_vector.magnitude() <= 3 * orbitalbody.om_radius:
            Actual_Container = orbitalbody
    return Actual_Container


def get_local_rotated_coordinates(Time_passed : float, coordinate : Vector, Actual_Container : OrbitalBody):
    try:
        Rotation_speed_in_degrees_per_second = 0.1 * (1/Actual_Container.rotation_speed)
    except ZeroDivisionError:
        Rotation_speed_in_degrees_per_second = 0

    Rotation_state_in_degrees = ((Rotation_speed_in_degrees_per_second * Time_passed) + Actual_Container.rotation_adjust) % 360

    local_unrotated_coordinates = coordinate - Actual_Container.coord
    return local_unrotated_coordinates.rotateZ(radians(-1*Rotation_state_in_degrees))


def get_lat_long_height(coordinate : Vector, Container : OrbitalBody):
    Radius = Container.body_radius
    Radial_Distance = coordinate.magnitude()
    Height = Radial_Distance - Radius

    #Latitude
    try :
        Latitude = degrees(asin(coordinate.z/Radial_Distance))
    except :
        Latitude = 0

    try :
        Longitude = -1*degrees(atan2(coordinate.x, coordinate.y))
    except :
        Longitude = 0

    return (Latitude, Longitude, Height)


def get_closest_POI(coordinate : Vector, Container : OrbitalBody, Quantum_marker : bool = False):
    Distances_to_POIs = []

    for name, POI in Container.pois.items():
        Vector_POI = coordinate - POI.coord
        Distance_POI = Vector_POI.magnitude()

        if Quantum_marker and POI.qtmarker or not Quantum_marker:
            Distances_to_POIs.append({"Name" : name, "Distance" : Distance_POI})

    Target_to_POIs_Distances_Sorted = sorted(Distances_to_POIs, key=lambda k: k['Distance'])
    return Target_to_POIs_Distances_Sorted



def get_closest_oms(coordinate : Vector, Container : OrbitalBody):
    Closest_OM = {}

    if coordinate.x >= 0:
        Closest_OM["X"] = {"OM" : Container.pois["OM-5"], "Distance" : (coordinate - Container.pois['OM-5'].coord).magnitude()}
    else:
        Closest_OM["X"] = {"OM" : Container.pois["OM-6"], "Distance" : (coordinate - Container.pois['OM-6'].coord).magnitude()}

    if coordinate.y >= 0:
        Closest_OM["Y"] = {"OM" : Container.pois["OM-3"], "Distance" : (coordinate - Container.pois['OM-3'].coord).magnitude()}
    else:
        Closest_OM["Y"] = {"OM" : Container.pois["OM-4"], "Distance" : (coordinate - Container.pois['OM-4'].coord).magnitude()}

    if coordinate.z >= 0:
        Closest_OM["Z"] = {"OM" : Container.pois["OM-1"], "Distance" : (coordinate - Container.pois['OM-1'].coord).magnitude()}
    else:
        Closest_OM["Z"] = {"OM" : Container.pois["OM-2"], "Distance" : (coordinate - Container.pois['OM-2'].coord).magnitude()}

    return Closest_OM



def get_sunset_sunrise_predictions(
    # X : float, Y : float, Z : float,
    Latitude : float, Longitude : float, Height : float,
    Container : OrbitalBody, Star : OrbitalBody,
    JulianDate : float):
    try :
        # Stanton X Y Z coordinates in refrence of the center of the system
        sx, sy, sz = Star.coord

        # Container X Y Z coordinates in refrence of the center of the system
        bx, by, bz = Container.coord

        # Rotation speed of the container
        rotation_speed = Container.rotation_speed

        # Container qw/qx/qy/qz quaternion rotation
        qw, qx, qy, qz = Container.rot

        # Stanton X Y Z coordinates in refrence of the center of the container
        bsx = ((1-(2*qy**2)-(2*qz**2))*(sx-bx))+(((2*qx*qy)-(2*qz*qw))*(sy-by))+(((2*qx*qz)+(2*qy*qw))*(sz-bz))
        bsy = (((2*qx*qy)+(2*qz*qw))*(sx-bx))+((1-(2*qx**2)-(2*qz**2))*(sy-by))+(((2*qy*qz)-(2*qx*qw))*(sz-bz))
        bsz = (((2*qx*qz)-(2*qy*qw))*(sx-bx))+(((2*qy*qz)+(2*qx*qw))*(sy-by))+((1-(2*qx**2)-(2*qy**2))*(sz-bz))

        # Solar Declination of Stanton
        Solar_declination = degrees(acos((((sqrt(bsx**2+bsy**2+bsz**2))**2)+((sqrt(bsx**2+bsy**2))**2)-(bsz**2))/(2*(sqrt(bsx**2+bsy**2+bsz**2))*(sqrt(bsx**2+bsy**2)))))*copysign(1,bsz)

        # Radius of Stanton
        StarRadius = Star.body_radius # OK

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
        RotationCorrection = Container.rotation_adjust

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
        ElevationCorrection = degrees(acos(Container.body_radius/(Container.body_radius))) if Height<0 else degrees(acos(Container.body_radius/(Container.body_radius+Height)))

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
        raise e
        print(f"Error in sunrise/sunset calculations: \n{e}\nValues were:\n-Latitude : {Latitude}\n-Longitude : {Longitude}\n-Height : {Height}\n-Container : {Container.name}\n-Star : {Star.name}", file=sys.stderr)
        return ["Unknown", "Unknown", 0]
