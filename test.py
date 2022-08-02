import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from win32com import client
from win32com.client import Dispatch, constants

# excel_path = r'C:\Users\PXie\Documents\Python Projects\FTT\AWDF\21-0248\RAW DATA\21-0248 Rohnert Park Site 1 (8).xlsx'
# df_path = r'C:\Users\PXie\Documents\Python Projects\FTT\AWDF\21-0248\RAW DATA\ADWF.csv'
# df = pd.read_csv(df_path)
#
# excelApp = client.gencache.EnsureDispatch("Excel.Application")
#
# wb = excelApp.Workbooks.Open(excel_path)
# excelApp.Visible = True
#
# if 'python_adwf' not in [wb.Sheets(i).Name for i in range(1,wb.Sheets.Count+1)]:
#     print('Creating Python adwf worksheet')
#     ws = wb.Worksheets.Add(wb.Sheets(4))
#     ws.Name = 'python_adwf'
# else:
#     print('python_adwf already exists. Pre-existing Data will be overwritten')
#
#
# ws.Range(ws.Cells(1, 1),  # Cell to start the "paste"
#          ws.Cells(1,1 + df.shape[1] - 1)
#          ).Value = df.columns
# ws.Range(ws.Cells(2, 1),  # Cell to start the "paste"
#          ws.Cells(1+df.shape[0] - 1,
#                   1 + df.shape[1] - 1)
#          ).Value = df.values
# wb.Save()


