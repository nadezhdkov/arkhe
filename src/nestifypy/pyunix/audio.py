"""
nestifypy.pyunix.audio
-------------------
Audio management for music and sound effects.

This module provides a simplified interface over Pygame's mixer module.
It differentiates between background music (streamed from disk) and
sound effects (loaded entirely into memory for low-latency playback).

Usage:
    Audio.play_music("bg.mp3", loop=True, fade_ms=1000)
    Audio.play_sfx("jump.wav")
"""

from __future__ import annotations

from typing import Optional

from nestifypy.pyunix.assets import Assets
from nestifypy.pyunix.exceptions import AudioError

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


class AudioSystem:
    """
    Manager for Pygame mixer audio.

    Handles independent volume controls for music streams and sound effects,
    gracefully bypassing operations if Pygame is not installed.
    """

    def __init__(self) -> None:
        """Initialize the AudioSystem with default maximum volume."""
        self._music_volume = 1.0
        self._sfx_volume = 1.0

    def play_music(self, path: str, loop: bool = True, fade_ms: int = 0) -> None:
        """
        Stream background music from a file.

        Unlike sound effects, music is streamed directly from the file, saving memory.
        Only one music track can play at a time.

        Args:
            path (str): The file path or asset name to play.
            loop (bool): Whether the music should loop indefinitely. Defaults to True.
            fade_ms (int): Time in milliseconds to fade the music in. Defaults to 0 (immediate).

        Raises:
            AudioError: If the file cannot be found or Pygame fails to load/play it.
        """
        if not _HAS_PYGAME:
            return

        resolved = Assets._resolve(path)
        if not resolved.exists():
            raise AudioError(f"Music file not found: {resolved}")

        try:
            pygame.mixer.music.load(str(resolved))
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            pygame.mixer.music.set_volume(self._music_volume)
        except Exception as e:
            raise AudioError(f"Failed to play music: {e}")

    def stop_music(self, fade_ms: int = 0) -> None:
        """
        Stop the currently playing music track.

        Args:
            fade_ms (int): Time in milliseconds to fade the music out before stopping.
                Defaults to 0 (stops immediately).
        """
        if not _HAS_PYGAME:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def play_sfx(self, path: str) -> None:
        """
        Play a loaded sound effect.

        Sound effects are loaded entirely into memory via the `Assets` manager
        for low-latency, simultaneous playback.

        Args:
            path (str): The file path or asset name of the sound effect.
        """
        if not _HAS_PYGAME:
            return
        snd = Assets.sound(path)
        snd.set_volume(self._sfx_volume)
        snd.play()

    def set_music_volume(self, volume: float) -> None:
        """
        Set the global volume for music streams.

        Args:
            volume (float): The desired volume, clamped between 0.0 (mute) and 1.0 (max).
        """
        self._music_volume = max(0.0, min(1.0, volume))
        if _HAS_PYGAME:
            pygame.mixer.music.set_volume(self._music_volume)

    def set_sfx_volume(self, volume: float) -> None:
        """
        Set the global volume applied to all newly played sound effects.

        Note:
            This will not affect sound effects that are already currently playing.

        Args:
            volume (float): The desired volume, clamped between 0.0 (mute) and 1.0 (max).
        """
        self._sfx_volume = max(0.0, min(1.0, volume))


# Global singleton
Audio = AudioSystem()