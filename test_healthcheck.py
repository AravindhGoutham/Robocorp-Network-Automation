#!/usr/bin/env python3

import unittest
import os
from unittest.mock import patch
import healthcheck

class TestYamlFile(unittest.TestCase):

    def test_yaml_file_exists(self):
        self.assertTrue(os.path.exists("devices.yaml"), "devices.yaml file is missing!")

    @patch("os.path.exists", return_value=False)
    def test_yaml_file_not_found(self, mock_exists):
        result = healthcheck.run_health_check("10.0.0.1")
        self.assertIn("not found", result)

if __name__ == "__main__":
    unittest.main()
