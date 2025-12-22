import pandas as pd
import geopandas as gpd
import os, sys
import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable


## 参数!=常量？

def read_csv(csv_path):
    return pd.read_csv(csv_path)


def read_gdf(gdf_path):
    gdf=gpd.read_file(gdf_path, encoding='utf-8')
    # print(f"scr :{gdf.crs}\n")
    return gdf
 
def save_gdf(gdf, outpath_gdf):
    if not outpath_gdf.endswith(".gpkg"):
        # shp文件无法接受col name大于10个字符，改用gpkg！
        print(f"[WARNING] check extension of outpath_gdf, should end with '.gpkg'!")
         
    os.makedirs(os.path.dirname(outpath_gdf), exist_ok=True)
    gdf.to_file(outpath_gdf, driver="GPKG", encoding="utf-8")
    # driver="ESRI Shapefile"
    
    print(f"☑️ [SAVE] gpkg file saved to {outpath_gdf}!")
    return 


def df2gdf(df, crs="EPSG:4326",  save=False, output_folder=None, filename=None):
    print(f"[INFO] len df: {len(df)}\n"
          f"default crs 'EPSG:4326'\n"
          f"ADD 'geometry' by latitude and longitude!\n")
    
    # check
    if not 'longitude' in df or not 'latitude' in df:
        print(f"[ERROR] 'latitude' or 'longitude' columns not found in df!!")
   
    # map 
    gdf=gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=crs
    )
    # display(gdf.head())
    
    # save
    if save and output_folder and filename:
        os.makedirs(output_folder, exist_ok=True)
        outpath_shp=os.path.join(output_folder,filename)    
        save_gdf(gdf, outpath_shp)

    return gdf




##=========================listings+map===========================
def locate_points(path_listings, path_map, CRS,  
                    save_gdf_joined=False,                     
                    output_folder=None,
                    filename_gdf_joined=None):
    #== load, align, sjoin
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        
    print("df_listings to gdf_listings by latitude and longitude!".center(100,"-"))        
    df=pd.read_csv(path_listings)
    
    gdf_listings=df2gdf(df=df, crs=CRS,
        save=False, output_folder=output_folder,
        filename='')
    
    print("read gdf map".center(100,'-'))
    gdf_map=read_gdf(path_map)
    
    
    print("join gdf_listings and gdf".center(100,'-'))
    if gdf_listings.crs!=gdf_map.crs:
        print(f"[WARNING] {gdf_listings.crs}!={gdf_map.crs}")
    
    # make sure
    gdf_listings = gdf_listings.to_crs(gdf_map.crs)
    
    #join: 把每一个 Airbnb 房源点，和它“所在的地图区域（多边形）”连在一起。
    gdf_joined = gpd.sjoin(
        gdf_listings,
        gdf_map,
        how="left",#保留左表gdf_listings的所有行,即使没有在右表中找到，填nan
        predicate="within"#左边的几何对象（pts）在右边的几何对象（polygone）之中
    )
    
    # save:
    if save_gdf_joined:
        outpath_gdf_joined=os.path.join(output_folder, filename_gdf_joined)
        save_gdf(gdf=gdf_joined, outpath_gdf=outpath_gdf_joined)
        
    return gdf_joined

    
    
    
    
    
##==============================pts map======================================

def get_pts_map(gdf_pts, gdf_map,title=None,
                save=False,output_folder=None,):
    
    fig, ax = plt.subplots(figsize=(16, 16))

    # Afficher les jeux de données sur la carte
    gdf_pts.plot(ax=ax, color='blue', markersize=5)
    gdf_map.plot(ax=ax, color='white', edgecolor='black')

    # Ajouter une grille de coordonnées et un titre
    ax.set_xlabel('Coordonnée x')
    ax.set_ylabel('Coordonnée y')
    ax.set_title(title)
    if save :
        os.makedirs(output_folder,exist_ok=True)
        
        outpath_pts_map=os.path.join(output_folder, "pts_map.jpg")
        plt.savefig(outpath_pts_map, dpi=300)
        print(f"✅ [SAVE] pts map saved to {outpath_pts_map}!")
        
    # Afficher la carte
    plt.show()

    return 



