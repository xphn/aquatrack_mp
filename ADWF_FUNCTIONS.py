import numpy as np
import pandas as pd
import plotly.graph_objects as go
import datetime
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import timedelta
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
from win32com import client

def read_flow_csv(path):
    df = pd.read_csv(path,parse_dates=[0])
    df = df.dropna(subset=['Flow'])
    return df


def rain_data(path):
    df = pd.read_csv(path, parse_dates=[0])
    df = df.dropna()
    return df

def read_flow_rain_from_excel(excel_path):
    raw_df = pd.read_excel(excel_path, sheet_name='15', skiprows=17,
                           usecols=['Date/Time', 'Lev 15', 'Vel 15', 'Flo 15', 'Rain Rate (in/hr)'],
                           parse_dates=[0])
    raw_df.rename(columns={'Date/Time': 'Datetime'}, inplace=True)
    raw_df['Datetime'] = pd.to_datetime(raw_df['Datetime'], errors='coerce')
    raw_df['Datetime'] = raw_df['Datetime'].apply(lambda x: x.round('1min'))

    first_valid = raw_df[raw_df['Lev 15'].notnull()].index[0]
    last_valid = raw_df[raw_df['Lev 15'].notnull()].index[-1]
    raw_df = raw_df.copy().iloc[first_valid:last_valid + 1]
    # raw_df.set_index('Datetime', inplace=True)

    flow_df = raw_df.copy()[['Datetime','Lev 15', 'Vel 15', 'Flo 15']]
    flow_df.rename(columns={'Lev 15': 'Level',
                                'Vel 15': 'Velocity',
                                'Flo 15': 'Flow'}, inplace=True)

    rain_df = raw_df.copy()[['Datetime','Rain Rate (in/hr)']]
    return flow_df, rain_df

def get_holidays(rain_df):
    cal = calendar()
    holidays = cal.holidays(start = rain_df['Datetime'].dt.date.min(), end = rain_df['Datetime'].dt.date.max())
    return holidays.to_list()

def get_rain_days(rain_df):
    rain_sum_by_day = rain_df.groupby(rain_df['Datetime'].dt.date).sum()
    rain_day = rain_sum_by_day[rain_sum_by_day['Rain Rate (in/hr)'] >0.05].index.to_list()
    for i in range(len(rain_day)):
        if (rain_day[i] + timedelta(hours=24)) not in rain_day:
            rain_day.append(rain_day[i] + timedelta(hours=24))
    return rain_day

def change_data_range(df, start=None, end=None):
    """

    :param df:
    :param start: start time in the format like '2022-03-02'
    :param end: end time in the format like '2022-03-02'
    :return:
    """
    df = df.copy()
    if start:
        start = datetime.datetime.strptime(start, '%Y-%m-%d')
        df = df.copy().loc[start:]

    elif end:
        end = datetime.datetime.strptime(end, '%Y-%m-%d')
        df = df.copy().loc[:end]
    return df



def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = 'percentile_%s' % n
    return percentile_


def fft_transform(flow_df,flow_fld,time_interval):
    if flow_df[flow_fld].isnull().values.any():
        raise ValueError('The data has nans. Thus unable to perform FFT')

    flow = flow_df[flow_fld].astype(float).values
    dt = (time_interval * 60)
    N = flow_df.shape[0]
    t = np.linspace(0, N * dt, N)
    fhat = np.fft.fft(flow, N)  # compute FFT
    PSD = fhat * np.conj(fhat) / N  # compute POWER SPECTRUM
    freq = np.arange(N) / (N * dt)
    # L = np.arange(0, np.floor(N / 2), dtype='int')  # the first half of the spectrum
    t_h = 1 / freq / (60 * 60)

    fft_df = pd.DataFrame.from_dict(dict(zip(freq, PSD.real)), orient='index', columns=['PSD'])
    fft_df.reset_index(inplace=True)
    fft_df.rename(columns={'index':'Freq(Hz)'}, inplace=True)
    fft_df['hours'] = t_h
    fft_df['fhat'] = fhat

    return fft_df


