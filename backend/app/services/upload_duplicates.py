"""Content-based duplicate detection, independent of filenames and row order."""
import hashlib
import json
from threading import Lock

# Serializes check+insert for the project's single-process development server.
# Multi-worker deployments need a database unique constraint/transaction instead.
UPLOAD_LOCK = Lock()


def fingerprint(rows, fields):
    normalized = sorted(json.dumps({key: row.get(key) for key in fields}, sort_keys=True,
                                   separators=(',', ':'), allow_nan=False) for row in rows)
    return hashlib.sha256(json.dumps(normalized).encode()).hexdigest()


def find_existing_upload(client, dataset_type, records):
    table = 'employee_records' if dataset_type == 'hr' else 'economic_indicators'
    fields = sorted(set(records[0]) - {'upload_id', 'id', 'created_at'})
    target = fingerprint(records, fields)
    uploads = client.table('dataset_uploads').select('id,record_count').eq('dataset_type', dataset_type).eq('record_count', len(records)).execute().data
    for upload in uploads:
        rows, offset = [], 0
        while True:
            batch = client.table(table).select(','.join(fields)).eq('upload_id', upload['id']).order('id').range(offset, offset + 499).execute().data
            rows.extend(batch)
            if len(batch) < 500:
                break
            offset += 500
        if len(rows) == len(records) and fingerprint(rows, fields) == target:
            return upload['id']
    return None
