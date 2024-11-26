### Adaptive Tone Control

---

#### **Project Overview**

This project implements **Adaptive Tone Control**, an audio processing system that adjusts the volume (gain) of specified frequency bands (e.g., low, mid, high). The system analyzes the energy in each frequency band using Fast Fourier Transform (FFT) and applies band-specific filters to balance energy levels across bands.

The project includes functionality for:
- Dynamic tone control with adjustable parameters.
- Visualization of audio before and after processing.
- Audio file input/output for real-world use cases.
- Some testing for key modules.

---

#### **How It Works**

1. **Energy Analysis**:
   - The signal is divided into short overlapping frames.
   - The energy in each frequency band (e.g., low: 0–300 Hz, mid: 300–2000 Hz, high: 2000+ Hz) is calculated using FFT.

2. **Gain Adjustment**:
   - Gain is dynamically adjusted for each band to balance energy levels.
   - A smoothing function ensures gradual transitions to avoid abrupt changes.

3. **Band Filtering**:
   - Bandpass filters isolate each frequency band.
   - The adjusted gain is applied to each band, and the bands are recombined to produce the output signal.

4. **Visualization**:
   - Spectrograms of the original and modified signals are displayed, showing the impact of tone control.

---

#### **Key Features**

- **Dynamic Tone Adjustment**:
  Balances energy levels in real-time using a sliding window approach.

- **Customizable Parameters**:
  - **Bands**: Define frequency bands and their ranges.
  - **Frame Size**: Set the size of the processing window.
  - **Hop Size**: Control overlap between frames.
  - **Smoothing Factor**: Adjust the rate of gain changes.

- **Visualization**:
  Displays spectrograms of the original and processed audio, with frequency bands marked.

---

#### **Usage**

1. **Setup**:

   Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Run the Script**:

   ```bash
   python src/main.py input_audio.wav --output_file output_audio.wav
   ```

   **Optional Arguments**:
   - `--bands`: Specify custom frequency bands in the format `name:low-high,...`.
     Example:
     ```bash
     --bands "low:0-300,mid:300-2000,high:2000-8000"
     ```
   - `--frame_size`: Frame size for processing (default: 2048).
   - `--hop_size`: Hop size for overlapping frames (default: 1024).
   - `--smoothing_factor`: Smoothing factor for gain adjustments (default: 0.9).

3. **View Visualization**:
   After processing, the script displays spectrograms of the original and processed audio, with band boundaries marked.

---

#### **Example**

**Command**:
```bash
python src/main.py aaa.wav --output_file modified_aaa.wav --bands "low:0-300,mid:300-2000,high:2000-8000" --frame_size 1024 --hop_size 512 --smoothing_factor 0.8
```

**Output**:
- `modified_audio.wav`: Processed audio file.
- Visualization: Before/after spectrograms with bands marked.

#### **Lessons Learned**

1. **Energy Balancing Isn't Trivial**:
   - Directly balancing energy can cause abrupt transitions; smoothing gain adjustments made a huge difference for creating a more natural sound.

2. **FFT Window Size Matters**:
   - Larger window sizes provide better frequency resolution but can introduce latency. Smaller windows are more responsive but less precise.

3. **Band Filtering is Sensitive**:
   - Defining valid frequency ranges for bandpass filters (avoiding `0 Hz` or exceeding Nyquist frequency) resolved a lot of errors.
