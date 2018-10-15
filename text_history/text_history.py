class TextHistory:
    _text = ''
    _version = 0

    def __init__(self):
        pass


class Action:
    pass


class InsertAction(Action):
    pass


class ReplaceAction(Action):
    pass


class DeleteAction(Action):
    pass


t = TextHistory()
print(t._text)
