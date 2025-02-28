from datetime import datetime
from typing import List, Optional
import cid


class BucketCreateResult:
    """
    The result of bucket creation.
    """
    def __init__(self, name: str, created_at: datetime):
        self.name = name
        self.created_at = created_at


class Bucket:
    """
    Represents a bucket.
    """
    def __init__(self, name: str, created_at: datetime):
        self.name = name
        self.created_at = created_at


class Chunk:
    """
    A piece of metadata of some file.
    """
    def __init__(self, cid: str, encoded_size: int, size: int, index: int):
        self.cid = cid
        self.encoded_size = encoded_size
        self.size = size
        self.index = index


class FileBlock:
    """
    A piece of metadata of some file.
    """
    def __init__(self, cid: str, data: bytes, permit: str, node_address: str, node_id: str):
        self.cid = cid
        self.data = data
        self.permit = permit
        self.node_address = node_address
        self.node_id = node_id


class FileBlockSP(FileBlock):
    """
    A piece of metadata of some file with an additional SPBaseURL.
    """
    def __init__(self, cid: str, data: bytes, permit: str, node_address: str, node_id: str, sp_base_url: str):
        super().__init__(cid, data, permit, node_address, node_id)
        self.sp_base_url = sp_base_url


class FileUpload:
    """
    Represents a file and some metadata.
    """
    def __init__(self, root_cid: str, bucket_name: str, file_name: str, file_size: int, blocks: List[FileBlock]):
        self.root_cid = root_cid
        self.bucket_name = bucket_name
        self.file_name = file_name
        self.file_size = file_size
        self.blocks = blocks


class FileDownload:
    """
    Represents a file download and some metadata.
    """
    def __init__(self, bucket_name: str, file_name: str, blocks: List[FileBlock]):
        self.bucket_name = bucket_name
        self.file_name = file_name
        self.blocks = blocks


class FileDownloadSP(FileDownload):
    """
    Represents a file download and some metadata with additional SPBaseURL.
    """
    def __init__(self, bucket_name: str, file_name: str, blocks: List[FileBlockSP]):
        super().__init__(bucket_name, file_name, blocks)


class FileListItem:
    """
    Contains bucket file list file meta information.
    """
    def __init__(self, root_cid: str, name: str, size: int, created_at: datetime):
        self.root_cid = root_cid
        self.name = name
        self.size = size
        self.created_at = created_at


class FileMeta:
    """
    Contains single file meta information.
    """
    def __init__(self, root_cid: str, name: str, size: int, created_at: datetime):
        self.root_cid = root_cid
        self.name = name
        self.size = size
        self.created_at = created_at


class FileUploadV2:
    """
    Contains single file meta information.
    """
    def __init__(self, bucket_name: str, name: str, stream_id: str, created_at: datetime):
        self.bucket_name = bucket_name
        self.name = name
        self.stream_id = stream_id
        self.created_at = created_at


class FileChunkUploadV2:
    """
    Contains single file chunk meta information.
    """
    def __init__(self, stream_id: str, index: int, chunk_cid: cid.Cid, actual_size: int, raw_data_size: int,
                 proto_node_size: int, blocks: List[FileBlock]):
        self.stream_id = stream_id
        self.index = index
        self.chunk_cid = chunk_cid
        self.actual_size = actual_size
        self.raw_data_size = raw_data_size
        self.proto_node_size = proto_node_size
        self.blocks = blocks


class FileDownloadV2:
    """
    Contains single file meta information.
    """
    def __init__(self, stream_id: str, bucket_name: str, name: str, chunks: List[Chunk]):
        self.stream_id = stream_id
        self.bucket_name = bucket_name
        self.name = name
        self.chunks = chunks


class FileChunkDownloadV2:
    """
    Contains single file chunk meta information.
    """
    def __init__(self, cid: str, index: int, encoded_size: int, size: int, blocks: List[FileBlock]):
        self.cid = cid
        self.index = index
        self.encoded_size = encoded_size
        self.size = size
        self.blocks = blocks


class FileMetaV2:
    """
    Contains single file meta information.
    """
    def __init__(self, stream_id: str, root_cid: str, bucket_name: str, name: str, encoded_size: int, size: int,
                 created_at: datetime, commited_at: datetime):
        self.stream_id = stream_id
        self.root_cid = root_cid
        self.bucket_name = bucket_name
        self.name = name
        self.encoded_size = encoded_size
        self.size = size
        self.created_at = created_at
        self.commited_at = commited_at
