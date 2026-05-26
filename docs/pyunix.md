# Pyunix Game Framework

`nestify.pyunix` is a highly declarative, decorator-driven game framework built on top of `pygame`. It abstracts away the complex game loop, delta-time calculations, input mapping, and rendering logic so you can focus entirely on game architecture.

---

## 1. The `@Game` Engine Loop

The entry point is the `@Game` decorator. It completely hides the standard `while running:` Pygame loop.

```python
from nestify.pyunix import Game, Color, Window

@Game(title="Cyberpunk 2077 Demake", size=(1280, 720), fps=60)
class MyGame:
    
    @Game.start
    def setup(self):
        print("Engine initialized! Window is open.")

    @Game.update
    def update(self, dt: float):
        # Variable Update: Called every frame. 
        # Always multiply movement by 'dt' to ensure smooth framerate-independent logic.
        pass

    @Game.fixed_update
    def physics(self):
        # Fixed Update: Called exactly 60 times per second.
        # Perfect for deterministic physics, collisions, and network synchronization.
        pass

    @Game.layer("background", priority=0)
    def draw_bg(self, screen):
        screen.fill(Color.from_hex("#111111").to_tuple())
        
    @Game.layer("ui", priority=100)
    def draw_ui(self, screen):
        # Drawn on top of everything else due to high priority
        pass

if __name__ == "__main__":
    game = MyGame()
    game.run() # Starts the managed engine loop
```

---

## 2. Decoupled Input System

Hardcoding `pygame.K_SPACE` leads to spaghetti code. Pyunix uses an Action Mapping system, allowing you to bind multiple physical keys to logical actions, and attach decorators directly to them.

```python
from nestify.pyunix import Input

# Map multiple keys to logical actions
Input.bind_action("jump", "SPACE", "UP", "W")
Input.bind_action("shoot", "Z", "RETURN")

class PlayerController:
    
    @Input.action("jump")
    def on_jump(self):
        # Fires exactly ONCE when the button is pressed down
        self.velocity.y = -10

    @Input.key_held("RIGHT")
    def walk_right(self):
        # Fires CONTINUOUSLY while the physical right arrow is held
        self.x += 200 * dt
        
    @Input.mouse_click("left")
    def on_click(self):
        print("Pew pew!")
```

---

## 3. ECS-Friendly Entities (`@Sprite`)

The `Entity` and `SpriteGroup` systems replace massive `update()` monoliths with modular, self-contained objects.

```python
from nestify.pyunix import Entity, Sprite, SpriteGroup, Assets

class Enemy(Entity):
    @Sprite.ready
    def setup(self):
        # Assets are automatically cached in memory
        self.image = Assets.image("enemy.png")
        self.hp = 100

    @Sprite.update
    def tick(self, dt: float):
        self.x -= 50 * dt

    @Sprite.destroy
    def on_death(self):
        # Hook triggered when entity.destroy() is called
        print("Enemy defeated!")

# In your main game:
enemies = SpriteGroup()
enemies.add(Enemy(x=500, y=300))

# Updates and draws all entities automatically
enemies.update(dt) 
enemies.draw(screen)
```

### Collisions
Entities come with built-in spatial math:
```python
if player.collides_with(enemy):
    player.take_damage()

if player.distance_to(item) < 50.0:
    item.pickup()
```

---

## 4. Scene Management (State Machine)

Instead of complex `if state == "MENU":` logic, use the Stack-based `SceneManager`.

```python
from nestify.pyunix import Scene

@Scene("main_menu")
class MainMenu:
    @Scene.load
    def enter(self):
        print("Fading into Menu...")

    @Scene.unload
    def exit(self):
        print("Cleaning up menu assets...")

# Push a scene onto the stack (pauses the previous scene)
Scene.push("main_menu")

# Pop the current scene (resumes the previous scene)
Scene.pop()
```

---

## 5. Global Event Bus

Decouple your game objects using the global Event Bus.

```python
from nestify.pyunix import Event

# Listener
@Event.on("level_up")
def play_fanfare(data):
    print(f"Leveled up to {data['level']}!")

# Emitter (can be called from anywhere)
Event.emit("level_up", {"level": 2})
```

---

## 6. Advanced Subsystems: Camera, Audio, & Timers

Pyunix provides built-in managers for complex game math.

### The Camera
```python
from nestify.pyunix import Camera

# Smoothly lerp towards a target Entity
Camera.follow(player, smooth=0.1)

# Screen shake for explosions!
Camera.shake(intensity=10.0, duration=0.5)

# Camera automatically applies offsets during SpriteGroup.draw()
enemies.draw(screen, offset=(Camera.x, Camera.y))
```

### Audio
```python
from nestify.pyunix import Audio

Audio.play_music("cyberpunk_theme.ogg", loop=True)
Audio.play_sfx("laser.wav", volume=0.5)
```

### Timers
A timer system that inherently respects `dt` and game pauses.
```python
from nestify.pyunix import Timer

# Fire and forget
Timer.after(2.0, lambda: print("Bomb exploded!"))

# Recurring loops
Timer.every(0.5, spawn_enemy)
```

---

## 7. Physics & Rigidbody

Pyunix includes a built-in 2D physics system. Add a `Rigidbody` and `Collider` to any `Entity` to integrate it into the `PhysicsWorld`.

```python
from nestify.pyunix import Entity, Rigidbody, BodyType, BoxCollider, PhysicsMaterial

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            layer="player",
            rigidbody=Rigidbody(
                body_type=BodyType.DYNAMIC,
                mass=1.0,
                drag=0.1,
                mask={"world", "enemy"}
            ),
            collider=BoxCollider(
                width=32, height=32,
                material=PhysicsMaterial(friction=0.5, bounciness=0.2)
            )
        )

    @Sprite.update
    def jump(self, dt):
        if self.input.is_action_pressed("jump"):
            # Apply an instantaneous impulse
            self.rigidbody.add_impulse(Vector2(0, -500))

    @Sprite.on_collision_enter
    def on_hit(self, info):
        if info.other.layer == "enemy":
            print(f"Hit by enemy! Normal: {info.normal}")
```

### Sensor Queries
The `PhysicsWorld` can be queried to find objects in specific areas.
```python
from nestify.pyunix import PhysicsWorld

# Find all entities in a rectangular area that are in the "enemy" layer
enemies = PhysicsWorld.overlap_rect((0, 0, 100, 100), mask={"enemy"})
```

---

## 8. Declarative Text & Fonts

Pyunix provides a declarative text system that automatically handles caching, outlines, shadows, and alignment.

First, load your fonts:
```python
from nestify.pyunix import Fonts

Fonts.load("main", "assets/fonts/PressStart2P.ttf")
```

Then, use the `@Game.text` decorator to automatically render text every frame:
```python
@Game.text(x=10, y=10, font="main", size=24, color="white", shadow=True, outline=True)
def draw_score(self):
    return f"SCORE: {self.score}"
```

You can also create standalone `Text` entities:
```python
from nestify.pyunix import Text

title = Text(
    "GAME OVER",
    x=400, y=300,
    font="main", size=48, color="red",
    align="center", anchor="center",
    outline=True, outline_size=2
)
# Add to SpriteGroup just like any Entity
group.add(title)
```
