# Final Project: Interpolator
# Description
Interpolator is a library designed to interpolate, through various means, between two continuous sounds. The idea started out as a more fully-fledged "mouth simulator", but I ended up finding the interpolation aspect of that interesting enough to warrant its own project.

The idea of this project was to identify and explore various aspects of sound that could be modified and interpolated between. The end goal was to generate audio that sounds like that interpolation in real life - for example, the way a human would transition between an "aaa" sound and an "ooo" sound.

This project was super educational, but my success was relatively limited. As you'll hear, the results definitely do not sound human, and there's a fair amount of popping and artifacts that I have yet to resolve.

## Installation
```bash
# Install requirements
pip install -r requirements.txt
# If developing, unstall developer requirements
pip install -r requirements-dev.txt

pip install -e .
```

## Execution
Interpolator generates an output sound using an instruction file and a directory of sample audio files. An example instruction file can be found at [instructions.json](./instructions.json), and the default sample directory is [./demo_sounds](./demo_sounds/`).

usage: main.py [-h] [-o OUT] [-s SOUNDS] instruction_file

### Positional Arguments:
* instruction_file      File generation instructions, in JSON format.

### Options:
* -h, --help: Show a help message and exit
* -o OUT, --out OUT: Path to save the output file. If no output file is given, the result is played immediately after generation.
* -s SOUNDS, --sounds SOUNDS: Directory of the sounds to use as samples (default: [./demo_sounds](./demo_sounds/)). Currently, only wav files named 'A','E','I','O', and 'U' are supported. (*Note: This is a silly restriction that can easily be fixed.*)

### Examples:
```bash
# Generate audio using the example instructions and play the output.
python src/main.py instructions.json
```
```bash
# Generate audio using a custom set of samples.
python src/main.py instructions.json -s ./custom_sounds
```
```bash
# Generate audio and save to output.wav
python src/main.py instructions.json -o output.wav
```

## How it works

Interpolator applies four different interpolations, which each use very different methods.

### Magnitue and Phase

The magnitude and phase interpolations are closely related, as they both modify different aspects of the Short-Time Fourier Transform (STFT).

These two were the first and simplest of the four methods to implement. On their own, they create a sort of nicer-sounding crossfade, where the two samples are easy for the ear to differentiate between throughout the transition.

#### Step 1: STFT Calculation

Sound A and Sound B are represented in the frequency domain using the STFT.

#### Step 2: Magnitude / Phase Separation
Each STFT is separated into its magnitude (absolute value) and phase (angle)

#### Step 3: Magnitude Interpolation

The magnitude interpolation was the most straightforward to implement of the four methods.

Magnitude interpolation focuses on the or volume of different frequency components in a sound. Each sound is represented in the frequency domain using the Short-Time Fourier Transform (STFT). To interpolate magnitudes between two sounds, the algorithm calculates a weighted average of their magnitude spectra, which creates a smooth transition in energy distribution between the two sounds.

#### Step 4: Phase Interpolation

Phase interpolation deals with the alignment of sound waves in the frequency domain. The phase spectrum of the STFT represents the timing offset of each frequency component relative to the beginning of the signal. Smoothly interpolating the phase spectra of two sounds helps to align their waveforms in time, reducing potential artifacts during the transition.

Like the magnitude interpolation, phase interpolation is performed using a weighted average.

This method doesn't effect the sound much on its own, but when used in concert with the magnitude interpolation, it helps to remove artifacts and generally smooth out the transition.

#### Step 6: Re-Combination

The magnitude and phase are re-combined, using the STFT equation.
$$
STFT_{interp}(f, t) = M_{interp}(f, t) \cdot e^{i \Phi_{interp}(f, t)}
$$

#### Step 7: Conversion back to audio

The resulting combination is converted back to audio with the ISTFT.

