import pandas as pd
import geopandas as gpd
import os, sys
import matplotlib.pyplot as plt

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


 # val_col=groups.columns[1]
    
    # old count:
    # group = gdf_joined.groupby(groupby).size().reset_index(name="count")

# if num_col and num_col in gdf_joined and gdf_joined[num_col].notna().any():
        #     print(f"[CHECK] NUMERIC values on mean_col/count_col :{gdf_joined[num_col].dtype}=> numeric!\n")   
        #     gdf_joined[num_col]=pd.to_numeric(gdf_joined[num_col], errors='coerce')
    
    
    
    
    
# ================================fixed map===================================



def get_single_choropleth_map(gdf_joined, gdf_map, groupby,
            col, way,
            loc, year, title=None,
            # ax, vmin, vmax,
            save=False, output_folder=None,filename=None
            ):
    
    # 1/3 ways 
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
    
    # print(groups)
    print(f"[CHECK] groups' type: {type(groups)}\n"
          f"groups cols:{groups.columns}")
   
    # merge to gdf_map: 把统计数字铁道map上
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")

    #-------------------plot-------------------
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    # 热度轴：
    gdf_merged.plot(
        column=way,
        ax=ax,
        legend=True,
        cmap="OrRd",       # 红色系，表示“强度”
        edgecolor="black",
        linewidth=0.5
    )
    
    # gdf_merged.plot(
        # column=way, 
        # ax=ax, 
        # cmap="OrRd", 
        # vmin=vmin, 
        # vmax=vmax, 
        # legend=False,#小图不显示热度轴 
        # edgecolor="black",
        # linewidth=0.5

        # )


    # 坐标与文字： 
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{int(row[way])} {col}",
            ha="center",
            va="center",
            fontsize=7,
            linespacing=1.2,
            # bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")#+底色
        )
    
    # 绘制标注（区号）
    # for idx, row in gdf_merged.iterrows():
    #     x = row["geometry"].centroid.x
    #     y = row["geometry"].centroid.y
    #     plt.text(
    #         x, y, 
    #         str(row[groupby]), 
    #         horizontalalignment='center',
    #         fontsize=8,
    #         fontweight='bold'
    #     ) 
    

    # title
    if loc and year and title:    
        title += f" à {loc} ({str(year)})"
        ax.set_title(title, fontsize=10)
    ax.axis("off")
    
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        filename=f"{col}_{way}_{loc}{year}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    plt.show()
    
    return




def get_choropleth_map_ax(gdf_joined, gdf_map, groupby,
            col, way,
            loc, year, #title=None,
            ax, vmin, vmax,
            # save=False, output_folder=None,filename=None
            ):
    
    # 1/3 ways 
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
    
    # print(groups)
    print(f"[CHECK] groups' type: {type(groups)}\n"
          f"groups cols:{groups.columns}")
   
    # merge to gdf_map: 把统计数字铁道map上
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")

    #-------------------plot-------------------
    # fig, ax = plt.subplots(1, 1, figsize=(8, 6))


    # 热度轴
    gdf_merged.plot(
        column=way, 
        ax=ax, 
        cmap="OrRd", 
        vmin=vmin, 
        vmax=vmax, 
        legend=False,#小图不显示热度轴 
        edgecolor="black",
        linewidth=0.5
        )
    
    #坐标与文字
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])}arr:\n{int(row[way])}",
            ha="center",
            va="center",
            fontsize=8,
            linespacing=1.2,
            # bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")#+底色
        )

    #小图不设立title
    # if loc and year and title:    
    if year:
        title = f"{str(year)}"
        ax.set_title(title, fontsize=10)

    ax.axis("off")

    # 小图不保存！ 
    # if save and output_folder:
    #     os.makedirs(output_folder, exist_ok=True)
    #     filename=f"{col}_{way}_{loc}{year}.jpg"
    #     outpath_fig=os.path.join(output_folder,filename)   
    #     fig.savefig(outpath_fig, dpi=300)      
    #     print(f"✅ [SAVE] map saved to {outpath_fig}!")
    # plt.show()
    
    return




