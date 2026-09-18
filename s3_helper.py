"""
S3 Storage Layer for Canopy deployment.
Falls back to local filesystem if S3 is not available.
Logs connection status for debugging.
"""
import os
import io
import sys
import pandas as pd

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    _boto3_installed = True
except ImportError:
    _boto3_installed = False
    ClientError = Exception
    NoCredentialsError = Exception

S3_BUCKET = "canopy-app-data-prod-796301651950"
S3_PREFIX = "javmuhak/workforce-compliance/"

_s3_available = False
_s3_client = None
_s3_error = ""

if _boto3_installed:
    try:
        _s3_client = boto3.client("s3")
        # Don't use head_bucket - just try to list objects directly
        resp = _s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=S3_PREFIX,
            MaxKeys=1
        )
        _s3_available = True
        _s3_error = f"S3 OK - found {resp.get('KeyCount', 0)} objects"
        print(f"[S3] Connected to s3://{S3_BUCKET}/{S3_PREFIX} - KeyCount={resp.get('KeyCount', 0)}", file=sys.stderr)
    except NoCredentialsError as e:
        _s3_error = f"No credentials: {e}"
        print(f"[S3] ERROR - No credentials: {e}", file=sys.stderr)
    except ClientError as e:
        _s3_error = f"Client error: {e}"
        print(f"[S3] ERROR - Client error: {e}", file=sys.stderr)
    except Exception as e:
        _s3_error = f"Unknown error: {e}"
        print(f"[S3] ERROR - {type(e).__name__}: {e}", file=sys.stderr)
else:
    _s3_error = "boto3 not installed"
    print("[S3] ERROR - boto3 not installed", file=sys.stderr)


def get_s3_status():
    """Return S3 connection status for debugging."""
    return {
        "boto3_installed": _boto3_installed,
        "s3_available": _s3_available,
        "bucket": S3_BUCKET,
        "prefix": S3_PREFIX,
        "error": _s3_error,
    }


def s3_key(path):
    return S3_PREFIX + path.replace("\\", "/")


def s3_exists(path):
    if not _s3_available:
        return False
    try:
        _s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key(path))
        return True
    except Exception:
        return False


def s3_read_bytes(path):
    if not _s3_available:
        return None
    try:
        obj = _s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key(path))
        return obj["Body"].read()
    except Exception:
        return None


def file_exists(path):
    if os.path.exists(path):
        return True
    return s3_exists(path)


def read_file_bytes(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return s3_read_bytes(path)


def read_excel_smart(path, **kwargs):
    if os.path.exists(path):
        return pd.read_excel(path, **kwargs)
    data = s3_read_bytes(path)
    if data:
        return pd.read_excel(io.BytesIO(data), **kwargs)
    return pd.DataFrame()


def read_excel_file_smart(path):
    if os.path.exists(path):
        return pd.ExcelFile(path)
    data = s3_read_bytes(path)
    if data:
        return pd.ExcelFile(io.BytesIO(data))
    return None


def read_csv_smart(path, **kwargs):
    if os.path.exists(path):
        return pd.read_csv(path, **kwargs)
    data = s3_read_bytes(path)
    if data:
        return pd.read_csv(io.BytesIO(data), **kwargs)
    return pd.DataFrame()
