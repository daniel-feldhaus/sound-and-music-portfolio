import argparse
import json
import os
import numpy as np
import soundfile as sf
import librosa

from typing import Tuple, List

# Assume these exist and work as in the original code:
# from interpolator.pitch import extract_pitch_contour, interpolate_pitch_contours, modify_pitch_with_world
# from interpolator.formants import interpolate_formants

# If these imports are unavailable, you'll need to implement or provide them.
from interpolator.pitch import (
    extract_pitch_contour,
    interpolate_pitch_contours,
    modify_pitch_with_world,
)
from interpolator.formants import interpolate_formants

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_SOUNDS_DIR = os.path.join(BASE_DIR, "../demo_sounds")

VOWEL_FILES = {"a": "aaa.wav", "e": "eee.wav", "i": "iii.wav", "o": "ooo.wav", "u": "uuu.wav"}

MIDDLE_C = 261.63  # Hz


def load_vowel(vowel: str) -> Tuple[np.ndarray, int]:
    if vowel not in VOWEL_FILES:
        raise ValueError(f"Unknown vowel: {vowel}")
    path = os.path.join(DEMO_SOUNDS_DIR, VOWEL_FILES[vowel])
    audio, sr = librosa.load(path, sr=None)
    return audio, sr


def pitch_shift_audio(audio: np.ndarray, sr: int, target_pitch: float) -> np.ndarray:
    semitones = 12 * np.log2(target_pitch / MIDDLE_C)
    shifted = librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=semitones)
    return shifted


def get_duration_in_samples(length: float, sr: int) -> int:
    return int(length * sr)


def create_single_vowel_segment(vowel: str, pitch: float, length: float) -> Tuple[np.ndarray, int]:
    audio, sr = load_vowel(vowel)
    max_length = len(audio) / sr
    if length > max_length:
        raise ValueError(
            f"Requested length {length}s is longer than available vowel clip {max_length}s."
        )
    shifted = pitch_shift_audio(audio, sr, pitch)
    seg_samples = get_duration_in_samples(length, sr)
    segment = shifted[:seg_samples]
    return segment, sr


def interpolate_arrays(
    array_a: np.ndarray,
    array_b: np.ndarray,
    sr: int,
    magnitude_interpolation: bool = True,
    phase_interpolation: bool = True,
    formant_interpolation: bool = True,
    pitch_interpolation: bool = True,
) -> np.ndarray:
    """
    Interpolate between array_a and array_b with given interpolation options.
    This mirrors the logic from the initial interpolate_signals function, but directly on arrays.
    We assume array_a and array_b are the same length.
    """

    # Ensure arrays are same length
    if len(array_a) != len(array_b):
        raise ValueError("Arrays must be of equal length for interpolation.")
    overlap_samples = len(array_a)

    # Start with spectral interpolation if magnitude or phase requested
    interpolated_signal = None
    if magnitude_interpolation or phase_interpolation:
        stft_a = librosa.stft(array_a)
        stft_b = librosa.stft(array_b)
        mag_a, phase_a = np.abs(stft_a), np.angle(stft_a)
        mag_b, phase_b = np.abs(stft_b), np.angle(stft_b)

        # Linear interpolation in time for each frame
        alpha = np.linspace(0, 1, mag_a.shape[1])[np.newaxis, :]

        if magnitude_interpolation:
            interpolated_mag = (1 - alpha) * mag_a + alpha * mag_b
        else:
            interpolated_mag = mag_a

        if phase_interpolation:
            interpolated_phase = (1 - alpha) * phase_a + alpha * phase_b
        else:
            interpolated_phase = phase_a

        stft_interpolated = interpolated_mag * np.exp(1j * interpolated_phase)
        interpolated_signal = librosa.istft(stft_interpolated)
    else:
        # If no spectral interpolation is requested, just crossfade linearly
        alpha = np.linspace(0, 1, overlap_samples)
        interpolated_signal = (1 - alpha) * array_a + alpha * array_b

    # Formant interpolation
    if formant_interpolation:
        # interpolate_formants expects original arrays plus the current interpolated signal
        # We call it similar to how we did in original code:
        interpolated_signal = interpolate_formants(array_a, array_b, interpolated_signal, sr)

    # Pitch interpolation
    if pitch_interpolation:
        # Similar approach as in original code
        frame_length = int(0.025 * sr)  # 25 ms
        hop_length = int(0.0125 * sr)  # 12.5 ms
        frame_period = (hop_length / sr) * 1000.0

        f0_a = extract_pitch_contour(array_a, sr, frame_length, hop_length)
        f0_b = extract_pitch_contour(array_b, sr, frame_length, hop_length)
        f0_interpolated = interpolate_pitch_contours(f0_a, f0_b)
        interpolated_signal = modify_pitch_with_world(
            interpolated_signal, sr, f0_interpolated, frame_period
        )

    return interpolated_signal


