"""
Pop Music Generator
Bart Massey 2024

This script generates four bars of music in the "Axis Progression" chord loop,
with a melody and bass line. The generated music can be played or saved to a file.
"""

import argparse
import random
import re
import wave
from typing import List

import numpy as np
import sounddevice as sd

# Canonical note names
NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NOTE_NAME_TO_INDEX = {name: i for i, name in enumerate(NOTE_NAMES)}

# Regular expression for parsing note names
NOTE_NAME_REGEX = re.compile(r"([A-G]b?)(\[([0-8])\])?")


def parse_note(note: str) -> int:
    """
    Convert a note name to a corresponding MIDI key number.

    Args:
        note: Note name in the format "D", "Eb[5]", etc.

    Returns:
        MIDI key number corresponding to the note.
    """
    match = NOTE_NAME_REGEX.fullmatch(note)
    if match is None:
        raise ValueError(f"Invalid note format: {note}")
    name = match[1][0].upper() + match[1][1:]
    octave = int(match[3]) if match[3] else 4
    return NOTE_NAME_TO_INDEX[name] + 12 * octave


def parse_log_knob(knob_value: str, db_at_zero: int = -40) -> float:
    """
    Convert a knob setting (0-10) to a linear gain value based on decibels.

    Args:
        knob_value: Knob value as a string (0-10).
        db_at_zero: Gain in decibels at 0.

    Returns:
        Linear gain value (0-1).
    """
    value = float(knob_value)
    if not 0 <= value <= 10:
        raise ValueError("Knob value must be between 0 and 10.")
    if value < 0.1:
        return 0
    if value > 9.9:
        return 1
    return 10 ** (-db_at_zero * (value - 10) / 200)


def parse_linear_knob(knob_value: str) -> float:
    """
    Convert a knob setting (0-10) to a linear gain value (0-1).

    Args:
        knob_value: Knob value as a string (0-10).

    Returns:
        Linear gain value (0-1).
    """
    value = float(knob_value)
    if not 0 <= value <= 11:
        raise ValueError("Knob value must be between 0 and 10.")
    return value / 10


def parse_db(decibels: str) -> float:
    """
    Convert a decibel value to a linear gain value.

    Args:
        decibels: Gain in decibels (must be negative).

    Returns:
        Linear gain value (0-1].
    """
    value = float(decibels)
    if value > 0:
        raise ValueError("Decibel values must be negative.")
    return 10 ** (value / 20)


def note_to_key_offset(scale_note: int) -> int:
    """
    Convert a scale note to a key offset based on the major scale.

    Args:
        scale_note: Scale note index (relative to root).

    Returns:
        MIDI key offset from the root note.
    """
    major_scale = [0, 2, 4, 5, 7, 9, 11]
    degree = scale_note % 7
    return scale_note // 7 * 12 + major_scale[degree]


def chord_to_note_offset(position: int) -> int:
    """
    Convert a chord position to a scale note offset.

    Args:
        position: Position within the chord.

    Returns:
        Scale note offset.
    """
    major_chord = [1, 3, 5]
    chord_position = position % 3
    return position // 3 * 7 + major_chord[chord_position] - 1


def pick_notes(chord_root: int, count: int = 4) -> List[int]:
    """
    Generate a sequence of notes from a chord.

    Args:
        chord_root: Root note of the chord (scale tone).
        count: Number of notes to generate.

    Returns:
        List of note offsets from the root.
    """
    global position
    notes = []
    for _ in range(count):
        offset = chord_to_note_offset(position)
        notes.append(note_to_key_offset(chord_root + offset))
        position += 1 if random.random() > 0.5 else -1
    return notes


def make_note(key: int, duration: int = 1) -> np.ndarray:
    """
    Generate a sine wave for a note.

    Args:
        key: MIDI key number.
        duration: Duration of the note in beats.

    Returns:
        Sine wave representing the note.
    """
    frequency = 440 * 2 ** ((key - 69) / 12)
    total_samples = beat_samples * duration
    cycles = 2 * np.pi * frequency * total_samples / samplerate
    t = np.linspace(0, cycles, total_samples)
    return np.sin(t)


def play(sound: np.ndarray) -> None:
    """
    Play a sound waveform.

    Args:
        sound: Waveform as a NumPy array.
    """
    sd.play(sound, samplerate=samplerate, blocking=True)


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Pop Music Generator")
parser.add_argument("--bpm", type=int, default=90)
parser.add_argument("--samplerate", type=int, default=48000)
parser.add_argument("--root", type=parse_note, default="C[5]")
parser.add_argument("--bass-octave", type=int, default=2)
parser.add_argument("--balance", type=parse_linear_knob, default="5")
parser.add_argument("--gain", type=parse_db, default="-3")
parser.add_argument("--output", help="Output file path")
parser.add_argument("--test", action="store_true", help="Run unit tests")
args = parser.parse_args()

# Parameters
bpm = args.bpm
samplerate = args.samplerate
beat_samples = int(np.round(samplerate / (bpm / 60)))
melody_root = args.root
bass_root = melody_root - 12 * args.bass_octave
chord_loop = [8, 5, 6, 4]
position = 0

# Testing mode
if args.test:
    # Add test cases here if needed
    exit(0)

# Generate music
sound = np.array([], dtype=np.float64)
for chord in chord_loop:
    melody_notes = pick_notes(chord - 1)
    melody = np.concatenate([make_note(note + melody_root) for note in melody_notes])
    bass = make_note(note_to_key_offset(chord - 1) + bass_root, n=4)

    melody_gain = args.balance
    bass_gain = 1 - melody_gain
    sound = np.append(sound, melody_gain * melody + bass_gain * bass)

# Output music
if args.output:
    with wave.open(args.output, "wb") as output_file:
        output_file.setnchannels(1)
        output_file.setsampwidth(2)
        output_file.setframerate(samplerate)
        output_file.setnframes(len(sound))
        data = args.gain * 32767 * np.clip(sound, -1, 1)
        output_file.writeframesraw(data.astype(np.int16))
else:
    play(args.gain * sound)
