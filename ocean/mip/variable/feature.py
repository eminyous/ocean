import gurobipy as gp
import numpy as np

from ...feature import Feature
from ...feature.keeper import FeatureKeeper
from ...typing import Key
from ..base import BaseModel, Var


class FeatureVar(Var, FeatureKeeper):
    X_VAR_NAME_FMT: str = "x[{name}]"

    _x: gp.MVar
    _mu: gp.MVar

    def __init__(self, feature: Feature, name: str) -> None:
        Var.__init__(self, name=name)
        FeatureKeeper.__init__(self, feature=feature)

    @property
    def x(self) -> gp.Var:
        if self.is_one_hot_encoded:
            msg = "x property is not available for one-hot encoded features"
            raise ValueError(msg)
        return self._x.item()

    @property
    def X(self) -> float:
        return self.x.X

    def build(self, model: BaseModel) -> None:
        self._x = self._add(model)

        if self.is_numeric:
            self._mu = self._add_mu(model)
            model.addConstr(self._x.item() == self._xget())
        elif self.is_one_hot_encoded:
            model.addConstr(self._x.sum() == 1.0)

    def mget(self, key: int) -> gp.Var:
        if self.is_numeric:
            return self._mu[key].item()
        msg = "This feature does not support indexing"
        raise ValueError(msg)

    def __getitem__(self, code: Key) -> gp.Var:
        if not self.is_one_hot_encoded:
            msg = "Indexing is only supported for one-hot encoded features"
            raise ValueError(msg)
        i = self.codes.index(code)
        return self._x[i].item()

    def _add(self, model: BaseModel) -> gp.MVar:
        name = self.X_VAR_NAME_FMT.format(name=self._name)

        # Case when the feature is one-hot encoded.
        if self.is_one_hot_encoded:
            return self._add_one_hot_encoded(model, name)

        # Case when the feature is binary.
        if self.is_binary:
            return self._add_binary(model, name)

        # Case when the feature is continuous or discrete.
        return self._add_numeric(model, name)

    def _add_mu(self, model: BaseModel) -> gp.MVar:
        vtype = gp.GRB.CONTINUOUS if self.is_continuous else gp.GRB.BINARY
        n = len(self.levels) - 1
        name = f"{self._name}_mu"
        lb, ub = 0.0, 1.0
        mu = model.addMVar(shape=n, vtype=vtype, lb=lb, ub=ub, name=name)

        for j in range(n - 1):
            model.addConstr(mu[j + 1] <= mu[j])

        return mu

    def _add_one_hot_encoded(self, model: BaseModel, name: str) -> gp.MVar:
        m = len(self.codes)
        vtype = gp.GRB.BINARY
        names = [f"{name}[{code}]" for code in self.codes]
        return model.addMVar(shape=m, vtype=vtype, name=names)

    @staticmethod
    def _add_binary(model: BaseModel, name: str) -> gp.MVar:
        vtype = gp.GRB.BINARY
        return model.addMVar(shape=1, vtype=vtype, name=name)

    @staticmethod
    def _add_numeric(model: BaseModel, name: str) -> gp.MVar:
        vtype = gp.GRB.CONTINUOUS
        lb = -gp.GRB.INFINITY
        return model.addMVar(shape=1, vtype=vtype, lb=lb, name=name)

    def _xget(self) -> gp.LinExpr:
        mu = self._mu
        levels = self.levels
        diff = np.diff(levels)
        level = float(levels[0])
        return level + (mu * diff).sum().item()
