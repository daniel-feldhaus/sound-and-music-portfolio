from dataclasses import dataclass
import numpy as np


@dataclass
class AudioData:
    """Audio data loaded using librosa.load"""

    data: np.ndarray
    sample_rate: int | float
