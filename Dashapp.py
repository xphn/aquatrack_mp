
from dash import Dash, dcc, html, Input, Output,dash_table,callback_context
from ADWF_FUNCTIONS import *
import dash_bootstrap_components as dbc
import pandas as pd
from pathlib import Path
from dash.exceptions import PreventUpdate

def FFT_App(excel_path,flow_df,rain_df, port):
    # port = random.randint(1000,9999)
    app = Dash(__name__,  external_stylesheets=[dbc.themes.FLATLY],
               suppress_callback_exceptions=True)
    Time_list = list(set(flow_df['Datetime'].dt.date.tolist()))
    Time_list.sort()
    file_name = Path(excel_path)
    file_name = file_name.stem


    # styling the sidebar
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    # padding for the page content
    CONTENT_STYLE = {
        "margin-left": "18rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    sidebar = html.Div(
        [
            html.H2("Sidebar", className="display-4"),
            html.Hr(),
            html.P(
                "Choose the Page", className="lead"
            ),
            dbc.Nav(
                [
                    dbc.NavLink("Flow Graph", href="/", active="exact"),
                    dbc.NavLink("ADWF Date Pick", href="/page-1", active="exact"),
                    dbc.NavLink("ADWF Daily Average", href="/page-2", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

    app.layout = html.Div([
        dcc.Location(id="url"),
        sidebar,
        dcc.Store(id='stored_flow_data',storage_type='session'),
        dcc.Store(id='stored_selected_dates',storage_type='session'),
        dcc.Store(id='stored_dropdown_choice', storage_type='session'),
        content])

    @app.callback((
            Output('stored_flow_data','data'),
            [Input('FFT Filter Level','value'),
             Input('flow_date_picker_range','start_date'),
             Input('flow_date_picker_range','end_date'),]
    ))
    def flow_df_store(percentile_to_remove,start_date, end_date):
        flow_dff = flow_df.loc[(flow_df['Datetime'] >= start_date) & (flow_df['Datetime'] <= end_date)].copy()
        rain_dff = rain_df.loc[(rain_df['Datetime'] >= start_date) & (rain_df['Datetime'] <= end_date)].copy()
        flow_dff = fft_filter(flow_dff, percentile_to_remove=percentile_to_remove, fhat_fld='fhat')
        holidays = get_holidays(flow_dff)
        rain_day = get_rain_days(rain_dff)
        date_to_remove_default = (holidays + rain_day)
        date_to_remove_default = [i.strftime('%Y-%m-%d') for i in date_to_remove_default]
        flow_df_days_selected = adwf_date_removal(flow_dff, date_to_remove_default)
        return [flow_df_days_selected.to_dict('records')]


    @app.callback((
            Output('diurnal_pattern_by_days',"figure"),
            [Input('stored_flow_data','data'),
             Input('dates_checklist','value')]
    ))
    def page_1_plot(data, option_chosen):
        flow_df = pd.DataFrame(data)
        flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
        flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(option_chosen)]
        adwf_df = adwf_process(flow_df)
        return [awdf_by_day(adwf_df)]

    @app.callback((
            Output('checklist', "children"),
            Input('stored_flow_data', 'data'),

    ))
    def dates_checklist(data):
        flow_df = pd.DataFrame(data)
        flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
        date_list = list(set(flow_df['Datetime'].dt.date.tolist()))
        date_list.sort()
        return [
            dcc.Checklist(
                id='dates_checklist',
                options = [{'label': x, 'value':x,'disabled':False} for x in date_list],
                value = date_list,
                inputStyle={"margin-right": "10px","margin-left": "10px"},
                persistence=True,
                persistence_type='session'
            )
        ]

    @app.callback((
            Output('stored_selected_dates','data'),
            [Input('dates_checklist','value')],
    ))
    def store_dates_selected(option_chosen):
        return [option_chosen]

    @app.callback(
        Output('page-content','children'),
        Input('url','pathname')
    )
    def render_page_content(pathname):
        if pathname == '/':
            return[
                html.H1('Average Dry Weather Flow Analysis Dash Board'),
                html.H3(f'For Flow QAQC Sheet: {file_name}'),
                html.Br(),
                html.H4('Select start and end date for the study period'),
                dcc.DatePickerRange(
                    id='flow_date_picker_range',
                    min_date_allowed=Time_list[0],
                    max_date_allowed=Time_list[-1]+timedelta(hours=24),
                    start_date=Time_list[0],
                    end_date=Time_list[-1]+ timedelta(hours=24),
                    minimum_nights=2,
                    updatemode='singledate',
                    persistence=True,
                    persistence_type='session'
                ),
                dcc.Graph(
                    id='flow-graph',
                    figure={},
                ),
                html.Div(html.P(
                    ['Inserting FFT Filter Level. ',
                    html.Br(),
                    '1. put 0 if you want to turn off the Fourier Transformation Denoise Function',
                    html.Br(),
                    '2. For denoization, the FFT level is usually between [0.8, 0.9]. ',
                    html.Br(),
                    '3. To better view patterns, the best guess for the FFT level is usually at 0.95']
            )),
                dcc.Input(
                    id='FFT Filter Level',
                    type='number',
                    placeholder='Insert FFT Filter Level in [0.1]',
                    min=0, max=1, step=0.05,
                    size='60,',
                    value=0,
                    persistence=True,
                    persistence_type='session'
                ),
            ]
        elif pathname == "/page-1":
            return [
                html.H1('Average Dry Weather Flow Date Pick',
                        style={'textAlign': 'center'}),
                html.Br(),
                html.H4(children='''
                Uncheck the dates you don't want to use
                          '''),
                html.Div(id='checklist', children=[]),
                html.Br(),
                html.Div(dcc.Graph(id='diurnal_pattern_by_days',figure={}))
            ]
        elif pathname == "/page-2":
            return [dbc.Container(
                [
                    dbc.Row([
                        dbc.Col([
                            html.H1('Average Dry Weather Flow Stats', style={'textAlign': 'center'}),
                            html.Br(),
                            html.H4('Choose Descriptive Statistics'),
                            dcc.Dropdown(id='stat_dropdown',
                                         options=[{'label': x, 'value': x, 'disabled': False} for x in
                                                  ['max', 'min', 'median', 'mean']],
                                         value='mean',
                                         persistence=True,
                                         style={'width': '12rem'},
                                         clearable=False,
                                         persistence_type='session'
                                         ),
                            html.Div(dcc.Graph(id='adwf_points', figure={})),
                            html.Br(),
                            html.H3('Average Dry Weather Flow Values', style={'textAlign': 'center'}),
                            html.Div(id='adwf_table', children=[]),
                            html.Br(),
                            html.H3('Daily Average Table', style={'textAlign': 'center'}),
                            html.Div(id='dav_table', children=[]),
                            html.Br(),
                        ],width=12)

                    ]),
                    dbc.Row([
                        dbc.Col([
                            # html.Button("Download CSV", id="btn_csv", style={'color': 'primary'}),
                            dbc.Button("Download CSV", id="btn_csv", color= 'primary', className='me-1'),
                            dcc.Download(id="download-dataframe-csv"),
                        ],width =4),
                        dbc.Col([
                            # html.Button("Download CSV", id="btn_csv", style={'color': 'primary'}),
                            dbc.Button("Write_to_Excel", id="btn_excel", color='primary', className='me-1'),
                            dcc.Download(id="write-df_to_excel"),
                        ], width=4)
                    ])

                ]
            )
            ]


    @app.callback((Output('adwf_points','figure'),
                   Input('stored_flow_data', 'data'),
                   Input('stored_selected_dates', 'data'),
                   Input('stat_dropdown', 'value') ))
    def chang_stats(data, selected_dates, stat):
        flow_df = pd.DataFrame(data)
        flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
        flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
        adwf_df = adwf_process(flow_df)
        adwf_df_no_outlier = adwf_outlier_removal(adwf_df)  # remove outliers
        adwf_df = adwf_get_stats_for_each_time(adwf_df)
        adwf_df_no_outlier = adwf_get_stats_for_each_time(adwf_df_no_outlier)
        return [adwf_visualize(adwf_df, adwf_df_no_outlier,stat)]

    @app.callback((Output('adwf_table','children'),
                   Input('stored_flow_data', 'data'),
                   Input('stored_selected_dates', 'data'),
                   Input('stat_dropdown', 'value') ))
    def adwf_table(data, selected_dates, stat):
        flow_df = pd.DataFrame(data)
        flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
        flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
        adwf_df = adwf_process(flow_df)
        adwf_df_no_outlier = adwf_outlier_removal(adwf_df)  # remove outliers
        adwf_df_no_outlier = adwf_get_stats_for_each_time(adwf_df_no_outlier)
        adwf_no_outlier_pivot = pd.pivot_table(adwf_df_no_outlier, columns=['type_day'],
                                               aggfunc='mean', values=[stat])
        adwf_no_outlier_pivot.reset_index(inplace=True)
        adwf_no_outlier_pivot = adwf_no_outlier_pivot[['index','Weekdays','Friday','Saturday','Sunday']]
        adwf_no_outlier_pivot = adwf_no_outlier_pivot.round(6)
        return [ dash_table.DataTable(
            id = 'summary_table',
            data = adwf_no_outlier_pivot.to_dict('records'),
            columns=[{"name": i, "id": i} for i in adwf_no_outlier_pivot.columns],
            style_table={
                'width': '90%',
                'margin': 'auto'},
        )
        ]

    @app.callback((Output('dav_table','children'),
                   Input('stored_flow_data', 'data'),
                   Input('stored_selected_dates', 'data'),
                   Input('stat_dropdown', 'value') ))
    def dav_table(data, selected_dates, stat):
        flow_df = pd.DataFrame(data)
        flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
        flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
        adwf_df = adwf_process(flow_df)
        adwf_df_no_outlier = adwf_outlier_removal(adwf_df)  # remove outliers
        adwf_df_no_outlier = adwf_get_stats_for_each_time(adwf_df_no_outlier)
        adwf_no_outlier_pivot = pd.pivot_table(adwf_df_no_outlier, columns=['type_day'], index=['time'],
                                               aggfunc=np.mean,values=[stat])
        adwf_no_outlier_pivot.columns = [f'{x[0]}_{x[1]}' for x in adwf_no_outlier_pivot.columns]
        adwf_no_outlier_pivot = adwf_no_outlier_pivot.round(6)
        adwf_no_outlier_pivot.reset_index(inplace=True)
        adwf_no_outlier_pivot = adwf_no_outlier_pivot[['time', f'{stat}_Weekdays', f'{stat}_Friday', f'{stat}_Saturday', f'{stat}_Sunday']]
        return [ dash_table.DataTable(
            id = 'dash_table',
            data = adwf_no_outlier_pivot.to_dict('records'),
            columns=[{"name": i, "id": i} for i in adwf_no_outlier_pivot.columns],
            style_table={
                'width': '90%',
                'margin': 'auto'},
        )
        ]

    @app.callback((
            Output('stored_dropdown_choice', 'data'),
            [Input('stat_dropdown', 'value')],
    ))
    def store_dropdown(choice):
        return [choice]

    @app.callback(
        Output("download-dataframe-csv", "data"),
        [Input('stored_flow_data', 'data'),
         Input('stored_selected_dates', 'data'),
         Input('stored_dropdown_choice', 'data'),
         Input("btn_csv", "n_clicks"),
         ],
        prevent_initial_call=True,
    )
    def func(data,selected_dates,stat, n_clicks):
        # if n_clicks is None:
        #     raise PreventUpdate
        # stat ='mean'
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if button_id == "btn_csv":
                flow_df = pd.DataFrame(data)
                flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
                flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
                adwf_df = adwf_process(flow_df)
                adwf_df_no_outlier = adwf_outlier_removal(adwf_df)  # remove outliers
                adwf_df_no_outlier = adwf_get_stats_for_each_time(adwf_df_no_outlier)
                adwf_no_outlier_pivot = pd.pivot_table(adwf_df_no_outlier, columns=['type_day'],
                                                       index=['time'],aggfunc=np.mean, values=[stat])
                adwf_no_outlier_pivot.columns = [f'{x[0]}_{x[1]}' for x in adwf_no_outlier_pivot.columns]
                adwf_no_outlier_pivot.reset_index(inplace=True)
                return dcc.send_data_frame(adwf_no_outlier_pivot.to_csv,'ADWF.csv')
            else:
                raise PreventUpdate

    @app.callback(
        Output("write_df_to_excel", "data"),
        [Input('stored_flow_data', 'data'),
         Input('stored_selected_dates', 'data'),
         Input('stored_dropdown_choice', 'data'),
         Input("btn_excel", "n_clicks"),
         ],
        prevent_initial_call=True,
    )
    def write_to_excel(data, selected_dates, stat, n_clicks):
        # if n_clicks is None:
        #     raise PreventUpdate
        # stat ='mean'
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if button_id == "btn_excel":
                flow_df = pd.DataFrame(data)
                flow_df['Datetime'] = pd.to_datetime(flow_df['Datetime'], errors='coerce')
                flow_df = flow_df[flow_df['Datetime'].dt.strftime('%Y-%m-%d').isin(selected_dates)]
                adwf_df = adwf_process(flow_df)
                adwf_df_no_outlier = adwf_outlier_removal(adwf_df)  # remove outliers
                adwf_df_no_outlier = adwf_get_stats_for_each_time(adwf_df_no_outlier)
                adwf_no_outlier_pivot = pd.pivot_table(adwf_df_no_outlier, columns=['type_day'],
                                                       index=['time'], aggfunc=np.mean, values=[stat])
                adwf_no_outlier_pivot.columns = [f'{x[0]}_{x[1]}' for x in adwf_no_outlier_pivot.columns]
                adwf_no_outlier_pivot.reset_index(inplace=True)
                write_to_excel(excel_path, adwf_no_outlier_pivot)
                return
            else:
                raise PreventUpdate

    #
    @app.callback(
        Output(component_id='flow-graph',component_property='figure'),
        [Input('flow_date_picker_range','start_date'),
         Input('flow_date_picker_range','end_date'),
         Input('FFT Filter Level','value')]
    )
    def update_output(start_date, end_date, percentile_to_remove):
        flow_dff = flow_df.loc[(flow_df['Datetime'] >= start_date) & (flow_df['Datetime'] <= end_date)].copy()
        rain_dff = rain_df.loc[(rain_df['Datetime'] >= start_date) & (rain_df['Datetime'] <= end_date)].copy()
        flow_dff = fft_filter(flow_dff, percentile_to_remove=percentile_to_remove, fhat_fld='fhat')
        fig = flow_plot(flow_dff, rain_dff, depth_fld='Level', velocity_fld='Velocity',
                          rainfall_fld='Rain Rate (in/hr)',
                          flow_fld='Flow',percentile_to_remove = percentile_to_remove, depth_unit='in',
                          flow_unit='mgd', velocity_unit='fps')
        return fig

    app.run_server(port=port, debug=False)