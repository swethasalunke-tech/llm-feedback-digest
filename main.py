"""llm-feedback-digest CLI entry point."""

from __future__ import annotations
import csv, json, os, sys
from pathlib import Path
from typing import Any
import click
from dotenv import load_dotenv
from rich.console import Console
from analyzer import FeedbackAnalyzer
from formatter import generate_digest, send_to_slack
load_dotenv()
console = Console(stderr=True)

def _load_feedback(p):
    if not p.exists(): raise FileNotFoundError(f"Not found: {p}")
    s = p.suffix.lower()
    if s == ".csv":
        with p.open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
    elif s == ".json":
        with p.open(encoding="utf-8") as f: d = json.load(f)
        if not isinstance(d,list): raise ValueError("Must be array")
        return d
    raise ValueError(f"Unsupported: {s}")

@click.group()
def cli(): """Analyze product feedback with Claude and produce a weekly digest."""

@cli.command()
@click.argument("input_file")
@click.option("--model",default="claude-3-5-sonnet-20241022",show_default=True)
@click.option("--batch-size",default=20,show_default=True,type=click.IntRange(1,100))
def analyze(input_file,model,batch_size):
    """Read feedback from INPUT_FILE and analyze with Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key: console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set"); sys.exit(1)
    p = Path(input_file)
    try: items = _load_feedback(p)
    except Exception as e: console.print(f"[red]Error:[/red] {e}"); sys.exit(1)
    analyzer = FeedbackAnalyzer(api_key=api_key,model=model)
    results = []
    for i in range(0,len(items),batch_size):
        try: results += analyzer.analyze_batch(items[i:i+batch_size])
        except RuntimeError as e: console.print(f"[red]Error:[/red] {e}"); sys.exit(1)
    out = p.parent / f"analyzed_{p.stem}.json"
    out.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
    console.print(f"[green]Done.[/green] {len(results)} items -> {out}")

@cli.command()
@click.argument("analyzed_file")
@click.option("--output","-o",default=None)
@click.option("--slack-webhook",default=None,envvar="SLACK_WEBHOOK_URL",help="Slack incoming webhook URL.")
def digest(analyzed_file,output,slack_webhook):
    """Read ANALYZED_FILE and print a markdown digest."""
    p = Path(analyzed_file)
    if not p.exists(): console.print(f"[red]Error:[/red] Not found: {p}"); sys.exit(1)
    items = json.loads(p.read_text(encoding="utf-8"))
    md = generate_digest(items)
    if slack_webhook:
        try: send_to_slack(slack_webhook,items); console.print("[green]Sent to Slack.[/green]")
        except Exception as e: console.print(f"[red]Slack error:[/red] {e}"); sys.exit(1)
    if output: Path(output).write_text(md,encoding="utf-8"); console.print(f"[green]Written to {output}[/green]")
    elif not slack_webhook: click.echo(md)

if __name__=="__main__": cli()
