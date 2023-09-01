

class CInformationFlow:

    def __init__(self, sender, receiver):
        self.sender = sender
        self.receiver = receiver
        self.name = f"{self.sender} -> {self.receiver}"
        self.stereotypes = list()
        self.tagged_values = list()

    def add_stereotype(self, stereotype):
        self.stereotypes = list(set(self.stereotypes.append(stereotype)))
        
    def add_tagged_value(self, tagged_value):
        self.tagged_values = list(set(self.tagged_values.append(tagged_value)))
        