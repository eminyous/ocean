from collections.abc import Iterable
from enum import Enum

import numpy as np
from ortools.sat.python import cp_model as cp
from pydantic import validate_call

from ..abc import Mapper
from ..feature import Feature
from ..tree import Tree
from ..typing import (
    Array1D,
    NonNegativeArray1D,
    NonNegativeInt,
    Unit,
)
from ._base import BaseModel
from ._builder.model import ModelBuilder, ModelBuilderFactory
from ._managers import FeatureManager, GarbageManager, TreeManager
from ._variables import FeatureVar


class Model(BaseModel, FeatureManager, TreeManager, GarbageManager):
    DEFAULT_EPSILON: Unit = 1.0 / (2.0**16)

    class Type(Enum):
        CP = "CP"

    # Constraints for the majority class.
    _scores: dict[tuple[NonNegativeInt, NonNegativeInt], cp.Constraint]

    # Model builder for the ensemble.
    _builder: ModelBuilder

    def __init__(
        self,
        trees: Iterable[Tree],
        mapper: Mapper[Feature],
        *,
        weights: NonNegativeArray1D | None = None,
        max_samples: NonNegativeInt = 0,
        epsilon: Unit = DEFAULT_EPSILON,
        model_type: Type = Type.CP,
    ) -> None:
        # Initialize the super models.
        BaseModel.__init__(self)
        TreeManager.__init__(
            self,
            trees=trees,
            weights=weights,
        )
        FeatureManager.__init__(self, mapper=mapper)
        GarbageManager.__init__(self)

        self._set_weights(weights=weights)
        self._max_samples = max_samples
        self._epsilon = epsilon
        self._scores = {}
        self._set_builder(model_type=model_type)

    def build(self) -> None:
        self.build_features(self)
        self.build_trees(self)
        self._builder.build(self, trees=self.trees, mapper=self.mapper)

    def add_objective(
        self,
        x: Array1D,
        *,
        norm: int = 1,
    ) -> None:
        objective = self._add_objective(x=x, norm=norm)
        self.Minimize(objective)

    @validate_call
    def set_majority_class(
        self,
        y: NonNegativeInt,
        *,
        op: NonNegativeInt = 0,
    ) -> None:
        if y >= self.n_classes:
            msg = f"Expected class < {self.n_classes}, got {y}"
            raise ValueError(msg)

        self._set_majority_class(y, op=op)

    def _set_builder(self, model_type: Type) -> None:
        match model_type:
            case Model.Type.CP:
                self._builder = ModelBuilderFactory.CP()

    def _set_majority_class(
        self,
        y: NonNegativeInt,
        *,
        op: NonNegativeInt,
    ) -> None:
        for class_ in range(self.n_classes):
            if class_ == y:
                continue

            rhs = self._epsilon if class_ < y else 0.0
            lhs = self.function[op, y] - self.function[op, class_]
            self._scores[op, class_] = self.Add(lhs >= rhs)
            self.add_garbage(self._scores[op, class_])

    def cleanup(self) -> None:
        self.remove_garbage()

    def _add_objective(self, x: Array1D, norm: int) -> cp.ObjLinearExprT:
        if x.size != self.mapper.n_columns:
            msg = f"Expected {self.mapper.n_columns} values, got {x.size}"
            raise ValueError(msg)
        if norm != 1:
            msg = f"Unsupported norm: {norm}"
            raise ValueError(msg)

        variables = self.mapper.values()
        return sum(map(self.L1, x, variables), start=cp.LinearExpr())

    def L1(self, x: np.float64, v: FeatureVar) -> cp.LinearExpr:
        objective_func = cp.LinearExpr()
        if v.is_binary:
            objective_func += v.xget() if x == 0.0 else 1 - v.xget()
        else:
            j = int(np.searchsorted(v.levels, x, side="right"))
            u = self.NewIntVar(
                0, len(v.levels) - 1, f"u_{v.X_VAR_NAME_FMT}_{j}"
            )
            self.add_garbage(u)
            self.add_garbage(self.AddAbsEquality(u, v.xget() - j))
            objective_func += u
        return objective_func
