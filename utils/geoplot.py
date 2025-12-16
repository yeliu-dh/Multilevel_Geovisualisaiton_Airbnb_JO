import pandas as pd
import geopandas as gpd
import os, sys
import matplotlib.pyplot as plt


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






def df2gdf(df, crs="EPSG:4326",  save=False, OUTPUT_FOLDER=None, filename=None):
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
    if save and OUTPUT_FOLDER and filename:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        outpath_shp=os.path.join(OUTPUT_FOLDER,filename)    
        save_gdf(gdf, outpath_shp)

    return gdf






##=========================listings+map===========================
def locate_points(path_listings, path_map, CRS,  
                    save_gdf_joined=False,                     
                    OUTPUT_FODLER=None,
                    filename_gdf_joined=None):
    if OUTPUT_FODLER:
        os.makedirs(OUTPUT_FODLER, exist_ok=True)
        
    print("df_listings to gdf_listings by latitude and longitude!".center(100,"-"))        
    df=pd.read_csv(path_listings)
    
    gdf_listings=df2gdf(df=df, crs=CRS,
        save=False, OUTPUT_FOLDER=OUTPUT_FODLER,
        filename='')
    
    print("read gdf map".center(100,'-'))
    gdf_map=read_gdf(path_map)
    
    
    print("join gdf_listings and gdf".center(100,'-'))
    if gdf_listings.crs!=gdf_map.crs:
        print(f"[WARNING] {gdf_listings.crs}!={gdf_map.crs}")
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
        outpath_gdf_joined=os.path.join(OUTPUT_FODLER, filename_gdf_joined)
        save_gdf(gdf=gdf_joined, outpath_gdf=outpath_gdf_joined)
        
    return gdf_joined



def get_choropleth_map(path_gdf_joined, path_gdf_map, groupby="c_ar",
                              loc="paris", year="2024",title=None,
                              save=False, OUTPUT_FOLDER=None,filename=None):
    
    # #aligne :确保两个 GeoDataFrame 使用完全一致的投影坐标系。
    # gdf_listings = gdf_listings.to_crs(gdf_map.crs)
    # print(f"[CHCEK] GDFs use the same crs {gdf_map.crs}!")

    # #join :
    # gdf_joined = gpd.sjoin(
    #     gdf_listings,
    #     gdf_map,
    #     how="left",
    #     predicate="within"
    # )
    
    # gdf_joined在groupby之后geo消失，必须按照groupby col贴回map
    gdf_joined=read_gdf(path_gdf_joined)
    gdf_map=read_gdf(path_gdf_map)

    #count:
    # group = gdf_joined.groupby(groupby).size().sort_values(ascending=False)
    group = gdf_joined.groupby(groupby).size().reset_index(name="count")

    # merge to gdf_map: 把统计数字铁道map上
    gdf_merged = gdf_map.merge(group, on=groupby, how="left")

    #-------------------plot-------------------
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    gdf_merged.plot(
        column="count",
        ax=ax,
        legend=True,
        cmap="OrRd",       # 红色系，表示“强度”
        edgecolor="black",
        linewidth=0.5
    )
    # 绘制标注（区号）
    for idx, row in gdf_merged.iterrows():
        x = row["geometry"].centroid.x
        y = row["geometry"].centroid.y
        plt.text(
            x, y, 
            str(row[groupby]), 
            horizontalalignment='center',
            fontsize=8,
            fontweight='bold'
        )
        
        
    if loc and year and title:    
        title+= f"à {loc} ({year})"
        ax.set_title(title, fontsize=16)
    ax.axis("off")
    if save and OUTPUT_FOLDER and filename:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        outpath_fig=os.path.join(OUTPUT_FOLDER,filename)   
        fig.savefig(outpath_fig, dpi=300)      
    plt.show()
    
    return 



