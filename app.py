import numpy as np
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb
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
df = pd.read_csv("C:\\Users\\pedro\\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\ks-projects-201801.csv")

#First look
df.columns

df.isnull().sum()
df.dropna(axis=0, inplace=True)

df.country.value_counts()
df.state.value_counts()
df.main_category.value_counts()
df.main_category.value_counts()
df.category.value_counts()

#Use usd_pledge_ instead of usd_pledged and usd_goal_real instead of goal
df["amnt_per_backer"] = [0 if df.loc[i,"backers"] == 0 else df.loc[i,"usd_pledged_real"]/df.loc[i,"backers"] for i in df.index.values]
df["completion_rate"] = df["usd_pledged_real"]/df["usd_goal_real"]

live_proj = df[df.state == "live"]
suspended_proj = df[df.state == "suspended"]

#Remove live and suspended projects as they are not complete so probably not as interesting?

df = df[~(df.state == "live")&~(df.state=="suspended")]

#Drop some columns
df.drop(["goal","pledged","usd pledged"], axis=1, inplace = True)

#clean launched tand deadline

df["launched"] = pd.to_datetime(df["launched"])
df["deadline"] = pd.to_datetime(df["deadline"])

#Compute days per project
df["days_passed"] = df["deadline"].sub(df["launched"], axis=0)

#Extract year and month and compute season
df["year"] = pd.DatetimeIndex(df["launched"]).year
df["month"] = pd.DatetimeIndex(df["launched"]).month

df["season"] = ["winter" if month<4 else "spring" if month < 7 else "summer" if month <10 else "autumn" for month in df.month.values]

df.year.value_counts()

df = df[~(df["year"]==2018)&~(df["year"]==1970)] #drop unecessary info

# convert datetime to days
df["days"] = df["days_passed"].dt.days
# convert to hours
df["hours"] = (df["days"]*24)+(df["days_passed"].dt.components["hours"])
# convert hours to minutes
df["minutes"] = df["hours"]*60

#Compute sucess rate
success_rate_overall = len(df[df.state == "successful"])/len(df)

success_rate_cat = pd.crosstab(df["main_category"], df["state"])
success_rate_cat_perc = success_rate_cat.apply(lambda r: r/r.sum(), axis=1)

success_rate_seas = pd.crosstab(df["season"], df["state"])
success_rate_seas_perc = success_rate_seas.apply(lambda r: r/r.sum(), axis=1)

success_rate_month = pd.crosstab(df["month"], df["state"])
success_rate_month_perc = success_rate_month.apply(lambda r: r/r.sum(), axis=1)

categories = df.main_category.unique()

#convert to percentage
success_rate_cat_perc.failed = pd.Series(["{0:.2f}%".format(val * 100) for val in success_rate_cat_perc.failed], index = success_rate_cat_perc.index)
success_rate_cat_perc.successful = pd.Series(["{0:.2f}%".format(val * 100) for val in success_rate_cat_perc.successful], index = success_rate_cat_perc.index)

success_rate_cat_perc = success_rate_cat_perc.reset_index()

#Calculations for Flashcards
max_money = df['usd_pledged_real'].max()
avg_money = df['usd_pledged_real'].mean()
min_money = df.usd_pledged_real[df['usd_pledged_real']>0].min()

shortest = df["minutes"][df["minutes"]>0].min()
longest = df["days"].max()


#add column month name
success_rate_month_perc['month name']=success_rate_month_perc.reset_index()['month'].apply(lambda x: calendar.month_abbr[x])
success_rate_month_perc.head()

# Sunburst Pre-processing

#data preparation for sunburst chart
#df totals by main category and category
grouped = df.groupby(['main_category','category'])['backers','usd_pledged_real'].sum().reset_index()
grouped['usd_pledged_mil']=grouped['usd_pledged_real']/1000 # drop decimals too
grouped.drop(['usd_pledged_real'],axis=1,inplace=True)

#top 10 for main category and category
grouped['rank']=grouped.groupby(['main_category'])['backers'].rank(ascending=False)
grouped=grouped[grouped['rank']<11]

#variables for sunburst
levels = ['category', 'main_category',] # levels used for the hierarchical chart
color_columns = ['backers','usd_pledged_mil']
value_column = 'backers'

