import json
import os
import pandas as pd
from datetime import date
import datetime
import requests
from datetime import datetime, timedelta



def read_games():

    data = open("data/liiga2024.json", "r")
    data = json.load(data)
    return data


def get_team_data_by_date(startDate, monthBefore):
    url = "https://www.liiga.fi/api/v2/teams/stats?seasonFrom="+monthBefore+"&seasonTo="+startDate+"&tournament=runkosarja&dataType=standings"
    res = requests.get(url)
    print("Team standings",res.status_code)
    data = json.loads(res.text)

    df_stand = pd.DataFrame(data)
    
    url_shots = "https://www.liiga.fi/api/v2/teams/stats?seasonFrom="+monthBefore+"&seasonTo="+startDate+"&tournament=runkosarja&dataType=shots"
    response = requests.get(url_shots)
    print("Team shots", response.status_code)
    data_shots = json.loads(response.text)
    
    df_shots = pd.DataFrame(data_shots)
    print(df_shots)
    result = pd.concat([df_stand.set_index('teamId'), df_shots.set_index('teamId')], axis=1).reset_index()
    
    #remove duplicates
    result = result.loc[:,~result.columns.duplicated()]
    return result
    
def correct_name(name):
    correct = ''
    for letter in name:
            if letter =='ä':
                correct += 'a'
            else:
                correct += letter
    return correct

def build_games(games):
    list = []
    for game in games:
        fintype=game['finishedType']
        
        if fintype == "ENDED_DURING_REGULAR_GAME_TIME":
            Hg = game['homeTeam']['goals']
            Ag = game['awayTeam']['goals']
        else:
            if game['awayTeam']['goals'] > game['homeTeam']['goals']:
                Ag, Hg = game['homeTeam']['goals'], game['homeTeam']['goals']
            else:
                Ag, Hg = game['awayTeam']['goals'], game['awayTeam']['goals']

        H_id = game['homeTeam']['teamId'].split(':')[0]
        A_id = game['awayTeam']['teamId'].split(':')[0]

        df = {}
        W = getWinner(fintype, Hg, Ag)

        df['HomeTeam_id'] = H_id
        df['Winner'] = W
        df['AwayTeam'] = A_id
        df['HomeGoals'] = Hg
        df['AwayGoals'] = Ag
        df["gameId"] = game['id']
        
        list.append(df)
    return list

def trim_data(data):
    
    try:
        columns = ["previousGameDayPoints","teamShortName","sortDesc","previousGameDayRanking","previousGameDayShotsPercentage",
        "previousGameDayWins",
        "previousGameDayGoalsFor",
        "previousGameDayGoalsAgainst"]

        df = data.drop(columns=columns)

       
        return df
    except:
        print('exception occurred')

def change_column_name(columns):
    newNames = []
    for col in columns:
        newNames.append('A'+col)

    return newNames

def getWinner(ftype, H, A):
    if ftype == "ENDED_DURING_REGULAR_GAME_TIME":
        if H>A:
            return 'H'
        else:
            return 'A'
    else:
        return 'D'

def get_date():
    today = date.today()
    yesterday = today - datetime.timedelta(days=1)
    return today,yesterday

def game_date(game):
    # Convert string to datetime object
    original_date = datetime.fromisoformat(game['start'].replace("Z", "+00:00"))

    # Subtract one day
    new_date = original_date - timedelta(days=1)


    # Format the new date as a string
    new_date_string = new_date.strftime("%Y-%m-%dT%H:%M:%SZ")


    date = new_date_string.split('T')[0]


    return date 

def month_before(date_string):
    original_date = datetime.strptime(date_string, "%Y-%m-%d")

    # Calculate the previous month
    previous_month = original_date - timedelta(days=30)

    # Format the previous month as a string
    monthBefore = previous_month.strftime("%Y-%m-%d")

    return monthBefore

    
def create_result_frame(my_df):
    try:
        if os.path.exists('Liiga/data/testCSV.csv'):
            print('toimii')
            file = pd.read_csv('Liiga/data/testCSV.csv')
            
            
            res_df = pd.concat([file, my_df], ignore_index=True)
            
            res_df.to_csv('Liiga/data/testCSV.csv', index=False)
        else:
            my_df.to_csv('Liiga/data/testCSV.csv')
    except:
        print('Error in create resultframe')

def main():
    master_list = {}
    data = read_games()
  
    for game in data:
            
        gameDate = game_date(game)
                
        if gameDate not in master_list.keys():
            master_list[gameDate] = [game]
        else:
            master_list[gameDate].append(game)
       

    for key in master_list.keys():
        #Get team stats for game day
        print(key)
        startDate = key
        monthBefore = month_before(key)
        print(monthBefore)
        
        data = get_team_data_by_date(startDate, monthBefore)
        #print(data)
        data = trim_data(data)
        
        games = master_list[key]
        #print(games[0])
        matches = build_games(games)
        

        for match in matches:
            H_id = int(match['HomeTeam_id'])
            A_id = int(match["AwayTeam"])
            print(H_id)
            maskHome = data['teamId'].isin([H_id])
            Home = data[maskHome]
            
            Home['gameId'] = match['gameId']
            
            maskAway = data['teamId'].isin([A_id])
            Away = data[maskAway]
            Away.columns = ['A' + col for col in Away.columns]
            Away['gameId'] = match["gameId"]
            Home = Home.set_index("gameId")
            Away = Away.set_index("gameId")
            
            
            df_match = pd.DataFrame([match])
            df_match = df_match.set_index("gameId")
            
            df = pd.concat([df_match,Home,Away], axis=1)
            create_result_frame(df)
        

main()