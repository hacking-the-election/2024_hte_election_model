import requests
import sys
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

def pvi_retriever(path=None):
    """
    Calculates the state pvi based on the 2012, 2016, 2020
    presidential elections using Wikipedia infoboxes. DOES not compute for Maine/Nebraska congressional districts.
    Args:
        path - Writes csv file to path, otherwise returns
        series.
    """
    score_data = pd.read_csv("data/state_similarities.csv", index_col="Geography")
    # no = BeautifulSoup(requests.get("https://en.wikipedia.org/wiki/Cook_Partisan_Voting_Index").content).body.find(id="mw-content-text").div.table
    # print(no)
    # for row in no.tbody.tr.next_siblings:
    # quit()
    years = ["2012", "2016", "2020"]
    dems = ["Barack Obama", "Hillary Clinton", "Joe Biden"]
    average_pvi = np.zeros(50)
    states = []
    for num in range(3):
        things = []
        dem_percentages = []
        rep_percentages = []
        for state in score_data.columns:
            if state == "District of Columbia":
                continue
            print(state)
            if num == 0:
                states.append(state)
            if state == "Washington":
                state = "Washington_(state)"
            if state.lower() == "national":
                l = 'https://en.wikipedia.org/wiki/' + years[num] + '_United_States_presidential_election'
            else:
                l = 'https://en.wikipedia.org/wiki/' + years[num] + '_United_States_presidential_election_in_' + state.replace(" ","_")
            seen_already = False
            dem_lead = False
            percentage_num = 0
            # Get info box
            no = BeautifulSoup(requests.get(l).content).body.find(id="content").find(id="bodyContent").find(id="mw-content-text").div.find(class_="infobox")
            for thing in no.tbody.tr.next_siblings:
                # print(thing)
                try:
                    for y in thing.td.table.tbody.find_all("tr"):
                        for th1 in y.find_all('td'):
                            # print(th1)
                        # iterate through rows of infobox
                            if seen_already == False:
                                try:
                                    # find leader
                                    if th1.b.a.text.strip() ==  dems[num]:
                                        dem_lead = True
                                        seen_already = True
                                except:
                                    pass
                            if percentage_num < 2:
                                try:
                                    # if voting percentage, add it to list (things)
                                    if th1.text.strip()[-1] ==  "%":
                                        try:
                                            percentage = float(th1.text.strip()[:-1])
                                            if dem_lead == False:
                                                if percentage_num == 0:
                                                    rep_percentages.append(percentage)
                                                    print(state, percentage, "appeneded to rep")
                                                else:
                                                    dem_percentages.append(percentage)
                                                    print(state, percentage, "appeneded to dem")
                                            else:
                                                if percentage_num == 1:
                                                    rep_percentages.append(percentage)
                                                    print(state, percentage, "appeneded to rep")
                                                else:
                                                    dem_percentages.append(percentage)
                                                    print(state, percentage, "appeneded to dem")
                                            percentage_num += 1
                                            # things.append(percentage)
                                        except:
                                            pass
                                except:
                                    pass
                except: 
                    pass
        things = np.array(things)
        # turn things into margins
        print(dem_percentages, rep_percentages)
        margins = np.array([dem_percentages[i]-rep_percentages[i] for i in range(len(dem_percentages))])
        # margins = things[::2]-things[1::2]
        pvi = margins[1:]-margins[0]
        print(margins, pvi)
        average_pvi += pvi
    # Average pvi out between the three elections
    average_pvi = average_pvi/3
    # np.insert(average_pvi, 0, "National")
    # states.remove("District of Columbia")
    states.remove("National")
    pvi = pd.Series(average_pvi, name="pvi")
    if path:
        with open("./data/state_pvi.csv", "w") as f:
                pvi.index = states
                pvi.index.name = "territories"
                f.write(pvi.round(2).to_csv())
    return pvi

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pvi_retriever(sys.argv[1])
    else:
        pvi = pvi_retriever(sys.argv[1])
        print(pvi)