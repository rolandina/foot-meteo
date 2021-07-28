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

#parameters
plot_title_font_size = 20

st.set_page_config(page_title="meteo-foot", layout='wide', initial_sidebar_state='auto')

@st.cache()
def get_data():
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

    match_meteo = pd.read_sql_query(f"""
    SELECT *
    FROM matches
    ;""", conn)

    match_meteo["is_rain"] = [True if mm>1 else False for mm in match_meteo['rainfall']]


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
    
    # prepare data Nina


    player_meteo = data2.copy()
    player_meteo = player_meteo.rename(columns = {"match_id": "id"})
    player_meteo = player_meteo.drop(['buts'], axis = 1)
    player_meteo["player-club"] = player_meteo.last_name + ': ' + player_meteo.city
    player_meteo["is_rain"] = [True if mm>1 else False for mm in player_meteo['rainfall']]

    df1 = player_meteo[['temperature', 'is_rain', 'id', 'last_name']].groupby(by = ['temperature', 'is_rain', 'id'], as_index= False).count()
    df1 = df1.rename(columns = {"last_name": "number_goals_per_match"})

    no_rain = df1[df1.is_rain == False]
    rain = df1[df1.is_rain == True]
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

    return data, data2,  df_score_player_match, player_meteo, match_meteo, rain, no_rain, rain2, no_rain2 


data, data2, df_score_player_match, player_meteo, match_meteo, rain, no_rain, rain2, no_rain2  = get_data()



# VIZ function 
def team_bar_meteo(team):

    """Function team_bar_meteo(team) plots number of goals by temperature and rainfall for a team
    Parameters: team - data frame
    Return: fig
    """
    fig, ax = plt.subplots(1, 2, figsize=(20,8))
    sns.barplot(data=data[data['city'] == team], x='temperature', y='team_goal', ax=ax[0])
    sns.barplot(data=data[data['city'] == team], x='rainfall', y='team_goal', ax=ax[1])
    #plt.suptitle(f'Distributions des buts de {team}', fontsize = 30, fontweight = 'bold')
    ax[0].set_title(f"Nb de buts en fonction de la temperature", fontsize = plot_title_font_size, fontweight = 'bold')
    ax[1].set_title(f"Nb de buts en fonction de la pluviométrie", fontsize = plot_title_font_size, fontweight = 'bold')
    return fig
    
def player_bar_meteo(player):

    """Function player_bar_meteo(player) plots number of goals by temperature and rainfall for a player
    Parameters: player - data frame
    Return: fig
    """
    fig, ax = plt.subplots(1, 2, figsize=(20,8))
    sns.barplot(data=df_score_player_match[df_score_player_match['last_name'] == player], x='temperature', y='buts', ax=ax[0])
    sns.barplot(data=df_score_player_match[df_score_player_match['last_name'] == player], x='rainfall', y='buts', ax=ax[1])
    #plt.suptitle(f'Distributions des buts de {player}', fontsize = 30, fontweight = 'bold')
    ax[0].set_title(f"Nb de buts en fonction de la temperature", fontsize = plot_title_font_size, fontweight = 'bold')
    ax[1].set_title(f"Nb de buts en fonction de la pluviométrie", fontsize = plot_title_font_size, fontweight = 'bold')
    return fig

