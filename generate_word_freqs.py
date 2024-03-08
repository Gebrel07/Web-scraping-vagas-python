from src.models.job_descr_handler import JobDescrHandler


def main():
    print("Generating word freqs...")

    handler = JobDescrHandler(language="portuguese")
    res = handler.generate_word_freqs()

    print(f"Inserted: {res}")

    print("Done!")


if __name__ == "__main__":
    main()
