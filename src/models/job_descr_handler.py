import os
from typing import Any

import nltk
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

from src.logger import Logger

from .job import Job
from .job_descr import JobDescr


class JobDescrHandler:
    def __init__(self, language: str) -> None:
        self.language = language

        self.logger = Logger()

        # create table if it doesnt exist
        self.engine = create_engine(os.environ["DB_URI"])
        JobDescr.metadata.create_all(self.engine)

        # install nltk data in virtual environment
        self._NLTK_DIR = ".venv/nltk_data"
        nltk.download("punkt", quiet=True, download_dir=self._NLTK_DIR)  # tokenizer
        nltk.download("stopwords", quiet=True, download_dir=self._NLTK_DIR)

    def generate_word_freqs(self):
        """Generate work frequencies for all companies
        and stores them in database
        """
        inserted = 0
        companies = self._get_companies()
        for company in companies:
            freqs = self._generate_company_freqs(company)
            freqs_json = self._freqs_to_json(company, freqs)
            res = self.insert_many(freqs_json)
            inserted += res
        return inserted

    def _get_companies(self):
        """Get unique company names"""
        stmt = select(Job.company).order_by(Job.company.asc()).distinct()
        with Session(self.engine) as session:
            return session.scalars(stmt).all()

    def _generate_company_freqs(self, company: str):
        """Generate word frequency for specific company"""
        # get job descriptions
        descr_list = self._get_job_descrs(company)
        # join all descriptions
        descrs_str = "".join(descr_list)
        # tokenize words
        tokens = word_tokenize(descrs_str, language=self.language)
        # filter tokens
        stopwords = nltk.corpus.stopwords.words(self.language)
        tokens = self._handle_tokens(tokens=tokens, stopwords=stopwords)
        # get word freq
        freqs = FreqDist(tokens)
        return freqs.most_common()

    def _handle_tokens(self, tokens: list[str], stopwords: list[str]):
        res = []
        for token in tokens:
            token = token.lower().replace(" ", "")
            if len(token) < 3:
                continue
            if not token.isalnum():
                continue
            if token.isnumeric():
                continue
            if token in stopwords:
                continue
            res.append(token)
        return res

    def _freqs_to_json(self, company: str, freqs: list[Any]):
        """Convert word frequency to json list"""
        res = []
        for word, freq in freqs:
            res.append({"company": company, "word": word, "freq": freq})
        return res

    def _get_job_descrs(self, company: str):
        """Query job descriptions for specific company"""
        stmt = select(Job.description).where(Job.company == company)
        with Session(self.engine) as session:
            return session.scalars(stmt).all()

    def insert_many(self, freqs: list[dict[str, Any]]):
        with Session(self.engine) as session:
            try:
                session.execute(insert(JobDescr), freqs)
                session.commit()
                return len(freqs)
            except Exception as err:
                self.logger.error(err, exc_info=True)
                session.rollback()
                return 0
