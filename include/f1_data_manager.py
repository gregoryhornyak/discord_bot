import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from include.logging_manager import logger
from include.constants import *
from include.database_manager import datetime

class F1DataFetcher:

    #* Includes:
    #*
    #* - previous grand prix details:
    #*   - id
    #*   - name / location
    #*   - sessions_info:
    #*     - previous sessions date
    #*   - grand prix results
    #* - next grand prix details:
    #*   - id
    #*   - name
    #*   - sessions_info:
    #*     - next sessions date
    #* - all the formula one urls
    #* - the grand prixes urls for the whole year
    #* - next grand prix drivers info:
    #*   - full name
    #*   - team name
    #* - next grand prix categories:
    #*   - FP1
    #*   - FP2
    #*   - ...
    #*   - R_DNF
    #*

    #* previous grand prix details:
    prev_gp_details = {
        "id": "",
        "name": "",
        "sessions":
        {
            "practice-1": "NAN",
            "practice-2": "NAN",
            "practice-3": "NAN",
            "sprint": "NAN",
            "sprint-shootout": "NAN",
            "qualifying": "NAN",
            "race": "NAN",
        },
        "results":
        {
            "FP1": "",
            "FP2": "",
            "FP3": "",
            "SO": "",
            "S": "",
            "Q1": "",
            "Q2": "",
            "Q3": "",
            "Q_BOTR": "",
            "R1": "",
            "R2": "",
            "R3": "",
            "R_BOTR": "",
            "DOTD": "",
            "R_FAST": "",
            "R_DNF": ""
        }
    }
    next_gp_details = {
        "id": "",
        "name": "",
        "sessions":
        {
            "practice-1": "NAN",
            "practice-2": "NAN",
            "practice-3": "NAN",
            "sprint": "NAN",
            "sprint-shootout": "NAN",
            "qualifying": "NAN",
            "race": "NAN",
        }
    }

    #* Best three teams - for BestOfTheRest
    best_three = ['FERRARI','RED BULL RACING HONDA RBPT','MERCEDES']

    #* All the formula one urls - driver is using 2023 -> needs to be changed into 2024
    formula_one_urls = {
        "all_past_races_url":   "https://www.formula1.com/en/results.html/2023/races.html",
        "all_races_url":        "https://www.formula1.com/en/results.html/2024/races.html",
        "year_schedule":        "https://www.formula1.com/en/racing/2024.html",
        "next_race_schedule":   "https://www.formula1.com/en/racing/2024/next_race_name.html",
        "practice-1":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-1.html",
        "practice-2":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-2.html",
        "practice-3":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-3.html",
        "sprint":               "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/sprint-results.html",
        "sprint-shootout":      "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/sprint-shootout.html",
        "qualifying":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/qualifying.html",
        "race":                 "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/race-result.html",
        "driver-of-the-day":    "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html",
        "fastest-lap-on-race":  "https://www.formula1.com/en/results.html/2023/fastest-laps.html",
        "driver_details_url":   "https://www.formula1.com/en/results.html/2023/drivers.html"
    }

    grand_prix_calendar_urls = {}

    next_gp_drivers_info = {}

    next_gp_categories = {}

    is_testing = True if BOT_STATE == "TEST" else False

    #* New Structure:
    #*
    #* 1) For optimisation: at every startup, check if results have been fetchen 'today'
    #*    A) Has been fetched, no need for requests -> load in results -> _6)_
    #*    B) Hasnt been fetched -> fetch all data _4)_ , store results _5)_, and load in _6)_
    #* 2) Get the previous and next race id and name | & STORE
    #* 3_A) Update URLs for any fetching
    #* 3_B) Check URLs if working (e.g. sprint and fp2-3) - event_in_schedule()
    #* 4) Fetch all data
    #* 5) Save the results to results_json
    #* 6) Load results in results_json

    #* SCENARIOS:
    #*
    #* not fetched yet -> fetch, save
    #* fetched -> load


    def __init__(self):
        logger.info("F1DataFetcher initialised")
        self.daily_fetch()

    def daily_fetch(self):
        """once every day fetch the data"""
        logger.info("Checking daily fetch need")
        start_fetch = self._check_fetch_log() #! MUST
        logger.info(f"Daily fetch starting: {start_fetch}")
        if start_fetch:
            self.fetch_prev_gp_details()
            self.fetch_next_gp_details()
            self.update_urls()
            self.sort_working_urls()
            self._fetch_prev_sessions()
            
            self.check_yearly_event_schedule_url()
            self.fetch_next_grand_prix_sessions()
            self.fetch_drivers_details()
            self.fetch_categories()
            self.save_all_data_to_json()
            self._update_fetch_log()
        else:
            self.load_all_data_from_json()
    
    def _check_fetch_log(self) -> bool:
        """True if needs to fetch"""
        fetch_log = {} # empty
        missing_results_json = False
        start_fetch = False
        fetch_date = datetime.datetime.now()

        #* see if fetched today 
        try:
            with open(f"{FETCH_LOG_PATH}","r") as f:
                fetch_log = json.load(f)
        #* if missing fetching -> not fetched
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            missing_results_json = True
            start_fetch = True
        #* if already fetched, check fetch date
        else:
            fetch_date = datetime.datetime.strptime(fetch_log['date'], "%Y-%m-%d %H:%M:%S.%f")
        #*
        finally:
            #* if out-of-date fetch info or missing 
            if fetch_date.day != datetime.datetime.now().day or missing_results_json:
                #todo START FETCHING
                start_fetch = True
                #self._update_fetch_log()
            #* else fetch info is up-to-date
        return start_fetch

    def _update_fetch_log(self):
        fetch_log = {}
        fetch_log['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") #
        with open(f"{FETCH_LOG_PATH}","w") as f:
            json.dump(fetch_log,f,indent=4)
        logger.info(f"{fetch_log = }")       

    def save_all_data_to_json(self):
        """cache all data"""
        logger.info("Saving previous grand prix details")
        with open(f"{PREV_GP_DETAILS_PATH}","w") as f:
            json.dump(self.prev_gp_details,f,indent=4)
        logger.info("Saving next grand prix details")
        with open(f"{NEXT_GP_DETAILS_PATH}","w") as f:
            json.dump(self.next_gp_details,f,indent=4)

        logger.info("Saving next grand prix drivers info")
        with open(f"{NEXT_GP_DRIVERS_INFO_PATH}","w") as f:
            json.dump(self.next_gp_drivers_info,f,indent=4)
        logger.info("Saving next grand prix categories")
        with open(f"{NEXT_GP_CATEGORIES_PATH}","w") as f:
            json.dump(self.next_gp_categories,f,indent=4)
        
    def load_all_data_from_json(self):
        """load cache"""
        logger.info("Loading previous grand prix details")
        with open(f"{PREV_GP_DETAILS_PATH}","r") as f:
            self.prev_gp_details=json.load(f)
        logger.info("Loading next grand prix details")
        with open(f"{NEXT_GP_DETAILS_PATH}","r") as f:
            self.next_gp_details=json.load(f)

        logger.info("Loading next grand prix drivers info")
        with open(f"{NEXT_GP_DRIVERS_INFO_PATH}","r") as f:
            self.next_gp_drivers_info = json.load(f)
        logger.info("Loading next grand prix categories")
        with open(f"{NEXT_GP_CATEGORIES_PATH}","r") as f:
            self.next_gp_categories = json.load(f)

    def fetch_prev_gp_details(self) -> None:
        """updates local-class id and name"""
        logger.info("Fetching previous grand prix details: id, name")
        all_races_soup = self._request_and_get_soap(self.formula_one_urls["all_past_races_url"])
        all_races_names_data = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
        if all_races_names_data == []:
            self.prev_gp_details["id"] = str(1226)
            self.prev_gp_details["name"] = "Abu Dhabi"
            return 0

        all_races_names = [name.get_text().strip() for name in all_races_names_data]
        all_races_ids_data = all_races_soup.find_all('a', class_='ArchiveLink')
        all_races_ids = [name.get('href') for name in all_races_ids_data]
        all_races_ids_text = [name.split('/')[5] for name in all_races_ids]

        self.prev_gp_details["id"] = str(all_races_ids_text[-1])
        self.prev_gp_details["name"] = all_races_names[-1]

    def _fetch_prev_sessions(self):

        for fpn in range(1,4):
            race_type = f"practice-{fpn}"
            code = f"FP{fpn}"
            if self.prev_gp_details["sessions"][race_type]:
                self.fetch_fpn_results(race_type,code)
        if self.prev_gp_details["sessions"]["race"]:
            self.fetch_race_results()
        if self.prev_gp_details["sessions"]["qualifying"]:
            self.fetch_qual_results()
        if self.prev_gp_details["sessions"]["sprint"]:
            self.fetch_sprint_race_results()
        if self.prev_gp_details["sessions"]["sprint-shootout"]:
            self.fetch_sprint_shootout_results()
        self.fetch_dotd_results()
        self.fetch_fastest_results()
        

    def fetch_next_gp_details(self) -> None:
        """updates local-class id and name"""
        logger.info("Fetching next grand prix details: id, name")
        all_races_soup = self._request_and_get_soap(self.formula_one_urls["all_races_url"])
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
            if key > self.prev_gp_details["id"]: # if its increasing
                next_key = key
                break

        self.next_gp_details["id"] = str(next_key)
        self.next_gp_details["name"] = all_races_names_divided[next_key]
        

    def check_yearly_event_schedule_url(self) -> bool: # TODO break it into two func: 1. checks 2. gets urls
        """checks if event schedule is saved\
            | if not: save it & FALSE\
            | else: TRUE """
        try:
            with open(f"{YEAR_SCHEDULE_PATH}","r") as f:
                self.grand_prix_calendar_urls = json.load(f)
        except FileNotFoundError:
            self.fetch_yearly_schedule_urls()
            return False
        else:
            return True
        
    def fetch_yearly_schedule_urls(self):
        logger.info("Fetching whole year grand prix URLs")
        next_event_id_and_url_json = {}        
        next_event_soap = self._request_and_get_soap(self.formula_one_urls["year_schedule"])
        next_event_soap_findings = next_event_soap.find_all('a', class_="event-item-wrapper event-item-link")
        next_event_soap_hrefs = ["https://www.formula1.com"+name.get('href') for name in next_event_soap_findings] # country URLs
        next_event_soap_ids = [name.get('data-meetingkey') for name in next_event_soap_findings] # URLs
        next_event_id_and_url = list(zip(next_event_soap_hrefs,next_event_soap_ids))
        next_event_id_and_url_json = {event_id: event_url for event_url, event_id in next_event_id_and_url}
        with open(f"{YEAR_SCHEDULE_PATH}","w") as f:
            json.dump(next_event_id_and_url_json,f,indent=4)
        self.grand_prix_calendar_urls = next_event_id_and_url_json

    def datetime_converter(self,start_time_str,gmt_offset_str):
        from datetime import datetime, timedelta
        import pytz

        # Given values
        #start_time_str = "2023-10-27T16:00:00"
        #gmt_offset_str = "-06:00"

        # Parse start time
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")

        # Parse GMT offset
        gmt_offset_hours, gmt_offset_minutes = map(int, gmt_offset_str.split(':'))
        gmt_offset = timedelta(hours=gmt_offset_hours, minutes=gmt_offset_minutes)

        # Calculate current time adjusted for GMT offset
        current_time_utc = datetime.utcnow()
        current_time_with_offset = current_time_utc + gmt_offset

        # Convert start time to the timezone of the current time
        local_tz = pytz.timezone('UTC')  # Assuming the start time is in UTC
        start_time_utc = local_tz.localize(start_time)
        start_time_with_offset = start_time_utc.astimezone(pytz.utc)

        # Calculate the start time according to the current time and offset
        adjusted_start_time = start_time_with_offset - (current_time_with_offset - current_time_utc)

        #logger.info(f'Adjusted Start Time (UTC):, {adjusted_start_time.strftime("%Y-%m-%dT%H:%M:%S") = }')

        return adjusted_start_time

    def fetch_next_grand_prix_sessions(self):

        logger.info("Fetching next grand prix sessions info: type, date")

        race_id = self.next_gp_details["id"]
        url= str(self.grand_prix_calendar_urls[self.next_gp_details["id"]]+"#my-time")
        
        event_soap = self._request_and_get_soap(url)
        event_soap_finds = event_soap.find_all('div', class_=lambda x: x and x.startswith("js-"))
        
        event_soap_race_types_classes = [name.get('class')[1] for name in event_soap_finds]
        grand_prix_schedule = {}
        grand_prix_schedule[str(race_id)] = {}

        for race_type_class in event_soap_race_types_classes:
            if race_type_class[:3] == "js-":
                class_name_pretty = race_type_class[3:] #* row js-race
            else:
                logger.error("NAGY SZAR VAN")
            class_name = str("row "+race_type_class)
            event_soap_finds = event_soap.find_all('div', class_=class_name)
            event_start_date = [name.get('data-start-time') for name in event_soap_finds]
            event_time_offset = [name.get('data-gmt-offset') for name in event_soap_finds]
            converted_start_time = self.datetime_converter(event_start_date[0],event_time_offset[0])
            datetime_obj = datetime.datetime.strftime(converted_start_time,'%Y-%m-%d %H:%M:%S.%f')
            grand_prix_schedule[str(race_id)][class_name_pretty] = datetime_obj

        #* next_event_details.json is loaded to replace true times | uncomment it for normal mode
        next_grand_prix_events = grand_prix_schedule[str(race_id)]
        self.next_gp_details["sessions"] = next_grand_prix_events

    def update_urls(self) -> None:
        """Replace placeholders with values using regular expressions"""
        logger.info("Updating all URL links")
        for key,url in self.formula_one_urls.items():
            url_updated_id = re.sub(r'prev_race_id', str(self.prev_gp_details["id"]), url)
            url_updated_id_name = re.sub(r'prev_race_name', self.prev_gp_details["name"], url_updated_id)
            url_updated_next_id_name = re.sub(r'next_race_name', self.next_gp_details["name"], url_updated_id_name)
            self.formula_one_urls[key] = url_updated_next_id_name

    def sort_working_urls(self):
        logger.info("Updating previous sessions info")
        for category in self.formula_one_urls.keys():
            for cur_race_name in self.prev_gp_details["sessions"].keys():
                if category == cur_race_name:
                    self.prev_gp_details["sessions"][cur_race_name] = self._event_in_schedule(cur_race_name,self.formula_one_urls[category])

    def _event_in_schedule(self,event_name,event_url) -> bool:
        """try to find if there was a specific type of event"""
        event_name = event_name.capitalize().replace('-', ' ')
        prev_event_soap = self._request_and_get_soap(event_url)
        # if there was no sprint, it returns the race board
        #  so have to find out if sprint is listed
        event_exist = prev_event_soap.find_all('ul',class_="resultsarchive-side-nav")
        event_exist_text = [name.get_text().strip() for name in event_exist]
        logger.info(f"{event_exist_text = }")
        if event_exist_text == []:
            return True
        event_exist_list_dirty = event_exist_text[0].split('\n')
        event_exist_list = [elem.strip() for elem in event_exist_list_dirty if elem.strip()]
        #logger.info(f"{event_name =} {event_exist_list = }")
        return (event_name in event_exist_list) # boolean
        
    def _request_and_get_soap(self,url) -> BeautifulSoup:
        response = requests.get(url).text
        soap = BeautifulSoup(response, 'html.parser')
        return soap

    def _join_names(self,start=2,end=4):
        return lambda arr: ' '.join(arr[start:end])

    def fetch_race_results(self) -> None:
        """ r1-3, r-botr, r-dnf results """
        logger.info("Fetching previous race results")
        prev_race_soap = self._request_and_get_soap(self.formula_one_urls["race"])
        prev_race_table = prev_race_soap.find_all('tr')
        prev_race_table_text = [name.get_text().strip() for name in prev_race_table]
        prev_race_table_text_clear = [name.split("\n") for name in prev_race_table_text]
        prev_race_table_filtered = [[item for item in original_list if item.strip() != ''] for original_list in prev_race_table_text_clear]
        prev_race_table_header = prev_race_table_filtered[0]
        prev_race_table_filtered_values = prev_race_table_filtered[1:]
        join_names = self._join_names()
        prev_race_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_race_table_filtered_values]
        prev_race_table_df = pd.DataFrame(prev_race_table_clean, columns=prev_race_table_header)
        #
        
        self.prev_gp_details["results"]["R1"] = prev_race_table_df.loc[0]['Driver']
        self.prev_gp_details["results"]["R2"] = prev_race_table_df.loc[1]['Driver']
        self.prev_gp_details["results"]["R3"] = prev_race_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_race_table_df['Driver'], prev_race_table_df['Car'])):
            if team.upper() not in self.best_three:
                self.prev_gp_details["results"]["R_BOTR"] = driver
                break

        for state in prev_race_table_df['Time/Retired']:
            if state in ['DNS','DNF']:
                if self.prev_gp_details["results"]["R_DNF"] == '':
                    self.prev_gp_details["results"]["R_DNF"] = '1'
                else:
                    self.prev_gp_details["results"]["R_DNF"] = str(1+int(self.prev_gp_details["results"]["R_DNF"]))
        
    def fetch_qual_results(self):
        """find out qualifying results in previous race"""
        logger.info("Fetching previous qualification results")
        prev_qual_soap = self._request_and_get_soap(self.formula_one_urls["qualifying"])
        prev_qual_table = prev_qual_soap.find_all('tr')
        prev_qual_table_text = [name.get_text().strip() for name in prev_qual_table]
        prev_qual_table_text_clear = [name.split("\n") for name in prev_qual_table_text]
        prev_qual_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_qual_table_text_clear]
        prev_qual_table_header = prev_qual_table_filtered[0]
        prev_qual_table_filtered = prev_qual_table_filtered[1:]
        join_names = self._join_names()
        prev_qual_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_qual_table_filtered]
        prev_qual_table_df = pd.DataFrame(prev_qual_table_clean, columns=prev_qual_table_header)

        self.prev_gp_details["results"]["Q1"] = prev_qual_table_df.loc[0]['Driver']
        self.prev_gp_details["results"]["Q2"] = prev_qual_table_df.loc[1]['Driver']
        self.prev_gp_details["results"]["Q3"] = prev_qual_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_qual_table_df['Driver'], prev_qual_table_df['Car'])):
            #
            if team.upper() not in self.best_three:
                #
                self.prev_gp_details["results"]["Q_BOTR"] = driver
                break

    def fetch_fpn_results(self,race_type,race_type_short):
        """ find out FP1-3 results in previous race"""
        logger.info("Fetching previous free practices results")
        prev_fpN_soap = self._request_and_get_soap(self.formula_one_urls[race_type])
        prev_fpN_table = prev_fpN_soap.find_all('tr')
        prev_fpN_table_text = [name.get_text().strip() for name in prev_fpN_table]
        prev_fpN_table_text_clean = [name.split("\n") for name in prev_fpN_table_text]
        prev_fpN_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fpN_table_text_clean]
        prev_fpN_table_header = prev_fpN_table_filtered[0]
        prev_fpN_table_filtered = prev_fpN_table_filtered[1:]
        join_names = self._join_names()
        prev_fpN_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_fpN_table_filtered]
        prev_fpN_table_df = pd.DataFrame(prev_fpN_table_clean, columns=prev_fpN_table_header)
        self.prev_gp_details["results"][race_type_short] = prev_fpN_table_df.loc[0]['Driver']

    def fetch_sprint_race_results(self):
        """find sprint results"""
        logger.info("Fetching previous sprint results")
        prev_sprint_soap = self._request_and_get_soap(self.formula_one_urls["sprint"])
        prev_sprint_table = prev_sprint_soap.find_all('tr')
        prev_sprint_table_text = [name.get_text().strip() for name in prev_sprint_table]
        prev_sprint_table_text_clean = [name.split("\n") for name in prev_sprint_table_text]
        prev_sprint_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_sprint_table_text_clean]
        prev_sprint_table_header = prev_sprint_table_filtered[0]
        join_names = self._join_names()
        prev_sprint_table_filtered = prev_sprint_table_filtered[1:]
        prev_sprint_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_sprint_table_filtered]
        prev_sprint_table_df = pd.DataFrame(prev_sprint_table_clean, columns=prev_sprint_table_header)
        #
        self.prev_gp_details["results"]["S"] = prev_sprint_table_df.loc[0]['Driver']

    def fetch_sprint_shootout_results(self):
        """Fetch sprint Shootout"""
        logger.info("Fetching previous sprint shootout results")
        prev_shootout_soap = self._request_and_get_soap(self.formula_one_urls["sprint-shootout"])
        prev_shootout_soap_table = prev_shootout_soap.find_all('tr')
        prev_shootout_table_text = [name.get_text().strip() for name in prev_shootout_soap_table]
        prev_shootout_table_text_clear = [name.split("\n") for name in prev_shootout_table_text]
        prev_shootout_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_shootout_table_text_clear]
        prev_shootout_table_header = prev_shootout_table_filtered[0]
        prev_shootout_table_filtered = prev_shootout_table_filtered[1:]
        join_names = self._join_names()
        prev_shootout_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_shootout_table_filtered]
        prev_shootout_table_df = pd.DataFrame(prev_shootout_table_clean, columns=prev_shootout_table_header)
        #
        self.prev_gp_details["results"]["SO"] = prev_shootout_table_df.loc[0]['Driver']

    def fetch_dotd_results(self):
        # driver of the day
        logger.info("Fetching previous driver of the day results")
        prev_dotd_soap = self._request_and_get_soap(self.formula_one_urls["driver-of-the-day"])
        prev_dotd_text = prev_dotd_soap.find_all('strong')
        prev_dotd_text_clean = [name.get_text().strip() for name in prev_dotd_text]
        prev_dotd_list = prev_dotd_text_clean[1]#latest
        # 'Carlos Sainz - 31.5%\nSergio Perez - 14.8%\nMax Verstappen - 13.3%\nAlex Albon - 10.7%\nCharles Leclerc - 6%',
        dotd = prev_dotd_list.split("\n")[0]
        self.prev_gp_details["results"]["DOTD"] = dotd.split("-")[0].strip()

    def fetch_fastest_results(self):
        """fastest lap driver name"""
        logger.info("Fetching previous fastest lap results")
        prev_fast_soap = self._request_and_get_soap(self.formula_one_urls["fastest-lap-on-race"])
        prev_fast_table = prev_fast_soap.find_all('tr')
        prev_fast_table_text = [name.get_text().strip() for name in prev_fast_table]
        prev_fast_table_text_clean = [name.split("\n") for name in prev_fast_table_text]
        prev_fast_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fast_table_text_clean]
        prev_fast_table_header = prev_fast_table_filtered[0]
        join_names = self._join_names(1,3)
        prev_fast_table_filtered = prev_fast_table_filtered[1:]
        prev_fast_table_clean = [[*arr[:1], join_names(arr), *arr[4:]] for arr in prev_fast_table_filtered]
        prev_fast_table_df = pd.DataFrame(prev_fast_table_clean, columns=prev_fast_table_header)
        self.prev_gp_details["results"]["R_FAST"] = prev_fast_table_df.iloc[-1]['Driver']

    def fetch_drivers_details(self) -> dict:
        """return driver and team"""
        logger.info("Fetching all next grand prix drivers info")
        # for guess selection
        drivers_soap = self._request_and_get_soap(self.formula_one_urls["driver_details_url"])
        surnames = drivers_soap.find_all('span', class_="hide-for-mobile")
        firstnames = drivers_soap.find_all('span', class_="hide-for-tablet")
        carnames = drivers_soap.find_all('a', class_="grey semi-bold uppercase ArchiveLink")
        drivers_surnames = [name.get_text() for name in surnames]
        drivers_firstnames = [name.get_text() for name in firstnames]
        cars = [name.get_text() for name in carnames]
        drivers_fullname = [fname+" "+sname for fname, sname in zip(drivers_firstnames,drivers_surnames)]
        drivers_info = {key: value for key, value in zip(drivers_fullname,cars)}
        self.next_gp_drivers_info = drivers_info

    def fetch_categories(self) -> list:
        logger.info("Fetching all next grand prix categories details")
        return_list = []
        if "sprint" in self.next_gp_details["sessions"].keys():
            return_list = ["FP1","SO","S","Q1","Q2","Q3","Q_BOTR","R1","R2","R3","R_BOTR","DOTD","R_FAST","R_DNF"] # refine it into a for loop
        else:
            return_list = ["FP1","FP2","FP3","Q1","Q2","Q3","Q_BOTR","R1","R2","R3","R_BOTR","DOTD","R_FAST","R_DNF"] 
        self.next_gp_categories = return_list
    
    ###* GET METHODS

    def get_drivers_details(self):
        logger.info("Sending all next grand prix drivers info")
        return self.next_gp_drivers_info

    def get_categories(self):
        logger.info("Sending all next grand prix categories details")
        return self.next_gp_categories
    
    def get_all_results(self):
        logger.info("Sending all previous sessions results")
        return self.prev_gp_details["results"]
    
    #* prev gp
    def get_prev_gp_id(self):
        logger.info("Sending previous grand prix id")
        return self.prev_gp_details["id"] 
    
    def get_prev_gp_name(self):
        logger.info("Sending previous grand prix name")
        return self.prev_gp_details["name"]
    
    #* next gp
    def get_next_gp_id(self):
        logger.info("Sending next grand prix id")
        return self.next_gp_details["id"] 
    
    def get_next_gp_name(self):
        logger.info("Sending next grand prix name")
        return self.next_gp_details["name"]
