from authenticate import auth_token
import requests
import datetime as dt
from datetime import datetime
import pytz
from dateutil.parser import parse


def parse_date_convert(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d %H:%M:%S' # Defaults to : 2022-08-31 07:47:30
    get_date_obj = parse(str(date))
    return str(get_date_obj.strftime(fmt))


def get(path,params=None):
    # GET UPDATED TOKEN
    token_data = auth_token()
    token = token_data
    # PREP GET REQUEST
    url = token['api_server']
    access_token = token['access_token']
    token_type = token['token_type']
    auth = {'Authorization': str(token_type + " " + access_token)}
    version = 'v1'
    resp = requests.get(str(url+version+path), headers=auth, params = params)
    data = resp.json()
    ########### USING EXISTING TOKEN ###########
    if 'code' in data.keys() and data['code'] == 1017:
        print("Token Refresh...",end='\r')
        _refresh_token = token['refresh_token']
        token_data = auth_token(refresh_token=_refresh_token)
        token = token_data
        url = token['api_server']
        access_token = token['access_token']
        token_type = token['token_type']
        auth = {'Authorization': str(token_type + " " + access_token)}
        version = 'v1'
        resp = requests.get(str(url+version+path), headers=auth, params = params)
        data = resp.json()
        ############ USING NEW TOKEN ###########
        if 'code' in data.keys():
            if data['code'] == 1017:
                print(f"CODE: {data['code']}")
                _refresh_token = input("Enter 'NEW' Refresh Token: ")
                token_data = auth_token(refresh_token=_refresh_token)
                token = token_data
                url = token['api_server']
                access_token = token['access_token']
                token_type = token['token_type']
                version = 'v1'
                auth = {'Authorization': str(token_type + " " + access_token)}
                resp = requests.get(str(url+version+path), headers=auth, params = params)
                data = resp.json()
            else:
                data = {}
                print(data)
    return data


# *******************GLOBAL FUNCTIONS*******************
def datetime_to_isoformat(date='today',timezone = 'US/Eastern',_type='start'):
    """
    Default Timezone: US/Eastern - Today's Date
    Date: YYY-mm-dd
    """    
    eastern = pytz.timezone(timezone)
    if date == 'today':
        d = datetime.now(tz=pytz.timezone(timezone))
    elif type(date) == datetime:
        d = eastern.localize(date)
    else:
        d = datetime.strptime(date,"%Y-%m-%d")
        if _type=='end':
            d = d.replace(hour=23,minute=59,second=59)
        d = eastern.localize(d)
    return d.isoformat("T")


def to_date(date:str):
    return parse(date).replace(tzinfo=None).date()


def to_datetime(date_time:str):
    return parse(date_time).replace(tzinfo=None)


def intervals(candle='15m'):
    """
    '1m':'OneMinute','2m':'TwoMinutes','3m':'ThreeMinutes','4m':'FourMinutes','5m':'FiveMinutes','10m':'TenMinutes',
    '15m':'FifteenMinutes','20m':'TwentyMinutes','30m':'HalfHour','1H':'OneHour','2H':'TwoHours','4H':'FourHours',
    '1D':'OneDay','1W':'OneWeek','1M':'OneMonth','1Y':'OneYear'
    """
    time_interval = {
    '1m':'OneMinute',
    '2m':'TwoMinutes',
    '3m':'ThreeMinutes',
    '4m':'FourMinutes',
    '5m':'FiveMinutes',
    '10m':'TenMinutes',
    '15m':'FifteenMinutes',
    '20m':'TwentyMinutes',
    '30m':'HalfHour',
    '1H':'OneHour',
    '2H':'TwoHours',
    '4H':'FourHours',
    '1D':'OneDay',
    '1W':'OneWeek',
    '1M':'OneMonth',
    '1Y':'OneYear'}
    return time_interval[candle]


def fix_dailytime_range(df,time_col='start',start=(9,30),end=(16,0)):
    """
    time_col: Time Column
    24 Hours Clock
    start: tuple (H:M)
    end: tuple (H:M)
    """
    df['Hrs'] = df[time_col].apply(lambda x:x.time())
    df = df[(df.Hrs>=dt.time(start[0],start[1])) & (df.Hrs<dt.time(end[0],end[1]))]
    return df
