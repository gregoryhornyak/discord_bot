import requests
from bs4 import BeautifulSoup
import logging
import pandas as pd

LOGS_PATH = "resources/logs/"

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] - %(levelname)s : %(message)s') # maybe terminal doesnt need time and levelname

file_handler = logging.FileHandler(f"{LOGS_PATH}botlogs.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

class F1DataFetcher:
    # class variables:
    ## race details
    prev_race_id = 0
    prev_race_name = ""
    free_prac_ser_num = 1

    ## common lists
    best_three = ['Ferrari','Red Bull Racing Honda RBPT','Mercedes']

    ## urls
    all_races_url = "https://www.formula1.com/en/results.html/2023/races.html"
    prev_race_results_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/race-result.html"
    prev_qual_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/qualifying.html"
    prev_free_prac_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/practice-"
    prev_sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/sprint-results.html"
    prev_dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
    prev_rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"

    ## race types and scores

    q1st,q2nd,q3rd,q_botr,r1st,r2nd,r3rd,r_botr,dotd,r_fast,r_dnf = [0] * 11

    free_practice = {'fp1':0,'fp2':0,'fp3':0}

    def __init__(self):
        pass

    def _update_urls(self) -> None:
        prev_race_id = F1DataFetcher.prev_race_id
        prev_race_name = F1DataFetcher.prev_race_name
        F1DataFetcher.prev_race_results_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/race-result.html"
        F1DataFetcher.prev_qual_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/qualifying.html"
        F1DataFetcher.prev_free_prac_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/practice-"
        F1DataFetcher.prev_sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/sprint-results.html"
        F1DataFetcher.prev_dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
        F1DataFetcher.prev_rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"

    def update_url(self):
        self._update_urls()

    def _request_and_get_soap(self,url,fpN=0) -> BeautifulSoup:
        self._update_urls()
        if fpN != 0:
            url = url+f"{fpN}.html"
        response = requests.get(url).text
        soap = BeautifulSoup(response, 'html.parser')
        return soap

    def _join_names(self,start=2,end=4):
        return lambda arr: ' '.join(arr[start:end])

    def get_prev_race_id_and_name(self) -> None:
        """updates local-class id and name"""
        all_races_soup = self._request_and_get_soap(F1DataFetcher.all_races_url)
        all_races_names_data = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
        all_races_names = [name.get_text().strip() for name in all_races_names_data]
        all_races_ids_data = all_races_soup.find_all('a', class_='ArchiveLink')
        all_races_ids = [name.get('href') for name in all_races_ids_data]
        all_races_ids_text = [name.split('/')[5] for name in all_races_ids]
        previous_race_id = all_races_ids_text[-1]
        previous_race_name = all_races_names[-1]
        logger.info(f"{previous_race_id = }\n{previous_race_name = }")
        F1DataFetcher.prev_race_id = previous_race_id
        F1DataFetcher.prev_race_name = previous_race_name

    def get_prev_race_results(self) -> None:
        """ r1-3, r-botr, r-dnf results """
        prev_race_soap = self._request_and_get_soap(F1DataFetcher.prev_race_results_url)
        prev_race_table = prev_race_soap.find_all('tr')
        prev_race_table_text = [name.get_text().strip() for name in prev_race_table]
        prev_race_table_text_clear = [name.split("\n") for name in prev_race_table_text]
        prev_race_table_filtered = [[item for item in original_list if item.strip() != ''] for original_list in prev_race_table_text_clear]
        prev_race_table_header = prev_race_table_filtered[0]
        prev_race_table_filtered_values = prev_race_table_filtered[1:]
        join_names = self._join_names()
        prev_race_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_race_table_filtered_values]
        prev_race_table_df = pd.DataFrame(prev_race_table_clean, columns=prev_race_table_header)
        logger.info(f"{prev_race_table_df = }")
        
        F1DataFetcher.r1st = prev_race_table_df.loc[0]['Driver']
        F1DataFetcher.r2nd = prev_race_table_df.loc[1]['Driver']
        F1DataFetcher.r3rd = prev_race_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_race_table_df['Driver'], prev_race_table_df['Car'])):
            if team not in F1DataFetcher.best_three:
                F1DataFetcher.r_botr = driver
                break

        for state in prev_race_table_df['Time/Retired']:
            if state in ['DNS','DNF']:
                F1DataFetcher.r_dnf += 1

    def get_prev_qual_results(self):
        """find out QUALIFYING results in previous race"""
        prev_qual_soap = self._request_and_get_soap(F1DataFetcher.prev_qual_url)
        prev_qual_table = prev_qual_soap.find_all('tr')
        prev_qual_table_text = [name.get_text().strip() for name in prev_qual_table]
        prev_qual_table_text_clear = [name.split("\n") for name in prev_qual_table_text]
        prev_qual_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_qual_table_text_clear]
        prev_qual_table_header = prev_qual_table_filtered[0]
        prev_qual_table_filtered = prev_qual_table_filtered[1:]
        join_names = self._join_names()
        prev_qual_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_qual_table_filtered]
        prev_qual_table_df = pd.DataFrame(prev_qual_table_clean, columns=prev_qual_table_header)
        logger.info(f"{prev_qual_table_df = }")

        F1DataFetcher.q1st = prev_qual_table_df.loc[0]['Driver']
        F1DataFetcher.q2nd = prev_qual_table_df.loc[1]['Driver']
        F1DataFetcher.q3rd = prev_qual_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_qual_table_df['Driver'], prev_qual_table_df['Car'])):
            if team not in F1DataFetcher.best_three:
                F1DataFetcher.q_botr = driver
                break


    def get_prev_fpX_results(self,fpN):
        """ find out FP1 results in previous race"""
        prev_fpN_soap = self._request_and_get_soap(F1DataFetcher.prev_free_prac_url,fpN)
        prev_fpN_table = prev_fpN_soap.find_all('tr')
        prev_fpN_table_text = [name.get_text().strip() for name in prev_fpN_table]
        prev_fpN_table_text_clean = [name.split("\n") for name in prev_fpN_table_text]
        prev_fpN_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fpN_table_text_clean]
        prev_fpN_table_header = prev_fpN_table_filtered[0]
        prev_fpN_table_filtered = prev_fpN_table_filtered[1:]
        join_names = self._join_names()
        prev_fpN_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_fpN_table_filtered]
        prev_fpN_table_df = pd.DataFrame(prev_fpN_table_clean, columns=prev_fpN_table_header)
        logger.info(f"FP{fpN} results: {prev_fpN_table_df = }")
        fp_round = f"fp{fpN}"
        F1DataFetcher.free_practice[fp_round] = prev_fpN_table_df.loc[0]['Driver']
        logger.info(f"{F1DataFetcher.free_practice[fp_round] = }")

    def _event_in_schedule(self,event_name,event_url):
        # try to find if there was a sprint
        prev_event_soap = self._request_and_get_soap(event_url)
        # if there was no sprint, it returns the race board
        #  so have to find out if sprint is listed
        event_exist = prev_event_soap.find_all('ul',class_="resultsarchive-side-nav")
        event_exist_text = [name.get_text().strip() for name in event_exist]
        event_exist_list_dirty = event_exist_text[0].split('\n')
        event_exist_list = [elem.strip() for elem in event_exist_list_dirty if elem.strip()]
        logger.info(f"{event_exist_list = }")
        if event_name in event_exist_list:
            return True

    def get_prev_sprint_results(self):
        """find sprint results"""
        if not self._event_in_schedule('SPRINT',F1DataFetcher.prev_sprint_url):
            logger.info("There was no SPRINT in the last race")
            return 0
        prev_sprint_soap = self._request_and_get_soap(F1DataFetcher.prev_sprint_url)
        prev_sprint_table = prev_sprint_soap.find_all('tr')
        prev_sprint_table_text = [name.get_text().strip() for name in prev_sprint_table]
        prev_sprint_table_text_clean = [name.split("\n") for name in prev_sprint_table_text]
        prev_sprint_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_sprint_table_text_clean]
        prev_sprint_table_header = prev_sprint_table_filtered[0]
        join_names = self._join_names()
        prev_sprint_table_filtered = prev_sprint_table_filtered[1:]
        prev_sprint_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_sprint_table_filtered]
        prev_sprint_table_df = pd.DataFrame(prev_sprint_table_clean, columns=prev_sprint_table_header)
        logger.info(f"{prev_sprint_table_df = }")

    def get_prev_dotd_results(self):
        # driver of the day
        prev_dotd_soap = self._request_and_get_soap(F1DataFetcher.prev_dotd_url)
        prev_dotd_text = prev_dotd_soap.find_all('strong')
        prev_dotd_text_clean = [name.get_text().strip() for name in prev_dotd_text]
        prev_dotd_list = prev_dotd_text_clean[1]#latest
        # 'Carlos Sainz - 31.5%\nSergio Perez - 14.8%\nMax Verstappen - 13.3%\nAlex Albon - 10.7%\nCharles Leclerc - 6%',
        dotd = prev_dotd_list.split("\n")[0]
        F1DataFetcher.dotd = dotd.split("-")[0].strip()
        logger.info(f"{F1DataFetcher.dotd =}")

    def get_prev_fastest_results(self):
        """fastest lap driver name"""
        prev_fast_soap = self._request_and_get_soap(F1DataFetcher.prev_rf_url)
        prev_fast_table = prev_fast_soap.find_all('tr')
        prev_fast_table_text = [name.get_text().strip() for name in prev_fast_table]
        prev_fast_table_text_clean = [name.split("\n") for name in prev_fast_table_text]
        prev_fast_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fast_table_text_clean]
        prev_fast_table_header = prev_fast_table_filtered[0]
        join_names = lambda arr: ' '.join(arr[1:3])
        prev_fast_table_filtered = prev_fast_table_filtered[1:]
        prev_fast_table_clean = [[*arr[:1], join_names(arr), *arr[4:]] for arr in prev_fast_table_filtered]
        prev_fast_table_df = pd.DataFrame(prev_fast_table_clean, columns=prev_fast_table_header)
        F1DataFetcher.r_fast = prev_fast_table_df.iloc[-1]['Driver']
        logger.info(f"{prev_fast_table_df = }")

    def get_all_results(self):
        """return all results in json"""
        scores_json = {
            "FP1": F1DataFetcher.free_practice["fp1"],
            "FP2": F1DataFetcher.free_practice["fp2"],
            "FP3": F1DataFetcher.free_practice["fp3"],
            "Q1st": F1DataFetcher.q1st,
            "Q2nd": F1DataFetcher.q2nd,
            "Q3rd": F1DataFetcher.q3rd,
            "Q-BOTR": F1DataFetcher.q_botr,
            "R1st": F1DataFetcher.r1st,
            "R2nd": F1DataFetcher.r2nd,
            "R3rd": F1DataFetcher.r3rd,
            "R-BOTR": F1DataFetcher.r_botr,
            "DOTD": F1DataFetcher.r_botr,
            "R-F": F1DataFetcher.r_fast,
            "R-DNF": F1DataFetcher.r_dnf
        }
        return scores_json

