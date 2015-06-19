import click

from . import loop


@click.command()
def cli():
    loop()
