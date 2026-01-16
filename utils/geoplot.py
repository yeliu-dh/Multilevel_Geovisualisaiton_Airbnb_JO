import pandas as pd
import geopandas as gpd
import os, sys
import math
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
import mapclassify
from matplotlib.cm import get_cmap
from matplotlib.colors import LinearSegmentedColormap




    
    
    
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
def locate_points(path_listings, path_map, crs="EPSG:4326",  
                    save_gdf_joined=False,                     
                    output_folder=None,
                    filename=None):
    #== load, align, sjoin
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        
    print("df_listings to gdf_listings by latitude and longitude!".center(100,"-"))        
    df=pd.read_csv(path_listings)
    # display(df.head())
    
    gdf_listings=df2gdf(df=df, crs=crs,
        save=False, output_folder=output_folder,
        filename=None)
    
    print("read gdf map".center(100,'-'))
    gdf_map=read_gdf(path_map)
    # print(gdf_map.crs)
    # print(gdf_map.head())
    
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
    # display(gdf_joined)
    
    # save:
    if save_gdf_joined:
        outpath_gdf_joined=os.path.join(output_folder, filename)
        save_gdf(gdf=gdf_joined, outpath_gdf=outpath_gdf_joined)
        
    return gdf_joined


    
    
    
##==============================pts map======================================

def get_pts_map(gdf_pts, gdf_map,title=None,
                save=False,output_folder=None,):
    
    gdf_pts=gdf_pts.to_crs(gdf_map.crs)
    print("pts CRS:", gdf_pts.crs)
    print("map CRS:", gdf_map.crs)


    fig, ax = plt.subplots(figsize=(16, 16))

    # Afficher les jeux de données sur la carte
    # gdf_pts.plot(ax=ax, color='blue', markersize=5)
    # gdf_map.plot(ax=ax, color='white', edgecolor='black')
    gdf_map.plot(ax=ax, color='white', edgecolor='black')
    gdf_pts.plot(ax=ax, color='blue', markersize=20)

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



###=====================================MAPS=============================================================###
## ==================================universal=========================================

def get_auto_cmap(vmin, vmax):    
    if vmin>=0:#均为正
        # base = plt.cm.OrRd
        # colors = base(np.linspace(0.1, 0.6, 256))  # 只取中间浅色段
        # cmap_light = LinearSegmentedColormap.from_list("OrRd_light", colors)
        # cmap=cmap_light
        cmap="OrRd"
    elif vmax<1 :# 大部分为负，全用蓝色！
        cmap= plt.cm.Blues_r 
    else :# 有正有负，且vmax超过1
        cmap='RdBu_r'
    return cmap



def add_cbar(vmin, vmax, 
            fig, on_right=True, 
            cbar_label=None,
            cmap=None,
            ):
    if cmap==None:
        cmap=get_auto_cmap(vmin, vmax)
        print(f"[CHECK] {vmin:.2f}-{vmax:.2f}=> cmap {cmap}")
    
    sm = mpl.cm.ScalarMappable(
    cmap=cmap,
    norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        )
    ## 这意味着：连续变量;线性映射;没有“分组”;没有强调分布结构
    
    sm._A = []
    if on_right==True:    
        cax = fig.add_axes([0.90, 0.15, 0.02, 0.5])
        # cax = fig.add_axes([0.90, 0.25, 0.02, 0.5])
        # [left, bottom, width, height]
    
    else :
        cax=fig.add_axes([0.08, 0.15, 0.02, 0.5])
        
    cbar = fig.colorbar(sm, cax=cax)
   
    cbar.set_label(cbar_label, fontsize=10)
    cbar.ax.tick_params(labelsize=8)
    # return #  条件赋值 / 间接赋值 / return 会将变量认为是局部变量


def build_bounds_norm(
    scheme,
    vmin=None,
    vmax=None,
    values=None,
    k_quantile=5,
    bins=None,
    cmap="OrRd"
):

    #传入的cmap(str)要转换成cm格式
    from matplotlib.cm import get_cmap

    if isinstance(cmap, str):
        cmap = get_cmap(cmap)
    elif cmap is None:
        cmap = plt.cm.viridis

    # --------------------------------------------------
    # Norm selection:
    # bounds = 分箱规则
    # norm = 数值 → 颜色的翻译器
    # --------------------------------------------------
    if scheme == "continuous":
        assert vmin is not None and vmax is not None, \
            "vmin and vmax must be provided for continuous scheme"
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        bounds = None

    elif scheme == "quantile":
        assert values is not None, \
            "values must be provided for quantile scheme"
        bounds = np.quantile(values, np.linspace(0, 1, k_quantile+ 1))
        norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N)

    elif scheme == "userdefined":
        assert bins is not None, \
            "bins must be provided for custom scheme"
        bounds = bins
        norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N)

    else:
        raise ValueError(f"Unknown scheme: {scheme}")

    return bounds, norm




