"""The audio player: the mixer, the music loop and the effects.

`load_audio` opens the mixer, loads the six sound files once and sets every volume once.
`AudioPlayer` starts the loop, pauses and resumes it (the mute) and plays the cues a tick asked
for (`core.sound_cue.SoundCue`). The loop is the mixer's music stream; each effect plays on its
own free channel, and a cue with no free channel is dropped, never cutting a sound that plays.
Sound never changes a game rule.

Source: docs/contracts/systems/audio.md, Interface and Rules; 15-tech-constraints.md, rules 3
and 5.
"""

import logging
from pathlib import Path

import pygame

from app.audio_tuning import AudioLevels
from core.sound_cue import SoundCue

log = logging.getLogger(__name__)

AUDIO_DIR: Path = Path(__file__).resolve().parent.parent / "assets" / "audio"
"""The audio folder in assets. Holds the loop and the five effects, all .ogg."""

MUSIC_FILE: str = "music_loop.ogg"
"""The music loop."""

EFFECT_FILES: dict[SoundCue, str] = {
    SoundCue.HIT: "sfx_hit.ogg",
    SoundCue.GRAZE: "sfx_graze.ogg",
    SoundCue.COIN: "sfx_coin.ogg",
    SoundCue.GAME_OVER: "sfx_game_over.ogg",
    SoundCue.LEVEL_UP: "sfx_level_up.ogg",
}
"""The file of each cue."""


class AudioPlayer:
    """The one owner of the music stream and the effect sounds."""

    def __init__(self, music_volume: float, effects: dict[SoundCue, pygame.mixer.Sound]) -> None:
        self._music_volume: float = music_volume
        self._effects: dict[SoundCue, pygame.mixer.Sound] = effects
        self._music_started: bool = False
        self._music_paused: bool = False

    @property
    def music_paused(self) -> bool:
        """True from pause_music until resume_music: the one source of "the music is muted"."""
        return self._music_paused

    def start_music(self) -> None:
        """Start the loop from its beginning, looping with no end. A second call does nothing."""
        if self._music_started:
            return
        pygame.mixer.music.load(str(AUDIO_DIR / MUSIC_FILE))
        pygame.mixer.music.set_volume(self._music_volume)
        pygame.mixer.music.play(loops=-1)
        self._music_started = True
        self._music_paused = False
        log.debug("music start")

    def pause_music(self) -> None:
        """Pause the music stream where it is. A no-op when paused or not started. Effects stay."""
        if not self._music_started or self._music_paused:
            return
        pygame.mixer.music.pause()
        self._music_paused = True
        log.debug("music pause")

    def resume_music(self) -> None:
        """Continue the music from where it paused, never from the start. A no-op if not paused."""
        if not self._music_paused:
            return
        pygame.mixer.music.unpause()
        self._music_paused = False
        log.debug("music resume")

    def play_cues(self, cues: tuple[SoundCue, ...]) -> None:
        """Play each cue in order on a free effect channel; drop one when none is free."""
        for cue in cues:
            channel: pygame.mixer.Channel | None = pygame.mixer.find_channel()
            if channel is None:
                log.debug("sound dropped cue=%s", cue.value)
                continue
            channel.play(self._effects[cue])
            log.debug("sound play cue=%s", cue.value)


def load_audio(levels: AudioLevels) -> AudioPlayer | None:
    """Open the mixer, load the six files once and set every volume once.

    Returns None after one WARNING when the mixer cannot start. A missing or unreadable sound file
    raises. A volume is a master percent over 100 times its own level percent over 100.
    """
    try:
        pygame.mixer.init()
    except pygame.error as err:
        log.warning("audio off: %s", err)
        return None
    pygame.mixer.set_num_channels(levels.effect_channels)
    _check_file(MUSIC_FILE)
    levels_by_cue: dict[SoundCue, float] = {
        SoundCue.HIT: levels.hit_level,
        SoundCue.GRAZE: levels.graze_level,
        SoundCue.COIN: levels.coin_level,
        SoundCue.GAME_OVER: levels.game_over_level,
        SoundCue.LEVEL_UP: levels.level_up_level,
    }
    effects: dict[SoundCue, pygame.mixer.Sound] = {}
    for cue, file in EFFECT_FILES.items():
        sound: pygame.mixer.Sound = pygame.mixer.Sound(str(_check_file(file)))
        sound.set_volume(_volume(levels.effects_master, levels_by_cue[cue]))
        effects[cue] = sound
    return AudioPlayer(_volume(levels.music_master, levels.loop_level), effects)


def _volume(master: float, level: float) -> float:
    """Return master percent times level percent as a volume, 0..1."""
    return master / 100 * (level / 100)


def _check_file(file: str) -> Path:
    """Return the path of a sound file; raise FileNotFoundError if it is missing."""
    path: Path = AUDIO_DIR / file
    if not path.is_file():
        raise FileNotFoundError(f"assets/audio/{file}: missing")
    return path
