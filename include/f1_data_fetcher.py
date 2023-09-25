import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from include.logging_manager import logger
from include.constants import *
from include.database_manager import datetime

class F1DataFetcher:

    #! STANDARD: JSON FILES

    # class variables:
    ## race details
    prev_race_details = {
        "id": 0,
        "name": ""
    }
    next_race_details = {
        "id": 0,
        "name": ""
    }

    free_prac_ser_num = 1

    ## common lists
    best_three = ['FERRARI','RED BULL RACING HONDA RBPT','MERCEDES'] # refine, as it doesnt work

    ## urls
    formula_one_urls = {
        "all_races_url":        "https://www.formula1.com/en/results.html/2023/races.html",
        "next_race_schedule":   "https://www.formula1.com/en/racing/2023/next_race_name.html",
        "year_schedule":        "https://www.formula1.com/en/racing/2023.html",
        "race":                 "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/race-result.html",
        "qualifying":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/qualifying.html",
        "practice-1":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-1.html",
        "practice-2":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-2.html",
        "practice-3":           "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/practice-3.html",
        "sprint":               "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/sprint-results.html",
        "sprint-shootout":      "https://www.formula1.com/en/results.html/2023/races/prev_race_id/prev_race_name/sprint-shootout.html",
        "driver-of-the-day":    "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html",
        "fastest-lap-on-race":  "https://www.formula1.com/en/results.html/2023/fastest-laps.html",
        "driver_details_url":   "https://www.formula1.com/en/results.html/2023/drivers.html"
    }

    grand_prix_urls = {}

    next_grand_prix_schedule = {}

    # current race schedules

    current_events_schedule = {
        "practice-1": False,
        "practice-2": False,
        "practice-3": False,
        "sprint": False,
        "sprint-shootout": False,
        "qualifying": False,
        "race": False,
    }

    ## results board 

    results_board = {
        "FP1_1ST": "",
        "FP2_1ST": "",
        "FP3_1ST": "",
        "S_SHO": "",
        "S_RACE": "",
        "Q_1ST": "",
        "Q_2ND": "",
        "Q_3RD": "",
        "Q_BOTR": "",
        "R_1ST": "",
        "R_2ND": "",
        "R_3RD": "",
        "R_BOTR": "",
        "DOTD": "",
        "R_FAST": "",
        "R_DNF": ""
        }

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
        self.daily_fetch()

    def daily_fetch(self):
        """once every day fetch the data"""
        start_fetch,fetch_log = self.check_fetch_log() #! MUST
        self.get_prev_race_id_and_name() #! MUST
        self.get_next_race_id_and_name() #! MUST
        self.update_urls() #! MUST
        self.check_yearly_event_schedule_url()
        self.get_next_event_details(str(self.next_race_details["id"]),self.grand_prix_urls[str(self.next_race_details["id"])])

        if start_fetch:
            self.check_urls_working() #! SHOULD
            self.fetch_all_into_cache() #? IF not fetched today
            self.save_results_to_json() #? IF not fetched today
        else:
            self.load_results()
        if fetch_log:
            
            self.create_fetch_log(fetch_log)

    def create_fetch_log(self,fetch_log):
        with open(f"{FETCH_LOG_PATH}","w") as f:
            json.dump(fetch_log,f,indent=4)

    def check_fetch_log(self) -> bool:
        fetch_log = {}
        missing_results_json = False
        start_fetch = False
        fetch_date = None

        #* see if fetched today 
        try:
            with open(f"{FETCH_LOG_PATH}","r") as f:
                fetch_log = json.load(f)

        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            

            missing_results_json = True
            start_fetch = True
            fetch_date = datetime.datetime.now()
            fetch_log['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            #self.create_fetch_log(fetch_log)
        
        else:
            
            fetch_date = datetime.datetime.strptime(fetch_log['date'], "%Y-%m-%d %H:%M:%S.%f")

        finally:
            if fetch_date.day != datetime.datetime.now().day or missing_results_json:
                
                #todo START FETCHING
                start_fetch = True
                fetch_log['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                
                with open(f"{FETCH_LOG_PATH}","w") as f:
                    json.dump(fetch_log,f,indent=4)

        #
        return start_fetch,fetch_log

    def save_results_to_json(self):
        
        results_json = {self.prev_race_details["id"]: self.results_board}
        with open(f"{RESULTS_PATH}","w") as f:
            json.dump(results_json,f,indent=4)
        

    def get_prev_race_id_and_name(self) -> None:
        """updates local-class id and name"""
        all_races_soup = self.request_and_get_soap(self.formula_one_urls["all_races_url"])
        all_races_names_data = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
        all_races_names = [name.get_text().strip() for name in all_races_names_data]
        all_races_ids_data = all_races_soup.find_all('a', class_='ArchiveLink')
        all_races_ids = [name.get('href') for name in all_races_ids_data]
        all_races_ids_text = [name.split('/')[5] for name in all_races_ids]

        self.prev_race_details["id"] = all_races_ids_text[-1]
        self.prev_race_details["name"] = all_races_names[-1]
        

    def get_next_race_id_and_name(self) -> None:
        """updates local-class id and name"""
        all_races_soup = self.request_and_get_soap(self.formula_one_urls["all_races_url"])
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
            if key > str(self.prev_race_details["id"]): # if its increasing
                next_key = key
                break

        self.next_race_details["id"] = next_key
        self.next_race_details["name"] = all_races_names_divided[next_key]
        

    def check_yearly_event_schedule_url(self) -> bool: # TODO break it into two func: 1. checks 2. gets urls
        """checks if event schedule is saved\
            | if not: save it & FALSE\
            | else: TRUE """
        try:
            with open(f"{YEAR_SCHEDULE_PATH}","r") as f:
                self.grand_prix_urls = json.load(f)
        except FileNotFoundError:
            
            self.get_yearly_schedule_urls()
            return False
        else:
            return True
        
    def get_yearly_schedule_urls(self):
        next_event_id_and_url_json = {}        
        next_event_soap = self.request_and_get_soap(self.formula_one_urls["year_schedule"])
        next_event_soap_findings = next_event_soap.find_all('a', class_="event-item-wrapper event-item-link")
        next_event_soap_hrefs = ["https://www.formula1.com"+name.get('href') for name in next_event_soap_findings] # country URLs
        next_event_soap_ids = [name.get('data-meetingkey') for name in next_event_soap_findings] # URLs
        next_event_id_and_url = list(zip(next_event_soap_hrefs,next_event_soap_ids))
        next_event_id_and_url_json = {event_id: event_url for event_url, event_id in next_event_id_and_url}
        with open(f"{YEAR_SCHEDULE_PATH}","w") as f:
            json.dump(next_event_id_and_url_json,f,indent=4)
        self.grand_prix_urls = next_event_id_and_url_json

    def get_next_event_details(self,race_id:str,url):
        url= str(url+"#track-time")
        event_soap = self.request_and_get_soap(url)
        event_soap_finds = event_soap.find_all('div', class_=lambda x: x and x.startswith("js-"))
        event_soap_race_types_classes = [name.get('class')[1] for name in event_soap_finds]
        grand_prix_schedule = {}
        grand_prix_schedule[str(race_id)] = {}

        for race_type_class in event_soap_race_types_classes:
            if race_type_class[:3] == "js-":
                class_name_pretty = race_type_class[3:] #* row js-race
            else:
                print("NAGY SZAR VAN")
            class_name = str("row "+race_type_class)
            event_soap_finds = event_soap.find_all('div', class_=class_name)
            event_start_date = [name.get('data-start-time') for name in event_soap_finds]
            datetime_obj = datetime.datetime.strptime(event_start_date[0], '%Y-%m-%dT%H:%M:%S')
            datetime_obj = datetime.datetime.strftime(datetime_obj,'%Y-%m-%d %H:%M:%S.%f')
            grand_prix_schedule[str(race_id)][class_name_pretty] = datetime_obj
        self.next_grand_prix_schedule = grand_prix_schedule[str(race_id)]
        
        with open(f"{NEXT_EVENT_DATES_PATH}","w") as f:
            json.dump(grand_prix_schedule,f,indent=4)
        
        

    def load_results(self):
        # see if results are existend
        results_json = {}
        try:
            with open(f"{RESULTS_PATH}","r") as f:
                results_json = json.load(f)
        
        except FileNotFoundError:
            
            with open(f"{RESULTS_PATH}","w") as f:
                f.write("")

        else:
            self.results_board = results_json[self.prev_race_details["id"]]
        

    def update_urls(self) -> None:
        # Replace placeholders with values using regular expressions
        

        """
        #! FOR TESTING PURPOSES OF PREV RACES, USE THIS FUNC

        custom_race_id = "1216"
        custom_race_name = "belgium"
        custom_next_race_name = ""

        self.prev_race_details["id"] = custom_race_id
        self.prev_race_details["name"] = custom_race_name

        for key,url in self.formula_one_urls_json.items():
            url_updated_id = re.sub(r'prev_race_id', custom_race_id, url)
            url_updated_id_name = re.sub(r'prev_race_name', custom_race_name, url_updated_id)
            # if oen word: Capitalise
            # if two words: separete by '-' -> Capitalise -> put '_' inbetween
            url_updated_next_id_name = re.sub(r'next_race_name', custom_next_race_name, url_updated_id_name)
            self.formula_one_urls_json[key] = url_updated_id_name
        
        return 0
        """
    
        for key,url in self.formula_one_urls.items():
            url_updated_id = re.sub(r'prev_race_id', str(self.prev_race_details["id"]), url)
            url_updated_id_name = re.sub(r'prev_race_name', self.prev_race_details["name"], url_updated_id)
            url_updated_next_id_name = re.sub(r'next_race_name', self.next_race_details["name"], url_updated_id_name)
            self.formula_one_urls[key] = url_updated_next_id_name
        

    def check_urls_working(self):
        for race_name in self.formula_one_urls.keys():
            for cur_race_name in self.current_events_schedule.keys():
                if race_name == cur_race_name:
                    self.current_events_schedule[cur_race_name] = self.event_in_schedule(cur_race_name,self.formula_one_urls[race_name])

    def event_in_schedule(self,event_name,event_url) -> bool:
        """try to find if there was an event"""
        event_name = event_name.capitalize().replace('-', ' ')
        prev_event_soap = self.request_and_get_soap(event_url)
        # if there was no sprint, it returns the race board
        #  so have to find out if sprint is listed
        event_exist = prev_event_soap.find_all('ul',class_="resultsarchive-side-nav")
        event_exist_text = [name.get_text().strip() for name in event_exist]
        event_exist_list_dirty = event_exist_text[0].split('\n')
        event_exist_list = [elem.strip() for elem in event_exist_list_dirty if elem.strip()]
        return (event_name in event_exist_list)

    def fetch_all_into_cache(self):
        
        if self.current_events_schedule["race"]: # true
            self.fetch_race_results()
        if self.current_events_schedule["qualifying"]:
            self.fetch_qual_results()
        if self.current_events_schedule["sprint"]:
            self.fetch_sprint_race_results()
        if self.current_events_schedule["sprint-shootout"]:
            self.fetch_sprint_shootout_results()
        self.fetch_dotd_results()
        self.fetch_fastest_results()
        for fpn in range(1,4):
            race_type = f"practice-{fpn}"
            if fpn == 1:
                code = "FP1_1ST"
            elif fpn == 2:
                code = "FP2_1ST"
            else:
                code = "FP3_1ST"
            if self.current_events_schedule[race_type]:
                self.fetch_fpn_results(race_type,code)
        
        
    def request_and_get_soap(self,url) -> BeautifulSoup:
        response = requests.get(url).text
        soap = BeautifulSoup(response, 'html.parser')
        return soap

    def join_names(self,start=2,end=4):
        return lambda arr: ' '.join(arr[start:end])

    def fetch_race_results(self) -> None:
        """ r1-3, r-botr, r-dnf results """
        prev_race_soap = self.request_and_get_soap(self.formula_one_urls["race"])
        prev_race_table = prev_race_soap.find_all('tr')
        prev_race_table_text = [name.get_text().strip() for name in prev_race_table]
        prev_race_table_text_clear = [name.split("\n") for name in prev_race_table_text]
        prev_race_table_filtered = [[item for item in original_list if item.strip() != ''] for original_list in prev_race_table_text_clear]
        prev_race_table_header = prev_race_table_filtered[0]
        prev_race_table_filtered_values = prev_race_table_filtered[1:]
        join_names = self.join_names()
        prev_race_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_race_table_filtered_values]
        prev_race_table_df = pd.DataFrame(prev_race_table_clean, columns=prev_race_table_header)
        #
        
        self.results_board["R_1ST"] = prev_race_table_df.loc[0]['Driver']
        self.results_board["R_2ND"] = prev_race_table_df.loc[1]['Driver']
        self.results_board["R_3RD"] = prev_race_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_race_table_df['Driver'], prev_race_table_df['Car'])):
            if team.upper() not in self.best_three:
                self.results_board["R_BOTR"] = driver
                break

        for state in prev_race_table_df['Time/Retired']:
            if state in ['DNS','DNF']:
                if self.results_board["R_DNF"] == '':
                    self.results_board["R_DNF"] = '1'
                else:
                    self.results_board["R_DNF"] = str(1+int(self.results_board["R_DNF"]))
        
        

    def fetch_qual_results(self):
        """find out qualifying results in previous race"""
        prev_qual_soap = self.request_and_get_soap(self.formula_one_urls["qualifying"])
        prev_qual_table = prev_qual_soap.find_all('tr')
        prev_qual_table_text = [name.get_text().strip() for name in prev_qual_table]
        prev_qual_table_text_clear = [name.split("\n") for name in prev_qual_table_text]
        prev_qual_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_qual_table_text_clear]
        prev_qual_table_header = prev_qual_table_filtered[0]
        prev_qual_table_filtered = prev_qual_table_filtered[1:]
        join_names = self.join_names()
        prev_qual_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_qual_table_filtered]
        prev_qual_table_df = pd.DataFrame(prev_qual_table_clean, columns=prev_qual_table_header)
        #
        #

        self.results_board["Q_1ST"] = prev_qual_table_df.loc[0]['Driver']
        self.results_board["Q_2ND"] = prev_qual_table_df.loc[1]['Driver']
        self.results_board["Q_3RD"] = prev_qual_table_df.loc[2]['Driver']

        for (driver, team) in (zip(prev_qual_table_df['Driver'], prev_qual_table_df['Car'])):
            #
            if team.upper() not in self.best_three:
                #
                self.results_board["Q_BOTR"] = driver
                break

        

    def fetch_fpn_results(self,race_type,race_type_short):
        """ find out FP1-3 results in previous race"""
        prev_fpN_soap = self.request_and_get_soap(self.formula_one_urls[race_type])
        prev_fpN_table = prev_fpN_soap.find_all('tr')
        prev_fpN_table_text = [name.get_text().strip() for name in prev_fpN_table]
        prev_fpN_table_text_clean = [name.split("\n") for name in prev_fpN_table_text]
        prev_fpN_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fpN_table_text_clean]
        prev_fpN_table_header = prev_fpN_table_filtered[0]
        prev_fpN_table_filtered = prev_fpN_table_filtered[1:]
        join_names = self.join_names()
        prev_fpN_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_fpN_table_filtered]
        prev_fpN_table_df = pd.DataFrame(prev_fpN_table_clean, columns=prev_fpN_table_header)
        #
        self.results_board[race_type_short] = prev_fpN_table_df.loc[0]['Driver']

        

    def fetch_sprint_race_results(self):
        """find sprint results"""
        prev_sprint_soap = self.request_and_get_soap(self.formula_one_urls["sprint"])
        prev_sprint_table = prev_sprint_soap.find_all('tr')
        prev_sprint_table_text = [name.get_text().strip() for name in prev_sprint_table]
        prev_sprint_table_text_clean = [name.split("\n") for name in prev_sprint_table_text]
        prev_sprint_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_sprint_table_text_clean]
        prev_sprint_table_header = prev_sprint_table_filtered[0]
        join_names = self.join_names()
        prev_sprint_table_filtered = prev_sprint_table_filtered[1:]
        prev_sprint_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_sprint_table_filtered]
        prev_sprint_table_df = pd.DataFrame(prev_sprint_table_clean, columns=prev_sprint_table_header)
        #
        self.results_board["S_RACE"] = prev_sprint_table_df.loc[0]['Driver']

        

    def fetch_sprint_shootout_results(self):
        """Fetch sprint Shootout"""
        prev_shootout_soap = self.request_and_get_soap(self.formula_one_urls["sprint-shootout"])
        prev_shootout_soap_table = prev_shootout_soap.find_all('tr')
        prev_shootout_table_text = [name.get_text().strip() for name in prev_shootout_soap_table]
        prev_shootout_table_text_clear = [name.split("\n") for name in prev_shootout_table_text]
        prev_shootout_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_shootout_table_text_clear]
        prev_shootout_table_header = prev_shootout_table_filtered[0]
        prev_shootout_table_filtered = prev_shootout_table_filtered[1:]
        join_names = self.join_names()
        prev_shootout_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_shootout_table_filtered]
        prev_shootout_table_df = pd.DataFrame(prev_shootout_table_clean, columns=prev_shootout_table_header)
        #
        self.results_board["S_SHO"] = prev_shootout_table_df.loc[0]['Driver']

        

    def fetch_dotd_results(self):
        # driver of the day
        prev_dotd_soap = self.request_and_get_soap(self.formula_one_urls["driver-of-the-day"])
        prev_dotd_text = prev_dotd_soap.find_all('strong')
        prev_dotd_text_clean = [name.get_text().strip() for name in prev_dotd_text]
        prev_dotd_list = prev_dotd_text_clean[1]#latest
        # 'Carlos Sainz - 31.5%\nSergio Perez - 14.8%\nMax Verstappen - 13.3%\nAlex Albon - 10.7%\nCharles Leclerc - 6%',
        dotd = prev_dotd_list.split("\n")[0]
        self.results_board["DOTD"] = dotd.split("-")[0].strip()

        

    def fetch_fastest_results(self):
        """fastest lap driver name"""
        prev_fast_soap = self.request_and_get_soap(self.formula_one_urls["fastest-lap-on-race"])
        prev_fast_table = prev_fast_soap.find_all('tr')
        prev_fast_table_text = [name.get_text().strip() for name in prev_fast_table]
        prev_fast_table_text_clean = [name.split("\n") for name in prev_fast_table_text]
        prev_fast_table_filtered = [[item for item in original_list if item != ''] for original_list in prev_fast_table_text_clean]
        prev_fast_table_header = prev_fast_table_filtered[0]
        join_names = self.join_names(1,3)
        prev_fast_table_filtered = prev_fast_table_filtered[1:]
        prev_fast_table_clean = [[*arr[:1], join_names(arr), *arr[4:]] for arr in prev_fast_table_filtered]
        prev_fast_table_df = pd.DataFrame(prev_fast_table_clean, columns=prev_fast_table_header)
        self.results_board["R_FAST"] = prev_fast_table_df.iloc[-1]['Driver']

    def get_all_results(self):
        """return all results in json"""
        return self.results_board
    
    def get_drivers_details(self) -> dict:
        """return driver and team"""
        # for guess selection
        drivers_soap = self.request_and_get_soap(self.formula_one_urls["driver_details_url"])
        surnames = drivers_soap.find_all('span', class_="hide-for-mobile")
        firstnames = drivers_soap.find_all('span', class_="hide-for-tablet")
        carnames = drivers_soap.find_all('a', class_="grey semi-bold uppercase ArchiveLink")
        drivers_surnames = [name.get_text() for name in surnames]
        drivers_firstnames = [name.get_text() for name in firstnames]
        cars = [name.get_text() for name in carnames]
        drivers_fullname = [fname+" "+sname for fname, sname in zip(drivers_firstnames,drivers_surnames)]
        drivers_info = {key: value for key, value in zip(drivers_fullname,cars)}
        return drivers_info

    def get_race_types(self) -> list:
        logger.warning(f"{self.results_board = }")
        return_list = [k for k,v in self.results_board.items() if v!=""]
        
        return return_list