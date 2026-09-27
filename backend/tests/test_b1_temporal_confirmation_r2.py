"""Local lifecycle checks only; no live or browser acceptance inferred."""
import tempfile
import unittest
from pathlib import Path
from sandbox.read_b1_temporal_confirmation_r2 import previous_windows


class PredecessorTests(unittest.TestCase):
    def test_all_predecessors_required_and_snapshot_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = ('b1-r5-independent-read', 'b1-r5-temporal-read',
                     'b1-r5-temporal-confirmation')
            for name in names:
                with self.assertRaises((OSError, ValueError)):
                    previous_windows(root)
                (root / (name + '.started')).write_text('READ_ONLY_SINGLE_WINDOW\n')
                (root / (name + '.closed')).write_text('CLOSED_NO_AUTOMATIC_RESTART\n')
            before = previous_windows(root)
            self.assertEqual(len(before), 6)
            self.assertEqual(before, previous_windows(root))
            last = root / (names[-1] + '.closed')
            last.write_text('OPEN')
            with self.assertRaises(ValueError):
                previous_windows(root)
            last.write_text('CLOSED_NO_AUTOMATIC_RESTART\n\n')
            self.assertNotEqual(before, previous_windows(root))


if __name__ == '__main__':
    unittest.main()
