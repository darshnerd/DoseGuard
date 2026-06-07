import logging


def set_logging(level = "INFO"):
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s"
    )
