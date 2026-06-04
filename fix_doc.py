import re

with open("docs/pyunix.md", "r") as f:
    content = f.read()

# Fix @Game.draw and @Sprite.draw signatures
content = re.sub(r'def \w+\(self, screen\):', lambda m: m.group(0).replace(', screen', ''), content)
content = re.sub(r'def \w+\(self, surface\):', lambda m: m.group(0).replace(', surface', ''), content)

# Fix draw_self calls
content = content.replace('self.draw_self(surface, Camera.offset)', 'self.draw_self(Camera.offset)')
content = content.replace('self.draw_self(screen, Camera.offset)', 'self.draw_self(Camera.offset)')
content = content.replace('self.draw_self(surface)', 'self.draw_self()')
content = content.replace('self.draw_self(screen)', 'self.draw_self()')
content = content.replace('self.jogador._dispatch("draw", screen)', 'self.jogador._dispatch("draw")')
content = content.replace('self.jogador._dispatch("draw", surface)', 'self.jogador._dispatch("draw")')
content = content.replace('self.enemies.draw(screen, Camera.offset)', 'self.enemies.draw(Camera.offset)')
content = content.replace('self.plataformas.draw(screen, Camera.offset)', 'self.plataformas.draw(Camera.offset)')
content = content.replace('self.hud.draw(screen)', 'self.hud.draw()')
content = content.replace('self.titulo.draw(surface)', 'self.titulo.draw()')
content = content.replace('Scene.draw(screen)', 'Scene.draw()')
content = content.replace('mapa.draw(screen, Camera.offset, Camera.zoom_level)', 'mapa.draw(Camera.offset, Camera.zoom_level)')
content = content.replace('titulo.draw(screen)', 'titulo.draw()')


# Fix pygame imports in code blocks
content = re.sub(r'import pygame\n\s*rect = pygame\.Rect\(.*\)\n\s*pygame\.draw\.rect\(.*?\)', 
                 'from arkhe.pyunix.render.draw import Draw\n        Draw.rect(self.x - 14, self.y - 24, 28, 48, (100, 180, 255))', 
                 content)

content = re.sub(r'import pygame\n\s*rect = pygame\.Rect\(\n.*?\n.*?\n.*?\n\s*\)\n\s*pygame\.draw\.rect\(.*?\)', 
                 'from arkhe.pyunix.render.draw import Draw\n        Draw.rect(self.x - self._largura // 2, self.y - self._altura // 2, self._largura, self._altura, (80, 160, 80))', 
                 content, flags=re.DOTALL)

content = re.sub(r'import pygame\n\s*font = pygame\.font\.SysFont\(None, 32\)\n\s*texto = font\.render\(f"Pontos: \{self\.pontos\}", True, \(255, 255, 100\)\)\n\s*screen\.blit\(texto, \(10, 10\)\)',
                 'from arkhe.pyunix.render.draw import Draw\n        Draw.text(f"Pontos: {self.pontos}", 10, 10, size=32, color=(255, 255, 100))',
                 content)

# Fix screen.fill to Canvas.clear
content = content.replace('screen.fill((30, 30, 40))', 'Canvas.clear((30, 30, 40))')
content = content.replace('screen.fill((20, 20, 30))', 'Canvas.clear((20, 20, 30))')
content = content.replace('screen.fill((0, 0, 0))', 'Canvas.clear((0, 0, 0))')
content = content.replace('screen.fill((30, 30, 50))', 'Canvas.clear((30, 30, 50))')

# Add Canvas import in examples
content = content.replace('from arkhe.pyunix.app import Game', 'from arkhe.pyunix.app import Game\nfrom arkhe.pyunix.render.canvas import Canvas')

# Component usage update
component_old = '''# Componentes customizados
entity.add_component("saude", SistemaDeVida())
entity.get_component("saude")
entity.has_component("saude")
entity.remove_component("saude")'''

component_new = '''# Componentes customizados (Unity-style ECS)
entity.add_component(Health(100))
entity.get_component(Health)
entity.has_component(Health)
entity.remove_component(Health)'''
content = content.replace(component_old, component_new)

with open("docs/pyunix.md", "w") as f:
    f.write(content)

print("Done")
