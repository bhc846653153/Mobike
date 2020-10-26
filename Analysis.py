###############数据分析###############

import pandas as pd
import datetime
from math import radians, cos, sin, asin, sqrt

####导入数据并对相关数据进行查看####
from pyecharts.commons.utils import JsCode

df = pd.read_csv("mobike_shanghai_sample_updated.csv",sep=",",parse_dates=["start_time","end_time"])  # 导入csv数据文件,将start_time转换为日期列，避免后续字符串和datetime的转换
df.head()  #查看前5条数据集
df.info()  #查看字段 其中orderid 订单号,bikeid 车辆ID,userid 用户ID,starttime 骑行起始日期时间,start_location_和start_location_y骑行起始位置.endtime 骑行终止日期时间end_location_和end_location_y骑行终止位置.track轨迹
df.shape   #数据集大小
df.bikeid.unique().size   #数据涵盖了近8万的单车，unique函数去除其中重复的元素，并按元素由大到小返回一个新的无重复元素
df.userid.unique().size   # 数据涵盖了1万+的骑行用户
df.describe()  #描述性统计



####分析用户骑行轨迹（track）####
# 用haversine公式计算球面两点间的距离
def geodistance(item):
        lon1, lat1, lon2, lat2 = map(radians,[item["start_location_x"], item["start_location_y"], item["end_location_x"],item["end_location_y"]])  # 将经纬度转换为弧度
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        dis = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        distance = 2 * asin(sqrt(dis)) * 6317 * 1000  # 地球的平均半径为6371km
        distance = round(distance / 1000, 3)
        return distance
df["distance"] = df.apply(geodistance, axis=1)


#通过单车的轨迹获取每次交易骑行的路径
def geoaadderLength(item):
    track_list = item["track"].split("#")
    adderLength_item ={}
    adderLength = 0
    for i in range (len(track_list)-1):
        start_loc = track_list[i].split(",")
        end_loc = track_list[i+1].split(",")
        adderLength_item["start_location_x"],adderLength_item["start_location_y"] = float(start_loc[0]),float(start_loc[1])
        adderLength_item["end_location_x"],adderLength_item["end_location_y"] = float(end_loc[0]),float(end_loc[1])
        adderLength_each = geodistance(adderLength_item)
        adderLength = adderLength_each + adderLength
    return adderLength
df["adderLength"] = df.apply(geoaadderLength,axis=1)
df.sort_values(["adderLength"],ascending=True)
#设置切分区域
listBins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 50,100,1000]
len(listBins)
#设置切分后对应标签
listLabels = ['0_1','1_2','2_3','3_4','4_5','5_6','6_7','7_8','8_9','9_10','10_15','15_20','20_25','25_30','30_50','50_100','100+']
type(listLabels)
df["length_num"] = pd.cut(df['adderLength'], bins=listBins, labels=listLabels, include_lowest=True)
# length_num = df['length_num'].groupby(df['length_num']).count()
# length_num['listLabels'] = length_num.reset_index()
# length_num.columns = ['num']
# le_bins = list(length_num[''])
# le_num = list(length_num['length_num'])
num1 = df['length_num'].groupby(df['length_num']).count() #计算每小时订单数并用index把索引列hour生成普通列
num1 = list(num1)
####时间处理####
#apply()函数的基本形式为：DataFrame.apply(func, axis=0, broadcast=False, raw=False, reduce=None, args=(), **kwds)
#其中，func是你想要这个DataFrame应用的函数，可以自己编写，也可以是已经存在的，相当于C/C++的函数指针。如果这个参数是自己实现的话，函数的传入参数根据axis来定，比如axis = 1，就会把一行数据作为Series的数据结构传入给自己实现的函数中，
#我们在函数中实现对Series不同属性之间的计算，返回一个结果，则apply函数会自动遍历每一行DataFrame的数据，最后将所有结果组合成一个Series数据结构并返回。

df["weekday"] = df["start_time"].apply(lambda s: s.weekday())  #使用weekday函数提取周几信息，周一为0，周日为6
df['daytype'] = df["weekday"].apply(lambda x: 'weekend' if x == 5 or x == 6 else 'workday')  #将周几分为工作日（workday)和周末(weekend)
df["day"] = df["start_time"].apply(lambda s:str(s)[:10])  #提取时间中的日期
df["hour"] = df["start_time"].apply(lambda s: s.hour)   # 提取小时数，hour属性
df["minute"] = df["start_time"].apply(lambda s: s.minute)  # 提取分钟数，minute属性


####分析24小时骑行订单数分布情况####
#python中groupby函数主要的作用是进行数据的分组以及分组后地组内运算！
#df["orderid"](指输出数据的结果属性名称为订单号).groupby([df[“hour”])(指分类的属性，数据的限定定语，为时间点).count()(对于数据的计算方式——函数名称)
hour_group = pd.DataFrame((df["orderid"].groupby(df["hour"]).count())).reset_index() #计算每小时订单数并用index把索引列hour生成普通列
hour_group.sort_values(["hour"],ascending=True) #把hour进行降序排列

