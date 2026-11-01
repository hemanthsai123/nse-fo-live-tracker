from historical_tracker import run_historical_tracker
from nifty_option_chain import fetch_option_chain

if __name__ == "__main__":
    print("Starting master NSE data pipeline...")
    run_historical_tracker()
    fetch_option_chain()
    print("Master pipeline execution complete.")
