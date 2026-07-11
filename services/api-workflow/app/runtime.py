from contextlib import contextmanager
import psycopg
from minio import Minio
from minio.deleteobjects import DeleteObject
from .settings import get_settings

@contextmanager
def database():
    with psycopg.connect(get_settings().database_url) as connection:
        yield connection

def object_store() -> Minio:
    settings = get_settings()
    return Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_secure)

def ensure_bucket() -> None:
    settings = get_settings()
    client = object_store()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)

def clear_bucket() -> None:
    settings = get_settings()
    client = object_store()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)
        return
    objects = (DeleteObject(item.object_name) for item in client.list_objects(settings.minio_bucket, recursive=True))
    errors = list(client.remove_objects(settings.minio_bucket, objects))
    if errors:
        raise RuntimeError(f"Could not reset artifact bucket: {errors}")

def readiness() -> dict[str, bool]:
    with database() as connection:
        database_ready = connection.execute("select 1").fetchone() == (1,)
    buckets = object_store().list_buckets()
    object_store_ready = any(bucket.name == get_settings().minio_bucket for bucket in buckets)
    return {"database": database_ready, "object_store": object_store_ready}
