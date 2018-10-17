import abc

class Engine(abc.ABC):

    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url

    def search(self, keyword):
        raise NotImplementedError
