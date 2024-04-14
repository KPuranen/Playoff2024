import requests
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
import joblib
import random


COLUMNS = []

def drop_unused_columns(file):
  columns = ["expectedPoints", "last5Results","previousGameDayGoals", "previousGameDayShots","gameId",
  "AexpectedPoints", "Alast5Results","ApreviousGameDayGoals", "ApreviousGameDayShots",
  "HomeGoals", "AwayGoals", "teamId", "teamName", "HomeTeam_id", "AwayTeam", "Winner", "AteamName", "AteamId","AshotsPercentagePenaltyKill"]
  df = file.drop(columns=columns)
  

  return df

def fit_model():
  file = pd.read_csv('Liiga/data/testCSV.csv')
  # Split the data into training and testing sets
  X = drop_unused_columns(file)
  for col in X.columns:
    COLUMNS.append(col)
    
  y = file["Winner"]
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

  # Create a random forest classifier

  clf = RandomForestClassifier()
  clf.fit(X_train, y_train)

  # Train the classifier on the training data
  
 # y_test_pred = clf.predict(X_test)
  joblib.dump(clf, "my_model")
  
  #my_model = joblib.load("my_model")

def get_data():
  url_standings = "https://www.liiga.fi/api/v2/teams/stats?seasonFrom=2024-02-14&seasonTo=2024-03-14&tournament=runkosarja&dataType=standings"
  res = requests.get(url_standings)
  data = json.loads(res.text)
  df_stand = pd.DataFrame(data)
  
  url_shots = "https://www.liiga.fi/api/v2/teams/stats?seasonFrom=2024-02-14&seasonTo=2024-03-14&tournament=runkosarja&dataType=shots"
  response = requests.get(url_shots)
  data_shots = json.loads(response.text)
  df_shots = pd.DataFrame(data_shots)
  
  result = pd.concat([df_stand.set_index('teamId'), df_shots.set_index('teamId')], axis=1)
  
  #swap ranking
  url_ranking = "https://www.liiga.fi/api/v2/standings/?season=2024"
  response = requests.get(url_ranking)
  rankings = json.loads(response.text)

  df2 = pd.DataFrame(rankings['season'])
  
  # Create a dictionary mapping internalId to new_ranking values
  ranking_map = dict(zip(df2['internalId'], df2['ranking']))

  result.reset_index(inplace=True)
  result['ranking'] = result['teamId'].map(ranking_map)
  result.set_index('teamId', inplace=True)
  
  #remove duplicates
  result = result.loc[:,~result.columns.duplicated()]
  return result
  
def trim_data(data):
  
  columns = ["previousGameDayPoints","teamShortName","sortDesc","previousGameDayRanking","previousGameDayShotsPercentage",
  "previousGameDayWins",
  "previousGameDayGoalsFor",
  "previousGameDayGoalsAgainst","expectedPoints", "last5Results","previousGameDayGoals", "previousGameDayShots"]

  df = data.drop(columns=columns)

  
  return df

def build_gameframe(df_home,df_away):
  df_away.columns = ['A' + col for col in df_away.columns]
  df1 = df_home.reset_index(drop=True)
  df2 = df_away.reset_index(drop=True)
  df = df1.join(df2)
  
  df.drop(columns=["AteamName","teamName","AshotsPercentagePenaltyKill"], inplace=True)
  df = df[COLUMNS]
  return df

def set_winners(pred, winners, Home, Away):
  if pred == "H":
    if Home not in list(winners.keys()):
      winners[Home] = 1
    else:
      winners[Home] += 1  
  elif pred == "A":
    if Away not in list(winners.keys()):
      winners[Away] = 1
    else:
      winners[Away] += 1 
  else:
    return
def check_winners(dict, up_to):
  for key in dict.keys():
    if dict[key] == up_to:
      return key
    else:
      return False
    
