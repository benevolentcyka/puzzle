"""Fault-injection and native Windows-lock tests of checkpoint durability."""
import ctypes
import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import checkpoint_io as io


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'wattpad-paragraphs.json').write_bytes(b'["fixture"]')
        (self.root / 'generator.py').write_bytes(b'# fixture')
        config = dict(family='joint-observed-formatting-v1', indices=[0],
                      source_sha256=hashlib.sha256(b'["fixture"]').hexdigest(),
                      code_sha256={'generator.py': hashlib.sha256(b'# fixture').hexdigest()})
        tag = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
        self.path = self.root / f'joint-format-{tag}.json'
        self.old = dict(configuration=config, next_rank=10, candidates_total=100, derived_addresses=10,
                        complete=False, matches=[], elapsed_search_seconds=1.0, sampled_cpu_comparisons=3)
        self.new = dict(self.old, next_rank=20, derived_addresses=20, elapsed_search_seconds=2.0, sampled_cpu_comparisons=6)
        io.atomic_json(self.path, self.old)

    def test_transient_access_denial_retries(self):
        real_replace = os.replace
        attempts = []

        def fail_then_succeed(source, destination):
            attempts.append(1)
            if len(attempts) < 4:
                raise PermissionError(13, 'injected access denial')
            return real_replace(source, destination)

        with patch.object(io.os, 'replace', side_effect=fail_then_succeed), patch.object(io.time, 'sleep'):
            io.atomic_json(self.path, self.new)
        self.assertEqual(len(attempts), 4)
        self.assertEqual(json.loads(self.path.read_bytes()), self.new)
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_persistent_denial_preserves_main_and_recovers_pending(self):
        with patch.object(io.os, 'replace', side_effect=PermissionError(13, 'injected persistent lock')):
            with self.assertRaises(PermissionError):
                io.atomic_json(self.path, self.new, timeout=0)
        self.assertEqual(json.loads(self.path.read_bytes()), self.old)
        pending = list(self.root.glob('*.pending-*.tmp'))
        self.assertEqual(len(pending), 1)
        self.assertEqual(json.loads(pending[0].read_bytes()), self.new)
        report = io.recover_pending(self.path, self.root)
        self.assertEqual(report['recovered_rank'], 20)
        self.assertEqual(json.loads(self.path.read_bytes()), self.new)
        self.assertTrue((self.root / 'checkpoint-recovery').is_dir())

    def test_recovers_original_writer_temporary_file(self):
        self.path.with_suffix('.json.tmp').write_text(json.dumps(self.new))
        io.recover_pending(self.path, self.root)
        self.assertEqual(json.loads(self.path.read_bytes()), self.new)

    def test_corrupt_and_inconsistent_pending_are_not_promoted(self):
        bad = self.path.with_suffix('.json.tmp')
        for contents in ['{"broken":', json.dumps(dict(self.new, derived_addresses=99)),
                         json.dumps(dict(self.new, complete=True)), json.dumps(dict(self.new, sampled_cpu_comparisons=0))]:
            bad.write_text(contents)
            self.assertIsNone(io.recover_pending(self.path, self.root))
            self.assertEqual(json.loads(self.path.read_bytes()), self.old)
            self.assertTrue(bad.exists())

    def test_stale_pending_does_not_regress(self):
        self.path.write_text(json.dumps(self.new))
        self.path.with_suffix('.json.tmp').write_text(json.dumps(self.old))
        self.assertIsNone(io.recover_pending(self.path, self.root))
        self.assertEqual(json.loads(self.path.read_bytes()), self.new)

    def test_fingerprint_mismatch_is_refused(self):
        self.path.with_suffix('.json.tmp').write_text(json.dumps(self.new))
        (self.root / 'generator.py').write_bytes(b'# changed')
        with self.assertRaises(ValueError):
            io.recover_pending(self.path, self.root)
        self.assertEqual(json.loads(self.path.read_bytes()), self.old)

    def test_same_rank_conflict_is_refused(self):
        self.path.with_suffix('.json.tmp').write_text(json.dumps(self.new))
        other = self.path.parent / (self.path.name + '.pending-conflict.tmp')
        other.write_text(json.dumps(dict(self.new, elapsed_search_seconds=5.0)))
        with self.assertRaises(ValueError):
            io.recover_pending(self.path, self.root)
        self.assertEqual(json.loads(self.path.read_bytes()), self.old)

    @unittest.skipUnless(os.name == 'nt', 'Native Windows file-sharing test')
    def test_actual_windows_no_delete_share_lock(self):
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes, close.restype = [wintypes.HANDLE], wintypes.BOOL
        # Read access and read/write sharing, deliberately omit FILE_SHARE_DELETE.
        handle = create(str(self.path), 0x80000000, 3, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            self.fail(f'CreateFileW failed: {ctypes.get_last_error()}')
        release = threading.Timer(0.2, lambda: close(handle))
        release.start()
        try:
            io.atomic_json(self.path, self.new, timeout=5)
        finally:
            release.join()
        self.assertEqual(json.loads(self.path.read_bytes()), self.new)


if __name__ == '__main__':
    unittest.main(verbosity=2)
