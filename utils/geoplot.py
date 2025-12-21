import pandas as pd
import geopandas as gpd
import os, sys
import matplotlib.pyplot as plt
import math
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





 # val_col=groups.columns[1]
    
    # old count:
    # group = gdf_joined.groupby(groupby).size().reset_index(name="count")

# if num_col and num_col in gdf_joined and gdf_joined[num_col].notna().any():
        #     print(f"[CHECK] NUMERIC values on mean_col/count_col :{gdf_joined[num_col].dtype}=> numeric!\n")   
        #     gdf_joined[num_col]=pd.to_numeric(gdf_joined[num_col], errors='coerce')
    
    
    
    
    
    
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
    print(f"choropleth map : groups cols:{groups.columns}")
   
    # merge to gdf_map: 把统计数字铁道map上
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")

    #-------------------plot-------------------
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    # 热度图：
    gdf_merged.plot(
        column=way,
        ax=ax,
        legend=True,
        cmap="OrRd",       # 红色系，表示“强度”
        edgecolor="black",
        linewidth=0.5
    )
    
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




def get_choropleth_map_ax(gdf_joined, gdf_map,
            col, way, groupby,
            ym, #for title
            ax, vmin, vmax
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

    if groupby and col and way: # get nb abs  
        #as_index=False 会自动把 Series 转成 DataFrame
        # 自定义的列名=处理的列，处理的方法(直接传入"mean"或者自己定义的函数)！
        groups=gdf_joined.groupby(groupby, as_index=False).agg(
                **{way:(col, way)}
                # way=(col, way) #简写无法动态取way的值 
        )
        print(f"choropleth_ax : groups cols:{groups.columns}\n")

   
    # merge to gdf_map: 把统计数字铁道map上
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")

    #-------------------plot-------------------
    # fig, ax = plt.subplots(1, 1, figsize=(8, 6))#子图大小格式由ax输入
    
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
            fontsize=6,
            linespacing=1.2,
            # bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")#+底色
        )
        
    # 小图标题:
    if ym:
        title = f"{str(ym)}"
        ax.set_title(title, fontsize=10)

    ax.axis("off")
    
    return




def layout_comparison_maps(dict_gdf_joined, gdf_map,
                col, way, groupby,
                suptitle, loc,# for filename
                n_axes, n_cols=3,#每行最多几张（列）
                save=False, output_folder=None, filename=None):
    
    # vmin & vmax
    vmin, vmax=0,0
    for ym, gdf_joined in dict_gdf_joined.items():
        groups=gdf_joined.groupby(groupby, as_index=False).agg(
            **{way:(col, way)}
        )        
        vmin_current= groups[way].min()
        if vmin> vmin_current:
            vmin=vmin_current
        vmax_current= groups[way].max()
        if vmax < vmax_current:
            vmax=vmax_current
    print(f"[INFO] vmin: {vmin}; vmax: {vmax}")
    
    
    # axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6* n_cols, 4 * n_rows)
    )
    axes = axes.flatten()
    print (f"[INFO] figure layout: {n_rows} rows x {n_cols} cols\n")

    # plot
    i=0
    for ym, gdf_joined in dict_gdf_joined.items():
        print(f"[INFO]{i}:{ym}, len gdf : {len(gdf_joined)}")
        get_choropleth_map_ax(gdf_joined, gdf_map, 
            col=col, way=way, groupby=groupby,
            ym=ym,
            ax=axes[i], vmin=vmin, vmax=vmax
        )
        i+=1
        
    #shut down
    for j in range(i, len(axes)):
         axes[j].axis("off")

        
    # same cbar
    sm = mpl.cm.ScalarMappable(
    cmap="OrRd",
        norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    )
    sm._A = []

    fig.subplots_adjust(right=0.88)
    cax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label(f"{col} ({way})", fontsize=6)

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
            filename=f"comparaison_{col}_{way}_{loc}-{'-'.join(dict_gdf_joined.keys())}.jpg"

        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    plt.show()
    

    return

















##===================================GAP COMPARISON=================================##