def layout_maps(dict_gdf_joined, gdf_map, loc,
                col, way, groupby,suptitle,
                save=False, output_folder=None):
    import matplotlib as mpl
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    years=list(dict_gdf_joined.keys())
    # 统一热度轴：
    vmin, vmax=0,0
    for year, gdf_joined in dict_gdf_joined.items():
        groups=gdf_joined.groupby(groupby, as_index=False).agg(
            **{way:(col, way)}
        )
        # print(len(groups))
        # print(groups.columns)
        # print(groups)
        
        
        vmin_current= groups[way].min()
        if vmin> vmin_current:
            vmin=vmin_current
        vmax_current= groups[way].max()
        if vmax < vmax_current:
            vmax=vmax_current
    print(f"[INFO] vmin: {vmin}; vmax: {vmax}")
    # fig
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    
    i=0
    for year, gdf_joined in dict_gdf_joined.items():
        print(f"[INFO]{i}:{year}, len gdf : {len(gdf_joined)}")
        
        get_choropleth_map_ax(gdf_joined, gdf_map, groupby=groupby,
            col=col, way=way,
            loc=loc, year=year,
            ax=axes[i], vmin=vmin, vmax=vmax
        )
        i+=1
        
    # 统一热度轴
    
    # sm = mpl.cm.ScalarMappable(cmap="OrRd", norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax))
    # sm._A = []  # 必须加这一行才能生成 colorbar
    # divider = make_axes_locatable(axes[-1])  # 绑定在右侧子图
    # cax = divider.append_axes("right", size="1%", pad=0.01)
    # cbar = fig.colorbar(sm, cax=cax)

    suptitle+=f"entre {years[0]} et {years[1]} à {loc}"    
    plt.suptitle(
            suptitle,
            fontsize=20,
            fontweight="bold",
            # y=0.98
        )
    
    # sm = mpl.cm.ScalarMappable(
    #     cmap="OrRd",
    #     norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    # )
    # sm._A = []
    # cbar = fig.colorbar(
    #     sm,
    #     ax=axes,
    #     fraction=0.035,
    #     pad=0.03
    # ) 
    # cbar.set_label(f"{col} ({way})", fontsize=12)
    # cbar.ax.tick_params(labelsize=10)

    ## V0
    sm = mpl.cm.ScalarMappable(cmap="OrRd", norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []  # 必须加这一行才能生成 colorbar
    cbar = fig.colorbar(sm, ax=axes, 
                        fraction=0.02, #colorbar 宽度
                        pad=0.03 #colorbar 和子图的间距
                        )
    cbar.set_label(f"{col} ({way})", fontsize=12) # label 字体大小
    cbar.ax.tick_params(labelsize=10) # 刻度字体大小
    

    
    plt.tight_layout()    
    
    #save
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        filename=f"comparaison_{col}_{way}_{loc}{'-'.join(years)}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    plt.show()
    

    # plt.tight_layout(rect=[0, 0, 0.98, 0.95])
    # plt.suptitle(f"Comparaison de {way} {col} entre {years[0]} et {years[1]} à {loc}", fontsize=16)
    # plt.show()
    
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
        print(f"[CHECK] groups' type: {type(groups)}\n"
            f"groups cols:{groups.columns}")
    
    # # check numeric in mean +/ sum
    # for  num_col in [mean_on,sum_on]:
    #     # if num_col and num_col in gdf_joined :
    #     if num_col and num_col in gdf_joined and gdf_joined[num_col].notna().any():
    #         print(f"[CHECK] NUMERIC values on mean_col/count_col :{gdf_joined[num_col].dtype}=> numeric!\n")   
    #         gdf_joined[num_col]=pd.to_numeric(gdf_joined[num_col], errors='coerce')
        
    # desc :groupby==ZONE        
    # if count_on and groupby:# get nb abs  
    #     groups=gdf_joined.groupby(groupby)[count_on].count()
    #     groups.columns=[groupby, count_on]
        
    # elif mean_on and groupby:
    #     groups=gdf_joined.groupby(groupby)[mean_on].mean()
    #     groups.columns=[groupby, mean_on]
    
    # elif sum_on and groupby:
    #     groups=gdf_joined.groupby(groupby)[sum_on].sum()
    #     groups.columns=[groupby, sum_on]
    
    # val_col=groups.columns[1]
    
    
    
    
    
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
        m.savesave(outpath_html)
        print(f'✅ [SAVE] map with buffer saved to {outpath_html}!')
         

    return 
    
    
    
    
    