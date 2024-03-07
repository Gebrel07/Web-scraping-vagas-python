import logging


class Logger(logging.getLoggerClass()):
    def __init__(self, name: str = "main", level: int | str = 0) -> None:
        super().__init__(name, level)

        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # file
        self.__ERR_FILENAME = "err.log"
        file_handler = logging.FileHandler(self.__ERR_FILENAME)
        file_handler.setFormatter(formatter)

        # console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.addHandler(file_handler)
        self.addHandler(stream_handler)
