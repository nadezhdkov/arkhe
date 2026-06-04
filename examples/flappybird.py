"""
Flappy Bird — arkhe.pyunix
==============================
Reescrito para usar o sistema pyunix corretamente:

  - @Game(...)         loop + janela
  - @Game.start        inicialização
  - @Game.layer(...)   camadas ordenadas de renderização
  - @Game.text(...)    HUD de pontuação sem pygame.font manual
  - @Game.on_pause / @Game.on_resume  integração com ESC
  - @Sprite.ready      setup de entidades
  - @Sprite.update     lógica por frame
  - @Sprite.draw       renderização via draw_self (sem duplicação)
  - @Sprite.on_collision_enter / on_trigger_enter  física
  - @Input.action      resposta a input por evento
  - Timer.after        delay para game-over → reset
  - Timer.pause/resume integração com pausa do jogo
  - Save               persistência de recorde entre sessões
  - Tween              animação de flash no score e fade de tela
  - Camera.shake       feedback de colisão
  - Event              comunicação desacoplada entre entidades e jogo
"""

import os
import random

import pygame

from arkhe.pyunix.app import Game
from arkhe.pyunix.render.draw import Draw
from arkhe.pyunix.render.canvas import Canvas
from arkhe.pyunix.assets import Assets
from arkhe.pyunix.camera import Camera
from arkhe.pyunix.events import Event
from arkhe.pyunix.input import Input
from arkhe.pyunix.math import Color, Vector2
from arkhe.pyunix.physics import (
    BodyType, BoxCollider, PhysicsWorld, Rigidbody,
)
from arkhe.pyunix.save import Save
from arkhe.pyunix.sprite import Entity, Sprite, SpriteGroup
from arkhe.pyunix.timer import Timer
from arkhe.pyunix.tween import Ease, Tween

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SCREEN_W, SCREEN_H = 400, 600
PIPE_SPEED          = -200          # px/s
PIPE_INTERVAL       = 1.5           # segundos entre pares de canos
GAP_SIZE            = 140           # abertura entre canos
GAP_Y_MIN           = 180
GAP_Y_MAX           = 400
GROUND_Y            = 500           # borda superior do chão
BIRD_X              = 100

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ---------------------------------------------------------------------------
# Bird
# ---------------------------------------------------------------------------

class Bird(Entity):
    """
    Pássaro controlado pelo jogador.

    Física DYNAMIC com gravity_scale ajustável.
    Ao colidir emite o evento global "bird_died" — o jogo reage de forma
    desacoplada sem referência direta de volta para a entidade.
    """

    JUMP_STRENGTH = -420.0

    def __init__(self) -> None:
        super().__init__(
            x=BIRD_X, y=SCREEN_H // 2,
            rigidbody=Rigidbody(
                body_type=BodyType.DYNAMIC,
                gravity_scale=1.0,
            ),
            collider=BoxCollider(28, 20),
        )
        self.tag = "bird"
        self.dead = False

    @Sprite.ready
    def setup(self) -> None:
        frames = [
            Assets.image("bird1.png"),
            Assets.image("bird2.png"),
            Assets.image("bird3.png"),
        ]
        self.animator.add_clip("fly",  frames, fps=10, loop=True)
        self.animator.add_clip("dead", frames[:1], fps=1, loop=True)
        self.animator.play("fly")

    def jump(self) -> None:
        if not self.dead:
            self.set_velocity(0, self.JUMP_STRENGTH)

    def die(self) -> None:
        """Congela física, muda clip e dispara evento global."""
        if self.dead:
            return
        self.dead = True
        self.rigidbody.gravity_scale = 0.0
        self.set_velocity(0, 0)
        self.animator.play("dead")
        Event.emit("bird_died")

    @Sprite.update
    def tick(self, dt: float) -> None:
        self.animator.update(dt)
        if not self.dead and self.rigidbody:
            # Inclina o pássaro para baixo ao cair, para cima ao subir
            vy = self.rigidbody.velocity.y
            self.rotation = min(max(vy * 0.1, -30), 90)

    @Sprite.draw
    def render(self) -> None:
        self.draw_self()   # câmera em (0,0) — sem offset

    @Sprite.on_collision_enter
    def on_hit(self, info) -> None:
        self.die()

    @Sprite.on_trigger_enter
    def on_trigger(self, info) -> None:
        # ScoreZone usa trigger; a própria zone emite "bird_scored"
        pass


# ---------------------------------------------------------------------------
# Pipe
# ---------------------------------------------------------------------------

