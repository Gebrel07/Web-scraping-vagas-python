from typing import Any

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class Google:
    """Job results from Google

    Uses Firefox
    """

    def __init__(self, headless: bool = False) -> None:
        self._base_url = "https://www.google.com"

        # NOTE: add this parameter to the url to force Google
        # to redirect the browser to the Jobs list page instead of
        # the normal results page
        self._joblist_param = "ibp=htl;jobs"

        # set driver options
        self._driver_options = webdriver.FirefoxOptions()
        if headless:
            self._driver_options.add_argument("-headless")

        # start driver
        self._driver = webdriver.Firefox(options=self._driver_options)

    def gather_job_data(self, search_term: str, limit: int = 20):
        url = self._make_search_url(search_term)
        self._search_jobs(url)

        job_data: list[dict[str, Any]] = []
        joblist = self._get_joblist()
        while True:
            # stop if limit is reached
            if len(job_data) >= limit:
                break

            # get job data
            job_data.extend(self._get_data(joblist))

            # get updated job list
            new_joblist = self._get_joblist()

            # stop if there are no new jobs in list
            if len(new_joblist) <= len(job_data):
                break

            # update joblist with new jobs only
            joblist = new_joblist[len(job_data):]

        self._driver.close()

        return job_data

    def _get_data(self, joblist: list[WebElement]):
        res: list[dict[str, Any]] = []
        for job in joblist:
            job.click()
            data = {
                "title": self._get_title(),
                "company": self._get_company_name(),
                "location": self._get_location(),
                "platform": self._get_platform(),
                "description": self._get_description(),
            }
            res.append(data)
        return res

    def _make_search_url(self, search_term: str):
        search_term = search_term.replace(" ", "+").lower()
        return f"{self._base_url}/search?q={search_term}&{self._joblist_param}"

    def _search_jobs(self, url: str):
        self._driver.get(url)

    def _get_joblist(self):
        return self._driver.find_elements(By.CLASS_NAME, "iFjolb")

    def _get_title(self):
        # xpath = "./div/div[1]/div[2]/div/div/div[2]/div[2]"
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/div[1]/div/"
            "div[1]/h2"
        )
        return self._driver.find_element(By.XPATH, xpath).text

    def _get_company_name(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/div[1]/div/"
            "div[2]/div[2]/div[1]"
        )
        return self._driver.find_element(By.XPATH, xpath).text

    def _get_location(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/div[1]/div/"
            "div[2]/div[2]/div[2]"
        )
        try:
            return self._driver.find_element(By.XPATH, xpath).text
        except NoSuchElementException:
            # some jobs have no location
            return None

    def _get_description(self):
        try:
            return self._get_short_description()
        except NoSuchElementException:
            return self._get_long_description()

    def _get_short_description(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/div[4]/span"
        )
        return self._driver.find_element(By.XPATH, xpath).text

    def _get_long_description(self):
        # parent span (first part of description)
        parent_span_xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/div[4]/div/span"
        )
        parent_span = self._driver.find_element(By.XPATH, parent_span_xpath)

        # child span (second part of description, display = none)
        child_span_xpath = parent_span_xpath + "/span[2]"
        child_span = self._driver.find_element(By.XPATH, child_span_xpath)

        # change visibility of span to capture text
        self._driver.execute_script(
            "arguments[0].style.display = 'block'", child_span
        )

        return parent_span.text + child_span.text

    def _get_platform(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/g-scrolling-carousel/"
            "div[1]/div/span/div/span[1]/a/div/div/span"
        )
        return self._driver.find_element(By.XPATH, xpath).text
