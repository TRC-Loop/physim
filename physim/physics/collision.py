"""Collision resolution between bodies.

Boundaries handle their own contact test and report a contact back; this module
turns contacts into velocity changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..types import Vec2


@dataclass
class Contact:
    """A resolved overlap between a body and something it hit."""

    normal: Vec2
    """Unit vector pointing out of the surface, toward the body."""

    depth: float
    """How far the body penetrated, in pixels."""

    point: Vec2 = Vec2()
    """Where the contact happened, in scene space."""


def resolve_wall(body, contact: Contact, restitution: float, friction: float) -> float:
    """Push a body out of a wall and reflect its velocity.

    Returns the impact speed along the normal, which handlers use to scale
    effects like sound volume.
    """
    normal = contact.normal
    if contact.depth > 0.0:
        body.transform.position = body.transform.position + normal * contact.depth

    normal_speed = body.velocity.dot(normal)
    if normal_speed >= 0.0:
        return 0.0

    normal_component = normal * normal_speed
    tangent_component = body.velocity - normal_component
    if friction:
        tangent_component = tangent_component * (1.0 - friction)
    body.velocity = tangent_component - normal_component * restitution
    return abs(normal_speed)


def resolve_pair(a, b, restitution: float, friction: float) -> float:
    """Resolve a collision between two circular bodies.

    Returns the closing speed, or zero when they were already separating.
    """
    delta = b.transform.position - a.transform.position
    distance = delta.length
    radii = a.collision_radius + b.collision_radius
    if distance >= radii:
        return 0.0

    normal = delta.normalized() if distance > 0.0 else Vec2(1.0, 0.0)
    inv_a, inv_b = a.inverse_mass, b.inverse_mass
    inv_total = inv_a + inv_b
    if inv_total == 0.0:
        return 0.0

    overlap = radii - distance
    a.transform.position = a.transform.position - normal * (overlap * inv_a / inv_total)
    b.transform.position = b.transform.position + normal * (overlap * inv_b / inv_total)

    relative = b.velocity - a.velocity
    closing = relative.dot(normal)
    if closing >= 0.0:
        return 0.0

    impulse = normal * (-(1.0 + restitution) * closing / inv_total)
    a.velocity = a.velocity - impulse * inv_a
    b.velocity = b.velocity + impulse * inv_b

    if friction:
        tangent = relative - normal * closing
        if tangent.length > 0.0:
            damp = tangent.normalized() * (tangent.length * friction / inv_total)
            a.velocity = a.velocity + damp * inv_a
            b.velocity = b.velocity - damp * inv_b

    return abs(closing)
