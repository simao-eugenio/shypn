# Example test for helpers
import unittest
from shypn.helpers.example_helper import add

class TestHelpers(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
