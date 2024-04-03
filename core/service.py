

class CService:

    def __init__(self, name, stereotypes = list(), tagged_values = list(), properties = list()):
        self.name = name
        self.stereotypes = stereotypes
        self.tagged_values = tagged_values
        self.properties = properties

    def __str__(self):
        return f"Service \"{self.name}\"\n\tStereotypes: {str(self.stereotypes)}\n\tTagged values: {str(self.tagged_values)}\n\tProperties: {str(self.properties)}"

    def add_stereotype(self, stereotype):
        if not stereotype in self.stereotypes:
            self.stereotypes.append(stereotype)
        
    def add_tagged_value(self, tagged_value):
        if not tagged_value in self.tagged_values:
            self.tagged_values.append(tagged_value)
    