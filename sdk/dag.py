import ipfshttpclient
from ipfshttpclient.exceptions import ErrorResponse
from typing import Optional
import hashlib

class DAGRoot:
    """
    A helper class to build a root CID from chunks.
    """
    def __init__(self, node: Optional[bytes] = None, fs_node: Optional[bytes] = None):
        """
        Initializes a DAGRoot object with the provided node and filesystem node.
        """
        self.node = node  # Represents the ProtoNode in Go
        self.fs_node = fs_node  # Represents the FSNode in Go

    def build_cid(self) -> str:
        """
        Builds a CID from the stored data (node or fs_node).
        """
        if self.node:
            return self._build_cid_from_node(self.node)
        elif self.fs_node:
            return self._build_cid_from_node(self.fs_node)
        else:
            raise ValueError("Neither node nor fs_node provided to build CID.")

    def _build_cid_from_node(self, node_data: bytes) -> str:
        """
        Helper method to build CID from the node data.
        This could involve hashing and CID generation.
        """
        # Here we use SHA256 as an example, as Go uses hashing to build CIDs
        cid = hashlib.sha256(node_data).hexdigest()
        return cid


class IPFSClient:
    """
    A simplified interface for interacting with an IPFS node.
    """
    def __init__(self, host: str = 'localhost', port: int = 5001):
        """
        Initializes the IPFSClient to interact with an IPFS node.
        """
        self.client = ipfshttpclient.connect(f'/dns/{host}/tcp/{port}/http')

    def add_file(self, file_data: bytes) -> str:
        """
        Adds a file to the IPFS node and returns its CID.
        """
        try:
            response = self.client.add_bytes(file_data)
            return response['Hash']
        except ErrorResponse as e:
            raise RuntimeError(f"Error adding file to IPFS: {str(e)}")

    def get_file(self, cid: str) -> bytes:
        """
        Retrieves a file from the IPFS node using its CID.
        """
        try:
            return self.client.cat(cid)
        except ErrorResponse as e:
            raise RuntimeError(f"Error retrieving file from IPFS: {str(e)}")
