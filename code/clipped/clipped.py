import argparse
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
        default=1.0,
        help="Amplitude of the sine wave (default is 1.0).",
    )

    args = parser.parse_args()

    # Generate the sine wave using the provided arguments
    sine_wave = generate_sine_wave(
        args.frequency, args.sample_rate, args.duration, args.amplitude
    )

    # Output the sine wave array
    print(sine_wave)


if __name__ == "__main__":
    main()
