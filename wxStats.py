#!/usr/bin/python3.7
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_auth
import plotly.express as px
import pandas as pd
import datetime
import sqlite3
import numpy as np
from weatherStats import PlotStep, CalcType, WeatherPlotter, DataCalculation, WeatherPlotThread
from calendar import monthrange
import math, time
from queue import Queue
#from users import VALID_USERNAME_PASSWORD_PAIRS # uncomment to enable simple user authentication

def capitalizeFirst(strIn):
    return strIn[0].upper() + strIn[1:]

def get_current_weather():
    weatherPlot.getCurrentWeather()

    # Convert wind direction to cardinal direction
    windDir = weatherPlot.currentConditions['wind']['dir']
    if (windDir == None):
        windDir = '--'
    elif (windDir > 0 and (windDir <= 11.25 or windDir > 348.75)):
        windDir = "N"
    elif (windDir > 11.25 and windDir <= 33.75):
        windDir = "NNE"
    elif (windDir > 33.75 and windDir <= 56.25):
        windDir = "NE"
    elif (windDir > 56.25 and windDir <= 78.75):
        windDir = "ENE"
    elif (windDir > 78.75 and windDir <= 101.25):
        windDir = "E"
    elif (windDir > 101.25 and windDir <= 123.75):
        windDir = "ESE"
    elif (windDir > 123.75 and windDir <= 146.25):
        windDir = "SE"
    elif (windDir > 146.25 and windDir <= 168.75):
        windDir = "SSE"
    elif (windDir > 168.75 and windDir <= 191.25):
        windDir = "S"
    elif (windDir > 191.25 and windDir <= 213.75):
        windDir = "SSW"
    elif (windDir > 213.75 and windDir <= 236.25):
        windDir = "SW"
    elif (windDir > 236.25 and windDir <= 258.75):
        windDir = "WSW"
    elif (windDir > 258.75 and windDir <= 281.25):
        windDir = "W"
    elif (windDir > 281.25 and windDir <= 303.75):
        windDir = "WNW"
    elif (windDir > 303.75 and windDir <= 326.25):
        windDir = "NW"
    elif (windDir > 326.25 and windDir <= 191.25):
        windDir = "NNW"

    
    return ["{} {}".format(weatherPlot.currentConditions['time'].strftime("%Y-%m-%d %H:%M:%S"), time.tzname[time.daylight]), 
        "{:.1f} {}F".format(weatherPlot.currentConditions['outTemp']['current'], u'\N{DEGREE SIGN}'),
        "{}%".format(int(weatherPlot.currentConditions['humidity'])),
        "{:.2f} in".format(weatherPlot.currentConditions['rain']['sum']),
        "{:.2f} in/hr".format(weatherPlot.currentConditions['rain']['rainRate']),
        "{:.1f} mph".format(weatherPlot.currentConditions['wind']['speed']),
        "{}".format(windDir),
        "{:.1f} mph".format(weatherPlot.currentConditions['wind']['gust'])
    ]

def get_graph_data(graphData):

        if (graphData == None):
            return {}
        
        if (graphData['type'] == 'tempPlot'):
            df = pd.DataFrame({
                "dates": graphData['dates'],
                graphData['data_type']: graphData['data'],
                "types": graphData['types']})
            title = "Temperature Summary Plot - {} - {} to {}".format(graphData['plotStep'].name.capitalize(), startTime.strftime("%Y-%m-%d %H:%M"), endTime.strftime("%Y-%m-%d %H:%M"))
            fig = px.scatter(df, x="dates", y=graphData['data_type'], color="types", title=title)
        
        else: # standard
            df = pd.DataFrame({
                "dates": graphData['dates'],
                graphData['data_type']: graphData['data']})
            title = "{} of {} - {} - {} to {}".format(graphData['calcType'].name.capitalize(), capitalizeFirst(graphData['data_type']), graphData['plotStep'].name.capitalize(), graphData['startTime'].strftime("%Y-%m-%d %H:%M"), graphData['endTime'].strftime("%Y-%m-%d %H:%M"))
            fig = px.scatter(df, x="dates", y=graphData['data_type'], title=title)

        return fig

