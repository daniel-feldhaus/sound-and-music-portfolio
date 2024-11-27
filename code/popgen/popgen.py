"""Pop Music Generator

This script puts out four bars in the "Axis Progression" chord loop,
with a melody and bass line.

Author: Bart Massey, 2024
"""

import argparse
import random
import re
import wave
from typing import Dict, List, Tuple, Literal
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

# 11 canonical note names.
names: List[str] = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
note_names: Dict[str, int] = {note_name: index for index, note_name in enumerate(names)}

# Relative notes of a major scale.
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

# Major chord scale tones — one-based.
MAJOR_CHORD = [1, 3, 5]

# Regular expression for parsing note names.
note_name_re = re.compile(r"([A-G]b?)(\[([0-8])\])?")


def parse_note(note_string: str) -> int:
    """Turn a note name into a corresponding MIDI key number.

    Format is name with optional bracketed octave, for example
    "D" or "Eb[5]". Default is octave 4 if no octave is
    specified.
    """
    match = note_name_re.fullmatch(note_string)
    if match is None:
        raise ValueError(f"Invalid note format: '{note_string}'") from None
    note_name = match[1]
    note_name = note_name[0].upper() + note_name[1:]
    octave = 4
    if match[3] is not None:
        octave = int(match[3])
    return note_names[note_name] + 12 * octave


def parse_log_knob(knob_setting: str, db_at_zero: float = -40) -> float:
    """Given a string representing a knob setting between 0 and 10 inclusive,
    return a linear gain value between 0 and 1 inclusive.

    The input is treated as decibels, with 10 being 0dB and 0 being the
    specified `db_at_zero` decibels.
    """
    try:
        value = float(knob_setting)
    except ValueError as e:
        raise ValueError(f"Knob setting must be a number between 0 and 10: '{knob_setting}'") from e

    if value < 0 or value > 10:
        raise ValueError(f"Knob setting must be between 0 and 10: received {value}") from None
    if value < 0.1:
        return 0.0
    if value > 9.9:
        return 10.0
    return 10 ** (-db_at_zero * (value - 10) / 200)


def parse_linear_knob(knob_setting: str) -> float:
    """Given a string representing a knob setting between 0 and 10 inclusive,
    return a linear gain value between 0 and 1 inclusive.
    """
    try:
        value = float(knob_setting)
    except ValueError as e:
        raise ValueError(f"Knob setting must be a number between 0 and 10: '{knob_setting}'") from e

    if value < 0 or value > 10:
        raise ValueError(f"Knob setting must be between 0 and 10: received {value}") from None
    return value / 10


def parse_db(db_string: str) -> float:
    """Given a string representing a gain in decibels, return a
    linear gain value in the interval (0,1].

    The input gain must be negative.
    """
    try:
        db_value = float(db_string)
    except ValueError as e:
        raise ValueError(f"Gain must be a negative number in decibels: '{db_string}'") from e

    if db_value > 0:
        raise ValueError(f"Gain must be negative in decibels: received {db_value}") from None
    return 10 ** (db_value / 20)


def parse_chord_loop(chord_loop_str: str) -> List[int]:
    """Parse a comma-separated string of chord roots into a list of integers."""
    if not chord_loop_str:
        raise ValueError("Chord loop string cannot be empty.")

    try:
        # Split the string by commas, strip whitespace, and convert to integers
        chord_loop = [int(chord.strip()) for chord in chord_loop_str.split(",") if chord.strip()]
    except ValueError as e:
        raise ValueError(
            f"Invalid chord loop format: '{chord_loop_str}'. "
            "Ensure it is a comma-separated list of integers, e.g., '8,5,6,4'."
        ) from e

    if not chord_loop:
        raise ValueError("Chord loop cannot be empty after parsing.")

    return chord_loop


def note_to_key_offset(note: int) -> int:
    """Given a scale note with root note 0, return a key offset
    from the corresponding root MIDI key.
    """
    scale_degree: int = note % 7
    return note // 7 * 12 + MAJOR_SCALE[scale_degree]


def chord_to_note_offset(posn: int) -> int:
    """Given a position within a chord, return a scale note offset — zero-based."""
    chord_posn: int = posn % 3
    return posn // 3 * 7 + MAJOR_CHORD[chord_posn] - 1


def pick_notes(chord_root: int, n: int = 4, max_offset: int = 5) -> List[int]:
    """Pick a sequence of notes for the melody line based on the chord root.

    The sequence length is determined by `n`.
    """
    current_pos = 0

    notes: List[int] = []
    for _ in range(n):
        chord_note_offset = chord_to_note_offset(current_pos)
        chord_note = note_to_key_offset(chord_root + chord_note_offset)
        notes.append(chord_note)

        # The probability of moving upwards approaches 1 as the offset approaches -max_offset.
        # Conversely, the probability approaches 0 as the offset approaches max_offset.
        p_up = (current_pos + max_offset) / (2 * max_offset)

        if random.random() > p_up:
            current_pos += 1
        else:
            current_pos -= 1

    return notes


