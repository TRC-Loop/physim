"""The fake physics engine.

Deliberately not a rigid-body solver: it integrates velocities on a fixed
sub-stepped timeline and resolves contacts with simple impulses. That keeps
results deterministic and fast enough for hundreds of objects, which matters
more here than physical accuracy.
"""

from __future__ import annotations

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
        for body in bodies:
            if not body.fixed:
                self._integrate(body, dt)
        for body in bodies:
            self._collide_boundaries(body, boundaries)
        if self.params.ball_collisions and len(bodies) > 1:
            self._collide_bodies(bodies)

    def _integrate(self, body, dt: float) -> None:
        """Apply accelerations and move a body forward one sub-step."""
        p = self.params
        velocity = body.velocity

        if p.gravity and body.gravity_scale:
            velocity = velocity + p.gravity_vector * (body.gravity_scale * dt)

        if p.attraction:
            offset = p.attraction_point - body.transform.position
            distance_sq = max(offset.length_squared, 1.0)
            pull = offset.normalized() * (p.attraction / distance_sq)
            velocity = velocity + pull * dt

        if p.damping != 1.0:
            velocity = velocity * (p.damping**dt)

        if p.max_speed is not None:
            velocity = velocity.clamped(p.max_speed)
        if p.min_speed and velocity.length < p.min_speed:
            velocity = Vec2()

        body.velocity = velocity
        body.transform.position = body.transform.position + velocity * dt

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
