class Value:
    def __init__(self, value, mask):
        if mask == 0 or (value & mask) != value:
            raise ValueError()
        self.value = value
        self.mask = mask
    
    def __or__(self, other):
        if (self.mask & other.mask) != 0:
            raise ValueError()
        return Value(self.value | other.value, self.mask | other.mask)


class Group:
    def __init__(self, count, offset):
        if count <= 0 or offset < 0:
            raise ValueError()
        self.mask = (2**count - 1) << offset
        self.values = tuple((i << offset for i in range(2**count)))
    
    def __getitem__(self, i):
        return self.values[i]
    
    def get(self, *values):
        return tuple((self[i] for i in values))
    
    def all(self):
        return self.values


def generate_groups(*counts):
    offset = 0
    for count in counts:
        yield Group(count, offset)
        offset += count


def make_groups(*counts):
    return tuple(generate_groups(*counts))
