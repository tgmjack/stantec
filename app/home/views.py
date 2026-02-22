from django.shortcuts import render
from stantec import settings as stg
from pathlib import Path
# Create your views here.


def seperate_latitude_and_logitude_from_rest_of_df(df):
    
    latitude_and_longitude = {}
    for unique_value in df["location"].unique():
        latitude = df[df["location"] == unique_value]["latitude"].iloc[0]
        longitude = df[df["location"] == unique_value]["longitude"].iloc[0]
        latitude_and_longitude[unique_value] = (latitude, longitude)
    data_to_display = df.drop(columns=["latitude", "longitude"])

    return latitude_and_longitude, data_to_display
    

def use_local_data():
    import pandas as pd
    data_file = Path(stg.BASE_DIR) / 'home' / 'static' / 'Data2.xlsx'
    df = pd.read_excel(data_file)
    latitude_and_longitude, data_to_display = seperate_latitude_and_logitude_from_rest_of_df(df)
    return latitude_and_longitude, data_to_display

def get_data_from_local_sqlite_db():
    import sqlite3
    sqlite_file = Path(stg.BASE_DIR) / 'home' / 'data.db'
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data')
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    return columns, rows

def get_data_from_postgres():

    columns = None
    rows = None
    return columns, rows



def get_data():
    if stg.TESTING:
        latitude_and_longitude, data_to_display = use_local_data()
    elif stg.USE_LOCAL_SQLITE_DB:
        latitude_and_longitude, data_to_display = get_data_from_local_sqlite_db()
    elif stg.USE_POSTGRES_DB:
        latitude_and_longitude, data_to_display = get_data_from_postgres()
    else:
        raise Exception("no data chosen")

    columns = list(data_to_display.columns)
    normalized_rows = []
    cell_data = []

    for row in data_to_display.itertuples(index=False):
        if isinstance(row, dict):
            ordered_row = [row.get(column) for column in columns]
            row_object = {column: row.get(column) for column in columns}
        else:
            ordered_row = list(row)
            row_object = {
                column: ordered_row[index] if index < len(ordered_row) else None
                for index, column in enumerate(columns)
            }

        normalized_rows.append(ordered_row)
        cell_data.append(row_object)


    return columns, normalized_rows, cell_data , latitude_and_longitude


def display_page(request):

    columns, rows, cell_data , latitude_and_longitude = get_data()
    
    title = 'think of a clever title'
    type_of_table_to_display = request.GET.get('type_of_table_to_display')


    print(type_of_table_to_display)
    print(columns)
    print(len(rows))

    

    default_latitude = None
    default_longitude = None
    if latitude_and_longitude:
        first_latitude, first_longitude = next(iter(latitude_and_longitude.values()))
        default_latitude = first_latitude
        default_longitude = first_longitude

    context = {
        'title': title,
        'columns': columns,
        'rows': rows,
        'cell_data': cell_data,
        'type_of_table_to_display': type_of_table_to_display,
        'latitude_and_longitude': latitude_and_longitude,
        'default_latitude': default_latitude,
        'default_longitude': default_longitude
    }

    return render(request, 'home/index2.html' , context)