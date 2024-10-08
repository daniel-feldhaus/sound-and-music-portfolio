import soundfile
import numpy as np


def generate_sine_wave(
    frequency: float, sample_rate: int, duration: float, amplitude: float = 1.0
) -> np.ndarray:
    """
    Generate a sine wave as a numpy array.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave


print(generate_sine_wave(100, 10, 1, 1))
