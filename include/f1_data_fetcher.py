import requests
from bs4 import BeautifulSoup
import pandas as pd

from include.logging_manager import logger
from include.constants import *
from include.database_manager import datetime

class F1DataFetcher:
    # class variables:
    ## race details
    prev_race_id = 0
    prev_race_name = ""
    next_race_id = 0
    next_race_name = ""
    free_prac_ser_num = 1

    ## common lists
    best_three = ['FERRARI','RED BULL RACING HONDA RBPT','MERCEDES'] # refine, as it doesnt work

    ## urls
    all_races_url = "https://www.formula1.com/en/results.html/2023/races.html"
    prev_race_results_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/race-result.html"
    prev_qual_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/qualifying.html"
    prev_free_prac_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/practice-"
    prev_sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/sprint-results.html"
    prev_dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
    prev_rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"
    driver_details_url = "https://www.formula1.com/en/results.html/2023/drivers.html"

    ## race types and scores

    results_board = {
        "FP1": "",
        "FP2": "",
        "FP3": "",
        "Q1ST": "",
        "Q2ND": "",
        "Q3RD": "",
        "Q_BOTR": "",
        "R1ST": "",
        "R2ND": "",
        "R3RD": "",
        "R_BOTR": "",
        "DOTD": "",
        "R_FAST": "",
        "R_DNF": ""
        }

    def __init__(self):
        self.check_fetch_log()
        self._get_prev_race_id_and_name() # first | MUST DO
        self._get_next_race_id_and_name() 
        self._update_urls() # second | MUST DO
        self.load_results()
        logger.warning(f"NEXT RACE: {self.next_race_name}: {self.next_race_id}")

    def load_results(self):
        with open(f"{RESULTS_PATH}results.json","r") as f:
            results_json = json.load(f)
        self.results_board = results_json[self.prev_race_id]
        logger.info(f"loaded results into instance")

    def check_fetch_log(self):
        fetch_info = {}
        res_temp = {}
        missing_results_json = False
        try:
            with open(f"{RESULTS_PATH}results.json","r") as f:
                res_temp = json.load(f)
        except FileNotFoundError:
            missing_results_json = True
            logger.info("missing results.json file")

        try:
            with open(f"{RESULTS_PATH}fetching_log.json","r") as f:
                fetch_info = json.load(f)
        except json.decoder.JSONDecodeError:
            logger.info("Faulty json file")
            fetch_info['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            with open(f"{RESULTS_PATH}fetching_log.json","w") as f:
                json.dump(fetch_info,f,indent=4)
        except FileNotFoundError:
            fetch_info['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            with open(f"{RESULTS_PATH}fetching_log.json","w") as f:
                json.dump(fetch_info,f,indent=4)

        fetch_date = datetime.datetime.strptime(fetch_info['date'], "%Y-%m-%d %H:%M:%S.%f")
        if fetch_date.day != datetime.datetime.now().day or missing_results_json:
            logger.info(f"f1 data hasnt been fetched today")
            self.cache_results() # and save them
            fetch_info['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
        logger.info(f"f1 data been fetched at {fetch_info['date']}")
            
        with open(f"{RESULTS_PATH}fetching_log.json","w") as f:
            json.dump(fetch_info,f,indent=4)

        logger.info("F1_bot fetch-task complete")

    def _update_urls(self) -> None:
        prev_race_id = self.prev_race_id
        prev_race_name = self.prev_race_name
        self.prev_race_results_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/race-result.html"
        self.prev_qual_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/qualifying.html"
        self.prev_free_prac_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/practice-"
        self.prev_sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/sprint-results.html"
        self.prev_dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
        self.prev_rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"

    def _request_and_get_soap(self,url,fpN=0) -> BeautifulSoup:
        self._update_urls()
        if fpN != 0:
            url = url+f"{fpN}.html"
        response = requests.get(url).text
        soap = BeautifulSoup(response, 'html.parser')
        return soap

    def _join_names(self,start=2,end=4):
        return lambda arr: ' '.join(arr[start:end])

    def _get_prev_race_id_and_name(self) -> None:
        """updates local-class id and name"""
        all_races_soup = self._request_and_get_soap(self.all_races_url)
        all_races_names_data = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
        all_races_names = [name.get_text().strip() for name in all_races_names_data]
        all_races_ids_data = all_races_soup.find_all('a', class_='ArchiveLink')
        all_races_ids = [name.get('href') for name in all_races_ids_data]
        all_races_ids_text = [name.split('/')[5] for name in all_races_ids]
        previous_race_id = all_races_ids_text[-1]
        previous_race_name = all_races_names[-1]
        #logger.info(f"{previous_race_id = }\n{previous_race_name = }")
        self.prev_race_id = previous_race_id
        self.prev_race_name = previous_race_name

    def _get_next_race_id_and_name(self) -> None:
        """updates local-class id and name"""
        all_races_soup = self._request_and_get_soap(self.all_races_url)
        all_races_names_data = all_races_soup.find_all('a',class_="resultsarchive-filter-item-link FilterTrigger")
        all_races_names = [name.get('data-value') for name in all_races_names_data]
        middle = all_races_names.index('fastest-laps')
        all_races_names = all_races_names[middle+1:]

        def process_race_name(race_name):
            race_names = race_name.capitalize().split('-')
            return " ".join(race_names)
        
        all_races_names_divided = {race.split('/')[0]: process_race_name(race.split('/')[1]) for race in all_races_names}
        next_key = None
        for key in sorted(all_races_names_divided.keys()):
            if key > str(self.prev_race_id):
                next_key = key
                break

        self.next_race_id = next_key
        self.next_race_name = all_races_names_divided[next_key]
        logger.info(f"Next race: {self.next_race_id} {self.next_race_name}")

    def get_prev_race_results(self) -> None:
        """ r1-3, r-botr, r-dnf results """
        prev_race_soap = self._request_and_get_soap(self.prev_race_results_url)
        prev_race_table = prev_race_soap.find_all('tr')
        prev_race_table_text = [name.get_text().strip() for name in prev_race_table]
        prev_race_table_text_clear = [name.split("\n") for name in prev_race_table_text]
        prev_race_table_filtered = [[item for item in original_list if item.strip() != ''] for original_list in prev_race_table_text_clear]
        prev_race_table_header = prev_race_table_filtered[0]
        prev_race_table_filtered_values = prev_race_table_filtered[1:]
        join_names = self._join_names()
        prev_race_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_race_table_filtered_values]
        prev_race_table_df = pd.DataFrame(prev_race_table_clean, columns=prev_race_table_header)
        #logger.info(f"{prev_race_table_df = }")
        
        self.results_board["R1ST"] = prev_race_table_df.loc[0]['Driver']
        self.results_board["R2ND"] = prev_race_table_df.loc[1]['Driver']
        self.results_board["R3RD"] = prev_race_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_race_table_df['Driver'], prev_race_table_df['Car'])):
            logger.info(f"TEAM: {team.upper()} in {self.best_three}?")
            if team.upper() not in self.best_three:
                logger.info(f"No, {team.upper()} isnt in {self.best_three}")
                self.results_board["R_BOTR"] = driver
                break

        for state in prev_race_table_df['Time/Retired']:
            if state in ['DNS','DNF']:
                if self.results_board["R_DNF"] == '':
                    self.results_board["R_DNF"] = '1'
                else:
                    self.results_board["R_DNF"] = str(1+int(self.results_board["R_DNF"]))

    def get_prev_qual_results(self):
        """find out QUALIFYING results in previous race"""
        prev_qual_soap = self._request_and_get_soap(self.prev_qual_url)
        prev_qual_table = prev_qual_soap.find_all('tr')
        prev_qual_table_text = [name.get_text().strip() for name in prev_qual_table]
        prev_qual_table_text_clear = [name.split("\n") for name in prev_qual_table_text]
        prev_qual_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_qual_table_text_clear]
        prev_qual_table_header = prev_qual_table_filtered[0]
        prev_qual_table_filtered = prev_qual_table_filtered[1:]
        join_names = self._join_names()
        prev_qual_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_qual_table_filtered]
        prev_qual_table_df = pd.DataFrame(prev_qual_table_clean, columns=prev_qual_table_header)
        #logger.info(f"{prev_qual_table_df = }")

        self.results_board["Q1ST"] = prev_qual_table_df.loc[0]['Driver']
        self.results_board["Q2ND"] = prev_qual_table_df.loc[1]['Driver']
        self.results_board["Q3RD"] = prev_qual_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_qual_table_df['Driver'], prev_qual_table_df['Car'])):
            if team not in self.best_three:
                self.results_board["Q_BOTR"] = driver
                break


    def get_prev_fpX_results(self,fpN):
        """ find out FP1 results in previous race"""
        prev_fpN_soap = self._request_and_get_soap(self.prev_free_prac_url,fpN)
        prev_fpN_table = prev_fpN_soap.find_all('tr')
        prev_fpN_table_text = [name.get_text().strip() for name in prev_fpN_table]
        prev_fpN_table_text_clean = [name.split("\n") for name in prev_fpN_table_text]
        prev_fpN_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fpN_table_text_clean]
        prev_fpN_table_header = prev_fpN_table_filtered[0]
        prev_fpN_table_filtered = prev_fpN_table_filtered[1:]
        join_names = self._join_names()
        prev_fpN_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_fpN_table_filtered]
        prev_fpN_table_df = pd.DataFrame(prev_fpN_table_clean, columns=prev_fpN_table_header)
        #logger.info(f"FP{fpN} results: {prev_fpN_table_df = }")
        fp_round = f"FP{fpN}"
        self.results_board[fp_round] = prev_fpN_table_df.loc[0]['Driver']

    def _event_in_schedule(self,event_name,event_url):
        # try to find if there was a sprint
        prev_event_soap = self._request_and_get_soap(event_url)
        # if there was no sprint, it returns the race board
        #  so have to find out if sprint is listed
        event_exist = prev_event_soap.find_all('ul',class_="resultsarchive-side-nav")
        event_exist_text = [name.get_text().strip() for name in event_exist]
        event_exist_list_dirty = event_exist_text[0].split('\n')
        event_exist_list = [elem.strip() for elem in event_exist_list_dirty if elem.strip()]
        #logger.info(f"{event_exist_list = }")
        if event_name in event_exist_list:
            return True

    def get_prev_sprint_results(self):
        """find sprint results"""
        if not self._event_in_schedule('SPRINT',self.prev_sprint_url):
            logger.info("There was no SPRINT in the last race")
            return 0
        prev_sprint_soap = self._request_and_get_soap(self.prev_sprint_url)
        prev_sprint_table = prev_sprint_soap.find_all('tr')
        prev_sprint_table_text = [name.get_text().strip() for name in prev_sprint_table]
        prev_sprint_table_text_clean = [name.split("\n") for name in prev_sprint_table_text]
        prev_sprint_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_sprint_table_text_clean]
        prev_sprint_table_header = prev_sprint_table_filtered[0]
        join_names = self._join_names()
        prev_sprint_table_filtered = prev_sprint_table_filtered[1:]
        prev_sprint_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_sprint_table_filtered]
        prev_sprint_table_df = pd.DataFrame(prev_sprint_table_clean, columns=prev_sprint_table_header)
        #logger.info(f"{prev_sprint_table_df = }")

    def get_prev_dotd_results(self):
        # driver of the day
        prev_dotd_soap = self._request_and_get_soap(self.prev_dotd_url)
        prev_dotd_text = prev_dotd_soap.find_all('strong')
        prev_dotd_text_clean = [name.get_text().strip() for name in prev_dotd_text]
        prev_dotd_list = prev_dotd_text_clean[1]#latest
        # 'Carlos Sainz - 31.5%\nSergio Perez - 14.8%\nMax Verstappen - 13.3%\nAlex Albon - 10.7%\nCharles Leclerc - 6%',
        dotd = prev_dotd_list.split("\n")[0]
        self.results_board["DOTD"] = dotd.split("-")[0].strip()

    def get_prev_fastest_results(self):
        """fastest lap driver name"""
        prev_fast_soap = self._request_and_get_soap(self.prev_rf_url)
        prev_fast_table = prev_fast_soap.find_all('tr')
        prev_fast_table_text = [name.get_text().strip() for name in prev_fast_table]
        prev_fast_table_text_clean = [name.split("\n") for name in prev_fast_table_text]
        prev_fast_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fast_table_text_clean]
        prev_fast_table_header = prev_fast_table_filtered[0]
        join_names = self._join_names(1,3)
        prev_fast_table_filtered = prev_fast_table_filtered[1:]
        prev_fast_table_clean = [[*arr[:1], join_names(arr), *arr[4:]] for arr in prev_fast_table_filtered]
        prev_fast_table_df = pd.DataFrame(prev_fast_table_clean, columns=prev_fast_table_header)
        self.results_board["R_FAST"] = prev_fast_table_df.iloc[-1]['Driver']
        #logger.info(f"{prev_fast_table_df = }")

    def get_all_results(self):
        """return all results in json"""
        return self.results_board
    
    def get_drivers_details(self) -> dict:
        """return driver and team"""
        # for guess selection
        drivers_soap = self._request_and_get_soap(self.driver_details_url)
        surnames = drivers_soap.find_all('span', class_="hide-for-mobile")
        firstnames = drivers_soap.find_all('span', class_="hide-for-tablet")
        carnames = drivers_soap.find_all('a', class_="grey semi-bold uppercase ArchiveLink")
        drivers_surnames = [name.get_text() for name in surnames]
        drivers_firstnames = [name.get_text() for name in firstnames]
        cars = [name.get_text() for name in carnames]
        drivers_fullname = [fname+" "+sname for fname, sname in zip(drivers_firstnames,drivers_surnames)]
        drivers_info = {key: value for key, value in zip(drivers_fullname,cars)}
        return drivers_info

    def cache_results(self):
        self._get_prev_race_id_and_name() # first | MUST DO
        self._get_next_race_id_and_name() 
        self._update_urls() # second | MUST DO
        self.get_prev_race_results()
        self.get_prev_sprint_results()
        self.get_prev_fastest_results()
        self.get_prev_dotd_results()
        for event in range(1,4):
            self.get_prev_fpX_results(event)
        self.get_prev_qual_results()
        # save race results
        logger.info('F1_MODULE finished fetching')
        results_json = {self.prev_race_id: self.results_board}
        with open(f"{RESULTS_PATH}results.json","w") as f:
            json.dump(results_json,f,indent=4)

    def get_prev_race_id_and_name(self) -> dict:
        """name,id"""
        return {
            "name": self.prev_race_name,
            "id": self.prev_race_id}

    def get_next_race_id_and_name(self) -> dict:
        """name,id"""
        return {
            "name": self.next_race_name,
            "id": self.next_race_id}

