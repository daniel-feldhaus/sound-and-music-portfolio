"""Create an interpolated output file based on a collection of input instructions."""

import argparse
from dataclasses import dataclass
from typing import Optional, List, Literal, Dict
from pathlib import Path
import json
import os
from itertools import pairwise
import soundfile as sf
import simpleaudio as sa
from interpolator.interpolate_signals import interpolate_signals, load_audio, AudioData
from interpolator.pitch import shift_pitch

TVowel = Literal["A", "E", "I", "O", "U"]


@dataclass
class Instruction:
    """Instruction for a single note."""

    vowel: TVowel
    # Semitone offset from middle C.
    offset: int
    # Duration of note (in ms)
    duration: int
    # Duration of interpolation between this instruction and the next (in ms)
    transition_duration: int


@dataclass
class InterpolationConfig:
    """Command line inputs."""

    instructions: List[Instruction]
    sample_dir: str
    save_path: Optional[str] = None


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
            transition_duration = None
            if idx < len(data) - 1:
                transition_duration = item["transition_duration"]
        except KeyError as e:
            raise ValueError(f"Missing field {e} in instruction at index {idx}.") from e

        if vowel not in "AEIOU":
            raise ValueError(f"Unrecognized vowel: {vowel}")

        # Validate offset
        if not isinstance(offset, int):
            raise ValueError(f"Offset must be an integer in instruction at index {idx}.")

        # Validate duration
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError(f"Duration must be a positive integer in instruction at index {idx}.")

        instruction = Instruction(
            vowel=vowel, offset=offset, duration=duration, transition_duration=transition_duration
        )
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
    save_path = Path(args.out) if args.out else None
    sample_dir = Path(args.sounds)
    if not os.path.isdir(sample_dir):
        raise FileNotFoundError(f"Sample directory does not exist: {sample_dir}")

    config = InterpolationConfig(
        instructions=parse_instruction_file(args.instruction_file),
        save_path=save_path,
        sample_dir=sample_dir,
    )
    return config


def get_sample_dict(instructions: List[Instruction], sample_dir) -> Dict[str, AudioData]:
    """Load a dictionary of sound samples for each unique vowel given in the instructions"""
    unique_vowels = set(instruction.vowel for instruction in instructions)
    sample_dict = {}
    for vowel in unique_vowels:
        sample_dict[vowel] = load_audio(os.path.join(sample_dir, f"{vowel}.wav"))
    return sample_dict


def adjust_audio_duration(audio: AudioData, duration: float) -> AudioData:
    """Shorten an audio by clipping, or lengthen through interpolated repetition."""
    start_duration = len(audio.data) / audio.sample_rate
    target_length = int(audio.sample_rate * duration)
    if start_duration < duration:
        overlap_duration = (len(audio.data) / audio.sample_rate) / 2
        while len(audio.data) < target_length:
            audio = interpolate_signals(audio, audio, overlap_duration)
    clipped_audio = AudioData(audio.data[:target_length], audio.sample_rate)
    return clipped_audio


def process_audio(audio: AudioData, instruction: Instruction) -> AudioData:
    """Process an audio clip based on its associated instruction."""
    audio = adjust_audio_duration(audio, instruction.duration / 1000)
    audio = shift_pitch(audio, instruction.offset)
    return audio


def generate_from_instructions(instructions: List[Instruction], sample_dir: Path):
    """Generate an audio file from instructions."""
    sample_dict = get_sample_dict(instructions, sample_dir)
    audio = process_audio(sample_dict[instructions[0].vowel], instructions[0])
    for instruction_a, instruction_b in pairwise(instructions):
        audio_b = process_audio(sample_dict[instruction_b.vowel], instruction_b)
        audio = interpolate_signals(
            audio, audio_b, duration=instruction_a.transition_duration / 1000
        )
    return audio


def main():
    """Connect two sound files by interpolating between their ends."""
    args = parse_arguments()

    output_audio = generate_from_instructions(args.instructions, args.sample_dir)

    # Save or play the result
    if args.save_path:
        sf.write(args.save_path, output_audio.data, output_audio.sample_rate)
        print(f"Output saved to {args.save_path}")
    else:
        # Play the signal
        audio = sa.play_buffer(
            (output_audio.data * 32767).astype("int16"), 1, 2, output_audio.sample_rate
        )
        audio.wait_done()


if __name__ == "__main__":
    main()
