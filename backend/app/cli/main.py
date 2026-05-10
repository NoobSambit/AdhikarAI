import asyncio
import json
from datetime import date
from pathlib import Path

import typer
from rich import print

from app.db.session import AsyncSessionLocal
from app.schemas.scheme import CreateSchemeRequest, EligibilityCriteriaModel, UpdateSchemeRequest
from app.services.eligibility.validation import validate_rule_payload
from app.services.jobs.expiry_checker import expire_schemes
from app.services.schemes import archive_scheme, create_scheme, update_scheme
from app.services.search.faiss_index import rebuild_faiss_index
from app.services.seeds import seed_central_schemes

app = typer.Typer()
scheme_app = typer.Typer()
index_app = typer.Typer()
expiry_app = typer.Typer()
app.add_typer(scheme_app, name="scheme")
app.add_typer(index_app, name="index")
app.add_typer(expiry_app, name="expiry-check")


def run(coro):
    return asyncio.run(coro)


@scheme_app.command("add")
def scheme_add(path: Path) -> None:
    async def _run() -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        async with AsyncSessionLocal() as db:
            result = await create_scheme(db, CreateSchemeRequest.model_validate(payload))
            print(result.model_dump())

    run(_run())


@scheme_app.command("update")
def scheme_update(scheme_id: str, path: Path) -> None:
    async def _run() -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        async with AsyncSessionLocal() as db:
            result = await update_scheme(db, scheme_id, UpdateSchemeRequest.model_validate(payload))
            print(result.model_dump())

    run(_run())


@scheme_app.command("archive")
def scheme_archive(organisation_id: str, scheme_id: str, reason: str) -> None:
    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            result = await archive_scheme(db, organisation_id, scheme_id, reason)
            print(result.model_dump())

    run(_run())


@scheme_app.command("validate")
def scheme_validate(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    criteria = payload.get("eligibility_rule", payload)
    issues = validate_rule_payload(criteria, set(payload.get("known_scheme_ids", [])))
    print([issue.__dict__ for issue in issues])
    raise typer.Exit(code=1 if issues else 0)


@scheme_app.command("seed")
def scheme_seed(path: Path | None = None) -> None:
    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            count = await seed_central_schemes(db, path)
            print({"seeded": count})

    run(_run())


@index_app.command("rebuild")
def index_rebuild(organisation_id: str, index_name: str = "schemes_active") -> None:
    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            result = await rebuild_faiss_index(db, organisation_id, index_name)
            print(result.__dict__)

    run(_run())


@expiry_app.command("run")
def expiry_run(today: date | None = None) -> None:
    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            result = await expire_schemes(today or date.today(), db)
            print(result.__dict__)

    run(_run())

