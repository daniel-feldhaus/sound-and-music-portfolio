"""Module for interpolating between audio signals."""

from typing import Tuple
import librosa
import numpy as np
from interpolator.audio_data import AudioData

from interpolator.pitch import (
    modify_pitch_with_world,
)
from .formants import interpolate_formants


def load_audio(file_path: str, sample_rate: int = None) -> AudioData:
    """
    Load an audio file.

    Args:
        file_path (str): Path to the audio file.
        sample_rate (int, optional): Desired sample rate. Defaults to None.

    Returns:
        Tuple[np.ndarray, int]: The loaded audio signal and its sample rate.
    """
    data, sample_rate = librosa.load(file_path, sr=sample_rate)
    return AudioData(data, sample_rate)


def offset_to_frequency(semitones: float, origin: float = 261) -> float:
    """Calculate the frequency from a semitone offset"""
    return origin * (2 ** (semitones / 12.0))


def interpolate_signals(
    audio_a: AudioData,
    audio_b: AudioData,
    duration: float,
    instruction_a=None,
    instruction_b=None,
    magnitude_interpolation: bool = True,
    phase_interpolation: bool = True,
    formant_interpolation: bool = True,
    pitch_interpolation: bool = True,
) -> Tuple[np.ndarray, int]:
    """
    Interpolate between the end of audio A and the beginning of audio B.

    Args:
        audio_a (AudioData): First audio data
        audio_b (AudioData): Second audio data
        duration (float): Duration of the overlap in seconds.
        magnitude_interpolation (bool): Whether to perform magnitude interpolation.
        phase_interpolation (bool): Whether to perform phase interpolation.
        formant_interpolation (bool): Whether to perform formant interpolation.
        pitch_interpolation (bool): Whether to perform pitch interpolation.

    Returns:
        AudioData: The interpolated audio signal and the sample rate.
    """
    # Ensure both files have the same sample rate
    if audio_a.sample_rate != audio_b.sample_rate:
        raise ValueError("Sample rates of input files must match.")
    sample_rate = audio_a.sample_rate

    # Calculate the number of samples for the overlap duration
    overlap_samples = int(duration * sample_rate)

    # Extract segments
    a_tail = audio_a.data[-overlap_samples:].copy()
    b_head = audio_b.data[:overlap_samples].copy()

    # Initialize interpolated signal
    interpolated_signal = np.zeros_like(a_tail)

    if pitch_interpolation and instruction_a.offset != instruction_b.offset:
        freq_a = offset_to_frequency(instruction_a.offset)
        freq_b = offset_to_frequency(instruction_b.offset)

        hop_length = int(0.0125 * sample_rate)  # 12.5 ms
        frame_period = (hop_length / sample_rate) * 1000  # in milliseconds
        print(f"Interpolating frequency between {freq_a:.0f}Hz and {freq_b:.0f}Hz")

        a_tail = modify_pitch_with_world(
            a_tail,
            sample_rate,
            source_freq=freq_a,
            target_start_freq=freq_a,
            target_end_freq=freq_b,
            frame_period=frame_period,
        )
        b_head = modify_pitch_with_world(
            b_head,
            sample_rate,
            source_freq=freq_b,
            target_start_freq=freq_a,
            target_end_freq=freq_b,
            frame_period=frame_period,
        )
    # Perform spectral interpolation (magnitude and phase)
    if magnitude_interpolation or phase_interpolation:
        stft_a = librosa.stft(a_tail)
        stft_b = librosa.stft(b_head)
        mag_a, phase_a = np.abs(stft_a), np.angle(stft_a)
        mag_b, phase_b = np.abs(stft_b), np.angle(stft_b)

        # Interpolate magnitude
        if magnitude_interpolation:
            alpha = np.linspace(0, 1, mag_a.shape[1])[np.newaxis, :]
            interpolated_mag = (1 - alpha) * mag_a + alpha * mag_b
        else:
            interpolated_mag = mag_a

        # Interpolate phase
        if phase_interpolation:
            alpha = np.linspace(0, 1, phase_a.shape[1])[np.newaxis, :]
            interpolated_phase = (1 - alpha) * phase_a + alpha * phase_b
        else:
            interpolated_phase = phase_a

        # Combine magnitude and phase
        stft_interpolated = interpolated_mag * np.exp(1j * interpolated_phase)
        interpolated_signal = librosa.istft(stft_interpolated)

    # Perform formant interpolation
    if formant_interpolation:
        interpolated_signal = interpolate_formants(a_tail, b_head, interpolated_signal, sample_rate)

    # Combine with the original signals
    combined_signal = np.concatenate(
        (
            audio_a.data[:-overlap_samples],
            interpolated_signal,
            audio_b.data[overlap_samples:],
        )
    )

    return AudioData(combined_signal, sample_rate)