# Weather plotter
path = "/home/weewx/archive/weewx.sdb" 
units = {"outTemp": "deg F", "rain": "in", "rainRate": "in/hr"}
weatherPlot = WeatherPlotter(path, units)

inQueue = Queue()
outQueue = Queue() 
#weatherPlotThread = WeatherPlotThread(weatherPlot, inQueue, outQueue)
#weatherPlotThread.start()

app = dash.Dash(__name__, update_title=None, requests_pathname_prefix='/wx/')

# User authentication
#auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS) # uncomment to enable simple user authentication


#df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/5d1ea79569ed194d432e56108a04d188/raw/a9f9e8076b837d541398e999dcbac2b2826a81f8/gdp-life-exp-2007.csv')

#figOrig = px.scatter(df, x="gdp per capita", y="life expectancy", size="population", color="continent", hover_name="country", log_x=True, size_max=60)
figOrig = {}
endTime = datetime.datetime.now()

# Get current weather
currentConditions = get_current_weather()
startTime = datetime.datetime(endTime.year, endTime.month, endTime.day, 0, 0, 0)
graphData = weatherPlot.getPlotData({'type': "standard", 'data_type': 'outTemp', 'startTime': startTime, 'endTime': endTime, 'plotStep': PlotStep.ALL, 'calcType': CalcType.AVG})
curTempGraph = get_graph_data(graphData)
graphData = weatherPlot.getPlotData({'type': "standard", 'data_type': 'rain', 'startTime': startTime, 'endTime': endTime, 'plotStep': PlotStep.ALL, 'calcType': CalcType.AVG})
curRainGraph = get_graph_data(graphData)
graphData = weatherPlot.getPlotData({'type': "standard", 'data_type': 'windSpeed', 'startTime': startTime, 'endTime': endTime, 'plotStep': PlotStep.ALL, 'calcType': CalcType.AVG})
curWindGraph = get_graph_data(graphData)

