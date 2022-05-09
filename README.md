# QuestradeAPI
Questrade API is designed to link one user account to Questrade Brokerage. 
It allows the user to gain access to realtime quotes (if market data package is active) or delayed quotes plus historical market data for stocks as well as options contracts.

Add the following PATHs to your shell (.bash_profile or .zshrc):
'''
sudo nano ~/.zshrc or ~/.bash_profile
export QUESTRADE_AUTH_PATH=“$HOME/.pswd/questrade_access_token”
export STOCK_DATA_PATH=“$HOME/Location_to_Data_Archive_Folder/"
'''

*Inside this path, follow the following Directory Structure:*

$STOCK_DATA_PATH/Database/

$STOCK_DATA_PATH/OHLC/