def play_pair(df1, df2, play_up_to):
  model = joblib.load("my_model")

  winners = {}
  org_cols1 = df1.columns.tolist()
  org_cols2 = df2.columns.tolist()
  i=1
  df1 = df1.reset_index()
  df2 = df2.reset_index()
  options = ["A", "D", "H"]
  while True:

    
    #Kotietu
    if i % 2 != 0:

      Home = int(df1["teamId"])
      Away = int(df2["teamId"])
      game = build_gameframe(df1[org_cols1],df2[org_cols2])

      proba = model.predict_proba(game)
      
      pred = np.random.choice(options, p=proba[0])
      
      set_winners(pred, winners, Home, Away)
      
    
    #vieraspeli
    else:
      Away = int(df1["teamId"])
      Home = int(df2["teamId"])
     
      game = build_gameframe(df2[org_cols2],df1[org_cols1])
      proba = model.predict_proba(game)
      pred = np.random.choice(options, p=proba[0])
      

      set_winners(pred, winners, Home, Away)
    i = i +1
    winner = check_winners(winners, play_up_to)
    if winner:
      return winner
    
def play_säälit(data):
  
  wins = []
  teams = [859884935,626537494,624554857,651304385]
  
  filtered_df = data[data.index.isin(teams)]
  sorted_df = filtered_df.sort_values(by='ranking')
  

  df1 = sorted_df.iloc[[0]]
  df2 = sorted_df.iloc[[1]]
  df3 = sorted_df.iloc[[2]]
  df4 = sorted_df.iloc[[3]]

  wins.append(play_pair(df1, df4, 2))
  wins.append(play_pair(df2,df3, 2))
  return wins

def play_quarters(data, quarters):
  
  wins = []
  teams = [362185137,951626834,875886777,495643563,292293444,168761288]
  for i in quarters:
    teams.append(i)
  
  filtered_df = data[data.index.isin(teams)]
  sorted_df = filtered_df.sort_values(by='ranking')
  
  df1 = sorted_df.iloc[[0]]
  df2 = sorted_df.iloc[[1]]
  df3 = sorted_df.iloc[[2]]
  df4 = sorted_df.iloc[[3]]
  df5 = sorted_df.iloc[[4]]
  df6 = sorted_df.iloc[[5]]
  df7 = sorted_df.iloc[[6]]
  df8 = sorted_df.iloc[[7]]
  
  wins.append(play_pair(df1, df8, 4))
  wins.append(play_pair(df2,df7, 4))
  wins.append(play_pair(df3, df6, 4))
  wins.append(play_pair(df4,df5, 4))

  return wins

def play_semis(data, teams):
  
  wins = []
  
  filtered_df = data[data.index.isin(teams)]
  sorted_df = filtered_df.sort_values(by='ranking')
  
  df1 = sorted_df.iloc[[0]]
  df2 = sorted_df.iloc[[1]]
  df3 = sorted_df.iloc[[2]]
  df4 = sorted_df.iloc[[3]]

  
  wins.append(play_pair(df1, df4, 4))
  wins.append(play_pair(df2,df3, 4))

  return wins

def play_final(data, teams):
  
  filtered_df = data[data.index.isin(teams)]
  sorted_df = filtered_df.sort_values(by='ranking')
  
  df1 = sorted_df.iloc[[0]]
  df2 = sorted_df.iloc[[1]]

  winner = play_pair(df1, df2, 4)
  
  return winner

def main():
  fit_model()
  winners = {}
  data = get_data()
  data = trim_data(data)
  
  #Sm liiga playoff logiikka
  #Paras seitsemästä, Parempi ranking aloittaa kotona, suurin ranking vastaan pienin ranking
  #Pidä kirjaa mikä joukkue etenee seuraavaan vaiheeseen ehkä sort by ranking tai jotain
  for i in range(500):
    to_quarters = play_säälit(data)
    print("SÄÄLI VOITTAJAT", to_quarters)
    to_semis = play_quarters(data, to_quarters)
    print("SEMEIHIN: ", to_semis)
    
    to_finals = play_semis(data, to_semis)
    print("FINAALEIHIN: ", to_finals)
    winner = play_final(data, to_finals)
    
    print("VOITTAJA:", winner)
    #Please be Ilves
    
    if winner not in winners.keys():
      winners[winner] = 1
    else:
      winners[winner] += 1
      
  print(winners)
    
main()