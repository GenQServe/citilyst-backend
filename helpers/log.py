import logging
import sys
import os
from datetime import datetime
from helpers.config import settings


def setup():
    # Set up main application logging
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    if app_logger.handlers:
        app_logger.handlers.clear()

    # Create formatters
    main_formatter = logging.Formatter(
        "%(levelname)s - %(asctime)s - %(filename)s:%(lineno)d - %(message)s"
    )
    sql_formatter = logging.Formatter("SQL - %(asctime)s - %(message)s")

    # Create console handler for app logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(main_formatter)
    console_handler.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)

    # Setup file logging for application logs
    try:
        log_dir = "logs"
        if settings.is_production:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            today = datetime.now().strftime("%Y-%m-%d")
            app_file_handler = logging.FileHandler(f"{log_dir}/app_{today}.log")
            app_file_handler.setFormatter(main_formatter)
            app_file_handler.setLevel(logging.INFO)
            app_logger.addHandler(app_file_handler)

            # Optional: Setup SQL logging to separate file
            sql_logger = logging.getLogger("sqlalchemy.engine")
            sql_logger.setLevel(
                logging.INFO
            )  # Still capture SQL but to a different file
            sql_file_handler = logging.FileHandler(f"{log_dir}/sql_{today}.log")
            sql_file_handler.setFormatter(sql_formatter)
            sql_logger.addHandler(sql_file_handler)

            # Remove SQL logging from console
            sql_logger.propagate = False
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    # Reduce noise from other libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    app_logger.info("Logging setup complete")

    # Return the app logger to use in the application
    return app_logger
