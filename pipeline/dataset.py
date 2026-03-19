"""
Dataset Pipeline — structured datasets for training & evaluation.

Builds labeled datasets from historical transactions for:
- Wallet scoring (profitable vs unprofitable)
- Rug pull detection (scam vs legit)
- Signal quality (signal → outcome mapping)

I/O:
  INPUT:  Raw transactions from ingestion + DexScreener prices
  OUTPUT: Labeled CSV/JSON datasets + train/test splits
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from dataclasses import dataclass, field
from pathlib import Path

import aiosqlite
from config import DATABASE_PATH

logger = logging.getLogger("hydranet.pipeline.dataset")


@dataclass
class LabeledSample:
    """A single labeled data point for training/eval."""
    sample_id: str
    features: dict[str, float]
    label: str  # "profitable" | "unprofitable" | "scam" | "legit" | "alpha" | "noise"
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class DatasetBuilder:
    """Builds structured datasets from raw transaction data."""

    def __init__(self, output_dir: str = "./datasets"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._samples: list[LabeledSample] = []

    async def build_wallet_scoring_dataset(self, wallets: list[dict]) -> list[LabeledSample]:
        """
        INPUT:  List of wallet dicts with transaction history
        OUTPUT: Labeled samples — wallet features → profitable/unprofitable

        Features extracted:
          - tx_count: total transactions in period
          - swap_ratio: % of txs that are swaps
          - avg_hold_time_hours: average token holding time
          - win_rate: % of trades with positive PnL
          - avg_roi: average return per trade
          - unique_tokens: number of distinct tokens traded
          - max_single_trade_sol: largest trade size
          - activity_hours: hour-of-day distribution entropy
        """
        samples = []
        for w in wallets:
            txs = w.get("transactions", [])
            if not txs:
                continue

            # Feature extraction
            swap_count = sum(1 for t in txs if t.get("tx_type") == "swap")
            total = len(txs)

            features = {
                "tx_count": float(total),
                "swap_ratio": swap_count / max(1, total),
                "avg_hold_time_hours": w.get("avg_hold_time", 0),
                "win_rate": w.get("win_rate", 0),
                "avg_roi": w.get("avg_roi", 0),
                "unique_tokens": float(w.get("unique_tokens", 0)),
                "max_single_trade_sol": w.get("max_trade_sol", 0),
                "total_volume_sol": w.get("total_volume", 0),
                "age_days": w.get("age_days", 0),
            }

            # Label based on profitability
            pnl = w.get("total_pnl", 0)
            label = "profitable" if pnl > 0 else "unprofitable"

            sample = LabeledSample(
                sample_id=w.get("address", "")[:12],
                features=features,
                label=label,
                confidence=min(1.0, total / 50),  # more txs = higher confidence
                metadata={"address": w.get("address"), "pnl": pnl},
            )
            samples.append(sample)

        self._samples.extend(samples)
        logger.info(f"Built wallet scoring dataset: {len(samples)} samples")
        return samples

    async def build_signal_quality_dataset(self, signals: list[dict]) -> list[LabeledSample]:
        """
        INPUT:  Historical signals with outcomes
        OUTPUT: Labeled samples — signal features → alpha/noise

        Features:
          - confidence: original signal confidence
          - wallets_involved: how many wallets in the signal
          - volume_spike_ratio: volume vs 7-day average
          - time_since_launch_hours: token age
          - holder_concentration: top 10 holder %
        """
        samples = []
        for s in signals:
            outcome = s.get("outcome", {})
            actual_roi = outcome.get("roi", 0)

            features = {
                "confidence": s.get("confidence", 0),
                "wallets_involved": float(s.get("wallets_involved", 0)),
                "volume_spike_ratio": s.get("volume_spike", 1.0),
                "time_since_launch_hours": s.get("token_age_hours", 0),
                "holder_concentration": s.get("top10_holder_pct", 0),
                "liquidity_usd": s.get("liquidity", 0),
                "market_cap_usd": s.get("market_cap", 0),
            }

            label = "alpha" if actual_roi > 0.2 else "noise"

            sample = LabeledSample(
                sample_id=s.get("signal_id", "")[:12],
                features=features,
                label=label,
                metadata={"token": s.get("token"), "actual_roi": actual_roi},
            )
            samples.append(sample)

        self._samples.extend(samples)
        logger.info(f"Built signal quality dataset: {len(samples)} samples")
        return samples

    def train_test_split(self, test_ratio: float = 0.2) -> tuple[list[LabeledSample], list[LabeledSample]]:
        """Split collected samples into train/test sets."""
        import random
        shuffled = list(self._samples)
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * (1 - test_ratio))
        return shuffled[:split_idx], shuffled[split_idx:]

    def export_json(self, filename: str = "dataset.json"):
        """Export dataset as JSON."""
        path = self._output_dir / filename
        data = [
            {
                "id": s.sample_id,
                "features": s.features,
                "label": s.label,
                "confidence": s.confidence,
            }
            for s in self._samples
        ]
        path.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported {len(data)} samples to {path}")
        return str(path)

    def get_stats(self) -> dict:
        """Dataset statistics."""
        if not self._samples:
            return {"total": 0}

        labels = {}
        for s in self._samples:
            labels[s.label] = labels.get(s.label, 0) + 1

        return {
            "total_samples": len(self._samples),
            "label_distribution": labels,
            "avg_confidence": sum(s.confidence for s in self._samples) / len(self._samples),
            "feature_count": len(self._samples[0].features) if self._samples else 0,
        }
