import numpy as np
import librosa
import soundfile as sf


def generate_sine_wave(
    frequency: float, duration: float, sampling_rate: int
) -> np.ndarray:
    """
    Generate a sine wave signal.

    Args:
        frequency: Frequency of the sine wave in Hz.
        duration: Duration of the signal in seconds.
        sampling_rate: Sampling rate in Hz.

    Returns:
        A NumPy array representing the sine wave.
    """
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)


def generate_square_wave(
    frequency: float, duration: float, sampling_rate: int
) -> np.ndarray:
    """
    Generate a square wave signal.

    Args:
        frequency: Frequency of the square wave in Hz.
        duration: Duration of the signal in seconds.
        sampling_rate: Sampling rate in Hz.

    Returns:
        A NumPy array representing the square wave.
    """
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    return np.sign(np.sin(2 * np.pi * frequency * t))


def generate_noise(duration: float, sampling_rate: int) -> np.ndarray:
    """
    Generate white noise.

    Args:
        duration: Duration of the signal in seconds.
        sampling_rate: Sampling rate in Hz.

    Returns:
        A NumPy array representing the noise signal.
    """
    return np.random.normal(0, 1, int(sampling_rate * duration))


def load_audio_file(
    filepath: str, sampling_rate: int = 44100
) -> tuple[np.ndarray, int]:
    """
    Load an audio file.

    Args:
        filepath: Path to the audio file.
        sampling_rate: Desired sampling rate in Hz.

    Returns:
        A tuple of the audio signal as a NumPy array and the sampling rate.
    """
    signal, sr = librosa.load(filepath, sr=sampling_rate)
    return signal, sr


def save_audio_file(filepath: str, signal: np.ndarray, sampling_rate: int) -> None:
    """
    Save an audio signal to a file.

    Args:
        filepath: Path to save the audio file.
        signal: Audio signal as a NumPy array.
        sampling_rate: Sampling rate in Hz.
    """
    sf.write(filepath, signal, sampling_rate, subtype="PCM_16")
