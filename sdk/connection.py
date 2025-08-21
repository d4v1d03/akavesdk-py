import grpc
import time
import threading
import logging
from typing import Dict, Optional, Tuple, Callable
from private.pb import nodeapi_pb2_grpc, ipcnodeapi_pb2_grpc
from .config import SDKError, MIN_BUCKET_NAME_LENGTH
from .shared.grpc_base import GrpcClientBase

class ConnectionPool(GrpcClientBase):
    def __init__(self, connection_timeout=10, retries=3, delay=1):
        super().__init__(connection_timeout=connection_timeout)
        self._lock = threading.RLock()
        self._connections = {}
        self.retries = retries
        self.delay = delay

    def _retry_with_backoff(self, func, method_name: str, *args, **kwargs):
        current_retry = 0
        current_delay = self.delay
        last_exception = None
        
        while current_retry < self.retries:
            try:
                return func(*args, **kwargs)
            except grpc.RpcError as e:
                self._handle_grpc_error(method_name, e)
                raise
            except Exception as e:
                last_exception = e
                current_retry += 1
                if current_retry >= self.retries:
                    break
                logging.warning(
                    f"{method_name} attempt {current_retry} failed: {e}. "
                    f"Retrying in {current_delay} seconds..."
                )
                time.sleep(current_delay)
                current_delay *= 2
        
        raise SDKError(f"{method_name} failed after {self.retries} attempts: {last_exception}") from last_exception

    def create_client(self, addr: str, pooled: bool):
        def _create():
            if not addr or not addr.strip():
                raise SDKError("Invalid address: empty or None")
                
            if pooled:
                conn = self._get_connection(addr)
                if conn is None:
                    raise SDKError(f"Failed to get pooled connection to {addr}")
                return nodeapi_pb2_grpc.NodeAPIStub(conn), None, None

            conn = self._create_new_connection(addr)
            if conn is None:
                raise SDKError(f"Failed to create new connection to {addr}")
            return nodeapi_pb2_grpc.NodeAPIStub(conn), lambda: conn.close(), None
        
        return self._retry_with_backoff(_create, "create_client")

    def create_ipc_client(self, addr: str, pooled: bool):
        def _create():
            if not addr or not addr.strip():
                raise SDKError("Invalid node address: empty or None")
                
            print(f"Creating IPC client for address: {addr}, pooled: {pooled}")
                
            if pooled:
                conn = self._get_connection(addr)
                if conn is None:
                    raise SDKError(f"Failed to get pooled IPC connection to {addr}")
                client = ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn)
                return client, None, None

            conn = self._create_new_connection(addr)
            if conn is None:
                raise SDKError(f"Failed to create IPC connection to {addr}")
            return ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn), lambda: conn.close(), None
        
        return self._retry_with_backoff(_create, "create_ipc_client")

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
        if not addr or not addr.strip():
            raise SDKError("Invalid address")
        
        logging.info(f"Creating new gRPC connection to {addr}")
        conn = grpc.insecure_channel(addr)

        try:
            grpc.channel_ready_future(conn).result(timeout=5)
            logging.info(f"Connection established to {addr}")
            return conn
        except grpc.FutureTimeoutError:
            logging.warning(f"_create_new_connection({addr}): connection not ready within timeout, proceeding anyway")

            return conn
        except Exception as e:
            try:
                conn.close()
            except:
                pass 
            raise SDKError(f"Failed to connect to {addr}: {e}") from e
        
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
                raise SDKError("Errors closing connections: " + ", ".join(errors))
