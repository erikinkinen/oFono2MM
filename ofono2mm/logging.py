import inspect

def ofono2mm_print(message, verbose):
    if not verbose:
        return

    frame = inspect.currentframe()
    caller_frame = frame.f_back
    cls_name = caller_frame.f_locals['self'].__class__.__name__
    func_name = caller_frame.f_code.co_name

    full_message = f"{cls_name}.{func_name}: {message}"
    print(full_message)
