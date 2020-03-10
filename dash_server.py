import os
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output

# import dash_leaflet as dl

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

daily_reports_dir = 'COVID-19/csse_covid_19_data/csse_covid_19_daily_reports'
files = [f for f in os.listdir(daily_reports_dir) if os.path.isfile(os.path.join(daily_reports_dir, f))]
pattern = re.compile("^(\\d+)-(\\d+)-(\\d+).csv$")
data = {}
counter = 0
countries = set()
for file in files:
    matches = pattern.search(file)
    if matches:
        counter = 1 + counter
        date_id = "{}-{}-{}".format(matches.group(3), matches.group(1), matches.group(2))
        file_path = os.path.join(daily_reports_dir, file)
        csv = pd.read_csv(file_path)
        data[date_id] = csv
        countries.update(csv["Country/Region"].unique())
print("Loaded {} files".format(counter))
print({c: c for c in countries})

countries_data = {c: {} for c in countries}
for date, csv_values in data.items():
    for value in csv_values.values:
        country = value[1]
        if date not in countries_data[country]:
            countries_data[country][date] = 0
        countries_data[country][date] = countries_data[country][date] + value.item(3)

app.layout = html.Div(children=[
    html.H1("COVID-19 dashboard"),
    dcc.Dropdown(id='country', options=[{'label': c, 'value': c} for c in countries], multi=True),
    dcc.Graph(id='graph', figure={'layout': {'title': 'Select country to display developing graph'}})
])


@app.callback(Output(component_id='graph', component_property='figure'),
              [Input(component_id='country', component_property='value')])
def update_graph(countries):
    result = {
        'data': [
        ],
        'layout': {'title': "Developing COVID-19 cases day-by-day in [{}]".format(", ".join(countries))}
    }
    for country in countries:
        result['data'].append({'type': 'scatter',
                               'x': list(countries_data[country].keys()),
                               'y': list(countries_data[country].values()),
                               'name': country}
                              )
    return result


if __name__ == '__main__':
    app.run_server(debug=False)
