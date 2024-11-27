"""Pop Music Generator

This script puts out four bars in the "Axis Progression" chord loop,
with a melody, bass line, and rhythm track.

Author: Bart Massey, 2024
"""

import random
import wave
from typing import List, Tuple, Literal

import numpy as np
import sounddevice as sd

from parsing import parse_args


# Relative notes of a major scale.
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

# Major chord scale tones — one-based.
MAJOR_CHORD = [1, 3, 5]


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


def make_kick(
    samplerate: int,
    duration: float = 0.1,
    attack_time: float = 0.005,
    release_time: float = 0.05,
) -> np.ndarray:
    """Generate a kick drum sound using white noise and an envelope.

    Args:
        samplerate (int): The audio sample rate.
        duration (float): Total duration of the kick sound in seconds.
        attack_time (float): Duration of the attack phase in seconds.
        release_time (float): Duration of the release phase in seconds.

    Returns:
        np.ndarray: The generated kick drum waveform.
    """
    # Calculate the number of samples for the kick
    sample_count = int(samplerate * duration)

    # Generate white noise
    noise = np.random.normal(0, 1, sample_count)

    # Create an envelope using the existing make_envelope function
    envelope = make_envelope(
        samplerate=samplerate,
        sample_count=sample_count,
        attack_time=attack_time,
        release_time=release_time,
    )

    # Apply the envelope to the noise to shape the kick
    kick = noise * envelope

    return kick

def make_snare(
    samplerate: int,
    duration: float = 0.2,        # Duration of the snare in seconds
    attack_time: float = 0.005,   # Attack time in seconds
    release_time: float = 0.1     # Release time in seconds
) -> np.ndarray:
    """Generate a snare drum sound using white noise and an envelope.

    Args:
        samplerate (int): The audio sample rate.
        duration (float): Total duration of the snare sound in seconds.
        attack_time (float): Duration of the attack phase in seconds.
        release_time (float): Duration of the release phase in seconds.

    Returns:
        np.ndarray: The generated snare drum waveform.
    """
    # Calculate the number of samples for the snare
    sample_count = int(samplerate * duration)

    # Generate white noise
    noise = np.random.normal(0, 1, sample_count)

    # Create an envelope using the existing make_envelope function
    envelope = make_envelope(
        samplerate=samplerate,
        sample_count=sample_count,
        attack_time=attack_time,
        release_time=release_time,
    )

    # Apply the envelope to the noise to shape the snare
    snare = noise * envelope

    return snare



def make_rhythm(
    pattern: str,
    beat_samples: int,
    samplerate: int,
    rhythm_volume: float,
) -> np.ndarray:
    """Generate a rhythm track based on the specified pattern using kick drum samples.

    'k' represents a kick drum, and '_' represents silence.

    Args:
        pattern (str): Rhythm pattern string (e.g., "k___k___k___k___").
        beat_samples (int): Number of samples per beat.
        samplerate (int): Audio sample rate.
        rhythm_volume (float): Volume level for the rhythm track (0.0 to 1.0).

    Returns:
        np.ndarray: The generated rhythm track waveform.
    """
    rhythm = np.zeros(beat_samples * len(pattern))

    for i, char in enumerate(pattern):
        # Calculate the insertion point in the rhythm array
        start_idx = i * beat_samples
        if char.lower() == "k":
            kick = make_kick(
                samplerate=samplerate,
                duration=0.1,
                attack_time=0.005,
                release_time=0.05
            )
            end_idx = min(start_idx + len(kick), len(rhythm))

            rhythm[start_idx:end_idx] += (kick * rhythm_volume)[: end_idx - start_idx]
        elif char.lower() == "s":
            snare = make_snare(
                samplerate,
                duration=0.2,
                attack_time=0.005,
                release_time=0.1
            )
            end_idx = min(start_idx + len(snare), len(rhythm))
            rhythm[start_idx:end_idx] += (snare * rhythm_volume)[: end_idx - start_idx]
        elif char != "_":
            raise ValueError(f"Unexpected rythm character '{char}'")
    # Normalize to prevent clipping
    max_val = np.max(np.abs(rhythm))
    if max_val > 1:
        rhythm = rhythm / max_val

    return rhythm


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


def main():
    """Stitch together a waveform for the desired music."""
    args = parse_args()
    if args.test:
        test()

        return
    # Samples per beat.
    beat_samples = int(np.round(args.samplerate / (args.bpm / 60)))
    rhythm_beat_samples = int(np.round(args.samplerate / (args.rhythm_bpm / 60)))
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

    # Generate rhythm track
    rhythm = make_rhythm(
        pattern=args.rhythm_pattern,
        beat_samples=rhythm_beat_samples,
        samplerate=args.samplerate,
        rhythm_volume=args.rhythm_volume,
    )

    # Loop the rhythm to match the sound length
    if len(rhythm) < len(sound):
        # Calculate the number of times to repeat the rhythm pattern
        num_repeats = int(np.ceil(len(sound) / len(rhythm)))
        # Repeat the rhythm pattern
        rhythm = np.tile(rhythm, num_repeats)
    # Trim the rhythm array to match the sound length exactly
    rhythm = rhythm[:len(sound)]

    # Mix rhythm with existing sound
    combined_sound = sound + rhythm

    # Normalize the combined sound to prevent clipping
    max_val = np.max(np.abs(combined_sound))
    if max_val > 1:
        combined_sound = combined_sound / max_val

    # Save or play the generated "music".
    if args.output:
        try:
            output = wave.open(args.output, "wb")
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(args.samplerate)
            # Convert float array to int16
            data = (combined_sound * args.gain * 32767).astype(np.int16)
            output.writeframes(data.tobytes())

            output.close()
        except Exception as e:
            raise RuntimeError(f"Failed to write to output file '{args.output}'") from e
    else:
        play(combined_sound * args.gain, args.samplerate)


if __name__ == "__main__":
    main()
