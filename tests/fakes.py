from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any, Iterable


def new_object_id() -> str:
    return secrets.token_hex(12)


@dataclass(slots=True)
class FakeUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


@dataclass(slots=True)
class FakeMessage:
    from_user: FakeUser | None
    text: str | None = None
    answers: list[tuple[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, reply_markup: Any = None) -> None:
        self.answers.append((text, reply_markup))


@dataclass(slots=True)
class FakeCallbackQuery:
    data: str | None
    message: FakeMessage | None = None
    answered: int = 0

    async def answer(self) -> None:
        self.answered += 1


@dataclass(slots=True)
class FakeFSMContext:
    state: Any = None
    data: dict[str, Any] = field(default_factory=dict)
    cleared: int = 0

    async def clear(self) -> None:
        self.cleared += 1
        self.state = None
        self.data.clear()

    async def set_state(self, state: Any) -> None:
        self.state = state

    async def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict[str, Any]:
        return dict(self.data)


@dataclass(slots=True)
class FakeUpdateResult:
    upserted_id: Any | None


@dataclass(slots=True)
class FakeInsertOneResult:
    inserted_id: Any


@dataclass(slots=True)
class FakeCursor:
    docs: list[dict[str, Any]]

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        if length is None:
            return list(self.docs)
        return list(self.docs[: int(length)])


class FakeCollection:
    def __init__(self, name: str, docs: Iterable[dict[str, Any]] = ()) -> None:
        self.name = name
        self.docs: list[dict[str, Any]] = [dict(d) for d in docs]
        self.inserted_docs: list[dict[str, Any]] = []
        self.aggregate_result: list[dict[str, Any]] = []
        self.last_pipeline: list[dict[str, Any]] | None = None

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self.docs:
            if _matches(doc, query):
                return dict(doc)
        return None

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], upsert: bool = False) -> FakeUpdateResult:
        for i, doc in enumerate(self.docs):
            if _matches(doc, query):
                if "$set" in update:
                    new_doc = dict(doc)
                    new_doc.update(dict(update["$set"]))
                    self.docs[i] = new_doc
                return FakeUpdateResult(upserted_id=None)

        if not upsert:
            return FakeUpdateResult(upserted_id=None)

        new_doc = dict(query)
        if "$set" in update:
            new_doc.update(dict(update["$set"]))
        if "$setOnInsert" in update:
            new_doc.update(dict(update["$setOnInsert"]))
        new_doc.setdefault("_id", new_object_id())
        self.docs.append(new_doc)
        return FakeUpdateResult(upserted_id=new_doc["_id"])

    def find(self, query: dict[str, Any] | None = None, projection: dict[str, Any] | None = None) -> FakeCursor:
        query = query or {}
        result = [dict(d) for d in self.docs if _matches(d, query)]
        if projection:
            # Keep `_id` unless explicitly excluded.
            include_keys = {k for k, v in projection.items() if v}
            exclude_id = projection.get("_id") == 0
            projected: list[dict[str, Any]] = []
            for doc in result:
                out: dict[str, Any] = {}
                if not exclude_id and "_id" in doc:
                    out["_id"] = doc["_id"]
                for k in include_keys:
                    if k in doc:
                        out[k] = doc[k]
                projected.append(out)
            result = projected
        return FakeCursor(result)

    async def insert_one(self, doc: dict[str, Any]) -> FakeInsertOneResult:
        out = dict(doc)
        out.setdefault("_id", new_object_id())
        self.docs.append(out)
        self.inserted_docs.append(out)
        return FakeInsertOneResult(inserted_id=out["_id"])

    def aggregate(self, pipeline: list[dict[str, Any]]) -> FakeCursor:
        self.last_pipeline = list(pipeline)
        return FakeCursor([dict(d) for d in self.aggregate_result])


class FakeRawDatabase:
    def __init__(self, collections: dict[str, FakeCollection]) -> None:
        self._collections = dict(collections)

    def get_collection(self, name: str) -> FakeCollection:
        return self._collections[name]

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections[name]


@dataclass(slots=True)
class FakeDB:
    collections: dict[str, FakeCollection]
    raw: FakeRawDatabase = field(init=False)

    def __post_init__(self) -> None:
        self.raw = FakeRawDatabase(self.collections)


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for k, v in query.items():
        if doc.get(k) != v:
            return False
    return True
