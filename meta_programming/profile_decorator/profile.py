from functools import wraps
import time
import inspect
import re
 
 
def profile(to_decorate):
    if inspect.isfunction(to_decorate):
        function_name_format = re.compile('(?P<type>.*) (?P<name>.*) (?P<at>.*) (?P<reference>.*)')
        match = function_name_format.match(repr(to_decorate))
        if not match:
            raise Exception('Incorrect func_name format')
 
        @wraps(to_decorate)
        def wrapper(*args, **kwargs):
            name = match.group('name')
            print(f'\'{name}\' started')
            start_time = time.time()
            result = to_decorate(*args, **kwargs)
            time_spend = start_time - time.time()
            print(f'\'{name}\' finished in {time_spend}s')
            return result
        return wrapper
    elif inspect.isclass(to_decorate):
        for attribute in to_decorate.__dict__:
            if inspect.isfunction(getattr(to_decorate, attribute)):
                setattr(to_decorate, attribute, profile(getattr(to_decorate, attribute)))
        return to_decorate
    else:
        raise Exception('Type of decorating obj should be func or class')