"""Tests for the pitch module."""

import numpy as np
from src.interpolator.pitch import shift_pitch, MIDDLE_C_HZ
from src.interpolator.interpolate_signals import AudioData


def test_shift_pitch():
    """
    Test the shift_pitch function with synthetic input.
    """
    sr = 16000
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Create a test tone at middle C
    test_tone = np.sin(2.0 * np.pi * MIDDLE_C_HZ * t).astype(np.float32)
    test_audio = AudioData(test_tone, sr)
    # Shift up by 12 semitones (one octave)
    shifted_audio = shift_pitch(test_audio, semitones=12.0)
    assert shifted_audio.shape == test_tone.shape

    # Shift down by 12 semitones
    shifted_audio = shift_pitch(test_audio, semitones=-12.0)
    assert shifted_audio.shape == test_tone.shape
