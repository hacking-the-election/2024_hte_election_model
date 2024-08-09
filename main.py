from election_simulator import run_simulations, analyze_simulations
from polling_scraper import scrape_raw_average, refine_polling

if __name__ == "__main__":
    scrape_raw_average()
    refine_polling()
    run_simulations()
    analyze_simulations()