# Layout app
app.layout = html.Div(style={'width': '1000px'}, children=[
    html.H1(children='Weather Status'),

    # Current weather
    html.Div([ 
    html.H2(children='Current Weather'),
  
    #html.Div([
    #    html.Div("Last Update Time:  ", style={'flex': '50%'}),
    #    html.Div(id='cur-time-div', children="No data", style={'flex': '50%'})
    #], style={'width': '500px', 'display': 'flex'}),
    html.Div([
        html.Div("Last Update Time:", className='column_label'),
        html.Div(id='cur-time-div', children=currentConditions[0], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Temperature:", className='column_label'),
        html.Div(id='cur-temp-div', children=currentConditions[1], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Humidity:", className='column_label'),
        html.Div(id='cur-hum-div', children=currentConditions[2], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Rain Total:", className='column_label'),
        html.Div(id='cur-rain-tot-div', children=currentConditions[3], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Rain Rate:", className='column_label'),
        html.Div(id='cur-rain-rate-div', children=currentConditions[3], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Wind Speed:", className='column_label'),
        html.Div(id='cur-wind-speed-div', children=currentConditions[4], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Wind Direction:", className='column_label'),
        html.Div(id='cur-wind-dir-div', children=currentConditions[5], className='column_data')
    ], className='row'),
    html.Div([
        html.Div("Wind Gust:", className='column_label'),
        html.Div(id='cur-wind-gust-div', children=currentConditions[6], className='column_data')
    ], className='row'),
    dcc.Interval( # current weather update interval
        id='cur-weather-interval',
        interval=60*1000 # milliseconds
    )
    #]),
    #], style={'width':"100%"}),
    #], style={'display': 'inline-block'}),
    ], style={'width': '1000px'}),
    # Current weather plots
    html.Div([   
        html.H3(children='Current Weather Graphs'),
        dcc.Graph(
            id='cur-temp-graph',
            figure=curTempGraph
        ),
        dcc.Graph(
            id='cur-rain-graph',
            figure=curRainGraph
        ),
        dcc.Graph(
            id='cur-wind-graph',
            figure=curWindGraph
        ),
    ]),
 
    # Custom weather plots
    #html.Br(),
    html.Div([ 
    html.H2(children='Custom Weather Graph'),

    html.Div([
        html.Div("Data Type:", className='column_label'),
        html.Div(children=[
            dcc.Dropdown(
                id='data-type-drop',
                options=[
                    {'label': 'rain', 'value': 'rain'},
                    {'label': 'outTemp', 'value': 'outTemp'}
                ],
                value='rain'
            )], className='column_label')
    ], className='row'),

    #html.Label('Data Type'),
    #dcc.Dropdown(
    #    id='data-type-drop',
    #    options=[
    #        {'label': 'rain', 'value': 'rain'},
    #        {'label': 'outTemp', 'value': 'outTemp'}
    #    ],
    #    value='rain'
    #),
    
    html.Div([
        html.Div("Start Time:", className='column_label'),
        html.Div(children=[
            dcc.Input(
                id='start-time-in',
                value=(endTime - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                type='text'
       )], className='column_label')
    ], className='row'),
    
    html.Div([
        html.Div("End Time:", className='column_label'),
        html.Div(children=[
            dcc.Input(
                id='end-time-in',
                value=endTime.strftime("%Y-%m-%d %H:%M:%S"),
                type='text'
       )], className='column_label')
    ], className='row'),

    html.Div([
        html.Div("Calculation Type:", className='column_label'),
        html.Div(children=[
            dcc.Dropdown(
                id='calc-type-drop',
                options=[
                    {'label': 'MIN', 'value': 'MIN'},
                    {'label': 'MAX', 'value': 'MAX'},
                    {'label': 'AVG', 'value': 'AVG'},
                    {'label': 'SUM', 'value': 'SUM'},
                    {'label': 'STATS', 'value': 'STATS'},
                ],
                value='MIN'
       )], className='column_label')
    ], className='row'),

    html.Div([
        html.Div("Plot Step:", className='column_label'),
        html.Div(children=[
            dcc.Dropdown(
                id='plot-step-drop',
                options=[
                    {'label': 'ALL', 'value': 'ALL'},
                    {'label': 'HOURLY', 'value': 'HOURLY'},
                    {'label': 'DAILY', 'value': 'DAILY'},
                    {'label': 'WEEKLY', 'value': 'WEEKLY'},
                    {'label': 'MONTHLY', 'value': 'MONTHLY'},
                    {'label': 'ANNUALLY', 'value': 'ANNUALLY'},
                ],
                value='ALL'
       )], className='column_label')
    ], className='row'),
   
    html.Button('Generate', id='generate-val', n_clicks=0),
    
    #html.Label('Output'),
    #html.Div(
    #    id='output-div',
    #    children='Never updated'
    #),

    #html.Div(id="graph-update-signal", style={'display': 'none'}),
 
    dcc.Graph(
        id='wx-graph',
        figure=figOrig
    ),

    #dcc.Interval(
    #    id='graph-interval',
    #    interval=5*1000 # milliseconds
    #),

    html.Div(id="dummy-div", style={'display': 'none'})
    #], style={'width':"100%"}),
    ], style={'display': 'inline-block'})

#], style={'columnCount': 1})
])

# Callbacks
#@app.callback([dash.dependencies.Output('cur-time-div', 'children'),
#    dash.dependencies.Output('cur-temp-div', 'children'),
#    dash.dependencies.Output('cur-hum-div', 'children'),
#    dash.dependencies.Output('cur-rain-tot-div', 'children'),
#    dash.dependencies.Output('cur-rain-rate-div', 'children'),
#    dash.dependencies.Output('cur-wind-speed-div', 'children'),
#    dash.dependencies.Output('cur-wind-dir-div', 'children'),
#    dash.dependencies.Output('cur-wind-gust-div', 'children')],
#    dash.dependencies.Input('cur-weather-interval', 'n_intervals'))


#@app.callback(dash.dependencies.Output('wx-graph', 'figure'),
#@app.callback(dash.dependencies.Output('dummy-div2', 'children'),
    #[dash.dependencies.Input('graph-update-signal', 'children')])
#    [dash.dependencies.Input('dummy-div', 'children')])
#    [dash.dependencies.Input('graph-interval', 'n_intervals')])


@app.callback(dash.dependencies.Output('wx-graph', 'figure'),
#@app.callback(dash.dependencies.Output('graph-update-signal', 'children'),
#@app.callback(dash.dependencies.Output('wx-graph', 'figure'),
    [dash.dependencies.Input('generate-val', 'n_clicks')],
    [dash.dependencies.State('data-type-drop', 'value')],
    [dash.dependencies.State('start-time-in', 'value')],
    [dash.dependencies.State('end-time-in', 'value')],
    [dash.dependencies.State('calc-type-drop', 'value')],
    [dash.dependencies.State('plot-step-drop', 'value')])
def update_graph(n_clicks, data_type, start_time, end_time, calc_type, plot_step):
    #global figOrig

    if (n_clicks == 0): # Ignore if button not clicked
        return figOrig
    
    # Get inputs
    startTime = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    endTime = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    plotStep = PlotStep[plot_step]
    calcType = CalcType[calc_type]
            
    #conn = sqlite3.connect(path)
    #dbCursor = conn.cursor()

    if (data_type == 'outTemp' and calcType == CalcType.STATS): # temperature stats plot
        graphData = weatherPlot.getPlotData({'type': "tempPlot", 'data_type': data_type, 'startTime': startTime, 'endTime': endTime, 'plotStep': plotStep})
        #inQueue.put({'type': "tempPlot", 'data_type': data_type, 'startTime': startTime, 'endTime': endTime, 'plotStep': plotStep})
        
        #dates, data, types = createTempPlot(dbCursor, startTime, endTime, plotStep)
        #df = pd.DataFrame({
        #    "dates": dates,
        #    data_type: data,
        #    "types": types})
        #title = "Temperature Summary Plot - {} - {} to {}".format(plotStep.name.capitalize(), startTime.strftime("%Y-%m-%d %H:%M"), endTime.strftime("%Y-%m-%d %H:%M"))
        #fig = px.scatter(df, x="dates", y=data_type, color="types", title=title)
    else:
        graphData = weatherPlot.getPlotData({'type': "standard", 'data_type': data_type, 'startTime': startTime, 'endTime': endTime, 'plotStep': plotStep, 'calcType': calcType})
        #inQueue.put({'type': "standard", 'data_type': data_type, 'startTime': startTime, 'endTime': endTime, 'plotStep': plotStep, 'calcType': calcType})
        #dates, data = getData(dbCursor, data_type, startTime, endTime, plotStep, calcType)
        #df = pd.DataFrame({
        #    "dates": dates,
        #    data_type: data})
        #title = "{} of {} - {} - {} to {}".format(calcType.name.capitalize(), capitalizeFirst(data_type), plotStep.name.capitalize(), startTime.strftime("%Y-%m-%d %H:%M"), endTime.strftime("%Y-%m-%d %H:%M"))
        #fig = px.scatter(df, x="dates", y=data_type, title=title)


    # Get new graph
    fig = get_graph_data(graphData)
    #if (fig != None):
    #    figOrig = fig
    
    return fig
    #return "Now updated {}, {}, {}, {}, {}".format(data_type, start_time, end_time, calc_step, plot_step)

if __name__ == '__main__':
    path = "/mnt/weewx/archive/weewx.sdb" 

    # Create plotter
    #units = {"outTemp": "deg F", "rain": "in", "rainRate": "in/hr"}
    #weatherPlot = WeatherPlotter(path, units, "plot_style.mplstyle")

    app.run_server(debug=False, host='192.168.0.58', port=8050)