def get_single_gap_choropleth(dict_gdf_joined, gap_between: list,
                       gdf_map,
                       col, way, groupby, 
                       title, loc, save=False, output_folder=None):
    """
    Docstring for get_gap_choropleth
    
    :param dict_gdf_joined: Description
    :param gap_between: 2 index in dict
    """
    # 2 ax!!!
    # gdf1=dict_gdf_joined[gap_between[0]]
    # gdf2=dict_gdf_joined[gap_between[1]]
    # inupt 
    
    # gdfs=[dict_gdf_joined[gap_between[0]], dict_gdf_joined[gap_between[1]]]
    dict_gdf_gap={
        ym: dict_gdf_joined[ym]
        for ym in gap_between
    }
        
    groups_for_gap=[]
    for ym, gdf_joined in dict_gdf_gap.items():  
        # 1/3 ways 
        ways =["count", "mean","sum"]
        if way not in ways :
            print(f"[WARNING] choose a calculation method from {'/ '.join(ways)}!")
        
        # check numeric !
        if way=="mean" or way=="sum":
            print(f"[CHECK] needs numeric values for mean/sum! \n"
                f" dtype :{gdf_joined[col].dtype}")
            gdf_joined[col]=pd.to_numeric(gdf_joined[col], errors='coerce')


        if groupby and col and way:
            groups=gdf_joined.groupby(groupby, as_index=False).agg(
                    **{way:(col, way)}
            )# => df
            # groups.columns=[groupby, f"{way}"]
            print(f"{ym} gap map: groups cols:{groups.columns}\n")
        
        groups_for_gap.append(groups)
    df_gap=groups_for_gap[0].merge(groups_for_gap[1], left_on=groupby, right_on=groupby, how='left')
    df_gap['gap']=df_gap[f'{way}_y']-df_gap[f'{way}_x']
    print(f"[CHECK] df gap columns :{df_gap.columns}!")
    # display(df_gap)
    
    # merge back to map:
    gdf_merged = gdf_map.merge(df_gap, on=groupby, how="left")
    # print(gdf_merged.columns)
    # print(gdf_merged[[groupby,f'{way}_x',f'{way}_y','gap']])
     
    #-------------------plot-------------------
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
   
    ## 热度轴：    
    # 有负值的时候才用蓝色！
    if gdf_merged['gap'].min()>0:
        cmap="OrRd"
    else :
        cmap='RdBu_r'#'coolwarm',  
        
    gdf_merged.plot(
        column='gap',# 之前按照way画，
        ax=ax,
        legend=True,
        cmap=cmap,
        edgecolor="black",
        linewidth=0.5
    )
    
    # 坐标与文字： 
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{'+' if int(row['gap'])>=0 else '-'}{int(row['gap'])} {col}",
            ha="center",
            va="center",
            fontsize=6,
            linespacing=1.2,
            # bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")#+底色
        )
    
    # title
    
    ax.set_title(title, fontsize=10)
    ax.axis("off")
    
    if save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        filename=f"gap_{col}_{way}_{loc}{'-'.join(gap_between)}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    plt.show()
   
   
    return 