## ==================================universal=========================================

def get_cmap(vmin, vmax):    
    if vmin>=0:#均为正
        cmap="OrRd"
    elif vmax<1 :# 大部分为负，全用蓝色！
        cmap= plt.cm.Blues_r 
    else :# 有正有负，且vmax超过1
        cmap='RdBu_r'
    return cmap


def add_cbar(vmin, vmax, 
             fig, on_right=True, 
             col=None, way=None):
    cmap=get_cmap(vmin, vmax)
    print(f"[CHECK] {vmin:.2f}-{vmax:.2f}=> cmap {cmap}")
    
    sm = mpl.cm.ScalarMappable(
    cmap=cmap,
    norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        )
    
    sm._A = []
    if on_right==True:    
        cax = fig.add_axes([0.90, 0.25, 0.02, 0.5])
        # [left, bottom, width, height]
    
    else :
        cax=fig.add_axes([0.08, 0.25, 0.02, 0.5])
        
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label(f"{col}({way})", fontsize=10)
    cbar.ax.tick_params(labelsize=8)
    # return #  条件赋值 / 间接赋值 / return 会将变量认为是局部变量







def get_groups (gdf_joined, col, way, groupby):

    ## 1/3 ways 
    ways =["count", "mean","sum"]
    if way not in ways :
        print(f"[WARNING] choose a calculation method from {'/ '.join(ways)}!")
    
    ## check numeric
    if way=="mean" or way=="sum":
        # print(f"[CHECK] needs numeric values for mean/sum! \n"
        #       f" dtype :{gdf_joined[col].dtype}")
        gdf_joined[col]=pd.to_numeric(gdf_joined[col], errors='coerce')


    if groupby and col and way:# get nb abs  
        #as_index=False 会自动把 Series 转成 DataFrame
        # 自定义的列名=处理的列，处理的方法(直接传入"mean"或者自己定义的函数)！
        groups=gdf_joined.groupby(groupby, as_index=False).agg(
                **{way:(col, way)}
                # way=(col, way) #简写无法动态取way的值 
        )
         
        
    vmin= groups[way].min()
    vmax= groups[way].max()
    return groups, vmin, vmax








#===============================choropleth map=============================================

def get_choropleth_map(gdf_joined, 
            gdf_map, 
            col, way, groupby,
            subtitle,
            fig=None, subax=None, vmin=None, vmax=None,# oblig for subplot
            save=False, loc=None, ym=None, 
            output_folder=None,filename=None
        ):
    
    
    # ##input :
    # gdf_joined=gpd.read_file(path_gdf_joined)
    # gdf_map=gpd.read_file(path_gdf_map)
    
    # agg
    groups, vmin_current, vmax_current =get_groups(gdf_joined=gdf_joined, col=col, way=way, groupby=groupby)
    
    # merge back to gdf_map
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")

    #----------------------------plot-----------------------------
    if not subax: 
        # 单图:打开cbar，单独ax，取当前vmin，vmax
        fontsize_text=8 
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        vmin, vmax=vmin_current, vmax_current
    else :
        #外部大图
        fontsize_text=5
        ax=subax

        
    ## color the map:
    cmap=get_cmap(vmin, vmax)
    # print(f"[CHECK] cmap {cmap} for vlaues btw {vmin}-{vmax}!")

    gdf_merged.plot(
        column=way,
        ax=ax,
        vmin=vmin,
        vmax=vmax,
        legend=False, #默认都不画cbar，自动生成的难以控制位置和大小
        cmap=cmap,       
        edgecolor="black",
        linewidth=0.5
    ) 
    
    if not subax: 
        add_cbar(vmin=vmin, vmax=vmax, 
             fig=fig, on_right=True, 
             col=col, way=way)
    
    
    # 坐标与文字：
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{int(row[way])}",
            ha="center",
            va="center",
            fontsize=fontsize_text,
            linespacing=1.2,
        )
    
    ax.set_title(subtitle, fontsize=10, pad=10)# pad btw title & ax
    ax.axis("off")
    
    
    # 非子图，由outpath才保存
    if not ax and save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        if not filename:        
            filename=f"map_{col}_{way}_{loc}{ym}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✔ [SAVE] choropleth map saved to {outpath_fig}!")
        plt.show()
    
    return