class Pipe(Entity):
    """
    Cano KINEMATIC que se move para a esquerda em velocidade constante.
    Usa draw_self para renderização — SpriteGroup chama automaticamente
    (sem @Sprite.draw definido = fallback do grupo).
    """

    def __init__(self, x: float, y: float, flipped: bool = False) -> None:
        super().__init__(
            x=x, y=y,
            rigidbody=Rigidbody(body_type=BodyType.KINEMATIC),
        )
        self.tag = "pipe"

        img = Assets.image("pipe.png")
        if flipped:
            img = pygame.transform.flip(img, False, True)

        self.image = img

        # Ancoragem: cano de baixo tem topo na gap_y + gap/2,
        # cano de cima tem base na gap_y - gap/2
        half_h = img.get_height() / 2
        if flipped:
            # cano superior: posição y = gap_y - gap/2 → âncora no fundo
            self.y = y - half_h
        else:
            # cano inferior: posição y = gap_y + gap/2 → âncora no topo
            self.y = y + half_h

        self.collider = BoxCollider(img.get_width() - 4, img.get_height())

    @Sprite.ready
    def setup(self) -> None:
        self.set_velocity(PIPE_SPEED, 0)


# ---------------------------------------------------------------------------
# ScoreZone
# ---------------------------------------------------------------------------

class ScoreZone(Entity):
    """
    Trigger invisível entre os dois canos.
    Quando o pássaro atravessa, emite "bird_scored".
    """

    def __init__(self, x: float, gap_y: float) -> None:
        super().__init__(
            x=x, y=gap_y,
            rigidbody=Rigidbody(body_type=BodyType.KINEMATIC),
            collider=BoxCollider(10, GAP_SIZE - 10, is_trigger=True),
        )
        self.tag = "score_zone"
        self._scored = False

    @Sprite.ready
    def setup(self) -> None:
        self.set_velocity(PIPE_SPEED, 0)

    @Sprite.on_trigger_enter
    def on_enter(self, info) -> None:
        if info.other.tag == "bird" and not self._scored:
            self._scored = True
            Event.emit("bird_scored")


# ---------------------------------------------------------------------------
# FlappyBirdGame
# ---------------------------------------------------------------------------