def get_gap_choropleth_ax(dict_gdf_joined, gap_between: list,
                       gdf_map,
                       col, way, groupby, 
                       ax, vmin, vmax, title):
    """
    Docstring for get_gap_choropleth
    
    :param dict_gdf_joined: Description
    :param gap_between: 2 index in dict
    """
    # input
    dict_gdf_gap={
        ym: dict_gdf_joined[ym]
        for ym in gap_between
    }
    
    # gdfs=[dict_gdf_joined[gap_between[0]], dict_gdf_joined[gap_between[1]]]
    
    groups_for_gap=[]
    for ym, gdf_joined in dict_gdf_gap.items():  
        # 1/3 ways 
        ways =["count", "mean","sum"]
        if way not in ways :
            print(f"[WARNING] choose a calculation method from {'/ '.join(ways)}!")
        
        # check numeric !
        if way=="mean" or way=="sum":
            print(f"[CHECK] needs numeric values for mean/sum! \n"
                f" dtype :{gdf_joined[col].dtype}")
            gdf_joined[col]=pd.to_numeric(gdf_joined[col], errors='coerce')

        if groupby and col and way:
            groups=gdf_joined.groupby(groupby, as_index=False).agg(
                    **{way:(col, way)}
            )# => df
            groups.columns=[groupby, f"{way}"]
            
            print(f"{ym} gap_map_ax: groups cols:{groups.columns}")
        
        groups_for_gap.append(groups)
    df_gap=groups_for_gap[0].merge(groups_for_gap[1], left_on=groupby, right_on=groupby, how='left')
    df_gap['gap']=df_gap[f'{way}_y']-df_gap[f'{way}_x']#总把Q2放在x的位置上！
    # df_gap['gap']=df_gap.iloc[:,1]-df_gap.iloc[:,2]
    # print(f"[CHECK] df gap columns :{df_gap.columns}!\n")
    # display(df_gap)
    
    
    # merge back to map:
    gdf_merged = gdf_map.merge(df_gap, on=groupby, how="left")
    # print(gdf_merged.columns)
    # print(gdf_merged[[groupby,f'{way}_x',f'{way}_y','gap']])
     
    #-------------------plot-------------------
    # fig, ax = plt.subplots(1, 1, figsize=(10, 8))
   
    ## cmap：    
    if vmin>0:#均为正
        cmap="OrRd"
    elif vmax<1 :# 大部分为负，全用蓝色！
        cmap= plt.cm.Blues_r 
    else :# 有正有负，且vmax超过1
        cmap='RdBu_r'
    print(f"[check] cmap {cmap} for gap comparaison!")
    
    # 差值图在左侧显示？
    gdf_merged.plot(
        column='gap', 
        ax=ax, 
        cmap=cmap, 
        vmin=vmin, 
        vmax=vmax, 
        legend=False,#小图不显示热度轴 
        edgecolor="black",
        linewidth=0.5
        )
       
    # 在ax上坐标与文字： 
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n {'+' if int(row['gap'])> 0 else''}{int(row['gap'])} {col}",
            ha="center",
            va="center",
            fontsize=6,
            linespacing=1.2,
            # bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")#+底色
        )
    
    # subtitle    
    ax.set_title(title, fontsize=10)
    ax.axis("off")

   
    return





    
    
