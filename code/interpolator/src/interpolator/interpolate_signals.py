from typing import Tuple
import librosa
import numpy as np

from interpolator.pitch import (
    extract_pitch_contour,
    interpolate_pitch_contours,
    modify_pitch_with_world,
)
from .formants import interpolate_formants


def load_audio(file_path: str, sample_rate: int = None) -> Tuple[np.ndarray, int]:
    """
    Load an audio file.

    Args:
        file_path (str): Path to the audio file.
        sample_rate (int, optional): Desired sample rate. Defaults to None.

    Returns:
        Tuple[np.ndarray, int]: The loaded audio signal and its sample rate.
    """
    audio, sr = librosa.load(file_path, sr=sample_rate)
    return audio, sr


def interpolate_signals(
    file_a: str,
    file_b: str,
    duration: float,
    magnitude_interpolation: bool = False,
    phase_interpolation: bool = False,
    formant_interpolation: bool = False,
    pitch_interpolation: bool = False,
) -> Tuple[np.ndarray, int]:
    """
    Interpolate between the end of file A and the beginning of file B.

    Args:
        file_a (str): Path to the first audio file.
        file_b (str): Path to the second audio file.
        duration (float): Duration of the overlap in seconds.
        magnitude_interpolation (bool): Whether to perform magnitude interpolation.
        phase_interpolation (bool): Whether to perform phase interpolation.
        formant_interpolation (bool): Whether to perform formant interpolation.

    Returns:
        Tuple[np.ndarray, int]: The interpolated audio signal and the sample rate.
    """
    # Load audio files
    y_a, sr_a = load_audio(file_a)
    y_b, sr_b = load_audio(file_b)

    # Ensure both files have the same sample rate
    if sr_a != sr_b:
        raise ValueError("Sample rates of input files must match.")
    sample_rate = sr_a

    # Calculate the number of samples for the overlap duration
    overlap_samples = int(duration * sample_rate)

    # Extract segments
    a_tail = y_a[-overlap_samples:]
    b_head = y_b[:overlap_samples]

    # Initialize interpolated signal
    interpolated_signal = np.zeros_like(a_tail)

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

    if pitch_interpolation:
        print("Performing pitch interpolation...")
        # Frame parameters
        frame_length = int(0.025 * sample_rate)  # 25 ms
        hop_length = int(0.0125 * sample_rate)  # 12.5 ms
        frame_period = (hop_length / sample_rate) * 1000  # in milliseconds

        # Extract pitch contours
        f0_a = extract_pitch_contour(a_tail, sample_rate, frame_length, hop_length)
        f0_b = extract_pitch_contour(b_head, sample_rate, frame_length, hop_length)

        # Interpolate pitch contours
        f0_interpolated = interpolate_pitch_contours(f0_a, f0_b)

        # Modify pitch of the overlapping segment
        interpolated_signal = modify_pitch_with_world(
            interpolated_signal, sample_rate, f0_interpolated, frame_period
        )

    # Combine with the original signals
    combined_signal = np.concatenate(
        (y_a[:-overlap_samples], interpolated_signal, y_b[overlap_samples:])
    )

    return combined_signal, sample_rate
