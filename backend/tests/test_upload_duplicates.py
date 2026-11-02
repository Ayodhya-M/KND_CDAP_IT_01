from app.services.upload_duplicates import fingerprint, find_existing_upload


def test_fingerprint_ignores_order_but_preserves_changed_content():
    rows = [{'employee_id': 'A', 'salary': 1}, {'employee_id': 'B', 'salary': 2}]
    fields = ['employee_id', 'salary']
    assert fingerprint(rows, fields) == fingerprint(list(reversed(rows)), fields)
    assert fingerprint(rows, fields) != fingerprint([rows[0], {**rows[1], 'salary': 3}], fields)


def test_existing_content_matches_despite_database_metadata():
    class Query:
        def __init__(self, table): self.table = table
        def select(self, *args): return self
        def eq(self, *args): return self
        def order(self, *args): return self
        def range(self, *args): return self
        def execute(self):
            class Result: pass
            result = Result()
            result.data = ([{'id': 'saved', 'record_count': 1}] if self.table == 'dataset_uploads'
                           else [{'employee_id': 'A', 'salary': 1, 'id': 'database-id'}])
            return result
    class Client:
        def table(self, name): return Query(name)
    assert find_existing_upload(Client(), 'hr', [{'employee_id': 'A', 'salary': 1, 'upload_id': 'pending'}]) == 'saved'
    assert find_existing_upload(Client(), 'hr', [{'employee_id': 'A', 'salary': 2, 'upload_id': 'pending'}]) is None
