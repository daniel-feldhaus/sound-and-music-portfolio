import numpy as np
import parselmouth
from parselmouth.praat import call


def extract_formants(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """
    Extract formants from a given audio signal.

    Args:
        audio (np.ndarray): Audio signal.
        sample_rate (int): Sampling rate of the audio signal.

    Returns:
        np.ndarray: Array of formant frequencies over time.
    """
    sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)
    formant = call(sound, "To Formant (burg)", 0.01, 5, 5500, 0.025, 50)
    times = np.linspace(0, len(audio) / sample_rate, len(audio))
    formant_values = []

    for i in range(5):  # Extract the first 5 formants
        formant_values.append(
            [call(formant, "Get value at time", i + 1, t, "Hertz", "Linear") for t in times]
        )

    return np.array(formant_values)


def interpolate_formants(
    audio_a: np.ndarray, audio_b: np.ndarray, combined_audio: np.ndarray, sample_rate: int
) -> np.ndarray:
    """
    Adjust the formants in combined_audio to transition between audio_a and audio_b.

    Args:
        audio_a (np.ndarray): The first audio segment.
        audio_b (np.ndarray): The second audio segment.
        combined_audio (np.ndarray): The combined audio to adjust.
        sample_rate (int): The sampling rate of the audio signals.

    Returns:
        np.ndarray: Audio with interpolated formants applied.
    """
    # Extract formants from audio_a and audio_b
    formants_a = extract_formants(audio_a, sample_rate)
    formants_b = extract_formants(audio_b, sample_rate)

    # Determine time frames in the formant data
    num_formant_frames = formants_a.shape[1]
    alpha = np.linspace(0, 1, num_formant_frames)  # Interpolation factor aligned to formant frames

    # Linearly interpolate formants
    interpolated_formants = (1 - alpha)[np.newaxis, :] * formants_a + alpha[
        np.newaxis, :
    ] * formants_b

    # Create a new spectral envelope for combined_audio
    combined_spectrum = np.fft.rfft(combined_audio)
    frequencies = np.fft.rfftfreq(len(combined_audio), 1 / sample_rate)

    # Modify spectral envelope based on interpolated formants
    modified_spectrum = np.zeros_like(combined_spectrum)

    for frame_formants in interpolated_formants.T:  # Iterate over time frames
        for f in frame_formants:  # Iterate over formants
            if not np.isnan(f) and f > 0:  # Skip invalid formants
                # Apply Gaussian bumps centered on each interpolated formant
                modified_spectrum += (
                    np.exp(-0.5 * ((frequencies - f) / 50) ** 2) * combined_spectrum
                )

    # Normalize and reconstruct the modified audio
    modified_spectrum /= np.max(np.abs(modified_spectrum)) + 1e-6
    modified_audio = np.fft.irfft(modified_spectrum)

    return modified_audio
