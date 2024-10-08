import argparse
from typing import Tuple
import soundfile as sf
import numpy as np
from pathlib import Path


def generate_sine_wave(
    frequency: float,
    sample_rate: int,
    duration: float,
    amplitude: float,
    clip_percent: float = 0.25,
) -> np.ndarray:
    """
    Generate a sine wave as a numpy array.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)

    clip_amplitude = amplitude * (1 - clip_percent)
    wave[wave > clip_amplitude] = clip_amplitude
    wave[wave < -clip_amplitude] = -clip_amplitude
    return wave


def save_to_wav(filepath: Path, samples: np.ndarray, sample_rate: int):
    """Save the given samples as a WAV file."""
    if filepath.suffix != ".wav":
        raise ValueError(f"Save file must have type 'wav': {filepath}")

    # Write the samples directly to the file
    sf.write(str(filepath), samples, sample_rate, format="WAV")


def main():
    """
    Takes command-line arguments and generates a sine wave.
    """
    parser = argparse.ArgumentParser(
        description="Generate a sine wave and output the numpy array."
    )
    parser.add_argument(
        "frequency", type=float, help="Frequency of the sine wave in Hz."
    )
    parser.add_argument(
        "--sample_rate",
        type=int,
        default=48000,
        help="Sample rate in Hz.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1,
        help="Duration of the sine wave in seconds.",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=8192,
        help="Amplitude of the sine wave (default is 8192).",
    )

    args = parser.parse_args()

    # Generate the sine wave using the provided arguments
    sine_wave = generate_sine_wave(
        args.frequency, args.sample_rate, args.duration, args.amplitude
    )

    save_to_wav(Path("sine.wav"), sine_wave, args.sample_rate)

    clipped_sine_wave = generate_sine_wave(
        args.frequency,
        args.sample_rate,
        args.duration,
        args.amplitude,
        clip_percent=0.25,
    )

    save_to_wav(Path("clipped.wav"), clipped_sine_wave, args.sample_rate)


if __name__ == "__main__":
    main()
