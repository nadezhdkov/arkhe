"""
example_platformer.py
---------------------
A minimal platformer demonstrating the key pyunix v2 features:

    - @Game lifecycle hooks
    - Entity subclass with @Sprite hooks
    - Animator with clips and transitions
    - Input actions + axes
    - Camera follow with dead zone + screen shake
    - Tween (scale pop on jump)
    - ParticleSystem (jump dust, death burst)
    - Timer (respawn delay)
    - Event bus (player_death)
    - Text (HUD)
    - Physics (Rigidbody + BoxCollider)
    - Scene manager (game / gameover)
    - TileMap (ground tiles)

Run with:  python example_platformer.py
"""

from arkhe.pyunix import (
    Game, Window, Input, Assets, Audio,
    Entity, Sprite, SpriteGroup,
    Animator,
    Tween, Ease,
    Camera,
    Text,
    ParticleSystem,
    Timer,
    Event,
    Scene,
    Rigidbody, BoxCollider, BodyType, PhysicsWorld,
    Vector2, Color,
)


# ── Constants ─────────────────────────────────────────────────────────────
W, H         = 960, 540
GRAVITY      = Vector2(0, 1600)
PLAYER_SPEED = 220.0
JUMP_FORCE   = -580.0


# ══════════════════════════════════════════════════════════════════════════
# Player
# ══════════════════════════════════════════════════════════════════════════

