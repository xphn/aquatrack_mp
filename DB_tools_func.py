from win32com import client
import pandas as pd
import simplekml
from arcgis.gis import GIS
import requests
import urllib
import pandas as pd
from arcgis.geocoding import reverse_geocode
import pathlib
import tkinter


def elevation_function(df, lat_column, lon_column):
    url = r'https://nationalmap.gov/epqs/pqs.php?'
    """Query service using lat, lon. add the elevation values as a new column."""
    elevations = []
    for lat, lon in zip(df[lat_column], df[lon_column]):

        # define rest query params
        params = {
            'output': 'json',
            'x': lon,
            'y': lat,
            'units': 'Feet'
        }

        # format query string and return query value
        result = requests.get((url + urllib.parse.urlencode(params)))
        elevations.append(result.json()['USGS_Elevation_Point_Query_Service']['Elevation_Query']['Elevation'])
    df['elev_feet'] = elevations

def find_addr(df, lat_column, lon_column):
    locations = []
    for lat, lon in zip(df[lat_column], df[lon_column]):
        try:
            geocoded = reverse_geocode([lon, lat])
            print(geocoded['address']['Match_addr'])
            locations.append(geocoded['address']['Match_addr'])
        except:
            print("Couldn't match address. Try another place...")
            locations.append('NA')
    df['LOCATIONS'] = locations

def run_db_tab1():
    project_id = input('please insert the poroject id: ')
    excel = tkinter.filedialog.askopenfilename(
                    title='Select the Site Info for DB excel xlsx file',
                    initialdir='/',
                    filetypes=(('Excel files', '*.xlsx'),))

    user = 'nkwan_v_and_a'
    password = '1000sewerRAT'
    gis = GIS('https://v-and-a.maps.arcgis.com', user, password)
    un = gis.properties.user.username
    print(f' Logged in as {un}')

    id = 'a73f76ec01cd40268b704a423e5d8fc5'  # using FMgbd_download as a test
    project_id = project_id  # project photos to download
    gdb = gis.content.get(id)
    assert gdb is not None, "No matching project for this ID. Please Check the GIS layer ID."

    attac_tbl = gdb.layers[0].query(out_sr=4326, as_df=True)  # access the table information
    attac_tbl_select = attac_tbl.loc[attac_tbl['project_no'].str.contains(project_id, na=False),
                       :].reset_index(drop=True)  # only contains the selcted project
    attac_tbl_select = attac_tbl_select.dropna(subset=['install_date']).reset_index(drop=True)

    attac_tbl_select['lat'] = attac_tbl_select['SHAPE'].apply(lambda i: i.y)
    attac_tbl_select['lon'] = attac_tbl_select['SHAPE'].apply(lambda i: i.x)
    attac_tbl_select['direction'].fillna('',inplace=True)
    attac_tbl_select['in_out'].fillna('', inplace=True)
    elevation_function(attac_tbl_select, 'lat', 'lon')
    # find_addr(attac_tbl_select, 'lat', 'lon')

    project_name = attac_tbl_select['project_location'][0]
    excelApp = client.gencache.EnsureDispatch("Excel.Application")
    wb = excelApp.Workbooks.Open(excel)
    excelApp.Visible = True
    ws = wb.Worksheets('Site info for Rpt')

    ws.Range('A1').Value = project_id
    ws.Range('B1').Value = project_name

    for i in range(len(attac_tbl_select)):
        ws.Range(f'A{4 + i}').Value = i + 1
        ws.Range(f'B{4 + i}').Value = attac_tbl_select.loc[i, 'site_name']
        ws.Range(f'D{4 + i}').Value = attac_tbl_select.loc[i, 'mh_id']
        ws.Range(f'E{4 + i}').Value = attac_tbl_select.loc[i, 'expected_diam']
        ws.Range(f'F{4 + i}').Value = attac_tbl_select.loc[i, 'install_diameter']
        ws.Range(f'H{4 + i}').Value = attac_tbl_select.loc[i, 'direction'] + '_' + attac_tbl_select.loc[i, 'in_out']
        ws.Range(f'I{4 + i}').Value = attac_tbl_select.loc[i, 'site_location']
        ws.Range(f'J{4 + i}').Value = str(attac_tbl_select.loc[i, 'install_date'])
        ws.Range(f'K{4 + i}').Value = attac_tbl_select.loc[i, 'lat']
        ws.Range(f'L{4 + i}').Value = attac_tbl_select.loc[i, 'lon']
        ws.Range(f'M{4 + i}').Value = attac_tbl_select.loc[i, 'elev_feet']
        ws.Range(f'N{4 + i}').Value = attac_tbl_select.loc[i, 'install_sediment']

    ws = wb.Worksheets('Info for DB')
    ws.Range(f"A{6}:S{6 + attac_tbl_select.shape[0] - 1}").FillDown()

