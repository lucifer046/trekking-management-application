class ServiceError(Exception):
    """Raised by service-layer functions when a business rule is
    violated (overbooking, illegal status transition, unauthorized
    assignment, ...). Routes catch this one exception type and flash
    str(err) rather than needing to know each service's specific guard
    conditions."""