class Player(Entity):

    def __init__(self) -> None:
        super().__init__(
            x=200, y=100,
            rigidbody=Rigidbody(
                body_type=BodyType.DYNAMIC,
                gravity_scale=1.0,
                drag=0.05,
                freeze_x=False,
                freeze_y=False,
            ),
            collider=BoxCollider(width=28, height=44),
            tag="player",
            layer="player",
        )
        self.lives       = 3
        self.score       = 0
        self.grounded    = False
        self._jump_dust  = ParticleSystem(x=self.x, y=self.y + 22)
        self._jump_dust.configure(
            count=18,
            lifetime=(0.2, 0.5),
            speed=(30, 90),
            angle=(160, 200),
            start_color=Color.from_hex("#C8A96E"),
            end_color=Color(200, 170, 110, 0),
            start_size=3,
            end_size=0,
            gravity=Vector2(0, 60),
        )

    # ── Animation setup ──────────────────────

    @Sprite.ready
    def setup(self) -> None:
        # In a real project you'd load from disk:
        # frames_idle = Assets.spritesheet_row("hero.png", (32, 48), row=0, count=4)
        # For this demo we use colored placeholder rectangles
        import pygame
        def make_frame(color, w=28, h=44):
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill(color)
            return s

        idle_frames  = [make_frame((80,  120, 220)) for _ in range(4)]
        run_frames   = [make_frame((60,  200, 120)) for _ in range(6)]
        jump_frame   = [make_frame((220, 200,  60))]
        fall_frame   = [make_frame((220, 120,  60))]

        (self.animator
            .add_clip("idle", idle_frames, fps=6,  loop=True)
            .add_clip("run",  run_frames,  fps=14, loop=True)
            .add_clip("jump", jump_frame,  fps=1,  loop=False)
            .add_clip("fall", fall_frame,  fps=1,  loop=False))

        # Transitions driven by lambdas (evaluated every frame)
        vx = lambda: abs(self.rigidbody.velocity.x)
        vy = lambda: self.rigidbody.velocity.y

        (self.animator
            .add_transition("idle", "run",  condition=lambda: vx() > 15 and self.grounded)
            .add_transition("run",  "idle", condition=lambda: vx() < 15 and self.grounded)
            .add_transition("idle", "fall", condition=lambda: not self.grounded and vy() > 50)
            .add_transition("run",  "fall", condition=lambda: not self.grounded and vy() > 50)
            .add_transition("jump", "fall", condition=lambda: vy() > 0)
            .add_transition("fall", "idle", condition=lambda: self.grounded))

        self.animator.play("idle")
        self.image = self.animator._current_clip.frames[0] if self.animator._current_clip else None

    # ── Input ─────────────────────────────────

    @Sprite.update
    def tick(self, dt: float) -> None:
        # Horizontal movement
        h = Input.get_axis("move")
        self.rigidbody.velocity.x = h * PLAYER_SPEED

        # Flip scale based on direction
        if h < 0:
            self.transform.local_scale = Vector2(-1, 1)
        elif h > 0:
            self.transform.local_scale = Vector2(1, 1)

        # Jumping
        if Input.action_just_pressed("jump") and self.grounded:
            self.rigidbody.velocity.y = JUMP_FORCE
            self.grounded = False
            self.animator.play("jump", reset=True)
            # Scale pop tween
            Tween.scale_to(self, Vector2(1.2, 0.8), 0.07, ease=Ease.OUT_QUAD).then(
                Tween.scale_to(self, Vector2(1.0, 1.0), 0.12, ease=Ease.OUT_BACK)
            )
            # Dust particles
            self._jump_dust.x = self.x
            self._jump_dust.y = self.y + 22
            self._jump_dust.burst()

        # Update animator
        self.animator.update(dt)

        # Update dust
        self._jump_dust.update(dt)

        # Fall-off death
        if self.y > H + 100:
            self.die()

    @Sprite.draw
    def render(self, surface) -> None:
        self.draw_self(surface, Camera.offset)
        self._jump_dust.draw(surface, Camera.offset)

    @Sprite.on_collision_enter
    def on_hit(self, info) -> None:
        # Ground detection
        if info.normal.y < -0.5:
            self.grounded = True

    @Sprite.on_collision_exit
    def on_leave(self, info) -> None:
        self.grounded = False

    # ── Death ─────────────────────────────────

    def die(self) -> None:
        self.lives -= 1
        Camera.shake(intensity=10, duration=0.4)
        Event.emit("player_death", {"lives": self.lives, "score": self.score})
        # Death burst
        burst = ParticleSystem(x=self.x, y=self.y)
        burst.configure(
            count=40,
            lifetime=(0.4, 1.0),
            speed=(80, 250),
            angle=(-180, 180),
            start_color=Color.from_hex("#FF4444"),
            end_color=Color(255, 50, 50, 0),
            start_size=5,
            end_size=0,
            gravity=Vector2(0, 400),
        )
        burst.burst()
        # Respawn after delay
        self.visible = False
        self.rigidbody.velocity = Vector2.zero()
        Timer.after(1.5, self._respawn)

    def _respawn(self) -> None:
        self.x, self.y = 200.0, 100.0
        self.rigidbody.velocity = Vector2.zero()
        self.visible = True
        # Fade in
        self.alpha = 0
        Tween.to(self, "alpha", 255, 0.5, ease=Ease.OUT_QUAD)


# ══════════════════════════════════════════════════════════════════════════
# Platform (static body)
# ══════════════════════════════════════════════════════════════════════════

class Platform(Entity):

    def __init__(self, x, y, w, h, color=(90, 90, 110)) -> None:
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.STATIC, layer="ground",
                                mask={"player", "ground"}),
            collider=BoxCollider(width=w, height=h),
            layer="ground",
        )
        self._w, self._h = w, h
        self._color = color

    @Sprite.ready
    def setup(self) -> None:
        import pygame
        surf = pygame.Surface((self._w, self._h))
        surf.fill(self._color)
        self.image = surf

    @Sprite.draw
    def render(self, surface) -> None:
        self.draw_self(surface, Camera.offset)


# ══════════════════════════════════════════════════════════════════════════
# Scenes
# ══════════════════════════════════════════════════════════════════════════

