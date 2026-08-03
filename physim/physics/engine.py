"""The fake physics engine.

Deliberately not a rigid-body solver: it integrates velocities on a fixed
sub-stepped timeline and resolves contacts with simple impulses. That keeps
results deterministic and fast enough for hundreds of objects, which matters
more here than physical accuracy.
"""

from __future__ import annotations

from math import sqrt

from ..events import BOUNCE, COLLISION, ESCAPE
from ..types import Vec2
from .collision import resolve_pair, resolve_wall
from .params import PhysicsParams
from .spatial import SpatialGrid


class Engine:
    """Advances bodies through time and resolves their contacts."""

    def __init__(self, params: PhysicsParams | None = None) -> None:
        self.params = params or PhysicsParams()
        self.grid = SpatialGrid()
        self.collisions_this_step = 0
        """Contacts resolved during the most recent :meth:`step`."""

    def step(self, bodies: list, boundaries: list, dt: float) -> None:
        """Advance every body by ``dt`` seconds, sub-stepping for stability."""
        self.collisions_this_step = 0
        if dt <= 0.0:
            return
        sub_dt = dt / self.params.substeps
        for _ in range(self.params.substeps):
            self._substep(bodies, boundaries, sub_dt)

    def _substep(self, bodies: list, boundaries: list, dt: float) -> None:
        """Run a single integration and collision pass."""
        p = self.params
        # hoist everything constant across the whole pass; at thousands of
        # bodies these lookups and the vector allocations they imply dominate
        gravity = p.gravity_vector if p.gravity else None
        gx = gravity.x * dt if gravity else 0.0
        gy = gravity.y * dt if gravity else 0.0
        damping = p.damping**dt if p.damping != 1.0 else 1.0
        max_speed = p.max_speed
        min_speed = p.min_speed
        attraction = p.attraction
        ax, ay = p.attraction_point.x, p.attraction_point.y

        for body in bodies:
            if body.fixed:
                continue
            velocity = body.velocity
            vx, vy = velocity.x, velocity.y
            position = body.transform.position
            px, py = position.x, position.y

            if gravity is not None and body.gravity_scale:
                scale = body.gravity_scale
                vx += gx * scale
                vy += gy * scale

            if attraction:
                ox, oy = ax - px, ay - py
                distance_sq = ox * ox + oy * oy
                if distance_sq > 1.0:
                    distance = sqrt(distance_sq)
                    pull = attraction / distance_sq * dt / distance
                    vx += ox * pull
                    vy += oy * pull
                else:
                    vx += ox * attraction * dt
                    vy += oy * attraction * dt

            if damping != 1.0:
                vx *= damping
                vy *= damping

            if max_speed is not None or min_speed:
                speed = sqrt(vx * vx + vy * vy)
                if max_speed is not None and speed > max_speed and speed > 0.0:
                    factor = max_speed / speed
                    vx *= factor
                    vy *= factor
                elif min_speed and speed < min_speed:
                    vx = vy = 0.0

            body.velocity = Vec2(vx, vy)
            body.transform.position = Vec2(px + vx * dt, py + vy * dt)

        for body in bodies:
            self._collide_boundaries(body, boundaries)
        if p.ball_collisions and len(bodies) > 1:
            self._collide_bodies(bodies)

    def _restitution_for(self, body) -> float:
        """Per-object bounciness, falling back to the scene parameters."""
        return self.params.restitution if body.restitution is None else body.restitution

    def _collide_boundaries(self, body, boundaries: list) -> None:
        """Test a body against every boundary and resolve what it hits."""
        for boundary in boundaries:
            if not boundary.alive:
                continue
            if boundary.contains_escape(body):
                body.emit(ESCAPE, boundary=boundary)
                continue
            contact = boundary.contact_with(body)
            if contact is None:
                continue
            impact = resolve_wall(body, contact, self._restitution_for(body), self.params.friction)
            if impact <= 0.0:
                continue
            self.collisions_this_step += 1
            body.bounces += 1
            body.emit(
                BOUNCE,
                boundary=boundary,
                impact=impact,
                normal=contact.normal,
                point=contact.point,
            )

    def _collide_bodies(self, bodies: list) -> None:
        """Resolve body-to-body contacts using the spatial grid for culling."""
        radii = [b.collision_radius for b in bodies]
        self.grid.cell_size = max(40.0, (max(radii) if radii else 40.0) * 2.0)
        self.grid.build(bodies)
        for i, j in self.grid.candidate_pairs():
            a, b = bodies[i], bodies[j]
            if not (a.alive and b.alive):
                continue
            restitution = min(self._restitution_for(a), self._restitution_for(b))
            impact = resolve_pair(a, b, restitution, self.params.friction)
            if impact <= 0.0:
                continue
            self.collisions_this_step += 1
            a.bounces += 1
            b.bounces += 1
            a.emit(COLLISION, other=b, impact=impact)
            b.emit(COLLISION, other=a, impact=impact)
