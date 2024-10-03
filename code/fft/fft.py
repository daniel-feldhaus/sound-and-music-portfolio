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
        return np.array([x[0]], dtype=complex)  # base case: DFT of size 1

    # DFT of the even-indexed elements
    X_even = ditfft2(x, N // 2, 2 * s)

    # DFT of the odd-indexed elements
    X_odd = ditfft2(x[s:], N // 2, 2 * s)

    # Combine the results
    X = np.zeros(N, dtype=complex)
    for k in range(N // 2):
        twiddle = np.exp(-2j * np.pi * k / N) * X_odd[k]
        X[k] = X_even[k] + twiddle
        X[k + N // 2] = X_even[k] - twiddle

    return X


def inverse_ditfft2(X: np.ndarray, N: int, s: int) -> np.ndarray:
    """
    Recursive implementation of radix-2 inverse DIT FFT.

    Args:
        X (np.ndarray): Input array of complex numbers representing the frequency-domain signal.
        N (int): Size of the inverse DFT to compute.
        s (int): Stride, used to pick every s-th element in the array during recursion.

    Returns:
        np.ndarray: The inverse DFT of the input array X, yielding the time-domain signal.
    """
    if N == 1:
        return np.array([X[0]], dtype=complex)  # base case

    # Inverse FFT of the even-indexed elements
    x_even = inverse_ditfft2(X, N // 2, 2 * s)

    # Inverse FFT of the odd-indexed elements
    x_odd = inverse_ditfft2(X[N // 2 :], N // 2, 2 * s)

    # Combine the results
    x = np.zeros(N, dtype=complex)
    for n in range(N // 2):
        twiddle = np.exp(2j * np.pi * n / N) * x_odd[n]
        x[n] = x_even[n] + twiddle
        x[n + N // 2] = x_even[n] - twiddle

    return x


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
        magnitude = np.abs(fft_result[: window_size // 2 + 1])
        spectrogram.append(magnitude)

    return np.array(spectrogram).T  # Transpose so that rows represent frequencies


def save_spectrogram(
    filename: str,
    spectrogram: np.ndarray,
    window_size: int,
    overlap: int,
    sample_rate: int,
):
    meta = PngImagePlugin.PngInfo()
    meta.add_text("window_size", str(window_size))
    meta.add_text("overlap", str(overlap))
    meta.add_text("sample_rate", str(sample_rate))

    log_spectrogram = 10 * np.log10(spectrogram + 1e-6)
    meta.add_text("min", str(log_spectrogram.min()))
    meta.add_text("max", str(log_spectrogram.max()))
    # Normalize the spectrogram to the range [0, 255] for grayscale representation
    log_spectrogram -= log_spectrogram.min()
    log_spectrogram /= log_spectrogram.max()
    log_spectrogram *= 255

    # Create an image from the data and save it
    image = Image.fromarray(log_spectrogram.astype(np.uint8))
    image.save(filename, "png", pnginfo=meta)


def load_spectrogram(filename: str):
    """
    Loads a spectrogram from a file and recreates it using the included metadata.

    Args:
    filename (str): Path to the spectrogram image file.

    Returns:
    tuple: (spectrogram, window_size, overlap, sample_rate)
    """
    # Open the image and read metadata
    image = Image.open(filename)
    meta = image.info

    # Read parameters from metadata
    window_size = int(meta.get("window_size"))
    overlap = int(meta.get("overlap"))
    sample_rate = int(meta.get("sample_rate"))
    log_spectrogram_min = float(meta.get("min"))
    log_spectrogram_max = float(meta.get("max"))

    # Read the image data and convert back to the original log_spectrogram
    log_spectrogram_normalized = np.array(image)
    log_spectrogram = log_spectrogram_normalized.astype(np.float32)
    log_spectrogram /= 255
    log_spectrogram *= log_spectrogram_max - log_spectrogram_min
    log_spectrogram += log_spectrogram_min

    # Convert back from log scale to linear spectrogram
    spectrogram = 10 ** (log_spectrogram / 10) - 1e-6  # Reverse the log

    return spectrogram, window_size, overlap, sample_rate


def spectrogram_to_audio(
    spectrogram: np.ndarray, window_size: int, overlap: int
) -> np.ndarray:
    """
    Reconstructs audio from a spectrogram.
    """
    step_size = window_size - overlap
    num_windows = spectrogram.shape[1]
    audio_length = num_windows * step_size + overlap
    audio_data = np.zeros(audio_length)

    for i in range(num_windows):
        # Get magnitude spectrum
        magnitude = spectrogram[:, i]
        # Assume zero phase
        phase = np.zeros_like(magnitude)
        # Construct the complex spectrum
        positive_freqs = magnitude * np.exp(1j * phase)
        # Reconstruct the full spectrum
        full_spectrum = np.concatenate([positive_freqs, positive_freqs[-2:0:-1].conj()])
        # Inverse FFT
        time_signal = inverse_ditfft2(full_spectrum, window_size, 1).real
        time_signal /= window_size  # Normalize

        # Overlap-add
        start_idx = i * step_size
        end_idx = start_idx + window_size
        audio_data[start_idx:end_idx] += time_signal

    return audio_data


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python script.py <input_audio_file> <output_image_file> <output_audio_file>"
        )
        sys.exit(1)

    input_audio_file = sys.argv[1]
    output_image_file = sys.argv[2]
    output_audio_file = sys.argv[3]

    # Read the audio file
    audio_data, sample_rate = sf.read(input_audio_file)

    # If stereo, select one channel (first channel)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    window_size = 1024  # Size of the FFT window
    overlap = 512  # Overlap between consecutive windows

    # Generate and save spectrogram
    spectrogram = audio_to_spectrogram(audio_data, window_size, overlap, ditfft2)
    save_spectrogram(output_image_file, spectrogram, window_size, overlap, sample_rate)
    print(f"Spectrogram saved as {output_image_file}")

    # Load spectrogram and reconstruct audio
    loaded_spectrogram, ws, ov, sr = load_spectrogram(output_image_file)
    reconstructed_audio = spectrogram_to_audio(loaded_spectrogram, ws, ov)

    # Save the reconstructed audio
    sf.write(output_audio_file, reconstructed_audio, sr)
    print(f"Reconstructed audio saved as {output_audio_file}")


if __name__ == "__main__":
    main()
