from build.util import project_wheel_metadata
from jaraco.ui.main import main


@main
def run(path='.', field='Requires-Dist'):
    for spec in project_wheel_metadata(path).get_all(field):
        print(spec)
