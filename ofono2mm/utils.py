import asyncio
import os

settings_dir = '/var/lib/ofono2mm'
settings_file = os.path.join(settings_dir, 'settings.conf')

def async_retryable(times=0):
    """
    Decorator that allows to retry the given function n times.

    Usage:

    @async_retryable(5)
    async def fail():
        raise Exception("This function will be tried five times!")

    If times is 0 (default), the function will be retried indefinitely.
    """

    def decorator(func):
            async def wrapper(*args, **kwargs):
                    current_try = 0
                    while times == 0 or current_try < times:
                            try:
                                    result = await func(*args, **kwargs)
                            except Exception as e:
                                    if current_try == times-1:
                                            raise

                                    # print("Trying again, error was %s" % e)
                                    await asyncio.sleep(5)

                                    current_try += 1
                            else:
                                    return result

            return wrapper

    return decorator

def async_locked(func):
    async def wrapper(*args, **kwargs):
        async with func.__lock:
            return await func(*args, **kwargs)

    func.__lock = asyncio.Lock()
    return wrapper

def save_setting(key, value):
    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir)

    settings = parse_settings()

    settings[key] = value

    with open(settings_file, 'w') as file:
        for k, v in settings.items():
            file.write(f"{k}: {v}\n")

def read_setting(key):
    settings = parse_settings()
    return str(settings.get(key, False))

def parse_settings():
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as file:
            for line in file:
                if ':' in line:
                    k, v = line.strip().split(':', 1)
                    settings[k] = v
    return settings
