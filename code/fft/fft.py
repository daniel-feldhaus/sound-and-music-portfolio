import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import sys


def ditfft2(x: np.ndarray, N: int, s: int) -> np.ndarray:
    """
    Recursive implementation of radix-2 DIT FFT.
    Adapted from pseudocode from here: https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm

    Args:
    x (np.ndarray): Input array of complex numbers.
    N (int): Size of the DFT to compute.
    s (int): Stride, to pick every s-th element in the array.

    Returns:
    np.ndarray: The DFT of the input array x.
    """
    if N == 1:
        return np.array([x[0]])  # base case: DFT of size 1

    # DFT of the even-indexed elements
    X_even = ditfft2(x, N // 2, 2 * s)

    # DFT of the odd-indexed elements
    X_odd = ditfft2(x[s:], N // 2, 2 * s)

    # Combine the results
    X = np.zeros(N, dtype=complex)
    for k in range(N // 2):
        p = X_even[k]
        q = np.exp(-2j * np.pi * k / N) * X_odd[k]
        X[k] = p + q
        X[k + N // 2] = p - q

    return X


def audio_to_spectrogram(
    audio_data: np.ndarray, window_size: int, overlap: int, fft_func
) -> np.ndarray:
    """
    Computes a 2D spectrogram using the FFT function.

    Args:
    audio_data (np.ndarray): Input audio signal.
    window_size (int): Size of each FFT window (number of samples per window).
    overlap (int): Overlap between consecutive windows (in samples).
    fft_func (function): FFT function to use.

    Returns:
    np.ndarray: Spectrogram as a 2D array (time x frequency).
    """
    step_size = window_size - overlap
    num_windows = (len(audio_data) - window_size) // step_size + 1
    spectrogram = []

    for i in range(num_windows):
        # Extract the windowed portion of the audio signal
        start_idx = i * step_size
        end_idx = start_idx + window_size
        window_data = audio_data[start_idx:end_idx]

        # Apply FFT to the window
        fft_result = fft_func(window_data, window_size, 1)

        # Compute magnitude and add to the spectrogram
        magnitude = np.abs(
            fft_result[: window_size // 2]
        )  # Only take the positive frequencies
        spectrogram.append(magnitude)

    return np.array(spectrogram).T  # Transpose so that rows represent frequencies