def layout_comparison_indep(dict_gdf_joined, gdf_map,
                col, way, groupby,
                suptitle, loc, # for filename
                n_axes, n_cols=3,#每行最多几张（列）
                save=False, output_folder=None, filename=None):
    
    # vmin & vmax
    vmin, vmax=0,0
    for ym, gdf_joined in dict_gdf_joined.items():
        groups, vmin_current, vmax_current=get_groups(gdf_joined=gdf_joined, col=col, way=way, groupby=groupby)
        if vmin> vmin_current:
            vmin=vmin_current
        vmax_current= groups[way].max()
        if vmax < vmax_current:
            vmax=vmax_current
    # print(f"[INFO] vmin-vmax: {vmin}-{vmax}!")
    
    
    # axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6* n_cols, 4 * n_rows)
    )
    axes = axes.flatten()
    print (f"[INFO] compa indep layout: {n_rows} rows x {n_cols} cols\n")

    # plot
    i=0
    for ym, gdf_joined in dict_gdf_joined.items():
        get_choropleth_map(gdf_joined=gdf_joined, 
            gdf_map=gdf_map, 
            col=col, way=way, groupby=groupby,
            subtitle=ym,
            fig=fig, subax=axes[i], vmin=vmin, vmax=vmax,
            save=False, loc=loc, ym=ym, 
            output_folder=None,filename=None
        )
        i+=1
        
    #shut down
    for j in range(i, len(axes)):
         axes[j].axis("off")
                 
    # add cbar
    add_cbar(vmin, vmax, 
             fig, on_right=True, 
             col=col, way=way)       

    # 大标题：
    plt.suptitle(
            suptitle,
            fontsize=20,
            fontweight="bold",
            # y=0.98
        )
    
    # plt.tight_layout() #layout会压缩到cbar！   
    
    #save
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        if not filename:
            filename=f"indep_comparaison_{col}_{way}_{loc}-{'-'.join(dict_gdf_joined.keys())}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    
    plt.show()
    
    return




###===================================GAP========================================

def get_groups_gap(dict_gdf_joined, gap_between,
                      col, way, groupby):
    
    dict_gdf_gap={
        ym: dict_gdf_joined[ym]
        for ym in gap_between
    }
    groups_for_gap=[]
    for ym, gdf_joined in dict_gdf_gap.items():
        groups, vmin_current, vmax_current= get_groups(gdf_joined, col=col, way=way, groupby=groupby)
        groups_for_gap.append(groups)               
        
    df_gap=groups_for_gap[0].merge(groups_for_gap[1], left_on=groupby, right_on=groupby, how='left')
    df_gap['gap']=df_gap[f'{way}_y']-df_gap[f'{way}_x']
    
    vmin_gap_current=df_gap['gap'].min()
    vmax_gap_current=df_gap['gap'].max()

    return df_gap, vmin_gap_current, vmax_gap_current

    
    
