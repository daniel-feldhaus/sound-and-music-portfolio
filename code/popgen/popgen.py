import argparse
import random
import re
import wave
from typing import Dict, List, Tuple

import numpy as np
import sounddevice as sd

# 11 canonical note names.
names: List[str] = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
note_names: Dict[str, int] = {note_name: index for index, note_name in enumerate(names)}

# Turn a note name into a corresponding MIDI key number.
# Format is name with optional bracketed octave, for example
# "D" or "Eb[5]". Default is octave 4 if no octave is
# specified.
note_name_re = re.compile(r"([A-G]b?)(\[([0-8])\])?")


def parse_note(note_string: str) -> int:
    match = note_name_re.fullmatch(note_string)
    if match is None:
        raise ValueError
    note_name = match[1]
    note_name = note_name[0].upper() + note_name[1:]
    octave = 4
    if match[3] is not None:
        octave = int(match[3])
    return note_names[note_name] + 12 * octave


# Given a string representing a knob setting between 0 and
# 10 inclusive, return a linear gain value between 0 and 1
# inclusive. The input is treated as decibels, with 10 being
# 0dB and 0 being the specified `db_at_zero` decibels.
def parse_log_knob(knob_setting: str, db_at_zero: float = -40) -> float:
    value = float(knob_setting)
    if value < 0 or value > 10:
        raise ValueError
    if value < 0.1:
        return 0
    if value > 9.9:
        return 10
    return 10 ** (-db_at_zero * (value - 10) / 200)


# Given a string representing a knob setting between 0 and
# 10 inclusive, return a linear gain value between 0 and 1
# inclusive.
def parse_linear_knob(knob_setting: str) -> float:
    value = float(knob_setting)
    if value < 0 or value > 10:
        raise ValueError
    return value / 10


# Given a string representing a gain in decibels, return a
# linear gain value in the interval (0,1]. The input gain
# must be negative.
def parse_db(db_string: str) -> float:
    db_value = float(db_string)
    if db_value > 0:
        raise ValueError
    return 10 ** (db_value / 20)


ap = argparse.ArgumentParser()
ap.add_argument("--bpm", type=int, default=90)
ap.add_argument("--samplerate", type=int, default=48_000)
ap.add_argument("--root", type=parse_note, default="C[5]")
ap.add_argument("--bass-octave", type=int, default=2)
ap.add_argument("--balance", type=parse_linear_knob, default="5")
ap.add_argument("--gain", type=parse_db, default="-3")
ap.add_argument("--output")
ap.add_argument("--test", action="store_true", help=argparse.SUPPRESS)
args = ap.parse_args()

# Tempo in beats per minute.
bpm: int = args.bpm

# Audio sample rate in samples per second.
samplerate: int = args.samplerate

# Samples per beat.
beat_samples = int(np.round(samplerate / (bpm / 60)))

# Relative notes of a major scale.
major_scale = [0, 2, 4, 5, 7, 9, 11]

# Major chord scale tones — one-based.
major_chord = [1, 3, 5]


# Given a scale note with root note 0, return a key offset
# from the corresponding root MIDI key.
def note_to_key_offset(note: int) -> int:
    scale_degree: int = note % 7
    return note // 7 * 12 + major_scale[scale_degree]


# Given a position within a chord, return a scale note
# offset — zero-based.
def chord_to_note_offset(posn: int) -> int:
    chord_posn: int = posn % 3
    return posn // 3 * 7 + major_chord[chord_posn] - 1


# MIDI key where melody goes.
melody_root: int = args.root

# Bass MIDI key is below melody root.
bass_root: int = melody_root - 12 * args.bass_octave

# Root note offset for each chord in scale tones — one-based.
chord_loop = [8, 5, 6, 4]

pos = 0


def pick_notes(chord_root: int, n: int = 4) -> List[int]:
    global pos
    current_pos = pos

    notes: List[int] = []
    for _ in range(n):
        chord_note_offset = chord_to_note_offset(current_pos)
        chord_note = note_to_key_offset(chord_root + chord_note_offset)
        notes.append(chord_note)

        if random.random() > 0.5:
            current_pos = current_pos + 1
        else:
            current_pos = current_pos - 1

    pos = current_pos
    return notes

# Given a MIDI key number and an optional number of beats of
# note duration, return a sine wave for that note.
def make_note(key: int, duration_beats: int = 1) -> np.ndarray:
    frequency: float = 440 * 2 ** ((key - 69) / 12)
    sample_count: int = beat_samples * duration_beats
    cycles: float = 2 * np.pi * frequency * sample_count / samplerate
    time_points: np.ndarray = np.linspace(0, cycles, sample_count)
    return np.sin(time_points)


# Play the given sound waveform using `sounddevice`.
def play(sound: np.ndarray) -> None:
    sd.play(sound, samplerate=samplerate, blocking=True)


# Unit tests, driven by hidden `--test` argument.
if args.test:
    note_tests: List[Tuple[int, int]] = [
        (-9, -15),
        (-8, -13),
        (-7, -12),
        (-6, -10),
        (-2, -3),
        (-1, -1),
        (0, 0),
        (6, 11),
        (7, 12),
        (8, 14),
        (9, 16),
    ]

    for note_num, expected_key_offset in note_tests:
        computed_key_offset = note_to_key_offset(note_num)
        assert (
            computed_key_offset == expected_key_offset
        ), (
            f"{note_num} {expected_key_offset} {computed_key_offset}"
        )

    chord_tests: List[Tuple[int, int]] = [
        (-3, -7),
        (-2, -5),
        (-1, -3),
        (0, 0),
        (1, 2),
        (2, 4),
        (3, 7),
        (4, 9),
    ]

    for chord_pos, expected_note_offset in chord_tests:
        computed_note_offset = chord_to_note_offset(chord_pos)
        assert (
            computed_note_offset == expected_note_offset
        ), (
            f"{chord_pos} {expected_note_offset} {computed_note_offset}"
        )

    exit(0)

# Stitch together a waveform for the desired music.
sound: np.ndarray = np.array([], dtype=np.float64)
for chord_root in chord_loop:
    notes = pick_notes(chord_root - 1)
    melody = np.concatenate(
        [make_note(note_offset + melody_root) for note_offset in notes]
    )

    bass_note = note_to_key_offset(chord_root - 1)
    bass = make_note(bass_note + bass_root, duration_beats=4)

    melody_gain: float = args.balance
    bass_gain = 1 - melody_gain

    sound = np.append(sound, melody_gain * melody + bass_gain * bass)

# Save or play the generated "music".
if args.output:
    output = wave.open(args.output, "wb")
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(samplerate)
    output.setnframes(len(sound))

    data = args.gain * 32767 * sound.clip(-1, 1)
    output.writeframesraw(data.astype(np.int16))

    output.close()
else:
    play(args.gain * sound)
