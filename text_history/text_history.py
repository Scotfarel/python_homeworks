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

    def action(self, act):
        if self._version != act.from_version or act.from_version == act.to_version:
            raise ValueError
        self._version = act.to_version
        self._text = act.text

        return self._version

    def insert(self, ins_str, pos=None):
        if pos is None:
            pos = len(self._text)

        action = InsertAction(pos, ins_str, self.version, self.version + 1)
        self._text = action.apply(ins_str)
        return self.action(action)

    def replace(self, rep_str, pos=None):
        pass

    def delete(self, pos=None, length=0):
        pass

    def get_actions(self, from_version=0, to_version=0):
        # TODO(@me): wrapper for actions
        # return wrapper(self._actions)
        pass


class Action:
    def __init__(self, from_version, to_version):
        self._from_version = from_version
        self._to_version = to_version

    @abstractmethod
    def apply(self, insert_str):
        pass

    @property
    def from_version(self):
        return self._from_version

    @property
    def to_version(self):
        return self._to_version


class InsertAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        self._pos = pos
        self._text = text
        super().__init__(from_version, to_version)

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def apply(self, insert_str):
        self._text = self.text[:self.pos] + insert_str + self.text[self.pos:]
        return self.text


class ReplaceAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        self._pos = pos
        self._text = text
        super().__init__(from_version, to_version)

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def apply(self, insert_str):
        return self.text

    def _replace(self, insert_str, pos):
        pass


class DeleteAction(Action):
    def __init__(self, pos, length, from_version, to_version):
        self._pos = pos
        self._length = length
        super().__init__(from_version, to_version)

    @property
    def pos(self):
        return self._pos

    @property
    def length(self):
        return self._length

    def apply(self, old_text, insert_str):
        pass

    def _delete(self, pos, del_len):
        pass
