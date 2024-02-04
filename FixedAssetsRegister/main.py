#! /usr/bin/env python3

from curses.ascii import isdigit
from datetime import datetime
from os import _exit
from pickle import dump, load
from typing import Any, cast

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import click

from models import App_Settings, FixedAsset


def exit_with_info(info: str, do_exit=True) -> None:
    print(info)
    if do_exit:
        _exit(1)

def get_app_settings() -> App_Settings:
    app_settings = App_Settings()

    if app_settings.wb_filename == '':
        files = app_settings.list_files()
        app_settings.wb_filename = files[1]
    return app_settings

def get_wordbook(filename) -> Workbook | None:
    '''Loads an Excel file from the given location on disk'''

    try:
        return load_workbook(filename, read_only=True)
    except FileNotFoundError:
        exit_with_info(
            f'Cannot find {filename}.\nPlease check your settings.')

def obtain_cell_values_from_wordbook(wb: Workbook, max_col) -> list:
    '''Returns cell values from given dimensions'''

    sheet: Worksheet = cast(Worksheet, wb.active)
    return list(sheet.iter_rows(2, max_col=max_col, values_only=True))

def obtain_last_column_from_worksheet(sheet: Worksheet) -> int:
    row = next(sheet.iter_rows(1, 1, 1, values_only=True), None)

    if row:  # if row is not None:
        for index, col in enumerate(row, 1):
            if col is None:
                return index
    return 0

def skip_on_pattern(value: str) -> bool:
    return value[:3] == 'do '

def create_document_name(row: tuple) -> tuple[str, str] | None:
    if row[2] is not None:
        serial = row[2][-6:]
        for char in serial:
            if not isdigit(char):
                return None
        return (row[12], serial)

def fix_date(_date: Any) -> str:
    if _date is None:
        _date = ''
    else:
        try:
            _date = _date.strftime('%Y-%m-%d')
        except AttributeError:
            pass
    return _date

def create_fixed_asset(row: tuple[Any]) -> FixedAsset:
    return FixedAsset(
        date=fix_date(row[11]),
        name_of_item=row[6],
        invoice=str(row[4]),
        invoice_date=fix_date(row[5]),
        issuer=str(row[10]),
        value=str(row[8]),
        material_duty_person=str(row[13]),
        psp=str(row[3]),
        mpk=str(row[3]),
        inventory_number=row[2],
    )
    
def select_fixed_assets(rows: list[tuple]) -> list[tuple, tuple]:
    selected_elements = []
    for i, row in enumerate(rows):
        if row[0] is None or row[0] == 'xx'  or row[2] is None or skip_on_pattern(row[2]):
            continue
        ot_name = create_document_name(row)
        if ot_name is not None:
            try:
                fa = create_fixed_asset(row)
            except TypeError:
                fa = None
            selected_elements.append([ot_name,
                                      row[0],
                                      fa])
    return selected_elements

def check_serials(elemets: list[tuple, tuple]) -> list[tuple]:
    return elemets
    
def read_wordbook_data() -> list[tuple]:
    app_settings = App_Settings()
    wordbook: Workbook = get_wordbook(app_settings.wb_filename)  # type: ignore
    rows = obtain_cell_values_from_wordbook(wordbook, app_settings.last_column)
    wordbook.close()
    return rows

def process_workbook_data(rows: list[tuple]) -> None:
    selected_items = select_fixed_assets(rows)
    with open('fixed_asstes.db', 'wb') as stream:
        dump(selected_items, stream)

@click.group(invoke_without_command=True)  
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        wordbook_data = read_wordbook_data()
        process_workbook_data(wordbook_data)

@cli.command()
def config():
    app_settings = get_app_settings()

    if app_settings.last_column == 0:
        wordbook: Workbook = get_wordbook(app_settings.wb_filename)  # type: ignore
        app_settings.last_column = obtain_last_column_from_worksheet(
            cast(Worksheet, wordbook.active))
    app_settings.save()

if __name__ == '__main__':
    cli()

