import numpy as np


def compute_fft(
    signal: np.ndarray, sampling_rate: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the FFT of a signal and return the frequency bins and corresponding magnitude spectrum.

    Args:
        signal: Input audio signal as a NumPy array.
        sampling_rate: Sampling rate of the signal in Hz.

    Returns:
        A tuple containing:
            - frequency_bins: Frequencies in Hz corresponding to the FFT bins.
            - magnitude_spectrum: Magnitudes of the FFT components.
    """
    n = len(signal)
    fft_result = np.fft.fft(signal)
    magnitude_spectrum = np.abs(
        fft_result[: n // 2]
    )  # Keep only the positive frequencies
    frequency_bins = np.fft.fftfreq(n, d=1 / sampling_rate)[: n // 2]
    return frequency_bins, magnitude_spectrum
