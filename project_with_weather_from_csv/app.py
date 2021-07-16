import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import psycopg2 as pg
import streamlit as st

# 1. GET AND PREPARE DATA
#Connexion to db with data
conn = pg.connect(dbname='d18d5k6eqpagnc',
                  user='qshqwgcxyldiib',
                  host='ec2-54-74-14-109.eu-west-1.compute.amazonaws.com',
                  password = '726d500b6531d0c8fb04410eb021d11ccccb5f369efa9cb7045538a1f56a8faa')
cursor = conn.cursor()


#create DF wuth matches data
data = pd.read_sql(f"""
SELECT t.city, mt.team_goal, m.temperature, m.rainfall
FROM matches_teams AS mt
JOIN matches as m
ON m.id = mt.match_id
JOIN teams as t
ON mt.team_id = t.id
;""", conn)

#create DF with goals per player data
data2 = pd.read_sql(f"""
SELECT g.match_id, p.last_name, t.city, m.temperature, m.rainfall
FROM goals AS g
JOIN players as p
ON p.id = g.player_id
JOIN matches as m
ON g.match_id = m.id
join teams as t
ON p.team_id = t.id
;""", conn)

## Michael VIZ
data2['buts'] = 1
df_total_but = data2[['city','temperature','rainfall', 'buts']].groupby(data2['match_id']).sum()
df_score_player_match = pd.DataFrame()

for i in range(data2['match_id'].min(), data2['match_id'].max()+1):
    
    new_df = pd.DataFrame(data2['buts'][data2['match_id'] == i].groupby(
        data2['last_name']).sum()).reset_index().assign(
        temperature=data2['temperature'][data2['match_id'] == i].mean()).assign(
        rainfall=data2['rainfall'][data2['match_id'] == i].mean()).assign(
        match_id=i)
    
    df_score_player_match = df_score_player_match.append(new_df, ignore_index=True)


df_score_player_match['buts'].groupby(df_score_player_match['last_name']).sum().sort_values(ascending = False)

# VIZ function 
def team_bar_meteo(team):

    """Function team_bar_meteo(team) plots number of goals by temperature and rainfall for a team
    Parameters: team - data frame
    Return: fig
    """
    fig, ax = plt.subplots(1, 2, figsize=(20,8))
    sns.barplot(data=data[data['city'] == team], x='temperature', y='team_goal', ax=ax[0])
    sns.barplot(data=data[data['city'] == team], x='rainfall', y='team_goal', ax=ax[1])
    plt.suptitle(f'Distributions des buts de {team}', fontsize = 30, fontweight = 'bold')
    ax[0].set_title(f"Nb de buts en fonction de la temperature", fontsize = 14, fontweight = 'bold')
    ax[1].set_title(f"Nb de buts en fonction de la pluviométrie", fontsize = 14, fontweight = 'bold')
    return fig
    
def player_bar_meteo(player):

    """Function player_bar_meteo(player) plots number of goals by temperature and rainfall for a player
    Parameters: player - data frame
    Return: fig
    """
    fig, ax = plt.subplots(1, 2, figsize=(20,8))
    sns.barplot(data=df_score_player_match[df_score_player_match['last_name'] == player], x='temperature', y='buts', ax=ax[0])
    sns.barplot(data=df_score_player_match[df_score_player_match['last_name'] == player], x='rainfall', y='buts', ax=ax[1])
    plt.suptitle(f'Distributions des buts de {player}', fontsize = 30, fontweight = 'bold')
    ax[0].set_title(f"Nb de buts en fonction de la temperature", fontsize = 14, fontweight = 'bold')
    ax[1].set_title(f"Nb de buts en fonction de la pluviométrie", fontsize = 14, fontweight = 'bold')
    return fig

# plot 1
selected_team = st.selectbox("Choose a team:", tuple(data['city'].unique()))
st.pyplot(team_bar_meteo(selected_team))

# plot 2
selected_player = st.selectbox("Choose a player:", tuple(data2['last_name'].unique()))
st.pyplot(player_bar_meteo(selected_player))



# Nina VIZ
# prepare data

player_meteo = data2.copy()
player_meteo = player_meteo.rename(columns = {"match_id": "id"})
player_meteo = player_meteo.drop(['buts'], axis = 1)
player_meteo["player-club"] = player_meteo.last_name + ': ' + player_meteo.city
player_meteo["is_rain"] = [True if mm>1 else False for mm in player_meteo['rainfall']]


def plot_player_goals_meteo(player):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    df = player_meteo[player_meteo['player-club']==player]
    sns.scatterplot(data = df, 
                    x = 'rainfall', 
                    y= 'temperature',  
                    alpha = 0.9)
    return fig


number_goals_by_player = player_meteo[['player-club', 'temperature']].groupby(by='player-club', as_index=False).count()
number_goals_by_player = number_goals_by_player.sort_values(by= 'temperature', ascending = False)
players_list = number_goals_by_player['player-club'].values

# plot 3
#value = players_list[0]
selected_player2 = st.selectbox("Choose a player:", tuple(players_list))
st.pyplot(plot_player_goals_meteo(selected_player2))


