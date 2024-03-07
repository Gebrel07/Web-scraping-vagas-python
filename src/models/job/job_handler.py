import os
from typing import Any

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session

from src.logger import Logger

from .job import Job


class JobHandler:
    def __init__(self) -> None:
        self.logger = Logger()
        self.engine = create_engine(os.environ["SQLITE_URI"])
        Job.metadata.create_all(self.engine)

    def insert_many(self, jobs: list[dict[str, Any]]):
        with Session(self.engine) as session:
            try:
                session.execute(insert(Job), jobs)
                session.commit()
                return len(jobs)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                session.rollback()
                return 0
