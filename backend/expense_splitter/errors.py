class StoreError(Exception):
    """Base class for domain errors raised by a store."""


class NotFoundError(StoreError):
    """The requested entity does not exist."""


class ConflictError(StoreError):
    """The operation conflicts with existing state (e.g. a member still in use)."""


class ValidationError(StoreError):
    """The payload violates a business rule."""