def flow_plot(flow_df, rain_df,depth_fld, velocity_fld, rainfall_fld, flow_fld,percentile_to_remove, depth_unit='in',
              flow_unit='mgd', velocity_unit='fps'):
    rain_df = rain_df.copy()
    flow_df = flow_df.copy()
    holidays = get_holidays(rain_df)
    rain_days = get_rain_days(rain_df)

    rain_df['_rainfall'] = rain_df[rainfall_fld]
    flow_df['_flow'] = flow_df[flow_fld]
    flow_df['_depth'] = flow_df[depth_fld]
    flow_df['_velocity'] = flow_df[velocity_fld]
    fig = make_subplots(rows=3, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.01,
                        row_heights=[0.2, 0.4, 0.6],
                        specs=[[{"secondary_y": False}], [{"secondary_y": True}], [{"secondary_y": False}]])

    fig.add_trace(go.Scatter(
        x=rain_df['Datetime'],
        y=rain_df['_rainfall'],
        name='rainfall',
        line_shape='hv',
        fill='tozeroy',
        line=dict(color='blue', width=1)

    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=flow_df['Datetime'],
        y=flow_df._depth,
        name='Level',
        line=dict(color='purple')
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=flow_df['Datetime'],
        y=flow_df._velocity,
        name='Velocity',
        line=dict(color='green', dash='dot')

    ), row=2, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(
        x=flow_df['Datetime'],
        y=flow_df._flow,
        name='Flow',
        line=dict(color='blue')
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=flow_df['Datetime'],
        y=flow_df['FFT_aproxd_flow'],
        name=f'FFT_Approxed_Flow_{percentile_to_remove}',
        line=dict(color='red')
    ), row=3, col=1)

    for i in range(len(holidays)):
        fig.add_vrect(x0=holidays[i], x1 = holidays[i]+ timedelta(hours=24),
                      fillcolor = 'purple', opacity =0.15, line_width =0)

    for i in range(len(rain_days)):
        fig.add_vrect(x0=rain_days[i], x1=rain_days[i] + timedelta(hours=24),
                      fillcolor='blue', opacity=0.15, line_width=0)


    fig['layout']['yaxis1'].update(autorange="reversed",
                                   title='Rainfall (in/hr)')
    fig['layout']['yaxis2'].update(title='Depth(%s)' % depth_unit)
    fig['layout']['yaxis3'].update(title='Velocity(%s)' % velocity_unit)
    fig['layout']['yaxis4'].update(title='Flow(%s)' % flow_unit)

    fig.update_layout(
        height=800, width=1200,
        title_text="Flow Data Plot",
        xaxis3_rangeslider_visible=True,
        xaxis3_rangeslider_thickness=0.1)
    # fig.show()
    return fig


def plot_fft(fft_df,freq_fld, PSD_fld, hour_fld, title='Pre_FFT_Filter Flow data in Frequency Domain'):
    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=False,
                        vertical_spacing=0.1,
                        row_heights=[0.5, 0.5])

    fig.add_trace(go.Scatter(
        x=fft_df[freq_fld][np.arange(0, np.floor(fft_df.shape[0] / 2), dtype='int')],
        y=fft_df[PSD_fld][np.arange(0, np.floor(fft_df.shape[0] / 2), dtype='int')],
        name='In Frequency (Hertz)',
        line=dict(color='red')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=fft_df[hour_fld][np.arange(1, np.floor(fft_df.shape[0] / 2), dtype='int')],
        y=fft_df[PSD_fld][np.arange(1, np.floor(fft_df.shape[0] / 2), dtype='int')],
        name='In Hours',
        line=dict(color='blue')
    ), row=2, col=1)

    fig.update_layout(
        height=800, width=1200,
        title_text=title)
    # fig.show()


