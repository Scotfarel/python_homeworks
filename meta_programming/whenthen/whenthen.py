from functools import wraps
 
 
def whenthen(func_to_decorate):
    conditions_lst = []
    actions_lst = []
 
    @wraps(func_to_decorate)
    def when(condition_func):
        if len(conditions_lst) != len(actions_lst):
            raise Exception('Conditions don\'t match to their actions')
        conditions_lst.append(condition_func)
        return wrapper
 
    @wraps(func_to_decorate)
    def then(action_func):
        if len(conditions_lst) - 1 != len(actions_lst):
            raise Exception('Actions don\'t match to their conditions')
        actions_lst.append(action_func)
        return wrapper
 
    @wraps(func_to_decorate)
    def wrapper(*args, **kwargs):
        for condition, action in zip(conditions_lst, actions_lst):
            if condition(*args, **kwargs):
                return action(*args, **kwargs)
        return func_to_decorate(*args, **kwargs)
 
    wrapper.when = when
    wrapper.then = then
    return wrapper