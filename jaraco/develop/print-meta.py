import autocommand
from pep517 import meta


@autocommand.autocommand(__name__)
def main(path='.', field='Requires-Dist'):
    md = meta.load(path).metadata
    for spec in md.get_all(field):
        print(spec)
