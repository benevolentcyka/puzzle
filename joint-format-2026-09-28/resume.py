"""Run the unchanged joint-format search with recoverable Windows-safe saves.

Only the I/O writer and locked startup recovery are adapted. All arguments go
to search.py. Keeping that exact search file unchanged preserves its candidate
identity and the user's existing checkpoint. The writer identity is recorded
as execution metadata, outside the unchanged search configuration.
"""
import contextlib
import hashlib
import importlib.util
from pathlib import Path

import checkpoint_io

HERE = Path(__file__).resolve().parent
EXPECTED_SEARCH_SHA256 = '8b83d66cd026cdc56045c128ce652d89c714f4972ae198fdb1ddb05b63176fb9'


def main():
    source = HERE / 'search.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_SEARCH_SHA256:
        raise RuntimeError('search.py changed; audit launcher compatibility before resuming old progress')
    spec = importlib.util.spec_from_file_location('unchanged_joint_search', source)
    search = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(search)
    original_support, original_lock = search.load_wallet_support, search.exclusive
    writer_identity = dict(mode='unique-pending-file-fsync-retry-and-validated-recovery-v1',
        code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [Path(__file__), HERE / 'checkpoint_io.py']})

    def write(path, value):
        if value.get('configuration', {}).get('family') == 'joint-observed-formatting-v1':
            value = dict(value, checkpoint_writer=writer_identity)
        checkpoint_io.atomic_json(path, value)

    def support():
        module = original_support()
        module.CERT.atomic_json = write
        return module

    @contextlib.contextmanager
    def locked_recovery(path):
        with original_lock(path):
            checkpoint_io.recover_pending(path.with_suffix('.json'), search.ROOT)
            yield

    search.load_wallet_support = support
    search.exclusive = locked_recovery
    print('Resilient checkpoint writer enabled; candidate generator and checkpoint identity unchanged.', flush=True)
    search.main()


if __name__ == '__main__':
    main()
