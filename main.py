#! /usr/bin/env python3

import click

from FixedAssetsRegister.functions import (
    create_fixed_asset_document,
    get_app_settings,
    load_fixed_assets,
    read_workbook_data,
    print_fixed_assets,
    process_workbook_data,
)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    This allows to use our proggie w/o any parameter,
    specyfying the default one.
    """
    if ctx.invoked_subcommand is None:
        report()

@cli.command()
def wb() -> None:
    """
    Imports workbook data to a simple DB (pickle)
    """
    workbook_data = read_workbook_data()
    process_workbook_data(workbook_data)

@cli.command()
def report():
    fixed_assets = load_fixed_assets()
    print_fixed_assets(fixed_assets)

@cli.command()
def fa(number: int) -> None:
    """
    Still to do - throws an error ATM
    """
    fixed_assets = load_fixed_assets()
    create_fixed_asset_document(fixed_assets, number)
# pylint: disable=fixme
# @cli.command()
# def search(item: str) -> None:
#     """
#     TODO
#     """
#     match item:
#         case '' : return None
#         case 1 : fixed_assets = load_fixed_assets()

#     return fixed_assets

@cli.command()
def config():
    app_settings = get_app_settings()
    app_settings.save()
    print('App settings saved!')

if __name__ == '__main__':
    cli(None)
