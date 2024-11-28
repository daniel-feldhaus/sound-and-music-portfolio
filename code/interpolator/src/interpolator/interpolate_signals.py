from typing import Tuple, List
import librosa
import numpy as np
import parselmouth
from parselmouth.praat import call
from scipy.interpolate import interp1d


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


def extract_formants(audio: np.ndarray, sample_rate: int, duration: float) -> np.ndarray:
    """
    Extract formants from a given audio signal.

    Args:
        audio (np.ndarray): Audio signal.
        sample_rate (int): Sampling rate of the audio signal.
        duration (float): Duration for formant extraction.

    Returns:
        np.ndarray: Array of formant frequencies.
    """
    sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)
    formant = call(sound, "To Formant (burg)", 0.01, 5, 5500, 0.025, 50)
    times = np.linspace(0, duration, len(audio))
    formant_values: List[List[float]] = []

    for i in range(5):  # Extract the first 5 formants
        formant_values.append(
            [
                call(
                    formant, "Get value at time", i + 1, t, "Hertz", "Linear"
                )  # Add Interpolation argument
                for t in times
            ]
        )

    return np.array(formant_values)


def interpolate_formants(
    formants_a: np.ndarray, formants_b: np.ndarray, alpha: np.ndarray
) -> np.ndarray:
    """
    Interpolate between two sets of formants.

    Args:
        formants_a (np.ndarray): Formants of the first signal.
        formants_b (np.ndarray): Formants of the second signal.
        alpha (np.ndarray): Interpolation factor.

    Returns:
        np.ndarray: Interpolated formants.
    """
    return (1 - alpha) * formants_a + alpha * formants_b


def spectral_interpolation(
    a_tail: np.ndarray, b_head: np.ndarray, overlap_samples: int
) -> np.ndarray:
    """
    Perform spectral interpolation between two audio segments.

    Args:
        a_tail (np.ndarray): Tail segment of the first audio file.
        b_head (np.ndarray): Head segment of the second audio file.
        overlap_samples (int): Number of overlapping samples.

    Returns:
        np.ndarray: Reconstructed audio signal from the interpolated spectrum.
    """
    # Ensure input segments match the overlap_samples length
    a_tail = a_tail[-overlap_samples:]
    b_head = b_head[:overlap_samples]

    # STFT on both segments
    stft_a = librosa.stft(a_tail)
    stft_b = librosa.stft(b_head)

    # Extract magnitude and phase
    mag_a, phase_a = np.abs(stft_a), np.angle(stft_a)
    mag_b, phase_b = np.abs(stft_b), np.angle(stft_b)

    # Interpolate magnitudes and phases
    alpha = np.linspace(0, 1, mag_a.shape[1])[np.newaxis, :]
    interpolated_mag = (1 - alpha) * mag_a + alpha * mag_b
    interpolated_phase = (1 - alpha) * phase_a + alpha * phase_b
    stft_interpolated = interpolated_mag * np.exp(1j * interpolated_phase)

    # Reconstruct the interpolated signal
    return librosa.istft(stft_interpolated)


def apply_interpolated_formants(
    audio: np.ndarray, formants: np.ndarray, sample_rate: int
) -> np.ndarray:
    """
    Modify the signal spectrum to match the interpolated formants.

    Args:
        audio (np.ndarray): Input audio signal.
        formants (np.ndarray): Interpolated formant frequencies.
        sample_rate (int): Sampling rate of the audio signal.

    Returns:
        np.ndarray: Signal modified to match interpolated formants.
    """
    # Perform STFT
    stft_audio = librosa.stft(audio)
    magnitude, phase = np.abs(stft_audio), np.angle(stft_audio)

    # Resample formants to match the STFT time resolution
    num_stft_frames = magnitude.shape[1]
    original_time = np.linspace(0, 1, formants.shape[1])
    target_time = np.linspace(0, 1, num_stft_frames)
    resampled_formants = np.zeros((formants.shape[0], num_stft_frames))

    for i in range(formants.shape[0]):  # Resample each formant
        interp_func = interp1d(original_time, formants[i], kind="linear", fill_value="extrapolate")
        resampled_formants[i] = interp_func(target_time)

    # Create a spectral envelope using the resampled formants
    frequencies = np.linspace(0, sample_rate // 2, magnitude.shape[0])
    envelope = np.zeros_like(magnitude)

    for i, frame_formants in enumerate(resampled_formants.T):  # Iterate over time frames
        for f in frame_formants:  # Iterate over formants
            if not np.isnan(f) and f > 0:  # Skip invalid formants
                # Add a Gaussian bump for each formant
                envelope[:, i] += np.exp(-0.5 * ((frequencies - f) / 50) ** 2)

    # Normalize envelope
    envelope = envelope / np.max(envelope, axis=0, keepdims=True)

    # Apply envelope to the magnitude spectrum
    modified_magnitude = magnitude * envelope

    # Reconstruct the signal
    modified_stft = modified_magnitude * np.exp(1j * phase)
    modified_audio = librosa.istft(modified_stft)

    return modified_audio


def interpolate_signals(
    file_a: str,
    file_b: str,
    duration: float,
    magnitude_interpolation: bool = False,
    phase_interpolation: bool = False,
    formant_interpolation: bool = False,
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
        formants_a = extract_formants(a_tail, sample_rate, duration)
        formants_b = extract_formants(b_head, sample_rate, duration)
        alpha = np.linspace(0, 1, formants_a.shape[1])
        interpolated_formants = interpolate_formants(formants_a, formants_b, alpha)
        interpolated_signal = apply_interpolated_formants(
            a_tail, interpolated_formants, sample_rate
        )

    # Combine with the original signals
    combined_signal = np.concatenate(
        (y_a[:-overlap_samples], interpolated_signal, y_b[overlap_samples:])
    )

    return combined_signal, sample_rate
