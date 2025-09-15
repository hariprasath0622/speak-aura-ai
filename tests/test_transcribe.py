"""
Unit tests for the transcription functionality.
"""

import unittest
from src.bigquery_utils import transcribe_audio
from src.config import PROJECT_ID, DATASET_ID

class TestTranscription(unittest.TestCase):
    def setUp(self):
        # Set up test data if needed
        pass
        
    def test_transcribe_audio(self):
        # Get transcription results
        results = transcribe_audio()
        
        # Basic validation
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 0)
        self.assertTrue('uri' in results.columns)
        self.assertTrue('transcript' in results.columns)

if __name__ == '__main__':
    unittest.main()
