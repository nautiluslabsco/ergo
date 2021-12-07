from src.topic import SubTopic, PubTopic


class ErgoContext:
    def __init__(self, subtopic: SubTopic = None, pubtopic: PubTopic = None):
        self._subtopic = subtopic
        self._pubtopic = pubtopic

    @property
    def subtopic(self):
        return self._subtopic

    @subtopic.setter
    def subtopic(self, value: str):
        self._subtopic = SubTopic(value)

    @property
    def pubtopic(self):
        return self._pubtopic

    @pubtopic.setter
    def pubtopic(self, value: str):
        self._pubtopic = PubTopic(value)