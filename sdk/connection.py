import grpc
import time
import threading
from typing import Dict, Optional, Tuple, Callable
from private.pb import nodeapi_pb2_grpc, ipcnodeapi_pb2_grpc


class ConnectionPool:
    def __init__(self, retries=3, delay=1):
        self._lock = threading.RLock()
        self._connections = {}
        self.retries = retries
        self.delay = delay

    def _retry_with_backoff(self, func, *args, **kwargs):
        current_retry = 0
        current_delay = self.delay
        last_exception = None
        
        while current_retry < self.retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                current_retry += 1
                if current_retry >= self.retries:
                    break
                print(f"Attempt {current_retry} failed: {e}. Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                current_delay *= 2
        
        raise last_exception if last_exception else Exception("All retry attempts failed")

    def create_client(self, addr: str, pooled: bool):
        def _create():
            if not addr or not addr.strip():
                raise Exception("Invalid address: empty or None")
                
            if pooled:
                conn = self._get_connection(addr)
                if conn is None:
                    raise Exception("Failed to get connection from pool")
                return nodeapi_pb2_grpc.NodeAPIStub(conn), None, None

            conn = self._create_new_connection(addr)
            if conn is None:
                raise Exception("Failed to create new connection")
            return nodeapi_pb2_grpc.NodeAPIStub(conn), lambda: conn.close(), None
        
        return self._retry_with_backoff(_create)

    def create_ipc_client(self, addr: str, pooled: bool):
        def _create():
            if not addr or not addr.strip():
                raise Exception("Invalid node address: empty or None")
                
            print(f"Creating IPC client for address: {addr}, pooled: {pooled}")
                
            if pooled:
                conn = self._get_connection(addr)
                if conn is None:
                    raise Exception("Failed to get connection from pool")
                client = ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn)
                return client, None, None

            conn = self._create_new_connection(addr)
            if conn is None:
                raise Exception("Failed to create new connection")
            
            client = ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn)
            closer = lambda: conn.close()
            print(f"Successfully created IPC client for {addr}")
            return client, closer, None
        
        try:
            return self._retry_with_backoff(_create)
        except Exception as e:
            return None, None, f"Failed to get connection: {str(e)}"

    def _get_connection(self, addr: str):
        with self._lock:
            conn = self._connections.get(addr)
            if conn:
                return conn
        
        with self._lock:
            conn = self._connections.get(addr)
            if conn:
                return conn
                
            conn = self._create_new_connection(addr)
            if conn:
                self._connections[addr] = conn
            return conn

    def _create_new_connection(self, addr: str):
        try:
            if not addr or not addr.strip():
                raise Exception("Invalid address")
                
            print(f"Creating new gRPC connection to: {addr}")
            
            conn = grpc.insecure_channel(addr)
            
            try:
                grpc.channel_ready_future(conn).result(timeout=5)
                print(f"gRPC connection established to {addr}")
                return conn
            except grpc.FutureTimeoutError:
                print(f"Warning: Connection to {addr} not ready within timeout, but proceeding")
                return conn  
            except Exception as e:
                print(f"Connection test failed for {addr}: {e}")
                try:
                    conn.close()
                except:
                    pass
                return None
                
        except Exception as e:
            print(f"Failed to create connection to {addr}: {e}")
            return None

    def close(self):
        with self._lock:
            errors = []
            for addr, conn in self._connections.items():
                try:
                    conn.close()
                except Exception as e:
                    errors.append(f"Failed to close connection to {addr}: {e}")
            self._connections.clear()
            
            if errors:
                return Exception("Encountered errors while closing connections: " + ", ".join(errors))
            return None