def f1_results_pipeline() -> dict:
    f1_data_fetcher = F1DataFetcher()
    f1_data_fetcher.get_prev_race_id_and_name() # first | MUST DO
    f1_data_fetcher.update_url() # second | MUST DO
    f1_data_fetcher.get_prev_race_results()
    f1_data_fetcher.get_prev_sprint_results()
    f1_data_fetcher.get_prev_fastest_results()
    f1_data_fetcher.get_prev_dotd_results()
    for event in range(1,4):
        f1_data_fetcher.get_prev_fpX_results(event)
    f1_data_fetcher.get_prev_qual_results()
    results = f1_data_fetcher.get_all_results()
    return results

def get_prev_race_id() -> int:
    f1_data_fetcher = F1DataFetcher()
    f1_data_fetcher.get_prev_race_id_and_name()
    return f1_data_fetcher.prev_race_id

def get_drivers_info():
    drivers_url = "https://www.formula1.com/en/results.html/2023/drivers.html"
    drivers_request = requests.get(drivers_url).text
    logger.info("Successfully requested URL")
    drivers_soup = BeautifulSoup(drivers_request, 'html.parser')
    surnames = drivers_soup.find_all('span', class_="hide-for-mobile")
    firstnames = drivers_soup.find_all('span', class_="hide-for-tablet")
    carnames = drivers_soup.find_all('a', class_="grey semi-bold uppercase ArchiveLink")
    drivers_surnames = [name.get_text() for name in surnames]
    drivers_firstnames = [name.get_text() for name in firstnames]
    cars = [name.get_text() for name in carnames]
    drivers_fullname = list(zip(drivers_firstnames,drivers_surnames))
    drivers_info = list(zip(drivers_fullname,cars)) # (('Max', 'Verstappen'), 'Red Bull Racing Honda RBPT')
    return drivers_info