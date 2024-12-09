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
    crossfade_duration: float = 0.05,
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
    crossfade_samples = int(crossfade_duration * sample_rate)
    # Extract segments
    a_tail = audio_a.data[-overlap_samples:].copy()
    b_head = audio_b.data[:overlap_samples].copy()

    # Initialize interpolated signal
    interpolated_signal = np.zeros_like(a_tail)

    if pitch_interpolation and instruction_a.offset != instruction_b.offset:
        freq_a = offset_to_frequency(instruction_a.offset)
        freq_b = offset_to_frequency(instruction_b.offset)

        hop_length = int(0.0005 * sample_rate)  # 0.5 ms
        frame_period = (hop_length / sample_rate) * 1000  # in milliseconds
        # print(f"Interpolating frequency between {freq_a:.0f}Hz and {freq_b:.0f}Hz")
        # plot_waveform(a_tail, sample_rate, "A tail before.")
        a_tail = modify_pitch_with_world(
            audio_a.data[-overlap_samples - 200 :].copy(),
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
        # plot_waveform(a_tail, sample_rate, "A tail after.")
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
    else:
        # If no phase or mag interpolation, just do a hard cutoff.
        interpolated_signal = np.concatenate(
            [a_tail[: overlap_samples // 2], b_head[overlap_samples // 2 :]]
        )

    # Perform formant interpolation
    if formant_interpolation:
        interpolated_signal = interpolate_formants(a_tail, b_head, interpolated_signal, sample_rate)

    # Apply crossfades between segments
    pre_interpolated = audio_a.data[:-overlap_samples]
    post_interpolated = audio_b.data[overlap_samples:]

    # Apply crossfade between pre_interpolated and interpolated_signal
    pre_crossfade = pre_interpolated[-crossfade_samples:]
    interpolated_start = interpolated_signal[:crossfade_samples]
    crossfade_in = np.linspace(0, 1, crossfade_samples)
    pre_crossfaded = (1 - crossfade_in) * pre_crossfade + crossfade_in * interpolated_start

    # Apply crossfade between interpolated_signal and post_interpolated
    interpolated_end = interpolated_signal[-crossfade_samples:]
    post_crossfade = post_interpolated[:crossfade_samples]
    crossfade_out = np.linspace(1, 0, crossfade_samples)
    post_crossfaded = (1 - crossfade_out) * interpolated_end + crossfade_out * post_crossfade
    # Combine all segments with crossfades
    combined_signal = np.concatenate(
        [
            pre_interpolated[:-crossfade_samples],  # Pre-crossfade segment
            pre_crossfaded,  # Pre-to-interpolated crossfade
            interpolated_signal[crossfade_samples:-crossfade_samples],  # Main interpolated region
            post_crossfaded,  # Interpolated-to-post crossfade
            post_interpolated[crossfade_samples:],  # Post-crossfade segment
        ]
    )

    # filtered_combined_signal = remove_quiet_chunks(combined_signal, 0.01, 0.03 * sample_rate)
    return AudioData(combined_signal, sample_rate)
