'''
This is the GUI designed for downloading rain gauge information. The main functionality is based on
getfromfile.py.
'''
import tkinter.filedialog
from tkinter import *
import pandas as pd
from Aquatrack_functions import convert, collect_all_days, coordinate, kml_making, fill_excel
import os
import requests

root = Tk()
root.title('AquaTrack V 0.0.4')
# root.iconbitmap(r'C:\Users\PXie\Documents\Python_Projects\wunderground\app_test\LOGO.ico')
root.geometry('600x450')
root.resizable(False, False)

# Define Variables
stationlist_var = StringVar(root)
exceltemp_var = StringVar(root)
savefolder_var = StringVar(root)
idffile_var = StringVar(root)



def select_file(var):
    filetypes = (
        ('text files', ('*.csv','*xlsx')),
        ('All files', '*.*')
    )

    filename = tkinter.filedialog.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)
    if var == 1: # For RG list
        stationlist_var.set("")
        file_entries.insert(0, f'{filename}')
    elif var ==2: # for cumlative remove excel
        exceltemp_var.set("")
        excelfile_entries.insert(0, f'{filename}')
    else:  # for idf
        idffile_var.set("")
        idffile_entry.insert(0, f'{filename}')



def save_to_folder():
    save_folder = tkinter.filedialog.askdirectory()
    savefolder_entry.insert(0, f'{save_folder}')


def run_app():
    '''

    :return:
    RG data file from on the list
    kml file for all the RGs on the list

    '''
    paccumchoice = "Yes"
    stationlist = stationlist_var.get()
    exceltemp = exceltemp_var.get()
    savefolder = savefolder_var.get()

    file = open(stationlist, "r")
    all_coordinate_dict = {}
    # Repeat for each station in the .csv file
    for line in file:
        # Let's split the line into an array called "fields" using the "," as a separator:
        fields = line.split(",")
        # and let's extract the data:
        stationName = fields[0]
        startDate_str = fields[1]
        endDate_str = fields[2]
        startDate = convert(startDate_str)
        endDate = convert(endDate_str)
        print("Get " + stationName + " from: " + startDate_str + " to: " + endDate_str)

        # collect rain data and the rain gauge coordination
        NA_station = collect_all_days(stationName, startDate, endDate, paccumchoice,savefolder)
        if stationName not in NA_station:
            coordinates = coordinate(stationName,startDate.strftime("%Y-%m-%d"))
            all_coordinate_dict[stationName] = coordinates
            df_coordinate_all = pd.DataFrame(all_coordinate_dict).T.rename(
            columns={1: 'Latitude (Degree)', 0: 'Longitude (Degree)'})
            fill_excel(stationName, exceltemp, savefolder)
        else:
            print(f'The Station {stationName} is not not available on the website')
            print('\n\n')


    # It is good practice to close the file at the end to free up resources
    file.close()

    # save the coordination file
    df_coordinate_all.to_csv(savefolder + '/'+os.path.split(stationlist)[1].split('.')[0]+'_coordinates.csv')

    # Making KML file
    kml_making(df_coordinate_all,savefolder,stationlist)




def get_idf():
    '''
    this function takes in the coordination list of RGs and download the IDF files to the designated folder
    :return: IDF files for each RG location
    '''
    # coordinate_list = tkinter.filedialog.askopenfilename(
    #     title='Select the coordinate list file')
    coordinate_list = idffile_var.get()
    coordinate_pd = pd.read_csv(coordinate_list)

    saveto = os.path.dirname(coordinate_list)

    for i in range(len(coordinate_pd)):
        station_name = coordinate_pd.iloc[i, 0]
        lon = str(coordinate_pd.iloc[i, 1])
        lat = str(coordinate_pd.iloc[i, 2])
        url_csv = f"https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv?lat={lat}6&lon={lon}&data=depth&units=english&series=pds&selAddr=Burlingame, California, USA&selElevNum=511.04&selElevSym=ft&selStaName=-"
        req_csv = requests.get(url_csv)

        with open(f"{saveto}/{station_name}_idf.csv", 'w', encoding=req_csv.encoding) as csvFile:
            csvFile.write(req_csv.text, )
        print(f"{station_name}'s IDF is downloaded")




