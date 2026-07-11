"""
S3 job-bus shared between the Posit Connect frontend and the dev container worker.

Layout:
  s3://<BUCKET>/<PREFIX>/<job_id>/job.json      frontend writes (the form answers)
  s3://<BUCKET>/<PREFIX>/<job_id>/status.json   worker writes/updates (live progress)
  s3://<BUCKET>/<PREFIX>/<job_id>/.claimed       worker marker (prevents double-processing)
  s3://<BUCKET>/<PREFIX>/<job_id>/04-report.md   worker uploads on completion

Both sides import this module. The frontend bundles a copy at deploy time.
"""

import json
import boto3
from botocore.exceptions import ClientError

BUCKET = "your-bucket-name"
PREFIX = "your-team/comp-analysis/jobs"

_s3 = boto3.client("s3")


def _key(job_id: str, name: str) -> str:
    return f"{PREFIX}/{job_id}/{name}"


def _put(job_id: str, name: str, body: str, content_type="application/json"):
    _s3.put_object(Bucket=BUCKET, Key=_key(job_id, name),
                   Body=body.encode("utf-8"), ContentType=content_type)


def _get(job_id: str, name: str):
    try:
        obj = _s3.get_object(Bucket=BUCKET, Key=_key(job_id, name))
        return obj["Body"].read().decode("utf-8")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


def _exists(job_id: str, name: str) -> bool:
    try:
        _s3.head_object(Bucket=BUCKET, Key=_key(job_id, name))
        return True
    except ClientError:
        return False


# ---- frontend side -------------------------------------------------------

def submit_job(job_id: str, spec: dict):
    """Write the form answers as job.json plus an initial 'queued' status."""
    _put(job_id, "job.json", json.dumps(spec, indent=2))
    _put(job_id, "status.json", json.dumps({
        "state": "queued", "stage": "queued", "percent": 0,
    }, indent=2))


def get_status(job_id: str) -> dict | None:
    raw = _get(job_id, "status.json")
    return json.loads(raw) if raw else None


def get_report(job_id: str) -> str | None:
    return _get(job_id, "04-report.md")


# ---- worker side ---------------------------------------------------------

def list_jobs() -> list[str]:
    """Return all job_ids under the prefix."""
    ids, token = set(), None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=f"{PREFIX}/", Delimiter="/")
        if token:
            kw["ContinuationToken"] = token
        resp = _s3.list_objects_v2(**kw)
        for cp in resp.get("CommonPrefixes", []):
            ids.add(cp["Prefix"][len(PREFIX) + 1:].rstrip("/"))
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return sorted(ids)


def open_jobs() -> list[str]:
    """Jobs that have job.json but have not been claimed by a worker yet."""
    return [j for j in list_jobs()
            if _exists(j, "job.json") and not _exists(j, ".claimed")]


def claim(job_id: str) -> bool:
    """Atomically-ish claim a job. Returns False if already claimed."""
    if _exists(job_id, ".claimed"):
        return False
    _put(job_id, ".claimed", "1", content_type="text/plain")
    return True


def fetch_spec(job_id: str) -> dict:
    return json.loads(_get(job_id, "job.json"))


def push_status(job_id: str, status: dict):
    _put(job_id, "status.json", json.dumps(status, indent=2))


def push_report(job_id: str, markdown: str):
    _put(job_id, "04-report.md", markdown, content_type="text/markdown")
