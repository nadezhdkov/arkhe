"""
Example demonstrating the declarative Arkhe Pyunix game framework.
Run this script to see the game loop and decorators in action.
"""

from arkhe.pyunix import Game, Input, Entity, Sprite, SpriteGroup, Window
from arkhe.types import Color
import pygame

# We will create a simple player entity
class Player(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.speed = 300.0

        # We'll use a simple colored rectangle instead of a loaded image for the demo
        self.image = pygame.Surface((50, 50))
        self.image.fill(Color.RED.to_tuple())

    @Sprite.update
    def update(self, dt: float):
        # We can handle input directly in the entity, but let's just do gravity here
        pass

@Game(title="Pyunix Demo", size=(800, 600), fps=30)
class DemoGame:
    def __init__(self):
        self.player = Player(400, 300)
        self.entities = SpriteGroup()
        self.entities.add(self.player)
        
        # Action map test
        Input.bind_action("jump", "SPACE", "UP")

    @Game.start
    def start(self):
        print("Game Started!")

    @Input.action("jump")
    def jump(self):
        self.player.y -= 50


    @Input.key_held("LEFT")
    def move_left(self):
        # The game runtime updates at variable dt, but we don't have dt directly here.
        # This is a limitation of the current naive key_held hook, we just move by a constant 
        # or grab dt from the game loop. For now, constant.
        self.player.x -= 5
        
    @Input.key_held("RIGHT")
    def move_right(self):
        self.player.x += 5

    @Input.mouse_click("left")
    def on_click(self):
        pass

    @Game.update
    def tick(self, dt: float):
        self.entities.update(dt)

    @Game.fixed_update
    def physics_tick(self):
        # Gravity
        self.player.y += 2

        # Floor collision
        if self.player.y > 500:
            self.player.y = 500

    @Game.draw
    def draw(self, screen):
        screen.fill(Color.BLACK.to_tuple())
        self.entities.draw(screen)

    @Game.stop
    def stop(self):
        print("Game Stopped!")


if __name__ == "__main__":
    demo = DemoGame()
    demo.run()
