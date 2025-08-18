from app.models.schema import CommonParams

def get_common_params(search: str | None = None, limit: int = 10, offset: int = 0):
    return CommonParams(search=search, limit=limit, offset=offset)
