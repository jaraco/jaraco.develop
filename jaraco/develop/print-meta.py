from typing import Any, List, cast

from build.util import project_wheel_metadata
from jaraco.ui.main import main


@main
def run(path: str = '.', field: str = 'Requires-Dist'):
    for spec in cast(List[Any], project_wheel_metadata(path).get_all(field)):
        print(spec)
