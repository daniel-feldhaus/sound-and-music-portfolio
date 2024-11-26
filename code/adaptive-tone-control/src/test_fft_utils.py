"""Tests for the fft_util module"""

import numpy as np
from fft_utils import compute_fft


def test_fft_single_tone():
    """Test FFT computation for a single sine wave."""
    frequency = 440  # Hz
    duration = 1.0  # seconds
    sampling_rate = 44100  # Hz
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    sine_wave = np.sin(2 * np.pi * frequency * t)

    freq_bins, magnitude_spectrum = compute_fft(sine_wave, sampling_rate)

    # Check if the peak frequency matches the sine wave frequency
    peak_frequency = freq_bins[np.argmax(magnitude_spectrum)]
    assert np.isclose(
        peak_frequency, frequency, atol=1
    ), f"Expected {frequency}, got {peak_frequency}"


def test_fft_noise():
    """Test FFT computation for white noise."""
    duration = 1.0  # seconds
    sampling_rate = 44100  # Hz
    noise = np.random.normal(0, 1, int(sampling_rate * duration))

    _, magnitude_spectrum = compute_fft(noise, sampling_rate)

    # Check if the magnitude spectrum length matches half the signal length
    expected_length = len(noise) // 2
    assert (
        len(magnitude_spectrum) == expected_length
    ), f"Expected {expected_length}, got {len(magnitude_spectrum)}"
