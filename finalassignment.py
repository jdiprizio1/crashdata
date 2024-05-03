'''
Created on Apr 23, 2024

@author: jdip1

Name: Jonathan DiPrizio
CS230: Section 2
Data: Motor Vehicle Crashes in MA in 2017
Description: This program summarizes the important and interesting parts of the data on 2017 MA car accidents.
The program allows the user to choose what they see. The options are: (1) a map showing all car crashes in the 
sample with the ability to filter by date, town, and if the accident was fatal, (2) a random accident generator,
which finds an accident based on the injury severity indicated by the user with a slider and shows on a map 
where the accident occurred, (3) a bar chart showing how many accidents occurred during each hour of the day,
(4) a pie chart showing distractions that most commonly caused accidents.

'''
#C:\Users\jdip1\anaconda3\Scripts\streamlit.exe run home.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pydeck as pdk
import random

def randomAccident(df):
    '''
    @param df: a dataframe
    @description: creates and displays a map and description of a random accident, based on the severity indicated by the slider
    '''
    
    #create header and slider
    st.subheader("Random Accident Generator")
    severity = st.slider("Injury Severity", 0.0, 3.0, 1.0)
    severityLst = ["No injury", "Non-fatal injury - Non-incapacitating", "Non-fatal injury - Incapacitating", "Fatal injury"]
    severity = round(severity)
    
    #create new df containing accidents of selected severity
    if severity == 3:
        df1 = df[df['CRASH_SEVERITY_DESCR'] == severityLst[severity]]
    else:
        df1 = df[df['MAX_INJR_SVRTY_CL'] == severityLst[severity]]
    
    df1 = df1[(pd.notna(df1["LAT"])) & (pd.notna(df1["LON"]))]
    
    #choose random accident    
    crashindex = random.randint(0, len(df1.index)-1)
    row = df1.iloc[crashindex]
    st.write("Injury severity:", row["MAX_INJR_SVRTY_CL"].split(" (")[0])
    if str(row["NUMB_VEHC"]) == "1":
        vehc = "single"
    else:
        vehc = str(row["NUMB_VEHC"])
    
    #display accident description  
    sentence = "At " + row["CRASH_TIME"] + " on " + row["CRASH_DATE_TEXT"] + ", a " + vehc + "-car accident on " + row["RDWY"].title() + " in " + row["CITY_TOWN_NAME"].title() + " caused " + row["CRASH_SEVERITY_DESCR"].lower().split(" (")[0] + "."
    st.write(sentence)
    crashid = row["OBJECTID"]
    df2 = df1[df1["OBJECTID"] == crashid]
   
    #define area shown
    view_state = pdk.ViewState(
        latitude=row['LAT'],
        longitude=row['LON'],
        zoom=17,
        pitch=0,
        )
    
    #plot points
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df2,
        get_position='[LON, LAT]',
        get_radius=7,
        get_fill_color=[255, 0, 0],
        pickable=True,
        filled=True)
    
    #choose map style
    map = pdk.Deck(layers=[layer], 
                 initial_view_state=view_state, 
                 map_style='mapbox://styles/mapbox/satellite-streets-v11'
                 )
    
    #display map
    st.pydeck_chart(map)


def lookup(df):
    '''
    @param df: a dataframe
    @description: creates a map of crashes, allowing user to filter what is shown
    '''
    
    st.subheader("Find accidents by:")
    
    #date input
    mindate = pd.to_datetime('2017-01-01')
    maxdate = pd.to_datetime('2017-12-31')
    date = st.date_input("Date", min_value=mindate, max_value=maxdate, value=None)
    date = pd.to_datetime(date)
    
    #town input
    towns = pd.unique(df["CITY_TOWN_NAME"])
    towns.sort()
    towns = np.insert(towns, 0, "All Cities")
    town = st.selectbox("City", towns)
    
    #fatal checkbox
    fatal_df = df[df["CRASH_SEVERITY_DESCR"] == "Fatal injury"]
    fatal = st.checkbox("Show only fatal crashes")
    
    #create new column; date in datetime format
    df["CRASH_DATE_TEXT1"] = pd.to_datetime(df["CRASH_DATE_TEXT"])
    
    #filter dfs by city
    if town != "All Cities":
        df = df[df['CITY_TOWN_NAME'] == town]
        fatal_df = fatal_df[fatal_df['CITY_TOWN_NAME'] == town]
    
    #define variables for map display
    maxLat = df["LAT"].max()
    maxLon = df["LON"].max()
    minLat = df["LAT"].min()
    minLon = df["LON"].min()
    midLat = (maxLat-minLat)/2 + minLat
    midLon = (maxLon-minLon)/2 + minLon
    zoom_level = -1 * np.log(max(maxLat-minLat, maxLon-minLon)) + 8.2   #asked CoPilot how to do dynamic zoom, altered formula until it was as I wanted
    
    #filter dfs by date
    if date is not None:    
        df = df[df['CRASH_DATE_TEXT1'] == date]
        if date in fatal_df:
            fatal_df = fatal_df[fatal_df['CRASH_DATE_TEXT1'] == date]
        else:
            fatal_df = pd.DataFrame(columns=['column1', 'column2'])
    
    #filter df by fatal        
    if fatal:
        df = df[df["CRASH_SEVERITY_DESCR"] == "Fatal injury"]
    
    #create and display map
    crashMap(df, fatal_df, zoom_level, midLat, midLon)
    


