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


df = pd.read_csv("https://raw.githubusercontent.com/pedromcsantos/DataViz_Project/master/ks-projects-201801.csv")

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


success_rate_month = pd.crosstab(index = [df["month"],df["main_category"]],columns= df["state"])
success_rate_month_perc = success_rate_month.apply(lambda r: r/r.sum(), axis=1)

categories = df.main_category.unique()

#convert to percentage
success_rate_cat_perc.failed = pd.Series(["{0:.2f}%".format(val * 100) for val in success_rate_cat_perc.failed], index = success_rate_cat_perc.index)
success_rate_cat_perc.successful = pd.Series(["{0:.2f}%".format(val * 100) for val in success_rate_cat_perc.successful], index = success_rate_cat_perc.index)

success_rate_cat_perc = success_rate_cat_perc.reset_index()

#Calculations for Flashcards
df3 = df[df["state"]=="successful"]
max_money = df3[["main_category",'usd_pledged_real']].groupby("main_category").max().reset_index()
min_money = df3[["main_category",'usd_pledged_real']][df3.usd_pledged_real>0].groupby("main_category").min().reset_index()
average_money = df3[["main_category",'usd_pledged_real']].groupby("main_category").mean().reset_index()

shortest = df3[["main_category",'minutes']][df3["minutes"]>0].groupby("main_category").min().reset_index()
longest = df3[["main_category",'days']].groupby("main_category").max().reset_index()


#add column month name
success_rate_month_perc = success_rate_month_perc.reset_index()
success_rate_month_perc['month name']=success_rate_month_perc['month'].apply(lambda x: calendar.month_abbr[x])
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
con.reset_index(inplace = True)
df2 = df.merge(con[["main_category","success_rank"]], left_on="main_category", right_on="main_category")

categories_sum = pd.pivot_table(df,
                                values=["usd_pledged_real"],
                                index=["main_category", "category","year"],
                                aggfunc="sum")


scaler = MinMaxScaler((10,80))
categories_sum2 = scaler.fit_transform(categories_sum)

categories_sum2 = pd.DataFrame(categories_sum2, columns=["pledged_minmax"], index=categories_sum.index)

categories_sum = categories_sum.merge(categories_sum2, left_index=True, right_index=True)


random.seed(17)
categories_sum["x"] = [random.uniform(1, 20) for i in categories_sum.index]
categories_sum["y"] = [random.uniform(1, 20) for i in categories_sum.index]
categories_sum.reset_index(inplace=True)
categories_sum = categories_sum.merge(con[["main_category","success_rank"]], left_on="main_category", right_on="main_category")


#### Uncomment next session to get csv
"""
df_all_trees.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\df_all_trees.csv")

categories_sum.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\categories_sum.csv")

success_rate_cat_perc.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\success_rate_cat_perc.csv")

success_rate_month_perc.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\success_rate_month_perc.csv")

con.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\conlolol.csv")

#flash cards
max_money.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\max_money.csv")
min_money.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\min_money.csv")
average_money.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\average_money.csv")
shortest.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\shortest.csv")
longest.to_csv("C:\\Users\\pedro\Desktop\\Slides\\Data Viz\\Proj\\Kickstarter\\Git\\DataViz_Project\\longest.csv")

"""
