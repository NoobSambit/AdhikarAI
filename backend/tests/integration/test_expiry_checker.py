from datetime import date, timedelta

from app.services.jobs.expiry_checker import expire_schemes


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeScheme:
    def __init__(self):
        self.id = "expired"
        self.name = "Expired Scheme"
        self.organisation_id = "org"
        self.valid_until = date.today() - timedelta(days=1)
        self.status = "active"
        self.is_active = True


class _FakeDb:
    def __init__(self):
        self.scheme = _FakeScheme()
        self.calls = 0
        self.added = []
        self.committed = False

    async def scalars(self, _stmt):
        self.calls += 1
        return _Rows([self.scheme] if self.calls == 1 else [])

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.committed = True


async def test_expiry_checker_marks_expired_scheme():
    db = _FakeDb()
    result = await expire_schemes(date.today(), db)
    assert result.expired_count == 1
    assert db.scheme.status == "expired"
    assert db.scheme.is_active is False
    assert db.committed

