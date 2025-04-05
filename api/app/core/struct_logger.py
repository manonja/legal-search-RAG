"""
Structured logging configuration for the Legal Search RAG project.

This module sets up a structured logger using the `structlog` library, which provides
a powerful and flexible logging system. The logger is configured to output JSON-formatted
logs, making it easier to parse and analyze log data in various environments.

The module configures the following:
1. Basic logging configuration using Python's built-in logging module.
2. Structlog processors for enhanced log formatting and additional context.
3. Log level filtering based on the LOG_LEVEL environment variable.

Usage:
    from struct_logger import logger

    logger.info("This is an info message", extra_field="some value")
    logger.error("An error occurred", exc_info=True)

Environment Variables:
    LOG_LEVEL: Sets the logging level (default: "INFO")

Note:
----
    This module should be imported early in the application to ensure
    proper logging configuration across all modules.

"""

import logging
import os
import sys

import structlog

# Set up logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(stream=sys.stdout, format="%(message)s")
logging.getLogger().setLevel(LOG_LEVEL)

# Configure structlog
structlog.configure(
    processors=[
        # If log level is too low, abort pipeline and throw away log entry.
        structlog.stdlib.filter_by_level,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt="iso"),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If the "exc_info" key in the event dict is either true or a
        # sys.exc_info() tuple, remove "exc_info" and render the exception
        # with traceback into the "exception" key.
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a unicode str.
        structlog.processors.UnicodeDecoder(),
        # Add callsite parameters.
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        # Render the final event dict as JSON.
        structlog.processors.JSONRenderer(),
    ],
    # `wrapper_class` is the bound logger that you get back from
    # get_logger(). This one imitates the API of `logging.Logger`.
    wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, LOG_LEVEL)),
    # `logger_factory` is used to create wrapped loggers that are used for
    # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
    # string) from the final processor (`JSONRenderer`) will be passed to
    # the method of the same name as that you've called on the bound logger.
    logger_factory=structlog.stdlib.LoggerFactory(),
    # Effectively freeze configuration after creating the first bound
    # logger.
    cache_logger_on_first_use=True,
)

# Create a logger instance
logger = structlog.get_logger()
log = logger.bind(topic="legal-search-rag")
