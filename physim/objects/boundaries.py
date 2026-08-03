"""Playfield boundaries: hollow shapes that objects bounce around inside.

A boundary reports contacts to the engine through :meth:`contact_with` and can
declare that an object has left through a gap via :meth:`contains_escape`.
"""

from __future__ import annotations

import math

from ..physics.collision import Contact
from ..types import Vec2, Vec2Like
from .base import SceneObject


class Boundary(SceneObject):
    """Base class for anything that acts as a wall."""

    is_boundary = True

    def __init__(self, pos: Vec2Like = (0.0, 0.0), *, thickness: float = 8.0, **kwargs) -> None:
        kwargs.setdefault("fill", None)
        kwargs.setdefault("stroke", "#ffffff")
        super().__init__(pos, **kwargs)
        self.thickness = thickness
        self.stroke_width = self.stroke_width or thickness

    def contact_with(self, body) -> Contact | None:
        """Return a contact if ``body`` is penetrating this boundary."""
        raise NotImplementedError

    def contains_escape(self, body) -> bool:
        """Whether ``body`` has left the playfield through an opening."""
        return False


class HollowCircle(Boundary):
    """A ring that objects bounce around inside.

    An angular gap turns it into the spinning-opening style: objects escape
    through the gap once they line up with it.
    """

    def __init__(
        self,
        radius: float = 400.0,
        pos: Vec2Like = (0.0, 0.0),
        *,
        gap_degrees: float = 0.0,
        gap_angle: float = 90.0,
        rotation_speed: float = 0.0,
        inward: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.radius = radius
        self.gap_degrees = gap_degrees
        """Angular size of the opening. Zero means a closed ring."""

        self.gap_angle = gap_angle
        """Where the opening starts, in degrees counter-clockwise from +x."""

        self.rotation_speed = rotation_speed
        """Degrees per second the gap rotates around the ring."""

        self.inward = inward
        """True keeps objects inside; false makes the ring a solid obstacle."""

        self.escaped: set[int] = set()
        """Ids of objects that already left, so escape only fires once each."""

    def update(self, dt: float) -> None:
        """Spin the gap forward by ``dt`` seconds."""
        super().update(dt)
        if self.rotation_speed:
            self.gap_angle = (self.gap_angle + self.rotation_speed * dt) % 360.0

    @property
    def collision_radius(self) -> float:
        """Ring radius scaled by the object's transform."""
        return self.radius * self.transform.uniform_scale

    def gap_span(self) -> tuple[float, float]:
        """Start and end angle of the opening in degrees."""
        return self.gap_angle % 360.0, (self.gap_angle + self.gap_degrees) % 360.0

    def angle_in_gap(self, angle: float) -> bool:
        """Whether an angle in degrees falls inside the opening."""
        if self.gap_degrees <= 0.0:
            return False
        if self.gap_degrees >= 360.0:
            return True
        start, end = self.gap_span()
        angle %= 360.0
        if start <= end:
            return start <= angle <= end
        return angle >= start or angle <= end

    def contact_with(self, body) -> Contact | None:
        """Return a contact when a body reaches the inner wall of the ring."""
        # this runs per body per substep, so the early-out stays scalar and
        # nothing is allocated until a contact is actually found
        position = body.transform.position
        centre = self.pos
        ox = position.x - centre.x
        oy = position.y - centre.y
        distance_sq = ox * ox + oy * oy
        limit = self.collision_radius - self.thickness / 2.0 - body.collision_radius

        if self.inward:
            if limit > 0.0 and distance_sq <= limit * limit:
                return None
            distance = math.sqrt(distance_sq)
            if self.angle_in_gap(math.degrees(math.atan2(oy, ox))):
                return None
            normal = Vec2(-ox / distance, -oy / distance) if distance > 0.0 else Vec2(0.0, -1.0)
            return Contact(
                normal=normal,
                depth=distance - limit,
                point=Vec2(centre.x + ox, centre.y + oy),
            )

        offset = Vec2(ox, oy)
        distance = math.sqrt(distance_sq)

        outer = self.collision_radius + self.thickness / 2.0 + body.collision_radius
        if distance >= outer:
            return None
        if self.angle_in_gap(offset.angle):
            return None
        normal = offset.normalized() if distance > 0.0 else Vec2(0.0, 1.0)
        return Contact(normal=normal, depth=outer - distance, point=self.pos + offset)

    def contains_escape(self, body) -> bool:
        """Whether a body has passed fully outside through the gap."""
        if self.gap_degrees <= 0.0 or not self.inward:
            return False
        if body.id in self.escaped:
            return False
        offset = body.transform.position - self.pos
        beyond = self.collision_radius + self.thickness / 2.0 + body.collision_radius
        if offset.length > beyond:
            self.escaped.add(body.id)
            return True
        return False

    def draw(self, canvas, ctx) -> None:
        """Draw the ring, leaving the gap unpainted."""
        ctx.draw_ring(
            canvas,
            self,
            self.pos,
            self.collision_radius,
            self.thickness,
            self.gap_degrees,
            self.gap_angle,
        )


class HollowRect(Boundary):
    """A rectangular arena that objects bounce around inside."""

    def __init__(
        self,
        width: float = 800.0,
        height: float = 800.0,
        pos: Vec2Like = (0.0, 0.0),
        *,
        corner_radius: float = 0.0,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.width = width
        self.height = height
        self.corner_radius = corner_radius

    def contact_with(self, body) -> Contact | None:
        """Return a contact when a body reaches one of the four walls."""
        local = body.transform.position - self.pos
        r = body.collision_radius
        half_w = self.width / 2.0 - self.thickness / 2.0 - r
        half_h = self.height / 2.0 - self.thickness / 2.0 - r

        # pick the wall the body has pushed furthest past
        overshoots = (
            (local.x - half_w, Vec2(-1.0, 0.0)),
            (-half_w - local.x, Vec2(1.0, 0.0)),
            (local.y - half_h, Vec2(0.0, -1.0)),
            (-half_h - local.y, Vec2(0.0, 1.0)),
        )
        depth, normal = max(overshoots, key=lambda item: item[0])
        if depth <= 0.0:
            return None
        return Contact(normal=normal, depth=depth, point=body.transform.position)

    def draw(self, canvas, ctx) -> None:
        """Draw the arena outline."""
        ctx.draw_rect(
            canvas, self, self.pos, self.width, self.height, self.corner_radius, outline=True
        )


class RingStack(SceneObject):
    """Several concentric rings drawn and simulated as one object.

    Each ring gets its own gap offset, which is how the multi-layer escape
    videos are built: the object works its way outward one ring at a time.
    """

    is_boundary = True

    def __init__(
        self,
        count: int = 5,
        inner_radius: float = 150.0,
        spacing: float = 60.0,
        pos: Vec2Like = (0.0, 0.0),
        *,
        gap_degrees: float = 30.0,
        gap_step: float = 40.0,
        rotation_speed: float = 30.0,
        alternate_direction: bool = True,
        thickness: float = 8.0,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.rings: list[HollowCircle] = []
        for i in range(count):
            speed = rotation_speed * (-1 if alternate_direction and i % 2 else 1)
            ring = HollowCircle(
                radius=inner_radius + spacing * i,
                pos=pos,
                gap_degrees=gap_degrees,
                gap_angle=(gap_step * i) % 360.0,
                rotation_speed=speed,
                thickness=thickness,
                stroke=kwargs.get("stroke", "#ffffff"),
            )
            self.rings.append(ring)

    def update(self, dt: float) -> None:
        """Advance every ring."""
        super().update(dt)
        for ring in self.rings:
            ring.update(dt)

    def contact_with(self, body) -> Contact | None:
        """Return the first contact found among the rings."""
        for ring in self.rings:
            if not ring.alive:
                continue
            contact = ring.contact_with(body)
            if contact is not None:
                return contact
        return None

    def contains_escape(self, body) -> bool:
        """Whether a body has escaped past the outermost live ring."""
        live = [r for r in self.rings if r.alive]
        return live[-1].contains_escape(body) if live else False

    def pop(self) -> HollowCircle | None:
        """Remove and return the innermost live ring, if any."""
        for ring in self.rings:
            if ring.alive:
                ring.alive = False
                return ring
        return None

    def draw(self, canvas, ctx) -> None:
        """Draw every live ring."""
        for ring in self.rings:
            if ring.alive:
                ring.draw(canvas, ctx)


def ring_gap_normal(ring: HollowCircle, angle_deg: float) -> Vec2:
    """Outward unit vector at an angle on a ring, useful in custom handlers."""
    rad = math.radians(angle_deg)
    return Vec2(math.cos(rad), math.sin(rad))
