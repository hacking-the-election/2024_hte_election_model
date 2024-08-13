import numpy as np 
import os
import numpy.polynomial.polynomial as poly
import pandas as pd 
import requests
from math import exp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from polling_error import polling_error_coeffs

REP = "Trump"
DEM = "Harris"


global today, score_data, score_matrix, territories

def time_weighting(poll_delta):
    """
    Returns how much to weight polls based on 
    how long ago they was added to FiveThirtyEight. Uses a logistic-type
    function. 
    Args:
        poll_delta - float from 0-1 that signifies percentage of time since
        this poll was added between today and the very earliest poll on FiveThirtyEight.
    
    Returns:
        float from 0-1 that indicates how much to weight polls on that date.
    """

    y = 1 + exp(3*poll_delta)
    y = 2/y
    return y

def date_converter(date):
    if date.find(" ") == -1:
        day = date[date.find(" "):].strip().zfill(2)
    else:
        day = date[date.find(" "):].strip().zfill(2)
    if day == "00":
        day = "01"
    if "Jan." in date:
        poll_date = np.datetime64("2024-01-"+day)
    if "Feb." in date:
        poll_date = np.datetime64("2024-02-"+day)
    if "March" in date:
        poll_date = np.datetime64("2024-03-"+day)
    if "April" in date:
        poll_date = np.datetime64("2024-04-"+day)
    if "May" in date:
        poll_date = np.datetime64("2024-05-"+day)
    if "June" in date:
        poll_date = np.datetime64("2024-06-"+day)
    if "July" in date:
        poll_date = np.datetime64("2024-07-"+day)
    if "Aug." in date:
        poll_date = np.datetime64("2024-08-"+day)
    if "Sep." in date:
        poll_date = np.datetime64("2024-09-"+day)
    if "Oct." in date:
        poll_date = np.datetime64("2024-10-"+day)
    if "Nov." in date:
        poll_date = np.datetime64("2024-11-"+day)
    if "Dec." in date:
        poll_date = np.datetime64("2024-12-"+day)
    today = np.datetime64('today')
    if today < poll_date:
        poll_date = poll_date - np.timedelta64(365, 'D')
    return poll_date

