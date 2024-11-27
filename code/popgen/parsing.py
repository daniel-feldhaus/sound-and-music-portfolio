"""Functions for parsing command line inputs."""
import argparse
from dataclasses import dataclass
import re
from typing import Dict, List

# Regular expression for parsing note names.
note_name_re = re.compile(r"([A-G]b?)(\[([0-8])\])?")
# 11 canonical note names.
names: List[str] = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
note_names: Dict[str, int] = {note_name: index for index, note_name in enumerate(names)}


@dataclass
class Args:
    """Command line arguments."""
    bpm: int
    rhythm_bpm: int
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
    rhythm_pattern: str
    rhythm_volume: float

def parse_args() -> Args:
    """Parse command line arguments into a typed object."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=int, default=90)
    ap.add_argument("--rhythm-bpm", default=None)
    ap.add_argument("--samplerate", type=int, default=48000)
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
        help="Type of waveform to use for note generation. Choices: 'sine', 'sawtooth', 'square'.",
    )
    ap.add_argument(
        "--max-offset",
        type=int,
        default=5,
        help="Maximum offset for melody note picking to constrain the melody range.",
    )
    ap.add_argument(
        "--rhythm-pattern",
        type=str,
        default="k___k___k___k___",
        help='Rhythm pattern using "k" for kick and "_" for silence, e.g., "k__k__k__k__".',
    )
    ap.add_argument(
        "--rhythm-volume",
        type=float,
        default=0.3,
        help="Volume level for the rhythm track (0.0 to 1.0).",
    )

    parsed_args = ap.parse_args()
    args = Args(
        bpm=parsed_args.bpm,
        rhythm_bpm=int(parsed_args.rhythm_bpm) if parsed_args.rhythm_bpm else parsed_args.bpm,
        samplerate=parsed_args.samplerate,
        root=parsed_args.root,
        bass_octave=parsed_args.bass_octave,
        balance=parsed_args.balance,
        gain=parsed_args.gain,
        output=parsed_args.output,
        test=parsed_args.test,
        chord_loop=parsed_args.chord_loop,
        waveform=parsed_args.waveform,
        max_offset=parsed_args.max_offset,
        rhythm_pattern=parsed_args.rhythm_pattern,
        rhythm_volume=parsed_args.rhythm_volume,
    )
    return args

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
