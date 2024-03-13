import os
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

from src.logger import Logger

from .job import Job


class JobHandler:
    def __init__(self) -> None:
        self.logger = Logger()
        self.engine = create_engine(os.environ["DB_URI"])
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

    def filter_new_data(
        self, new_job_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Checks new_job_data for jobs that already exist in database
        and removes them from the list
        """
        similar_jobs = self._get_similar_jobs(new_job_data)
        # if no similar jobs, new_job_data is ok
        if not similar_jobs:
            return new_job_data

        # merge dfs to get of each job
        filtered_df = pd.DataFrame(new_job_data).merge(
            pd.DataFrame(similar_jobs),
            how="left",
            on=["title", "company"],
        )
        # keep only jobs with no id (new jobs)
        filtered_df = filtered_df[filtered_df["id"].isna()]

        # if filtered_df is empty, new_job_data is duplicated
        if filtered_df.empty:
            return []

        # remove id column
        filtered_df.drop("id", axis="columns", inplace=True)

        # return list of dicts
        return filtered_df.to_dict(orient="records")

    def _get_similar_jobs(self, job_data: list[dict[str, Any]]):
        titles = [data["title"] for data in job_data]
        companies = [data["company"] for data in job_data]
        stmt = (
            select(Job.id, Job.title, Job.company)
            .where(Job.title.in_(titles))
            .where(Job.company.in_(companies))
        )
        with Session(self.engine) as session:
            return session.execute(stmt).all()
