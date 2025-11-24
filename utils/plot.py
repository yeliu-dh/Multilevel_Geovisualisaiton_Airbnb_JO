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
 
def save_gdf(gdf, gdf_path):
    if not gdf_path.endswith(".shp"):
        print(f"[WARNING] check extension of gdf_path, should end with '.shp'!")

    os.makedirs(os.path.dirname(gdf_path), exist_ok=True)

    gdf.to_file(gdf_path, driver="ESRI Shapefile", encoding="utf-8")
    return 


def df2gdf(df, gdf_path, crs="EPSG:4326"):
    print(f"len df: {len(df)}")

    if not 'longitude' in df or not 'latitude' in df:
        print(f"[ERROR] 'latitude' or 'longitude' columns not found in df!!")

    gdf=gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=crs
    )
    print(f"df => gdf in crs {crs}:\n")
    display(gdf.head())
    

    save_gdf(gdf, gdf_path)
    print(f"gdf saved to {gdf_path}!")

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