def create_transition_segment(
    start_vowel: str, end_vowel: str, pitches: List[float], length: float
) -> Tuple[np.ndarray, int]:
    if len(pitches) != 2:
        raise ValueError("Transition requires exactly two pitches.")
    v1, sr1 = load_vowel(start_vowel)
    v2, sr2 = load_vowel(end_vowel)
    if sr1 != sr2:
        raise ValueError("Sample rates differ between vowel files.")
    sr = sr1

    max_length_v1 = len(v1) / sr
    max_length_v2 = len(v2) / sr

    if length > max_length_v1 or length > max_length_v2:
        raise ValueError(f"Requested length {length}s is longer than available vowel clips.")

    # Pitch shift both vowels to their respective target pitches
    v1_shifted = pitch_shift_audio(v1, sr, pitches[0])
    v2_shifted = pitch_shift_audio(v2, sr, pitches[1])

    seg_samples = get_duration_in_samples(length, sr)
    v1_segment = v1_shifted[-seg_samples:]
    v2_segment = v2_shifted[:seg_samples]

    # Use all interpolations previously available
    # magnitude, phase, formant, pitch interpolation
    transition = interpolate_arrays(
        v1_segment,
        v2_segment,
        sr,
        magnitude_interpolation=True,
        phase_interpolation=True,
        formant_interpolation=True,
        pitch_interpolation=True,
    )

    return transition, sr


def main():
    parser = argparse.ArgumentParser(description="Produce audio output from instructions.")
    parser.add_argument("instructions_file", help="Path to the instructions JSON file.")
    parser.add_argument("-o", "--output", default="output.wav", help="Output file name.")
    args = parser.parse_args()

    with open(args.instructions_file, "r") as f:
        instructions = json.load(f)

    final_segments = []
    sr = None

    for inst in instructions:
        if "vowel" in inst and "transition" not in inst:
            vowel = inst["vowel"]
            pitch = inst["pitch"]
            length = inst["length"]
            segment, sr_current = create_single_vowel_segment(vowel, pitch, length)
            if sr is None:
                sr = sr_current
            elif sr != sr_current:
                raise ValueError("Sample rate mismatch encountered.")
            final_segments.append(segment)

        elif "transition" in inst:
            transition_str = inst["transition"]
            if len(transition_str) != 2:
                raise ValueError("transition should be two letters, e.g. 'ae'.")

            start_vowel = transition_str[0]
            end_vowel = transition_str[1]
            pitches = inst["pitch"]
            length = inst["length"]
            transition_seg, sr_current = create_transition_segment(
                start_vowel, end_vowel, pitches, length
            )
            if sr is None:
                sr = sr_current
            elif sr != sr_current:
                raise ValueError("Sample rate mismatch encountered.")
            final_segments.append(transition_seg)
        else:
            raise ValueError("Instruction must have either a 'vowel' or a 'transition'.")

    if not final_segments:
        raise ValueError("No segments produced.")

    final_audio = np.concatenate(final_segments)
    sf.write(args.output, final_audio, sr)
    print(f"Output saved to {args.output}")


if __name__ == "__main__":
    main()
