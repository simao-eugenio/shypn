
# Example test for ExampleAPI
import unittest
from shypn.api.example_api import ExampleAPI

class TestExampleAPI(unittest.TestCase):
    def test_greet(self):
        api = ExampleAPI("TestAPI")
        self.assertEqual(api.greet(), "Hello from TestAPI!")

if __name__ == "__main__":
    unittest.main()
