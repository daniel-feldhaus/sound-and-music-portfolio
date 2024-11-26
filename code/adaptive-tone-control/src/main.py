"""This module takes in command line arguments to modify a sound file. It then saves the result, and visualizes the applied changes."""

import argparse
import librosa
import librosa.display
import soundfile as sf
from energy_analysis import dynamic_tone_control
from visualization import visualize_spectrograms


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Dynamic Tone Control with Visualization."
    )
    parser.add_argument(
        "input_file", type=str, help="Path to the input audio file (required)."
    )
    parser.add_argument(
        "--output_file",
        type=str,
        help="Path to save the modified audio file (optional).",
        default="output_audio.wav",
    )
    parser.add_argument(
        "--bands",
        type=str,
        default="low:0-300,mid:300-2000,high:2000-22050",
        help="Frequency bands in the format 'band_name:low-high,...' (default: low:0-300,mid:300-2000,high:2000-22050).",
    )
    parser.add_argument(
        "--frame_size",
        type=int,
        default=2048,
        help="Frame size for dynamic processing (default: 2048).",
    )
    parser.add_argument(
        "--hop_size",
        type=int,
        default=1024,
        help="Hop size for overlapping frames (default: 1024).",
    )
    parser.add_argument(
        "--smoothing_factor",
        type=float,
        default=0.9,
        help="Smoothing factor for dynamic gain adjustment (default: 0.9).",
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


def main():
    # Parse arguments
    args = parse_arguments()

    # Load audio file
    signal, sampling_rate = librosa.load(args.input_file, sr=None)

    # Parse bands
    bands = parse_bands(args.bands, sampling_rate)

    # Apply dynamic tone control
    modified_signal = dynamic_tone_control(
        signal,
        sampling_rate,
        bands,
        frame_size=args.frame_size,
        hop_size=args.hop_size,
        smoothing_factor=args.smoothing_factor,
    )

    # Save output file
    if args.output_file:
        sf.write(args.output_file, modified_signal, sampling_rate)

    # Visualize before/after spectrograms
    visualize_spectrograms(signal, modified_signal, sampling_rate, bands)


if __name__ == "__main__":
    main()
