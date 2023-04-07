"""SWC geometry operations."""

from typing import Generic, Literal, Optional, TypeVar

import numpy as np
import numpy.typing as npt

from ..core import DictSWC
from ..core.swc_utils import SWCNames, get_names
from ..utils import rotate3d, rotate3d_x, rotate3d_y, rotate3d_z, scale3d, translate3d
from .base import Transform

__all__ = [
    "Normalizer",
    "Translate",
    "Scale",
    "Rotate",
    "RotateX",
    "RotateY",
    "RotateZ",
]

T = TypeVar("T", bound=DictSWC)
Center = Literal["root", "soma", "origin"]


# pylint: disable=too-few-public-methods
class Normalizer(Generic[T], Transform[T, T]):
    """Noramlize coordinates and radius to 0-1."""

    names: SWCNames

    def __init__(self, *, names: Optional[SWCNames] = None) -> None:
        super().__init__()
        self.names = get_names(names)

    def __call__(self, x: T) -> T:
        """Scale the `x`, `y`, `z`, `r` of nodes to 0-1."""
        new_tree = x.copy()
        xyzr = [self.names.x, self.names.y, self.names.z, self.names.r]
        for key in xyzr:  # TODO: does r is the same?
            vs = new_tree.ndata[key]
            new_tree.ndata[key] = (vs - np.min(vs)) / np.max(vs)

        return new_tree


class _Transform(Generic[T], Transform[T, T]):
    tm: npt.NDArray[np.float32]
    center: Center
    fmt: str

    def __init__(
        self,
        tm: npt.NDArray[np.float32],
        center: Center = "origin",
        fmt: str = "",
        *,
        names: Optional[SWCNames] = None,
    ) -> None:
        self.tm, self.center, self.fmt = tm, center, fmt
        self.names = get_names(names)

    def __call__(self, x: T) -> T:
        match self.center:
            case "root" | "soma":
                idx = np.nonzero(x.ndata[self.names.pid] == -1)[0].item()
                xyz = x.xyz()[idx]
                tm = (
                    translate3d(-xyz[0], -xyz[1], -xyz[2])
                    .dot(self.tm)
                    .dot(translate3d(xyz[0], xyz[1], xyz[2]))
                )
            case _:
                tm = self.tm

        xyzw = x.xyzw().dot(tm).T
        y = x.copy()
        y.ndata[self.names.x] = xyzw[0]
        y.ndata[self.names.y] = xyzw[1]
        y.ndata[self.names.z] = xyzw[2]
        return y

    def __repr__(self) -> str:
        return self.fmt


class Translate(_Transform[T]):
    """Translate SWC."""

    def __init__(self, tx: float, ty: float, tz: float) -> None:
        fmt = f"Translate-{tx}-{ty}-{tz}"
        super().__init__(translate3d(tx, ty, tz), fmt=fmt)

    @classmethod
    def transform(cls, x: T, tx: float, ty: float, tz: float) -> T:
        return cls(tx, ty, tz)(x)


class Scale(_Transform[T]):
    """Scale SWC."""

    def __init__(
        self, sx: float, sy: float, sz: float, center: Center = "root"
    ) -> None:
        fmt = f"Scale-{sx}-{sy}-{sz}"
        super().__init__(scale3d(sx, sy, sz), center=center, fmt=fmt)

    @classmethod
    def transform(  # pylint: disable=too-many-arguments
        cls, x: T, sx: float, sy: float, sz: float, center: Center = "root"
    ) -> T:
        return cls(sx, sy, sz, center=center)(x)


class Rotate(_Transform[T]):
    """Rotate SWC."""

    def __init__(
        self, n: npt.NDArray[np.float32], theta: float, center: Center = "root"
    ) -> None:
        fmt = f"Rotate-{n[0]}-{n[1]}-{n[2]}-{theta:.4f}"
        super().__init__(rotate3d(n, theta), center=center, fmt=fmt)

    @classmethod
    def transform(
        cls, x: T, n: npt.NDArray[np.float32], theta: float, center: Center = "root"
    ) -> T:
        return cls(n, theta, center=center)(x)


class RotateX(_Transform[T]):
    """Rotate SWC with x-axis."""

    def __init__(self, theta: float, center: Center = "root") -> None:
        super().__init__(rotate3d_x(theta), center=center, fmt=f"RotateX-{theta}")

    @classmethod
    def transform(cls, x: T, theta: float, center: Center = "root") -> T:
        return cls(theta, center=center)(x)


class RotateY(_Transform[T]):
    """Rotate SWC with y-axis."""

    def __init__(self, theta: float, center: Center = "root") -> None:
        super().__init__(rotate3d_y(theta), center=center, fmt=f"RotateX-{theta}")

    @classmethod
    def transform(cls, x: T, theta: float, center: Center = "root") -> T:
        return cls(theta, center=center)(x)


class RotateZ(_Transform[T]):
    """Rotate SWC with z-axis."""

    def __init__(self, theta: float, center: Center = "root") -> None:
        super().__init__(rotate3d_z(theta), center=center, fmt=f"RotateX-{theta}")

    @classmethod
    def transform(cls, x: T, theta: float, center: Center = "root") -> T:
        return cls(theta, center=center)(x)