from json import load, dump
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

class App_Settings(BaseModel):
    data_path: Path = Path.cwd()
    config_file: str = 'settings.json'
    wb_filename: str = ''
    sheet_name: str = ''
    fa_filename: str = ''
    fa_path: Optional[str] = 'FA_documents'
    last_column: int = 0
    configured: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.fa_path = str(self.data_path / self.fa_path)
        filename = self.data_path / self.config_file
        if Path.is_file(filename):
            with open(filename, encoding='utf-8') as config_file:
                config = load(config_file)

            self.__dict__.update(config)
            self.data_path = Path(config.get('data_path'))

        # Pydantic requires use of __context to initialize the model,
        # here it defaults to None
        return super().model_post_init(__context)

    def list_files(self) -> list[str]:
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
                "sheet_name": self.sheet_name,
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
    date: str = Field(...)
    name_of_item: str = Field(...)
    # characteristics: Optional[str] = ''
    invoice: str = Field(...)
    invoice_date: str = Field(...)
    issuer: str = Field(...)
    # usage: str = Field(...)
    value: str = Field(...)
    date: str = Field(...)
    material_duty_person: str = Field(...)
    psp: str = Field(...)
    cost_center: str = Field(...)
    inventory_number: str = Field(...)

class FixedAssetDocument(FixedAsset):
    FA_TEMPLATE: str = 'FA_template.xlsx'
    document_name: str = Field(...)
    committee: list = ['John Smith', 'Jane Doe']
