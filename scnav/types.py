"""NamedTuple and dataclass definitions."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, sin, sqrt
from typing import NamedTuple, Mapping


class Vector(NamedTuple):
    x: float
    y: float
    z: float

    def magnitude(self):
        """Return the magnitude (length) of the vector."""
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def cross(self, b : Vector):
        """Compute the cross product of two vectors."""
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
        """Return this vector rotated around the Z axis by an angle (in radians)."""
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

    def __mul__(a, b):
        if not isinstance(b, Vector):
            return NotImplemented
        return a.dot(b)

    def __matmul__(a, b):
        if not isinstance(b, Vector):
            return NotImplemented
        return a.cross(b)


class Quaternion(NamedTuple):
    w: float
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Location:
    name: str
    parent: str | None
    coords: Vector
    rotation: Quaternion
    qtmarker: bool


@dataclass(frozen=True)
class OrbitalBody(Location):
    om_radius: float        # km
    body_radius: float      # km
    arrival_radius: float   # km
    time_lines: float
    rotation_speed: float   # hours per rotation
    rotation_adjust: float  # rotation about Z axis to match in-game orientation
    orbital_radius: float   # km
    orbital_speed: float
    orbital_angle: float
    grid_radius: float
    adjustment_date: float  # date corresponding to the rotation_adjust value
    pois: Mapping[str, Location]