def get_choropleth_map_gap(dict_gdf_joined, 
            gap_between,
            gdf_map, 
            col, way, groupby,
            subtitle,
            fig=None, subax=None, vmin=None, vmax=None,# optional for single map
            save=False, loc=None, ym=None, # for filename
            output_folder=None,filename=None
        ):    

    df_gap, vmin_gap_current, vmax_gap_current= get_groups_gap(dict_gdf_joined, gap_between,
                      col=col, way=way, groupby=groupby) 
    
    # merge back to map:
    gdf_merged = gdf_map.merge(df_gap, on=groupby, how="left")


    #----------------------------plot-----------------------------

    if not subax:
        fontsize_text=8 
        # 单图:打开cbar，单独ax，取当前vmin，vmax(无外部输入)
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        vmin, vmax=vmin_gap_current, vmax_gap_current

    else : 
        fontsize_text=5
        ax=subax


    ## color the map:
    cmap=get_cmap(vmin, vmax)
    # print(f"[CHECK] cmap '{cmap}' for vlaues btw {vmin}-{vmax}!")

    gdf_merged.plot(
        column='gap',#*
        ax=ax,
        vmin=vmin,
        vmax=vmax,
        legend=False, #默认都不画cbar，自动生成的难以控制位置和大小
        cmap=cmap,       
        edgecolor="black",
        linewidth=0.5
    ) 
    
    if not subax:# 单图则画cbar 
        add_cbar(vmin=vmin, vmax=vmax, 
                fig=fig, on_right=True, 
                col=col, way=way)
    
    # 坐标与文字：
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{int(row['gap'])}",#*
            ha="center",
            va="center",
            fontsize=fontsize_text,
            linespacing=1.2,
        )
    
    ax.set_title(subtitle, fontsize=10, pad=10)# pad btw title & ax
    ax.axis("off")

    
    # 非子图，由outpath才保存
    if not subax and save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        if not filename:        
            filename=f"gap_map_{col}_{way}_{loc}{'-'.join(gap_between)}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✔ [SAVE]  choropleth gap map saved to {outpath_fig}!")
        plt.show()
    
    return





    
    
def layout_comparison_gap (dict_gdf_joined, gdf_map,
                        ym_key,
                        col, way, groupby,
                        n_axes, n_cols=3,
                        suptitle=None, loc=None,#for filename
                        save=False, output_folder="../output_map",
                        filename=None
                        ):
    ## experimental group : 2406 ; control groups 2403, 2409 
    # 只能有一个实验组，其余均是对照组？
    
    
    ## ------------------------------vmin vmax-----------------------------------
    # key  
    groups_density, vmin_density, vmax_density = get_groups(gdf_joined=dict_gdf_joined[ym_key],
            col=col, way=way, groupby=groupby)
    
    # ref        
    ym_refs=[i for i in dict_gdf_joined.keys() if i !=ym_key]    

    vmin_gap, vmax_gap=0,0
    for ym_ref in ym_refs:    
        df_gap, vmin_gap_current, vmax_gap_current=get_groups_gap(dict_gdf_joined, 
                    gap_between=[ym_key, ym_ref],
                    col=col, way=way, groupby=groupby)
        if vmin_gap> vmin_gap_current:
            vmin_gap=vmin_gap_current
        if vmax_gap < vmax_gap_current:
            vmax_gap=vmax_gap_current
                   
    # print(f"[INFO] vmin_density:{vmin_density}, vmax_density:{vmax_density} ")
    # print(f"[INFO]OVERALL vmin_gap :{vmin_gap}, OVERALL vmax_gap:{vmax_gap}!\n")
                
    
   
    # #-----------------------------axes--------------------------------    
    ## layout axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(10* n_cols, 8* n_rows)
    )
    axes = axes.flatten()
    print (f"[INFO] compa gap layout: {n_rows} rows x {n_cols} cols\n")

    
    ## -----------------------------plot--------------------------------
    i=0
    for ym, gdf_joined in dict_gdf_joined.items():
        if ym ==ym_key:#中间正常显示值 
            get_choropleth_map(gdf_joined=gdf_joined, 
                gdf_map=gdf_map, 
                col=col, way=way, groupby=groupby,
                subtitle=ym,
                fig=fig, subax=axes[i], vmin=vmin_density, vmax=vmax_density,# oblig for subplot
                save=False, loc=loc, ym=ym, 
                output_folder=None,filename=None
            )      
        
        else : #参照组显示gap             
            gap_between=[ym_key, ym]#key放前面,x的位置!                     
            get_choropleth_map_gap(dict_gdf_joined, 
                    gap_between=gap_between,
                    gdf_map=gdf_map, 
                    col=col, way=way, groupby=groupby,
                    subtitle=f"{ym} comparé au {ym_key}",
                    fig=fig, subax=axes[i], 
                    vmin=vmin_gap, vmax=vmax_gap,# optionel
                    save=False, loc=loc, ym=ym, 
                    output_folder=None,filename=None
                )                    
        i+=1
    
    # shutdown else
    for j in range(i, len(axes)):
         axes[j].axis("off")
    
    
    #--------------------------------cbar---------------------------------#
    
    # # 已经在_ax中给map画了在vmin， vmax范围内的color
    ## 左边 cbar_gap
    add_cbar(vmin=vmin_gap, vmax=vmax_gap, 
             fig=fig, on_right=False, 
             col=col, way='gap')
    
    # 右边cbar_density
    add_cbar(vmin=vmin_density, vmax=vmax_density, 
             fig=fig, on_right=True, 
             col=col, way=way)   
    
    
    # suptitle：
    plt.suptitle(
            suptitle,
            fontsize=20,
            fontweight="bold",
            # y=0.98
        )

    
    # no layout tight!!!!!

    ## save
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        filename=f"gap_comparaison_{col}_{way}_{loc}{'-'.join(dict_gdf_joined.keys())}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] comparasion gap map saved to {outpath_fig}!")
    plt.show()
       
    
    return


