def fft_filter(flow_df, percentile_to_remove, fhat_fld):
    fft_df = fft_transform(flow_df, 'Flow', 15)  # 15 min interval
    # plot_fft(fft_df, freq_fld='Freq(Hz)', PSD_fld='PSD',hour_fld='hours')

    PSD = fft_df['PSD']
    # In experience, the best starting point is over 95 percentile
    percentile_to_remove = percentile_to_remove
    best_guess = fft_df['PSD'].quantile(percentile_to_remove)
    mask = (PSD > best_guess)
    indices = mask
    PSDfilter = PSD * indices
    fhat_filter = indices * fft_df[fhat_fld]
    ffilter = np.fft.ifft(fhat_filter)
    fft_df['PSD_filtered'] = PSDfilter
    plot_fft(fft_df, freq_fld='Freq(Hz)', PSD_fld='PSD_filtered',hour_fld='hours',
             title='Post_FFT_Filter Flow data in Frequency Domain')
    flow_df['FFT_aproxd_flow'] = ffilter.real
    flow_df.loc[flow_df['FFT_aproxd_flow'] < 0, 'FFT_aproxd_flow'] = 0  # remove the negative flow data
    return flow_df


def plot_pre_post(flow_df, flow_fig,percentile_to_remove):
    fig = flow_fig
    fig.add_trace(go.Scatter(
        x=flow_df.index,
        y=flow_df['FFT_aproxd_flow'],
        name=f'FFT_Approxed_Flow_{percentile_to_remove}',
        line=dict(color='red')
    ), row=3, col=1)
    # fig.show()
    return fig


def adwf_process(flow_df):
    flow_df = flow_df.copy()
    flow_df = flow_df.dropna(subset = ['FFT_aproxd_flow'])
    flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
    flow_df['date'] = flow_df['Datetime'].dt.date
    flow_df['dow'] = flow_df['Datetime'].dt.dayofweek
    flow_df['wkno'] = flow_df['Datetime'].dt.isocalendar().week
    flow_df['time'] = flow_df['Datetime'].dt.time
    flow_df['hour'] = flow_df['Datetime'].dt.hour
    flow_df.loc[flow_df['dow']<4, 'type_day'] = 'Weekdays'
    flow_df.loc[flow_df['dow']==4, 'type_day'] = 'Friday'
    flow_df.loc[flow_df['dow']==5, 'type_day'] = 'Saturday'
    flow_df.loc[flow_df['dow']==6, 'type_day'] = 'Sunday'
    # flow_df['flow_derivative'] = flow_df['FFT_aproxd_flow'].diff()

    flow_df_grp = flow_df.groupby(by=['type_day', 'time']).agg({
        'FFT_aproxd_flow': [percentile(25), percentile(50), percentile(75)]
    })
    flow_df_grp.columns = [f"{col[0]}_{col[1]}" for col in flow_df_grp.columns]
    adwf_df_grp = flow_df_grp.reset_index()

    flow_df = flow_df.merge(adwf_df_grp, on=['type_day', 'time'])
    # flow_df_outlier_removed = adwf_outlier_removal(flow_df) #remove outliers

    # flow_df = adwf_get_average_for_each_time(flow_df)
    # flow_df_outlier_removed = adwf_get_average_for_each_time(flow_df_outlier_removed)
    return flow_df

def awdf_by_day(adwf_df):

    fig = px.scatter(adwf_df.sort_values(by=['time','wkno']), x='time', y=['FFT_aproxd_flow']
                     , color='date',facet_col='type_day',facet_col_wrap=2,
                     category_orders={'type_day':['Weekdays','Friday','Saturday','Sunday']})

    fig.update_layout(
        height=800, width=1200,
        title_text="Average Dry Weather Flow")
    # fig.show()
    return fig


def adwf_box_plot(df):
    fig = px.box(df.sort_values(by=['time','wkno']), x='time', y='FFT_aproxd_flow',facet_col='type_day',facet_col_wrap=2 )
    fig.update_layout(
        height=800, width=1000,
        title_text="Average Dry Weather Flow Boxplot")
    fig.show()

