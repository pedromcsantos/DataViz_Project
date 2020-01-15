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


########################################## DATA PREPROCESSING ##########################################
df_all_trees = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/df_all_trees.csv")
categories_sum = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/categories_sum.csv")
success_rate_cat_perc = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/success_rate_cat_perc.csv")
success_rate_month_perc = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/success_rate_month_perc.csv")
con = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/conlolol.csv")
max_money=pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/max_money.csv")
min_money=pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/min_money.csv")
average_money = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/average_money.csv")
shortest=pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/shortest.csv")
longest=pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/longest.csv")

########################################## INTERACTIVE COMPONENTS ##########################################
cat_options = [dict(label=category, value = category) for category in categories_sum.main_category.unique()]

########################################## APP ##########################################
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.Div([html.Img(src='https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/kickstarter-online-share-social-icon-290c27462fcd11ee7b4a6cbd9c1a46a9.png')],
                 style={'width': '15%'}),
        html.Div([
            html.H1('Kickstarter Projects')], className='Title',style={'color':'#FFFFFF','font-family': "Verdana",'width': '85%'}),
            html.H3("Explore the Industries", style={"margin-top": "0px", 'color':'#FFFFFF'}),
            html.H3("Measuring Success and Failure", style={"margin-top": "0px", 'color':'#FFFFFF'}),
        ],className = 'row container-display'),

    html.Div([# start row 1 flex display
        html.Div([html.Div([dcc.Graph(id = "sunburst")], className ='pretty')], style={'width': '40%', 'display': 'inline-block'}),
        html.Div([html.Div([dcc.Graph(id = "barchart")], className ='pretty')],style={'width': '60%', 'float': 'right', 'display': 'inline-block'}),
    ],className ='row container-display'),

    html.Br(),

    html.P('Filter by Category: ',style={'color':"#ffffff"}),

    html.Div([dcc.Dropdown(
    id='cat_drop',
    options=cat_options,
    value='Games'
    )
    ],className='pretty', style={'background-color':'#98f5ff'}),

    html.Br(),

    html.Div([
        html.Div([dcc.Graph(id='fc_1')], className='pretty column',style={'width': '24.6%', 'height':'30%','display': 'inline'}),
        html.Div([dcc.Graph(id='fc_2')], className='pretty column',style={'width': '24.5%', 'height':'30%','float': 'right', 'display': 'inline'}),
        html.Div([dcc.Graph(id='fc_3')], className='pretty column',style={'width': '24.5%','height':'30%','float': 'right', 'display': 'inline'}),
        html.Div([dcc.Graph(id='fc_4')], className='pretty column',style={'width': '24.6%','height':'30%','float': 'right', 'display': 'inline'}),
    ],className ='row container-display'),

    html.Br(),

    html.Div([html.Div([dcc.Graph(id="linechart")], className ='pretty')], style={'width': '100%', 'float': 'right', 'display': 'inline-block'}),

    html.Br(),

    html.Div([html.Div([dcc.Graph(id="bubble")], className ='pretty')],style={'width': '100%', 'float': 'right', 'display': 'inline-block'}),

    html.Br(),

    html.P('Filter by Year: ',style={'color':"#ffffff"}),

    html.Div([dcc.Slider( id = "year_slider",
                min=2009,
                max=2017,
                step=None,
                marks={str(year): str(year) for year in categories_sum['year'].sort_values().unique()},
                value=2017)], style={'width': '100%', 'float': 'right', 'display': 'inline-block'}),

    html.Br(),

    html.Div([html.Div([dcc.Graph(id="parallel")], className ='pretty')],style={'width': '100%', 'float': 'right', 'display': 'inline-block'}),

],style={"display": "flex", "flex-direction": "column"}
)

########################################## CALL BACKS ##########################################

