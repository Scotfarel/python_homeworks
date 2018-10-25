from abc import abstractmethod


class TextHistory:
    def __init__(self):
        self._text = ''
        self._version = 0
        self._actions = []

    @property
    def text(self):
        return self._text

    @property
    def version(self):
        return self._version

    @property
    def actions(self):
        return self._actions

    def action(self, action):
        if action.from_version != self.version or action.from_version >= action.to_version:
            raise ValueError
        self._text = action.apply(self.text)
        self._version = action.to_version
        return self.version

    def insert(self, text, pos=None):
        if pos is None:
            pos = len(self.text)
        if pos < 0 or pos > len(self.text):
            raise ValueError

        action = InsertAction(pos, text, self.version, self.version + 1)

        return self.action(action)

    def replace(self, text, pos=None):
        if pos is None:
            pos = len(self.text)
        if pos < 0 or pos > len(self.text):
            raise ValueError

        action = ReplaceAction(pos, text, self.version, self.version + 1)

        return self.action(action)

    def delete(self, pos, length):
        pass

    def get_actions(self, from_version=0, to_version=0):
        pass


class Action:
    def __init__(self, from_version, to_version):
        self._from_version = from_version
        self._to_version = to_version

    @abstractmethod
    def apply(self, mutable_string):
        pass

    @property
    def from_version(self):
        return self._from_version

    @property
    def to_version(self):
        return self._to_version


class InsertAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        super().__init__(from_version, to_version)
        self._pos = pos
        self._text = text

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def apply(self, text):
        return text[:self.pos] + self.text + text[self.pos:]


class ReplaceAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        super().__init__(from_version, to_version)
        self._pos = pos
        self._text = text

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def apply(self, text):
        offset = len(self.text)
        if self.pos + offset > len(text):
            return text[:self.pos] + self.text
        return text[:self.pos] + self.text + text[self.pos + len(self.text):]


class DeleteAction(Action):
    def __init__(self, pos, length, from_version, to_version):
        super().__init__(from_version, to_version)
        self._pos = pos
        self._length = length

    @property
    def pos(self):
        return self._pos

    @property
    def length(self):
        return self._length

    def apply(self, mutable_string):
        pass