def adwf_outlier_removal(adwf_df):
    adwf_df[f'FFT_aproxd_flow_IQR'] = (adwf_df[f'FFT_aproxd_flow_percentile_75'] - adwf_df[f'FFT_aproxd_flow_percentile_25'])
    # adwf_df['flow_derivative_IQR'] = (adwf_df.flow_derivative_percentile_75 - adwf_df.flow_derivative_percentile_25)
    mask_select = ((adwf_df['FFT_aproxd_flow'] >= (adwf_df[f'FFT_aproxd_flow_percentile_25'] - 1.5 * adwf_df[f'FFT_aproxd_flow_IQR'])) &
                   (adwf_df['FFT_aproxd_flow'] <= (adwf_df[f'FFT_aproxd_flow_percentile_75'] + 1.5 * adwf_df[f'FFT_aproxd_flow_IQR'])))
    adwf_df_no_outlier = adwf_df[mask_select]
    return adwf_df_no_outlier

def adwf_get_stats_for_each_time(adwf_df):
    adwf_df_grp = adwf_df[['type_day', 'time', 'FFT_aproxd_flow']].groupby(by=['type_day', 'time']).agg(
        ['min', 'max', 'median', 'mean'])
    adwf_df_grp = adwf_df_grp.reset_index()
    adwf_df_grp.columns = ['type_day', 'time', 'min', 'max', 'median', 'mean']
    adwf_df = adwf_df.merge(adwf_df_grp, on=['type_day', 'time'])
    return adwf_df

def adwf_get_type_day_df(df):
    """
    :param df:
    :return: sub dataframes based on tyep of days
    """
    weekdays = df.copy().loc[df['dow']<4, :]
    fridays = df.copy().loc[df['dow']==4, :]
    saturdays = df.copy().loc[df['dow']==5, :]
    sundays = df.copy().loc[df['dow']==6, :]
    return weekdays,fridays,saturdays,sundays


