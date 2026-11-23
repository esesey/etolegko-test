import argparse
import asyncio
import sys
import time

import aiohttp


async def fetch_once(session, url, timeout):
    start = time.perf_counter()
    total = 0
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
        resp.raise_for_status()
        async for chunk in resp.content.iter_chunked(64 * 1024):
            total += len(chunk)
    elapsed = time.perf_counter() - start
    return total, elapsed


async def run(url, requests_count, timeout):
    total_bytes = 0
    total_time = 0.0
    async with aiohttp.ClientSession() as session:
        for i in range(1, requests_count + 1):
            n_bytes, elapsed = await fetch_once(session, url, timeout)
            total_bytes += n_bytes
            total_time += elapsed
            print(f"[{i}/{requests_count}] {n_bytes} байт за {elapsed:.3f}с", file=sys.stderr)
    avg_time = total_time / requests_count
    speed = total_bytes / total_time if total_time > 0 else 0.0
    return total_bytes, total_time, avg_time, speed


def human_bytes(n):
    for unit in ("Б", "Кб", "Мб", "Гб"):
        if n < 1024 or unit == "Гб":
            return f"{n:.2f} {unit}" if unit != "Б" else f"{int(n)} Б"
        n /= 1024


def main():
    parser = argparse.ArgumentParser(description="Sequential download test")
    parser.add_argument("url")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    try:
        total_bytes, total_time, avg_time, speed = asyncio.run(
            run(args.url, args.requests, args.timeout)
        )
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 1
    except asyncio.TimeoutError:
        print("Request timed out", file=sys.stderr)
        return 1

    print(f"Запросов: {args.requests}")
    print(f"Всего байтов: {human_bytes(total_bytes)}")
    print(f"Всего времени: {total_time:.3f}с")
    print(f"Среднее время запроса: {avg_time:.3f}с")
    print(f"Скорость загрузки: {human_bytes(speed)}/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())