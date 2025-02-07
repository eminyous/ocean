# Optimal Counterfactual Explanations in Tree Ensembles

![Logo](logo.svg)

This repository provides methods to generate optimal counterfactual explanations in tree ensembles.
It is based on the paper *Optimal Counterfactual Explanations in Tree Ensemble* by Axel Parmentier and Thibaut Vidal in the *Proceedings of the thirty-eighth International Conference on Machine Learning*, 2021, in press. The article is [available here](http://proceedings.mlr.press/v139/parmentier21a/parmentier21a.pdf).

## Installation

This project requires the gurobi solver. You can request for a free academic license [here](https://www.gurobi.com/academia/academic-program-and-licenses/). Once you have installed gurobi, you can install the package with the following command:

```bash
pip install git+https://github.com/eminyous/ocean.git
```

## Usage

The package provides multiple classes and functions to wrap the tree ensemble models from the `scikit-learn` library. A minimal example is provided below:

```python
import gurobipy as gp
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ocean.datasets import load_adult
from ocean.mip import FeatureVar, Model
from ocean.tree import parse_trees


def get_value(var: FeatureVar) -> float | str | int | None:
    if not var.is_one_hot_encoded:
        if var.is_binary:
            return int(var.X)

        if np.isclose(var.X, 0.0):
            return 0.0
        return var.X
    for code in var.codes:
        if var[code].X == 1:
            return code
    msg = "No code has been selected."
    raise ValueError(msg)


def print_dict[K, V](dictionary: dict[K, V]) -> None:
    max_key_length = max(len(set(k)) for k in dictionary)
    for k, v in dictionary.items():
        print(f"{str(k).ljust(max_key_length + 1)} :\t{v}")


mapper, (data, target) = load_adult()

x, y = data.to_numpy(), target.to_numpy()

rf = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
rf.fit(x, y)

trees = parse_trees(rf, mapper=mapper)

env = gp.Env(empty=True)
env.setParam("OutputFlag", 0)
env.start()

model = Model(trees, mapper, env=env)
model.build()

generator = np.random.default_rng(42)
i = generator.integers(0, x.shape[0])
x_ = x[i]
y_ = rf.predict(x_.reshape(1, -1))[0]

model.set_majority_class(m_class=1 - y_)
model.optimize()

new_x = dict(model.solution.apply(get_value))
print_dict(new_x)
```