def adwf_visualize(adwf_df, adwf_df_filtered, stat):
    weekdays, fridays, saturdays, sundays = adwf_get_type_day_df(adwf_df) # types of days with outliers
    df_list = [weekdays, fridays, saturdays, sundays]

    weekdays_filtered, fridays_filtered, saturdays_filtered, sundays_filtered = adwf_get_type_day_df(adwf_df_filtered) #types of days without outliers
    filtered_df_list = [weekdays_filtered, fridays_filtered, saturdays_filtered, sundays_filtered]

    sorted_df_list = [x.sort_values(by=['time', 'wkno']) for x in df_list]
    sorted_filtered_df_list = [x.sort_values(by=['time', 'wkno']) for x in filtered_df_list]

    fig = make_subplots(rows=2, cols=2,
                        shared_xaxes=True,
                        shared_yaxes=True,
                        vertical_spacing=0.1,
                        row_heights=[0.6, 0.6],
                        subplot_titles=('Weekdays','Fridays','Saturdays','Sundays'))

    for i in range(len(df_list)):
        fig.add_trace(go.Scatter(
            x=sorted_df_list[i].time,
            y=sorted_df_list[i]['FFT_aproxd_flow'],
            name=sorted_df_list[i]['type_day'].values[0] + '_with_outliers',
            mode='markers',
            marker=dict(color='gray'),
            hovertemplate='Datetime: %{x} <br>Flow: %{y}',
        ), col=(i % 2) + 1, row=(i // 2) + 1)

        fig.add_trace(go.Scatter(
            x=sorted_filtered_df_list[i].time,
            y=sorted_filtered_df_list[i]['FFT_aproxd_flow'],
            name=sorted_filtered_df_list[i]['type_day'].values[0] + '_without_outliers',
            mode='markers',
            marker=dict(color='#7fffd4'),
            hovertemplate='Datetime: %{x} <br>Flow: %{y}'
        ), col=(i % 2) + 1, row=(i // 2) + 1)

        fig.add_trace(go.Scatter(
            x=sorted_filtered_df_list[i].time,
            y=sorted_filtered_df_list[i][stat],
            name=sorted_df_list[i]['type_day'].values[0] + f'_{stat}',
            line=dict(color='orange', width=2)
        ), col=(i % 2) + 1, row=(i // 2) + 1)

        # fig.add_trace(go.Scatter(
        #     x=sorted_filtered_df_list[i].time,
        #     y=sorted_filtered_df_list[i]['max'],
        #     name=sorted_filtered_df_list[i]['type_day'].values[0] + '_max',
        #     line=dict(color='red', width=4)
        # ), col=(i % 2) + 1, row=(i // 2) + 1)
        #
        # fig.add_trace(go.Scatter(
        #     x=sorted_filtered_df_list[i].time,
        #     y=sorted_filtered_df_list[i][f'median'],
        #     name=sorted_filtered_df_list[i]['type_day'].values[0] + '_median',
        #     line=dict(color='blue', width=4)
        # ), col=(i % 2) + 1, row=(i // 2) + 1)
        #
        # fig.add_trace(go.Scatter(
        #     x=sorted_filtered_df_list[i].time,
        #     y=sorted_filtered_df_list[i][f'mean'],
        #     name=sorted_df_list[i]['type_day'].values[0] + '_mean',
        #     line=dict(color='orange', width=4)
        # ), col=(i % 2) + 1, row=(i // 2) + 1)

        fig.update_layout(
            height=800, width=1200,
            title_text="Average Dry Weather Flow")
    # fig.show()
    return fig


def adwf_date_removal(flow_df, dates_to_remove):
    flow_df['date'] = flow_df['Datetime'].dt.date
    dates_to_remove = [datetime.datetime.strptime(x, '%Y-%m-%d').date() for x in dates_to_remove]
    flow_df = flow_df[~flow_df['date'].isin(dates_to_remove)]
    return flow_df

def adwf_calculation(dfs_list,remove_date_or_not=True,filter_or_not =True, median_or_average ='average'):
    adwf_df = dfs_list[0]
    adwf_df_filtered = dfs_list[1]
    adwf_df_date_remvd = dfs_list[2]
    adwf_df_filtered_date_remvd = dfs_list[3]

    if remove_date_or_not:
        if filter_or_not:
            df = adwf_df_filtered_date_remvd
        else:
            df = adwf_df_date_remvd
    else:
        if filter_or_not:
            df = adwf_df_filtered
        else:
            df = adwf_df

    if median_or_average == 'average':
        field = 'FFT_aproxd_flow_average_by_time'
    elif median_or_average == 'median':
        field = 'FFT_aproxd_flow_percentile_50'
    else:
        print('Wrong parameter')
        print('-----------------Choose again-------------------')
        return

    weekdays, fridays, saturdays, sundays = adwf_get_type_day_df(df)
    overall_adwf = df[field].mean()
    weekdays_adwf = weekdays[field].mean()
    fridays_adwf = fridays[field].mean()
    saturdays_adwf = saturdays[field].mean()
    sundays_adwf = sundays[field].mean()

    print(f'overall_adwf is: {overall_adwf}')
    print(f'weekday_adwf is: {weekdays_adwf}')
    print(f'friday_adwf is: {fridays_adwf}')
    print(f'saturday_adwf is: {saturdays_adwf}')
    print(f'sundays_adwf is: {sundays_adwf}')
    return overall_adwf, weekdays_adwf, fridays_adwf, saturdays_adwf, sundays_adwf

def write_to_excel(excel_path, df):
    # excel_path = r'C:\Users\PXie\Documents\Python Projects\FTT\AWDF\21-0248\RAW DATA\21-0248 Rohnert Park Site 1 (8).xlsx'
    # df_path = r'C:\Users\PXie\Documents\Python Projects\FTT\AWDF\21-0248\RAW DATA\ADWF.csv'
    # df = pd.read_csv(df_path)

    excelApp = client.gencache.EnsureDispatch("Excel.Application")

    wb = excelApp.Workbooks.Open(excel_path)
    excelApp.Visible = True

    if 'python_adwf' not in [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]:
        print('Creating Python adwf worksheet')
        ws = wb.Worksheets.Add(wb.Sheets(4))
        ws.Name = 'python_adwf'
    else:
        print('python_adwf already exists. Pre-existing Data will be overwritten')

    ws.Range(ws.Cells(1, 1),  # Cell to start the "paste"
             ws.Cells(1, 1 + df.shape[1] - 1)
             ).Value = df.columns
    ws.Range(ws.Cells(2, 1),  # Cell to start the "paste"
             ws.Cells(1 + df.shape[0] - 1,
                      1 + df.shape[1] - 1)
             ).Value = df.values
    wb.Save()
