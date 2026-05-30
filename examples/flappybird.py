import os
import random
import pygame
from nestifypy.pyunix import Game, Input, Entity, SpriteGroup, Sprite
from nestifypy.pyunix.assets import Assets
from nestifypy.pyunix.physics import Rigidbody, BoxCollider, BodyType, PhysicsWorld
from nestifypy.types import Color

# Path to assets
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
Assets.set_base_path(ASSETS_DIR)

class Bird(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.DYNAMIC, gravity_scale=1.0),
            collider=BoxCollider(28, 20)
        )
        self.tag = "bird"

    @Sprite.ready
    def setup(self):
        frames = [
            Assets.image("bird1.png"),
            Assets.image("bird2.png"),
            Assets.image("bird3.png")
        ]
        self.animator.add_clip("fly", frames, fps=10, loop=True)
        self.animator.play("fly")
        self.jump_strength = -400.0

    def jump(self):
        self.set_velocity(0, self.jump_strength)

    @Sprite.update
    def tick(self, dt: float):
        self.animator.update(dt)
        if self.rigidbody:
            self.rotation = min(max(-self.rigidbody.velocity.y * 0.1, -90), 45)

    @Sprite.on_collision_enter
    def hit(self, info):
        if hasattr(self, "on_death"):
            self.on_death()

class Pipe(Entity):
    def __init__(self, x: float, y: float, flipped: bool = False):
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.KINEMATIC)
        )
        self.tag = "pipe"
        
        self.image = Assets.image("pipe.png")
        if flipped:
            self.image = pygame.transform.flip(self.image, False, True)
            self.y -= self.image.get_height() / 2
        else:
            self.y += self.image.get_height() / 2
            
        self.collider = BoxCollider(self.image.get_width() - 4, self.image.get_height())

    @Sprite.ready
    def setup(self):
        self.set_velocity(-200, 0)

class ScoreZone(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.KINEMATIC),
            collider=BoxCollider(20, 800, is_trigger=True)
        )
        self.tag = "score_zone"
        self.passed = False

    @Sprite.ready
    def setup(self):
        self.set_velocity(-200, 0)

    @Sprite.on_trigger_enter
    def score_point(self, info):
        if info.other.tag == "bird" and not self.passed:
            self.passed = True
            if hasattr(self, "on_score"):
                self.on_score()

@Game(title="Pyunix Flappy Bird", size=(400, 600), fps=60, resizable=False, fullscreen=False)
class FlappyBirdGame:
    def __init__(self):
        Assets.set_base_path(ASSETS_DIR)
        PhysicsWorld.set_gravity(0, 1200)

        self.bg_image = pygame.transform.scale(Assets.image("background.png"), (400, 600))
        self.ground_image = pygame.transform.scale(Assets.image("ground.png"), (400, 100))
        self.ground_x = 0
        
        self.entities = SpriteGroup()
        self.pipes = SpriteGroup()
        
        Input.bind_action("jump", "SPACE", "UP")
        
        self.reset_game()

    def reset_game(self):
        # Destroy old entities properly so they are removed from the Physics engine
        for entity in list(self.entities) + list(self.pipes):
            entity.destroy()
            
        self.entities.clear()
        self.pipes.clear()
        
        self.bird = Bird(100, 300)
        self.bird.on_death = self.trigger_game_over
        self.entities.add(self.bird)
        
        self.score = 0
        self.game_over = False
        self.pipe_timer = 0.0

    def trigger_game_over(self):
        if self.game_over: return
        self.game_over = True
        
        if self.bird.rigidbody:
            self.bird.set_velocity(0, 0)
            self.bird.rigidbody.gravity_scale = 0
            
        for pipe in list(self.pipes):
            if pipe.rigidbody:
                pipe.set_velocity(0, 0)

    def increment_score(self):
        if not self.game_over:
            self.score += 1

    @Input.action("jump")
    def jump(self):
        if not self.game_over:
            self.bird.jump()
        else:
            self.reset_game()

    @Game.update
    def update(self, dt: float):
        if self.game_over:
            return

        self.ground_x -= 200 * dt
        if self.ground_x <= -400:
            self.ground_x = 0

        self.entities.update(dt)
        self.pipes.update(dt)

        self.pipe_timer += dt
        if self.pipe_timer > 1.5:
            self.pipe_timer = 0.0
            gap_y = random.randint(200, 400)
            gap_size = 140
            
            p_bottom = Pipe(450, gap_y + gap_size / 2, flipped=False)
            p_top = Pipe(450, gap_y - gap_size / 2, flipped=True)
            zone = ScoreZone(450, gap_y)
            zone.on_score = self.increment_score
            
            self.pipes.add(p_bottom, p_top, zone)

        # Floor/Ceil collision
        if self.bird.y >= 500 or self.bird.y <= 0:
            self.trigger_game_over()

        # Remove offscreen pipes
        for pipe in list(self.pipes):
            if pipe.x < -100:
                pipe.destroy()
                self.pipes.remove(pipe)

    @Game.draw
    def draw(self, screen):
        screen.blit(self.bg_image, (0, 0))
        self.pipes.draw(screen)
        screen.blit(self.ground_image, (self.ground_x, 500))
        screen.blit(self.ground_image, (self.ground_x + 400, 500))
        self.entities.draw(screen)
        
        pygame.font.init()
        font = pygame.font.SysFont(None, 48)
        score_surface = font.render(str(self.score), True, Color.WHITE.to_tuple())
        screen.blit(score_surface, (200 - score_surface.get_width()//2, 50))
        
        if self.game_over:
            go_surface = font.render("Game Over! Press SPACE", True, Color.RED.to_tuple())
            screen.blit(go_surface, (200 - go_surface.get_width()//2, 250))

if __name__ == "__main__":
    game = FlappyBirdGame()
    game.run()