def scrape_raw_average():
    """
    Retrieves time-weighted polling average for as many states as possible from 
    FiveThirtyEight. 
    Returns:
        territory_averages - pd.DataFrame with columns containing the margin, 
            number of polls, and weights for as many states as possible 
            (at least one poll necessary for a state.) Uses 999 as the margin 
            for states with no data. 
    """
    today = np.datetime64('today')
    score_data = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + "/data/state_similarities.csv", index_col="Geography")
    territories = np.asarray(score_data.index)
    global time_weighting 
    time_weighting = np.vectorize(time_weighting)
    time = np.datetime64(np.datetime64('now'), 'h')
    time_string = np.datetime_as_string(time, unit='h')
    to_fill = {"margin":np.zeros(len(territories)), "poll_num":np.zeros(len(territories))}
    territory_averages = pd.DataFrame(to_fill, index=territories)
    for num, territory in enumerate(territories):
        web_territory = territory.replace("-","/")
        web_territory = web_territory.replace(" ","-")
        print(web_territory.lower())
        # link = "https://www.realclearpolitics.com/epolls/2020/president/us/general_election_" + REP.lower() + "_vs_" + DEM.lower() + "-6247.html"
        link = "https://projects.fivethirtyeight.com/polls/president-general/2024/" + web_territory.lower() + "/"
        chromedriver_path= "/home/pbnjam/.cache/selenium/chromedriver/linux64/127.0.6533.99/chromedriver.exe"
        # driver = webdriver.Chrome(chromedriver_path)
        # service = Service(executable_path='C:/Program Files (x86)/Google/Chrome/Application/chrome.exe')
        service = Service(executable_path=os.path.dirname(os.path.abspath(__file__)) + '/chromedriver-win64/chromedriver.exe')
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(link)
        try:
            show_more = driver.find_element(By.CLASS_NAME, 'more-polls')
            show_more.click()
            print("CLICKED")
        except:
            print("NO SHOW MORE", territory)
            # continue
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        # print(yes.json())
        # if yes.status_code == 404:
        #     territory_averages.iat[num,0] = 999
        #     territory_averages.iat[num,1] = 0
        #     continue
        # soup = BeautifulSoup(yes.content, features="lxml")
        try:
            # poll_container = soup.body.find(attrs={"class":"container content"}).find(attrs={"class":"day-container"}).find_all(attrs={"class":"polls-table"})[0]
            poll_container = soup.body.find(attrs={"class":"container content"}).find_all(attrs={"class":"day-container"})
        except:
            print("MISSED STATE", territory)
            continue
        territory_margins = []
        dates = []
        sample_weights = []
        previous_pollsters = []
        previous_sample_types = []
        previous_dates = []
        for day_container in poll_container:
            if "-" not in territory and territory != "National":
                # if territory is a state
                if territory not in day_container.find(attrs={"class":"poll-group-hed"}).text:
                    # Ensure polls are actually for the state itself
                    continue
                # print(territory, day_container.find(attrs={"class":"poll-group-hed"}))
            poll_container = day_container.find_all(attrs={"class":"polls-table"})
            for poll_group in poll_container:
                for x in poll_group.children:
                    # Iterate through polls
                    for poll in x.find_all("tr", attrs={"class":"visible-row"}):
                    # poll = x.tr
                        # Ignore polls not including rep/dem candidates
                        choices = poll.find(attrs={"class":"answers hide-desktop"}).find_all(attrs={"class":"mobile-answer"})
                        choices = [choice.p.text.strip() for choice in choices]
                        if REP not in choices or DEM not in choices:
                            continue

                        poll_date = poll.find(attrs={"class":"date-wrapper"}).text
                        # print(poll_date.find(" "))
                        poll_date = poll_date[:poll_date.find("-")]
                        poll_date = date_converter(poll_date)

                        pollster = poll.find(attrs=("pollster-name")).text
                        if "SoCal" in pollster or "Trafalgar" in pollster or "Rasmussen" in pollster:
                            continue
                        sample = poll.find(attrs=("sample")).text
                        sample_type = poll.find(attrs=("sample-type")).text
                        # If the poll is a repeated (i.e. expanded vs. head to head) poll, remove
                        repeat = False
                        for i in range(len(previous_pollsters)):
                            if previous_pollsters[i] == pollster and previous_sample_types[i] == sample_type and previous_dates[i] == poll_date:
                                repeat = True
                                break
                        if repeat:
                            continue
                        print(choices)
                        # print(list(zip(previous_pollsters, previous_sample_types, previous_dates)))
                        print(pollster, sample_type, poll_date)
                        previous_pollsters.append(pollster)
                        previous_dates.append(poll_date)
                        previous_sample_types.append(sample_type)

                        # Turn poll date into time since poll date
                        dates.append((today - poll_date).astype(int))

                        # Weight based on sample type (LV = 1.5, RV = 1, A = 0.5)
                        if "RV" in sample_type:
                            sample_weights.append(1)
                        elif "V" in sample_type:
                            sample_weights.append(1)
                        elif "A" in sample_type:
                            sample_weights.append(0.5)
                        elif "LV" in sample_type:
                            sample_weights.append(1.5)
                        else:
                            print("WEIRD SAMPLE TYPE??", str(sample_type))

                        
                        # Read off margin (EVEN, dem lead, or rep lead)
                        if poll.find_all(attrs={"class":"net hide-mobile even"}) != []:
                            poll_margin = 0
                        else:
                            if poll.find_all(attrs={"class":"leader hide-mobile"})[0].text == DEM:
                                poll_margin = int(poll.find_all(attrs={"class":"net hide-mobile dem"})[0].text[1:])
                            else:
                                poll_margin = -int(poll.find_all(attrs={"class":"net hide-mobile rep"})[0].text[1:])
                        print(poll_margin, "poll margin")
                        territory_margins.append(poll_margin)
        dates = np.array(dates)
        try:
            # Ratio of days passed over a month
            time_weights = time_weighting(dates/30)
        except ValueError:
            territory_averages.iat[num,0] = 999
            territory_averages.iat[num,1] = 0
            continue
        else:
            if max(dates) == 0:
                territory_averages.iat[num,0] = 999
                territory_averages.iat[num,1] = 0
                continue
        try:
            # Take double weighted (time weighted and sample type weighted) 
            total_weights = time_weights * sample_weights
            territory_average = sum(territory_margins*total_weights)/sum(total_weights)
            print(territory_average, sample_weights, time_weights, total_weights)
        except ZeroDivisionError:
            territory_averages.iat[num,0] = 999
            territory_averages.iat[num,1] = 0
            continue
        territory_averages.iat[num,0] = territory_average
        # territory_averages.iat[num,1] = len(territory_margins)/max(dates)
        territory_averages.iat[num,1] = sum(time_weights)
        print(territory_averages, np.cbrt(len(territory_margins)/max(dates))
)

    # Generate percentage (number of polls / how long since oldest poll)
    territory_averages["poll_num"] /= max(territory_averages["poll_num"])
    territory_averages["percentage"] = np.cbrt(territory_averages["poll_num"])

    with open(os.path.dirname(os.path.abspath(__file__)) + "/data/raw_averages.csv", "w") as f:
        f.write(territory_averages.to_csv(lineterminator="\n"))
    # territory_averages["percentage"] /= sum(territory_averages["percentage"])
    # print(territory_averages["percentage"])
    return territory_averages 