@Scene("game")
class GameScene:

    @Scene.load
    def on_load(self) -> None:
        PhysicsWorld.set_gravity(0, GRAVITY.y)

        self.player   = Player()
        self.entities = SpriteGroup()
        self.entities.add(self.player)

        # Build level platforms
        for px, py, pw, ph in [
            (0,   490, 960, 50,),   # floor
            (300, 370,  160, 20),
            (550, 280,  160, 20),
            (150, 250,  120, 20),
            (700, 180,  200, 20),
        ]:
            p = Platform(px, py, pw, ph)
            self.entities.add(p)

        Camera.follow(self.player, smooth=0.1)
        Camera.set_world_bounds(0, 0, 960, 540)
        Camera.set_dead_zone(120, 80)

        # HUD
        self.score_label = Text("Score: 0",   x=16, y=12, size=22, color="white",
                                shadow=True, anchor="topleft")
        self.lives_label = Text("Lives: 3",   x=16, y=40, size=22, color="#FF6666",
                                shadow=True, anchor="topleft")
        self.hint_label  = Text("← → to move  |  SPACE to jump  |  ESC pause",
                                x=W//2, y=H-28, size=14, color="#AAAAAA",
                                align="center", anchor="midbottom")

        @Event.on("player_death")
        def on_death(data) -> None:
            lives = data["lives"]
            self.lives_label.set_text(f"Lives: {lives}")
            self.lives_label.set_color("#FF4444")
            Tween.to(self.lives_label, "font_size", 28, 0.1, Ease.OUT_QUAD).then(
                Tween.to(self.lives_label, "font_size", 22, 0.15, Ease.IN_QUAD)
            )
            if lives <= 0:
                Timer.after(2.0, lambda: Scene.switch("gameover"))

    @Scene.unload
    def on_unload(self) -> None:
        Event.clear("player_death")

    @Scene.update
    def on_update(self, dt) -> None:
        self.entities.update(dt)
        score = int(self.player.score)
        self.score_label.set_text(f"Score: {score}")

    @Scene.draw
    def on_draw(self, surface) -> None:
        surface.fill((25, 25, 35))
        self.entities.draw(surface, Camera.offset)
        self.score_label.draw(surface)
        self.lives_label.draw(surface)
        self.hint_label.draw(surface)


@Scene("gameover")
class GameOverScene:

    @Scene.load
    def on_load(self) -> None:
        self.title   = Text("GAME OVER",   x=W//2, y=200, size=64, color="#FF4444",
                            shadow=True, shadow_offset=(3, 3), anchor="center")
        self.sub     = Text("Press SPACE to restart", x=W//2, y=290, size=24,
                            color="white", anchor="center")
        # Fade the title in
        self.title.alpha = 0
        Tween.to(self.title, "alpha", 255, 0.8, ease=Ease.OUT_CUBIC)

    @Scene.update
    def on_update(self, dt) -> None:
        if Input.action_just_pressed("jump"):
            Scene.destroy_instance("game")
            Scene.switch("game")

    @Scene.draw
    def on_draw(self, surface) -> None:
        surface.fill((10, 10, 20))
        self.title.draw(surface)
        self.sub.draw(surface)


# ══════════════════════════════════════════════════════════════════════════
# Main Game
# ══════════════════════════════════════════════════════════════════════════

@Game(title="Pyunix v2 – Platformer Demo", size=(W, H), fps=60)
class PlatformerDemo:

    @Game.start
    def on_start(self) -> None:
        # Bind inputs
        Input.bind_action("jump", "SPACE", "W", "UP")
        Input.bind_axis("move", positive="RIGHT", negative="LEFT")
        Input.bind_axis("move", positive="d",     negative="a")

        # Start the first scene
        Scene.push("game")

    @Game.update
    def on_update(self, dt) -> None:
        Scene.update(dt)

    @Game.draw
    def on_draw(self, screen) -> None:
        Scene.draw(screen)


if __name__ == "__main__":
    PlatformerDemo().run()