def add_cbar_scheme(
    fig,
    # *,
    scheme="continuous",      # "continuous" | "quantile" | "custom"
    
    # 1) continus input
    vmin=None,
    vmax=None,
    # 2) quantile input
    values=None,              # for scheme quantile
    k_quantile=5,                      # number of classes for quantile
    # 3) custom input
    bins=None,               
    
    # layout
    on_right=True,
    cbar_label=None,
    cmap=None,
    tick_format="{:.2f}"
    ):
    
    print(f"[INFO] cbar takes bounds: {scheme}!")
    
    """
    Flexible colorbar constructor with explicit classification schemes.
    """
    
    bounds, norm=build_bounds_norm(
        scheme=scheme,
        vmin=vmin, 
        vmax=vmax,
        values=values,
        k_quantile=k_quantile,
        bins=bins,
        cmap=cmap
    ) 
        
    # --------------------------------------------------
    # ScalarMappable : create cbar 
    # --------------------------------------------------
    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []

    # --------------------------------------------------
    # position of cbar
    # --------------------------------------------------
    if on_right:
        cax = fig.add_axes([0.90, 0.15, 0.02, 0.5])
    else:
        cax = fig.add_axes([0.08, 0.15, 0.02, 0.5])

    # --------------------------------------------------
    # Colorbar
    # --------------------------------------------------
    if bounds is None:
        cbar = fig.colorbar(sm, cax=cax)
    else:
        cbar = fig.colorbar(
            sm,
            cax=cax,
            boundaries=bounds,
            ticks=bounds
        )
        cbar.ax.set_yticklabels([tick_format.format(b) for b in bounds])

    cbar.set_label(cbar_label, fontsize=10)
    cbar.ax.tick_params(labelsize=8)

    return cbar



def add_circle_legend(k, vmin_circle, vmax_circle,fig):
    #legend
    n_levels = 3  # legend 等级数
    legend_values = np.linspace(vmin_circle, vmax_circle, n_levels)
    legend_values = np.round(legend_values / 100) * 100
    legend_values = legend_values.astype(int) 
    
    if not k :            
        max_marker_area = 5000  # 你视觉上觉得最大的圆
        k = max_marker_area / vmax_circle
    
    circle_handles = [
    plt.scatter(
            [], [],
            s=val * k/50 ,
            facecolors="none",
            edgecolors="black",
            linewidth=1,
            label=f"{val/50:.2f} hôtes"
        )
        for val in legend_values
    ]
    return circle_handles


def add_legend(fig, k, vmin_circle, vmax_circle,
               ):
    
    circle_handles=add_circle_legend(k, vmin_circle, vmax_circle,fig)
    
    fig.legend(
        handles=circle_handles,
        title="Nombre",
        loc="upper right",
        bbox_to_anchor=(0.94, 0.8),  # 调整 legend 内部位置
        frameon=True,

        fontsize=9,            # label 字号 ↑
        title_fontsize=10,     # 标题字号 ↑
        markerscale=1.4,       # 关键：放大圆
        handlelength=1.6,      # 色块/符号长度
        labelspacing=0.6,      # 行距
        borderpad=0.6          # 内边距
    )






##====================================STATS====================================

def get_groups(gdf_joined, col, way, groupby):
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
         
    # vmin= groups[way].min()
    # vmax= groups[way].max()
    return groups





#===============================choropleth map=============================================

def get_choropleth_map(gdf_joined, 
            gdf_venues,
            gdf_map, 
            col, way, groupby,
            title=None,
        
            fig=None, subax=None, vmin=None, vmax=None,values=None,bins=None,  #oblig for subplots   
            scheme='quantile', k_quantile=10, cmap="OrRd", # colors
            
            save=False, loc=None, ym=None,# for automatic filename 
            output_folder=None,filename=None
        ):
    # agg
    groups =get_groups(gdf_joined=gdf_joined, col=col, way=way, groupby=groupby)
    # display(groups)
    
    # merge back to gdf_map
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")
    
      
    #----------------------------plot-----------------------------
    if not subax: # 单图:打开cbar，单独ax，取当前vmin，vmax
        fontsize_text=8 
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        vmin, vmax=groups[way].min(),groups[way].max()
        values=groups[way].dropna().values
        
        # same color for map and cbar:
        bounds, norm=build_bounds_norm(
            scheme=scheme,
            vmin=vmin,
            vmax=vmax,
            values=values,
            k_quantile=5,
            bins=bins,
            cmap=cmap
        )
        
        # add color to map :  
        gdf_merged.plot(
            column=way,
            ax=ax,
            # vmin=vmin,
            # vmax=vmax,
            legend=False,
            norm=norm,
            cmap=cmap,
            edgecolor="black",
            linewidth=0.5
        )
        
        # show cbar:
        add_cbar_scheme(
            fig,
            scheme=scheme,      # "continuous" | "quantile" | "custom"
            # 1) continus input
            vmin=vmin,
            vmax=vmax,
            # 2) quantile input
            values=values,              # for scheme quantile
            k_quantile=k_quantile,                      # number of classes for quantile
            # 3) custom input
            bins=bins,              
            
            # layout
            on_right=True,
            cbar_label=f"{col} ({way})",
            cmap=cmap,
            tick_format="{:.2f}"
        )       
        
    
    else :#小图
        fontsize_text=5
        ax=subax
        
        # # V2:
        ## same bounds for gdf plot and cbar!!!
        bounds, norm=build_bounds_norm(
            scheme=scheme,
            vmin=vmin,
            vmax=vmax,
            values=values,
            k_quantile=k_quantile,
            bins=bins,
            cmap=cmap
        )
        gdf_merged.plot(
            column=way,
            ax=ax,
            legend=False,
            norm=norm,
            cmap=cmap,
            edgecolor="black",
            linewidth=0.5
        )


    # ========================SAME======================= 
    # 坐标与文字：
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{row[way]:.2f}",
            ha="center",
            va="center",
            fontsize=fontsize_text,
            linespacing=1.2,
        )
    
    if gdf_venues is not None and not gdf_venues.empty:#不为none且不为空        
        # center
        gdf_venues = gdf_venues.to_crs(gdf_merged.crs)
        gdf_venues.plot(
            ax=ax, 
            markersize=100, 
            color="blue", 
            marker="*",
            label="Main Venue"
        )
    
    ax.set_title(title, fontsize=10, pad=10)# pad btw title & ax
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
        # gdf_pts.plot(ax=ax, color='blue', markersize=20)

    return




