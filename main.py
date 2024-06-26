#! /usr/bin/env python3

import click

from register.functions import (
    generate_fixed_asset_document,
    get_app_settings,
    load_fixed_assets,
    print_fixed_assets,
    process_workbook_data,
)
from register.workbook import read_workbook_data

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    This allows to use our proggie w/o any parameter,
    specifying the default one.
    """
    if ctx.invoked_subcommand is None:
        report()

@cli.command()
def import_wb() -> None:
    """
    Imports workbook data to a simple DB (pickle)
    """
    workbook_data = read_workbook_data()
    process_workbook_data(workbook_data)

@cli.command()
@click.option('--gdpr', is_flag=True)
def report(gdpr: bool = False) -> None:
    """
    Prints all data in the DB.
    
    Parameters: --gdpr (bool).
    If True, hides material duty person in the output,
    GDPR stands for General Data Protection Regulation in the European Union.
    """
    fixed_assets = load_fixed_assets()
    print_fixed_assets(fixed_assets, gdpr)

@cli.command()
@click.argument('serial')
def create_document(serial: str) -> None:
    """
    Makes the fixed asset document (Excel file) based on the passed serial.

    Parameters:
    serial (str): Serial number of the fixed asset.
    Pass '--all' to generate all documents.
    """
    fixed_assets = load_fixed_assets()
    generate_fixed_asset_document(fixed_assets, serial)

@cli.command()
def search(item: str) -> None:
    """
    Search for item in the DB
    """
    fixed_assets = load_fixed_assets()

    match item:
        case 'date' : return None
        case 'serial' : return None

    return fixed_assets

@cli.command()
def config():
    app_settings = get_app_settings()
    app_settings.save()
    print('App settings saved!')

if __name__ == '__main__':
    cli(None)
