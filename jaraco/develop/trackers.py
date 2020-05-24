import re
import itertools
import urllib.request
import urllib.parse

try:
    import html5lib.treebuilders
except ImportError:
    # html5lib not available on Python 3 so suppress import errors
    pass

from .patch import Patch


class RoundupTracker(object):
    """
    An object representing a RoundUp issue (referenced by URL).
    """

    def __init__(self, url):
        self.url = url

    def get_patch_refs(self):
        return (
            urllib.parse.urljoin(self.url, link.parent['href'])
            for link in self.find_patch_links()
        )

    @staticmethod
    def patch_number(link):
        number = re.compile(r'\d+(\.\d+)?')
        return float(number.search(link.string).group(0))

    def find_patch_links(self):
        # note, this will only work if BeautifulSoup is present
        parser = html5lib.HTMLParser(
            tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup")
        )
        soup = parser.parse(urllib.request.urlopen(self.url))
        files = soup.find(attrs='files')
        links = files.findAll(text=re.compile(r'.*\.patch'))
        links.sort(key=self.patch_number, reverse=True)
        return links

    def get_patches(self):
        return itertools.imap(Patch.urlopen, self.get_patch_refs())

    def get_latest_patch(self):
        return next(self.get_patches())


class PythonBugTracker(RoundupTracker):
    def __init__(self, id):
        url = 'http://bugs.python.org/issue' + str(id)
        super(PythonBugTracker, self).__init__(url)
