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

    def increase_version(self):
        return self.version + 1

    def check_pos(self, pos):
        if pos > len(self.text) or pos < 0:
            raise ValueError

    def action(self, action):
        if action.from_version != self.version or action.from_version >= action.to_version:
            raise ValueError
        self._text = action.apply(self.text)
        self._version = action.to_version
        self._actions.append(action)

        return self.version

    def insert(self, text, pos=None):
        if pos is None:
            pos = len(self.text)
        self.check_pos(pos)

        action = InsertAction(pos, text, self.version, self.increase_version())

        return self.action(action)

    def replace(self, text, pos=None):
        if pos is None:
            pos = len(self.text)
        self.check_pos(pos)

        action = ReplaceAction(pos, text, self.version, self.increase_version())

        return self.action(action)

    def delete(self, pos, length):
        self.check_pos(pos)

        action = DeleteAction(pos, length, self.version, self.increase_version())

        return self.action(action)

    def get_actions(self, from_version=0, to_version=None):
        if to_version is None:
            to_version = self.version

        if from_version < 0 or to_version > self.version or to_version < from_version:
            raise ValueError

        return self.actions[from_version:to_version]

    def optimize_insert(self):
        changed = False
        for idx, action in enumerate(self.actions):
            if action == self.actions[-1]:
                break
            if isinstance(action, InsertAction) and isinstance(self.actions[idx + 1], InsertAction) \
                    and action.pos + len(action.text) == self.actions[idx + 1].pos:

                new_text = action.text + self.actions[idx + 1].text
                new_action = InsertAction(action.pos, new_text, self.version, self.increase_version())

                self.replace_optimized_actions(idx, new_action)
                changed = True
        if changed:
            self.optimize_insert()

    def optimize_replace(self):
        changed = False
        for idx, action in enumerate(self.actions):
            if action == self.actions[-1]:
                break
            if isinstance(action, ReplaceAction) and isinstance(self.actions[idx + 1], ReplaceAction) \
                    and action.pos + len(action.text) == self.actions[idx + 1].pos:

                new_text = action.text + self.actions[idx + 1].text
                new_action = ReplaceAction(action.pos, new_text, self.version, self.increase_version())

                self.replace_optimized_actions(idx, new_action)
                changed = True
        if changed:
            self.optimize_replace()

    def optimize_delete(self):
        changed = False
        for idx, action in enumerate(self.actions):
            if action == self.actions[-1]:
                break
            if isinstance(action, DeleteAction) and isinstance(self.actions[idx + 1], DeleteAction) \
                    and action.pos == self.actions[idx + 1].pos:

                new_length = action.length + self.actions[idx + 1].length
                new_action = DeleteAction(action.pos, new_length, self.version, self.increase_version())

                self.replace_optimized_actions(idx, new_action)
                changed = True
        if changed:
            self.optimize_delete()

    def replace_optimized_actions(self, idx, new_action):
        self.actions.pop(idx + 1)
        self.actions.pop(idx)
        self.actions.insert(idx, new_action)

    def optimize_actions(self):
        self.optimize_insert()
        self.optimize_replace()
        self.optimize_delete()


class Action:
    def __init__(self, from_version, to_version):
        self._from_version = from_version
        self._to_version = to_version

    @abstractmethod
    def apply(self, text):
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

    def apply(self, text):
        if self.pos + self.length > len(text):
            raise ValueError
        return text[:self.pos] + text[self.pos + self.length:]
