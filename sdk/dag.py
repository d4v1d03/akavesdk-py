import io
import hashlib
import struct
from typing import List, Optional, Any, BinaryIO
from dataclasses import dataclass

try:
    from multiformats import CID, multihash
    from multiformats.multicodec import multicodec
    MULTIFORMATS_AVAILABLE = True
except ImportError:
    MULTIFORMATS_AVAILABLE = False
    class CID:
        def __init__(self, cid_str):
            self.cid_str = cid_str
        
        @classmethod
        def decode(cls, cid_str):
            return cls(cid_str)
        
        def __str__(self):
            return self.cid_str
        
        def string(self):
            return self.cid_str
            
        def bytes(self):
            return self.cid_str.encode()
        
        def type(self):
            if self.cid_str.startswith('bafybeig'):
                return 0x70  # dag-pb
            else:
                return 0x55  # raw

from private.encryption.encryption import encrypt
from .model import FileBlockUpload

# IPFS constants matching Go implementation
DEFAULT_CID_VERSION = 1
DAG_PB_CODEC = 0x70
RAW_CODEC = 0x55

class DAGError(Exception):
    pass

class DAGRoot:
    
    def __init__(self):
        self.links = []  # Store chunk links
        self.total_file_size = 0  # Total raw data size across all chunks
        
    @classmethod 
    def new(cls):
        return cls()
    
    def add_link(self, chunk_cid, raw_data_size: int, proto_node_size: int) -> None:
        if hasattr(chunk_cid, 'string'):
            cid_str = chunk_cid.string()
        elif hasattr(chunk_cid, '__str__'):
            cid_str = str(chunk_cid)
        else:
            cid_str = chunk_cid
            
        self.links.append({
            "cid": cid_str,
            "name": "",  # Empty name for file chunks
            "size": proto_node_size
        })
        
        self.total_file_size += raw_data_size
    
    def build(self):
        if len(self.links) == 0:
            raise DAGError("no chunks added")
        
        if len(self.links) == 1:
            return self.links[0]["cid"]
        
        try:
            unixfs_data = self._create_unixfs_file_data()
            dag_pb_data = self._create_dag_pb_node(unixfs_data, self.links)
            
            root_cid = self._generate_dag_pb_cid(dag_pb_data)
            return root_cid
            
        except Exception as e:
            raise DAGError(f"failed to build DAG root: {str(e)}")
    
    def _create_unixfs_file_data(self) -> bytes:
        unixfs_data = bytes([0x08, 0x02])  # field 1, type = file
        
        if self.total_file_size > 0:
            unixfs_data += bytes([0x18]) + self._encode_varint(self.total_file_size)
        
        return unixfs_data
    
    def _create_dag_pb_node(self, data: bytes, links: List[dict]) -> bytes:
        pb_data = b''
        
        # Add links (field 2)
        for link in links:
            link_data = self._encode_pb_link(link)
            pb_data += bytes([0x12]) + self._encode_varint(len(link_data)) + link_data
        
        if data:
            pb_data += bytes([0x0a]) + self._encode_varint(len(data)) + data
        
        return pb_data
    
    def _encode_pb_link(self, link: dict) -> bytes:
        link_data = b''
        
        # Hash field (field 1) - CID bytes
        cid_bytes = self._cid_to_bytes(link["cid"])
        link_data += bytes([0x0a]) + self._encode_varint(len(cid_bytes)) + cid_bytes
        
        # Name field (field 2)
        name = link.get("name", "")
        if name:
            name_bytes = name.encode('utf-8')
            link_data += bytes([0x12]) + self._encode_varint(len(name_bytes)) + name_bytes
        
        # Tsize field (field 3)
        size = link.get("size", 0)
        if size > 0:
            link_data += bytes([0x18]) + self._encode_varint(size)
        
        return link_data
    
    def _cid_to_bytes(self, cid_str: str) -> bytes:
        try:
            if MULTIFORMATS_AVAILABLE:
                cid_obj = CID.decode(cid_str)
                return cid_obj.bytes
            else:
                return hashlib.sha256(cid_str.encode()).digest()
        except:
            return hashlib.sha256(cid_str.encode()).digest()
    
    def _generate_dag_pb_cid(self, data: bytes) -> str:
        hash_digest = hashlib.sha256(data).digest()
        
        if MULTIFORMATS_AVAILABLE:
            try:
                mh = multihash.digest(hash_digest, 'sha2-256')
                cid = CID('base32', 1, 'dag-pb', mh)
                return str(cid)
            except:
                pass
        
        import base64
        b32_hash = base64.b32encode(hash_digest).decode().lower().rstrip('=')
        char_map = str.maketrans('01', 'ab')
        b32_hash = b32_hash.translate(char_map)
        cid_str = f"bafybeig{b32_hash[:50]}"
        return cid_str
    
    def _encode_varint(self, value: int) -> bytes:
        result = b''
        while value > 127:
            result += bytes([(value & 127) | 128])
            value >>= 7
        result += bytes([value & 127])
        return result

@dataclass 
class ChunkDAG:   
   
    cid: str                        # Chunk CID  
    raw_data_size: int             # Size of data read from disk
    proto_node_size: int           # Size of the ProtoNode in the DAG (RawDataSize + protonode overhead)
    blocks: List[FileBlockUpload]  # List of blocks in chunk

