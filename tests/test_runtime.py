"""Run locks and Linux child-tree cleanup must work independently of zeta."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/2026-09-09-gpu-wide-survey'))
import wide_common
import run_pipeline


class Runtime(unittest.TestCase):
    def test_same_run_has_exclusive_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = wide_common.HERE
            try:
                wide_common.HERE = Path(tmp)
                with wide_common.lock('test.lock'):
                    with self.assertRaises(OSError):
                        with wide_common.lock('test.lock'):
                            self.fail('Duplicate owner acquired run lock')
                with wide_common.lock('test.lock'):
                    pass
            finally:
                wide_common.HERE = original

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux process-group cleanup')
    def test_stage_termination_cleans_descendant(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = Path(tmp) / 'grandchild.pid'
            code = ('import subprocess,sys,time,pathlib; '
                    'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
                    'pathlib.Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)')
            child = subprocess.Popen([sys.executable, '-c', code, str(pid_file)], start_new_session=True)
            try:
                deadline = time.monotonic() + 5
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(pid_file.exists())
                descendant = int(pid_file.read_text())
                run_pipeline.terminate(child)
                self.assertIsNotNone(child.poll())
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    proc = Path(f'/proc/{descendant}/stat')
                    if not proc.exists() or proc.read_text().split(') ', 1)[1][0] == 'Z':
                        break
                    time.sleep(.05)
                else:
                    self.fail('Descendant survived stage termination')
            finally:
                run_pipeline.terminate(child)


if __name__ == '__main__':
    unittest.main()
