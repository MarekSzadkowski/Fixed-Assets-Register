#! /usr/bin/env python3

import click

from FixedAssetsRegister import functions
from FixedAssetsRegister.models import FixedAssetDocument

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
    Imports wordbook data to a simple DB (pickle)
    """
    wordbook_data = functions.read_wordbook_data()
    functions.process_workbook_data(wordbook_data)

@cli.command()
def report():
    fixed_assets = functions.load_fixed_assets()
    functions.print_fixed_assets(fixed_assets)

@cli.command()
def ot() -> None:
    """
    Still to do - throws an error ATM
    """
    fixed_assets = functions.load_fixed_assets()
    for t, fa in fixed_assets:
        try:
            fa_document = FixedAssetDocument(
                fa=fa,
                document_name=t)
        except Exception as e:
            functions.exit_with_info(f'Error:\n{fa.model_dump()}\n{t}\n{e}')

        print(fa_document)

# @cli.command()
# def search(item: str) -> None:
#     """
#     TODO
#     """
#     match item:
#         case '' : return None
#         case 1 : fixed_assets = functions.load_fixed_assets()
    
#     return fixed_assets

@cli.command()
def config():
    app_settings = functions.get_app_settings()
    app_settings.save()
    print('App settings saved!')

if __name__ == '__main__':
    cli(None)
