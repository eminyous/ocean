from collections.abc import Hashable, Iterable
from enum import Enum

import numpy as np

from ..typing import FloatArray1D, Number


class Feature:
    class Type(Enum):
        CONTINUOUS = "continuous"
        DISCRETE = "discrete"
        ONE_HOT_ENCODED = "one-hot-encoded"
        BINARY = "binary"

    _ftype: Type
    _levels: FloatArray1D
    _codes: tuple[Hashable, ...]

    def __init__(
        self,
        *,
        ftype: Type = Type.BINARY,
        levels: Iterable[Number] = (),
        codes: Iterable[Hashable] = (),
    ) -> None:
        self._ftype = ftype
        self._levels = np.sort(list(set(levels))).flatten().astype(np.float64)
        self._codes = tuple(set(codes))

    @property
    def ftype(self) -> Type:
        return self._ftype

    @property
    def is_continuous(self) -> bool:
        return self.ftype == Feature.Type.CONTINUOUS

    @property
    def is_discrete(self) -> bool:
        return self.ftype == Feature.Type.DISCRETE

    @property
    def is_one_hot_encoded(self) -> bool:
        return self.ftype == Feature.Type.ONE_HOT_ENCODED

    @property
    def is_binary(self) -> bool:
        return self.ftype == Feature.Type.BINARY

    @property
    def is_numeric(self) -> bool:
        return self.is_continuous or self.is_discrete

    @property
    def levels(self) -> FloatArray1D:
        if not self.is_numeric:
            msg = "Levels can only be accessed for numeric features."
            raise AttributeError(msg)
        if self._levels.size == 0:
            msg = "Levels have not been defined for this feature."
            raise AttributeError(msg)
        return self._levels

    @property
    def codes(self) -> tuple[Hashable, ...]:
        if not self.is_one_hot_encoded:
            msg = "Codes can only be accessed for one-hot encoded features."
            raise AttributeError(msg)
        if not self._codes:
            msg = "Codes have not been defined for this feature."
            raise AttributeError(msg)
        return self._codes

    def add(self, *levels: Number) -> None:
        if not self.is_continuous:
            msg = "Levels can only be added to continuous features."
            raise AttributeError(msg)
        if np.any(np.isnan(levels)):
            msg = "Levels cannot contain NaN values."
            raise ValueError(msg)
        lvls = list(set(self._levels) | set(levels))
        self._levels = np.sort(lvls).flatten().astype(np.float64)
