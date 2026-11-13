import logging

logger = logging.getLogger("taskflow")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.setLevel(level)
