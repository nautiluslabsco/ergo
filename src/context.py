

class ErgoContext:
    def __init__(self, subtopic=None, pubtopic=None):
        self.subtopic = subtopic
        self.pubtopic = pubtopic
        #TODO: maybe we have from_config() func that grabs and holds a config object OR maps those vals to vals here?
        #TODO: make setters that do #.#.# thing for each property