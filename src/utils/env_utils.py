import os

get_int = lambda key, default: int(os.getenv(key, default))
get_bool = lambda name, default: str(os.getenv(name, default)).lower() == "true"
get_list = lambda name, default="", sep=',': [v for v in os.getenv(name, default).split(sep) if v]
get_str = lambda name, default: os.getenv(name, default)
get_float = lambda name, default: float(os.getenv(name, default))