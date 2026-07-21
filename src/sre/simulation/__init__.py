"""Simulation engine for evaluating reconstruction accuracy under controlled conditions."""

from .engine import (
    RandomProtoGenerator,
    ReconstructionTrial,
    SimulatedSoundChange,
    SimulationReport,
    run_battery,
    run_trial,
)
from .metrics import segment_accuracy, sound_change_precision_recall

__all__ = [
    "RandomProtoGenerator",
    "ReconstructionTrial",
    "SimulatedSoundChange",
    "SimulationReport",
    "run_battery",
    "run_trial",
    "segment_accuracy",
    "sound_change_precision_recall",
]
