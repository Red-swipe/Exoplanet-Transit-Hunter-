"""Machine learning model definitions for transit detection.

This module will host classical and deep learning model implementations used
to classify candidate transit events in astronomical light curves.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for the baseline neural transit classifier.

    Attributes:
        input_channels: Number of channels in each light curve sample.
        hidden_channels: Number of convolutional filters.
        output_classes: Number of target classes.
    """

    input_channels: int = 1
    hidden_channels: int = 32
    output_classes: int = 2


class TransitClassifier(nn.Module):
    """Baseline one-dimensional CNN for light curve classification."""

    def __init__(self, config: ModelConfig | None = None) -> None:
        """Initialize the classifier.

        Args:
            config: Optional model configuration.
        """

        super().__init__()
        self.config = config or ModelConfig()
        self.network = nn.Sequential(
            nn.Conv1d(
                in_channels=self.config.input_channels,
                out_channels=self.config.hidden_channels,
                kernel_size=7,
                padding=3,
            ),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(self.config.hidden_channels, self.config.output_classes),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """Run a forward pass.

        Args:
            inputs: Tensor shaped ``(batch, channels, sequence_length)``.

        Returns:
            Logits for each target class.
        """

        return self.network(inputs)