data_orderids = list(hour_group['orderid'])
data_hoursum = list(hour_group["hour"])



####分析工作日和周末订单数分布情况####
g1 = df.groupby(["daytype","hour"])
week = pd.DataFrame(g1['orderid'].count()).reset_index()
weekend = week[week['daytype'].isin(["weekend"])]
workday = week[week['daytype'].isin(["workday"])]

####分析工作日和周末占比率####
idsum = week['orderid'].sum()
weeksum = weekend['orderid'].sum() / idsum
worksum = workday['orderid'].sum() / idsum

workday = list(workday["orderid"])
weekend = list(weekend["orderid"])


####分析自行车被使用的情况####（总时长lag和总次数num）
t1 = df['bikeid'].groupby(df['bikeid']).count() #相同id单车被使用的次数，groupby函数主要的作用是进行数据的分组以及分组后地组内运算
df["lag"] = (df.end_time-df.start_time).dt.seconds/60  #每个单车被使用的时间
t2 = (df['lag'].groupby(df["bikeid"]).sum()).sort_values(ascending=False)  #计算相同id的单车使用的总时长,并进行降序
df3 = pd.merge(t1, t2,left_index=True, right_on='bikeid', how="left")  #将相同id单车被使用的次数和总时长放在一个列表，其中索引列bikeid当作连接键,left_index=True, right_on=‘bikeid’，表示左表连接键作为索引、右边连接键作为普通列
df3['index1'] = df3.index  #生成bikeid列
df3.columns = ['num','lag','bikeid']  #用columns改表头num、lay、bikeid
df3 = df3.sort_values(["num"],ascending=False).head(100) #对总次数进行降序排列，并取出前100


####分析起始位置&结束位置####(track[0][-1])
####空闲单车&紧缺单车(瓜分区块，原的数量，后的数量)####


#可视化
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Grid, Liquid
#用户路程图
a = (
    Bar()
    .add_xaxis(listLabels)
    .add_yaxis("用户人数", num1,color="#d48265")
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="用户路程分布图"),
        xaxis_opts=opts.AxisOpts(name="人数"),
        yaxis_opts=opts.AxisOpts(name="km"),
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=False),)
    .render("bar_datazoom_slider.html")
)
#工作日和周末的订单数分布折线图
c = (
    Line()
    .add_xaxis(data_hoursum)
    .add_yaxis("工作日", workday, color="#749f83")
    .add_yaxis("周末", weekend, color="#61a0a8")
    .set_series_opts(
        areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
        label_opts=opts.LabelOpts(is_show=False),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="工作日和周末的订单数分布折线图"),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        yaxis_opts=opts.AxisOpts(
            type_="value",
            axistick_opts=opts.AxisTickOpts(is_show=True),
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
    )

    .render("line_base.html")
)

# 周末和工作日的订单量占比图
l1 = (
    Liquid()
    .add("周末订单占比", [0.13], center=["70%", "50%"])
    # .set_global_opts(title_opts=opts.TitleOpts(title="多个 Liquid 显示"))
)

l2 = Liquid().add(
    "工作日订单占比",
    [0.87],
    center=["25%", "50%"],
    label_opts=opts.LabelOpts(
        font_size=25,
        formatter=JsCode(
            """function (param) {
                    return (Math.floor(param.value * 10000) / 100) + '%';
                }"""
        ),
        position="inside",
    ),
)

grid = Grid().add(l1, grid_opts=opts.GridOpts()).add(l2, grid_opts=opts.GridOpts())
grid.render("multiple_liquid.html")

# 前100辆单车的使用情况
data2 = list(df3['bikeid'])
data3 = list(df3['num'])
data4 = list(df3['lag'])
x_data = (data2)  #x轴数值为data2：bikeid
colors = ["#fab27b","#83bff6"]
bar = (
    Bar()
    .add_xaxis(xaxis_data=x_data)
    .add_yaxis("总时长",data4, stack="stack1", color=colors[0])
    .add_yaxis("总次数",data3, stack="stack1", color=colors[1])
    .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="前100辆单车的使用情况"),
        datazoom_opts=opts.DataZoomOpts(),
    )
)

bar.render("overlap_bar_line.html")

# 24小时订单量分布图
b= (
    Bar()
    .add_xaxis(data_hoursum)
    .add_yaxis("订单量", data_orderids , color="#2378f7")
    .set_global_opts(
        title_opts=opts.TitleOpts(title="24小时订单量分布图"),
        xaxis_opts=opts.AxisOpts(name="小时"),
        yaxis_opts=opts.AxisOpts(name="订单量"),
    )
    .set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
        markline_opts=opts.MarkLineOpts(
            data=[
                opts.MarkLineItem(type_="average", name="平均值"),
            ]
        ),
    )
        .render("df2.html")
)
