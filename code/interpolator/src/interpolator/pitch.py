"""Module for functions related to modifying pitch."""

import numpy as np
import librosa
import pyworld as pw
from interpolator.audio_data import AudioData

MIDDLE_C_HZ = 261


def shift_pitch(
    audio: AudioData,
    semitones: float = 0.0,
    frame_period: float = 5.0,
) -> AudioData:
    """
    Shift the pitch of an input signal. By default, assume the input is at a constant
    middle C and shift it by a given number of semitones.
    """
    f0 = MIDDLE_C_HZ * (2.0 ** (semitones / 12.0))
    data = audio.data.astype(np.float64)
    _f0, time_axis = pw.harvest(
        data,
        audio.sample_rate,
        f0_floor=50.0,
        f0_ceil=800.0,
        frame_period=frame_period,
    )
    sp = pw.cheaptrick(data, _f0, time_axis, audio.sample_rate)
    ap = pw.d4c(data, _f0, time_axis, audio.sample_rate)

    f0_shifted = np.full_like(_f0, f0)

    synthesized_audio = pw.synthesize(
        f0_shifted, sp, ap, audio.sample_rate, frame_period=frame_period
    )

    # Normalize the synthesized audio to prevent clipping
    max_val = np.max(np.abs(synthesized_audio))
    if max_val > 1.0:
        synthesized_audio = synthesized_audio / max_val

    # Truncate to match the original length
    synthesized_audio = synthesized_audio[: len(data)].astype(np.float32)

    return AudioData(synthesized_audio, audio.sample_rate)


def extract_pitch_contour(
    audio: np.ndarray,
    sample_rate: int,
    frame_length: int,
    hop_length: int,
    fmin: float = 50.0,
    fmax: float = 800.0,
) -> np.ndarray:
    """
    Extract the pitch contour from an audio signal using librosa's pyin method.

    Args:
        audio (np.ndarray): Audio signal.
        sample_rate (int): Sampling rate of the audio signal.
        frame_length (int): Length of each frame in samples.
        hop_length (int): Number of samples between frames.
        fmin (float): Minimum frequency to consider (Hz).
        fmax (float): Maximum frequency to consider (Hz).

    Returns:
        np.ndarray: Pitch contour (fundamental frequency over time).
    """
    f0, _voiced_flag, _ = librosa.pyin(
        audio,
        sr=sample_rate,
        fmin=fmin,
        fmax=fmax,
        frame_length=frame_length,
        hop_length=hop_length,
    )
    return f0


def interpolate_pitch_contours(f0_a: np.ndarray, f0_b: np.ndarray) -> np.ndarray:
    """
    Interpolate between two pitch contours to create a smooth transition.

    Args:
        f0_a (np.ndarray): Pitch contour of the first audio segment.
        f0_b (np.ndarray): Pitch contour of the second audio segment.

    Returns:
        np.ndarray: Interpolated pitch contour.
    """
    # Ensure both pitch contours are the same length
    min_length = min(len(f0_a), len(f0_b))
    f0_a = f0_a[:min_length]
    f0_b = f0_b[:min_length]

    # Create an alpha factor for interpolation
    alpha = np.linspace(0, 1, min_length)

    # Initialize interpolated pitch contour
    f0_interpolated = (1 - alpha) * f0_a + alpha * f0_b

    return f0_interpolated


def modify_pitch_with_world(
    audio: np.ndarray, sample_rate: int, f0_interpolated: np.ndarray, frame_period: float
) -> np.ndarray:
    """
    Modify the pitch of an audio signal using the WORLD vocoder.

    Args:
        audio (np.ndarray): Audio signal to modify.
        sample_rate (int): Sampling rate of the audio signal.
        f0_interpolated (np.ndarray): Interpolated pitch contour.
        frame_period (float): Frame period in milliseconds.

    Returns:
        np.ndarray: Audio signal with modified pitch.
    """
    # Step 1: Analysis
    print("Analyzing audio with WORLD vocoder...")
    _f0, time_axis = pw.harvest(
        audio.astype(np.float64),
        sample_rate,
        f0_floor=50.0,
        f0_ceil=800.0,
        frame_period=frame_period,
    )
    audio = audio.astype(np.float64)
    sp = pw.cheaptrick(audio, _f0, time_axis, sample_rate)
    ap = pw.d4c(audio, _f0, time_axis, sample_rate)

    # Ensure f0_interpolated matches the length of _f0
    min_length = min(len(_f0), len(f0_interpolated))
    _f0 = _f0[:min_length]
    sp = sp[:min_length]
    ap = ap[:min_length]
    f0_interpolated = f0_interpolated[:min_length]

    # Handle NaNs in f0_interpolated
    f0_modified = np.where(np.isnan(f0_interpolated), 0.0, f0_interpolated)

    # Step 3: Synthesis
    print("Synthesizing audio with modified pitch...")
    synthesized_audio = pw.synthesize(f0_modified, sp, ap, sample_rate, frame_period=frame_period)

    return synthesized_audio.astype(np.float32)
