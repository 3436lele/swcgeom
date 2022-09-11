"""Tree Folder Dataset."""

import os
from typing import Generic, TypeVar, cast

import torch.utils.data

from ...core import Tree
from ...transforms import Transform

__all__ = ["TreeFolderDataset"]

T = TypeVar("T")


class TreeFolderDataset(torch.utils.data.Dataset, Generic[T]):
    """Tree folder in swc format."""

    swc_dir: str
    swcs: list[str]

    transform: Transform[Tree, T] | None

    def __init__(
        self,
        swc_dir: str,
        transform: Transform[Tree, T] | None = None,
    ) -> None:
        """Create tree dataset.

        Parameters
        ----------
        swc_dir : str
            Path of SWC file directory.
        transfroms : Transfroms[Tree, T], optional
            Branch transformations.

        See Also
        --------
        ~swcgeom.data.torch.transforms : module
            Preset transform set.
        """
        super().__init__()
        self.swc_dir = swc_dir
        self.swcs = self.find_swcs(swc_dir)
        self.transform = transform

    def __getitem__(self, idx: int) -> tuple[T, int]:
        """Get a tree data.

        Returns
        -------
        x : Tree
            A tree from swc format.
        y : int
            Label of x, always 0.
        """
        tree = Tree.from_swc(self.swcs[idx])
        x = self.transform(tree) if self.transform else tree
        return cast(T, x), 0

    def __len__(self) -> int:
        """Get length of set of trees."""
        return len(self.swcs)

    @staticmethod
    def find_swcs(swc_dir: str) -> list[str]:
        """Find all swc files."""
        swcs = list[str]()
        for root, dirs, files in os.walk(swc_dir):  # pylint: disable=unused-variable
            files = [f for f in files if os.path.splitext(f)[-1] == ".swc"]
            swcs.extend([os.path.join(root, f) for f in files])

        return swcs