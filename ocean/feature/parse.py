from typing import Any

import pandas as pd

from ..abc import Mapper
from ..typing import Key
from .feature import Feature

N_BINARY: int = 2


def _count_unique(series: "pd.Series[Any]") -> int:
    return series.nunique()


def _remove_na_columns(data: pd.DataFrame) -> pd.DataFrame:
    return data.dropna(axis=1)


def _remove_constant_columns(data: pd.DataFrame) -> pd.DataFrame:
    return data.loc[:, data.apply(_count_unique) > 1]


def _parse(
    data: pd.DataFrame,
    *,
    discretes: tuple[Key, ...] = (),
    scale: bool = True,
) -> tuple[Mapper[Feature], pd.DataFrame]:
    discrete = set(discretes)
    frames: list[pd.DataFrame | pd.Series[int] | pd.Series[float]] = []
    features: list[Feature] = []
    keys: list[Key] = []

    for column in data.columns:
        series: pd.Series[Any] = data[column].rename("")
        levels: tuple[float, ...] = ()
        codes: tuple[Key, ...] = ()

        if column in discrete:
            series = series.astype(float)
            frames.append(series)
            levels = tuple(set(series.dropna()))
            feature = Feature(Feature.Type.DISCRETE, levels=levels)
        elif series.nunique() == N_BINARY:
            frames.append(
                pd.get_dummies(series, drop_first=True)
                .iloc[:, 0]
                .rename("")
                .astype(int)
            )
            feature = Feature(Feature.Type.BINARY)
        elif pd.to_numeric(series, errors="coerce").notna().all():
            x = series.astype(float)
            if scale:
                x = ((x - x.min()) / (x.max() - x.min()) - 0.5).astype(float)
            frames.append(x)
            levels = (x.min() - 0.5, x.max() + 0.5)
            feature = Feature(Feature.Type.CONTINUOUS, levels=levels)
        else:
            frames.append(pd.get_dummies(series).astype(int))
            codes = tuple(set(series))
            feature = Feature(Feature.Type.ONE_HOT_ENCODED, codes=codes)

        keys.append(column)
        features.append(feature)

    proc = pd.concat(frames, axis=1, keys=keys)
    mapping = dict(zip(keys, features, strict=True))

    if proc.columns.nlevels == 1:
        columns = pd.Index(proc.columns)
    else:
        columns = pd.MultiIndex.from_tuples(proc.columns)

    mapper = Mapper(mapping, columns=columns)
    return mapper, proc


def parse_features(
    data: pd.DataFrame,
    *,
    discretes: tuple[Key, ...] = (),
    drop_na: bool = True,
    drop_constant: bool = True,
    scale: bool = True,
) -> tuple[Mapper[Feature], pd.DataFrame]:
    """
    Preprocesses a DataFrame by validating, cleaning, and parsing features.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to be processed.
    discretes : tuple[Key, ...], optional
        A tuple of column names that should be treated as discrete features.
        default is (). If None, no column is treated as discrete.
    drop_na : bool, optional
        Whether to drop columns with NaN values. default is True.
    drop_constant : bool, optional
        Whether to drop columns with constant values. default is True.
    scale : bool, optional
        Whether to scale continuous features between [0, 1].
        default is True.

    Returns
    -------
        Mapper[Feature]
            A mapper that maps the DataFrame columns to the features.
        pd.DataFrame
            The processed DataFrame.

    Raises
    ------
    ValueError
        If a column in `discretes` is not found in the DataFrame.

    """
    missing = [col for col in discretes if col not in data.columns]
    if missing:
        msg = f"Columns not found in the data: {missing}"
        raise ValueError(msg)

    if drop_na:
        data = _remove_na_columns(data)
    if drop_constant:
        data = _remove_constant_columns(data)

    return _parse(data, discretes=discretes, scale=scale)
