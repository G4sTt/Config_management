"""Validate interpretation of the independent cargo tree output."""

import unittest

from comparison import parse_cargo_tree


class ComparisonTests(unittest.TestCase):
    """Check parsing of native Cargo dependency trees."""
    def test_depth_prefix_and_multiple_versions(self):
        """Verify depth prefix and multiple versions."""
        nodes, edges = parse_cargo_tree(
            "0root v1.0.0\n1child v1.0.0\n2leaf v1.0.0\n1leaf v2.0.0\n"
        )
        self.assertEqual(len(nodes), 4)
        self.assertIn(("root@1.0.0", "leaf@2.0.0"), edges)
        self.assertIn(("child@1.0.0", "leaf@1.0.0"), edges)

    def test_corrupt_native_output(self):
        """Verify corrupt native output."""
        for text in ("unexpected text", "2missing v1.0.0"):
            with self.assertRaises(ValueError):
                parse_cargo_tree(text)


if __name__ == "__main__":
    unittest.main()