#function that converts df to sunburst compatible format
def build_hierarchical_dataframe(df, levels, value_column, color_columns=None):
    """
    Build a hierarchy of levels for Sunburst or Treemap charts.

    Levels are given starting from the bottom to the top of the hierarchy,
    ie the last level corresponds to the root.
    """
    df_all_trees = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
    for i, level in enumerate(levels):
        df_tree = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
        dfg = df.groupby(levels[i:]).sum(numerical_only=True)
        dfg = dfg.reset_index()
        df_tree['id'] = dfg[level].copy()
        if i < len(levels) - 1:
            df_tree['parent'] = dfg[levels[i+1]].copy()
        else:
            df_tree['parent'] = 'Total'
        df_tree['value'] = dfg[value_column]
        df_tree['color'] = dfg[color_columns[0]] / dfg[color_columns[1]]
        df_all_trees = df_all_trees.append(df_tree, ignore_index=True)
    total = pd.Series(dict(id='Total', parent='',
                              value=df[value_column].sum(),
                              color=df[color_columns[0]].sum() / df[color_columns[1]].sum()))
    df_all_trees = df_all_trees.append(total, ignore_index=True)
    return df_all_trees

#converting df to sunburst format
df_all_trees = build_hierarchical_dataframe(grouped, levels, value_column, color_columns)

#replacing duplicate values in id column
df_all_trees['id1'] = df_all_trees['id'].str.cat(df_all_trees['parent'],sep=" ")
mask = df_all_trees['id'].duplicated()
df_all_trees.iloc[0:125, 0:1]=df_all_trees['id'].where(~mask, df_all_trees['id1'])

mask2=df_all_trees['id']==df_all_trees['parent']
df_all_trees['id']=df_all_trees['id'].where(~mask2, df_all_trees['id1'])

#dropping redundant column
df_all_trees.drop(['id1'],axis=1,inplace=True)

#creating info for colour selection
average_backer = grouped['usd_pledged_mil'].sum()/ grouped['backers'].sum()


# Calculations for Parallel Coordinates and Bubbles

df["counter"] = 1
sums_cat = pd.pivot_table(df,
                          values=["usd_pledged_real", "backers", "counter"],
                          index=["main_category"],
                          aggfunc="sum")

avg_backer = pd.pivot_table(df,
                            values=["amnt_per_backer"],
                            index=["main_category"],
                            aggfunc="mean")

sums_cat = sums_cat.merge(avg_backer, left_index=True, right_index=True)
con = sums_cat.merge(success_rate_cat_perc, left_index=True, right_on = "main_category").set_index("main_category")

con["success_rank"] = con["successful"].rank(ascending=True)
con["backers_rank"] = con["backers"].rank(ascending=True)
con["projects_rank"] = con["counter"].rank(ascending=True)
con["usd_pledged_rank"] = con["usd_pledged_real"].rank(ascending=True)
con["amnt_per_backer_rank"] = con["amnt_per_backer"].rank(ascending=True)

df2 = df.merge(con["success_rank"], left_on="main_category", right_on=con.index)

categories_sum = pd.pivot_table(df,
                                values=["usd_pledged_real"],
                                index=["main_category", "category"],
                                aggfunc="sum")


scaler = MinMaxScaler((10,80))
categories_sum2 = scaler.fit_transform(categories_sum)

categories_sum2 = pd.DataFrame(categories_sum2, columns=["pledged_minmax"], index=categories_sum.index)

categories_sum = categories_sum.merge(categories_sum2, left_index=True, right_index=True)


random.seed(17)
categories_sum["x"] = [random.uniform(1, 20) for i in categories_sum.index]
categories_sum["y"] = [random.uniform(1, 20) for i in categories_sum.index]

categories_sum = categories_sum.merge(con.success_rank, left_index=True, right_index=True)


categories_sum.reset_index(inplace=True)


########################################## INTERACTIVE COMPONENTS ##########################################
cat_options = [dict(label=category, value = category) for category in df.main_category.unique()]

########################################## APP ##########################################
app = dash.Dash(__name__)

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
            cmin=average_backer),
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