def layout_gap_comparison (dict_gdf_joined, gdf_map,
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
    # density
    
    groups=dict_gdf_joined[ym_key].groupby(groupby, as_index=False).agg(
        **{way:(col, way)}
    )        
    vmin_density= groups[way].min()
    vmax_density= groups[way].max()
    
    # # gap        
    ym_refs=[i for i in dict_gdf_joined.keys() if i !=ym_key]    
    
    vmin_gap, vmax_gap=0,0
    for ym_ref in ym_refs:
        dict_gdf_gap={
            ym: dict_gdf_joined[ym]
            for ym in [ym_key,ym_ref]# ym_key放前！！
        }
        groups_for_gap=[]
        for ym, gdf_joined in dict_gdf_gap.items():  
            if groupby and col and way:
                groups=gdf_joined.groupby(groupby, as_index=False).agg(
                        **{way:(col, way)}
                )# => df
                print(f"layout gap_map : {ym} groups cols:{groups.columns}\n")
            
            groups_for_gap.append(groups)
        df_gap=groups_for_gap[0].merge(groups_for_gap[1], left_on=groupby, right_on=groupby, how='left')
        df_gap['gap']=df_gap[f'{way}_y']-df_gap[f'{way}_x']
        
        vmin_current= df_gap["gap"].min()
        if vmin_gap> vmin_current:
            vmin_gap=vmin_current
    
        vmax_current= df_gap["gap"].max()
        if vmax_gap < vmax_current:
            vmax_gap=vmax_current
            
        
    print(f"[INFO] vmin_density:{vmin_density}, vmax_density:{vmax_density} ")
    print(f"[INFO] vmin_gap:{vmin_gap}, vmax_gap:{vmax_gap}!")
                
    
   
    # #-----------------------------axes--------------------------------    
    ## layout axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(10* n_cols, 8* n_rows)
    )
    axes = axes.flatten()
    print (f"[INFO] figure layout: {n_rows} rows x {n_cols} cols\n")

    
    ## -----------------------------plot--------------------------------
    i=0
    for ym, gdf_joined in dict_gdf_joined.items():
        if ym ==ym_key:#中间正常显示值
            print(f"[INFO] event period {i}:{ym}, len gdf : {len(gdf_joined)}")
            get_choropleth_map_ax(gdf_joined=gdf_joined, 
                        gdf_map=gdf_map,
                        col=col, way=way, groupby=groupby,
                        ym=ym,
                        ax=axes[i], vmin=vmin_density, vmax=vmax_density
                        )        
        
        else : #参照组显示gap             
            gap_between=[ym_key, ym]#key放前面,x的位置!
            # gap_between_sorted=sorted(gap_between, key= lambda x : int(x), reverse=False)
            
            print(f"[INFO] gap between :{gap_between[1]}-{gap_between[0]}")
            get_gap_choropleth_ax(dict_gdf_joined, 
                    gap_between=gap_between,
                    gdf_map=gdf_map,
                    col=col, way=way, groupby=groupby, 
                    ax=axes[i], vmin=vmin_gap, vmax=vmax_gap,
                    title=f"{ym} comparé au {ym_key}")            
        i+=1
    
    # shutdown else
    for j in range(i, len(axes)):
         axes[j].axis("off")
    
    
    #--------------------------------cbar---------------------------------#
    
    # 已经在_ax中给map画了在vmin， vmax范围内的颜色
    
    
    # 创建 gap colorbar（左边，覆盖 ax2 和 ax3）
    sm_gap = mpl.cm.ScalarMappable(cmap='RdBu_r', norm=mpl.colors.Normalize(vmin=vmin_gap, vmax=vmax_gap))
    sm_gap._A = []  # 必须赋值空数组，matplotlib hack
    # 手动创建 axes 在 figure 左边
    cax_gap = fig.add_axes([0.08, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar_gap = fig.colorbar(sm_gap, cax=cax_gap, orientation='vertical')
    cbar_gap.set_label(f"Ecart de {col} ({way})")
    cbar_gap.ax.yaxis.set_label_position('left')  # label 放左边
    cbar_gap.ax.yaxis.tick_left()                # 刻度放左边




    # 创建 density colorbar（右边）
    sm_density = mpl.cm.ScalarMappable(cmap='OrRd', norm=mpl.colors.Normalize(vmin=vmin_density, vmax=vmax_density))
    sm_density._A = []
    # 手动创建 axes 在 figure 右边
    cax_density = fig.add_axes([0.90, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar_density = fig.colorbar(sm_density, cax=cax_density, orientation='vertical')
    cbar_density.set_label(f"{col} ({way})")




    # # show cbar
    # sm_density = mpl.cm.ScalarMappable(cmap='OrRd', norm=mpl.colors.Normalize(vmin=vmax_density, vmax=vmax_density))
    # sm_density._A = []
    # cbar_density = fig.colorbar(sm_density, ax=ax1, orientation='vertical', fraction=0.05, pad=0.02)
    # cbar_density.set_label(f"{col} ({way})")


    # # 创建 gap colorbar（左边，覆盖 ax2 和 ax3）
    # sm_gap = mpl.cm.ScalarMappable(cmap='RdBu_r', norm=mpl.colors.Normalize(vmin=vmin_gap, vmax=vmax_gap))
    # sm_gap._A = []
    # cbar_gap = fig.colorbar(sm_gap, ax=[ax2, ax3], orientation='vertical', fraction=0.05, pad=0.02)
    # cbar_gap.set_label(f"Ecart de {col} ({way})")
    # cbar_gap.ax.yaxis.set_label_position('left')  # label 放左边
    # cbar_gap.ax.yaxis.tick_left()                # 刻度放左边

    
    # ## same cbar：
    # sm = mpl.cm.ScalarMappable(
    # cmap="OrRd",
    #     norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    # )
    # sm._A = []

    # fig.subplots_adjust(right=0.88)
    # cax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    # cbar = fig.colorbar(sm, cax=cax)
    # cbar.set_label(f"{col} ({way})", fontsize=12)

    
    
    
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
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
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
    
    
    
    
    