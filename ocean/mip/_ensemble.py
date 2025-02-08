from collections.abc import Iterable

import gurobipy as gp
import numpy as np

from ..tree import Tree
from ..typing import (
    NonNegativeArray1D,
    NonNegativeInt,
    PositiveInt,
)
from ._base import BaseModel
from ._variable import TreeVar


class Ensemble:
    TREE_VAR_FMT: str = "tree[{t}]"

    # Tree variables in the ensemble.
    _trees: tuple[TreeVar, *tuple[TreeVar, ...]]

    # Numer of isolators in the model.
    _n_isolators: NonNegativeInt

    # Maximum number of samples in the isolators.
    _max_samples: NonNegativeInt

    # Weights for the estimators in the ensemble.
    _weights: NonNegativeArray1D

    def __init__(
        self,
        trees: Iterable[Tree],
        *,
        weights: NonNegativeArray1D | None = None,
        n_isolators: NonNegativeInt = 0,
        max_samples: NonNegativeInt = 0,
        flow_type: TreeVar.FlowType = TreeVar.FlowType.CONTINUOUS,
    ) -> None:
        self._set_trees(trees=trees, flow_type=flow_type)
        self._n_isolators = n_isolators
        self._max_samples = max_samples
        self._set_weights(weights)

    def build_trees(self, model: BaseModel) -> None:
        model.build_vars(*self.trees)

    @property
    def n_trees(self) -> PositiveInt:
        return len(self.trees)

    @property
    def n_isolators(self) -> NonNegativeInt:
        return self._n_isolators

    @property
    def n_estimators(self) -> PositiveInt:
        return self.n_trees - self.n_isolators

    @property
    def trees(self) -> tuple[TreeVar, *tuple[TreeVar, ...]]:
        return self._trees

    @property
    def estimators(self) -> tuple[TreeVar, *tuple[TreeVar, ...]]:
        return self._trees[0], *self._trees[1 : self.n_estimators]

    @property
    def isolators(self) -> tuple[TreeVar, ...]:
        return self._trees[self.n_estimators :]

    @property
    def shape(self) -> tuple[NonNegativeInt, ...]:
        return self._trees[0].shape

    @property
    def n_classes(self) -> NonNegativeInt:
        return self.shape[-1]

    @property
    def max_samples(self) -> NonNegativeInt:
        return self._max_samples

    @property
    def weights(self) -> NonNegativeArray1D:
        return self._weights

    @property
    def function(self) -> gp.MLinExpr:
        return self.weighted_function(weights=self.weights)

    @property
    def length(self) -> gp.LinExpr:
        return sum((tree.length for tree in self.isolators), gp.LinExpr())

    def weighted_function(self, weights: NonNegativeArray1D) -> gp.MLinExpr:
        # \sum_{t=1}^{T} w_t f_t(x)
        return sum(
            (
                np.float64(weights[t]) * tree.value
                for t, tree in enumerate(self.estimators)
            ),
            gp.MLinExpr.zeros(self.shape),
        )

    def _set_trees(
        self,
        trees: Iterable[Tree],
        *,
        flow_type: TreeVar.FlowType,
    ) -> None:
        def create(item: tuple[int, Tree]) -> TreeVar:
            t, tree = item
            name = self.TREE_VAR_FMT.format(t=t)
            return TreeVar(tree, name=name, flow_type=flow_type)

        tree_vars = tuple(map(create, enumerate(trees)))
        if len(tree_vars) == 0:
            msg = "At least one tree is required."
            raise ValueError(msg)

        self._trees = tree_vars[0], *tree_vars[1:]

    def _set_weights(self, weights: NonNegativeArray1D | None = None) -> None:
        if weights is None:
            weights = np.ones(self.n_estimators, dtype=np.float64)

        if len(weights) != self.n_estimators:
            msg = "The number of weights must match the number of trees."
            raise ValueError(msg)

        self._weights = weights
