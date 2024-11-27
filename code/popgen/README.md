# popgen: play a pop music loop
Bart Massey 2024

This Python program generates a pseudo-melody using chord
and bass notes from the [Axis
Progression](https://en.wikipedia.org/wiki/axis_progression).

# Changes
Some improvements and additions have been made as part of assigned work.

Of the suggested features to implement, the following ones have been added:

### Get rid of the note clicking by adding a bit of envelope.

All notes and beats use a linear envelope to reduce popping.

### Add a constructed rhythm track using noise samples.

Kick and snare drums are supported, along with the following arguments to control them:
* `--rhythm-pattern`: Set the pattern of snare / kick beats
* `--rhythm-volume`: Set the volume of the rhythm sounds.


Example:
```bash
python popgen.py --rhythm-pattern "ks_ks_k_ks_ks_kk" --rhythm-volume 0.5
```

### Use a more interesting waveform than sine waves.

Sawtooth and square waves can be set with the `--waveform` argument.

Example:
```bash
python popgen.py --waveform square
```

### Keep the melody locked or rubber-banded to a certain range, so that it doesn't go "too high" or "too low".

The melody now wanders a set maximum distance from the origin. Instead of clamping the values, the probability of moving towards the center increases as the melody nears the edge. The maximum offset can be controlled with `--max-offset`

Example:
```bash
python popgen.py --max-offset 1
```

### Allow rhythm patterns for the melody other than one note per beat.

The rhythm pattern can be set to a separate BPM witth the `--rhythm-bpm` argument. If unset, the rhythm will default to the same bpm as the melody.

Example:
```bash
python popgen.py   --bpm 120   --rhythm-bpm 240   --rhythm-pattern "k__s__k_"   --rhythm-volume 0.35   --waveform sine
```
# Demo

Demos for the three wave types can be found here:
* [Sawtooth](./demo_sawtooth.wav)
* [Sine](./demo_sine.wav)
* [Square](./demo_square.wav)

An additional demo demonstrating a three/four time signature can be found at [demo_three_four.wav](./demo_three_four.wav).

The three/four demo was generated using this command:
```bash
python popgen.py   --bpm 120   --rhythm-bpm 240   --rhythm-pattern "k__s__k_"   --rhythm-volume 0.35   --waveform sine   --outp
ut demo_three_four.wav
```


# License

This work is licensed under the "MIT License". Please see the file
`LICENSE.txt` in this distribution for license terms.
