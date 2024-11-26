import argparse
import librosa
import librosa.display
import soundfile as sf
import numpy as np
from energy_analysis import calculate_band_energy_from_signal, apply_gain
from visualization import visualize_spectrograms


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process audio with dynamic tone control."
    )
    parser.add_argument(
        "input_file", type=str, help="Path to the input audio file (required)."
    )
    parser.add_argument(
        "--bands",
        type=str,
        default="low:0-300,mid:300-2000,high:2000-22050",
        help="Frequency bands in the format 'band_name:low-high,...' (default: low:0-300,mid:300-2000,high:2000-22050).",
    )
    parser.add_argument(
        "--output_file", type=str, help="Path to save the modified audio (optional)."
    )
    parser.add_argument(
        "--gain",
        type=str,
        help="Gain adjustments for bands in the format 'band_name:gain,...' (e.g., low:1.5,mid:1.0,high:0.8).",
    )
    return parser.parse_args()


def parse_bands(bands_arg, sampling_rate):
    """Parse the bands argument into a dictionary."""
    nyquist = sampling_rate / 2
    bands = {}
    for band_def in bands_arg.split(","):
        name, range_def = band_def.split(":")
        low, high = map(float, range_def.split("-"))
        bands[name] = (max(low, 1), min(high, nyquist - 1))
    return bands


def parse_gain(gain_arg, default_gain):
    """Parse the gain argument into a dictionary."""
    if not gain_arg:
        return default_gain
    gain = {}
    for gain_def in gain_arg.split(","):
        name, value = gain_def.split(":")
        gain[name] = float(value)
    return gain


def main():
    args = parse_arguments()

    # Load audio file
    signal, sampling_rate = librosa.load(args.input_file, sr=None)

    # Parse bands and gain arguments
    bands = parse_bands(args.bands, sampling_rate)
    initial_energy = calculate_band_energy_from_signal(signal, sampling_rate, bands)
    average_energy = np.mean(list(initial_energy.values()))
    default_gain = {
        band: average_energy / (energy + 1e-6)
        for band, energy in initial_energy.items()
    }
    gain = parse_gain(args.gain, default_gain)

    # Apply gain adjustments
    modified_signal = apply_gain(signal, gain, sampling_rate, bands)

    # Save modified audio if output file is specified
    if args.output_file:
        sf.write(args.output_file, modified_signal, sampling_rate)

    visualize_spectrograms(signal, modified_signal, sampling_rate, bands)


if __name__ == "__main__":
    main()