def layout_comparison_indep(dict_gdf_joined, gdf_map,
                gdf_venues,
                col, way, groupby,
                scheme, vmin, vmax, k_quantile, bins, cmap,
                suptitle, loc, # for filename
                n_axes=3, n_cols=3,#每行最多几张（列）
                save=False, output_folder=None, filename=None):
    
    # overall vmin & vmax & values
    if not vmin and not vmax:     
        vmin, vmax=0,0
        values=[]        
        for ym, gdf_joined in dict_gdf_joined.items():
            groups=get_groups(gdf_joined=gdf_joined, col=col, way=way, groupby=groupby)
            vmin_current= groups[way].min()
            vmax_current=groups[way].max()
            values_current=groups[way]
            values.extend(values_current)
            
            if vmin>vmin_current:
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
        figsize=(6* n_cols, 5 * n_rows)
    )
    axes = axes.flatten()

    # --------------------------plot-----------------------------    
    i=0
    for subtitle_ym, gdf_joined in dict_gdf_joined.items():
        get_choropleth_map(gdf_joined=gdf_joined, 
            gdf_venues=gdf_venues,
            gdf_map=gdf_map, 
            col=col, way=way, groupby=groupby,
            title=subtitle_ym,
        
            fig=fig, subax=axes[i], vmin=vmin, vmax=vmax,values=values, bins=None,  #oblig for subplots   
            scheme='quantile', k_quantile=10, cmap=cmap, # colors
            
            save=False, loc=None, ym=None,# for automatic filename 
            output_folder=None,filename=None
        )

        i+=1   
    #shut down
    for j in range(i, len(axes)):
         axes[j].axis("off")
                 
    # add cbar_scheme: same vmin/vmax/values as map
    add_cbar_scheme(
        fig,
        scheme=scheme,      # "continuous" | "quantile" | "custom"        
        # 1) continus input
        vmin=vmin,
        vmax=vmax,
        # 2) quantile input
        values=values,              # for scheme quantile
        k_quantile=k_quantile,                      # number of classes for quantile
        # 3) custom input
        bins=bins,               
        # layout
        on_right=True,
        cbar_label=f"{col} ({way})",
        cmap=cmap,
        tick_format="{:.2f}"
    )
    

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
        groups= get_groups(gdf_joined, col=col, way=way, groupby=groupby)
        groups_for_gap.append(groups)               
        
    df_gap=groups_for_gap[0].merge(groups_for_gap[1], left_on=groupby, right_on=groupby, how='left')
    df_gap['gap']=df_gap[f'{way}_y']-df_gap[f'{way}_x']
    
    # vmin_gap_current=df_gap['gap'].min()
    # vmax_gap_current=df_gap['gap'].max()

    return df_gap
    
    

    
