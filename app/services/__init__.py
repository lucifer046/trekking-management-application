"""
Business-logic layer. Every route handler that needs to mutate booking
state, trek status, staff approval, or write a review/notification/audit
entry should call into one of these modules rather than touching models
directly; this is what keeps the rules testable without a request
context and prevents the same logic being reimplemented slightly
differently in the admin vs staff vs user blueprints.
"""
