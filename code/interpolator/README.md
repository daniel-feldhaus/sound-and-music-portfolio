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
## Instruction Format
The instruction file contains a series of instructions in JSON format. Each instruction contains informaiton about a sound, its pitch, its duration, and the duration of the transition to the next sound.

The four settings are:
* **vowel**: The vowel sound to make. Restricted to 'A', 'E', 'I', 'O', and 'U'.
* **offset**: The note's offset in semitones from middle C.
* **duration**: How long the note should be played*
* **transition_duration**: How long the transition should be between this note and the next. If left out, there is no transition. This parameter is ignored for the last instruction.

Example:
```json
[
    {
        "vowel": "A",
        "offset": 0,
        "duration": 500,
        "transition_duration": 250
    },
    {
        "vowel": "E",
        "offset": 0,
        "duration": 400,
    },
]
```

\* The duration of each note is not super intuitive. Since each note overlaps with the one after it, the actual duration of the audio is dependent on both `duration` and `transition_duration`. This "feature" makes it difficult to create audio with a consistent tempo.



## How it works

Interpolator applies four different interpolations to achieve the final result.

### Method 1: Pitch Interpolation

Pitch interpolation adjusts the pitch of the two sounds before they are combined further by the other three methods.

I initially expected this to be the easiest of the four methods, but it turned out to be relatively difficult to apply a linear change over time. In my initial implementation, I attempted to create a system that worked with any input sound, however I eventually simplified to a method that assumes the input is at middle C.

The final method that I settle on uses the `WORLD` vocoder, which made things significantly easier by handing all of the feature extraction and recombination.

The final result accomplishes the pitch transition, while introducing a fair amount of artifacts.

#### Step 1: Pitch Analysis

The original pitch of the audio is estimated using `WORLD`. This step extracts the fundamental frequency (f0) over time, which represents the perceived pitch of the sound.

#### Step 2: Interpolating Pitch Scaling Factors

A scaling factor is computed to adjust the pitch from the source frequency to the target frequency. The target frequency is linearly interpolated over time to ensure a smooth pitch transition:

#### Step 3: Modifying the Pitch

The extracted f0 values are multiplied by the interpolated scaling factors to achieve the desired pitch adjustment. Care is taken to ensure the modified f0 values remain within a reasonable range to avoid unnatural artifacts.

#### Step 4: Resynthesis

The audio is reconstructed using the modified f0 values, along with the spectral envelope and aperiodicity features extracted during the analysis step. This ensures that the pitch-modified audio retains its original timbre and quality.


### Methods 2 & 3: Magnitue and Phase Interpolation

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

### Method 4: Formant Interpolation

The formant interpolation method focuses on smoothly transitioning the resonant frequencies (formants) between two sounds. I chose this method because formants are key features of vocal and instrumental timbres, so I thought that interpolating between them would help to emulate a more human transition. In reality, it seems that modifying formants like this is not very effective, or at least my chosen method wasn't.

The result is a bit of a mixed bag. When paired with magnitude/phase shifting, I think that it does better-approximate human transitions, but it adds a sort of rhaspy quality and the occasional artifact.

#### Step 1: Formant Extraction

Formants are extracted from both audio signals using the `parcelmouth` library, which estimates resonant frequencies frame by frame.

#### Step 2: Interpolation of Formants

Once the formant frequencies are extracted, they are interpolated linearly over time between the two sounds.

#### Step 3: Modification of Combined Audio

The spectral envelope of the combined audio is modified to match the interpolated formants, frame by frame. This is achieved by:

* Calculating the frequency spectrum of each frame using the FFT.
* Applying a Gaussian weighting function centered on the interpolated formant frequencies to enhance the spectral energy at those frequencies.

#### Step 4: Reconstructing the Audio

The modified frames are recalculated using the inverse FFT. They're then recombined using overlap-add to create smooth transitions between frames. The final audio is normalized to prevent clipping and ensure consistent amplitude.

### Bonus Method 5: Crossfade

In an effort to create a smoother transition in and out of the transitions themselves, a very short crossfade is applied at each point. This helps to hide some of the artifacts produced by the other methods.

## Lessons Learned
One of the most challenging aspects of this project was the debugging process. The majority of the issues that I encountered were that the audio didn't "sound right" in one way or another, which was difficult to resolve through testing, or to research. My intention with this project was to find novel, new (read: worse) methods than the ones that already exist, which meant I couldn't pull too much information from one source.

One benefit from this hardship is that I ended up learning a ton about audio analysis and manipulation. While these results have issues, there was a lot of learning behind the scenes, and I feel a lot more prepared for future audio projects.

## Future Work

This project has a lot of room for improvement!

#### Non-vowel support
I could easily add support for filenames other than the five vowels. I didn't test with any non-human noses, like instruments, but I expect the results would be interesting.

### Artifacts
The four methods combined generate a lot of artifacts, with the main culprits being the phase and formant methods.

I believe I could resolve some of these issues by modifying the formants of the two sounds separately before being merged via magnitude / phase.