"""Module for analyzing and modifying a signal's sound energy."""

import numpy as np
from scipy.signal import butter, lfilter

from fft_utils import compute_fft


def calculate_band_energy_from_signal(
    signal: np.ndarray, sampling_rate: int, bands: dict[str, tuple[float, float]]
) -> dict[str, float]:
    """
    Calculate the energy in specified frequency bands for a given signal.

    Args:
        signal: Input audio signal as a NumPy array.
        sampling_rate: Sampling rate of the signal in Hz.
        bands: A dictionary where keys are band names and values are tuples defining band ranges (low, high).

    Returns:
        A dictionary with band names as keys and their respective energy as values.
    """
    # Compute FFT
    frequency_bins, magnitude_spectrum = compute_fft(signal, sampling_rate)

    # Calculate energy in each band
    band_energy = {}
    for band_name, (low, high) in bands.items():
        band_indices = np.where((frequency_bins >= low) & (frequency_bins < high))[0]
        band_energy[band_name] = np.sum(
            magnitude_spectrum[band_indices] ** 2
        )  # Energy is sum of squares
    return band_energy


def apply_gain(
    signal: np.ndarray,
    gain: dict[str, float],
    sampling_rate: int,
    bands: dict[str, tuple[float, float]],
) -> np.ndarray:
    """
    Apply gain adjustments to the signal for each frequency band.

    Args:
        signal: Input audio signal.
        gain: Dictionary of gain values for each band.
        sampling_rate: Sampling rate of the audio signal.
        bands: Frequency bands with their ranges.

    Returns:
        Filtered signal with gain applied.
    """
    filtered_signal = np.zeros_like(signal)
    nyquist = 0.5 * sampling_rate

    for band_name, (low, high) in bands.items():
        # Adjust frequencies to valid ranges
        low = max(low, 1.0)  # Ensure low frequency is at least 1 Hz
        high = min(high, nyquist - 1.0)  # Ensure high frequency is less than Nyquist

        # Normalize frequencies
        low_cut = low / nyquist
        high_cut = high / nyquist

        # Validate the filter frequency range
        if not (0 < low_cut < high_cut < 1):
            raise ValueError(
                f"Invalid bandpass filter range for {band_name}: {low_cut}-{high_cut} (normalized)"
            )

        # Create a Butterworth bandpass filter
        b, a = butter(N=2, Wn=[low_cut, high_cut], btype="bandpass")
        band_signal = lfilter(b, a, signal)

        # Apply gain
        filtered_signal += band_signal * gain[band_name]

    return filtered_signal
