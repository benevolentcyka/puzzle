"""Atomic checkpoint saves resilient to temporary Windows sharing violations.

The current checkpoint is never truncated or deleted. A flushed unique pending
file survives a failed replacement and can be validated/recovered on restart.
Recovery must be called while holding the search's existing exclusive lock.
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path


def replace_with_retry(source, destination, timeout=30.0):
    deadline = time.monotonic() + timeout
    delay, failures = 0.05, 0
    while True:
        try:
            os.replace(source, destination)
            return failures
        except OSError as error:
            retryable = isinstance(error, PermissionError) or getattr(error, 'winerror', None) in {5, 32, 33} or error.errno in {errno.EACCES, errno.EPERM, errno.EBUSY}
            if not retryable:
                raise
            failures += 1
            if failures == 1:
                print(f'Checkpoint replacement is temporarily denied; retrying for up to {timeout:g}s. Pending data: {Path(source).name}', flush=True)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PermissionError(f'Checkpoint replacement stayed unavailable. Completed-batch data is preserved in {source}. Rerun resume.py after the file becomes available.') from error
            time.sleep(min(delay, remaining))
            delay = min(1.0, delay * 2)


def atomic_json(path, value, timeout=30.0):
    path = Path(path)
    payload = (json.dumps(value, indent=2) + '\n').encode('utf8')
    # A unique name preserves any earlier pending save, including the original
    # writer's .json.tmp file. An interrupted write cannot corrupt the main file.
    with tempfile.NamedTemporaryFile(mode='wb', prefix=path.name + '.pending-', suffix='.tmp',
                                     dir=path.parent, delete=False) as handle:
        pending = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    replace_with_retry(pending, path, timeout)


def validate_checkpoint(path, destination, root):
    """Validate recorded identity/progress, not replay the underlying search."""
    state = json.loads(Path(path).read_bytes())
    configuration = state['configuration']
    tag = hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()[:16]
    if Path(destination).name != f'joint-format-{tag}.json':
        raise ValueError('configuration fingerprint does not match destination')
    if configuration['family'] != 'joint-observed-formatting-v1':
        raise ValueError('not a joint-format checkpoint')
    root = Path(root).resolve()
    for name, digest in configuration['code_sha256'].items():
        file = (root / name).resolve()
        if not file.is_relative_to(root) or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise ValueError(f'code fingerprint mismatch: {name}')
    if hashlib.sha256((root / 'wattpad-paragraphs.json').read_bytes()).hexdigest() != configuration['source_sha256']:
        raise ValueError('source fingerprint mismatch')
    rank, total, count = state['next_rank'], state['candidates_total'], state['derived_addresses']
    if any(type(x) is not int for x in [rank, total, count]) or not 0 <= rank <= total:
        raise ValueError('invalid rank/count')
    if count != rank * len(configuration['indices']) or type(state['complete']) is not bool or state['complete'] != (rank == total):
        raise ValueError('inconsistent address count/completion')
    if not isinstance(state['matches'], list):
        raise ValueError('invalid matches record')
    if state['elapsed_search_seconds'] < 0 or state['sampled_cpu_comparisons'] < 0:
        raise ValueError('invalid timing/comparison record')
    return state


def recover_pending(destination, root, timeout=30.0):
    destination = Path(destination)
    primary = validate_checkpoint(destination, destination, root) if destination.exists() else None
    candidates = []
    legacy = destination.with_suffix(destination.suffix + '.tmp')
    pending = ([legacy] if legacy.exists() else []) + sorted(destination.parent.glob(destination.name + '.pending-*.tmp'))
    for path in pending:
        try:
            state = validate_checkpoint(path, destination, root)
            if primary is not None:
                if state['configuration'] != primary['configuration'] or state['candidates_total'] != primary['candidates_total']:
                    raise ValueError('pending save belongs to different configuration/count')
                if state['next_rank'] <= primary['next_rank']:
                    continue
                if state['elapsed_search_seconds'] < primary['elapsed_search_seconds'] or state['sampled_cpu_comparisons'] < primary['sampled_cpu_comparisons']:
                    raise ValueError('pending counters regress')
                if any(match not in state['matches'] for match in primary['matches']):
                    raise ValueError('pending save loses an earlier match')
            candidates.append((state['next_rank'], path, state))
        except (ValueError, KeyError, TypeError, OSError) as error:
            print(f'Leaving unverified pending file untouched: {path.name} ({type(error).__name__}: {error})', flush=True)
    if not candidates:
        return None
    _, path, state = max(candidates, key=lambda item: item[0])
    # Refuse ambiguous states at the same rank instead of choosing arbitrarily.
    for rank, other_path, other_state in candidates:
        if rank == state['next_rank'] and other_state != state:
            raise ValueError(f'Conflicting pending checkpoints at rank {rank}: {path.name}, {other_path.name}')
    report = dict(recovered_from=path.name, previous_rank=primary['next_rank'] if primary else 0,
                  recovered_rank=state['next_rank'], candidates_total=state['candidates_total'],
                  pending_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  previous_sha256=hashlib.sha256(destination.read_bytes()).hexdigest() if primary else None,
                  configuration_sha256=hashlib.sha256(json.dumps(state['configuration'], sort_keys=True).encode()).hexdigest())
    # Preserve both exact records as evidence before replacing the checkpoint.
    evidence = destination.parent / 'checkpoint-recovery'
    evidence.mkdir(exist_ok=True)
    for name, item in [('previous', primary), ('recovered', state)]:
        if item is not None:
            backup = evidence / f'{destination.stem}-{name}-{item["next_rank"]}.json'
            if not backup.exists():
                atomic_json(backup, item, timeout)
    atomic_json(evidence / f'{destination.stem}-recovery-{state["next_rank"]}.json', report, timeout)
    replace_with_retry(path, destination, timeout)
    print(f'Recovered checked progress: {report["previous_rank"]:,} -> {state["next_rank"]:,}; no completed batches discarded.', flush=True)
    return report
