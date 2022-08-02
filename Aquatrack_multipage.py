from tkinter import font as tkfont # python 3
import tkinter.filedialog
import tkinter as tk
from AquactracFunctions import *
import time
from DB_tools_func import *

#==================================================================================================================

# App Layouts
#====================================================================================================================
class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo, PageThree,PageFour):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.controller.title('Aquatrack')
        self.controller.state('zoomed')

        headinglabel1 = tk.Label(self, text="Aquatrack Multifunction Version",
                         font=('Helvetica', 45, "bold"),
                         foreground = 'white',
                         background = '#add8e6')

        space_label1 = tk.Label(self,height=3)

        headinglabel2 = tk.Label(self, text='Select Tools',
                                 font=('Helvetica', 30, "bold"))


        button1 = tk.Button(self, text="Rain Gauge Data Download and Processing",
                            font = ('Helvetica', 15),
                            relief = 'raised',
                            borderwidth = 3,
                            width =40,
                            height =3,
                            command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(self, text="Flow Sketches&KMZ Download",
                            font=('Helvetica', 15),
                            relief='raised',
                            borderwidth=3,
                            width=40,
                            height=3,
                            command=lambda: controller.show_frame("PageTwo"))
        button3 = tk.Button(self, text="Flow QAQC",
                            font=('Helvetica', 15),
                            relief='raised',
                            borderwidth=3,
                            width=40,
                            height=3,
                            command=lambda: controller.show_frame("PageThree"))
        button4 = tk.Button(self, text="Datebase Creation Tools",
                            font=('Helvetica', 15),
                            relief='raised',
                            borderwidth=3,
                            width=40,
                            height=3,
                            command=lambda: controller.show_frame("PageFour"))

        headinglabel1.pack(side="top", fill="x", pady=20)
        space_label1.pack()
        headinglabel2.pack(fill='both', ipady =17)
        button1.pack(pady = 5)
        button2.pack(pady = 5)
        button3.pack(pady=5)
        button4.pack(pady=5)


class PageOne(tk.Frame):
    "Rain Gauge Data Prcessing Page"

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

# ========================Functions===========================================
        def select_file(var):
            if var == 1:  # For RG list
                filename = tkinter.filedialog.askopenfilename(
                    title='Open a RG list csv file',
                    initialdir='/',
                    filetypes= (('CSV files','*.csv'),))
                stationlist_var.set("")
                entry_rglist.insert(0, f'{filename}')

            elif var == 2:  # for cumlative remove excel
                filename = tkinter.filedialog.askopenfilename(
                    title='Open a Accumulative excel xlsx file',
                    initialdir='/',
                    filetypes=(('Excel files', '*.xlsx'),))
                exceltemp_var.set("")
                entry_excelfile.insert(0, f'{filename}')


        def save_to_folder():
            save_folder = tkinter.filedialog.askdirectory()
            entry_savefolder.insert(0, f'{save_folder}')

        def run_app():
            '''
            :return:
            RG data file from on the list
            kml file for all the RGs on the list
            '''
            start = time.time()
            stationlist = stationlist_var.get()
            exceltemp = exceltemp_var.get()
            savefolder = savefolder_var.get()
            choice = mode_var.get()
            download_or_append = doa_var.get()
            run_func(stationlist, choice, download_or_append, savefolder, exceltemp)

            end = time.time()

            # total time taken
            print(f'Runtime of the program is {end - start} seconds')


        # ========================Variables=========================================================================
        stationlist_var = tk.StringVar(self)
        exceltemp_var = tk.StringVar(self)
        savefolder_var = tk.StringVar(self)
        mode_var=tk.IntVar(self)
        mode_var.set(1)
        doa_var = tk.IntVar(self)
        doa_var.set(1)

        # ========================Pages Layout======================================================================
        headinglabel1 = tk.Label(self, text="Rain Gauge Data Download and Processing",
                         font=('Helvetica', 45, "bold"),
                         foreground = 'white',
                         background = '#add8e6')
        headinglabel1.pack(side="top", fill="x", pady=10)

        space_label1 = tk.Label(self,text="Tips: If the app says the data is missing from some sites for certain days,"
                                          " it is very likely due to the ads in WUNDERGROUND. Please check the website "
                                          "or choose to download the data after webpage is fully rendered",
                         font=('Helvetica', 15), height=3)
        space_label1.pack()

        #==================================Step 1 =====================================================================
        label_step1 = tk.LabelFrame(self, borderwidth=2,
                                  text='Step1: Load the list of RGs CSV file and CUMULATIVE REMOVE formula.xlsx',
                                  font=('Helvetica', 15),height = 80, padx = 20, pady =15,)
        label_step1.pack(fill='both', ipady=20, ipadx = 20)
        btn_load_rglist = tk.Button(label_step1, text='Load RG_list File', font=('Helvetica', 12),command = lambda: select_file(1))
        entry_rglist = tk.Entry(label_step1,font=('Helvetica', 10), textvariable =stationlist_var)

        label_step1.pack(fill='both', pady=20)
        btn_load_rglist.pack(side='left', padx= 10)
        entry_rglist.pack(side= 'left', fill='x',expand = True, padx = 10, ipady=5)

        btn_loadexcel = tk.Button(label_step1, text='CUMULATIVE REMOVE Excel',font=('Helvetica', 12),command =lambda: select_file(2))
        entry_excelfile = tk.Entry(label_step1, font=('Helvetica', 10),textvariable = exceltemp_var)
        btn_loadexcel.pack(side='left', padx = 10)
        entry_excelfile.pack(side= 'left', fill='x',expand = True, padx = 10, ipady=5)

        ## Step 2: Selecting the save file locations----------------------------------------------
        label_step2 = tk.LabelFrame(self, borderwidth=2, text='Step2: Select the folder to save the files. '
                                                              'It is highly recommended to create new folder for this',
                                  font=('Helvetica', 15),height = 80, padx = 20, pady =15)
        label_step2.pack(fill='both', pady=20)

        btn_savefolder = tk.Button(label_step2, text='Save to Folder',font=('Helvetica', 12),command = save_to_folder)
        btn_savefolder.pack(side='left', padx = 10)
        entry_savefolder = tk.Entry(label_step2, width = 70,textvariable = savefolder_var)
        entry_savefolder.pack(side= 'left', fill='x',expand = True, padx = 10, ipady=5)

        ## Step 3: Run Obtain rain data-------------------------------------------------------
        label_step3 = tk.LabelFrame(self, borderwidth=2, text='Step3: Download RG Data',
                                  font=('Helvetica', 15),height = 80, padx = 20, pady =15)
        label_step3.pack(fill='both', pady=20)

        backend = Radiobutton(label_step3, text='Backend mode', value=1, font=('Helvetica', 12), variable=mode_var,
                              tristatevalue=1)
        selenium = Radiobutton(label_step3, text='Selinum mode', value=2, font=('Helvetica', 12), variable=mode_var,
                               tristatevalue=0)
        backend.pack(side='left', padx=10)
        selenium.pack(side='left', padx=10)

        download = Radiobutton(label_step3, text='Download RG Data', value=1, font=('Helvetica', 12), variable=doa_var,
                              tristatevalue=1)
        append = Radiobutton(label_step3, text='Append to Previous RG Data', value=2, font=('Helvetica', 12), variable=doa_var,
                               tristatevalue=0)
        download.pack(side='left', padx=10)
        append.pack(side='left', padx=10)

        btn_run = tk.Button(label_step3, text='Download RG Data', font=('Helvetica', 12),command = run_app)
        btn_run.pack(side='left',fill='x',expand = True, padx = 10, ipady=5)


        ## Step 4: Additional Steps------------------------------------------------

        label_step4 = tk.LabelFrame(self, borderwidth=2, text='Step 4: Get Coordination, IDF and Tidal Data',
                                 font=('Helvetica', 15),height = 80, padx = 20, pady =15)

        btn_getcoord = tk.Button(label_step4, text='Get_Coordination', font=('Helvetica', 12), command=coordinate)
        btn_getcoord.pack(side='left', fill='x', expand=True, padx=5, ipady=5)

        btn_getidf = tk.Button(label_step4, text='Get_IDF (need to run Get_coordination first)',font=('Helvetica', 12),command = get_idf)
        label_step4.pack(fill='both', pady=20)
        btn_getidf.pack(side='left',fill='x',expand = True, padx = 5, ipady=5)

        btn_gettidal = tk.Button(label_step4, text='Get_Tidal', font=('Helvetica', 12), command=get_tidal)
        btn_gettidal.pack(side='left', fill='x', expand=True, padx=5, ipady=5)


#------------------------------------------Step 5----------------------------------------------------------------
        label_step5 = tk.LabelFrame(self, borderwidth=2, text='Step 5: Rain QAQC',font=('Helvetica', 15),height = 80, padx = 20, pady =15)
        label_step5.pack(fill='both', pady=20)
        btn_getrainqaqc = tk.Button(label_step5, text='Create Rain QAQC (need coordination list and processed xlsx)',
                                    font=('Helvetica', 12), command=create_rain_qaqc)
        btn_getrainqaqc.pack(side='left', fill='x', expand=True, padx=5, ipady=5)

        btn_rain_visual = tk.Button(label_step5, text='Rain Visualization (need rain QAQC sheet)',
                                    font=('Helvetica', 12), command=rain_visual)
        btn_rain_visual.pack(side='left', fill='x', expand=True, padx=5, ipady=5)


 #--------------------------------------------------------------------------------------------------------------------------
        button = tk.Button(self, text="Go to the Menu Page",
                           command=lambda: controller.show_frame("StartPage"),font=('Helvetica', 20, 'bold') )
        button.pack(pady=10, expand=True)

#--------------------------------------------------------------------------------------------------------------------
class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        def savefolderpath():
            save_folder = tkinter.filedialog.askdirectory()
            entry_savefolder.insert(0, f'{save_folder}')

        def get_img():
            project_id = proj_var.get()
            savepath = savefolder_var.get()
            download_img(project_id, savepath)

        def get_install_kmz():
            save_folder = savefolder_var.get()
            project_id = proj_var.get()
            get_install_kmz_func(save_folder, project_id)


        proj_var = tk.StringVar(self)
        savefolder_var = tk.StringVar(self)

        # ========================Pages Layout===========================================
        headinglabel1 = tk.Label(self, text="Field Reconn Data Download and Processing",
                                 font=('Helvetica', 45, "bold"),
                                 foreground='white',
                                 background='#add8e6')
        headinglabel1.pack(side="top", fill="x", pady=10)

        space_label1 = tk.Label(self, height=3)
        space_label1.pack()

        label_step1 = tk.LabelFrame(self, borderwidth=2,
                                    text='Define project No. and save folder',
                                    font=('Helvetica', 15), height=200, padx=20, pady=10, )
        label_step1.pack(fill='x', ipady=20, ipadx=20)
        label_input_proj = tk.Label(label_step1, text='Input Project Number', font=('Helvetica', 12))
        entry_proj = tk.Entry(label_step1, font=('Helvetica', 10), textvariable=proj_var)

        label_input_proj.pack(side='left', padx=10)
        entry_proj.pack(side='left', fill='x', expand=True, padx=10, ipady=5)

        btn_savefolder = tk.Button(label_step1,text='Save to Folder',font=('Helvetica', 12),command=savefolderpath)
        btn_savefolder.pack(side='left', padx=10)
        entry_savefolder = tk.Entry(label_step1, width=70, textvariable=savefolder_var)
        entry_savefolder.pack(side='left', fill='x', expand=True, padx=10, ipady=5)

        button_img_dl = tk.Button(self, text="Image Downloading",command=get_img,
                               font=('Helvetica', 15, 'bold'))
        button_img_dl.pack(pady=10)

        button_kmz_dl = tk.Button(self, text="Installed KMZ Downloading", command=get_install_kmz,
                                  font=('Helvetica', 15, 'bold'))
        button_kmz_dl.pack(pady=10)

        button = tk.Button(self, text="Go to the Menu Page",
                           command=lambda: controller.show_frame("StartPage"),font=('Helvetica', 20, 'bold'))
        button.pack(pady=20, expand=True)

class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        headinglabel1 = tk.Label(self, text="Flow QAQC Sheet Processing",
                                 font=('Helvetica', 45, "bold"),
                                 foreground='white',
                                 background='#add8e6')
        headinglabel1.pack(side="top", fill="x", pady=10)
        label_step1 = tk.LabelFrame(self, borderwidth=2,
                                    text='ADWF Calculation',
                                    font=('Helvetica', 15), height=200, padx=20, pady=10, )
        label_step1.pack(fill='x', ipady=20, ipadx=20)

        btn_dash = tk.Button(label_step1, text='Initial ADWF Analysis App', font=('Helvetica', 12),command=initial_dash)
        btn_dash.pack(side='left', padx=10)

        button = tk.Button(self, text="Go to the Menu Page",
                           command=lambda: controller.show_frame("StartPage"), font=('Helvetica', 20, 'bold'))
        button.pack(pady=20, expand=True)

class PageFour(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        headinglabel1 = tk.Label(self, text="DataBase Creation Assisting Tools",
                                 font=('Helvetica', 45, "bold"),
                                 foreground='white',
                                 background='#add8e6')
        headinglabel1.pack(side="top", fill="x", pady=10)
        label_step1 = tk.LabelFrame(self, borderwidth=2,
                                    text='Creating Site Info for DB Spread Sheet (make sure no empty space',
                                    font=('Helvetica', 15), height=200, padx=20, pady=10, )
        label_step1.pack(fill='x', ipady=20, ipadx=20)

        btn_tab1 = tk.Button(label_step1, text='Step 1: Fill tab Site Info for Rpt', font=('Helvetica', 12),command=run_db_tab1)
        btn_tab1.pack(side='left', padx=10)

        btn_tab2 = tk.Button(label_step1, text='Step 2: Fill tab Info for DB and Missing Photos ',
                             font=('Helvetica', 12),
                             command=run_db_tab2)
        btn_tab2.pack(side='left', padx=10)

        button = tk.Button(self, text="Go to the Menu Page",
                           command=lambda: controller.show_frame("StartPage"), font=('Helvetica', 20, 'bold'))
        button.pack(pady=20, expand=True)


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()






