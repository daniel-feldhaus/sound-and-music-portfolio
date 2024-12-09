"""Module for functions related to modifying pitch."""

import numpy as np
import librosa
import pyworld as pw
from interpolator.audio_data import AudioData

MIDDLE_C_HZ = 261


def shift_pitch(audio: AudioData, semitones: float) -> AudioData:
    """
    Shift the pitch of an input signal uniformly by a given number of semitones using librosa.

    Args:
        audio (AudioData): The input audio signal and its sample rate.
        semitones (float): The number of semitones to shift (positive for upward, negative for downward).

    Returns:
        AudioData: The pitch-shifted audio signal.
    """
    # Use librosa to shift pitch
    shifted_signal = librosa.effects.pitch_shift(
        audio.data, sr=audio.sample_rate, n_steps=semitones
    )

    return AudioData(shifted_signal, audio.sample_rate)


def modify_pitch_with_world(
    audio: np.ndarray,
    sample_rate: int,
    source_freq: float,
    target_start_freq: float,
    target_end_freq: float,
    frame_period: float,
) -> np.ndarray:
    """
    Modify the pitch of a sustained audio signal using the WORLD vocoder with interpolated scaling factors.

    Args:
        audio (np.ndarray): Audio signal to modify.
        sample_rate (int): Sampling rate of the audio signal.
        source_freq (float): Original frequency of the input audio (freq_a or freq_b).
        target_start_freq (float): Starting frequency for pitch modification.
        target_end_freq (float): Ending frequency for pitch modification.
        frame_period (float): Frame period in milliseconds.

    Returns:
        np.ndarray: Audio signal with modified pitch.
    """
    # Step 1: Analysis
    print("Analyzing audio with WORLD vocoder...")
    _f0, time_axis = pw.harvest(
        audio.astype(np.float64),
        sample_rate,
        f0_floor=50,
        f0_ceil=800,
        frame_period=frame_period,
    )
    sp = pw.cheaptrick(audio.astype(np.float64), _f0, time_axis, sample_rate)
    ap = pw.d4c(audio.astype(np.float64), _f0, time_axis, sample_rate)

    # Step 2: Compute Scaling Factors
    num_frames = len(_f0)

    # Handle cases where source_freq is zero or invalid
    if source_freq <= 0:
        raise ValueError("source_freq must be a positive number.")

    # Compute scaling factors from start to end
    scaling_factors = np.linspace(
        target_start_freq / source_freq, target_end_freq / source_freq, num=num_frames
    )

    # Apply scaling factors to the original f0
    f0_modified = _f0 * scaling_factors

    # Ensure that f0_modified does not exceed WORLD's f0 floor and ceil
    f0_modified = np.clip(f0_modified, 50, 800)

    # Replace NaNs and infinities with zeros (unvoiced)
    f0_modified = np.where(np.isfinite(f0_modified), f0_modified, 0.0)

    # Step 3: Synthesis
    print("Synthesizing audio with modified pitch...")
    synthesized_audio = pw.synthesize(f0_modified, sp, ap, sample_rate, frame_period=frame_period)

    return synthesized_audio.astype(np.float32)
