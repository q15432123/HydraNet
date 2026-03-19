"""
Solana Client — on-chain data fetcher for wallet intelligence.

Fetches wallet transactions, token balances, and DEX activity
from Solana RPC and Helius API.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from config import SOLANA_RPC_URL, HELIUS_API_KEY

logger = logging.getLogger("hydranet.solana")


class SolanaClient:
    """Async Solana RPC + Helius API client."""

    def __init__(self):
        self._rpc_url = SOLANA_RPC_URL
        self._helius_key = HELIUS_API_KEY
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rpc_call(self, method: str, params: list | None = None) -> Any:
        session = await self._get_session()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        async with session.post(self._rpc_url, json=payload) as resp:
            data = await resp.json()
            if "error" in data:
                logger.error(f"RPC error: {data['error']}")
                return None
            return data.get("result")

    async def get_balance(self, address: str) -> float | None:
        """Get SOL balance in SOL (not lamports)."""
        result = await self._rpc_call("getBalance", [address])
        if result and "value" in result:
            return result["value"] / 1e9
        return None

    async def get_signatures(self, address: str, limit: int = 20) -> list[dict]:
        """Get recent transaction signatures for a wallet."""
        result = await self._rpc_call(
            "getSignaturesForAddress",
            [address, {"limit": limit}],
        )
        return result or []

    async def get_transaction(self, signature: str) -> dict | None:
        """Get full transaction details."""
        result = await self._rpc_call(
            "getTransaction",
            [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        )
        return result

    async def get_token_accounts(self, address: str) -> list[dict]:
        """Get all token accounts for a wallet."""
        result = await self._rpc_call(
            "getTokenAccountsByOwner",
            [
                address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )
        if result and "value" in result:
            accounts = []
            for item in result["value"]:
                info = item.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                accounts.append({
                    "mint": info.get("mint"),
                    "amount": float(info.get("tokenAmount", {}).get("uiAmount", 0)),
                    "decimals": info.get("tokenAmount", {}).get("decimals", 0),
                })
            return accounts
        return []

    async def get_wallet_history(self, address: str, limit: int = 50) -> list[dict]:
        """Get parsed transaction history using Helius (if available)."""
        if not self._helius_key:
            # Fallback to basic RPC
            return await self.get_signatures(address, limit)

        session = await self._get_session()
        url = f"https://api.helius.xyz/v0/addresses/{address}/transactions"
        params = {"api-key": self._helius_key, "limit": limit}

        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Helius error: {resp.status}")
                return []
        except Exception as e:
            logger.error(f"Helius request failed: {e}")
            return []

    async def get_token_price(self, mint: str) -> dict | None:
        """Get token price from DexScreener."""
        session = await self._get_session()
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"

        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # DexScreener returns list directly
                    pairs = data if isinstance(data, list) else data.get("pairs", [])
                    if pairs:
                        top = pairs[0]
                        return {
                            "price_usd": float(top.get("priceUsd", 0)),
                            "price_sol": float(top.get("priceNative", 0)),
                            "liquidity": top.get("liquidity", {}).get("usd", 0),
                            "volume_24h": top.get("volume", {}).get("h24", 0),
                            "pair": top.get("pairAddress"),
                        }
        except Exception as e:
            logger.error(f"DexScreener error: {e}")
        return None
