import pandas as pd
import datetime as dt
from pandas.tseries.offsets import BusinessDay
import matplotlib.pyplot as plt
import numpy as np
import requests
from io import StringIO

class Portfolio:
    def __init__(self, streakLength=4, thresholdType="returnRaw") -> None:
        """Initialize the Portfolio class."""
        # Read the CSV file
        self.stockData, self.marketInterest, self.ff_weekly = self._read_csv()          #Daten werden einfach nur eingelesen, die in data_reader erstellt wurden

        # Initialize the hyperparameters
        self.streakLength = streakLength
        self.thresholdingType = thresholdType
        self.holdingPeriod = None # TODO: Implement
        self.weighting = None # TODO: Implement
        self.longShort = None # TODO: Implement

        # Initialize the dataFrames
        self.returns = None
        self.threshCapm = None

        # Run the trading strategy
        self.dailyReturnsLong, self.dailyReturnsShort, self.datesLong, self.datesShort = self._run()     #bekommen 4 Listen zurück, 2 mit den täglichen durchschnittlichen Rendite und 2 mit den Tagen an denen Rendite erzielt wurde
        self._calculate_annualized_return()
        self.performance_portfolio()

    def _run(self) -> None:
        """Run the trading strategy."""
        self.returns, self.threshCapm = self._prepare_data()            #Daten werden verarbeitetet, Dataframe mit Returns und was anderes zurückgegeben
        # formation_date = pd.Timestamp("2024-05-15")
        # self.los, self.win = self.calculate_loser_winner_streaks(formation_date, self.streak_length)
        # print("Output", self.los, self.win)

        dailyReturnsLong, dailyReturnsShort, datesLong, datesShort  = self._calculate_long_short_portfolio()                #bekommen 2 Listen zurück mit den durch. töglichen Renditen und eine an welchen Tagen diese Renditen gemacht werden
        #print("Returns long", dailyReturnsLong)
        print("Returns short", dailyReturnsShort)
        #print("Tage an den Long Rendite erzielt wird:", datesLong)
        #print("Tage an den short Rendite erzielt wird:", datesShort)
        return dailyReturnsLong, dailyReturnsShort, datesLong, datesShort

    def _choose_thresholding_type(self, thresholdType) -> int:
        """Choose the thresholding type."""
        if thresholdType == "CAPM":
            return "Streak_CAPM"
        elif thresholdType == "marketExcessReturn":
            return "Streak_Market_Return"
        elif thresholdType == "returnRaw":
            return "Streak_Raw_Return"
        else:
            print(
                "Invalid thresholding type. Please choose one of the following: CAPM, marketExcessReturn, returnRaw"
            )

    def _read_csv(self) -> pd.DataFrame:
        """Read the CSV file."""
        try:
            stockData = pd.read_csv(
                "/Users/fabianzanghellini/Desktop/Seminararbeit Finance SS24/Backtesting/data/sp500_stock_data.csv"
            )
            marketInterest = pd.read_csv(
                "/Users/fabianzanghellini/Desktop/Seminararbeit Finance SS24/Backtesting/data/market_interest.csv"
            )
            ff_weekly = pd.read_csv("/Users/fabianzanghellini/Desktop/Seminararbeit Finance SS24/Backtesting/data/ff_weekly.csv")
        except Exception as e:
            print(f"Error loading data: {e}")
        return stockData, marketInterest, ff_weekly

    def _prepare_data(self):
        """Prepare the data for the trading strategy."""
        self.stockData["DATE"] = pd.to_datetime(self.stockData["DATE"])                         #konvertieren in Datumsangabe
        prices = self.stockData.pivot(index="DATE", columns="TICKER", values="CLOSE")           #neuer Datensatz wird erstellt, jede Spalte ein Ticker, jede Zeile ein Datum, und drin stehen die Schlusskurse
        returns = prices.pct_change()                                                           #Dataframe der die Returns enthält (Preisverändeungen)
        threshCapm = pd.DataFrame(index=prices.index, columns=prices.columns)                   #leerer DF mit gleicher Struktur wie prices-DF

        return returns, threshCapm

    def _get_previous_business_day(self, dt) -> dt.datetime:                                    #für gegebenes Datum dt soll der vorherige Werktag gefunden werden
        while True:
            if dt.weekday() < 5 and dt not in self.returns.index:                               #Montag = 0; ..
                dt -= BusinessDay(1)
            else:
                return dt

    # def _get_previous_business_day(self, date) -> dt.datetime:
    #     """Get the previous business day."""
    #     while date not in self.returns.index:
    #         date -= BusinessDay(1)
    #     return date

    def _get_previous_returns(self, formation, streak_length=5) -> pd.DataFrame:
        """Get the previous returns for the given streak length."""
        previous_returns = {}
        for i in range(1, self.streakLength + 1):
            previous_day = formation - pd.offsets.BusinessDay(i)
            previous_returns[f"ret_{i}"] = self.returns.loc[
                self._get_previous_business_day(previous_day)                       #in previous returns werden die Ticker und die zugehörigen retruns tageweise gespeichert
            ]
        return pd.DataFrame(previous_returns)                                                  #hier liegen die Renditen der Streak drin

    def _calculate_streak_raw_return(self, x) -> int:
        """Calculate if there is a streak raw return."""
        return 1 if (x > 0).all() or (x < 0).all() else 0                                     #wenn in einer Zeile alle Werte größer oder alle Werte kleiner 0 ist, eine 1 zurück

    def _calculate_loser_winner_streaks(self, formation, streak_length=5) -> tuple:
        """Calculate the loser and winner streaks for the given formation date."""
        returnStreak = pd.DataFrame(self._get_previous_returns(formation, streak_length))       #Dataframe erstellen, der die Renditen gegeben dem Datum und der strak length enthölt
        returnStreak["Streak_Raw_Return"] = returnStreak.apply(
            lambda x: self._calculate_streak_raw_return(x), axis=1                              #zeilenweiser Methodenaufruf, der calculate...Funktin, neue Spalte entsteht, entweder mit 0 (wenn keine Streak) oder mit der durchschnittlichen Renidte der streak tage
        ) * returnStreak.mean(axis=1)
        returnStreak["Streak_Market_Return"] = 0  # TODO: implement
        returnStreak["Streak_CAPM"] = 0  # TODO: implement
        thresholdType = self._choose_thresholding_type(self.thresholdingType)                   #Ausgabe welche Thresholding wir gewählt haben, wird aber nicht angezeigt ???
        losersRawReturn = returnStreak[returnStreak[thresholdType] < 0].index                   #Liste mit Unternehmen die eine Streak haben
        print("Amount of Stock for this day that are losers", len(losersRawReturn))
        winnersRawReturn = returnStreak[returnStreak[thresholdType] > 0].index
        #print("Amount of Stock for this day that are losers", len(losersRawReturn))            #für einheitlich eventuell noch einfügen


        # TODO: Calculate the weighted returns for the losers and winners
        # Calculate the average raw return for losers and winners (Equal weighted)
        losRetRawReturn = self.returns.loc[
            formation, self.returns.columns.isin(losersRawReturn)               #tägliche durch. Rendite aller Unternehmen mit vorangeganer neg. Streak
        ].mean()
        winRetRawReturn = self.returns.loc[
            formation, self.returns.columns.isin(winnersRawReturn)
        ].mean() * (-1)                                                             #tageweise die mittlere Rendite der Unternehmen errechnen die eine Streak haben (und deshalb in losersRawReturn stehen)

        # return losret, winret
        return losRetRawReturn, winRetRawReturn             #zurück kommt die durchschnittliche Rendite am formation Tag für die Unternehmen mit pos und neg Streak

    def _calculate_long_short_portfolio(self, streakLength=5) -> tuple:
        """Calculate the daily returns for given streak length."""
        returnsLong = []
        returnsShort = []
        datesLong = []                                                                      #4 leere Listen werden erstellt
        datesShort = []

        # Go through each day but starting from the 6th day since we need 5 days to calculate the streak
        for date in self.returns.index[8:]:
            # Berechne die Long- und Short-Renditen für das aktuelle Datum
            long_return, short_return = self._calculate_loser_winner_streaks(pd.Timestamp(date), streakLength)

            # Füge die Long-Rendite und das Datum hinzu, wenn ein Long-Rendite-Wert berechnet wurde
            if pd.notna(long_return):
                returnsLong.append(long_return)
                datesLong.append(pd.Timestamp(date).date())

            # Füge die Short-Rendite und das Datum hinzu, wenn ein Short-Rendite-Wert berechnet wurde
            if pd.notna(short_return):
                returnsShort.append(short_return)
                datesShort.append(pd.Timestamp(date).date())

        return returnsLong, returnsShort, datesLong, datesShort                                             #Liste mit den täglichen Renditen der Unternehmen pps. (short) Streak

    def _plot_data(self) -> None:
        """Plot the daily returns for the long and short portfolios."""
        print(self.returns)
        print(self.threshCapm)

    def _calculate_annualized_return(self) -> None:
        """Calculate the annualized return."""
        cleanReturnsLong = [x for x in self.dailyReturnsLong if str(x) != "nan"]
        cleanReturnsShort = [x for x in self.dailyReturnsShort if str(x) != "nan"]

        longData = pd.DataFrame({
        'Date': self.datesLong,
        'Return': self.dailyReturnsLong
        })

        shortData = pd.DataFrame({
            'Date': self.datesShort,
            'Return': self.dailyReturnsShort
        })
        longData['Date'] = pd.to_datetime(longData['Date'])
        longData.set_index('Date', inplace=True)

        shortData['Date'] = pd.to_datetime(shortData['Date'])
        shortData.set_index('Date', inplace=True)

        dailyReturnLong = np.array(cleanReturnsLong).mean()
        dailyReturnShort = np.array(cleanReturnsShort).mean()

        monthly_Return_Long = longData['Return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_Return_Short = shortData['Return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        annual_Return_Long = longData['Return'].resample('Y').apply(lambda x: (1 + x).prod() - 1)
        annual_Return_Short = shortData['Return'].resample('Y').apply(lambda x: (1 + x).prod() - 1)

        aver_Monthly_Return_Long = monthly_Return_Long.mean()
        aver_Monthly_Return_Short = monthly_Return_Short.mean()
        global aver_annual_Return_Long
        aver_annual_Return_Long = annual_Return_Long.mean()
        aver_annual_Return_Short = annual_Return_Short.mean()

        total_Return_long = np.prod([(1 + r) for r in cleanReturnsLong]) - 1

        print("Average daily long return ", dailyReturnLong)
        print("Average monthly long return ", aver_Monthly_Return_Long)
        print("Average annual long return ", aver_annual_Return_Long)
        print("Total long return ", total_Return_long)

    def performance_portfolio(self) -> None:

        ### Volatility ###

        returnLong_variance = np.array(self.dailyReturnsLong).var()
        returnLong_volatility= np.sqrt(returnLong_variance)
        print("Varianz des long Portfolio:", returnLong_variance)
        print("Volatilität des long Portfolio:", returnLong_volatility)

        ###Risk Free###

        self.ff_weekly['Date'] = pd.to_datetime(self.ff_weekly['Date'])
        self.ff_weekly.set_index('Date', inplace=True)
        riskFree_Monthly_Rate_ = self.ff_weekly['RF'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        riskFree_annual_Rate_ = self.ff_weekly['RF'].resample('Y').apply(lambda x: (1 + x).prod() - 1)
        #print("Risk Free Rate:", riskFree_annual_Rate_)

        aver_riskFree_Rate = riskFree_annual_Rate_.mean()

        ###Sharp Ratio###

        sharp_Ratio = (aver_annual_Return_Long - aver_riskFree_Rate) / returnLong_volatility
        print("Sharp Ratio: ", sharp_Ratio)





    def visualize_portfolio(self):
        """Visualize the portfolio."""
        cleanReturnsLong = [x for x in self.dailyReturnsLong if str(x) != "nan"]
        cleanReturnsShort = [x for x in self.dailyReturnsShort if str(x) != "nan"]

        initialBudget = 1
        budgetLong = [initialBudget]
        budgetMarket = [initialBudget]
        budgetShort = [initialBudget]

        min_length = min(len(cleanReturnsLong), len(cleanReturnsShort), len(self.marketInterest["SP500_Returns"]))

        for i in range(1,min_length):
            budgetLong.append(budgetLong[i - 1] * (1 + cleanReturnsLong[i]))
            budgetShort.append(budgetShort[i - 1] * (1 + self.dailyReturnsShort[i]))
            budgetMarket.append(budgetMarket[i - 1] * (1 + self.marketInterest["SP500_Returns"][i]))
        plt.plot(budgetLong, label="Long Portfolio")
        plt.plot(budgetMarket, label="Market Portfolio")
        plt.plot(budgetShort, label="Short Portfolio")
        plt.legend()
        plt.show()



# trading = TradingBot()

