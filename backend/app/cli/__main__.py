"""CLI entry point."""
import typer
from app.cli.seed import app as seed_app

main = typer.Typer()
main.add_typer(seed_app, name="db")

if __name__ == "__main__":
    main()
