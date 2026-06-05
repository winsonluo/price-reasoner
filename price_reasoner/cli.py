import typer
from datetime import date
from pathlib import Path
from price_reasoner.config import Config
from price_reasoner.data_sources.mock import MockDataSource
from price_reasoner.models import AnalysisReport
from price_reasoner.report import ReportGenerator

app = typer.Typer()
config = Config()

@app.command()
def analyze(
    commodity: str = typer.Option(..., "--commodity", "-c", help="Commodity name"),
    start_date: str = typer.Option(..., "--start", "-s", help="Start date YYYY-MM-DD"),
    end_date: str = typer.Option(..., "--end", "-e", help="End date YYYY-MM-DD"),
    output: str = typer.Option("price_report.md", "--output", "-o", help="Output filename"),
):
    """Analyze commodity price trends and generate attribution report"""
    typer.echo(f"Starting analysis for {commodity} ({start_date} ~ {end_date})")

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    ds = MockDataSource()
    stages = ds.get_price_stages(commodity, start, end)
    macro = ds.get_macro_factors(commodity, start, end)
    events = ds.get_event_timeline(commodity, start, end)

    report = AnalysisReport(
        commodity=commodity,
        start_date=start,
        end_date=end,
        stages=stages,
        attributions=[],
        causal_graph="(pending AI generation)",
        scenarios=["(pending AI generation)"],
    )

    gen = ReportGenerator(output_dir=config.output_dir)
    path = gen.save(report, output)
    typer.echo(f"Report saved: {path}")

@app.command()
def version():
    """Show version info"""
    typer.echo("price-reasoner v0.1.0")

if __name__ == "__main__":
    app()