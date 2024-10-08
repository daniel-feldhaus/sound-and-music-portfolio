# Homework 1: Clipped

## What I Did
[clipped.py](./clipped.py) contains functions for creating sin wave samples, saving them, and playing them. When run, the program saves two files ([sine.wav](./sine.wav) and and [clipped.wav](./clipped.wav)), and plays the sine wave samples directly.

I used the provided [wavfile](https://github.com/pdx-cs-sound/wavfile/blob/master/wavfile.py) utility to double-check that both files were saved correctly.

## How It Went
This was actually super easy! I couldn't wait till this week to get started, so last week I wrote a program that converts audio to spectrogram and back again using the fast fourier transform and inverse fast fourier transform. This assignment was basically the same thing but simpler!

You can check out last week's project [here](../fft/).

## To Run:
1. Install dependencies
```bash
python -m pip install -r requirements.txt
```
2. Run the program.
```
python clipped.py
```

