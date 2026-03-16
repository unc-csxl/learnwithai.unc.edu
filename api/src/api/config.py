from learnwithai.config import get_settings, Settings
from typing import TypeAlias, Annotated
from fastapi import Depends

SettingsDI: TypeAlias = Annotated[Settings, Depends(get_settings)]
