import grpc
from threading import Lock
from typing import Dict, Optional

class ConnectionPool:
    """
    A class to manage a pool of gRPC connections.
    """
    def __init__(self, use_connection_pool: bool):
        """
        Initializes the connection pool with the option to use it or not.
        """
        self.mu = Lock()  # Lock for synchronization
        self.connections: Dict[str, grpc.ClientConn] = {}  # Dictionary to store connections
        self.use_connection_pool = use_connection_pool

    def get_connection(self, target: str) -> Optional[grpc.ClientConn]:
        """
        Retrieves a gRPC connection from the pool, or creates a new one if it doesn't exist.
        """
        if not self.use_connection_pool:
            return None  # If not using a connection pool, return None

        with self.mu:  # Ensures thread safety while accessing the connections map
            if target in self.connections:
                return self.connections[target]  # Return existing connection
            else:
                # Create a new connection
                conn = grpc.insecure_channel(target)
                self.connections[target] = conn  # Store in the pool
                return conn

    def close(self):
        """
        Closes all connections in the pool.
        """
        with self.mu:
            for conn in self.connections.values():
                conn.close()
            self.connections.clear()  # Clear the pool after closing all connections
