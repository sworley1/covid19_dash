# File Name: Dashboard.py

# Description:

# ------------
# imports
# -----------
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output

# ----------
# read data
# ---------
def read_and_clean():
    '''
    Reads in data from .csv file and then cleans it
    '''
    df = pd.read_csv("data.csv", dtype={"FIPS":str})
    df.drop(columns=["Unnamed: 0"], inplace=True)

    # Filter for US Data only
    us_filter = df['Country_Region'] == 'US'
    df = df[us_filter]

    # Filter out weird 'Recovered US' in combined key
    rec_us = df['Combined_Key'] != 'Recovered, US'
    df = df[rec_us]

    return df

# --------
# generate input fields
# -------
def get_input_fields(df):
    '''
    Generates input field options
    '''
    scope_options = list( df["Province_State"].unique() )
    scope_options.append('All U.S.') 

    value_options = [{'label':'Confirmed Cases', 'value':'Confirmed'},
                 {'label':'Active Cases', 'value':'Active'},
                 {'label':'Recoveries', 'value':'Recovered'},
                 {'label':'Deaths', 'value':'Deaths'}]

    

    return [ scope_options, value_options ]

def filters(df, *args):
    '''
    Working on filtering data by state, county, date
    '''
    for arg in args:
        for key, value in arg.items():
            if value not in ['All', 'All U.S.']:
                filters = df[key] == value
                df = df[filters]

    return df


# ----------------
# main
# ---------------

# -----
# get counties
# ----
from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

app = dash.Dash()
df = read_and_clean()

df = df[df['Date']=='11-25-2020']

options = get_input_fields( df )

app.layout = html.Div([ 
                        html.Div([
                                    html.H1('COVID-19 Dashboard'),
                                    html.H3('Data From John Hopkins University.')
                                ], style = {'text-align':'center', 'width':'100%','height':'125px', 'background-color':'#63A088'}),

                        html.Div([
                            html.Label(['Region'], style={'margin':'50px'}),
                            dcc.Dropdown(id='scope-input',
                                        options=[{'label':i, 'value':i} for i in options[0]],
                                        value='All U.S.' )

                            ], style={'width':'50%', 'display':'inline-block'}),

                        html.Div([
                            html.Label(['Value Type:'], style={'margin':'50px'}),
                            dcc.Dropdown(id='z-input',
                                        options=options[1],
                                        value='Confirmed')
                            ], style = {'width':'50%', 'display':'inline-block'}),

                        html.Div([
                            dcc.Graph( id='heatmap')],
                            style={'height':'610px',
                                'display':'inline',
                                'background-color':'#09BA4B'})

                               

                        

                            ], style={"background-color":"#FFFCF7", 'text-align':'center'})

@app.callback( Output('heatmap', 'figure'),
               [Input('scope-input', 'value'),
                Input('z-input', 'value')
                ])
def update_graph(scope, z):
    # need to put date in here
    current = filters( {'Province_State':scope, 'Date':'11-25-2020'} )
    current = df
    fig = px.choropleth( current, 
                         geojson=counties,
                         locations='FIPS',
                         color=z,
                         #scope='usa'
                       )
    fig.update_geos(fitbounds='locations', visible=False)
    fig.update_layout(geo=dict(scope='usa'))

    return fig
                   

if __name__ == '__main__':
    app.run_server()