def get_choropleth_map_gap(dict_gdf_joined, 
            gap_between,
            gdf_map, 
            gdf_venues, 
            col, way, groupby,
            title='Gap map',
            add_buffer_m=None,
            fig=None, subax=None, vmin=None, vmax=None,values=None,bins=None,  #oblig for subplots   
            scheme='quantile', k_quantile=10, cmap="OrRd", # colors
            save=False, loc=None, ym=None, # for filename
            output_folder=None,filename=None
        ):    

    df_gap= get_groups_gap(dict_gdf_joined, gap_between,
                      col=col, way=way, groupby=groupby) 
    
    # merge
    gdf_merged = gdf_map.merge(df_gap, on=groupby, how="left")


    #----------------------------plot-----------------------------
    if not subax:        # 单图:打开cbar，单独ax，取当前vmin，vmax(无外部输入)

        fontsize_text=8 
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        # vmin, vmax=vmin_gap_current, vmax_gap_current

        vmin, vmax, values = df_gap['gap'].min(), df_gap['gap'].max() ,df_gap['gap']
        
        
        # same color for map and cbar:
        bounds, norm=build_bounds_norm(
            scheme=scheme,
            vmin=vmin,
            vmax=vmax,
            values=values,
            k_quantile=5,
            bins=bins,
            cmap=cmap
        )
        
        # add color to map :  
        gdf_merged.plot(
            column='gap',
            ax=ax,
            # vmin=vmin,
            # vmax=vmax,
            legend=False,
            norm=norm,
            cmap=cmap,
            edgecolor="black",
            linewidth=0.5
        )
        
        # show cbar:
        add_cbar_scheme(
            fig,
            scheme=scheme,      # "continuous" | "quantile" | "custom"
            # 1) continus input
            vmin=vmin,
            vmax=vmax,
            # 2) quantile input
            values=values,              # for scheme quantile
            k_quantile=k_quantile,                      # number of classes for quantile
            # 3) custom input
            bins=bins,              
            
            # layout
            on_right=True,
            cbar_label=f"écart de {col} ",
            cmap=cmap,
            tick_format="{:.2f}"
        )            

    
    else : # 小图
        fontsize_text=5
        ax=subax
        
        ## same bounds for gdf plot and cbar!!!
        bounds, norm=build_bounds_norm(
            scheme=scheme,
            vmin=vmin,
            vmax=vmax,
            values=values,
            k_quantile=k_quantile,
            bins=bins,
            cmap=cmap
        )
        gdf_merged.plot(
            column='gap',
            ax=ax,
            legend=False,
            norm=norm,
            cmap=cmap,
            edgecolor="black",
            linewidth=0.5
        )

        
    # 坐标与文字：
    
    for idx, row in gdf_merged.iterrows():
        x = row.geometry.centroid.x
        y = row.geometry.centroid.y
        if row["gap"]>=0:
            gap_label=f"+ {row['gap']:.2f}"
        else :
            gap_label=f"- {row['gap']:.2f}"
        
        ax.text(
            x, y,
            f"{int(row[groupby])} arr :\n{gap_label}",#*
            ha="center",
            va="center",
            fontsize=fontsize_text,
            linespacing=1.2,
        )
        
    #--------------------------venues------------------------------
    if not gdf_venues is None and not gdf_venues.empty:
        label="Sites olympiques"
        if add_buffer_m!=None and add_buffer_m!=0:
            draw_buffer(ax, gdf_venues, buffer_dist=add_buffer_m, buffer_label="Venue buffer")
            label=f"Sites olympiques (buffer {add_buffer_m/1000:.1f}km)"
        
        # center
        gdf_venues = gdf_venues.to_crs(gdf_merged.crs)
        gdf_venues.plot(
            ax=ax, 
            markersize=100, 
            color="blue", 
            marker="*",
            label=label
        )
    ax.set_title(title, fontsize=10, pad=10)# pad btw title & ax
    ax.axis("off")

    
    # SAVE: 非子图，由outpath才保存
    if not subax and save and output_folder:
        os.makedirs(output_folder, exist_ok=True)
        if not filename:        
            filename=f"gap_map_{col}_{way}_{loc}{'-'.join(gap_between)}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✔ [SAVE]  choropleth gap map saved to {outpath_fig}!")
        plt.show()
    
    return




def layout_comparison_gap(dict_gdf_joined, 
                gdf_map,
                gdf_venues=None,add_buffer_m=None,
                gap_groups=[['T1 2024', "T2 2024"], ["T1 2024","T3 2024"]],
                col=None, way=None, groupby=None,
                scheme="quantile", vmin=None, vmax=None, k_quantile=10, bins=None, cmap="orRd",
                suptitle='gap comparaison', loc="Paris", # for filename
                n_axes=2, n_cols=3,#每行最多几张（列）
                save=False, output_folder=None, filename=None):
    
    # overall vmin & vmax & values
    vmin, vmax, values =0, 0, []
    for gap_between in gap_groups:
        df_gap= get_groups_gap(dict_gdf_joined, gap_between,
                        col=col, way=way, groupby=groupby) 
        vmin_current, vmax_current,values_current = df_gap['gap'].min(), df_gap['gap'].max(),df_gap['gap']

        if vmin > vmin_current:
            vmin=vmin_current
        if vmax < vmax_current:
                vmax=vmax_current
        values.extend(values_current)
        
        
    # axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6* n_cols, 5 * n_rows)
    )
    axes = axes.flatten()
    
    
    i=0
    for i, gap_between in enumerate(gap_groups):
        get_choropleth_map_gap(dict_gdf_joined=dict_gdf_joined, 
                gap_between=gap_between,
                gdf_map=gdf_map, 
                gdf_venues=gdf_venues, 
                col=col, way=way, groupby=groupby,
                title=f'Evolution de {col} ({way}) du {gap_between[0]} au {gap_between[1]} à {loc}',
                add_buffer_m=add_buffer_m,
                fig=fig, subax=axes[i], vmin=vmin, vmax=vmax,values=values,bins=bins,  #oblig for subplots   
                scheme=scheme, k_quantile=k_quantile, cmap=cmap, # colors
                # save=False, loc=None, ym=None, # for filename
                # output_folder=None,filename=None
            )
    for j in range(i, len(axes)):
         axes[j].axis("off")    
               
    # add cbar_scheme: same vmin/vmax/values as map
    add_cbar_scheme(
        fig,
        scheme=scheme,      # "continuous" | "quantile" | "custom"        
        # 1) continus input
        vmin=vmin,
        vmax=vmax,
        # 2) quantile input
        values=values,              # for scheme quantile
        k_quantile=k_quantile,                      # number of classes for quantile
        # 3) custom input
        bins=bins,               
        # layout
        on_right=True,
        cbar_label=f"{col} ({way})",
        cmap=cmap,
        tick_format="{:.2f}"
    )
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
            filename=f"gap_comparaison_{col}_{way}_{loc}-{'-'.join(dict_gdf_joined.keys())}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    
    plt.show()     
        
        
    return    
   




