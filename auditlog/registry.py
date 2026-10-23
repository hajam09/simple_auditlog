_audited_models = set()


def register(model):
    """
    Register a model for audit logging.
    Can be used as a decorator or a function.
    """
    _audited_models.add(model)
    return model


def is_registered(sender):
    return sender in _audited_models


def get_registered_models():
    return _audited_models
