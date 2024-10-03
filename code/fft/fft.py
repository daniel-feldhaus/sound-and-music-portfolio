import numpy as np
from PIL import Image
from PIL import PngImagePlugin
import soundfile as sf
import sys


def ditfft2(x: np.ndarray, N: int, s: int) -> np.ndarray:
    """
    Recursive implementation of radix-2 DIT FFT.
    Adapted from pseudocode from here: https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm

    Args:
    x (np.ndarray): Input array of complex numbers.
    N (int): Size of the DFT to compute.
    s (int): Stride, to pick every s-th element in the array.

    Returns:
    np.ndarray: The DFT of the input array x.
    """
    if N == 1:
        return np.array([x[0]])  # base case: DFT of size 1

    # DFT of the even-indexed elements
    X_even = ditfft2(x, N // 2, 2 * s)

    # DFT of the odd-indexed elements
    X_odd = ditfft2(x[s:], N // 2, 2 * s)

    # Combine the results
    X = np.zeros(N, dtype=complex)
    for k in range(N // 2):
        p = X_even[k]
        q = np.exp(-2j * np.pi * k / N) * X_odd[k]
        X[k] = p + q
        X[k + N // 2] = p - q

    return X


def audio_to_spectrogram(
    audio_data: np.ndarray, window_size: int, overlap: int, fft_func
) -> np.ndarray:
    """
    Computes a 2D spectrogram using the FFT function.

    Args:
    audio_data (np.ndarray): Input audio signal.
    window_size (int): Size of each FFT window (number of samples per window).
    overlap (int): Overlap between consecutive windows (in samples).
    fft_func (function): FFT function to use.

    Returns:
    np.ndarray: Spectrogram as a 2D array (time x frequency).
    """
    step_size = window_size - overlap
    num_windows = (len(audio_data) - window_size) // step_size + 1
    spectrogram = []

    for i in range(num_windows):
        # Extract the windowed portion of the audio signal
        start_idx = i * step_size
        end_idx = start_idx + window_size
        window_data = audio_data[start_idx:end_idx]

        # Apply FFT to the window
        fft_result = fft_func(window_data, window_size, 1)

        # Compute magnitude and add to the spectrogram
        magnitude = np.abs(
            fft_result[: window_size // 2]
        )  # Only take the positive frequencies
        spectrogram.append(magnitude)

    return np.array(spectrogram).T  # Transpose so that rows represent frequencies


def save_spectrogram(
    filename: str, spectrogram: np.ndarray, window_size: int, overlap: int
):
    meta = PngImagePlugin.PngInfo()
    meta.add_text("window_size", str(window_size))
    meta.add_text("overlap", str(overlap))

    log_spectrogram = 10 * np.log10(spectrogram + 1e-6)
    meta.add_text("min", str(log_spectrogram.min()))
    meta.add_text("max", str(log_spectrogram.max()))
    # Normalize the spectrogram to the range [0, 255] for grayscale representation
    log_spectrogram -= log_spectrogram.min()
    log_spectrogram /= log_spectrogram.max()
    log_spectrogram *= 255
    with Image.open(filename) as im:
        im.save(filename, "png", pngInfo=meta)


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_audio_file> <output_image_file>")
        sys.exit(1)

    input_audio_file = sys.argv[1]
    output_image_file = sys.argv[2]

    # Read the audio file
    audio_data, _sample_rate = sf.read(input_audio_file)

    # If stereo, select one channel (first channel)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    window_size = 1024  # Size of the FFT window
    overlap = 512  # Overlap between consecutive windows

    spectrogram = audio_to_spectrogram(audio_data, window_size, overlap, ditfft2)
    save_spectrogram(output_image_file, spectrogram, window_size, overlap)
    print(f"Spectrogram saved as {output_image_file}")


if __name__ == "__main__":
    main()
