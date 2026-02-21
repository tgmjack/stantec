from django.shortcuts import render
from stantec import settings as stg
# Create your views here.



def use_local_data():
    import pandas as pd
    df = pd.read_excel('home/static/data.xlsx')
    return df.columns, df.values.tolist()

def get_data_from_local_sqlite_db():
    import sqlite3
    conn = sqlite3.connect('home/data.db')
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
        columns, rows = use_local_data()
    elif stg.USE_LOCAL_SQLITE_DB:
        columns, rows = get_data_from_local_sqlite_db()
    elif stg.USE_POSTGRES_DB:
        columns, rows = get_data_from_postgres()
    else:
        raise Exception("no data chosen")

    columns = list(columns)
    normalized_rows = []
    cell_data = []

    for row in rows:
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

# so its like this 
#    { make: "Tesla", model: "Model Y", price: 64950, electric: true },
 #   { make: "Ford", model: "F-Series", price: 33850, electric: false },
  #  { make: "Toyota", model: "Corolla", price: 29600, electric: false },
    return columns, normalized_rows, cell_data


def display_page(request):

    columns, rows, cell_data = get_data()
    
    title = 'think of a clever title'
    type_of_table_to_display = request.GET.get('type_of_table_to_display')


    print(type_of_table_to_display)
    print(columns)
    print(len(rows))

    context = {
        'title': title,
        'columns': columns,
        'rows': rows,
        'cell_data': cell_data,
        'type_of_table_to_display': type_of_table_to_display
    }

    return render(request, 'home/index2.html' , context)