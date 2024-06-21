import autocommand

from build.util import project_wheel_metadata


@autocommand.autocommand(__name__)
def main(path='.', field='Requires-Dist'):
    for spec in project_wheel_metadata(path).get_all(field):
        print(spec)
