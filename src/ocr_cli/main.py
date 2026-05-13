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
    raise typer.Exit(code=run_setup(check_only=check, debug=debug))


@app.command()
def cleanup(purge_models: bool = typer.Option(True, "--purge-models/--keep-models")):
    raise typer.Exit(code=run_cleanup(purge_models=purge_models))


@app.command()
def run(
    image: Path,
    output: str = typer.Option("text", "--output", help="text|json|markdown"),
    profile: str = typer.Option("default", "--profile"),
    long_image: bool = typer.Option(False, "--long-image"),
    max_side_len: int = 2000,
    min_side_len: int = 30,
    width_height_ratio: float = 8,
    min_height: int = 30,
    debug: bool = typer.Option(False, "--debug"),
):
    if output not in {"text", "json", "markdown"}:
        typer.echo("--output 仅支持 text/json/markdown", err=True)
        raise typer.Exit(1)
    if long_image:
        if max_side_len == 2000:
            max_side_len = 4000
        if width_height_ratio == 8:
            width_height_ratio = -1
    try:
        engine = OCREngine(profile=profile, debug=debug)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    result = engine.run(
        image,
        max_side_len=max_side_len,
        min_side_len=min_side_len,
        width_height_ratio=width_height_ratio,
        min_height=min_height,
        markdown=(output == "markdown"),
    )
    if result.status != "success":
        typer.echo(result.error, err=True)
        raise typer.Exit(1)
    if output == "json":
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False))
    elif output == "markdown":
        typer.echo(result.markdown)
    else:
        typer.echo(result.text)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, profile: str = "default", debug: bool = typer.Option(False, "--debug")):
    try:
        engine = OCREngine(profile=profile, debug=debug)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    engine.load()
    uvicorn.run(create_app(engine), host=host, port=port)


if __name__ == "__main__":
    app()
