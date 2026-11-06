# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "lightgbm"]
# ///
# How to run: imported by group_fit.py and group_checks.py.
"""Complete-group smooth absolute loss with a global diagonal majorizer."""
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
import lightgbm as lgb

@dataclass(frozen=True, slots=True)
class GroupLoss:
    group: NDArray[np.int64]
    share: NDArray[np.float64]
    target: NDArray[np.float64]
    cf: NDArray[np.float64]
    weight: NDArray[np.float64]
    group_weight: NDArray[np.float64]
    delta: float
    regularizer: float
    grouped: bool

    def __post_init__(self) -> None:
        assert len(self.group) == len(self.cf) == len(self.share) == len(self.weight)
        assert self.group.min() == 0 and self.group.max()+1 == len(self.target)
        for array in (self.share,self.target,self.cf,self.weight,self.group_weight):
            assert np.isfinite(array).all()
        assert (self.share>0).all() and (self.weight>=0).all() and self.weight.sum()>0
        assert self.delta>0 and self.regularizer>=0
        np.testing.assert_allclose(np.bincount(self.group,weights=self.share),1.,rtol=1e-12)
        np.testing.assert_allclose(self.weight,self.group_weight[self.group]*self.share,rtol=1e-12)

    def residual(self, prediction: NDArray[np.float64]) -> NDArray[np.float64]:
        assert prediction.shape == self.cf.shape and np.isfinite(prediction).all()
        return np.bincount(self.group,weights=self.share*prediction,minlength=len(self.target))-self.target

    def derivatives(self, prediction: NDArray[np.float64]) -> tuple[NDArray[np.float64],NDArray[np.float64]]:
        residual = self.residual(prediction)[self.group] if self.grouped else prediction-self.cf
        gradient = self.weight*(residual/np.hypot(residual,self.delta)+self.regularizer*(prediction-self.cf))
        majorizer = self.weight*(1/self.delta+self.regularizer)
        assert np.isfinite(gradient).all() and np.isfinite(majorizer).all()
        return gradient,majorizer

    def value(self, prediction: NDArray[np.float64]) -> float:
        residual = self.residual(prediction) if self.grouped else prediction-self.cf
        weights = self.group_weight if self.grouped else self.weight
        return float(np.dot(weights,np.hypot(residual,self.delta)-self.delta)+self.regularizer/2*np.dot(self.weight,(prediction-self.cf)**2))

    def __call__(self, prediction: NDArray[np.float64], dataset: lgb.Dataset) -> tuple[NDArray[np.float64],NDArray[np.float64]]:
        assert dataset.num_data() == len(self.cf)
        np.testing.assert_array_equal(dataset.get_label(),self.cf.astype(np.float32))
        assert dataset.get_weight() is None and dataset.get_init_score() is None
        return self.derivatives(prediction)
