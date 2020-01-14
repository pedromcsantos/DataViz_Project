import numpy as np
import pandas as pd
from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output
import numpy as np
import plotly.graph_objs as go
import plotly.offline as pyo
import calendar
import random
from sklearn.preprocessing import MinMaxScaler

########################################## DATA PREPROCESSING ##########################################


########################################## INTERACTIVE COMPONENTS ##########################################
cat_options = [dict(label=category, value = category) for category in categories_sum.main_category.unique()]

########################################## APP ##########################################
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1('Kickstarter Projects - Data Visualization')], className='Title'),
    html.Div([# Left side division
        html.Div([dcc.Graph(id = "sunburst")], className = "column1"),
        html.Div([dcc.Graph(id="bubble")], className = "column1"),
             ]),
        html.Div([#Slider
            dcc.Slider( id = "year_slider",
                min=df.year.min(),
                max=df.year.max(),
                step=None,
                marks={str(year): str(year) for year in df['year'].sort_values().unique()},
                value = df['year'].max())
             ]),
    html.Div([ #right side
        html.Div([#Flash Cards
            html.Div([html.Label(id='fc_1')], className='mini pretty'),
            html.Div([html.Label(id='fc_2')], className='mini pretty'),
            html.Div([html.Label(id='fc_3')], className='mini pretty'),
            html.Div([html.Label(id='fc_4')], className='mini pretty'),
        ], className = "column2"),
        html.Div([#Bar chart
            dcc.Graph(id="linechart")
         ], className = "column2"),
        html.Div([#linechart
            dcc.Graph(id = "barchart")
        ], className = "column2"),
        html.Div([#Drop down
            dcc.Dropdown(
                id='cat_drop',
                options=cat_options,
                value=['Games'],
                multi=True
                )
             ])
    ]),
    html.Div([# Parallel last row
        dcc.Graph(id="parallel")
         ], className = "column3")

])

########################################## CALL BACKS ##########################################

@app.callback(
    [
        Output("sunburst","figure"),
        Output("bubble","figure"),
        Output("barchart","figure"),
        Output("linechart","figure"),
        Output("parallel","figure")
    ],
    [
        Input("year_slider", "value"),
        Input("cat_drop", "value")
    ]
)
def plots(year,cat):
    ########### Sunburst ###########
    data_sunburst = dict(type = "sunburst",
        labels=df_all_trees['id'],
        parents=df_all_trees['parent'],
        values=df_all_trees['value'],
        branchvalues='total',
        opacity=0.8,
        marker=dict(
            colors=df_all_trees['color'],
            colorscale='ice',
            showscale=False,  # 'GnBu'
            cmin=con["usd_pledged_real"].sum()/con["backers"].sum()),
        hovertemplate='<b>%{label} </b> <br> Backers: %{value}<br> Per Backer: %{color:.2f}',
        maxdepth=2
    )

    #layout_sunburst = margin=dict(t=5, b=5, r=5, l=5)

    ########### Bubble ###########
    data_bubble=[go.Scatter(
        x=categories_sum["x"],
        y=categories_sum["y"],
        mode='markers',
        text=round(categories_sum["usd_pledged_real"] / 1000, 0), textposition="top center",
        marker=dict(colorscale="viridis", showscale=True,
            colorbar=dict(title="Main Category", tickvals=list(range(1, 16)),
            ticklen=5,
            ticktext=categories_sum.sort_values("success_rank")["main_category"].unique()),
            color=categories_sum.success_rank,
            size=(categories_sum["pledged_minmax"])
            ),
        hovertext=categories_sum["category"] + "<br>" + round(categories_sum["usd_pledged_real"] / 1000000, 1).map(str) + "M $",
        hoverinfo="text")]
    layout_bubble=go.Layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    ########### barchart ###########
    data_bar = [
        go.Bar(
            x=success_rate_cat_perc.main_category,
            y=success_rate_cat_perc.failed,
            base=0,
            marker=dict(
                color='#cc0000'
            ),
            name='Failure',
            yaxis='y2'
        ),
        go.Bar(
            x=success_rate_cat_perc.main_category,
            y=success_rate_cat_perc.successful,
            base=0,
            marker=dict(
                color='#00802b'
            ),
            name='Successful'
        )
    ]

    layout_bar=go.Layout(
        yaxis2=dict(rangemode='nonnegative', overlaying='y', range=[100, -100],
                    tickvals=np.arange(0, 101, 20), tickmode='array'),
        title='Success vs Failure', xaxis=dict(title='Categories'),
        barmode='stack',
        yaxis=dict(range=[-100, 100], tickvals=np.arange(0, 101, 20), tickmode='array',
                   title='Percentage of Failure/Success')
    )

    ########### linechart ###########
    x = success_rate_month_perc['month name']
    y = success_rate_month_perc['successful']

    data_line=go.Scatter(x=x, y=y, mode='lines+markers')

    layout_line=go.Layout(title='April is best month to start a Project', xaxis_title='Month', yaxis_title='Success Rate')

    ########### parallel ###########
    data_parallel=go.Parcoords(
        line=dict(color=con["success_rank"], colorscale="Electric"),
        dimensions=list([
            dict(range=[1, 15],
                 label='Amount of Projects Ranking', values=con['projects_rank'],
                 tickvals=list(range(1, 16)),
                 ticktext=con["projects_rank"].sort_values().index),
            dict(range=[1, 15],
                 label='Backers Ranking', values=con['backers_rank']),
            dict(range=[1, 15],
                 label='Amount per Backer Ranking', values=con['amnt_per_backer_rank']),
            dict(range=[1, 15],
                 label='Pledged Dollars Ranking', values=con['usd_pledged_rank']),
            dict(range=[1, 15],
                 label='Success Rate Ranking', values=con['success_rank'],
                 tickvals=list(range(1, 16)),
                 ticktext=con["success_rank"].sort_values().index)]))

    return go.Figure(data=data_sunburst), \
           go.Figure(data=data_bubble, layout=layout_bubble),\
           go.Figure(data=data_bar, layout=layout_bar),\
           go.Figure(data=data_line, layout=layout_line),\
           go.Figure(data=data_parallel)

if __name__ == '__main__':
    app.run_server(debug=True)
