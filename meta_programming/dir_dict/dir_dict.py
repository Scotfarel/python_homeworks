from collections.abc import MutableMapping
import os
 
 
class DirDict(MutableMapping):
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            os.makedirs(path)
 
    def __getitem__(self, item):
        filepath = os.path.join(self.path, str(item))
        if not os.path.exists(filepath):
            raise KeyError(f'{item}')
        with open(os.path.join(self.path, str(item)), 'r', encoding='utf8') as f_obj:
            data = f_obj.read()
            return data
 
    def __setitem__(self, key, value):
        with open(os.path.join(self.path, str(key)), 'w', encoding='utf8') as f_obj:
            f_obj.write(str(value))
 
    def __delitem__(self, key):
        filepath = os.path.join(self.path, str(key))
        if not os.path.exists(filepath):
            raise KeyError(f'{key}')
        os.remove(os.path.join(self.path, str(key)))
 
    def __iter__(self):
        filenames_lst = os.listdir(self.path)
        return iter(filenames_lst)
 
    def __len__(self):
        filenames_lst = os.listdir(self.path)
        return len(filenames_lst)