@app.callback(
    [
        Output("sunburst","figure"),
        Output("bubble","figure"),
        Output("barchart","figure"),
        Output("linechart","figure"),
        Output("parallel","figure"),
        Output("fc_1","figure"),
        Output("fc_2","figure"),
        Output("fc_3","figure"),
        Output("fc_4","figure")
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
        marker=dict(reversescale=True,
            colors=df_all_trees['color'],
            colorscale='Viridis',
            showscale=True,  # 'GnBu'
            cmin=con["usd_pledged_real"].sum()/con["backers"].sum()),
        hovertemplate='<b>%{label} </b> <br> Backers: %{value}<br> Per Backer/Supporter: %{color:.2f}',
        maxdepth=2,
        name=''
    )

    layout_sunburst = go.Layout(
        title= "Category size by number of backers",
        paper_bgcolor="#2b2b2b",
        plot_bgcolor="#2b2b2b",font=dict(color="#ffffff")
        #plot_margin='0'
    )

    ########### Bubble ###########
    categories_sum_0 = categories_sum.loc[categories_sum["year"] <= year]

    data_bubble=[go.Scatter(
        x=categories_sum_0["x"],
        y=categories_sum_0["y"],
        mode='markers',
        text="TITLE", textposition="top center",
        marker=dict(colorscale="viridis", showscale=True,
            colorbar=dict(title="Main Category", tickvals=list(range(1, 16)),
            ticklen=5,
            ticktext=categories_sum_0.sort_values("success_rank")["main_category"].unique()),
            color=categories_sum_0.success_rank,
            size=(categories_sum_0["pledged_minmax"])
            ),
        hovertext=categories_sum_0["category"] + "<br>" + round(categories_sum_0["usd_pledged_real"] / 1000000, 1).map(str) + "M $" + "<br>" + categories_sum_0["year"].map(str),
        hoverinfo="text")]
    layout_bubble=go.Layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        title = "Amount of yearly investment by subcategory",
        paper_bgcolor="#2b2b2b",
        plot_bgcolor="#2b2b2b",font=dict(color="#ffffff")
        )
    ########### barchart ###########
    data_bar = [
        go.Bar(
            x=success_rate_cat_perc.main_category,
            y=success_rate_cat_perc.failed,
            base=0,
            marker=dict(
                color='#990000'
            ),
            name='Failure',
            yaxis='y2'
        ),
        go.Bar(
            x=success_rate_cat_perc.main_category,
            y=success_rate_cat_perc.successful,
            base=0,
            marker=dict(
                color='rgb(109,205,89)'
            ),
            name='Successful'
        )
    ]

    layout_bar=go.Layout(
        yaxis2=dict(rangemode='nonnegative', overlaying='y', range=[100, -100],
                    tickvals=np.arange(0, 101, 20), tickmode='array'),
        title='Percentage of Successful and Failure projects by subcategory', xaxis=dict(title='Categories'),
        barmode='stack',
        yaxis=dict(range=[-100, 100], tickvals=np.arange(0, 101, 20), tickmode='array',
                   title='Percentage of Failure/Success'),
        paper_bgcolor="#2b2b2b",
        plot_bgcolor="#2b2b2b",font=dict(color="#ffffff"),
        legend=dict(
            x=1,
            y=1.0,
            bgcolor="#2b2b2b",
            bordercolor="#2b2b2b")
    )

    ########### linechart ###########
    success_rate_month_perc_0 = success_rate_month_perc.loc[success_rate_month_perc.main_category == cat]

    x = success_rate_month_perc_0['month name']
    y = success_rate_month_perc_0['successful']

    data_line=go.Scatter(x=x, y=y, mode='lines+markers',marker=dict(color="rgb(109,205,89)"))
    best_month = success_rate_month_perc_0.loc[success_rate_month_perc_0["successful"] == success_rate_month_perc_0["successful"].max()]["month name"]
    best_month = best_month.to_string(index = False)

    layout_line=go.Layout(title= 'Monthly success rate:' +'<b>'+best_month+'</b>'+ ' is the best month to start a project in '+ '<b>'+cat+'</b>' + '.',
                          xaxis_title='Month', yaxis_title='Success Rate',
                          paper_bgcolor= "#2b2b2b", plot_bgcolor="#2b2b2b",font=dict(color="#ffffff"))

    ########### parallel ###########
    data_parallel=go.Parcoords(labelfont = dict(color="white"), rangefont=dict(color="white"),
        line=dict(color=con["success_rank"], colorscale="Viridis"),
        dimensions=list([
            dict(range=[1, 15],
                 label='Amount of Projects Ranking', values=con['projects_rank'],
                 tickvals=list(range(1, 16)),
                 ticktext=con[["main_category","projects_rank"]].sort_values("projects_rank")["main_category"]),
            dict(range=[1, 15],
                 label='Backers Ranking', values=con['backers_rank']),
            dict(range=[1, 15],
                 label='Amount per Backer Ranking', values=con['amnt_per_backer_rank']),
            dict(range=[1, 15],
                 label='Pledged Dollars Ranking', values=con['usd_pledged_rank']),
            dict(range=[1, 15],
                 label='Success Rate Ranking', values=con['success_rank'],
                 tickvals=list(range(1, 16)),
                 ticktext=con[["success_rank","main_category"]].sort_values("success_rank")["main_category"])]))

    layout_parallel = go.Layout( legend = dict(font=dict(color="white")),
        title= dict(text="Category Rankings (15 = Best)",font=dict(color="white")),
        paper_bgcolor= "#2b2b2b", plot_bgcolor="#2b2b2b"
    )
    #Flash Card 1
    max_money_0 = max_money.loc[max_money.main_category == cat]
    avg_money  = average_money.loc[average_money.main_category == cat]
    fc_1 = go.Indicator(
        mode = "number+delta",
        number={'prefix': "$", 'font':{'size':25}},
        title = {'text':"Maximum Investment", 'font':{'size':20}},
        delta={'reference': int(avg_money["usd_pledged_real"])},
        value = int(max_money_0["usd_pledged_real"]),
        domain = {'row': 0, 'column': 0})

    layout_fc = go.Layout(height = 120, paper_bgcolor = "#E0e0e0")

    #Flash Card 2
    min_money_0 = min_money.loc[min_money.main_category == cat]
    fc_2 = go.Indicator(
        mode="number+delta",
        number={'prefix': "$", 'font':{'size':25}},
        delta={'reference':  int(avg_money["usd_pledged_real"])},
        title={'text':"Minimum Investment",'font':{'size':20}},
        value=int(min_money_0["usd_pledged_real"]),
        domain={'row': 0, 'column': 1})

    #Flash Card 3
    longest_0  =longest.loc[longest.main_category == cat]
    fc_3 = go.Indicator(
        mode="number",
        number={'suffix': " Days",'font':{'size':25}},
        title={"text":"Longest Project", 'font':{'size':20}},
        value=int(longest_0["days"]),
        domain={'row': 1, 'column': 1})

    #Flash Card 4
    shortest_0 = shortest.loc[shortest.main_category == cat]
    fc_4 = go.Indicator(
        mode="number",
        number={'suffix': " Minutes", 'font':{'size':25}},
        title={"text":"Shortest Project",'font':{'size':20}},
        value=int(shortest_0["minutes"]),
        domain={'row': 1, 'column': 0})


    return go.Figure(data=data_sunburst, layout= layout_sunburst), \
           go.Figure(data=data_bubble, layout=layout_bubble),\
           go.Figure(data=data_bar, layout=layout_bar),\
           go.Figure(data=data_line, layout=layout_line),\
           go.Figure(data=data_parallel, layout=layout_parallel),\
           go.Figure(data=fc_1,layout=layout_fc), \
           go.Figure(data=fc_2,layout=layout_fc),\
           go.Figure(data=fc_3,layout=layout_fc),\
           go.Figure(data=fc_4,layout=layout_fc)

if __name__ == '__main__':
    app.run_server(debug=True)
