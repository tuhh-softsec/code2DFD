

class CExternalEntity:

    def __init__(self, name):
        self.name = name
        self.stereotypes = list()
        self.tagged_values = list()

    def add_stereotype(self, stereotype):
        if not stereotype in self.stereotypes:
            self.stereotypes.append(stereotype)
        
    def add_tagged_value(self, tagged_value):
        if not tagged_value in self.tagged_values:
            self.tagged_values.append(tagged_value)
    