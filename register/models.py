from json import load, dump
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

class AppSettings(BaseModel):
    data_path: Path = Path.cwd()
    config_file: str = 'settings.txt'
    wb_filename: str | None = None
    # sheet_name: str | None = None
    fa_filename: str | None = None
    fa_path: str = 'FA_documents'
    last_column: int | None = None
    configured: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.fa_path = str(self.data_path / self.fa_path)
        filename = self.data_path / self.config_file
        if Path.is_file(filename):
            with open(filename, encoding='utf-8') as config_file:
                config = load(config_file)

            self.__dict__.update(config)
            self.data_path = Path(config.get('data_path'))

        # It seems Pydantic requires use of __context to initialize the model,
        # here it defaults to None
        super().model_post_init(__context)

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
                # "sheet_name": self.sheet_name,
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


class FixedAsset(BaseModel):
    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        extra='forbid',
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    date: str
    name_of_item: str
    invoice: str
    invoice_date: str
    issuer: str
    value: str
    material_duty_person: str
    psp: str
    cost_center: str
    inventory_number: str

class FixedAssetDocument(BaseModel):
    document_name_unit: str
    document_name_serial: str
    fixed_asset: FixedAsset
    FA_TEMPLATE: str = 'FA_template.xlsx'
    committee: list = ['John Smith', 'Jane Doe']

class BadDateFormat(Exception):
    """
    Raised if the date is not in the correct format
    """
    def __init__(self, date: str):
        self.date = date
        self.message = f'Invalid date format: {date}'
        super().__init__(self.message)
