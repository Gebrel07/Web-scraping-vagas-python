from dotenv import load_dotenv

from src.google import Google
from src.logger import Logger
from src.models.job_handler import JobHandler


def main():
    # load environment variables from file
    load_dotenv(".env")

    handler = JobHandler()

    print("Collecting data...")
    g = Google(headless=False)
    g.open_driver()
    job_data = g.gather_job_data(search_term="python", limit=300)
    g.close_driver()

    print("Processing data...")
    filtered_data = handler.filter_new_data(job_data)
    if not filtered_data:
        print("No new data found.")
        return None

    print("Inserting in database...")
    res = handler.insert_many(filtered_data)
    print(f"Inserted: {res}")


if __name__ == "__main__":
    logger = Logger()

    try:
        main()
        print("Done!")
    except Exception as err:
        logger.error(err, exc_info=True)
