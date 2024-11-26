"""Module for analyzing a signal's sound energy profile."""

import numpy as np

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