##  Headers
frame_header = Frame(root, borderwidth=2, pady=2)
center_frame = Frame(root, borderwidth=1, pady=1)
bottom_frame = Frame(root, borderwidth=2, pady=5)
idf_frame = Frame(root, borderwidth=2, pady=5)
run_idf_frame = Frame(root, borderwidth=2, pady=5)

frame_header.grid(row=0, column=0)
center_frame.grid(row=1, column=0)
bottom_frame.grid(row=3, column=0)
idf_frame.grid(row=4, column=0)
run_idf_frame.grid(row =5, column =0)

#  label header to be placed in the frame_header
header = Label(frame_header, text = 'This is AquaTrack V_0.0.4 for automated RG data and IDF data collection. For questions, email: pxie@vaengineering.com',
               wraplength = 600, bg='lightblue', fg='black', height='3', font=("Helvetica 14 bold"))

header.grid(row=0, column=0)


##  Step 1: The loading files for rain gauge list
frame_main_1 = LabelFrame(center_frame, borderwidth=2, text = 'Step1: Load the csv file that contains the list of RGs and CUMULATIVE REMOVE formula.xlsx',
                          width=550, height = 80, padx = 10, pady =5, relief ='raised')
frame_main_1.pack(pady = 2)
loadfile_btn = Button(frame_main_1, text = 'Load RG_list File', command = lambda: select_file(1))
file_entries = Entry(frame_main_1, width = 70, textvariable = stationlist_var)

loadexecl_btn = Button(frame_main_1, text = 'CUMULATIVE REMOVE Excel', command =lambda: select_file(2))
excelfile_entries = Entry(frame_main_1, width = 58, textvariable = exceltemp_var)


frame_main_1.pack(pady = 2, fill= 'x')
loadfile_btn.place(width=93, height =20)
loadexecl_btn.place(width =160, height=20, x=0, y=30)
file_entries.place(x= 100, y=0)
excelfile_entries.place(x=173, y=30)
frame_main_1.pack_propagate(0)


## Step 2: Selecting the save file locations
frame_main_2 = LabelFrame(center_frame, borderwidth=2, text = 'Step2: Select the folder to save the files',
                          width=550, height = 50, padx = 10, pady =5, relief ='raised' )
savefile_btn = Button(frame_main_2, text = 'Save to Folder', command = save_to_folder)
savefolder_entry = Entry(frame_main_2, width = 70, textvariable = savefolder_var)

frame_main_2.pack(pady = 10)
frame_main_2.pack_propagate(0)
savefile_btn.pack(side='left')
savefolder_entry.pack(side ='right')

## Step 3: Run Obtain rain data

frame_main_3 = LabelFrame(bottom_frame, borderwidth=2, text = 'Step3: Run the application',
                          width=550, height = 50, padx = 150, pady =5, relief ='raised')
runfile_btn = Button(frame_main_3, text = 'Get RG Data', command = run_app)
# get_idf_btn = Button(frame_main_3, text = 'Get_IDF', command = get_idf)
frame_main_3.pack()
frame_main_3.pack_propagate(0)
runfile_btn.pack()
# get_idf_btn.pack(side ='right')


## Step 4: IDF DATA
frame_main_4 = LabelFrame(idf_frame, borderwidth=2, text = 'Step4: Select the coordination list for the RGs',
                          width=550, height = 50, padx = 10, pady =5, relief ='raised' )

idffile_btn = Button(frame_main_4, text = 'Load Coordination_list File', command = lambda: select_file(3))
# idffile_btn = Button(frame_main_4, text = 'Coordination list file', command = get_idf)
idffile_entry = Entry(frame_main_4, width = 58, textvariable = idffile_var)

frame_main_4.pack(pady = 10)
frame_main_4.pack_propagate(0)
idffile_btn.pack(side='left')
idffile_entry.pack(side ='right')

## Step 5: Run get idf data

frame_main_5 = LabelFrame(run_idf_frame, borderwidth=2, text = 'Step5: Get IDF Data',
                          width=550, height = 50, padx = 150, pady =5, relief ='raised')

get_idf_btn = Button(frame_main_5, text = 'Get_IDF', command = get_idf)
frame_main_5.pack()
frame_main_5.pack_propagate(0)
get_idf_btn.pack()



root.mainloop()
