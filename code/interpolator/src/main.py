import argparse
import soundfile as sf
import simpleaudio as sa
from interpolator.interpolate_signals import interpolate_signals


def main():
    """Connect two sound files by interpolating between their ends."""
    parser = argparse.ArgumentParser(description="Interpolate between two audio files.")
    parser.add_argument("file_a", help="Path to the first audio file")
    parser.add_argument("file_b", help="Path to the second audio file")
    parser.add_argument("-s", "--save", help="Path to save the output file", default=None)
    parser.add_argument(
        "-d", "--duration", type=float, help="Overlap duration in seconds", default=1
    )
    parser.add_argument(
        "-m", "--magnitude", action="store_true", help="Enable magnitude interpolation"
    )
    parser.add_argument("-p", "--phase", action="store_true", help="Enable phase interpolation")
    parser.add_argument("-f", "--formant", action="store_true", help="Enable formant interpolation")
    args = parser.parse_args()

    # Interpolate signals
    output_signal, sample_rate = interpolate_signals(
        args.file_a,
        args.file_b,
        args.duration,
        magnitude_interpolation=args.magnitude,
        phase_interpolation=args.phase,
        formant_interpolation=args.formant,
        pitch_interpolation=True,
    )

    # Save or play the result
    if args.save:
        sf.write(args.save, output_signal, sample_rate)
        print(f"Output saved to {args.save}")
    else:
        # Play the signal
        audio = sa.play_buffer((output_signal * 32767).astype("int16"), 1, 2, sample_rate)
        audio.wait_done()


if __name__ == "__main__":
    main()