# MOT 
list_jo =['olympic', 'jo', 'stade']
list_geo=["close"]







#=================================HTML MAP=====================================

import pandas as pd
import geopandas as gdf
import os, sys, importlib, time
import mapclassify#***
import folium #***
from folium import Map, CircleMarker
import matplotlib.pyplot as plt


# def plot_points_map(gdf_pts, gdf_map, 
#                     save=False, OUTPUT_FOLDER=None,filename=None):
    
#     return 

def get_desc_map_html(gdf_joined, gdf_map,
                    # pts_is_letf=True,
                    groupby=None,
                    # sum_on=None, count_on=None, mean_on=None,
                    col=None, way=None,  
                    size_ratio=50,
                    save=False, output_folder=None, 
                    ):

    # # aligne :
    # gdf_pts=gdf_pts.to_crs(gdf_map.crs)
    # print(f"[CHECK] pts and map in same crs {gdf_map.crs}!")
    # #EPSG:3857
    
    # # join
    # if pts_is_letf:
    #     gdf_joined=gdf.sjoin(gdf_pts,
    #     		gdf_map, how='inner',predicate='intersects')
    # else:
    #     gdf_joined=gdf.sjoin(gdf_map,
    #             gdf_pts, how="inner", predicate='intersects')

    
    # desc : 1/3 ways 
    ways =["count", "mean","sum"]
    if way not in ways :
        print(f"[WARNING] choose a calculation method from {'/ '.join(ways)}!")
    
    # check numeric !
    if way=="mean" or way=="sum":
        print(f"[CHECK] needs numeric values for mean/sum! \n"
              f" dtype :{gdf_joined[col].dtype}")
        gdf_joined[col]=pd.to_numeric(gdf_joined[col], errors='coerce')

    if groupby and col and way:# get nb abs  
        #as_index=False 会自动把 Series 转成 DataFrame
        # 自定义的列名=处理的列，处理的方法(直接传入"mean"或者自己定义的函数)！
        groups=gdf_joined.groupby(groupby, as_index=False).agg(
                **{way:(col, way)}
                # way=(col, way) #简写无法动态取way的值 
        )
        print(f"groups cols:{groups.columns}\n")
    

    
    # merge groups back to map by "groupby"
    gdf_to_map=gdf_map.merge(groups,
            on=groupby, how='left')
    # display(gdf_to_map.head())
 
 	#map it:
	# Folium fonctionne mieux avec des coordonnées WGS84 (4326)
    gdf_to_map = gdf_to_map.to_crs(epsg=4326)

    #通过mean找到zone的中心点
    m = folium.Map(location=[gdf_to_map.geometry.centroid.y.mean(),
                        gdf_to_map.geometry.centroid.x.mean()], zoom_start=12)
    
    for idx, row in gdf_to_map.iterrows():
        folium.CircleMarker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            radius=row[way] / size_ratio,  # Ajustez le facteur de division selon vos besoins
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=folium.Popup(f"{row[groupby]}<br> {row[groupby]}", parse_html=True)# title?
        ).add_to(m)
    
    # legend
    example_sizes = [100, 500, 1000]  #图例中点的大小
    legend_circles = ""
    for size in example_sizes:
        radius = size / size_ratio # 要和map上的比例尺一致！
        legend_circles += f"""
        &nbsp; <svg width="{2*radius}" height="{2*radius}">
            <circle cx="{radius}" cy="{radius}" r="{radius}" fill="blue" fill-opacity="0.6" stroke="blue"/>
        </svg>&nbsp; {size}<br>
        """

    # Ajouter une légende
    legend_html = f"""
        <div style="position: fixed;
        bottom: 50px; left: 50px; width: 170px; height: auto;
        background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
        padding: 10px;">
        <b>Légende</b> <br>
        {col} {way}: <br>
        {legend_circles}
        </div>
        """
    m.get_root().html.add_child(folium.Element(legend_html))    
    display(m)
        
    if save and output_folder:            
        os.makedirs(output_folder, exist_ok=True)
        filename=f"proportional_map_on_{way}_{col}.html"
        outpath_html=os.path.join(output_folder, filename)
        m.save(outpath_html)
        print(f'✅ [SAVE] map of proportional cercles saved to {outpath_html}!')
  
    return 


