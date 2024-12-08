"""Create an interpolated output file based on a collection of input instructions."""

import argparse
from dataclasses import dataclass
from typing import Optional, List, Literal
from pathlib import Path
import json
import soundfile as sf
import simpleaudio as sa
from interpolator.interpolate_signals import interpolate_signals

TVowel = Literal["A", "E", "I", "O", "U"]


@dataclass
class Instruction:
    """Instruction for a single note."""

    vowel: TVowel
    # Semitone offset from middle C.
    offset: int
    # Duration of note.
    duration: int


@dataclass
class InterpolationConfig:
    """Command line inputs."""

    instructions: List[Instruction]
    sample_dir: str
    save: Optional[str] = None


def parse_instruction_file(file_path: str) -> List[Instruction]:
    """
    Parse the contents of a JSON file into a list of Instruction objects.

    Args:
        file_path (str): Path to the JSON instruction file.

    Returns:
        List[Instruction]: A list of Instruction dataclass instances.

    Raises:
        ValueError: If the JSON structure is invalid or required fields are missing.
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if path.suffix.lower() != ".json":
        raise ValueError(f"Instruction file {path} is not a JSON file.")

    if not path.is_file():
        raise FileNotFoundError(f"Instruction file {path} does not exist.")

    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error decoding JSON: {e.msg}", e.doc, e.pos)

    if not isinstance(data, list):
        raise ValueError("JSON instruction file must contain a list of instructions.")

    instructions = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Instruction at index {idx} is not a JSON object.")

        # Extract and validate fields
        try:
            vowel = item["vowel"].upper()
            offset = item["offset"]
            duration = item["duration"]
        except KeyError as e:
            raise ValueError(f"Missing field {e} in instruction at index {idx}.") from e

        if vowel not in "AEIOU":
            raise ValueError(f"Unrecognized vowel: ${vowel}")

        # Validate offset
        if not isinstance(offset, int):
            raise ValueError(f"Offset must be an integer in instruction at index {idx}.")

        # Validate duration
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError(f"Duration must be a positive integer in instruction at index {idx}.")

        instruction = Instruction(vowel=vowel, offset=offset, duration=duration)
        instructions.append(instruction)

    return instructions


def get_default_sound_dir() -> str:
    """Get the default sound directory (<project directory>/demo_sounds/)"""
    return (Path(__file__).parent / ".." / "demo_sounds").resolve()


def parse_arguments() -> InterpolationConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interpolate between two audio files.")
    parser.add_argument(
        "instruction_file", help="File generation instructions, in JSON format.", type=str
    )
    parser.add_argument("-o", "--out", help="Path to save the output file.", default=None)
    parser.add_argument(
        "-s", "--sounds", help="Sound sample directory.", default=get_default_sound_dir()
    )

    args = parser.parse_args()
    config = InterpolationConfig(
        instructions=parse_instruction_file(args.instruction_file),
        save=args.out,
        sample_dir=args.sounds,
    )
    return config


def main():
    """Connect two sound files by interpolating between their ends."""
    args = parse_arguments()
    file_a = "demo_sounds/" + args.instructions[0].vowel + ".wav"
    file_b = "demo_sounds/" + args.instructions[1].vowel + ".wav"
    # Interpolate signals
    output_signal, sample_rate = interpolate_signals(
        file_a,
        file_b,
        0.5,
        magnitude_interpolation=True,
        phase_interpolation=True,
        formant_interpolation=True,
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
