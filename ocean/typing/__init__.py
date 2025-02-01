import numpy as np
from sklearn.ensemble import RandomForestClassifier

BaseEnsemble = RandomForestClassifier

Number = int | float
Array1D = np.ndarray[tuple[int], np.dtype[np.float64]]
Array2D = np.ndarray[tuple[int, int], np.dtype[np.float64]]
Array = np.ndarray[tuple[int, ...], np.dtype[np.float64]]

__all__ = [
    "Array",
    "Array1D",
    "Array2D",
    "BaseEnsemble",
    "Number",
]
