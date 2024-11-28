import librosa
import numpy as np


def interpolate_signals(file_a: str, file_b: str, duration: float):
    """
    Interpolate between the end of file A and the beginning of file B.

    Args:
        file_a (str): Path to the first audio file.
        file_b (str): Path to the second audio file.
        duration (float): Duration of the overlap in seconds.

    Returns:
        tuple: Interpolated audio signal and sample rate.
    """
    # Load audio files
    y_a, sr_a = librosa.load(file_a, sr=None)
    y_b, sr_b = librosa.load(file_b, sr=None)

    # Ensure both files have the same sample rate
    if sr_a != sr_b:
        raise ValueError("Sample rates of input files must match.")
    sample_rate = sr_a

    # Calculate the number of samples for the overlap duration
    overlap_samples = int(duration * sample_rate)

    # Extract segments
    a_tail = y_a[-overlap_samples:]
    b_head = y_b[:overlap_samples]

    # Perform STFT
    stft_a = librosa.stft(a_tail)
    stft_b = librosa.stft(b_head)

    # Interpolate magnitudes and phases
    mag_a, phase_a = np.abs(stft_a), np.angle(stft_a)
    mag_b, phase_b = np.abs(stft_b), np.angle(stft_b)
    alpha = np.linspace(0, 1, mag_a.shape[1])[np.newaxis, :]
    interpolated_mag = (1 - alpha) * mag_a + alpha * mag_b
    interpolated_phase = (1 - alpha) * phase_a + alpha * phase_b
    stft_interpolated = interpolated_mag * np.exp(1j * interpolated_phase)

    # Reconstruct the interpolated signal
    interpolated_signal = librosa.istft(stft_interpolated)

    # Combine with the original signals
    combined_signal = np.concatenate(
        (y_a[:-overlap_samples], interpolated_signal, y_b[overlap_samples:])
    )

    return combined_signal, sample_rate