@Game(title="Pyunix Flappy Bird", size=(SCREEN_W, SCREEN_H), fps=60)
class FlappyBirdGame:
    """
    Jogo principal.

    Estrutura de renderização por layers ordenados:
      0 — background
      1 — pipes
      2 — ground
      3 — bird
      4 — ui   (gerenciado por @Game.text + overlay manual)

    Comunicação com as entidades exclusivamente via Event — sem callbacks
    diretos (on_death / on_score) como no código original.
    """

    # ── Inicialização ────────────────────────

    def __init__(self) -> None:
        Assets.set_base_path(ASSETS_DIR)
        PhysicsWorld.set_gravity(0, 1400)
        PhysicsWorld.set_cell_size(64)

        # Assets de background/ground (não são entidades)
        self._bg     = Assets.image("background.png", scale=(SCREEN_W, SCREEN_H)) # pygame.transform.scale(Assets.image("background.png"), (SCREEN_W, SCREEN_H))
        self._ground = Assets.image("ground.png", scale=(SCREEN_W, 100)) # pygame.transform.scale(Assets.image("ground.png"), (SCREEN_W, 100))
        self._ground_x: float = 0.0

        # Grupos de entidades
        self._bird_group  = SpriteGroup()
        self._pipe_group  = SpriteGroup()

        # Estado do jogo
        self._score:     int   = 0
        self._game_over: bool  = False
        self._pipe_timer: float = 0.0
        self._flash_alpha: float = 0.0   # alpha do flash branco ao marcar ponto

        # Persistência de recorde
        Save.set_path("saves/")
        Save.set_defaults({"record": 0})
        Save.load()

        # Bindings de input
        Input.bind_action("jump", "SPACE", "UP")

        # Eventos globais emitidos pelas entidades
        Event.on("bird_died")(self._on_bird_died)
        Event.on("bird_scored")(self._on_bird_scored)

        self._start_round()

    # ── Round / Reset ────────────────────────

    def _start_round(self) -> None:
        """Inicia ou reinicia uma rodada completa."""
        # Remove entidades antigas da física e dos grupos
        for e in list(self._bird_group) + list(self._pipe_group):
            e.destroy()
        self._bird_group.clear()
        self._pipe_group.clear()
        Tween.kill_all()

        self._score      = 0
        self._game_over  = False
        self._pipe_timer = 0.0
        self._flash_alpha = 0.0

        self._bird = Bird()
        self._bird_group.add(self._bird)

    def _on_bird_died(self) -> None:
        """Reage à morte do pássaro: shake, congela pipes, agenda reset."""
        if self._game_over:
            return
        self._game_over = True

        # Para todos os pipes
        for pipe in list(self._pipe_group):
            pipe.set_velocity(0, 0)

        # Screen shake via Camera
        Camera.shake(intensity=10, duration=0.35)

        # Salva recorde se bateu
        if self._score > Save.get("record"):
            Save.set("record", self._score)
            Save.commit()

    def _on_bird_scored(self) -> None:
        """Incrementa score e anima o flash."""
        if self._game_over:
            return
        self._score += 1
        # Flash branco rápido usando Tween no próprio campo float
        self._flash_alpha = 80.0
        Tween.to(self, "_flash_alpha", 0.0, duration=0.25, ease=Ease.OUT_QUAD)

    # ── Input ────────────────────────────────

    @Input.action("jump")
    def on_jump(self) -> None:
        if not self._game_over:
            self._bird.jump()
        else:
            # Qualquer tecla de jump reinicia após game-over
            self._start_round()

    # ── Pause / Resume ───────────────────────

    @Game.on_pause
    def on_pause(self) -> None:
        Timer.pause()

    @Game.on_resume
    def on_resume(self) -> None:
        Timer.resume()

    # ── Update ───────────────────────────────

    @Game.start
    def on_start(self) -> None:
        """Chamado pelo engine após a janela ser criada."""
        # Nada extra necessário — __init__ já faz tudo porque o
        # @Game decorator chama original_init depois de criar a janela.
        pass

    @Game.update
    def update(self, dt: float) -> None:
        if self._game_over:
            return

        # Ground scroll
        self._ground_x -= 200 * dt
        if self._ground_x <= -SCREEN_W:
            self._ground_x = 0.0

        # Atualiza entidades
        self._bird_group.update(dt)
        self._pipe_group.update(dt)

        # Spawn de canos
        self._pipe_timer += dt
        if self._pipe_timer >= PIPE_INTERVAL:
            self._pipe_timer = 0.0
            self._spawn_pipe_pair()

        # Colisão com chão / teto
        if self._bird.y >= GROUND_Y or self._bird.y <= 0:
            self._bird.die()

        # Remove pipes fora da tela
        for pipe in list(self._pipe_group):
            if pipe.x < -120:
                pipe.destroy()
                self._pipe_group.remove(pipe)

    def _spawn_pipe_pair(self) -> None:
        gap_y = random.randint(GAP_Y_MIN, GAP_Y_MAX)
        x     = SCREEN_W + 60

        p_bottom  = Pipe(x, gap_y + GAP_SIZE / 2, flipped=False)
        p_top     = Pipe(x, gap_y - GAP_SIZE / 2, flipped=True)
        zone      = ScoreZone(x, gap_y)

        self._pipe_group.add(p_bottom, p_top, zone)

    # ── Layers de Renderização ───────────────

    @Game.layer("background", order=0)
    def draw_background(self) -> None:
        Draw.image(self._bg, 0, 0)

    @Game.layer("pipes", order=1)
    def draw_pipes(self) -> None:
        self._pipe_group.draw()

    @Game.layer("ground", order=2)
    def draw_ground(self) -> None:
        gx = int(self._ground_x)
        Draw.image(self._ground, gx, GROUND_Y)
        Draw.image(self._ground, gx + SCREEN_W, GROUND_Y)

    @Game.layer("bird", order=3)
    def draw_bird(self) -> None:
        self._bird_group.draw()

    @Game.layer("ui", order=4)
    def draw_ui(self) -> None:
        # Pontuação centralizada
        Draw.text(str(self._score), x=SCREEN_W // 2, y=45, size=56, color="white", anchor="midtop")

        # Flash branco ao pontuar
        if self._flash_alpha > 0:
            Draw.rect(0, 0, SCREEN_W, SCREEN_H, color=Color(255, 255, 255, int(self._flash_alpha)))

        # Tela de Game Over
        if self._game_over:
            self._draw_game_over()

    def _draw_game_over(self) -> None:
        # Overlay escuro semi-transparente
        Draw.rect(0, 0, SCREEN_W, SCREEN_H, color=Color(0, 0, 0, 140))

        cx = SCREEN_W // 2

        # "GAME OVER"
        Draw.text("GAME OVER", x=cx, y=190, size=58, color=Color(255, 80, 80), anchor="center")

        # Pontuação atual
        Draw.text(f"Pontuação: {self._score}", x=cx, y=265, size=34, color="white", anchor="center")

        # Recorde
        record = Save.get("record")
        Draw.text(f"Recorde:    {record}", x=cx, y=305, size=34, color=Color(255, 220, 60), anchor="center")

        # Instrução de restart
        Draw.text("SPACE ou ↑ para jogar de novo", x=cx, y=360, size=26, color=Color(200, 200, 200), anchor="center")

    # ── HUD de recorde via @Game.text ────────
    # (renderizado automaticamente pelo engine sobre todas as layers)

    @Game.text(x=8, y=8, size=18, color="yellow", anchor="topleft")
    def record_label(self) -> str:
        return f"Recorde: {Save.get('record')}"

    # ── Encerramento ─────────────────────────

    @Game.stop
    def on_stop(self) -> None:
        Save.commit()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    FlappyBirdGame().run()