def buffer_in(geometry, distance_x_meters):
    # create a buffer around a pt!  
    # return pt x, y, polygone
    crs = geometry.crs
    return geometry.to_crs(epsg=3857).buffer(distance_x_meters).to_crs(crs)


def get_buffer_map_html(gdf_pts, gdf_map,
                        filter_by_col=None, filter_by_value=None,
                        pts_col=None, distance_x_meters=None,   
                        save=False, output_folder=None, filename='map_buffer.html'):
    # gdf_pts!=gdf_pts_filter by zone!
    
    # aligne :
    gdf_pts=gdf_pts.to_crs(gdf_map.crs)
    print(f"[CHECK] gdf_pts & gdf_map on the same CRS : {gdf_pts.crs}!")
    
    # sjoin first
    gdf_joined=gdf.sjoin(gdf_pts,
    		gdf_map, how='inner',predicate='intersects')

    # then filter by zone : 
    gdf_joined_filtered=gdf_joined.copy()

    if filter_by_col and filter_by_value:
        gdf_joined_filtered=gdf_joined_filtered[gdf_joined_filtered[filter_by_col]==filter_by_value]
        print(f"[INFO] len gdf_joined_filtered :{len(gdf_joined_filtered)}\n"
              f"cols :{gdf_joined_filtered.columns}")
    else :
        print(f'[INFO] no filteration applied on gdf_joined!')

    # create buffer:
    # 要先把pt列设为index！
    areas=buffer_in(gdf_joined_filtered.set_index(pts_col).geometry, distance_x_meters=distance_x_meters)
    
    # series to gdf
    gdf_areas = areas.to_frame().rename(columns={0:'geometry'})
    
    # 指明空间列！
    gdf_areas=gdf.GeoDataFrame(gdf_areas, geometry=gdf_areas['geometry'])
    m = gdf_areas.explore()
    display(m)

    # plt
    # ax = gdf_areas.plot(figsize = (10, 10), color='white', edgecolor='black'
    # # ax.set_xlabel('Coordonnée x')
    # # ax.set_ylabel('Coordonnée y')
    # ax.set_title(title)
        
    # # 悬停鼠标时显示idx文字
    # for idx, row in gdf_areas.iterrows():
    #     ax.annotate(text=idx, xy=row.geometry.centroid.coords[0], horizontalalignment='center', fontsize=10)
        
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        outpath_html=os.path.join(output_folder, filename)
        m.save(outpath_html)
        print(f'✅ [SAVE] map with buffer saved to {outpath_html}!')
         

    return 
    
    
    
    
    