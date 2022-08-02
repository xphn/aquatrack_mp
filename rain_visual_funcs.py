import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.colors as colors
import pandas as pd
from PIL import Image
import glob
import pathlib
import re


def degree_to_decimal(EWSN):
    degree_str =  input('Input the coordination in the format of DD/MM/SSSS, [EWNS]:   ')
    deg, minutes, seconds, direction = re.split('[°\'"]+', degree_str)
    while direction != EWSN:
        print('--------------------Warning You have used the wrong type of coordination--------------------')
        degree_str = input('Input the coordination in the format of DD/MM/SSSS, [EWNS]:   ')
        deg, minutes, seconds, direction = re.split('[°\'"]+', degree_str)
    point = (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1)
    print(f'Convert it to: {point}')
    print('')
    print()

    return point




def simple_idw(x, y, z, xi, yi):
    dist = distance_matrix(x,y, xi,yi)

    # In IDW, weights are 1 / distance^2
    weights = 1.0 / dist**2

    # Make weights sum to one
    weights /= weights.sum(axis=0)

    # Multiply the weights for each interpolated point by all observed Z-values
    zi = np.dot(weights.T, z)
    return zi

def distance_matrix(x0, y0, x1, y1):
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T

    # Make a distance matrix between pairwise observations
    # Note: from <http://stackoverflow.com/questions/1871536>
    # (Yay for ufuncs!)
    d0 = np.subtract.outer(obs[:,0], interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])

    return np.hypot(d0, d1)

def plot(x,y,site_name,grid, xmin, xmax, ymin, ymax, vmin=0, vmax=0.1):
    #  for 2017-08-17 the vmax is 22
    fig, ax = plt.subplots(figsize=(12,12))
    # ax = boundary_poly.to_crs(epsg=4326).plot(edgecolor="black", color='none', figsize=(12,12),alpha=0.5)
    # ctx.add_basemap(ax, zoom= 10, source=ctx.providers.OpenStreetMap.Mapnik, crs=boundary_poly.crs )
    ax.scatter(x, y,  marker="^", facecolors="tab:red",label="Rain Gauges")
    for i, txt in enumerate(site_name):
        ax.annotate(txt, (x[i]+0.001, y[i]+0.001))

    plt.imshow(grid, extent=(xmin, xmax, ymax, ymin), cmap='Blues',alpha=0.65, norm=colors.PowerNorm(gamma=0.7))
    plt.clim(vmin, vmax)

    plt.xlabel("Longitude", fontsize=16)
    plt.ylabel("Latitude", fontsize=16)
    plt.legend(prop = {'size':14})

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=1)
    cb = plt.colorbar(cax=cax, alpha =1)
    cb.ax.tick_params(labelsize =12)
    cb.set_label('Rain(inch)',fontsize=16)
    return fig,ax

def get_rain_df(excel_path,site_list):
    sheet_name = None
    while sheet_name is None:
        interval = input ('Please enter the data inerval: "day","hour" or "15min": ')
        if interval == 'day':
            sheet_name = 'Data24'
        elif interval =='hour':
            sheet_name = 'Data60'
        elif interval == '15min':
            sheet_name = 'Data15'

    if sheet_name == 'Data15':
        Data_df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=8)
    else:
        Data_df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=5)

    columns = ['Unnamed: 1'] + site_list
    Data_df = Data_df[columns]
    Data_df = Data_df[1:].copy().dropna()
    Data_df.rename(columns = {'Unnamed: 1':'Date'}, inplace=True)
    Data_df['Date'] = pd.to_datetime(Data_df['Date'])
    Data_df.set_index('Date', inplace=True)
    return Data_df, interval

def make_directory(savefolder, subfolder):
    """
    creating directory
    :param savefolder:
    :param subfolder:
    :return:
    """
    d = pathlib.PurePath(savefolder, subfolder)
    p = pathlib.Path(d).mkdir(parents=True, exist_ok=True)
    return d

def get_para_df(excel_path):
    para_df = pd.read_excel(excel_path, sheet_name='Para', skiprows=10)
    para_df = para_df.dropna(subset=['Lat'])
    para_df = para_df[['Site Name', 'Lat', 'Long']].copy()
    num_site = len(para_df)
    site_list = list(para_df['Site Name'].values)
    para_df.set_index('Site Name', inplace=True)
    return para_df, num_site,site_list


def change_time_format(str):
    newstr=''
    for i in range(len(str)):
        if str[i] == ':':
            newstr += '-'
        else:
            newstr += str[i]
    return newstr

def create_plot(nx,ny,xmin, xmax,ymin,ymax,rain_data,para_df,vmax,time,outputfolder_new):
    # boundary_poly = gpd.read_file(path)
    # boundary_poly = boundary_poly.to_crs(epsg=4326)
    # bounds = boundary_poly.bounds.loc[0,:]

    # xmin = bounds.minx
    # xmax = bounds.maxx
    # ymin = bounds.miny
    # ymax = bounds.maxy


# Define the grid size
    nx, ny = nx, ny
    xi = np.linspace(xmin, xmax, nx)
    yi = np.linspace(ymin, ymax, ny)
    xi, yi = np.meshgrid(xi, yi)
    xi, yi = xi.flatten(), yi.flatten()

    z = rain_data
    x = para_df['Long']
    y = para_df['Lat']
    site_name = list(para_df.index)
    grid1 = simple_idw(x, y, z, xi, yi)
    grid1 = grid1.reshape((ny, nx))

    grid1_copy = grid1.copy()
    # mask_shp = boundary_poly['geometry'].iloc[0]
    # grid1_copy = np.copy(grid1)
    # for i in range(len(xi)):
    #     if not Point(xi[i], yi[i]).within(mask_shp):
    #         grid1_copy[int(i / ny), int(i % ny)] = np.nan  # (yi,xi)

    grid1_copy_flip = np.flip(grid1_copy, 0)
    grid1_copy_flip = grid1_copy_flip.astype(float)
    fig, ax = plot(x, y,site_name, grid1_copy_flip, xmin, xmax, ymax, ymin,vmax=vmax)
    plt.figtext(0.5, 0.85, f'Time: {time}', fontsize=20, ha='center')
    plt.figtext(0.5, 0.9, 'Rain Distribution', fontsize=20, ha='center')
    plt.savefig(str(outputfolder_new) + f'/{time}.png', dpi=fig.dpi)

def create_animation(outputfolder_new):
    frames = []
    imgs = glob.glob(str(outputfolder_new) + r'\*.png')
    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # save into a GIF file
    frames[0].save(str(outputfolder_new) + r'\animation.gif', format='GIF',
                   append_images=frames[1:],
                   save_all=True,
                   duration=1000, loop=0)

def export_fig_animation(nx, ny, xmin, xmax,ymin,ymax, Data_df, para_df, outputfolder_new):
    max_rain = Data_df.max()
    vmax = max_rain.max() * 1.1
    for i in range(len(Data_df)):
        rain_data = Data_df.iloc[i,:]
        time = Data_df.index[i].strftime('%m-%d-%Y, %H-%M')
        create_plot(nx,ny,xmin, xmax,ymin,ymax,rain_data,para_df,vmax, time, outputfolder_new)
    ##-------------------
    create_animation(outputfolder_new)