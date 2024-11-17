# GAIL - STOCK POINT LOCATION, EX WORK LOCATION, POLYMER PRICE SHEET EXTRACTER AND SERVER

## Installation

1. `git clone git@github.com:beingtharur/gail-backend.git`

2. `python3 -m venv env`

3. `source env/bin/activate`

4. `pip install -r requirements.txt`

5. `python3 manage.py migrate`

6. `python3 manage.py createsuperuser` [create superuser]

7. `python3 manage.py runserver 0.0.0.0:8000`



## Note

Upload the files

file_types:
    "stock_point_file" --> "STOCK POINT FILE"
    "freight_file"     --> "FREIGHT FILE"
    "ex_work_file"     --> "EX WORK FILE"

To get data of stock point file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=stock_point_file&month=november&year=2024

To get data of freight file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=freight_file&month=november&year=2024

To get data of freight file of november 2024: http://0.0.0.0:8000/api/pdf/file-data/?file_type=ex_work_file&month=november&year=2024




