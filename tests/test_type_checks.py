"""
Runs the statically type-checked usage examples, so that code pyright
accepts is also guaranteed to work at runtime.
"""

import unittest

from tests.type_checks import accepted


class AcceptedUsageRunsTests(unittest.TestCase):
    def test_accepted_usage_runs(self):
        accepted.run()


if __name__ == "__main__":
    unittest.main()
