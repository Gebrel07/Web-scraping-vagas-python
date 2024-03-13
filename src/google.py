from typing import Any, Literal

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox, FirefoxOptions, Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .logger import Logger


class Google:
    """Job results from Google

    Uses Firefox
    """

    def __init__(self, headless: bool = True) -> None:
        self._base_url = "https://www.google.com"

        # NOTE: add this parameter to the url to force Google
        # to redirect the browser to the Jobs list page instead of
        # the normal results page
        self._joblist_param = "ibp=htl;jobs"

        # set driver options
        self._driver_options = FirefoxOptions()
        if headless:
            self._driver_options.add_argument("-headless")

        self._driver: Remote | None = None

        self._logger = Logger()

    def open_driver(self):
        self._driver = Firefox(options=self._driver_options)

    def close_driver(self):
        self._driver.close()
        self._driver = None

    def gather_job_data(
        self,
        search_term: str,
        limit: int = 50,
        language: Literal["pt", "en", "es"] | None = None,
    ):
        url = self._make_search_url(search_term=search_term)
        if language:
            url = self._set_lang(url=url, lang=language)

        self._search_jobs(url)

        # NOTE: Wait for url to change: google reloads the page with a different url after
        # the initial search. Due to the page reload, this is necessary to avoid
        # StaleElement exception when using the joblist
        res = WebDriverWait(self._driver, 5).until(EC.url_changes(url))

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
            joblist = new_joblist[len(job_data) :]

        return job_data

    def _get_data(self, joblist: list[WebElement]):
        res: list[dict[str, Any]] = []
        for job in joblist:
            job.click()
            if not self._wait_for_job_div():
                continue
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

    def _set_lang(self, url: str, lang: str):
        lang_params = (
            f"htischips=language:{lang}#htivrt=jobs&"
            f"htichips=language:{lang}&"
            f"htischips=language;{lang}"
        )
        return f"{url}&{lang_params}"

    def _search_jobs(self, url: str):
        self._driver.get(url)

    def _get_joblist(self):
        return self._driver.find_elements(By.CLASS_NAME, "iFjolb")

    def _wait_for_job_div(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div"
        )
        try:
            WebDriverWait(self._driver, timeout=5).until(
                method=EC.presence_of_element_located((By.XPATH, xpath)),
                message="Job data did not load",
            )
            return True
        except Exception as err:
            self._logger.error(err, exc_info=True)
            return False

    def _get_title(self):
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
        self._driver.execute_script("arguments[0].style.display = 'block'", child_span)

        return parent_span.text + child_span.text

    def _get_platform(self):
        xpath = (
            "/html/body/div[2]/div/div[2]/"
            "div[1]/div/div/div[3]/div[2]/"
            "div/div[1]/div/div/g-scrolling-carousel/"
            "div[1]/div/span/div/span[1]/a/div/div/span"
        )
        return self._driver.find_element(By.XPATH, xpath).text
