import numpy as np 
import numpy.polynomial.polynomial as poly
import pandas as pd 
import requests
from math import exp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from polling_error import polling_error_coeffs

REP = "Trump"
DEM = "Harris"

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

def setup():
    """
    Initalizes some global variables for use in other functions.
    """
    global date, election_date, score_matrix, territories
    date = np.datetime64('today')
    election_date = np.datetime64('2020-11-03')
    score_data = pd.read_csv("data/state_similarities.csv", index_col="Geography")
    score_matrix = score_data.to_numpy()
    territories = np.asarray(score_data.index)
    global time_weighting 
    time_weighting = np.vectorize(time_weighting)

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
    setup()
    time = np.datetime64(np.datetime64('now'), 'h')
    time_string = np.datetime_as_string(time, unit='h')
    to_fill = {"margin":np.zeros(len(territories)), "poll_num":np.zeros(len(territories))}
    territory_averages = pd.DataFrame(to_fill)
    for num, territory in enumerate(territories):
        if num == 1:
            quit()
        territory = territory.replace("-","/")
        territory = territory.replace(" ","-")
        print(territory.lower())
        # link = "https://www.realclearpolitics.com/epolls/2020/president/us/general_election_" + REP.lower() + "_vs_" + DEM.lower() + "-6247.html"
        link = "https://projects.fivethirtyeight.com/polls/president-general/2024/" + territory.lower() + "/"
        chromedriver_path= "/home/pbnjam/.cache/selenium/chromedriver/linux64/127.0.6533.99/chromedriver"
        # driver = webdriver.Chrome(chromedriver_path)
        service = Service(executable_path='C:/Program Files (x86)/Google/Chrome/Application/chrome.exe')
        driver = webdriver.Chrome(service=service)
        driver.get(link)
        time.sleep(3) #if you want to wait 3 seconds for the page to load
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        yes = requests.get(link)
        print(yes.json())
        if yes.status_code == 404:
            territory_averages.iat[num,0] = 999
            territory_averages.iat[num,1] = 0
            continue
        soup = BeautifulSoup(yes.content, features="lxml")
        print(soup)
        poll_container = soup.body.find(attrs={"class":"container content"}).find(attrs={"class":"day-container"}).find_all(attrs={"class":"polls-table"})[0]
        # poll_container = soup.body.find(attrs={"class":"container content"}).find(attrs={"class":"day-container"})
        # print(poll_co ntainer)
        territory_margins = []
        dates = []
        # print(poll_container.children)
        for x in poll_container.children:
            # print(x)
            # Iterate through polls
            # day = x.table.tbody
            # for poll in x.find(attrs={"class":"visible-row"}):
            for poll in x.find_all("tr", attrs={"class":"visible-row"}):
            # poll = x.tr
                poll_date = poll.find(attrs={"class":"date-wrapper"}).text
                # print(poll_date.find(" "))
                poll_date = poll_date[:poll_date.find("-")]
                poll_date = date_converter(poll_date)
                print(poll_date)
                # Ignore polls not including rep/dem candidates
                choices = poll.find(attrs={"class":"answers hide-desktop"}).find_all(attrs={"class":"mobile-answer"})
                choices = [choice.p.text.strip() for choice in choices]
                print(choices)
                if REP not in choices or DEM not in choices:
                    continue
                
                # area = poll.find(attrs={"class":"dates hide-desktop"}).span.text.lower()
                # if territory.lower() in ["maine", "nebraska"]:
                #     if area.lower() != territory.lower():
                #         continue
                # print(poll.prettify())
                # print(poll.find_all(attrs={"class":"visible-row"}))
                # Read off margin (EVEN, dem lead, or rep lead)
                if poll.find_all(attrs={"class":"net hide-mobile even"}) != []:
                    poll_margin = 0
                else:
                    # print(poll.find_all(attrs={"class":"leader hide-mobile"})[0].text)
                    if poll.find_all(attrs={"class":"leader hide-mobile"})[0].text == DEM:
                        poll_margin = int(poll.find_all(attrs={"class":"net hide-mobile dem"})[0].text[1:])
                    else:
                        # print(poll.find_all(attrs={"class":"net hide-mobile rep"}))
                        poll_margin = -int(poll.find_all(attrs={"class":"net hide-mobile rep"})[0].text[1:])
                print(poll_margin, "poll margin ")
                territory_margins.append(poll_margin)
                dates.append((date - poll_date).astype(int))
        dates = np.array(dates)
        try:
            weights = time_weighting(dates/max(dates))
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
            territory_average = sum(territory_margins*weights)/sum(weights)
        except ZeroDivisionError:
            territory_averages.iat[num,0] = 999
            territory_averages.iat[num,1] = 0
            continue
        territory_averages.iat[num,0] = territory_average
        territory_averages.iat[num,1] = len(territory_margins)/max(dates)

    # print(np.cbrt(territory_averages["poll_num"]))
    territory_averages["percentage"] = np.cbrt(territory_averages["poll_num"])
    # territory_averages["percentage"] /= sum(territory_averages["percentage"])
    # print(territory_averages["percentage"])
    return territory_averages 

def refine_polling():
    """
    Takes polling margins and adjusts them based on 
    state similarity scores. Also calculates expected margins 
    for states without polling.
    """
    territory_averages = scrape_raw_average()
    lean_data = pd.read_csv("data/state_pvi.csv")
    lean_data["territories"] = lean_data["territories"].str.lower()
    lean_data['pvi'] = lean_data['pvi'].astype(float)
    lean_data["predicted_margin"] = lean_data["pvi"] + territory_averages["margin"][0]
    for key, series in territory_averages.iteritems():
        lean_data[key] = series
    lean_data["dem difference"] = lean_data["margin"]-lean_data["predicted_margin"]
    lean_data.drop(["pvi","poll_num"],axis=1,inplace=True)
    deviation_vector = lean_data["dem difference"].to_numpy()
    # print(deviation_vector)
    for num, weight in enumerate(lean_data["percentage"]):
        score_matrix[num,num] = (weight+2) ** 5
        score_matrix[num] *= lean_data["percentage"]
        score_matrix[num] /= sum(score_matrix[num])
    with open("data/state_weights.csv", "w") as f:
        modified_score_data = pd.DataFrame(np.around(score_matrix,3))
        modified_score_data.columns = territories
        modified_score_data.index = territories
        modified_score_data.index.name = "Geography"
        f.write(modified_score_data.to_csv())
    for num,x in enumerate(score_matrix):
        diff_sum = 0
        for n, y in enumerate(x):
            diff_sum += y * deviation_vector[n]
            # print(lean_data["territories"][num], lean_data["territories"][n], diff_sum, score_matrix[num][n])
    new_deviation_vector = np.dot(score_matrix, deviation_vector)
    # print(new_deviation_vector)
    new_margin = new_deviation_vector.reshape(len(new_deviation_vector)) + lean_data["predicted_margin"]
    lean_data["new_margin"] = new_margin
    with open("data/polling_averages.csv", "w") as f:
        poll_data = lean_data["new_margin"]
        poll_data.index = lean_data["territories"]
        f.write(poll_data.to_csv())
    # print(lean_data.sort_values("new_margin"))


if __name__ == "__main__":
    refine_polling()