##==============================choropleth+ratio+buffer=====================================
def draw_buffer(ax, gdf_points, buffer_dist=3000, buffer_label="Venue buffer"):
    """
    在地图上绘制 gdf_points 的缓冲区（单位：米）
    """
    # 1. 转为米（EPSG:2154）
    gdf_m = gdf_points.to_crs(epsg=2154)

    # 2. 计算 buffer（米）
    gdf_m["buffer"] = gdf_m.geometry.buffer(buffer_dist)

    # 3. 将 geometry 改为 buffer（关键步骤）
    gdf_buffer = gdf_m.set_geometry("buffer")

    # 4. 转回 WGS84（EPSG:4326）
    gdf_buffer = gdf_buffer.to_crs(epsg=4326)

    # 5. 绘制
    gdf_buffer.plot(
        ax=ax,
        edgecolor="skyblue",
        facecolor="skyblue",
        linewidth=1.2,
        alpha=0.1,
        label=buffer_label
    )
    return #gdf_buffer




def get_choro_circle_map(groups, gdf_map, gdf_venues=None,add_buffer_m=None, 
            col_choropleth="ratio", col_circle="count", 
            groupby="c_ar",
            vmin_choro=None, vmax_choro=None, 
            vmin_circle=None, vmax_circle=None, 
            fig=None, subax=None,
            k=None,cmap=None,
            title_cbar="Part des hôtes réactifs",
            title="Part des hôtes réactifs par arrondissement et localisation des sites olympiques"
        ):
    print(f"[input] CIRCLE (COUNT) vmin vmax :{vmin_circle}-{vmax_circle}")

    if cmap==None:    
        base = plt.cm.OrRd
        colors = base(np.linspace(0.2, 0.7, 256))  # 只取中间浅色段
        cmap_light = LinearSegmentedColormap.from_list("OrRd_light", colors)
        cmap=cmap_light
   
    gdf_merged = gdf_map.merge(groups, on=groupby, how="left")
    # display(gdf_merged)
    
    
    if not subax:
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    else :
        ax=subax
        
        
    # -------------------------choropleth-------------------------------
    if col_choropleth:
        if not subax and  vmin_choro is None and vmax_choro is None:
            vmin_choro=groups[col_choropleth].min()
            vmax_choro=groups[col_choropleth].max()
            print("vmin vmax of current groups:", vmin_choro, vmax_choro)
        else :
            print(f"[input] CHORO (RATIO) vmin vmax :{vmin_choro}-{vmax_choro}")
        
        gdf_merged.plot(
            column=col_choropleth,
            ax=ax,
            vmin=vmin_choro,
            vmax=vmax_choro,
            legend=False, #默认都不画cbar，自动生成的难以控制位置和大小
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
                f"{int(row[groupby])} arr\n{row[col_choropleth]*100:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                linespacing=1.2,
            )
        if not subax: 
            add_cbar(vmin=vmin_choro, vmax=vmax_choro, 
                fig=fig, on_right=True, 
                cbar_label='proportion de hôte', cmap=cmap)

    #----------------------porportional circle--------------------
    if col_circle:
        if not vmin_circle and not vmax_circle :
            vmin_circle=groups[col_circle].min()
            vmax_circle=groups[col_circle].max()
            
        if not k :            
            max_marker_area = 5000  # 你视觉上觉得最大的圆
            k = max_marker_area / vmax_circle
            print(f"suitable k : {k}!")

        # k = 5  # 缩放因子，按效果调
        centroids = gdf_merged.geometry.centroid
        ax.scatter(
            centroids.x,
            centroids.y,
            s = gdf_merged[col_circle] * k,   # ← 可替换
            facecolors="none",
            edgecolors="black",
            linewidth=1,
            zorder=2
        )   
        if not subax:        
            add_circle_legend(k=5, vmin_circle=vmin_circle, vmax_circle=vmax_circle,fig=fig)
            
        
    
    #--------------------------venues------------------------------
    if not gdf_venues is None and not gdf_venues.empty:
        label="Sites olympiques"
        if add_buffer_m!=None and add_buffer_m!=0:
            draw_buffer(ax, gdf_venues, buffer_dist=add_buffer_m, buffer_label="Venue buffer")
            label=f"Sites olympiques (buffer {add_buffer_m/1000:.1f}km)"
        
        # center
        gdf_venues = gdf_venues.to_crs(gdf_merged.crs)
        gdf_venues.plot(
            ax=ax, 
            markersize=100, 
            color="blue", 
            marker="*",
            label=label
        )
    #-------------------------titile------------------------
    ax.set_title(title, fontsize=10, pad=10)# pad btw title & ax
    ax.axis("off")
    # ax.legend()
    # plt.show()
  
    return plt




