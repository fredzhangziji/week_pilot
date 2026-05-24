"""WeekPilot CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from weekpilot.llm import MissingAPIKeyError
from weekpilot.pipeline import run_generate
from weekpilot.sample_data import write_sample_inputs
from weekpilot.utils import ensure_dir

app = typer.Typer(help='WeekPilot: data-driven weekly report generator.')


@app.command()
def generate(
    input_dir: Path = typer.Option(Path('input'), '--input-dir', '-i', help='Input directory.'),
    output_dir: Path = typer.Option(Path('output'), '--output-dir', '-o', help='Output directory.'),
    demo: bool = typer.Option(False, '--demo', help='Use local demo provider when no API key is configured.'),
) -> None:
    """Generate weekly report artifacts."""

    try:
        result = run_generate(input_dir=input_dir, output_dir=output_dir, project_root=Path.cwd(), demo=demo)
    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        typer.echo('请检查 Provider、模型、Base URL 和 API Key 是否匹配。DeepSeek Key 需要选择 deepseek。')
        raise typer.Exit(code=1) from exc

    typer.secho('WeekPilot generation completed.', fg=typer.colors.GREEN)
    typer.echo(f'Output: {Path(result.output_dir).resolve()}')
    typer.echo(f'History: {Path(result.history_dir).resolve() if result.history_dir else "not saved"}')
    typer.echo(f'Mode: {result.report.llm_mode} / Model: {result.report.model}')


@app.command()
def sample(input_dir: Path = typer.Option(Path('input'), '--input-dir', '-i', help='Input directory.')) -> None:
    """Create sample input files."""

    files = write_sample_inputs(input_dir)
    typer.secho('Sample input files created.', fg=typer.colors.GREEN)
    for path in files:
        typer.echo(f'- {path}')


@app.command('clean-output')
def clean_output(output_dir: Path = typer.Option(Path('output'), '--output-dir', '-o', help='Output directory.')) -> None:
    """Clean generated output files while keeping .gitkeep."""

    root = ensure_dir(output_dir)
    removed = 0
    for path in root.iterdir():
        if path.name == '.gitkeep':
            continue
        if path.is_dir():
            import shutil

            shutil.rmtree(path)
        else:
            path.unlink()
        removed += 1
    typer.secho(f'Cleaned {removed} output item(s).', fg=typer.colors.GREEN)


if __name__ == '__main__':
    app()
