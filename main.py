from dotenv import load_dotenv

from src.google import Google
from src.logger import Logger
from src.models.job.job_handler import JobHandler


def main():
    # load environment variables from file
    load_dotenv(".env")

    handler = JobHandler()

    print("Collecting data...")

    g = Google(headless=True)
    job_data = g.gather_job_data(search_term="python", limit=5)

    print("Collection done.")

    # TODO: make sure there Job data doesnt already
    # exist in db before inserting use title + company as search params
    print("Inserting in database...")

    res = handler.insert_many(job_data)

    print(f"Inserted: {res}")

    print("Done!")


if __name__ == "__main__":
    logger = Logger()

    try:
        main()
    except Exception as err:
        logger.error(err, exc_info=True)
