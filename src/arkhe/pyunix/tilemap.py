"""
arkhe.pyunix.tilemap
------------------------
Tile-based level rendering with collision generation and CSV/2D-array loading.

Supports multiple layers (background, collision, decoration), automatic
static BoxCollider generation for solid tiles, and camera-culled rendering
so only visible tiles are drawn.

Usage:
    # Define a tile set
    tileset = TileSet("tiles.png", tile_size=(16, 16))
    tileset.mark_solid(1, 2, 3)    # tile IDs that block movement

    # Load a map from a 2D list (or CSV)
    tilemap = TileMap(tileset, tile_size=(16, 16))
    tilemap.load_layer("ground", [
        [1, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1],
        [2, 2, 2, 2],
    ])
    tilemap.build_colliders()     # generates physics bodies for solid tiles

    # In draw:
    tilemap.draw(screen, Camera.offset, Camera.zoom_level)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from arkhe.pyunix.math import Vector2

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


# ---------------------------------------------------------------------------
# TileSet
# ---------------------------------------------------------------------------

class TileSet:
    """
    A sprite-sheet sliced into individual tile frames.

    Args:
        path:       Path to the tile sheet image.
        tile_size:  (width, height) of each tile in pixels.
    """

    def __init__(self, path: str, tile_size: Tuple[int, int]) -> None:
        from arkhe.pyunix.assets import Assets
        self._path      = path
        self._tile_size = tile_size
        self._tiles: List[Any] = []   # list of pygame Surfaces indexed by tile ID
        self._solid_ids: Set[int] = set()
        self._custom_props: Dict[int, dict] = {}

        self._tiles = Assets.spritesheet(path, tile_size)

    def mark_solid(self, *tile_ids: int) -> "TileSet":
        """Mark tile IDs as physically solid (will generate colliders)."""
        self._solid_ids.update(tile_ids)
        return self

    def is_solid(self, tile_id: int) -> bool:
        return tile_id in self._solid_ids

    def set_property(self, tile_id: int, **props: Any) -> None:
        """Attach custom key-value properties to a tile ID."""
        if tile_id not in self._custom_props:
            self._custom_props[tile_id] = {}
        self._custom_props[tile_id].update(props)

    def get_property(self, tile_id: int, key: str, default: Any = None) -> Any:
        return self._custom_props.get(tile_id, {}).get(key, default)

    def get_surface(self, tile_id: int) -> Optional[Any]:
        if 0 <= tile_id < len(self._tiles):
            return self._tiles[tile_id]
        return None

    @property
    def tile_width(self) -> int:
        return self._tile_size[0]

    @property
    def tile_height(self) -> int:
        return self._tile_size[1]


# ---------------------------------------------------------------------------
# TileMap
# ---------------------------------------------------------------------------

@dataclass
class _TileLayer:
    name: str
    data: List[List[int]]
    visible: bool = True
    opacity: float = 1.0


class TileMap:
    """
    A multi-layer tile map with camera-culled rendering and auto-generated colliders.
    """

    def __init__(self, tileset: TileSet, tile_size: Optional[Tuple[int, int]] = None) -> None:
        self.tileset    = tileset
        self.tile_w     = tile_size[0] if tile_size else tileset.tile_width
        self.tile_h     = tile_size[1] if tile_size else tileset.tile_height
        self._layers:   List[_TileLayer] = []
        self._colliders: List[Any] = []   # Static physics entities

    # ── Loading ──────────────────────────────

    def load_layer(
        self,
        name: str,
        data: List[List[int]],
        visible: bool = True,
        opacity: float = 1.0,
    ) -> "TileMap":
        """
        Add a tile layer from a 2D list.

        Args:
            name:    Unique layer name.
            data:    2D list of tile IDs (0 = empty/transparent).
            visible: Whether to render this layer.
            opacity: Layer transparency 0.0–1.0.
        """
        self._layers.append(_TileLayer(name=name, data=data,
                                       visible=visible, opacity=opacity))
        return self

    def load_layer_csv(self, name: str, path: str, **kwargs: Any) -> "TileMap":
        """Load a layer from a CSV file (one row per line, comma-separated tile IDs)."""
        import csv
        from pathlib import Path
        with open(Path(path)) as f:
            reader = csv.reader(f)
            data = [[int(v) for v in row] for row in reader]
        return self.load_layer(name, data, **kwargs)

    def get_layer(self, name: str) -> Optional[_TileLayer]:
        return next((l for l in self._layers if l.name == name), None)

    # ── Properties ───────────────────────────

    @property
    def width_tiles(self) -> int:
        if not self._layers:
            return 0
        return max((len(row) for layer in self._layers for row in layer.data), default=0)

    @property
    def height_tiles(self) -> int:
        if not self._layers:
            return 0
        return max(len(layer.data) for layer in self._layers)

    @property
    def pixel_width(self) -> int:
        return self.width_tiles * self.tile_w

    @property
    def pixel_height(self) -> int:
        return self.height_tiles * self.tile_h

    # ── Tile access ──────────────────────────

    def get_tile(self, layer_name: str, col: int, row: int) -> int:
        """Return tile ID at (col, row) in the named layer (0 = empty)."""
        layer = self.get_layer(layer_name)
        if not layer:
            return 0
        try:
            return layer.data[row][col]
        except IndexError:
            return 0

    def set_tile(self, layer_name: str, col: int, row: int, tile_id: int) -> None:
        """Set the tile at (col, row) in the named layer."""
        layer = self.get_layer(layer_name)
        if not layer:
            return
        try:
            layer.data[row][col] = tile_id
        except IndexError:
            pass

    def world_to_tile(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world-space coordinates to tile column/row."""
        return (int(world_x // self.tile_w), int(world_y // self.tile_h))

    def tile_to_world(self, col: int, row: int) -> Tuple[float, float]:
        """Convert tile column/row to world-space top-left pixel coordinates."""
        return (col * self.tile_w, row * self.tile_h)

    # ── Colliders ────────────────────────────

    def build_colliders(self, layer_name: str = None) -> None:
        """
        Generate static BoxCollider entities for every solid tile.

        If `layer_name` is None, all layers are scanned. Existing colliders
        are cleared first.

        Note:
            This does a simple 1-tile-per-body approach. For large maps consider
            merging adjacent solid tiles into larger rectangles (not implemented here).
        """
        from arkhe.pyunix.sprite import Entity
        from arkhe.pyunix.physics import BoxCollider, Rigidbody, BodyType, PhysicsWorld

        # Remove old colliders
        for e in self._colliders:
            PhysicsWorld.unregister(e)
        self._colliders.clear()

        layers_to_scan = (
            [self.get_layer(layer_name)] if layer_name else self._layers
        )

        for layer in layers_to_scan:
            if layer is None:
                continue
            for row_idx, row in enumerate(layer.data):
                for col_idx, tile_id in enumerate(row):
                    if tile_id > 0 and self.tileset.is_solid(tile_id):
                        wx = col_idx * self.tile_w + self.tile_w / 2
                        wy = row_idx * self.tile_h + self.tile_h / 2
                        e = Entity(
                            x=wx, y=wy,
                            rigidbody=Rigidbody(body_type=BodyType.STATIC),
                            collider=BoxCollider(
                                width=float(self.tile_w),
                                height=float(self.tile_h),
                            ),
                        )
                        self._colliders.append(e)

    # ── Rendering ────────────────────────────

    def draw(
        self,
        surface: Any,
        offset: Tuple[float, float] = (0.0, 0.0),
        zoom: float = 1.0,
        screen_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Draw all visible layers with camera culling.

        Args:
            surface:     pygame Surface to draw onto.
            offset:      Camera offset (Camera.offset).
            zoom:        Camera zoom level (Camera.zoom_level).
            screen_size: (w, h) of the viewport — used for culling. Auto-detected if None.
        """
        if not _HAS_PYGAME:
            return

        ox, oy = offset
        if screen_size is None:
            screen_size = surface.get_size()
        sw, sh = screen_size

        # Visible tile range
        start_col = max(0, int(ox / self.tile_w))
        start_row = max(0, int(oy / self.tile_h))
        end_col   = min(self.width_tiles,  int((ox + sw / zoom) / self.tile_w) + 2)
        end_row   = min(self.height_tiles, int((oy + sh / zoom) / self.tile_h) + 2)

        for layer in self._layers:
            if not layer.visible:
                continue
            for row in range(start_row, end_row):
                if row >= len(layer.data):
                    break
                for col in range(start_col, end_col):
                    if col >= len(layer.data[row]):
                        continue
                    tile_id = layer.data[row][col]
                    if tile_id <= 0:
                        continue
                    tile_surf = self.tileset.get_surface(tile_id - 1)  # 1-indexed IDs
                    if tile_surf is None:
                        continue
                    dx = int((col * self.tile_w - ox) * zoom)
                    dy = int((row * self.tile_h - oy) * zoom)
                    if zoom != 1.0:
                        tile_surf = pygame.transform.scale(
                            tile_surf,
                            (int(self.tile_w * zoom), int(self.tile_h * zoom))
                        )
                    if layer.opacity < 1.0:
                        tile_surf = tile_surf.copy()
                        tile_surf.set_alpha(int(layer.opacity * 255))
                    surface.blit(tile_surf, (dx, dy))