def make_wave(
    key: int,
    sample_count: int,
    samplerate: int,
    waveform: Literal["sine", "sawtooth", "square"],
):
    """Generate a signal with a given wave shape."""
    frequency: float = 440 * 2 ** ((key - 69) / 12)
    cycles: float = 2 * np.pi * frequency * sample_count / samplerate
    time_points: np.ndarray = np.linspace(0, cycles, sample_count, endpoint=False)

    match waveform:
        case "sine":
            return np.sin(time_points)
        case "sawtooth":
            # Generate sawtooth waveform
            # Sawtooth wave ranges from -1 to 1 over each period
            return 2 * (time_points / (2 * np.pi) - np.floor(0.5 + time_points / (2 * np.pi)))
        case "square":
            # Generate square waveform using the sign of a sine wave
            return np.sign(np.sin(time_points))
    raise ValueError(f"Unsupported waveform type: '{waveform}'.")

def make_envelope(
    samplerate: int,
    sample_count: int,
    attack_time: float = 0.01,
    release_time: float = 0.01,
) -> np.ndarray:
    """Generate an envelope to use for tapering audio amplitude."""
    # Calculate the number of samples for attack and release
    attack_samples = int(samplerate * attack_time)
    release_samples = int(samplerate * release_time)

    # Ensure that attack and release do not exceed the total sample count
    if attack_samples + release_samples > sample_count:
        attack_samples = release_samples = sample_count // 2

    # Initialize the envelope with ones (sustain level)
    envelope = np.ones(sample_count)

    # Create the attack ramp (linear increase from 0 to 1)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Create the release ramp (linear decrease from 1 to 0)
    if release_samples > 0:
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)

    return envelope

def make_note(
    key: int,
    beat_samples: int,
    samplerate: int,
    duration_beats: int = 1,
    waveform: Literal["sine", "sawtooth", "square"] = "sine",
) -> np.ndarray:
    """Given a MIDI key number and an optional number of beats of
    note duration, return the specified waveform for that note.
    """
    sample_count: int = beat_samples * duration_beats

    wave_signal = make_wave(key, sample_count, samplerate, waveform)
    envelope = make_envelope(samplerate, sample_count)
    return wave_signal * envelope



def play(sound: np.ndarray, samplerate: int) -> None:
    """Play the given sound waveform using `sounddevice`."""
    sd.play(sound, samplerate=samplerate, blocking=True)


def test():
    """Unit tests, driven by hidden `--test` argument."""
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

@dataclass
class Args:
    """Command line arguments."""
    bpm: int
    samplerate: int
    root: int
    bass_octave: int
    balance: float
    gain: float
    output: str
    test: bool
    chord_loop: List[int]
    waveform: str
    max_offset: int


def parse_args() -> Args:
    """Parse command line arguments into a typed object."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=int, default=90)
    ap.add_argument("--samplerate", type=int, default=48_000)
    ap.add_argument("--root", type=parse_note, default="C[5]")
    ap.add_argument("--bass-octave", type=int, default=2)
    ap.add_argument("--balance", type=parse_linear_knob, default="5")
    ap.add_argument("--gain", type=parse_db, default="-3")
    ap.add_argument("--output")
    ap.add_argument("--test", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument(
        "--chord-loop",
        type=parse_chord_loop,
        default="8,5,6,4",
        help="Comma-separated list of chord roots in scale tones (one-based).",
    )

    ap.add_argument(
        "--waveform",
        type=str,
        choices=["sine", "sawtooth", "square"],
        default="sine",
        help="Type of waveform to use for note generation. Choices: 'sine', 'sawtooth', `square`.",
    )
    ap.add_argument("--max-offset", type=int, default=6)

    parsed_args = ap.parse_args()
    args = Args(
        bpm=parsed_args.bpm,
        samplerate=parsed_args.samplerate,
        root=parsed_args.root,
        bass_octave=parsed_args.bass_octave,
        balance=parsed_args.balance,
        gain=parsed_args.gain,
        output=parsed_args.output,
        test=parsed_args.test,
        chord_loop=parsed_args.chord_loop,
        waveform=parsed_args.waveform,
        max_offset=parsed_args.max_offset
    )
    return args


def main():
    """Stitch together a waveform for the desired music."""
    args = parse_args()
    if args.test:
        test()
        return
    # Samples per beat.
    beat_samples = int(np.round(args.samplerate / (args.bpm / 60)))
    # MIDI key where melody goes.
    melody_root: int = args.root
    # Bass MIDI key is below melody root.
    bass_root: int = melody_root - 12 * args.bass_octave

    sound: np.ndarray = np.array([], dtype=np.float64)
    for chord_root in args.chord_loop:
        notes = pick_notes(chord_root - 1, max_offset=args.max_offset)
        melody = np.concatenate(
            [
                make_note(
                    note_offset + melody_root,
                    beat_samples,
                    args.samplerate,
                    waveform=args.waveform,
                )
                for note_offset in notes
            ]
        )

        bass_note = note_to_key_offset(chord_root - 1)
        bass = make_note(
            bass_note + bass_root,
            beat_samples,
            args.samplerate,
            duration_beats=4,
            waveform=args.waveform,
        )

        melody_gain: float = args.balance
        bass_gain = 1 - melody_gain

        sound = np.append(sound, melody_gain * melody + bass_gain * bass)

    # Save or play the generated "music".
    if args.output:
        try:
            output = wave.open(args.output, "wb")
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(args.samplerate)
            output.setnframes(len(sound))

            data = args.gain * 32767 * sound.clip(-1, 1)
            output.writeframesraw(data.astype(np.int16))

            output.close()
        except Exception as e:
            raise RuntimeError(f"Failed to write to output file '{args.output}'") from e
    else:
        play(args.gain * sound, args.samplerate)


if __name__ == "__main__":
    main()
