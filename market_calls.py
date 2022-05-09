from io import RawIOBase
from functions import datetime_to_isoformat, to_datetime, to_date, intervals, get
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import os
import pytz

class Symbols:
    def symbol_data(self,ticker):
        call = get(f'/symbols/search?prefix={ticker}')['symbols']
        if len(call) == 0:
            return f"{ticker}: Not Found"
        return call[0]

    def get_ticker_id(self,ticker):
        db_path = os.path.join(os.getenv("STOCK_DATA_PATH"),'DataBase')
        tkr_db_path = os.path.join(db_path,'StockIds.csv')
        if os.path.exists(tkr_db_path):
            ticker_db = pd.read_csv(tkr_db_path,index_col=0,sep="|")
        else:
            ticker_db = pd.DataFrame(columns=['symbol','symbolId','description',
                                            'securityType','listingExchange','isTradable',
                                            'isQuotable','currency'])
            
        if ticker not in ticker_db.symbol.tolist():
            call = get(f'/symbols/search?prefix={ticker}')['symbols']
            if len(call) == 0:
                print(f"{ticker}: Not Found")
                return 0
            else:
                data = call[0]
                _df = pd.DataFrame([[t] for t in data.values()],index=data.keys()).T  
                ticker_db = ticker_db.append(_df,ignore_index=True)
                ticker_db.to_csv(tkr_db_path,sep="|")
                print(f"{ticker}: {data['symbolId']} UPDATED")
        # else:
        #     print(f"{ticker}: {ticker_db[ticker_db.symbol==ticker].symbolId.iloc[0]}")
        return ticker_db[ticker_db.symbol==ticker].symbolId.iloc[0]

    def symbol_exch(self, ticker):
        return self.symbol_data(ticker)['listingExchange']

    def option_chain(self, ticker):
        now = datetime.today()
        today = dt.date(now.year, now.month, now.day)
        try:
            _chain = get(f'/symbols/{self.symbol_id(ticker)}/options')['optionChain']
            df = pd.DataFrame(_chain)
            # CHAIN CLEANUP
            df.drop(labels = ['listingExchange', 'description', 'optionExerciseType'], axis = 1, inplace = True)
            df['rawExpiryDate'] = df['expiryDate']
            df['expiryDate'] = df['expiryDate'].apply(to_date)
            df['daysToExpire'] = df['expiryDate'].apply(lambda x: (x - today).days)
            df['weeksToExpire'] = [d // 7 for d in df.daysToExpire.to_list()]
            df['expiryWkDay'] = df.expiryDate.apply(datetime.weekday)
            return df
        except:
            return f"No chain found for {ticker}."

    def option_id(self, ticker, strike, expiry_date, direction):
        option_df = self.option_chain(ticker)
        print(f"{ticker}: Chain")
        # OPTION CHAIN BY EXPIRY
        try:
            chain_root = pd.DataFrame(
                option_df[option_df['expiryDate'] == datetime.strptime(expiry_date, '%Y-%m-%d').date()][
                    'chainPerRoot'].iloc[0][0]['chainPerStrikePrice'])
            print(f"Expiry: {expiry_date}")
            try:
                _root = chain_root[chain_root.strikePrice == strike]
                print(f"Strike ${strike}")
                if direction.lower() == 'c':
                    _option_id = _root.callSymbolId.iloc[0]
                elif direction.lower() == 'p':
                    _option_id = _root.putSymbolId.iloc[0]
                else:
                    _option_id = 0
            except:
                print(f"!!!!Strike ${strike} NOT FOUND!!!!")
                _option_id = 0
        except:
            print(f"!!!!Expiry: {expiry_date} NOT FOUND!!!!")
            _option_id = 0
        return _option_id

    def option_wk_root(self, ticker, WEEK = 0, DAY = 4):
        """
        days_to_expire: int | strike_price: int | side: c/p (call or put)

        days_to_expire: Default (earliest expiry)

        WEEK: weeks to expire
        wk_day = 4 # FRIDAY
        retruns >>>> DataFrame by Default including Call and Put Ids for a given strike prices
        """
        df = self.option_chain(ticker)
        try:
            # print(f"Expiry Weeks: {list(set(df.weeksToExpire.to_list()))}")
            expiry_weeks = list(set(df.weeksToExpire.to_list()))
            if int(WEEK) not in expiry_weeks:
                print("Earliest Week Available:", expiry_weeks[0])
                earliest_week = expiry_weeks[0]
                if earliest_week < 1:
                    WEEK = expiry_weeks[1]
                else:
                    WEEK = earliest_week
                print(f"WEEK MODIFIED TO: {WEEK}")

            try:
                df_id_list = df[(df.weeksToExpire == WEEK) & (df.expiryWkDay == DAY)]
                if len(df_id_list) > 0:
                    print("!!!Chain Found!!!")
                    print(f"Expiry Wk:{df_id_list.weeksToExpire.iloc[0]} wk_Day:{df_id_list.expiryWkDay.iloc[0]}")
                    _ids_list = df_id_list.iloc[0].chainPerRoot[0]['chainPerStrikePrice']
                else:
                    # TRY NEXT WEEK
                    df_id_list = df[(df.weeksToExpire == int(WEEK) + 1) & (df.expiryWkDay == DAY)]
                    print(f"Expiry Wk:{df_id_list.weeksToExpire.iloc[0]} wk_Day:{df_id_list.expiryWkDay.iloc[0]}")
                    _ids_list = df_id_list.iloc[0].chainPerRoot[0]['chainPerStrikePrice']
            except:
                print("Week and WeekDay Contract Not Found")
                # GETTING THE LAST EXPIRY CONTRACT
                _ids_list = df.iloc[-1].chainPerRoot[0]['chainPerStrikePrice']

            if len(_ids_list) > 0:
                chain_root = pd.DataFrame(_ids_list)
                return chain_root

            else:
                print("No chain_root found!")
                return [0]
        except:
            return [0]


class Market(Symbols):
    def __init__(self) -> None:
        super().__init__()

    def markets(self):
        mrkt = get('/markets')
        mrkt = pd.DataFrame(mrkt['markets'])
        cols = ['extendedStartTime', 'startTime', 'endTime', 'extendedEndTime']
        for col in cols:
            mrkt[col] = mrkt[col].apply(to_datetime)
            mrkt[col].replace()
        return mrkt

    def market_hours(self, EXCH = 'NASDAQ'):
        data = self.markets()
        try:
            _startTime, _endTime = data[data['name'] == EXCH][['startTime', 'endTime']].iloc[0]
        except:
            print("Fixed Market Hours 9:30-16:00")
            t = datetime.today()
            _startTime = t.replace(hour=9,minute=30,second=0,microsecond=0)
            _endTime = t.replace(hour=16,minute=0,second=0,microsecond=0)
        return _startTime, _endTime

    def market_candles(self,ticker:str,time_frame:str,start_date=None,end_date:str=""):
        """
        ticker: Stocks and ETFs Symbol
        time_frame: 1m 2m 3m 4m 5m 10m 15m 20m 30m 1H 2H 4H 1D 1W 1M 1Y
        start_date: (int/str) Default: 100 days back # Includes holidays
            int: days back 
            str:YYYY-mm-dd
        end_date: (str:YYYY-mm-dd)
        """
        eastern = pytz.timezone("US/Eastern")
        try:
            ticker_id = self.get_ticker_id(ticker)
        except:
            return "Ticker ID Error!"
            # "Ticker ID Error!"

        # Current EST
        current_time = datetime.now(eastern)
        # End Date Handling
        if end_date=='':
            end = current_time.isoformat('T')
        else:
            end = datetime_to_isoformat(end_date,_type='end')
        # Start Date Handling
        if type(start_date)==str:
            start = datetime_to_isoformat(datetime.strptime(start_date,'%Y-%m-%d'))
        elif type(start_date)==int:
            start = (current_time.replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=start_date)).isoformat("T")
        else:
            # Default: 100 days
            start = (current_time.replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=100)).isoformat("T")
        _time_frame = intervals(time_frame)
        data = get(f'/markets/candles/{ticker_id}?startTime={start}&endTime={end}&interval={_time_frame}')
        try:
            df = pd.DataFrame(data['candles'])
            df['start'] = df['start'].apply(to_datetime)
            df['end'] = df['end'].apply(to_datetime)
            df.index = df.start
            df.index.name = 'Date'
            df.rename(columns = {'start': 'StartTime', 'end': 'EndTime', 'open': 'Open', 'high': 'High', 'low': 'Low',
                'close': 'Close', 'volume': 'Volume'}, inplace = True)
            return df
        except:
            print(f"{ticker}| !ERROR: Encountered in market_candles(...) ")
            _d = pd.DataFrame(columns=['StartTime', 'EndTime', 'Low', 'High', 'Open', 'Close', 'Volume', 'VWAP'],index='Date')
            _d.index.name = 'Date'
            return _d

    def DataReader(self, ticker:str, time_frame:str, duration:int=365,_start_date:datetime=None):
        """
        _start_date: str
        duration: int
        """
        ticker = ticker.upper()
        _start = _start_date if _start_date else duration
        # INIT First Call
        main_df = self.market_candles(ticker, time_frame=time_frame,start_date=_start)
        # print(f"Main_df: {len(main_df)}")
        if len(main_df)>0:
            lastCall_MAXROW = len(main_df)
            print_count = 1
            while lastCall_MAXROW >= 20000:
                print("*"*print_count,end='\r')
                last_date = datetime.strftime(max(main_df.index).date(),'%Y-%m-%d')
                # MAKE NEW CALL
                df = self.market_candles(ticker, time_frame=time_frame,start_date=last_date)
                print(f"df: {len(main_df)}")
                lastCall_MAXROW  = len(df)
                main_df.reset_index(inplace=True)
                df.reset_index(inplace=True)
                main_df = main_df.append(df,ignore_index=True)
                # REMOVE DUPLICATE ITEMS
                main_df = main_df[~main_df['Date'].duplicated(keep = 'last')]
                # SORT VALUES BY DATE
                main_df.sort_values("Date",inplace=True)
                # SET DATE AS INDEX
                main_df.set_index('Date',inplace=True)
                #print(f"Main_df: {len(main_df)}")
                print_count += 1
            return main_df
        else:
            print(f"{ticker}| !ERROR: Encountered in DataReader(...) ")
            _d = pd.DataFrame(columns=['Date','StartTime', 'EndTime', 'Low', 'High', 'Open', 'Close', 'Volume', 'VWAP'])
            _d.set_index('Date',inplace=True)
            return _d

    def quote(self, ticker = None, _id = None):
        """
        Ticker: Stocks and ETFs symbols
        _id: Use for Options
        """
        # if ticker:
        #     _id = self.get_ticker_id(ticker)
        # elif not _id and not ticker:
        #     return "No ticker or Symbol_ID given"
        try:
            _id = self.get_ticker_id(ticker)
            q = get(f'/markets/quotes/{_id}')['quotes'][0]
        except:
            q = {
                'symbol': ticker,
                'symbolId': 0,
                'tier': '',
                'bidPrice': 0,
                'bidSize': 0,
                'askPrice': 0,
                'askSize': 0,
                'lastTradePriceTrHrs': 0,
                'lastTradePrice': 0,
                'lastTradeSize': 0,
                'lastTradeTick': '-',
                'lastTradeTime': '',
                'volume': 0,
                'openPrice': 0,
                'highPrice': 0,
                'lowPrice': 0,
                'delay': 0,
                'isHalted': False,
                'high52w': 0,
                'low52w': 0,
                'VWAP': 0
            }
        return pd.Series(q)

    def options_data(self, ticker, expiry, start, end):
        pass


if __name__=='__main__':
    ticker = 'SPY'
    time_frame = '1D'
    market = Market()
    df = market.market_candles(ticker,time_frame)
    print(df)