def run_db_tab2():
    # -------------------------------tab info for db----------------------------
    excel = tkinter.filedialog.askopenfilename(
        title='Select the Site Info for DB excel xlsx file',
        initialdir='/',
        filetypes=(('Excel files', '*.xlsx'),))

    user = 'nkwan_v_and_a'
    password = '1000sewerRAT'
    gis = GIS('https://v-and-a.maps.arcgis.com', user, password)
    un = gis.properties.user.username
    print(f' Logged in as {un}')

    excelApp = client.gencache.EnsureDispatch("Excel.Application")
    wb = excelApp.Workbooks.Open(excel)
    excelApp.Visible = True

    ws = wb.Worksheets('Info for DB')
    df = pd.DataFrame(ws.UsedRange())
    site_list = df.iloc[5:, [0]].dropna()
    site_list = site_list.iloc[:, 0].tolist()
    site_list = [i for i in site_list if i != 0]

    photo_dir = tkinter.filedialog.askdirectory(
            title='Choose the folder where the photos are saved')
    print(photo_dir)
    photo_dir =  pathlib.Path(photo_dir)
    photos = [i.stem for i in pathlib.Path.glob(photo_dir, '*.jpg')]
    photos = [i for i in photos if ' ' in i]

    pattern = ''
    while pattern != 'y' and pattern != 'n':
        pattern = input('Is there an empty space between Site and the number. i.e. Site 1. y/n')


    for idx, value in enumerate(site_list):
        site_name = value
        if pattern == 'n':
            photos_per_site = [x for x in photos if site_name == x.split(' ')[0]]
        else:
            photos_per_site = [x for x in photos if x.split(' ')[0]+' '+ x.split(' ')[1]]

        eff_photos = [x for x in photos_per_site if 'EFF' in x.upper()]
        inf_photos = [x for x in photos_per_site if 'INF' in x.upper()]

        for i in photos_per_site:
            if 'VIC' in i.upper():
                ws.Range(f'U{6 + idx}').Value = i + '.jpg'
            elif 'SAT' in i.upper():
                ws.Range(f'V{6 + idx}').Value = i + '.jpg'
                ws.Range(f'AI{6 + idx}').Value = 'Satellite Map'
            elif 'SAN' in i.upper():
                ws.Range(f'W{6 + idx}').Value = i + '.jpg'
                ws.Range(f'AJ{6 + idx}').Value = 'Sanitary Map'
            elif 'FLOW' in i.upper():
                ws.Range(f'X{6 + idx}').Value = i + '.jpg'
                ws.Range(f'AK{6 + idx}').Value = 'Flow Sketch'
            elif 'STREET' in i.upper():
                ws.Range(f'Y{6 + idx}').Value = i + '.jpg'
                ws.Range(f'AL{6 + idx}').Value = 'Street View'
            elif 'PLAN' in i.upper():
                ws.Range(f'Z{6 + idx}').Value = i + '.jpg'
                ws.Range(f'AM{6 + idx}').Value = 'Plan View'

        ws.Range(ws.Cells(6 + idx, 27),  # Cell to start the "paste"
                 ws.Cells(6 + idx, 27 + len(eff_photos) - 1)
                 ).Value = [i + '.jpg' for i in eff_photos]

        ws.Range(ws.Cells(6 + idx, 30),  # Cell to start the "paste"
                 ws.Cells(6 + idx, 30 + len(inf_photos) - 1)
                 ).Value = [i + '.jpg' for i in inf_photos]

        if len(eff_photos) == 1:
            ws.Range(f'AN{6 + idx}').Value = 'Effluent Pipe'

        if len(inf_photos) == 1:
            ws.Range(f'AQ{6 + idx}').Value = 'Influent Pipe'

    matrix = pd.DataFrame(ws.UsedRange())
    matrix = matrix.iloc[5:5 + len(site_list), 20:34]

    mask = matrix.notnull()
    matrix[mask] = 'h'
    matrix[~mask] = 'n'

    # -------------------------------tab info for missing photos----------------------------
    ws = wb.Worksheets('Missing Photos')
    ws.Range(ws.Cells(7, 2),  # Cell to start the "paste"
             ws.Cells(7 + len(site_list) - 1, 15)
             ).Value = matrix.values