# title
st.markdown("<h1 style='text-align: center; color: red;'> Etude du nombre de buts en fonction de la météo </h1>",  unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<h3 style='text-align: center;'>

<strong>Objectif et mise en situation: </strong> Jean-Michel à une idée lumineuse: Il est persuadé que lorsqu’il fait beau les matchs de foot sont plus intéressants que lorsque le temps est mauvais. Il souhaite vendre des espaces publicitaires dans le stades à des sponsors et faire varier le prix en fonction de la météo. Mais pour cela il a besoin d’illustrer son propos. C’est pour cela qu’il vient à vous. Il souhaite avoir au minimum deux représentations visuelles:

<ul>
    <li>l’évolution du nombre de buts d’une équipe en fonction de la météo (pluviométrie, température)</li>
    <li>l’évolution du nombre de buts d’un joueur en fonction de la météo (pluviométrie, température)</li>
</ul>

Il est ouvert à toutes propositions permettant d’illustrer au mieux la relation entre météo et le dynamisme d’un match.

</h3>
""",  unsafe_allow_html=True)

page = st.sidebar.radio("Outline:", ("Distributions du nombre de buts par equipe", 
"Distributions du nombre de buts par joueur",
  "Distributions du nombre de buts total en fonction de la météo",
   "Distribution du nombre de buts moyen par match en fonction de la temperature",
     "Conclusion"))

if page == "Distributions du nombre de buts par equipe":

    # plot 1
    st.markdown("---")
    st.markdown(f"<h2 style='text-align: center;'> <b> Distributions du nombre de buts par equipe </b> </h2>", unsafe_allow_html=True)
    empty, col1 = st.beta_columns([3,1])
    with col1:
        selected_team = st.selectbox("Choose a team:", tuple(data['city'].unique()))
    st.markdown(f"<h3 style='text-align: center;'>Distributions des buts de {selected_team} </h3>", unsafe_allow_html=True)
    st.pyplot(team_bar_meteo(selected_team))


# Nina VIZ

def plot_player_goals_meteo(player):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    df = player_meteo[player_meteo['player-club']==player]
    sns.scatterplot(data = df, 
                    x = 'rainfall', 
                    y= 'temperature',  s = 80,
                    alpha = 0.9)
    return fig


number_goals_by_player = player_meteo[['player-club', 'temperature']].groupby(by='player-club', as_index=False).count()
number_goals_by_player = number_goals_by_player.sort_values(by= 'temperature', ascending = False)
players_list = number_goals_by_player['player-club'].values

if page == "Distributions du nombre de buts par joueur":
# plot 2
    st.markdown("---")
    st.markdown(f"<h2 style='text-align: center;'> <b> Distributions du nombre de buts par joueur </b> </h2>", unsafe_allow_html=True)
    empty, col1 = st.beta_columns([3,1])
    with col1:
        selected_player = st.selectbox("Choose a player:", tuple(data2['last_name'].unique()))
    st.markdown(f"<h3 style='text-align: center;'>Distributions des buts de {selected_player} </h3>", unsafe_allow_html=True)
    st.pyplot(player_bar_meteo(selected_player))



# plot 3
#value = players_list[0]


    empty, col1 = st.beta_columns([3,1])
    with col1:
        selected_player2 = st.selectbox("Choose a player:", tuple(players_list))

    st.markdown("---")
    st.markdown(f"""
    <h3 style='text-align: center;'>Distributions des buts de {selected_player2} </h3>
    <br>
    """, unsafe_allow_html=True)
    empty1, col, empty2 = st.beta_columns([1,2,1])
    with col:
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

    #plt.suptitle(f'Distributions du nombre de buts totals en function de la météo', fontsize = 30, fontweight = 'bold')

    ax[0].set_title(f"Total nombre de buts par pluviométrie",
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    ax[1].set_title(f"Total nombre de buts par temperature",
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    return fig

def plot_total_goals_number_by_meteo(player_meteo):
    fig, ax = plt.subplots(2, 1, figsize=(10, 16))
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
    ax[0].set_title(f"Total du nombre de buts par température",
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    ax[1].set_title(f"Total du nombre de match par température",
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    return fig


if page == "Distributions du nombre de buts total en fonction de la météo":
# plot 4
    st.markdown(f"""
    <h2 style='text-align: center;'> <b> Distributions du nombre de buts total en fonction de la météo </b> </h2>
    
    """, unsafe_allow_html=True)
    empt1, col, empt2 = st.beta_columns([1,2,1])
    with col:   
        st.pyplot(plot_total_goals_number_by_meteo(player_meteo))

#assuption is_rain = true si le plue > 1mm et faux si non


# Evolution du nombre de buts moyen par mathc en fonction de la temperature

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

df_no_rain2 = regroup_by_temperature(no_rain2, "cut_temperature")
df_rain2 = regroup_by_temperature(rain2, "cut_temperature")


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
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    ax[1].legend()
    ax[1].set_title(f"Residuals plot du nombre de buts moyen par match \n en fonction de la {feature}",
                    fontsize=plot_title_font_size,
                    fontweight='bold')
    #plt.suptitle(f'Distribution du nombre de buts moyen par match en fonction de la {feature}  ', fontsize = 30, fontweight = 'bold')
    return fig

# plot 6
if page == "Distribution du nombre de buts moyen par match en fonction de la temperature":
    st.markdown(f"<h2 style='text-align: center;'> <b> Distribution du nombre de buts moyen par match en fonction de la temperature </b> </h2>", unsafe_allow_html=True)
    st.pyplot(plot_mean_goals_per_match_per_temperature(df_rain, df_no_rain))


    # plot 7
    st.markdown("---")
    st.markdown(f"<h2 style='text-align: center;'> <b> Distribution du nombre de buts moyen par match en fonction de la temperature bins </b> </h2>", unsafe_allow_html=True)
    st.pyplot(plot_mean_goals_per_match_per_temperature(df_rain2, df_no_rain2, 'cut_temperature'))


if page == "Conclusion":
    conclusion = st.button('Conclusion')
    if conclusion:

        st.markdown("""
        <h2>Conclusion</h2>
        <p>Avec tout le respect que l'on vous doit, cher Jean Michel, il semblerait qu'il n'y ait pas, voir très peu de corrélation entre le nombre de buts marqués par joueur ou par équipe et la météo en ligue 1.</p>
        """, unsafe_allow_html=True)
        st.balloons()