"""Opt-in integration checks; never run against a runtime by default."""
import os
import unittest

from oktopai.runtimes.ollama import OllamaRuntime

@unittest.skipUnless(os.getenv("OKTOPAI_LIVE_TESTS") == "1", "set OKTOPAI_LIVE_TESTS=1 to require a running Ollama daemon")
class OllamaIntegrationTests(unittest.TestCase):
    def test_ollama_lists_models(self):
        self.assertIsInstance(OllamaRuntime().list_models(), list)

