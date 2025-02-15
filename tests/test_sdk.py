import unittest
from unittest.mock import MagicMock, patch
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sdk.sdk import SDK, SDKError, BucketCreateResult, Bucket, encryption_key_derivation


class TestSDK(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_conn = MagicMock()

        with patch("private.pb.NodeAPIClient", return_value=self.mock_client):
            self.sdk = SDK(
                address="localhost:50051",
                max_concurrency=5,
                block_part_size=1024,
                use_connection_pool=False,
                encryption_key=b"0123456789abcdef0123456789abcdef",
                private_key="some_private_key",
                streaming_max_blocks_in_chunk=32,
                parity_blocks_count=2
            )

    def test_create_bucket_valid(self):
        mock_response = MagicMock()
        mock_response.name = "test_bucket"
        mock_response.created_at = Timestamp()
        self.mock_client.bucket_create.return_value = mock_response

        result = self.sdk.create_bucket("test_bucket")

        self.assertEqual(result.name, "test_bucket")
        self.assertIsInstance(result.created_at, Timestamp)

    def test_create_bucket_invalid_name(self):
        with self.assertRaises(SDKError):
            self.sdk.create_bucket("ab")  # Less than MIN_BUCKET_NAME_LENGTH

    def test_view_bucket_valid(self):
        mock_response = MagicMock()
        mock_response.name = "test_bucket"
        mock_response.created_at = Timestamp()
        self.mock_client.bucket_view.return_value = mock_response

        result = self.sdk.view_bucket("test_bucket")

        self.assertEqual(result.name, "test_bucket")
        self.assertIsInstance(result.created_at, Timestamp)

    def test_view_bucket_invalid_name(self):
        with self.assertRaises(SDKError):
            self.sdk.view_bucket("")

    def test_delete_bucket(self):
        self.mock_client.bucket_delete.return_value = None

        result = self.sdk.delete_bucket("test_bucket")
        self.assertIsNone(result)

    def test_encryption_key_derivation(self):
        key = encryption_key_derivation(b"parent_key", "info1", "info2")
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)


if __name__ == "__main__":
    unittest.main()
