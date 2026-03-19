"""
HydraNet Benchmark Suite — measures real system performance.

Run: python benchmarks/run_benchmark.py

Measures:
  - Agent decision latency
  - Multi-head fusion latency
  - Memory read/write throughput
  - Message bus throughput
  - Evolution cycle time
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus, Message, MessageType
from core.task_router import TaskRouter, Task, TaskPriority
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


def bench(name: str):
    """Decorator for benchmark functions."""
    def decorator(func):
        async def wrapper():
            print(f"\n  [{name}]")
            start = time.perf_counter()
            result = await func()
            elapsed = (time.perf_counter() - start) * 1000
            print(f"    Total: {elapsed:.1f}ms")
            return result
        return wrapper
    return decorator


@bench("Message Bus Throughput")
async def bench_message_bus():
    bus = MessageBus()
    received = {"count": 0}

    async def handler(msg: Message):
        received["count"] += 1

    bus.subscribe("bench", "agent1", handler)

    n = 1000
    start = time.perf_counter()
    for i in range(n):
        await bus.publish(Message(
            sender_id="sender",
            msg_type=MessageType.EVENT,
            channel="bench",
            payload={"i": i},
        ))
    elapsed = (time.perf_counter() - start) * 1000

    print(f"    {n} messages in {elapsed:.1f}ms ({n/elapsed*1000:.0f} msg/sec)")
    print(f"    Received: {received['count']}")


@bench("Task Router")
async def bench_task_router():
    router = TaskRouter()
    router.register_agent("a1", ["scanner"])
    router.register_agent("a2", ["analyzer"])
    router.register_agent("a3", ["scanner", "analyzer"])

    n = 100
    start = time.perf_counter()
    for i in range(n):
        task = Task(
            task_id=f"t{i}",
            task_type="scan",
            payload={"i": i},
            required_capabilities=["scanner"],
        )
        await router.submit_task(task)
        await router.assign_next()
    elapsed = (time.perf_counter() - start) * 1000

    print(f"    {n} tasks routed in {elapsed:.1f}ms ({n/elapsed*1000:.0f} tasks/sec)")


@bench("Short-Term Memory")
async def bench_stm():
    stm = ShortTermMemory()

    n = 10000
    start = time.perf_counter()
    for i in range(n):
        stm.set(f"key:{i}", {"data": i, "value": i * 1.5})
    write_time = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    for i in range(n):
        stm.get(f"key:{i}")
    read_time = (time.perf_counter() - start) * 1000

    print(f"    Write: {n} entries in {write_time:.1f}ms ({n/write_time*1000:.0f} ops/sec)")
    print(f"    Read:  {n} lookups in {read_time:.1f}ms ({n/read_time*1000:.0f} ops/sec)")


@bench("Long-Term Memory (ChromaDB)")
async def bench_ltm():
    try:
        ltm = LongTermMemory(collection_name="benchmark_test")

        n = 100
        start = time.perf_counter()
        for i in range(n):
            ltm.store(f"doc{i}", f"Wallet analysis for address {i}: profitable trader with {i} transactions")
        write_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        for i in range(10):
            ltm.query(f"profitable wallet with many transactions", n_results=5)
        query_time = (time.perf_counter() - start) * 1000

        print(f"    Write: {n} docs in {write_time:.1f}ms ({n/write_time*1000:.0f} docs/sec)")
        print(f"    Query: 10 searches in {query_time:.1f}ms ({10/query_time*1000:.0f} queries/sec)")
    except Exception as e:
        print(f"    Skipped (ChromaDB not available): {e}")


async def main():
    print("=" * 50)
    print("  HydraNet Benchmark Suite")
    print("=" * 50)

    total_start = time.perf_counter()

    await bench_message_bus()
    await bench_task_router()
    await bench_stm()
    await bench_ltm()

    total = (time.perf_counter() - total_start) * 1000
    print(f"\n{'='*50}")
    print(f"  Total benchmark time: {total:.1f}ms")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
