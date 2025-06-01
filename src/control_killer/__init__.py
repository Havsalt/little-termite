import random
import sys

from charz._annotations import ColliderNode
import keyboard
import colex
from charz import (
    Engine,
    Screen,
    Node2D,
    Sprite,
    Label,
    Camera,
    ColliderComponent,
    Hitbox,
    Time,
    Vec2,
    move_toward,
    sign,
)


class SmoothCamera(Camera):
    _LERP_PERCENT: float = 0.001

    def update(self) -> None:
        assert isinstance(self.parent, Node2D)
        self.global_position = self.global_position.lerp(
            self.parent.global_position,
            self._LERP_PERCENT,
        )


class Eater(Node2D, ColliderComponent):
    hitbox = Hitbox(size=Vec2(7, 5))

    def update(self) -> None:
        for collider in self.get_colliders():
            if isinstance(collider, Enemy):
                if keyboard.is_pressed("f"):
                    # FIXME: Use `queue_free` when fixed in `charz`
                    collider.hide()
                    collider.hitbox.disabled = True
                    center = collider.global_position + collider.get_texture_size() / 2
                    for x in range(10):
                        for y in range(3):
                            EatParticle().with_global_position(
                                center + Vec2(x, y)
                            )


class Player(ColliderComponent, Sprite):
    _SIDE_SPEED: float = 1
    _JUMP_POWER: float = 3
    _GRAVITY: float = 0.2
    _FRICITON: float = 0.5
    _SUPER_JUMP_PERCENT: float = 0.80
    _SIMULATION_STEP: float = 1
    _REACH: float = 3
    hitbox = Hitbox(size=Vec2(5, 3))
    color = colex.SKY_BLUE
    transparency = " "
    texture = [
        "  O",
        "/ | \\",
        " / \\",
    ]

    def __init__(self) -> None:
        self._velocity = Vec2.ZERO
        self._eater = Eater(self, position=Vec2(-1, -1))

    def update(self) -> None:
        if keyboard.is_pressed("d"):
            self._velocity.x += self._SIDE_SPEED
        if keyboard.is_pressed("a"):
            self._velocity.x -= self._SIDE_SPEED
        if keyboard.is_pressed("space") and self.is_on_floor():
            added_velocity = Vec2.UP.y * self._JUMP_POWER
            self._velocity.y = added_velocity
            if keyboard.is_pressed("shift"):
                self._velocity.y += added_velocity * self._SUPER_JUMP_PERCENT
                center = self.global_position + Vec2(
                    0,
                    self.get_texture_size().y,
                )
                for x_offset in range(5):
                    JumpParticle().with_position(
                        center + Vec2(x_offset, 0),
                    )

        # Y check
        remaining_velocity = self._velocity.y
        direction = sign(self._velocity.y)
        while remaining_velocity != 0:
            remaining_velocity = move_toward(
                remaining_velocity,
                0,
                change=self._SIMULATION_STEP,
            )
            self.position.y += direction * self._SIMULATION_STEP
            if self.is_colliding():
                self.position.y -= direction * self._SIMULATION_STEP
                self._velocity.y = 0
                break

        # X check
        self.position.x += self._velocity.x
        # Revert motion if ended up colliding
        if self.is_colliding():
            self.position.x -= self._velocity.x

        self._velocity.y += self._FRICITON + self._GRAVITY
        self._velocity.x = move_toward(self._velocity.x, 0, change=self._SIDE_SPEED)
        self._velocity.y = move_toward(self._velocity.y, 0, change=self._FRICITON)

    def is_colliding_with(self, collider_node: ColliderNode) -> bool:
        if isinstance(collider_node, Eater):
            return False
        return super().is_colliding_with(collider_node)

    def is_on_floor(self) -> bool:
        self.position.y += 1
        collided = self.is_colliding()
        self.position.y -= 1
        return collided


class JumpParticle(Sprite):
    color = colex.WHITE
    texture = ["~"]

    def __init__(self) -> None:
        self._lifetime = 0.7 * random.random() + 0.4

    def update(self) -> None:
        self.position += Vec2(
            random.randint(-1, 1),
            random.randint(-1, 1),
        )
        self._lifetime -= Time.delta
        if self._lifetime <= 0:
            self.hide()


class EatParticle(JumpParticle):
    color = colex.DARK_RED
    texture = ["o"]


class Enemy(ColliderComponent, Label): ...


class Game(Engine):
    screen = Screen(auto_resize=True)

    def __init__(self) -> None:
        self.player = Player()
        Camera.current = SmoothCamera(
            self.player, mode=Camera.MODE_CENTERED | Camera.MODE_INCLUDE_SIZE
        )
        for y_position, raw_line in enumerate(sys.stdin, start=10):
            line = raw_line.replace("\n", "")
            if not line:
                continue
            Enemy(
                text=line,
                color=colex.from_random(),
            ).with_position(
                x=0,
                y=y_position,
            ).with_hitbox(
                Hitbox(size=Vec2(len(line), 1)),
            )


def main() -> None:
    game = Game()
    game.run()
