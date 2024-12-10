import numpy as np
import parselmouth
from parselmouth.praat import call
from tqdm import tqdm
import numpy as np
from scipy.signal import get_window


def extract_formants_per_frame(
    audio: np.ndarray, sample_rate: int, frame_length: int, hop_length: int, num_formants: int = 5
) -> np.ndarray:
    """
    Extract formant frequencies per frame from an audio signal.

    Args:
        audio (np.ndarray): The audio signal.
        sample_rate (int): The sampling rate of the audio signal.
        frame_length (int): Length of each frame in samples.
        hop_length (int): Number of samples to advance between frames.
        num_formants (int): The number of formants to extract per frame.

    Returns:
        np.ndarray: An array of shape (num_formants, num_frames) containing formant frequencies.
    """
    num_samples = len(audio)
    num_frames = int(np.ceil((num_samples - frame_length) / hop_length)) + 1
    formant_frequencies = np.empty((num_formants, num_frames))
    formant_frequencies.fill(np.nan)  # Initialize with NaNs

    for i in range(num_frames):
        start_idx = i * hop_length
        end_idx = start_idx + frame_length
        frame = audio[start_idx:end_idx]

        # Zero-pad the frame if it's shorter than frame_length
        if len(frame) < frame_length:
            frame = np.pad(frame, (0, frame_length - len(frame)), mode="constant")

        # Create a parselmouth Sound object
        snd = parselmouth.Sound(frame, sampling_frequency=sample_rate)

        # Estimate formants using the Burg method
        formant = call(snd, "To Formant (burg)", 0.0, num_formants, 5500, 0.025, 50)

        # Time at which to extract formant values (center of the frame)
        t = (start_idx + frame_length / 2) / sample_rate

        # Extract formant frequencies for each formant
        for n in range(num_formants):
            frequency = formant.get_value_at_time(n + 1, t)
            if np.isnan(frequency) or frequency <= 0:
                frequency = np.nan
            formant_frequencies[n, i] = frequency

    return formant_frequencies


def interpolate_formants(
    audio_a: np.ndarray, audio_b: np.ndarray, combined_audio: np.ndarray, sample_rate: int
) -> np.ndarray:
    """
    Adjust the formants in combined_audio to transition between audio_a and audio_b.

    This function processes the combined audio signal frame by frame, modifying each frame's
    spectrum based on interpolated formants between audio_a and audio_b. The formants are
    extracted per frame from the two audio segments and linearly interpolated over time.

    Args:
        audio_a (np.ndarray): The first audio segment (e.g., tail of the first audio file).
        audio_b (np.ndarray): The second audio segment (e.g., head of the second audio file).
        combined_audio (np.ndarray): The combined audio to adjust (overlapping region).
        sample_rate (int): The sampling rate of the audio signals.

    Returns:
        np.ndarray: The audio signal with interpolated formants applied.
    """
    print("Starting formant interpolation...")

    # Parameters for framing
    frame_length = int(0.025 * sample_rate)  # 25 ms frames
    hop_length = int(0.0125 * sample_rate)  # 12.5 ms hop (50% overlap)
    window = get_window("hann", frame_length)

    # Extract formants per frame from audio_a and audio_b
    formants_a = extract_formants_per_frame(audio_a, sample_rate, frame_length, hop_length)
    formants_b = extract_formants_per_frame(audio_b, sample_rate, frame_length, hop_length)

    # Ensure both formant arrays have the same number of frames
    num_frames = min(formants_a.shape[1], formants_b.shape[1])
    formants_a = formants_a[:, :num_frames]
    formants_b = formants_b[:, :num_frames]

    # Interpolation factors
    alpha = np.linspace(0, 1, num_frames)

    # Interpolate formants
    interpolated_formants = (1 - alpha)[np.newaxis, :] * formants_a + alpha[
        np.newaxis, :
    ] * formants_b

    # Initialize the output audio with padding for overlap-add
    output_length = len(combined_audio) + frame_length
    output_audio = np.zeros(output_length)

    # Number of frames for combined_audio
    num_frames_audio = int(np.ceil((len(combined_audio) - frame_length) / hop_length)) + 1
    num_frames = min(num_frames, num_frames_audio)

    for i in tqdm(range(num_frames), "Modifying spectral envelope", unit="frame"):
        start = i * hop_length
        end = start + frame_length
        frame = combined_audio[start:end]

        # Zero-pad if the frame is shorter than frame_length
        if len(frame) < frame_length:
            frame = np.pad(frame, (0, frame_length - len(frame)), mode="constant")

        # Apply window function
        windowed_frame = frame * window

        # FFT to get the spectrum
        spectrum = np.fft.rfft(windowed_frame)
        frequencies = np.fft.rfftfreq(frame_length, 1 / sample_rate)

        # Modify the spectrum based on interpolated formants
        envelope = np.ones_like(spectrum)
        frame_formants = interpolated_formants[:, i]
        for f in frame_formants:
            if not np.isnan(f) and f > 0:
                gaussian = np.exp(-0.5 * ((frequencies - f) / 50) ** 2)
                envelope *= 1 + gaussian

        modified_spectrum = spectrum * envelope

        # Inverse FFT to get the modified frame
        modified_frame = np.fft.irfft(modified_spectrum)

        # Overlap-add the modified frame into the output audio
        output_audio[start:end] += modified_frame * window

    # Remove the padding to match the original combined_audio length
    output_audio = output_audio[: len(combined_audio)]

    # Normalize the output to prevent clipping
    max_amplitude = np.max(np.abs(output_audio))
    if max_amplitude > 1e-6:
        output_audio /= max_amplitude
    else:
        print("Warning: Output audio has very low amplitude.")

    return output_audio
