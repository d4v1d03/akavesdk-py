import grpc
import time
import threading
import logging
from typing import Dict, Optional, Tuple, Callable
from private.pb import nodeapi_pb2_grpc, ipcnodeapi_pb2_grpc
from .config import SDKError


class ConnectionPool:
    
    def __init__(self):
        self._lock = threading.RLock()
        self._connections: Dict[str, grpc.Channel] = {}

    def create_ipc_client(self, addr: str, pooled: bool) -> Tuple[ipcnodeapi_pb2_grpc.IPCNodeAPIStub, Optional[Callable[[], None]], Optional[Exception]]:
        try:
            if pooled:
                conn, err = self._get(addr)
                if err:
                    return None, None, err
                return ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn), None, None

            conn = grpc.insecure_channel(addr)
            return ipcnodeapi_pb2_grpc.IPCNodeAPIStub(conn), conn.close, None
            
        except Exception as e:
            return None, None, SDKError(f"Failed to create IPC client: {str(e)}")

    def create_streaming_client(self, addr: str, pooled: bool) -> Tuple[nodeapi_pb2_grpc.StreamAPIStub, Optional[Callable[[], None]], Optional[Exception]]:
        try:
            if pooled:
                conn, err = self._get(addr)
                if err:
                    return None, None, err
                return nodeapi_pb2_grpc.StreamAPIStub(conn), None, None

            conn = grpc.insecure_channel(addr)
            return nodeapi_pb2_grpc.StreamAPIStub(conn), conn.close, None
            
        except Exception as e:
            return None, None, SDKError(f"Failed to create streaming client: {str(e)}")

    def _get(self, addr: str) -> Tuple[Optional[grpc.Channel], Optional[Exception]]:
        with self._lock:
            if addr in self._connections:
                return self._connections[addr], None

        with self._lock:
            if addr in self._connections:
                return self._connections[addr], None

            try:
                conn = grpc.insecure_channel(addr)
                
                try:
                    grpc.channel_ready_future(conn).result(timeout=5)
                except grpc.FutureTimeoutError:
                    logging.warning(f"Connection to {addr} not ready within timeout, proceeding anyway")
                
                self._connections[addr] = conn
                return conn, None
                
            except Exception as e:
                return None, SDKError(f"Failed to connect to {addr}: {str(e)}")

    def close(self) -> Optional[Exception]:
        with self._lock:
            errors = []
            
            for addr, conn in self._connections.items():
                try:
                    conn.close()
                except Exception as e:
                    errors.append(f"failed to close connection to {addr}: {str(e)}")
            
            self._connections.clear()
            
            if errors:
                return SDKError(f"encountered errors while closing connections: {errors}")
            
            return None


def new_connection_pool() -> ConnectionPool:
    return ConnectionPool()