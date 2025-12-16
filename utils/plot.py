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
          f"default crs 'EPSG:4326'!")
    
    # check
    if not 'longitude' in df or not 'latitude' in df:
        print(f"[ERROR] 'latitude' or 'longitude' columns not found in df!!")
   
    # map 
    gdf=gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=crs
    )
    display(gdf.head())
    
    # save
    if save and OUTPUT_FOLDER and filename:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        outpath_shp=os.path.join(OUTPUT_FOLDER,filename)    
        save_gdf(gdf, outpath_shp)

    return 




def generate_choropleth_count(gdf_points, gdf_map, groupby="c_ar", loc="paris", year="2024"):
    #aligne :确保两个 GeoDataFrame 使用完全一致的投影坐标系。
    gdf_points = gdf_points.to_crs(gdf_map.crs)
    print(f"[CHCEK] GDFs in the same crs {gdf_map.crs}!")

    #join :
    gdf_joined = gpd.sjoin(
        gdf_points,
        gdf_map,
        how="left",
        predicate="within"
    )


    #count:
    # group = gdf_joined.groupby(groupby).size().sort_values(ascending=False)
    group = gdf_joined.groupby(groupby).size().reset_index(name="count")

    # merge to gdf_map
    gdf_merged = gdf_map.merge(group, on=groupby, how="left")

    #plot 
    
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

    ax.set_title(f"Airbnb Distribution by Arrondissement in {loc} ({year})", fontsize=16)
    ax.axis("off")
    plt.show()
    return 


