"""MinIO implementation of immutable artifact object storage."""

from io import BytesIO

from minio import Minio


class MinioArtifactObjectStore:
    def __init__(self, client: Minio, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put(self, object_key: str, content: bytes, media_type: str) -> None:
        self._client.put_object(
            self._bucket,
            object_key,
            BytesIO(content),
            len(content),
            content_type=media_type,
        )

    def remove(self, object_key: str) -> None:
        self._client.remove_object(self._bucket, object_key)

    def read(self, object_key: str) -> bytes:
        response = self._client.get_object(self._bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