# def get_choro_circle_map(groups, gdf_map, gdf_venues=None,add_buffer_m=None, 
#             col_choropleth="ratio", col_circle="count", 
#             groupby="c_ar",
#             vmin_choro=None, vmax_choro=None, 
#             vmin_circle=None, vmax_circle=None, 
#             fig=None, subax=None,
#             k=None,cmap=None,
#             title_cbar="Part des hôtes réactifs",
#             title="Part des hôtes réactifs par arrondissement et localisation des sites olympiques"
#         ):
#     print(f"[input] CIRCLE (COUNT) vmin vmax :{vmin_circle}-{vmax_circle}")

#     if cmap==None:    
#         base = plt.cm.OrRd
#         colors = base(np.linspace(0.2, 0.7, 256))  # 只取中间浅色段
#         cmap_light = LinearSegmentedColormap.from_list("OrRd_light", colors)
#         cmap=cmap_light
   
#     gdf_merged = gdf_map.merge(groups, on=groupby, how="left")
#     # display(gdf_merged)
    
    
#     if not subax:
#         fig, ax = plt.subplots(1, 1, figsize=(12, 10))
#     else :
#         ax=subax
        
        
#     # -------------------------choropleth-------------------------------
#     if col_choropleth:
#         if not subax and  vmin_choro is None and vmax_choro is None:
#             vmin_choro=groups[col_choropleth].min()
#             vmax_choro=groups[col_choropleth].max()
#             print("vmin vmax of current groups:", vmin_choro, vmax_choro)
#         else :
#             print(f"[input] CHORO (RATIO) vmin vmax :{vmin_choro}-{vmax_choro}")
        
#         gdf_merged.plot(
#             column=col_choropleth,
#             ax=ax,
#             vmin=vmin_choro,
#             vmax=vmax_choro,
#             legend=False, #默认都不画cbar，自动生成的难以控制位置和大小
#             cmap=cmap,       
#             edgecolor="black",
#             linewidth=0.5
#         ) 

#         # 坐标与文字：
#         for idx, row in gdf_merged.iterrows():
#             x = row.geometry.centroid.x
#             y = row.geometry.centroid.y
#             ax.text(
#                 x, y,
#                 f"{int(row[groupby])} arr\n{row[col_choropleth]*100:.1f}%",
#                 ha="center",
#                 va="center",
#                 fontsize=8,
#                 linespacing=1.2,
#             )
#         if not subax: 
#             add_cbar(vmin=vmin_choro, vmax=vmax_choro, 
#                 fig=fig, on_right=True, 
#                 cbar_label='proportion de hôte', cmap=cmap)

#     #----------------------porportional circle--------------------
#     if col_circle:
#         if not vmin_circle and not vmax_circle :
#             vmin_circle=groups[col_circle].min()
#             vmax_circle=groups[col_circle].max()
            
#         if not k :            
#             max_marker_area = 5000  # 你视觉上觉得最大的圆
#             k = max_marker_area / vmax_circle
#             print(f"suitable k : {k}!")

#         # k = 5  # 缩放因子，按效果调
#         centroids = gdf_merged.geometry.centroid
#         ax.scatter(
#             centroids.x,
#             centroids.y,
#             s = gdf_merged[col_circle] * k,   # ← 可替换
#             facecolors="none",
#             edgecolors="black",
#             linewidth=1,
#             zorder=2
#         )   
#         if not subax:        
#             add_circle_legend(k=5, vmin_circle=vmin_circle, vmax_circle=vmax_circle,fig=fig)
            
        
    
#     #--------------------------venues------------------------------
#     if not gdf_venues is None and not gdf_venues.empty:
#         label="Sites olympiques"
#         if add_buffer_m!=None and add_buffer_m!=0:
#             draw_buffer(ax, gdf_venues, buffer_dist=add_buffer_m, buffer_label="Venue buffer")
#             label=f"Sites olympiques (buffer {add_buffer_m/1000:.1f}km)"
        