def plot_total_goals_number_by_meteo(player_meteo):

    # total numbre de buts par pluvoimetrie
    fig, ax = plt.subplots(1, 2, figsize=(20, 8))
    sns.histplot(data = player_meteo, 
                    x = 'rainfall',  
                    alpha = 0.9, ax = ax[0])
    # totlal numbre de buts par temperature
    sns.histplot(data = player_meteo, 
                    x = 'temperature',  
                    alpha = 0.9,
                ax = ax[1])

    plt.suptitle(f'Distributions du nombre de buts total en function de la météo', fontsize = 30, fontweight = 'bold')

    ax[0].set_title(f"Total nombre de buts par pluviométrie",
                    fontsize=14,
                    fontweight='bold')
    ax[1].set_title(f"Total nombre de buts par temperature",
                    fontsize=14,
                    fontweight='bold')
    return fig

st.pyplot(plot_total_goals_number_by_meteo(player_meteo))


#assuption is_rain = true si le plue > 1mm et faux si non
match_meteo = pd.read_sql_query(f"""
    SELECT *
    FROM matches
    ;""", conn)

match_meteo["is_rain"] = [True if mm>1 else False for mm in match_meteo['rainfall']]



fig, ax = plt.subplots(2, 1, figsize=(10, 10))
sns.histplot(data=player_meteo,
             x='temperature',
             hue='is_rain',
             bins=20,
             multiple="stack",
             alpha=0.9,
             ax=ax[0])
sns.histplot(data=match_meteo,
             x='temperature',
             bins=20,
             hue='is_rain',
             multiple="stack",
             alpha=0.9,
             ax=ax[1])
ax[0].set_title(f"Total nombre de buts par témpérature",
                fontsize=14,
                fontweight='bold')
ax[1].set_title(f"Total nombre de match par témpérature",
                fontsize=14,
                fontweight='bold')

st.pyplot(fig)

# Evolution du nombre de buts moyen par mathc en fonction de la temperature


df1 = player_meteo[['temperature', 'is_rain', 'id', 'last_name']].groupby(by = ['temperature', 'is_rain', 'id'], as_index= False).count()
df1 = df1.rename(columns = {"last_name": "number_goals_per_match"})

no_rain = df1[df1.is_rain == False]
rain = df1[df1.is_rain == True]

def regroup_by_temperature(df0, g='temperature'):
    """This function return data frame groupped by temperature
    Parameters: df0 - data frame
    Return: df - data frame.
    """
    df = df0[[g, 'number_goals_per_match']].groupby(by = g, as_index= False).sum()
    df = df.rename(columns = {"number_goals_per_match": "total_goals"})
    df['num_match'] = df0[[g, 'id']].groupby(by = g, as_index= False).count()["id"]
    df['mean_goals_per_match'] = df['total_goals']/df['num_match']
    return df


df_rain = regroup_by_temperature(rain)
df_no_rain = regroup_by_temperature(no_rain)


def plot_mean_goals_per_match_per_temperature(df_rain, df_no_rain, feature = 'temperature'):
    fig, ax = plt.subplots(1, 2, figsize=(20, 9))

    sns.regplot(data=df_rain,
                x=feature,
                y='mean_goals_per_match',
                 scatter_kws = {'lw': 5},
                  line_kws = {'lw':5},
                label='Rain',
                ax=ax[0])
    sns.regplot(data=df_no_rain,
                x=feature,
                y='mean_goals_per_match',
                 scatter_kws = {'lw': 5},
                  line_kws = {'lw':5},
                label='No rain',
                ax=ax[0])


    sns.residplot(data=df_rain,
                  x=feature,
                  y='mean_goals_per_match',
                  scatter_kws = {'lw': 5},
                  line_kws = {'lw':5},
                  label='Rain',
                  ax=ax[1])
    sns.residplot(data=df_no_rain,
                  x=feature,
                  y='mean_goals_per_match',
                  label='No rain',
                  scatter_kws = {'lw': 5},
                  ax=ax[1])

    ax[0].legend()
    ax[0].set_title(f"Plot du nombre de buts moyen par match \n en fonction de la {feature}",
                    fontsize=14,
                    fontweight='bold')
    ax[1].legend()
    ax[1].set_title(f"Residuals plot du nombre de buts moyen par match \n en fonction de la {feature}",
                    fontsize=14,
                    fontweight='bold')
    plt.suptitle(f'Distribution du nombre de buts moyen par match en fonction de la {feature}  ', fontsize = 30, fontweight = 'bold')
    return fig

# plot 4 
st.pyplot(plot_mean_goals_per_match_per_temperature(df_rain, df_no_rain))


temperature_bins = [-5., 5., 10., 15., 20., 30.]
temperature_labels = [0., 7.5, 12.5, 17.5, 25.]
no_rain2 = no_rain.copy()
rain2 = rain.copy()
no_rain2['cut_temperature'] = pd.cut(no_rain2['temperature'],
                                     bins=temperature_bins,
                                     labels=temperature_labels)
rain2['cut_temperature'] = pd.cut(rain2['temperature'],
                                  bins=temperature_bins,
                                  labels=temperature_labels)
rain2.tail()


df_no_rain2 = regroup_by_temperature(no_rain2, "cut_temperature")
df_rain2 = regroup_by_temperature(rain2, "cut_temperature")

# plot 5
st.pyplot(plot_mean_goals_per_match_per_temperature(df_rain2, df_no_rain2, 'cut_temperature'))