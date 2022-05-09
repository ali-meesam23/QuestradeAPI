import requests
import json
import os



def auth_token(refresh_token = None):
    """
    Retrieves Auth and Refresh Token Data
    """
    tkn_path = os.getenv("QUESTRADE_TOKEN_PATH")
    if os.path.exists(tkn_path) and not(refresh_token):
        # GET ACCESS TOKEN FROM LOCAL FILE
        with open(tkn_path, 'r') as f:
            token_data = json.loads(f.read())
            f.close()
    elif refresh_token:
        # SEND REFRESH TOKEN TO QUESTRADE
        url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={refresh_token}"
        try:
            resp = requests.get(url)
            # TOKEN DATA
            token_data = resp.json()
        except:
            refresh_token = input("ERROR!>>Enter a new refresh token: ")
            url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={refresh_token}"
            resp = requests.get(url)
            # TOKEN DATA
            token_data = resp.json()

        # SAVE TOKEN FROM REFRESH_TOKEN TO LOCAL FILE
        with open(tkn_path, 'w') as f:
            f.write(json.dumps(token_data))
            print("New Token Created",end='\r')
            f.close()
    else:
        print(f"token.json NOT FOUND\n No refresh token provided!")
        refresh_token = input("Enter refresh_token: ")
        # SEND REFRESH TOKEN TO QUESTRADE
        url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={refresh_token}"
        resp = requests.get(url)
        # TOKEN DATA
        token_data = resp.json()
        # SAVE TOKEN FROM REFRESH_TOKEN TO LOCAL FILE
        with open(tkn_path, 'w') as f:
            f.write(json.dumps(token_data))
            f.close()
    return token_data

if __name__=='__main__':
    auth_token(refresh_token=True)