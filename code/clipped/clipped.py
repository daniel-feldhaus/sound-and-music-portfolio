from typing import Optional
import numpy as np
import soundfile as sf
import sounddevice as sd
from pathlib import Path


def generate_sine_wave(
    frequency: float,
    sample_rate: int,
    duration: float,
    amplitude: int,
    clip_amplitude: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a sine wave as a numpy array.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)

    if clip_amplitude != None:
        clip_amplitude = np.int16(clip_amplitude)
        wave[wave > clip_amplitude] = clip_amplitude
        wave[wave < -clip_amplitude] = -clip_amplitude

    wave = np.int16(wave)

    return wave


def save_to_wav(filepath: Path, samples: np.ndarray, sample_rate: int):
    """Save the given samples as a WAV file."""
    if filepath.suffix != ".wav":
        raise ValueError(f"Save file must have type 'wav': {filepath}")

    sf.write(str(filepath), samples, sample_rate, format="WAV", subtype="PCM_16")


def play(samples: np.ndarray, sample_rate: int):
    # Convert int16 samples to float32 in the range [-1.0, 1.0]
    float_samples = samples.astype(np.float32) / np.iinfo(np.int16).max

    # Play the sound
    sd.play(float_samples, sample_rate)
    sd.wait()  # Wait until playback finishes


def main():
    """
    Takes command-line arguments and generates a sine wave, then saves it to a WAV file.
    """
    FREQUENCY = 440
    SAMPLE_RATE = 48000
    DURATION = 1
    # Generate the sine wave using the provided arguments
    sine_wave = generate_sine_wave(FREQUENCY, SAMPLE_RATE, DURATION, amplitude=8192)
    clipped_sine_wave = generate_sine_wave(
        FREQUENCY, SAMPLE_RATE, DURATION, amplitude=16384, clip_amplitude=8192
    )

    save_to_wav(Path("sine.wav"), sine_wave, SAMPLE_RATE)

    save_to_wav(Path("clipped.wav"), clipped_sine_wave, SAMPLE_RATE)

    play(sine_wave, SAMPLE_RATE)


if __name__ == "__main__":
    main()
