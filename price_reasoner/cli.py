import typer
from datetime import date
from pathlib import Path
from price_reasoner.config import Config
from price_reasoner.data_sources.mock import MockDataSource
from price_reasoner.data_sources.competitor_mock import MockCompetitorDataSource
from price_reasoner.models import AnalysisReport, CompetitorReport
from price_reasoner.report import ReportGenerator
from price_reasoner.competitor_analyzer import CompetitorAnalyzer
from price_reasoner.competitor_report import CompetitorReportGenerator

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
def competitor(
    commodity: str = typer.Option(..., "--commodity", "-c", help="Product/commodity name"),
    competitors: str = typer.Option(None, "--competitors", help="Comma-separated competitor names (skip to let AI auto-recommend)"),
    current_product: str = typer.Option(None, "--product", "-p", help="Your product info as JSON string, e.g. '{\"name\":\"Dior S8U\",\"price_range\":\"4000-6000\",\"target_segment\":\"高端\"}'"),
    output: str = typer.Option("competitor_report.md", "--output", "-o", help="Output filename"),
    start_date: str = typer.Option(None, "--start", "-s", help="Start date YYYY-MM-DD (default: 12 months ago)"),
    end_date: str = typer.Option(None, "--end", "-e", help="End date YYYY-MM-DD (default: today)"),
    list_only: bool = typer.Option(False, "--list", help="Only list known competitors, don't analyze"),
):
    """
    Competitor analysis: recommend competitors, generate data collection plan,
    build comparison matrix, and produce actionable insights.

    Examples:
      price-reasoner competitor -c "Dior S8U 墨镜"                       # AI auto-recommend competitors
      price-reasoner competitor -c "Dior S8U" --competitors "Gucci,Prada"  # specify competitors
      price-reasoner competitor -c "Dior S8U" --list                      # list known competitors
    """
    from datetime import timedelta
    import json

    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today - timedelta(days=365)
    end = date.fromisoformat(end_date) if end_date else today

    ds = MockCompetitorDataSource()

    # Step 1: Determine competitors to analyze
    if list_only:
        known = ds.list_competitors(commodity)
        typer.echo(f"Known competitors for '{commodity}':")
        for c in known:
            typer.echo(f"  - {c}")
        return

    if competitors:
        comp_list = [c.strip() for c in competitors.split(",")]
        comp_recommendations = [{"name": c, "rationale": "User-specified", "priority_dimensions": []} for c in comp_list]
    else:
        typer.echo("Asking AI to recommend competitors...")
        analyzer = CompetitorAnalyzer()
        comp_recommendations = analyzer.recommend_competitors(commodity)
        comp_list = [c["name"] for c in comp_recommendations]
        typer.echo(f"AI recommended competitors: {', '.join(comp_list)}")

    # Step 2: Generate collection plan (AI-driven)
    typer.echo("Generating data collection plan...")
    analyzer = CompetitorAnalyzer()
    product_info = json.loads(current_product) if current_product else {
        "name": commodity,
        "price_range": "未知",
        "target_segment": "未知",
        "key_features": [],
        "channels": []
    }
    collection_plan = analyzer.generate_collection_plan(commodity, comp_recommendations, product_info)

    # Step 3: Collect data (mock for now)
    typer.echo("Collecting competitor data...")
    competitor_data_list = []
    for comp_name in comp_list:
        data = ds.get_competitor_data(comp_name, start, end)
        if data:
            competitor_data_list.append(data)

    # Step 4: Build competitive matrix + insights
    typer.echo("Building competitive matrix and generating insights...")
    matrix = analyzer.build_competitive_matrix(commodity, competitor_data_list, product_info)
    gaps = [s.notes for s in collection_plan if s.notes]
    insights = analyzer.generate_insights(commodity, competitor_data_list, matrix, gaps)

    report = CompetitorReport(
        target_commodity=commodity,
        competitors=competitor_data_list,
        data_collection_plan=collection_plan,
        competitive_matrix=matrix,
        insights=insights,
        gaps=gaps,
    )

    gen = CompetitorReportGenerator(output_dir=config.output_dir)
    path = gen.save(report, output)
    typer.echo(f"Competitor report saved: {path}")


@app.command()
def version():
    """Show version info"""
    typer.echo("price-reasoner v0.2.0")


if __name__ == "__main__":
    app()