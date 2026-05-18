class ApplicationError(Exception):
    pass


class AccountNotFoundError(ApplicationError):
    pass


class InsufficientFundsError(ApplicationError):
    pass


class DuplicateTransactionError(ApplicationError):
    pass


class InvalidOperationError(ApplicationError):
    pass
