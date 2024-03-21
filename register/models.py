from datetime import datetime  # pylint: disable=unused-import
from json import load, dump
from pathlib import Path
from re import match, split, sub
from typing import Any

from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import load_workbook

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    ValidationInfo,
)
from pydantic.alias_generators import to_camel

class AppSettings(BaseModel):
    data_path: Path = Path.cwd()
    config_file: str = 'settings.txt'
    wb_filename: str | None = None
    fa_filename: str | None = None
    fa_path: str = 'FA_documents'
    last_column: int | None = None
    committee: list = Field(
        min_length=1,
        max_length=3,
        default=['John Smith', 'Jane Doe']
    )
    configured: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.fa_path = str(self.data_path / self.fa_path)
        filename = self.data_path / self.config_file
        if Path.is_file(filename):
            with open(filename, encoding='utf-8') as config_file:
                config = load(config_file)

            self.__dict__.update(config)
            self.data_path = Path(config.get('data_path'))

    def list_excel_files(self) -> list[str] | None:
        path = self.data_path.home()
        elements = path.rglob('*.xlsx')
        return [str(e) for e in elements]

    def save(self):
        if  self.configured:
            filename = self.data_path / self.config_file
            json_dict = {
                "data_path": str(self.data_path),
                "config_file": self.config_file,
                "wb_filename": self.wb_filename,
                "fa_path": self.fa_path,
                "fa_filename": self.fa_filename,
                "last_column": self.last_column,
                "configured": self.configured,
            }
            try:
                with open(filename,'w', encoding='utf-8') as config_file:
                    dump(json_dict, config_file, indent=2)
            except OSError as e:
                print(f'Write error: ({e})')


DATE_PATTERN: str = r'^\d{2}-\d{2}-\d{4}$'


class FixedAsset(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        coerce_numbers_to_str=True,
        extra='forbid',
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    date: str
    name_of_item: str
    invoice: str
    issuer: str
    value: str
    material_duty_person: str
    psp: str
    cost_center: str
    inventory_number: str
    invoice_date: str | None

    @field_validator('invoice', 'issuer', mode='before')
    @classmethod
    def parse_default(cls, value: Any) -> str:
        if value is None:
            return 'appendix'
        return value

    @field_validator('date', 'material_duty_person', mode='before')
    @classmethod
    def parse_value(cls, value: Any) -> str:
        if value is None:
            return ''
        return value

    @field_validator('date', 'invoice_date', mode='before')
    @classmethod
    def before_date_parser(cls, date: str) -> str:
        if isinstance(date, datetime):
            return date.strftime('%d-%m-%Y')
        return date

    @field_validator('date', 'invoice_date')
    @classmethod
    def after_date_parser(cls, value: str) -> str:
        """
        Usually excel's date is a datetime object, but sometimes may be given
        as a string not complying with the actual standards, e.g. as
        'date, date' literals. In this case the former literal is taken.

        Parameters:
        date (str | None): The input date string to be corrected.

        Returns:
        str: The corrected date string.
        """
        if value == '' or value is None:
            return value
        try:
            cls._parse_date(cls, value)
        except ValueError:
            date_string = cls._format_date(cls, value)
            date = match(DATE_PATTERN, date_string)
            try:
                return date.group()
            except AttributeError as e:
                raise ValueError(f'Invalid date format: {value}') from e
        return value

    @field_validator('cost_center')
    @classmethod
    def date_after_parser(
        cls,
        cost_center: str,
        validated_values: ValidationInfo
    ) -> str:
        """
        Sometimes financial_source is a very complex string, in such cases
        values of 'invoice' and 'issuer' are usually not given, therefore None,
        which needed fixing so the class' constructor wouldn't complain.
        Now we can check it again. We DO NOT have a value of financial_source,
        but we can check the value of cost_center, which in such cases is copied
        to the psp and cost_center fields.
        """
        values = validated_values.data
        if  'date' in values:
            if values['date'] == '' and ' ' not in cost_center:
                raise ValueError('Please specify date as DD-MM-YYYY')
        return cost_center

    def _parse_date(self, date_str: str) -> None:
        """
        Raises ValidationError if the date is not in the correct format.

        Parameters:
        date (str): The input date string to be checked.
        """
        if not match(DATE_PATTERN, date_str):
            raise ValueError(date_str)
        return date_str

    def _format_date(self, date_str: str) -> str:
        """
        Corrects the date format by removing any comma or space,
        replaces dots with dashes and returns the corrected date.

        Parameters:
        date (str): The input date string to be corrected.

        Returns:
        str: The corrected date string.
        """
        date_str, _ = split(r'\,| ', date_str, 1)
        date_str = sub(r'\.|\/', '-', date_str)
        return date_str


CELLS = ('D3', 'A5', 'A9', 'C9', 'C11', 'A21', 'A23', 'D23', 'A25')


class FixedAssetDocument(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    document_name_unit: str
    document_name_serial: str
    fixed_asset: FixedAsset

    @field_validator('document_name_unit', mode='before')
    @classmethod
    def document_name_unit_parser(cls, value: str) -> str:
        """
        Parses the document name and removes any slashes in the name.
        """
        if value == '' or value is None:
            return 'unknown_unit'
        if '/' in value:
            value = sub(r'\/', '_', value)
        return value

    def _populate_worksheet(self, wb: Workbook) -> None:
        """
        Creates a new worksheet that makes the fixed asset document.
        """
        sheet: Worksheet = wb.active
        fixed_asset = self.fixed_asset.model_dump()
        invoice_date = fixed_asset.pop('invoice_date', None)
        if invoice_date is not None:
            fixed_asset['invoice'] = f'{fixed_asset["invoice"]}' \
            + f' on {invoice_date}'
        cells = dict(zip(CELLS, fixed_asset.values()))
        for cell, value in cells.items():
            sheet[cell] = value

    def generate_document(self) -> None:
        """
        Makes the fixed asset document.
        """
        settings = AppSettings()
        template_filename = Path(settings.fa_filename)
        document_name = f'{
            self.document_name_unit}-{self.document_name_serial
        }'

        document: Workbook = load_workbook(template_filename)
        self._populate_worksheet(document)
        document.active.title = document_name
        document.save(Path(f'{settings.fa_path}/{document_name}.xlsx'))
