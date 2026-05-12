from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn

from .engine import OCREngine
from .server import create_app
from .setup_cmd import run_cleanup, run_setup

app = typer.Typer(help="Local-first OCR tool for agents")


@app.command()
def setup(check: bool = typer.Option(False, "--check"), debug: bool = typer.Option(False, "--debug")):
    code = run_setup(check_only=check, debug=debug)
    raise typer.Exit(code=code)


@app.command()
def cleanup(purge_models: bool = typer.Option(True, "--purge-models/--keep-models")):
    code = run_cleanup(purge_models=purge_models)
    raise typer.Exit(code=code)


@app.command()
def run(image: Path, output: str = typer.Option("text", "--output", help="text|json")):
    engine = OCREngine()
    result = engine.run(image)
    if result.status != "success":
        typer.echo(result.error, err=True)
        raise typer.Exit(1)
    if output == "json":
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        typer.echo(result.text)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    engine = OCREngine()
    engine.load()
    uvicorn.run(create_app(engine), host=host, port=port)


if __name__ == "__main__":
    app()