def crashMap(df, fatal_df, zoom_level, midLat, midLon, ptch = 0):
    '''
    @param df: a dataframe
    @param fatal_df: a dataframe
    @param zoom_level: a number indicating the zoom of the map
    @param midLat: number indicating latitude that will be the center of the map
    @param midLon: number indicating longitude that will be the center of the map
    @param ptch: number indicating pitch for map, default is 0
    '''
    
    #define area shown
    view_state = pdk.ViewState(
        latitude=midLat,
        longitude=midLon,
        zoom=zoom_level,
        pitch=ptch)
    
    #plot points
    layer1 = pdk.Layer('ScatterplotLayer',
                      data=df,
                      get_position='[LON, LAT]',
                      get_radius=500 - 30*zoom_level,
                      get_color=[0,0,255],
                      pickable=True
                      )
    layer2 = pdk.Layer('ScatterplotLayer',
                       data=fatal_df,
                       get_position='[LON, LAT]',
                       get_radius=700 - 30*zoom_level,
                       get_color=[255,0,0],
                       pickable=True
                       )

              
    #define map style and layers
    map = pdk.Deck(
        map_style='mapbox://styles/mapbox/outdoors-v11',
        initial_view_state=view_state,
        layers=[layer1, layer2],
    
    )
    
    #display map
    st.pydeck_chart(map)

    
def crashesByHour(df):
    '''
    @param df: a dataframe
    @return: a bar chart showing crashes by hour
    '''
    
    #convert time to datetime and sort by time
    df["CRASH_TIME"] = pd.to_datetime(df["CRASH_TIME"], format = "mixed")
    df1 = df.sort_values("CRASH_TIME")
    
    #count crashes by hour
    crash_counts = df1['CRASH_HOUR'].value_counts(sort = False)
    
    #create and modify list of times for x-axis labels
    timeLst = []
    for x in range(0,2):
        if x == 0:
            m = "AM"
        else:
            m = "PM"
        timeLst.append("12" + m)
        for num in range(1,12):
            timeLst.append(str(num) + m)    
    for item in timeLst:
        if int(item[:-2])%3 != 0:
            timeLst[timeLst.index(item)] = " " * timeLst.index(item)
    
    #create chart
    fig = plt.figure()
    plt.bar(timeLst, crash_counts)
    
    #modify chart
    plt.xticks(ticks = range(0, len(timeLst), 1), rotation=0)
    plt.title('Crashes by Hour')
    plt.xlabel('Time')
    plt.ylabel('Crashes')
    
    return fig
    

def distractColumn(column = ['DRVR_DISTRACTED_CL']):
    '''
    @param column: name of a column in a dataframe
    @return: value for new column
    '''
    
    if pd.isnull(column):
        x = 0  #filler
    elif "electronic device" in column:
        return "Using Electronic Device"
    elif "External" in column:
        return "Something Outside the Car"
    elif "Passenger" in column:
        return "Passenger"
    else:
        return "Other Distraction"    

    
    
def distractPieChart(df):  
    '''
    @param df: a dataframe
    @return: a pie chart showing the distractions causing accidents
    @return: total number of accidents caused by distractions
    '''
    
    df['DISTRACT'] = df['DRVR_DISTRACTED_CL'].apply(distractColumn)  #asked CoPilot how to call the function I created above
    distractCounts = df["DISTRACT"].value_counts()
    
    fig = plt.figure()
    plt.title("Types of Distractions Leading to Accident")
    plt.pie(distractCounts, labels=distractCounts.index, autopct='%.2f%%')
    
    distractTotal = distractCounts.sum()
    
    return fig, distractTotal
    

def crashesPerDay():
    '''
    @return: number of accidents reported per day
    '''
    
    count = 145068
    perday = count/365
    return perday
    

def main():    
    #read dataframe
    df = pd.read_csv("2017_Crashes_10000_sample.csv")    
    
    #produce top of page
    st.header("In 2017, Massachusetts reported")
    st.title(f"{round(crashesPerDay(), 2)} **car accidents per day.**")
    st.title(" ")
    
    #insert image
    image = 'https://media.nbcboston.com/2022/12/stonehamaccident-1.jpg?quality=85&strip=all&resize=1200%2C675'
    st.image(image, caption="A car accident on I-93 in Stoneham", use_column_width=True)
    
    #creates select box
    navLst = ["Select an Option", "Map of Accidents", "Random Accident Generator", "Crashes By Hour", "Accidents Caused by Distractions"]
    choice = st.selectbox("Choose what to see:", navLst)
    
    #displays content based on select box
    if choice == navLst[1]:
        lookup(df)
    elif choice == navLst[2]:
        randomAccident(df)
    elif choice == navLst[3]:
        st.header("Accidents are most likely to happen between 2PM and 6PM.")
        st.pyplot(crashesByHour(df))
    elif choice == navLst[4]:
        pieLst = distractPieChart(df)
        distractPct = (pieLst[1]/len(df))*100    
        distractStr = str(distractPct) + "% of accidents were confirmed to be caused by distractions. The real number is likely far higher."
        st.header(distractStr)
        st.pyplot(pieLst[0])
    


main()

