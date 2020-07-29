import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash_table.Format import Format
from dash.dependencies import Input, Output, State
import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime as dt

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# цвета для графиков
blue = '#7bc7ff'
green = "#92d8d8"
red = "#fac1b7"

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets,
)
server = app.server
app.config["suppress_callback_exceptions"] = True

true_data = pd.read_csv('data/original.csv')
regions = true_data['region'].unique()

predicted_data = pd.read_csv('data/submit.csv')
id_info = predicted_data['id'].str.split('_', expand=True)
id_info.columns = ['region', 'date', 'hour', 'pred_number']
predicted_data = pd.concat((id_info, predicted_data[['y']]), axis=1)

data = true_data[['region', 'tpep_pickup_datetime', 'T+1']]
data.columns = ['region', 'datetime', 'y']
data['datetime'] = pd.to_datetime(data['datetime'])
data['y'] = data['y'].astype(float)

pred_data = predicted_data[predicted_data['pred_number'] == '1'].drop('pred_number', axis=1)
pred_data['datetime'] = pred_data['date'] + ' ' + pred_data['hour'] + ':00:00'
pred_data['datetime'] = pd.to_datetime(pred_data['datetime'])
pred_data['y'] = pred_data['y'].astype(float)
pred_data.drop(['date', 'hour'], axis=1, inplace=True)

coordinates = pd.read_csv('data/regions.csv', sep=';')
coordinates = coordinates[coordinates['region'].isin(regions)]
coordinates.set_index('region', inplace=True)
geo = {
    'type': 'FeatureCollection',
    'features': []
}
for region, row in coordinates.iterrows():
    cur_coords = row.values
    geo['features'].append(
        {
            'type': 'Feature',
            'properties': {
                'REGION': region,
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': [
                    [
                        [cur_coords[0], cur_coords[3]],
                        [cur_coords[1], cur_coords[3]],
                        [cur_coords[1], cur_coords[2]],
                        [cur_coords[0], cur_coords[2]],
                        [cur_coords[0], cur_coords[3]],
                    ]
                ]
            },
            'id': region
        },
    )


def build_banner():
    return html.Div(
        [
            html.H3("", className="one-third column"),
            html.Div(
                [
                    html.H3(
                        "Прогноз вызовов в такси", style={'text-align': 'center'}
                    ),
                    html.H5(
                        "Нью-Йорк", style={'text-align': 'center'}
                    ),
                ],
                className="one-half column",
            ),
            html.A(
                html.Button("github"),
                href="https://github.com/OrionChocoPie/Coursera-Taxi-Project",
                className="one-third column",
                style={'float': 'right'}
            )
        ],
        className="row flex-display",
    )

@app.callback(
    Output("time-series-plot", "figure"),
    [
        Input("region-selector", "value"),
    ],
)
def render_time_series(region):
    fig = go.Figure()
    cur_true_data = data[data['region'] == region]
    cur_pred_data = pred_data[pred_data['region'] == str(region)]

    fig.add_trace(
        go.Scatter(
            x=cur_true_data['datetime'], y=cur_true_data['y'],
            name='Реальное',
            line=dict(shape="spline", smoothing=1.05, width=1, color=green),
            marker=dict(symbol='circle-open'),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=cur_pred_data['datetime'], y=cur_pred_data['y'],
            name='Прогноз',
            line=dict(shape="spline", smoothing=1.05, width=1, color=red),
            marker=dict(symbol='circle-open'),
        )
    )

    fig.update_layout(
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    return fig

@app.callback(
    Output("map", "figure"),
    [
        Input("date-picker", "date"),
    ],
)
def render_map(date):
    cur_pred_data = pred_data[pred_data['datetime'] == pd.to_datetime(date)]

    fig = go.Figure(go.Choroplethmapbox(
            geojson=geo,
            locations=cur_pred_data['region'],
            z=cur_pred_data['y'],
            colorscale=[[0, 'rgb(184, 225, 255)'], [1, 'rgb(0, 147, 255)']],
            showscale = False,
            text='region: ' + cur_pred_data['region'] + ' taxi: ' + cur_pred_data['y'].astype(int).astype(str),
            hoverinfo='text',
            marker_opacity=0.7,
        )
    )

    fig.update_layout(
        mapbox = {
            'style': "carto-positron",
            'center': {'lon': -73.98519, 'lat': 40.74843},
            'zoom': 10
        },
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend = False
    )

    return fig


# Основная часть, где отрисовывается весь сайт
app.layout = html.Div(
    id="big-app-container",
    style={"display": "flex", "flex-direction": "column"},
    children=[
        build_banner(),
        html.Div(
            [
                html.Div(
                    className="mini_container fourth columns",
                    children=[
                        html.Label(children='Выберите область'),
                        dcc.Dropdown(
                            id="region-selector",
                            options=[
                                {'label': i, 'value': i} for i in regions
                            ],
                            value=regions[0],
                            searchable=False,
                        ),
                    ],
                ),
                html.Div(
                    className="mini_container second columns",
                    children=[
                        html.Label(children='Выберите дату'),
                        dcc.DatePickerSingle(
                            id='date-picker',
                            min_date_allowed=dt(2016, 6, 1),
                            max_date_allowed=dt(2016, 6, 30),
                            initial_visible_month=dt(2016, 6, 1),
                            date=str(dt(2016, 6, 1))
                        ),
                    ],
                ),
            ],
            className="row container-display",
        ),
        html.Div(
            className="pretty_container",
            children=[dcc.Graph(id='time-series-plot')],
        ),
        html.Div(
            className="pretty_container",
            children=[dcc.Graph(id='map')],
        ),
    ],
)

# if __name__ == "__main__":
#     app.run_server(debug=True, host='0.0.0.0', port=8050)