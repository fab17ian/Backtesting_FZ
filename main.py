from src.portfolio import Portfolio
from src.data_reader import DataReader
import urllib.request
import pandas as pd


def main():
    """The main function of the trading bot."""
    # Initialize the DataReader class and get the stock data
    Date = "2010-01-01"
    data_reader = DataReader(Date)                 #ab hier werden die Daten von yfinance geladen
    data_reader.run()
    portfolio = Portfolio(streakLength=3, thresholdType="returnRaw")
    #portfolio = Portfolio(streakLength=7, thresholdType="returnRaw")
    #portfolio = Portfolio(streakLength=8, thresholdType="returnRaw")

    portfolio.visualize_portfolio()
    #portfolio.get_FamaFrech_3Factors_weekly(Date)



    try:
        print("#============================" "=============================#\n")

        print("The trading bot has finished running.")
    except KeyboardInterrupt:
        print("\n\nThe trading bot has been interrupted.")


if __name__ == "__main__":
    main()