#         # center
#         gdf_venues = gdf_venues.to_crs(gdf_merged.crs)
#         gdf_venues.plot(
#             ax=ax, 
#             markersize=100, 
#             color="blue", 
#             marker="*",
#             label=label
#         )
#     #-------------------------titile------------------------
#     ax.set_title(title, fontsize=10, pad=10)# pad btw title & ax
#     ax.axis("off")
#     # ax.legend()
#     # plt.show()
  
#     return plt




def get_groups_count_ratio(gdf_joined, col_choropleth, col_circle, groupby="c_ar"):
    # col_choropleth==col_cirle
    
    groups = (
        gdf_joined
        .groupby(groupby, as_index=False)
        .agg(
            total_hosts=(col_choropleth, "count"),
            count=(col_circle, "sum"),
            ratio=(col_choropleth, "mean"),
        )
        .reset_index()
    )
    # display(groups)
    return groups




def layout_comparison_indep2(dict_gdf_joined, gdf_map,
                gdf_venues,add_buffer_m, 
                col, groupby, k, 
                suptitle, loc, # for filename
                n_axes, n_cols=3,#每行最多几张（列）
                save=False, output_folder=None, filename=None):
    dict_groups={}

    # vmin & vmax
    vmin_choro, vmax_choro=0,0
    vmin_circle, vmax_circle=0,0
    for ym, gdf_joined in dict_gdf_joined.items():
        groups=get_groups_count_ratio(gdf_joined=gdf_joined, col_choropleth=col,col_circle=col, groupby=groupby)
        dict_groups[ym]=groups
        #默认给ratio画choropleth，找到对应的cbar
        vmin_choro_current,vmax_choro_current=groups['ratio'].min(),groups['ratio'].max()
        # vmax_ratio_current=groups['ratio'].max()
        vmin_circle_current,vmax_circle_current=groups['count'].min(),groups['count'].max()
     
        if vmin_choro> vmin_choro_current:
            vmin_choro=vmin_choro_current
        if vmax_choro < vmax_choro_current:
            vmax_choro=vmax_choro_current
        
        
        if vmin_circle > vmin_circle_current:
            vmin_circle=vmin_circle_current
        if vmax_circle < vmax_circle_current:
            vmax_circle=vmax_circle_current

    print(f"[INFO] OVERALL RATIO vmin-vmax of {col}: {vmin_choro:.2f} ~ {vmax_choro:.2f}")    
    print(f"COUNT vmin-vmax of {col}: {vmin_circle:.2f} ~ {vmax_circle:.2f}")
       

    # axes
    n_rows = math.ceil(n_axes / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(12* n_cols, 10* n_rows)
    )
    axes = axes.flatten()
    print (f"[INFO] compa indep layout: {n_rows} rows x {n_cols} cols\n")

    # plot
    i=0
    for ym, groups in dict_groups.items():
        get_choro_circle_map(groups=groups, gdf_map=gdf_map, gdf_venues=gdf_venues,add_buffer_m=add_buffer_m, 
            col_choropleth="ratio", col_circle="count", 
            groupby="c_ar",
            vmin_choro=vmin_choro, vmax_choro=None, 
            vmin_circle=vmin_circle, vmax_circle=vmax_circle, 
            fig=fig, subax=axes[i],
            k=None,cmap=None,
            title_cbar=None,#小图中不显示cbar
            title=ym
        )           
                
        i+=1
        
    #shut down
    for j in range(i, len(axes)):
         axes[j].axis("off")
                 
    # add cbar
    add_cbar(vmin=vmin_choro, vmax=vmax_choro, 
             fig=fig, on_right=True, 
             cbar_label="part de hôte")       

    #legend
    n_levels = 3  # legend 等级数
    legend_values = np.linspace(vmin_circle, vmax_circle, n_levels)
    legend_values = np.round(legend_values / 100) * 100
    legend_values = legend_values.astype(int)
    print("legend_values:", legend_values)

    if not k :            
        max_marker_area = 5000  # 你视觉上觉得最大的圆
        k = max_marker_area / vmax_circle
    circle_handles = [
    plt.scatter(
            [], [],
            s=val * k/50 ,
            facecolors="none",
            edgecolors="black",
            linewidth=1,
            label=f"{val/50:.2f} hôtes"
        )
        for val in legend_values
    ]

    
    fig.legend(
        handles=circle_handles,
        title="Nombre",
        loc="upper right",
        bbox_to_anchor=(0.95, 0.95),  # 调整 legend 内部位置
        # bbox_to_anchor=(0.03, 0.97),  # ← 左上角留出一块“版面”
        frameon=True,

        fontsize=9,            # label 字号 ↑
        title_fontsize=10,     # 标题字号 ↑
        markerscale=1.4,       # 关键：放大圆
        handlelength=1.6,      # 色块/符号长度
        labelspacing=0.6,      # 行距
        borderpad=0.6          # 内边距
    )



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
            filename=f"indep_comparaison_{col}_{loc}-{'-'.join(dict_gdf_joined.keys())}.jpg"
        outpath_fig=os.path.join(output_folder,filename)   
        fig.savefig(outpath_fig, dpi=300)      
        print(f"✅ [SAVE] map saved to {outpath_fig}!")
    
    plt.show()
    
    return



 

