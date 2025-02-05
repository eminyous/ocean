from collections.abc import Iterator

from ..typing import NonNegativeInt
from .node import Node
from .tree import Tree

TreeLike = Tree | Node


class TreeKeeper:
    _tree: Tree

    def __init__(self, tree: TreeLike) -> None:
        if not isinstance(tree, Tree):
            tree = Tree(root=tree)
        self._tree = tree

    @property
    def root(self) -> Node:
        return self._tree.root

    @property
    def n_nodes(self) -> NonNegativeInt:
        return self._tree.n_nodes

    @property
    def leaves(self) -> tuple[Node, ...]:
        return self._tree.leaves

    @property
    def max_depth(self) -> NonNegativeInt:
        return self._tree.max_depth

    @property
    def shape(self) -> tuple[NonNegativeInt, ...]:
        return self._tree.shape

    def nodes_at(self, depth: int) -> Iterator[Node]:
        return self._tree.nodes_at(depth=depth)
