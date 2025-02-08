from sklearn.ensemble._iforest import (
    _average_path_length,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType, reportPrivateUsage, reportArgumentType] # noqa: PLC2701
)

from ..typing import NonNegativeInt, Number


def average_length(n: NonNegativeInt) -> Number:
    return float(_average_path_length([n])[0])  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