def refine_polling():
    """
    Takes polling margins and adjusts them based on 
    state similarity scores. Also calculates expected margins 
    for states without polling.
    """
    # definitions
    score_data = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + "/data/state_similarities.csv", index_col="Geography")
    score_matrix = score_data.to_numpy()
    territories = np.asarray(score_data.index)

    territory_averages = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + "/data/raw_averages.csv")
    lean_data = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + "/data/state_pvi.csv")
    lean_data["territories"] = lean_data["territories"].str.lower()
    lean_data['pvi'] = lean_data['pvi'].astype(float)
    # Estimate what margins should be based on PVI + national polling average
    lean_data["predicted_margin"] = lean_data["pvi"] + territory_averages["margin"][0]
    for key, series in territory_averages.items():
        lean_data[key] = series
    # Calculate how much democrats are overperforming predicted margin (tilt)
    print(lean_data["margin"], lean_data["predicted_margin"])
    dem_difference = []
    for i in range(len(territories)):
        if lean_data["margin"].iloc[i] in [0, 999]:
            dem_difference.append(0)
        else:
            dem_difference.append(lean_data["margin"].iloc[i]-lean_data["predicted_margin"].iloc[i])
    lean_data["dem difference"] = pd.Series(dem_difference)
    lean_data.drop(["pvi","poll_num"],axis=1,inplace=True)
    deviation_vector = lean_data["dem difference"].to_numpy()
    # print(deviation_vector)
    # Create state weights based on state similarities percentage 
    for num, weight in enumerate(lean_data["percentage"]):
        # Weight on state polls highly, especially those for the state itself, multiplied by percentage
        # (roughly) how many polls there are
        score_matrix[num,num] = (weight+2) ** 5
        score_matrix[num] *= lean_data["percentage"]
        score_matrix[num] /= sum(score_matrix[num])

    with open(os.path.dirname(os.path.abspath(__file__)) + "/data/state_weights.csv", "w") as f:
        modified_score_data = pd.DataFrame(np.around(score_matrix,3))
        modified_score_data.columns = territories
        modified_score_data.index = territories
        modified_score_data.index.name = "Geography"
        f.write(modified_score_data.to_csv(lineterminator="\n"))
    # for num,x in enumerate(score_matrix):
    #     diff_sum = 0
    #     for n, y in enumerate(x):
    #         diff_sum += y * deviation_vector[n]
            # print(lean_data["territories"][num], lean_data["territories"][n], diff_sum, score_matrix[num][n])
    new_deviation_vector = np.dot(score_matrix, deviation_vector)
    print(lean_data["dem difference"])
    print(new_deviation_vector, "new vector")
    new_margin = new_deviation_vector.reshape(len(new_deviation_vector)) + lean_data["predicted_margin"]
    lean_data["new_margin"] = new_margin
    poll_data = lean_data["new_margin"]
    poll_data.index = lean_data["territories"]
    with open(os.path.dirname(os.path.abspath(__file__)) + "/data/polling_averages.csv", "w") as f:
        f.write(poll_data.to_csv(lineterminator="\n"))
    # print(lean_data.sort_values("new_margin"))


if __name__ == "__main__":
    scrape_raw_average()
    refine_polling()