def build_dag(ctx: Any, reader: BinaryIO, block_size: int, enc_key: Optional[bytes] = None) -> ChunkDAG:
    try:
        data = reader.read()
        if not data:
            raise DAGError("empty data")
        
        raw_data_size = len(data)
        
        if enc_key and len(enc_key) > 0:
            data = encrypt(enc_key, data, b"dag_encryption")
        
        blocks = []
        offset = 0
        
        while offset < len(data):
            end_offset = min(offset + block_size, len(data))
            block_data = data[offset:end_offset]
            
            block_cid = _generate_block_cid(block_data)
            
            block = FileBlockUpload(
                cid=block_cid,
                data=block_data
            )
            blocks.append(block)
            
            offset = end_offset
        
        if not blocks:
            raise DAGError("no blocks created")
        
        if len(blocks) == 1:
            chunk_cid = blocks[0].cid
            proto_node_size = len(blocks[0].data)
        else:
            chunk_dag_data = _create_chunk_dag_node(blocks)
            chunk_cid = _generate_block_cid(chunk_dag_data)
            proto_node_size = len(chunk_dag_data)
        
        return ChunkDAG(
            cid=chunk_cid,
            raw_data_size=raw_data_size,
            proto_node_size=proto_node_size,
            blocks=blocks
        )
        
    except Exception as e:
        raise DAGError(f"failed to build chunk DAG: {str(e)}")

def _generate_block_cid(data: bytes) -> str:
    hash_digest = hashlib.sha256(data).digest()
    
    if MULTIFORMATS_AVAILABLE:
        try:
            mh = multihash.digest(hash_digest, 'sha2-256')
            cid = CID('base32', 1, 'raw', mh)
            return str(cid)
        except:
            pass
    
    # Fallback: create CID-like string with raw prefix
    import base64
    b32_hash = base64.b32encode(hash_digest).decode().lower().rstrip('=')
    # Ensure valid base32 characters  
    char_map = str.maketrans('01', 'ab')
    b32_hash = b32_hash.translate(char_map)
    cid_str = f"bafkreig{b32_hash[:50]}"  # bafkreig prefix for raw blocks
    return cid_str

def _create_chunk_dag_node(blocks: List[FileBlockUpload]) -> bytes:
    links = []
    for i, block in enumerate(blocks):
        links.append({
            "cid": block.cid,
            "name": "",  # Empty name for data blocks
            "size": len(block.data)
        })
    
    dag_root = DAGRoot()
    pb_data = dag_root._create_dag_pb_node(b"", links)
    return pb_data

def extract_block_data(cid_str: str, data: bytes) -> bytes:
    try:
        if MULTIFORMATS_AVAILABLE:
            try:
                cid_obj = CID.decode(cid_str)
                cid_type = cid_obj.codec
            except:
                if cid_str.startswith('bafkreig'):
                    cid_type = RAW_CODEC
                else:
                    cid_type = DAG_PB_CODEC
        else:
            if cid_str.startswith('bafkreig'):
                cid_type = RAW_CODEC
            else:
                cid_type = DAG_PB_CODEC
        
        # Handle different CID types (matches Go switch statement)
        if cid_type == DAG_PB_CODEC:
            # DAG-PB format - extract UnixFS data
            return _extract_unixfs_data(data)
        elif cid_type == RAW_CODEC:
            # Raw format - return data as-is
            return data
        else:
            raise DAGError(f"unknown CID type: {cid_type}")
            
    except Exception as e:
        return data

def _extract_unixfs_data(pb_data: bytes) -> bytes:
    try:
        offset = 0
        data_content = b""
        
        while offset < len(pb_data):
            if offset >= len(pb_data):
                break
                
            # Read field header
            tag = pb_data[offset]
            offset += 1
            
            field_num = tag >> 3
            wire_type = tag & 0x07
            
            if wire_type == 2:  # Length-delimited
                # Read length
                length, length_bytes = _decode_varint(pb_data, offset)
                offset += length_bytes
                
                # Read data
                field_data = pb_data[offset:offset + length]
                offset += length
                
                if field_num == 1:  # Data field
                    data_content = _extract_from_unixfs(field_data)
                    break
            else:
                break
        
        return data_content if data_content else pb_data
        
    except:
        return pb_data

def _extract_from_unixfs(unixfs_data: bytes) -> bytes:
    try:
        offset = 0
        
        while offset < len(unixfs_data):
            if offset >= len(unixfs_data):
                break
                
            tag = unixfs_data[offset]
            offset += 1
            
            field_num = tag >> 3
            wire_type = tag & 0x07
            
            if field_num == 3 and wire_type == 2:  # Data field (field 3)
                length, length_bytes = _decode_varint(unixfs_data, offset)
                offset += length_bytes
                
                return unixfs_data[offset:offset + length]
            elif wire_type == 2:  # Length-delimited, skip
                length, length_bytes = _decode_varint(unixfs_data, offset)
                offset += length_bytes + length
            else:
                offset += 1
        
        return b""
        
    except:
        return b""

def _decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    result = 0
    shift = 0
    bytes_read = 0
    
    while offset + bytes_read < len(data):
        byte = data[offset + bytes_read]
        bytes_read += 1
        
        result |= (byte & 0x7F) << shift
        
        if (byte & 0x80) == 0:
            break
            
        shift += 7
        
        if shift >= 64:
            raise ValueError("varint too long")
    
    return result, bytes_read

def block_by_cid(blocks: List[FileBlockUpload], cid_str: str) -> tuple[FileBlockUpload, bool]:
    for block in blocks:
        if block.cid == cid_str:
            return block, True
    return FileBlockUpload(cid="", data=b""), False
