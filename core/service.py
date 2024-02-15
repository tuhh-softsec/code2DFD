

class CService:

    def __init__(self, name, stereotypes = list(), tagged_values = list()):
        self.name = name
        self.stereotypes = stereotypes
        self.tagged_values = tagged_values

    def add_stereotype(self, stereotype):
        if not stereotype in self.stereotypes:
            self.stereotypes.append(stereotype)
        
    def add_tagged_value(self, tagged_value):
        if not tagged_value in self.tagged_values:
            self.tagged_values.append(tagged_value)
    