# def layout_comparison_gap (dict_gdf_joined, gdf_map,
#                         ym_key,
#                         col, way, groupby,
#                         n_axes, n_cols=3,
#                         gdf_venues=None,
#                         suptitle=None, loc=None,#for filename
#                         save=False, output_folder="../output_map",
#                         filename=None
#                         ):
#     ## experimental group : 2406 ; control groups 2403, 2409 
#     # 只能有一个实验组，其余均是对照组？
    
    
#     ## ------------------------------vmin vmax-----------------------------------
#     # key  
#     groups_density = get_groups(gdf_joined=dict_gdf_joined[ym_key],
#             col=col, way=way, groupby=groupby)
    
#     # ref        
#     ym_refs=[i for i in dict_gdf_joined.keys() if i !=ym_key]    

#     vmin_gap, vmax_gap=0,0
#     for ym_ref in ym_refs:    
#         df_gap, vmin_gap_current, vmax_gap_current=get_groups_gap(dict_gdf_joined, 
#                     gap_between=[ym_key, ym_ref],
#                     col=col, way=way, groupby=groupby)
#         if vmin_gap> vmin_gap_current:
#             vmin_gap=vmin_gap_current
#         if vmax_gap < vmax_gap_current:
#             vmax_gap=vmax_gap_current
                   
#     # print(f"[INFO] vmin_density:{vmin_density}, vmax_density:{vmax_density} ")
#     # print(f"[INFO]OVERALL vmin_gap :{vmin_gap}, OVERALL vmax_gap:{vmax_gap}!\n")
                
    
   
#     # #-----------------------------axes--------------------------------    
#     ## layout axes
#     n_rows = math.ceil(n_axes / n_cols)
#     fig, axes = plt.subplots(
#         n_rows,
#         n_cols,
#         figsize=(10* n_cols, 8* n_rows)
#     )
#     axes = axes.flatten()
#     print (f"[INFO] compa gap layout: {n_rows} rows x {n_cols} cols\n")

    
#     ## -----------------------------plot--------------------------------
#     i=0
#     for ym, gdf_joined in dict_gdf_joined.items():
#         if ym ==ym_key:#中间正常显示值 
#             get_choropleth_map(gdf_joined=gdf_joined, 
#                 gdf_map=gdf_map, 
#                 gdf_venues=gdf_venues,
#                 col=col, way=way, groupby=groupby,
#                 subtitle=ym,
#                 fig=fig, subax=axes[i], vmin=vmin_density, vmax=vmax_density,# oblig for subplot
#                 save=False, loc=loc, ym=ym, 
#                 output_folder=None,filename=None
#             )      
        
#         else : #参照组显示gap             
#             gap_between=[ym_key, ym]#key放前面,x的位置!                     
#             get_choropleth_map_gap(dict_gdf_joined, 
#                     gap_between=gap_between,
#                     gdf_map=gdf_map, 
#                     col=col, way=way, groupby=groupby,
#                     subtitle=f"{ym} comparé au {ym_key}",
#                     fig=fig, subax=axes[i], 
#                     vmin=vmin_gap, vmax=vmax_gap,# optionel
#                     save=False, loc=loc, ym=ym, 
#                     output_folder=None,filename=None
#                 )                    
#         i+=1
    
#     # shutdown else
#     for j in range(i, len(axes)):
#          axes[j].axis("off")
    
    
#     #--------------------------------cbar---------------------------------#
    
#     # # 已经在_ax中给map画了在vmin， vmax范围内的color
#     ## 左边 cbar_gap
#     add_cbar(vmin=vmin_gap, vmax=vmax_gap, 
#              fig=fig, on_right=False, 
#              col=col, way='gap')
    
#     # 右边cbar_density
#     add_cbar(vmin=vmin_density, vmax=vmax_density, 
#              fig=fig, on_right=True, 
#              col=col, way=way)   
    
    
#     # suptitle：
#     plt.suptitle(
#             suptitle,
#             fontsize=20,
#             fontweight="bold",
#             # y=0.98
#         )

    
#     # no layout tight!!!!!

#     ## save
#     if save and output_folder:
#         os.makedirs(output_folder, exist_ok=True)
#         filename=f"gap_comparaison_{col}_{way}_{loc}{'-'.join(dict_gdf_joined.keys())}.jpg"
#         outpath_fig=os.path.join(output_folder,filename)   
#         fig.savefig(outpath_fig, dpi=300)      
#         print(f"✅ [SAVE] comparasion gap map saved to {outpath_fig}!")
#     plt.show()
       
    
#     return












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
    
    
    
    
    