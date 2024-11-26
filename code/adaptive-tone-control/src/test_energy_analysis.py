"""Tests of the energy_analysis module."""

import numpy as np
from energy_analysis import calculate_band_energy_from_signal


def test_calculate_band_energy_sine_wave():
    """Test energy calculation for a sine wave in the low band."""
    frequency = 100  # Hz (within the low band)
    duration = 1.0  # seconds
    sampling_rate = 44100  # Hz
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    sine_wave = np.sin(2 * np.pi * frequency * t)

    bands = {
        "low": (0, 300),
        "mid": (300, 2000),
        "high": (2000, sampling_rate / 2),
    }

    energy = calculate_band_energy_from_signal(sine_wave, sampling_rate, bands)

    # Check that the energy is concentrated in the low band
    assert (
        energy["low"] > energy["mid"] and energy["low"] > energy["high"]
    ), f"Expected low band energy to dominate, got {energy}"


def test_calculate_band_energy_white_noise():
    """Test energy distribution for white noise."""
    duration = 1.0  # seconds
    sampling_rate = 44100  # Hz
    noise = np.random.normal(0, 1, int(sampling_rate * duration))

    bands = {
        "low": (0, 300),
        "mid": (300, 2000),
        "high": (2000, sampling_rate / 2),
    }

    energy = calculate_band_energy_from_signal(noise, sampling_rate, bands)

    for band_name, band_energy in energy.items():
        assert band_energy > 0, f"Energy in band '{band_name}' should be greater than 0"
