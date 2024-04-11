from json import dumps

from pydantic import ValidationError

from ..register.models import FixedAsset
from .model_constrains import model_constrains, expected_data

def test_model_deserialization():
    """
    Tests if model is deserialized correctly
    """
    fixed_asset = FixedAsset.model_validate(model_constrains)
    got = fixed_asset.model_dump()
    assert got == expected_data

def test_model_deserialization_json():
    """
    Tests if json is deserialized correctly
    """
    model_constrains_json = dumps(model_constrains)
    fixed_asset = FixedAsset.model_validate_json(model_constrains_json)
    got = fixed_asset.model_dump()
    assert got == expected_data

def test_model_deserialization_with_extra_field_added():
    """
    Here we only check if the deserialization fails with an extra field
    added to the model. Earlier, in the FixedAsset's ConficDict we
    supressed any extra data.
    See the class definition in register/models.py for more details.
    """
    model_constrains_with_extra_field_added = expected_data.copy()
    model_constrains_with_extra_field_added.update({
        'extra': 'extra field added',
    })
    try:
        FixedAsset.model_validate(model_constrains_with_extra_field_added)
    except ValidationError:
        assert True
    else:
        assert False
