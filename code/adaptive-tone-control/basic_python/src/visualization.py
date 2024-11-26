import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt


def visualize_spectrograms(
    signal: np.ndarray,
    modified_signal: np.ndarray,
    sampling_rate: int,
    bands: dict[str, tuple[float, float]],
):
    """Display before/after spectrograms with band indicators."""
    _, axes = plt.subplots(2, 1, figsize=(10, 8))

    # Original spectrogram
    librosa.display.specshow(
        librosa.amplitude_to_db(np.abs(librosa.stft(signal)), ref=np.max),
        sr=sampling_rate,
        x_axis="time",
        y_axis="hz",
        ax=axes[0],
    )
    axes[0].set_title("Original Spectrogram")
    for low, high in bands.values():
        axes[0].axhline(low, color="red", linestyle="--", alpha=0.6)
        axes[0].axhline(high, color="red", linestyle="--", alpha=0.6)

    # Modified spectrogram
    librosa.display.specshow(
        librosa.amplitude_to_db(np.abs(librosa.stft(modified_signal)), ref=np.max),
        sr=sampling_rate,
        x_axis="time",
        y_axis="hz",
        ax=axes[1],
    )
    axes[1].set_title("Modified Spectrogram")
    for low, high in bands.values():
        axes[1].axhline(low, color="red", linestyle="--", alpha=0.6)
        axes[1].axhline(high, color="red", linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.show()
