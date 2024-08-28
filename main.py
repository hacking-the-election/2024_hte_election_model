import pandas as pd
import os
from election_simulator import run_simulations, analyze_simulations
from polling_scraper import scrape_raw_average, refine_polling


if __name__ == "__main__":
    scrape_raw_average()
    refine_polling()
    run_simulations(write=True)
    simulations = pd.read_csv(os.path.dirname(os.path.abspath(__file__)) + "/data/simulations.csv")
    analyze_simulations(simulations, write=True)