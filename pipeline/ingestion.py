"""
Data Ingestion Pipeline — real-time on-chain data collection.

Clear I/O:
  INPUT:  Solana RPC WebSocket stream, Helius webhooks, DexScreener API
  OUTPUT: Normalized transaction records → MessageBus + SQLite

This is the data source for all downstream agents and heads.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
from typing import Any
from dataclasses import dataclass, field

import aiohttp

from config import SOLANA_RPC_URL, HELIUS_API_KEY

logger = logging.getLogger("hydranet.pipeline.ingestion")


@dataclass
class NormalizedTx:
    """Standardized transaction record — the universal data unit."""
    signature: str
    wallet: str
    tx_type: str  # "swap" | "transfer" | "lp_add" | "lp_remove" | "mint" | "unknown"
    token_in: str | None = None
    token_out: str | None = None
    amount_in: float = 0.0
    amount_out: float = 0.0
    amount_usd: float = 0.0
    program: str = ""
    timestamp: float = field(default_factory=time.time)
    block_slot: int = 0
    success: bool = True
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "signature": self.signature,
            "wallet": self.wallet,
            "tx_type": self.tx_type,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount_in": self.amount_in,
            "amount_out": self.amount_out,
            "amount_usd": self.amount_usd,
            "program": self.program,
            "timestamp": self.timestamp,
            "block_slot": self.block_slot,
            "success": self.success,
        }


class IngestionPipeline:
    """
    Collects, normalizes, and emits on-chain transactions.

    Data flow:
      Solana RPC / Helius → parse → normalize → emit to bus + store in DB
    """

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._running = False
        self._buffer: asyncio.Queue[NormalizedTx] = asyncio.Queue(maxsize=10000)
        self._stats = {
            "total_ingested": 0,
            "swaps": 0,
            "transfers": 0,
            "errors": 0,
            "started_at": 0.0,
        }
        self._watched_wallets: set[str] = set()
        self._on_tx_callbacks: list = []

    @property
    def stats(self) -> dict:
        elapsed = time.time() - self._stats["started_at"] if self._stats["started_at"] else 0
        return {
            **self._stats,
            "buffer_size": self._buffer.qsize(),
            "watched_wallets": len(self._watched_wallets),
            "tx_per_second": self._stats["total_ingested"] / max(1, elapsed),
        }

    def watch_wallet(self, address: str):
        self._watched_wallets.add(address)

    def on_transaction(self, callback):
        self._on_tx_callbacks.append(callback)

    async def start(self):
        self._running = True
        self._stats["started_at"] = time.time()
        self._session = aiohttp.ClientSession()
        logger.info(f"Ingestion pipeline started, watching {len(self._watched_wallets)} wallets")

    async def stop(self):
        self._running = False
        if self._session:
            await self._session.close()

    async def poll_wallet(self, address: str, limit: int = 10) -> list[NormalizedTx]:
        """Poll recent transactions for a specific wallet."""
        if not self._session:
            return []

        txs = []

        if HELIUS_API_KEY:
            txs = await self._fetch_helius(address, limit)
        else:
            txs = await self._fetch_rpc(address, limit)

        for tx in txs:
            self._stats["total_ingested"] += 1
            if tx.tx_type == "swap":
                self._stats["swaps"] += 1
            elif tx.tx_type == "transfer":
                self._stats["transfers"] += 1

            for cb in self._on_tx_callbacks:
                try:
                    await cb(tx)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        return txs

    async def poll_all_watched(self) -> list[NormalizedTx]:
        """Poll all watched wallets."""
        all_txs = []
        for addr in list(self._watched_wallets):
            try:
                txs = await self.poll_wallet(addr, limit=5)
                all_txs.extend(txs)
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Poll error for {addr[:8]}: {e}")
        return all_txs

    async def _fetch_helius(self, address: str, limit: int) -> list[NormalizedTx]:
        """Fetch parsed transactions from Helius API."""
        url = f"https://api.helius.xyz/v0/addresses/{address}/transactions"
        params = {"api-key": HELIUS_API_KEY, "limit": limit}

        try:
            async with self._session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [self._normalize_helius_tx(tx, address) for tx in data]
        except Exception as e:
            logger.error(f"Helius fetch error: {e}")
            return []

    async def _fetch_rpc(self, address: str, limit: int) -> list[NormalizedTx]:
        """Fetch transaction signatures from Solana RPC (basic fallback)."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": limit}],
        }
        try:
            async with self._session.post(SOLANA_RPC_URL, json=payload) as resp:
                data = await resp.json()
                sigs = data.get("result", [])
                return [
                    NormalizedTx(
                        signature=s.get("signature", ""),
                        wallet=address,
                        tx_type="unknown",
                        timestamp=s.get("blockTime", time.time()),
                        block_slot=s.get("slot", 0),
                        success=s.get("err") is None,
                    )
                    for s in sigs
                ]
        except Exception as e:
            logger.error(f"RPC fetch error: {e}")
            return []

    def _normalize_helius_tx(self, raw: dict, wallet: str) -> NormalizedTx:
        """Convert Helius parsed transaction to NormalizedTx."""
        tx_type = raw.get("type", "unknown").lower()

        # Map Helius types to our types
        type_map = {
            "swap": "swap",
            "transfer": "transfer",
            "create_account": "transfer",
            "add_liquidity": "lp_add",
            "remove_liquidity": "lp_remove",
        }
        normalized_type = type_map.get(tx_type, "unknown")

        token_transfers = raw.get("tokenTransfers", [])
        token_in = token_out = None
        amount_in = amount_out = 0.0

        for tt in token_transfers:
            if tt.get("toUserAccount") == wallet:
                token_in = tt.get("mint")
                amount_in = float(tt.get("tokenAmount", 0))
            elif tt.get("fromUserAccount") == wallet:
                token_out = tt.get("mint")
                amount_out = float(tt.get("tokenAmount", 0))

        return NormalizedTx(
            signature=raw.get("signature", ""),
            wallet=wallet,
            tx_type=normalized_type,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            amount_out=amount_out,
            program=raw.get("source", ""),
            timestamp=raw.get("timestamp", time.time()),
            block_slot=raw.get("slot", 0),
            success=not raw.get("transactionError"),
            raw=raw,
        )
