class Keyword(str):
    def __call__(self, other):
        return self in other


class Tag(str):
    def __call__(self, other):
        return self in other.tags
