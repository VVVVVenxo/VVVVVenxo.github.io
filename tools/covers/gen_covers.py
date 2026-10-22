#!/usr/bin/env python3
"""Generate editorial technical covers with title-specific SVG diagrams."""
import glob
import html
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSTS = os.path.join(BASE, "source", "_posts")
GEN = os.path.join(BASE, "source", "img", "covers", "gen")
PREFIX = "/img/covers/gen/"
BG, GRID = "#E8ECE9", "#AEBDB7"
INK, MUTED, TEAL, ORANGE = "#17343B", "#61747A", "#287B73", "#C47743"
PALE, MINT, SOFT = "#F4F6F3", "#D8E6E0", "#AABBB4"
FONT = "'Microsoft YaHei','Noto Sans SC',sans-serif"
MONO = "Consolas,'Microsoft YaHei',monospace"
CAPTIONS = {
    "sorting": "比较与移动，让无序区逐步缩小", "graph": "扩展搜索边界，并记录抵达路径",
    "hash": "计算索引；冲突时继续寻找位置", "memory": "栈上指针保存地址，堆上对象独立存放",
    "dispatch": "对象通过虚表找到最终函数入口", "move": "资源所有权从旧对象交接给新对象",
    "vector": "连续存储随容量增长而重新分配", "language": "编译、运行与类型信息各司其职",
    "iterator": "按需推进位置，而非复制整段序列", "reflection": "运行时读取类型元数据并调用目标",
    "parameters": "值传递复制参数；引用传递共享原对象",
    "lifecycle": "对象经历创建、更新，最后离开场景",
    "physics": "模拟世界持续更新，并处理对象间的接触",
    "async": "任务等待完成，再恢复到合适的上下文",
    "animation": "关键帧定义属性值，插值补全连续运动",
    "assets": "定位资源、异步加载，再按生命周期释放",
    "render": "共享状态以减少重复提交与重建",
    "gc": "追踪根对象可达性，回收不再使用的内存",
    "network": "数据经过编码、传输，再由对端解析",
    "frame-sync": "广播玩家输入，各端按相同帧序推进",
    "state-sync": "服务端状态下发，并持续校正客户端",
    "process": "进程隔离地址空间，线程执行具体工作",
    "huffman": "高频符号走短路径，低频符号走长路径",
    "architecture": "模块各守边界，通过清晰接口协作",
    "learning": "输入、练习与复盘形成学习闭环",
    "reflection-notes": "观察经验、提炼判断，再回到实践",
    "ai-coding": "工具负责执行；人把握范围与最终判断",
    "ai-agent": "规划任务，调用工具，再依据反馈调整行动",
    "covers": "文章信息经过排版，生成可发布封面",
    "pipeline": "三维顶点经过坐标变换与光栅化，最终着色为屏幕像素",
}


def esc(value):
    return html.escape(str(value), quote=True)


def t(x, y, value, size=18, color=INK, weight=500, anchor="start", family=FONT):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>')


def rule(x1, y1, x2, y2, color=SOFT, width=2, dash=None, marker=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    extra += f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"{extra}/>'


def box(x, y, w, h, label, fill=PALE, stroke=SOFT, size=18, sub=None, mono=False):
    family = MONO if mono else FONT
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>']
    parts.append(t(x+w/2, y+(h/2+7 if not sub else h/2-3), label, size, INK, 650, "middle", family))
    if sub:
        parts.append(t(x+w/2, y+h/2+22, sub, 14, MUTED, 500, "middle", family))
    return "".join(parts)


def dot(cx, cy, radius=7, fill=TEAL, stroke=None):
    outline = f' stroke="{stroke}" stroke-width="2"' if stroke else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}"{outline}/>'


def node(cx, cy, label, fill=PALE, stroke=TEAL, radius=19):
    return (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            + t(cx, cy+6, label, 15, INK, 650, "middle"))


def defs():
    return '''<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#AEBDB7" stroke-width="1" opacity=".20"/></pattern>
<marker id="tealArrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9Z" fill="#287B73"/></marker>
<marker id="orangeArrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9Z" fill="#C47743"/></marker>'''


def diagram_sorting():
    vals, parts = [8, 3, 6, 1, 5, 4], [t(650, 205, "选择排序 · 第一轮", 21, INK, 650)]
    parts += [rule(650, 222, 1125, 222), t(650, 255, "无序序列", 16, MUTED)]
    for i, value in enumerate(vals):
        x, height = 686+i*70, value*15
        selected = value == 1
        parts += [t(x+24, 418-height-12, f"{value:02}", 19, ORANGE if selected else INK, 650, "middle"),
                  f'<rect x="{x}" y="{418-height}" width="48" height="{height}" fill="{ORANGE if selected else SOFT}"/>',
                  t(x+24, 444, str(i), 15, MUTED, 400, "middle")]
    parts += [rule(670, 418, 1110, 418, MUTED, 1.5), t(650, 495, "最小值 01", 17, ORANGE, 650),
              rule(757, 489, 824, 489, ORANGE, 2, marker="orangeArrow"), box(842, 470, 52, 38, "01", TEAL, TEAL, 18),
              t(909, 495, "进入有序区", 17, MUTED)]
    return "".join(parts)


def diagram_graph():
    points = [(700,310),(795,260),(795,375),(900,310),(925,430),(1040,260),(1080,375)]
    edges = [(0,1),(0,2),(1,3),(2,3),(2,4),(3,5),(3,6),(4,6),(5,6)]
    route = {tuple(sorted(edge)) for edge in [(0,2),(2,3),(3,5)]}
    parts = [t(650,205,"图搜索 · 扩展边界",21,INK,650), rule(650,222,1125,222)]
    for a,b in edges:
        active=tuple(sorted((a,b))) in route
        parts.append(rule(*points[a],*points[b],ORANGE if active else SOFT,3 if active else 1.5))
    for i,(x,y) in enumerate(points):
        active=i in (0,2,3,5)
        parts.append(node(x,y,str(i),"#F4E6D9" if i==0 else MINT if active else PALE,ORANGE if i==0 else TEAL if active else SOFT))
    parts += [dot(674,490,7,"#F4E6D9",ORANGE),t(692,496,"起点",15,MUTED),
              rule(760,490,804,490,ORANGE,3),t(817,496,"已发现路径",15,MUTED),t(650,535,"访问标记避免重复扩展",16,MUTED)]
    return "".join(parts)


def diagram_hash():
    parts=[t(650,205,"哈希索引 · 冲突处理",21,INK,650),rule(650,222,1125,222),t(675,260,"桶",16,MUTED),t(936,260,"冲突后继续探测",16,MUTED)]
    for i,value in enumerate(["—","key 12","—","—","—"]):
        y=275+i*43; active=i==1
        fill,stroke=("#F4E6D9",ORANGE) if active else (PALE,SOFT)
        parts += [f'<rect x="680" y="{y}" width="164" height="38" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
                  t(700,y+25,str(i),15,MUTED),t(758,y+25,value,16,ORANGE if active else INK,600)]
    parts += [t(680,510,"hash(key) = 1",16,TEAL,650,family=MONO),rule(845,316,920,316,ORANGE,2,marker="orangeArrow"),
              box(942,285,126,58,"key 12","#F4E6D9",ORANGE,17),rule(1068,314,1090,314,TEAL,2,marker="tealArrow"),
              box(1093,285,40,58,"…",MINT,TEAL,18)]
    return "".join(parts)


def diagram_memory():
    return "".join([t(650,205,"地址与对象的关系",21,INK,650),rule(650,222,1125,222),
        t(674,260,"栈区",18,TEAL,650),t(925,260,"堆区",18,TEAL,650),
        f'<rect x="650" y="274" width="214" height="212" fill="#F0F3F0" stroke="{SOFT}" stroke-width="2"/>',
        f'<rect x="905" y="274" width="226" height="212" fill="#F0F3F0" stroke="{SOFT}" stroke-width="2"/>',
        box(672,306,170,58,"p = 0x04A0",PALE,TEAL,17,mono=True),box(672,384,170,58,"count = 3",PALE,SOFT,17,mono=True),
        rule(844,335,930,335,TEAL,3,marker="tealArrow"),box(948,306,184,132,"Node",PALE,ORANGE,20,"value = 3"),
        t(970,423,"0x04A0",15,MUTED,500,family=MONO),t(650,526,"变量保存地址；对象位于独立存储区域",16,MUTED)])


def diagram_dispatch():
    return "".join([t(650,205,"一次虚函数调用",21,INK,650),rule(650,222,1125,222),
        box(655,300,132,88,"Derived",MINT,TEAL,18,"对象"),box(825,300,116,88,"vptr",PALE,SOFT,18,"0x1020",True),
        box(980,260,150,174,"vtable",PALE,ORANGE,18),rule(787,344,815,344,TEAL,2,marker="tealArrow"),
        rule(941,344,970,344,TEAL,2,marker="tealArrow"),t(994,322,"[0] Base::draw",13,MUTED,500,family=MONO),
        rule(993,334,1117,334,SOFT,1),t(994,364,"[1] Derived::draw",12,ORANGE,650,family=MONO),
        rule(993,376,1117,376,SOFT,1),t(994,406,"[2] ...",13,MUTED,500,family=MONO),
        t(650,518,"运行时类型决定最终调用入口",17,MUTED)])


def diagram_move():
    return "".join([t(650,205,"资源所有权交接",21,INK,650),rule(650,222,1125,222),
        box(672,294,168,112,"旧对象",PALE,SOFT,19,"buffer = 0xA0",True),box(968,294,168,112,"新对象",MINT,TEAL,19,"buffer = —",True),
        rule(842,326,954,326,ORANGE,3,marker="orangeArrow"),t(898,307,"move",14,ORANGE,650,"middle",MONO),
        rule(954,374,842,374,TEAL,2,"6 6","tealArrow"),t(650,518,"移动转移资源；旧对象仍能安全析构",17,MUTED)])


def diagram_vector():
    parts=[t(650,205,"vector · 连续存储",21,INK,650),rule(650,222,1125,222),
           t(665,264,"size = 4",15,TEAL,650,family=MONO),t(930,264,"capacity = 6",15,MUTED,600,family=MONO)]
    for i in range(6):
        x=666+i*75; filled=i<4
        fill,stroke=(MINT,TEAL) if filled else (PALE,SOFT)
        parts += [f'<rect x="{x}" y="290" width="70" height="62" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
                  t(x+35,328,str(i+1) if filled else "·",18,INK if filled else MUTED,600,"middle")]
    parts += [rule(676,378,935,378,TEAL,2,marker="tealArrow"),t(665,422,"push_back 超出容量",16,MUTED),
              box(684,460,382,48,"申请新块 · 搬移元素 · 更新容量","#F4E6D9",ORANGE,16),t(650,540,"扩容可能使已有迭代器失效",16,MUTED)]
    return "".join(parts)

def diagram_layers(kind, title):
    if kind == "language":
        heading=".NET 程序的运行路径"; layers=[("应用代码","C#"),("基础类库","BCL"),("运行时","CLR · GC · JIT"),("操作系统","Windows / Linux")]
    elif kind == "process":
        heading="进程隔离与线程执行"; layers=[("进程 A","独立地址空间"),("线程 1","执行任务"),("线程 2","共享进程资源"),("操作系统","调度与管理")]
    else:
        heading="职责按层次收敛"; layers=[("调用入口","API / facade"),("业务模块","domain logic"),("基础服务","resource · event"),("运行平台","engine / runtime")]
    parts=[t(650,205,heading,21,INK,650),rule(650,222,1125,222)]
    for i,(label,detail) in enumerate(layers):
        y=252+i*61; fill,stroke=(MINT,TEAL) if i==1 else (PALE,SOFT)
        parts += [box(686,y,280,49,label,fill,stroke,17),t(987,y+30,detail,14,MUTED,500,family=MONO)]
        if i<3: parts.append(rule(824,y+50,824,y+59,TEAL,2,marker="tealArrow"))
    parts.append(t(650,526,"各层通过稳定接口协作",17,MUTED))
    return "".join(parts)


def diagram_iterator():
    parts=[t(650,205,"迭代器推进游标",21,INK,650),rule(650,222,1125,222),t(650,272,"当前位置",16,ORANGE,650)]
    for i,value in enumerate("ABCDE"):
        x=666+i*88; active=i==2
        parts.append(box(x,310,68,66,value,MINT if active else PALE,TEAL if active else SOFT,21))
        parts.append(t(x+34,405,str(i),15,ORANGE if active else MUTED,500,"middle"))
    parts += [rule(838,285,838,304,ORANGE,2,marker="orangeArrow"),t(650,480,"begin()",16,MUTED,500,family=MONO),
              rule(735,474,1049,474,TEAL,2,marker="tealArrow"),t(1060,480,"end()",16,MUTED,500,family=MONO),
              t(650,526,"解引用读取当前位置；递增推进状态",16,MUTED)]
    return "".join(parts)


def diagram_reflection():
    return "".join([t(650,205,"运行时读取类型信息",21,INK,650),rule(650,222,1125,222),
        box(663,304,132,90,"Type",MINT,TEAL,20,"metadata"),box(858,260,150,66,"字段 / 方法",PALE,SOFT,16),
        box(858,365,150,66,"委托 / 事件","#F4E6D9",ORANGE,16),box(1050,365,83,66,"回调",PALE,SOFT,16),
        rule(795,330,846,293,TEAL,2,marker="tealArrow"),rule(795,367,846,398,ORANGE,2,marker="orangeArrow"),
        rule(1008,398,1038,398,ORANGE,2,marker="orangeArrow"),t(650,518,"反射读取元数据；委托保存可调用目标",16,MUTED)])


def diagram_parameters():
    return "".join([t(650,205,"调用时传递了什么",21,INK,650),rule(650,222,1125,222),
        t(690,266,"调用方",17,MUTED,600),t(960,266,"被调用函数",17,MUTED,600),
        box(675,292,165,68,"value = 7",PALE,SOFT,17,mono=True),box(675,398,165,68,"ref → object",MINT,TEAL,15,mono=True),
        box(960,292,165,68,"独立副本",PALE,SOFT,18),box(960,398,165,68,"同一对象","#F4E6D9",ORANGE,18),
        rule(840,326,948,326,SOFT,2,marker="tealArrow"),rule(840,432,948,432,ORANGE,3,marker="orangeArrow"),
        t(650,518,"值传递复制参数；引用传递别名到原对象",16,MUTED)])


def diagram_animation():
    parts=[t(650,205,"动画属性随时间变化",21,INK,650),rule(650,222,1125,222),
        t(650,278,"位置 X",16,MUTED),t(650,365,"旋转 Y",16,MUTED),
        rule(730,282,1110,282,SOFT,2),rule(730,366,1110,366,SOFT,2)]
    for x,y,label,color in [(760,282,"0",TEAL),(850,282,"1.2",ORANGE),(1002,282,"2.4",TEAL),(790,366,"0",TEAL),(940,366,"1.8",TEAL),(1080,366,"3.0",ORANGE)]:
        parts += [rule(x,y-14,x,y+14,color,2),dot(x,y,6,color),t(x,y+34,label,14,MUTED,500,"middle",MONO)]
    parts += [rule(730,444,1110,444,INK,1.5,marker="tealArrow"),t(650,450,"时间",16,MUTED),t(650,518,"插值决定关键帧之间的运动",17,MUTED)]
    return "".join(parts)


def diagram_lifecycle():
    labels=[("Awake","创建"),("OnEnable","激活"),("Start","首次运行"),("Update","逐帧"),("OnDestroy","销毁")]
    xs=[672,770,868,966,1064]; parts=[t(650,205,"MonoBehaviour 生命周期",21,INK,650),rule(650,222,1125,222)]
    for i,((name,note),x) in enumerate(zip(labels,xs)):
        color,fill=(ORANGE,"#F4E6D9") if i in (0,4) else (TEAL,MINT if i==3 else PALE)
        parts += [dot(x,326,20,fill,color),t(x,332,str(i+1),15,color,650,"middle"),
                  t(x,382,name,13,INK,650,"middle",MONO),t(x,409,note,13,MUTED,500,"middle")]
        if i<4: parts.append(rule(x+23,326,xs[i+1]-23,326,SOFT,2,marker="tealArrow"))
    parts += [rule(1085,437,706,471,ORANGE,1.5,"5 5","orangeArrow"),t(650,526,"启用、禁用与销毁也会改变回调顺序",16,MUTED)]
    return "".join(parts)


def diagram_physics():
    return "".join([t(650,205,"物体运动与碰撞",21,INK,650),rule(650,222,1125,222),
        rule(680,456,1110,456,INK,2),
        f'<path d="M700 420Q790 240 880 420T1060 420" fill="none" stroke="{TEAL}" stroke-width="3"/>',
        dot(700,420,9,TEAL),dot(880,420,9,ORANGE),dot(1060,420,9,TEAL),
        t(700,484,"t",15,MUTED,500,"middle",MONO),t(880,484,"t + Δ",15,MUTED,500,"middle",MONO),
        t(1060,484,"t + 2Δ",15,MUTED,500,"middle",MONO),t(650,526,"物理世界按固定时间步推进",17,MUTED)])


def diagram_async():
    return "".join([t(650,205,"协程与线程调度",21,INK,650),rule(650,222,1125,222),
        t(650,272,"主线程",16,TEAL,650),t(650,390,"工作线程",16,MUTED,650),
        rule(744,276,1120,276,SOFT,1.5),rule(744,394,1120,394,SOFT,1.5),
        box(770,244,112,62,"调用",MINT,TEAL,17),box(914,358,130,72,"耗时任务",PALE,SOFT,17,"I/O / CPU"),
        box(1070,244,72,62,"恢复",MINT,TEAL,16),rule(883,275,905,390,TEAL,2,marker="tealArrow"),
        rule(1045,390,1080,306,ORANGE,2,marker="orangeArrow"),t(650,518,"等待期间释放主线程执行权",17,MUTED)])


def diagram_assets():
    return "".join([t(650,205,"资源加载与释放",21,INK,650),rule(650,222,1125,222),
        box(650,310,105,78,"Catalog",PALE,SOFT,16),box(796,310,105,78,"Bundle",MINT,TEAL,16),
        box(942,310,105,78,"Asset",PALE,SOFT,16),box(1088,310,72,78,"实例","#F4E6D9",ORANGE,16),
        rule(755,349,787,349,TEAL,2,marker="tealArrow"),rule(901,349,933,349,TEAL,2,marker="tealArrow"),
        rule(1047,349,1079,349,ORANGE,2,marker="orangeArrow"),rule(1124,399,1124,458,ORANGE,2),
        rule(1124,458,650,458,ORANGE,2,marker="orangeArrow"),t(650,490,"释放句柄",15,ORANGE,600),
        t(650,526,"异步加载与生命周期决定资源占用",16,MUTED)])


def diagram_render(kind):
    if kind=="gc":
        return "".join([t(650,205,"从根对象追踪可达性",21,INK,650),rule(650,222,1125,222),
            box(665,286,104,66,"Root",MINT,TEAL,17),box(837,266,104,66,"A",PALE,SOFT,20),
            box(837,372,104,66,"B",PALE,SOFT,20),box(1010,266,104,66,"C",MINT,TEAL,20),
            box(1010,372,104,66,"D","#F4E6D9",ORANGE,20),rule(769,318,828,298,TEAL,2,marker="tealArrow"),
            rule(769,328,828,405,TEAL,2,marker="tealArrow"),rule(941,298,1000,298,TEAL,2,marker="tealArrow"),
            rule(941,405,1000,405,ORANGE,2,"5 5","orangeArrow"),t(650,510,"可达对象保留；不可达对象成为回收候选",16,MUTED)])
    return "".join([t(650,205,"界面到渲染批次",21,INK,650),rule(650,222,1125,222),
        box(650,310,108,80,"RectTransform",PALE,SOFT,13,sub="布局"),box(772,310,108,80,"Layout",PALE,SOFT,16,sub="计算"),
        box(894,310,108,80,"Canvas",MINT,TEAL,16,sub="组织批次"),box(1016,310,108,80,"Renderer",PALE,SOFT,13,sub="提交绘制"),
        rule(758,350,764,350,TEAL,2,marker="tealArrow"),rule(880,350,886,350,TEAL,2,marker="tealArrow"),
        rule(1002,350,1008,350,TEAL,2,marker="tealArrow"),t(650,510,"层级变化可能触发布局与 Canvas 重建",16,MUTED)])


def diagram_sync(kind):
    parts=[t(650,205,"客户端 A       服务端       客户端 B",17,INK,600),rule(650,222,1125,222)]
    lanes=[("客户端 A",278), ("服务端",366), ("客户端 B",454)]
    for label,y in lanes: parts += [t(650,y+5,label,14,MUTED),rule(740,y,1120,y,SOFT,1.5)]
    if kind=="frame-sync":
        for i,x in enumerate((790,900,1010)):
            parts += [rule(x,278,x+70,454,TEAL,2,marker="tealArrow"),t(x+8,350,f"输入 F{i+1}",13,TEAL)]
        parts.append(t(650,518,"广播输入，各端按相同帧序推进",16,MUTED))
    else:
        parts += [rule(790,278,850,366,ORANGE,2,marker="orangeArrow"),rule(850,366,940,454,TEAL,2,marker="tealArrow"),
                  box(816,340,180,52,"权威状态","#F4E6D9",ORANGE,17),rule(1000,366,1040,278,TEAL,2,marker="tealArrow"),
                  rule(1000,366,1080,454,TEAL,2,marker="tealArrow"),t(650,518,"服务端周期性下发状态并校正偏差",16,MUTED)]
    return "".join(parts)


def diagram_network():
    return "".join([t(650,205,"数据包从编码到抵达",21,INK,650),rule(650,222,1125,222),
        box(656,302,134,82,"客户端",PALE,SOFT,18,"编码"),box(847,302,134,82,"网络",MINT,TEAL,18,"传输"),
        box(1038,302,106,82,"服务端",PALE,SOFT,17,"解析"),rule(790,324,838,324,TEAL,2,marker="tealArrow"),
        rule(981,324,1029,324,TEAL,2,marker="tealArrow"),rule(1038,366,790,366,ORANGE,2,marker="orangeArrow"),
        t(656,432,"序列化",15,MUTED),t(847,432,"延迟 · 丢包 · 重传",15,MUTED),t(1038,432,"校验",15,MUTED),
        t(650,518,"协议决定数据如何可靠地抵达对端",17,MUTED)])


def diagram_huffman():
    return "".join([t(650,205,"按频率构建前缀树",21,INK,650),rule(650,222,1125,222),
        rule(890,305,790,365,SOFT,2),rule(890,305,990,365,SOFT,2),rule(790,405,740,458,SOFT,2),rule(790,405,840,458,SOFT,2),
        node(890,278,"10",MINT,TEAL,26),node(790,386,"4",PALE,SOFT,23),node(990,386,"6","#F4E6D9",ORANGE,23),
        box(700,458,78,46,"a · 2",PALE,SOFT,15),box(802,458,78,46,"b · 2",PALE,SOFT,15),
        t(650,538,"反复合并最低频节点，形成前缀编码",16,MUTED)])


def diagram_ai(kind):
    if kind == "ai-agent":
        return "".join([
            box(650, 307, 110, 76, "目标", PALE, SOFT, 18, "任务 · 上下文"),
            box(810, 254, 128, 76, "规划器", MINT, TEAL, 18, "拆解 · 选择"),
            box(1000, 307, 120, 76, "工具", PALE, SOFT, 18, "搜索 · 执行"),
            box(810, 420, 128, 76, "观察", "#F4E6D9", ORANGE, 18, "结果 · 记忆"),
            rule(760, 330, 802, 294, TEAL, 2, marker="tealArrow"),
            rule(938, 294, 992, 330, TEAL, 2, marker="tealArrow"),
            rule(1060, 383, 938, 454, ORANGE, 2, marker="orangeArrow"),
            rule(810, 458, 710, 458, TEAL, 2),
            rule(710, 458, 710, 383, TEAL, 2, marker="tealArrow"),
            t(650, 535, "根据工具反馈更新状态，直到目标完成", 16, MUTED),
        ])
    if kind == "covers":
        return "".join([t(650,205,"文章到封面的生成链路",21,INK,650),rule(650,222,1125,222),
            box(646,300,118,82,"文章",PALE,SOFT,18,"标题 · 分类"),box(803,300,118,82,"主题",MINT,TEAL,18,"识别内容"),
            box(960,300,118,82,"SVG",PALE,SOFT,18,"图文排版"),box(1086,300,74,82,"PNG","#F4E6D9",ORANGE,16),
            rule(764,341,793,341,TEAL,2,marker="tealArrow"),rule(921,341,950,341,TEAL,2,marker="tealArrow"),
            rule(1078,341,1079,341,ORANGE,2,marker="orangeArrow"),t(650,500,"主题图解由标题与分类共同选择",16,MUTED)])
    return "".join([
        box(650, 302, 122, 76, "任务", PALE, SOFT, 18, "目标 · 约束"),
        box(824, 286, 152, 104, "代码代理", MINT, TEAL, 18, "读取 · 编辑"),
        box(1028, 302, 118, 76, "代码库", PALE, SOFT, 18, "变更 · 测试"),
        box(824, 431, 152, 76, "人工复核", "#F4E6D9", ORANGE, 18, "决策 · 发布"),
        rule(772, 340, 815, 340, TEAL, 2, marker="tealArrow"),
        rule(976, 340, 1020, 340, TEAL, 2, marker="tealArrow"),
        rule(1087, 378, 1087, 469, TEAL, 2),
        rule(1087, 469, 977, 469, TEAL, 2, marker="tealArrow"),
        rule(824, 469, 713, 469, ORANGE, 2),
        rule(713, 469, 713, 378, ORANGE, 2, marker="orangeArrow"),
        t(650, 535, "Agent 执行变更，人负责审查与最终发布", 16, MUTED),
    ])

def diagram_learning(reflection=False):
    heading = "经验如何变成能力" if reflection else "学习闭环"
    accent = ORANGE if reflection else TEAL
    accent_fill = "#F4E6D9" if reflection else MINT
    points = ((665, 280), (970, 280), (970, 414), (665, 414))
    labels = (("观察", "收集问题"), ("理解", "建立模型"), ("练习", "动手验证"), ("复盘", "调整认识"))
    parts = [t(650, 205, heading, 21, INK, 650), rule(650, 222, 1125, 222)]
    for (x, y), (title, note), index in zip(points, labels, range(4)):
        fill, stroke = (accent_fill, accent) if index == 3 else (MINT, TEAL) if index == 2 else (PALE, SOFT)
        parts.append(box(x, y, 132, 62, title, fill, stroke, 18, note))
    parts.extend([
        rule(805, 311, 955, 311, TEAL, 2, marker="tealArrow"),
        rule(1036, 348, 1036, 405, TEAL, 2, marker="tealArrow"),
        rule(955, 445, 805, 445, accent, 2, marker="orangeArrow" if reflection else "tealArrow"),
        rule(731, 405, 731, 348, accent, 2, marker="orangeArrow" if reflection else "tealArrow"),
        t(650, 535, "通过反复实践，把知识变成稳定能力", 16, MUTED),
    ])
    return "".join(parts)


def diagram_pipeline():
    return "".join([
        t(650, 205, "顶点变换 · 光栅化 · 片元着色", 21, INK, 650),
        rule(650, 222, 1125, 222),
        box(650, 286, 112, 82, "Vertex", PALE, SOFT, 17, "MVP 变换"),
        box(792, 286, 118, 82, "Rasterize", MINT, TEAL, 16, "图元 · 插值"),
        box(940, 286, 112, 82, "Fragment", "#F4E6D9", ORANGE, 16, "光照 · 采样"),
        box(1078, 286, 74, 82, "Frame", PALE, TEAL, 15, "Z / Blend"),
        rule(762, 327, 784, 327, TEAL, 2, marker="tealArrow"),
        rule(910, 327, 932, 327, ORANGE, 2, marker="orangeArrow"),
        rule(1052, 327, 1070, 327, TEAL, 2, marker="tealArrow"),
        box(650, 412, 210, 52, "Uniform / CBuffer", PALE, SOFT, 14, mono=True),
        box(892, 412, 260, 52, "Texture2D + BRDF Lighting", MINT, TEAL, 14, mono=True),
        rule(755, 412, 706, 368, SOFT, 1.5, "4 4"),
        rule(1022, 412, 996, 368, TEAL, 1.5, "4 4"),
        t(650, 522, "可编程着色器与固定管线阶段协同生成最终画面", 16, MUTED),
    ])


def select_variant(top, sub, title):
    if sub == "图形学" or "渲染管线" in title or "Shader" in title:
        return "pipeline"
    if top == "AI探索":
        if "封面" in title: return "covers"
        return "ai-agent" if sub == "AI Agent" else "ai-coding"
    if top == "项目实战": return "huffman" if "哈夫曼" in title else "architecture"
    if top == "随笔杂谈": return "reflection-notes" if ("最近" in title or "所思所想" in title) else "learning"
    if sub == "算法": return "graph" if ("图" in title or "搜索" in title) else "sorting"
    if sub == "数据结构": return "hash" if "哈希" in title else "huffman"
    if sub == "计算机基础": return "process"
    if sub == "网络":
        if "帧同步" in title: return "frame-sync"
        if "状态同步" in title: return "state-sync"
        return "network"
    if sub == "C++":
        for terms,kind in [("内存","memory"),("虚函数","dispatch"),("值语义","move"),("移动","move"),("STL","vector"),("容器","vector"),("类型转换","language"),("整体框架","architecture"),("关键字","language")]:
            if terms in title: return kind
        return "language"
    if sub == "C#":
        if ".NET" in title or "平台" in title: return "language"
        if "迭代器" in title: return "iterator"
        if "反射" in title or "委托" in title: return "reflection"
        return "parameters"
    if sub == "Unity":
        if "动画" in title: return "animation"
        if "物理" in title: return "physics"
        if "协程" in title or "多线程" in title: return "async"
        if "热更新" in title: return "assets"
        if "资源" in title or "内存" in title: return "assets"
        if "DrawCall" in title or "合批" in title or "UI" in title or "UGUI" in title: return "render"
        if "GC" in title: return "gc"
        return "lifecycle"
    return "architecture"


def diagram_for(kind):
    if kind=="sorting": return diagram_sorting()
    if kind=="graph": return diagram_graph()
    if kind=="hash": return diagram_hash()
    if kind=="memory": return diagram_memory()
    if kind=="dispatch": return diagram_dispatch()
    if kind=="move": return diagram_move()
    if kind=="vector": return diagram_vector()
    if kind in ("language","architecture","process"): return diagram_layers(kind, "")
    if kind=="iterator": return diagram_iterator()
    if kind=="reflection": return diagram_reflection()
    if kind=="parameters": return diagram_parameters()
    if kind=="animation": return diagram_animation()
    if kind=="lifecycle": return diagram_lifecycle()
    if kind=="physics": return diagram_physics()
    if kind=="async": return diagram_async()
    if kind=="assets": return diagram_assets()
    if kind=="gc": return diagram_render("gc")
    if kind=="render": return diagram_render("render")
    if kind in ("frame-sync","state-sync"): return diagram_sync(kind)
    if kind=="network": return diagram_network()
    if kind=="huffman": return diagram_huffman()
    if kind in ("ai-coding", "ai-agent", "covers"): return diagram_ai(kind)
    if kind == "pipeline": return diagram_pipeline()
    if kind in ("learning","reflection-notes"): return diagram_learning(kind=="reflection-notes")
    return diagram_layers("architecture", "")


def diagram_heading(kind):
    names={"sorting":"选择排序 · 第一轮","graph":"图搜索 · 扩展边界","hash":"哈希索引 · 冲突处理",
        "memory":"地址与对象的关系","dispatch":"一次虚函数调用","move":"资源所有权交接","vector":"vector · 连续存储",
        "language":"语言与运行环境","architecture":"模块职责与依赖","process":"进程隔离与线程执行",
        "iterator":"迭代器推进游标","reflection":"运行时读取类型信息","parameters":"参数传递与别名","animation":"动画属性随时间变化",
        "lifecycle":"MonoBehaviour 生命周期","physics":"物体运动与碰撞","async":"协程与线程调度",
        "assets":"资源加载与释放","gc":"GC · 可达对象","render":"界面到渲染批次","frame-sync":"帧同步",
        "state-sync":"状态同步","network":"数据包从编码到抵达","huffman":"按频率构建前缀树",
        "ai-coding":"人机协作 · 工程回路","ai-agent":"Agent · 规划与工具调用",
        "covers":"文章到封面的生成链路","pipeline":"顶点变换 · 光栅化 · 片元着色",
        "learning":"学习闭环","reflection-notes":"经验与思考"}
    return names[kind]


def wrap_title(title, max_units=10.5):
    lines=[]; current=""; units=0.0
    for char in title:
        size=0.56 if ord(char)<128 else 1.0
        if char==" " and not current: continue
        if current and units+size>max_units:
            lines.append(current.rstrip());current="";units=0.0
            if char==" ": continue
        current+=char;units+=size
    if current: lines.append(current.rstrip())
    if len(lines)>1:
        last_units=sum(0.56 if ord(char)<128 else 1.0 for char in lines[-1])
        if last_units<3.0:
            combined=lines[-2]+lines[-1]
            split=len(combined)//2
            lines[-2:]=[combined[:split],combined[split:]]
    return lines or [title]


def make_svg(title, top, sub):
    kind=select_variant(top,sub,title); clean=re.sub(r"^【.+?】", "", title).strip()
    title_lines=wrap_title(clean); font_size=51 if max(map(len,title_lines))<10 else 44
    line_height=68; start_y=314-(len(title_lines)-1)*line_height/2
    title_svg="".join(t(78,start_y+i*line_height,value,font_size,INK,700) for i,value in enumerate(title_lines))
    label=top if top==sub else f"{top} / {sub}" if top else "技术笔记"
    caption=CAPTIONS[kind]
    diagram_svg=diagram_for(kind)
    # Each topic diagram supplies an internal label; the shared layout owns that label now.
    diagram_svg=re.sub(r'<text x="650" y="205"[^>]*>.*?</text>', "", diagram_svg, count=1)
    diagram_svg=re.sub(r'<path d="M650 222L1125 222"[^>]*/>', "", diagram_svg, count=1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="coverTitle coverDesc">
<title id="coverTitle">{esc(clean)}</title><desc id="coverDesc">{esc(label)}：{esc(caption)}</desc><defs>{defs()}</defs>
<rect width="1200" height="630" fill="{BG}"/><rect width="1200" height="630" fill="url(#grid)"/>
<path d="M585 72V558" stroke="{GRID}" stroke-width="1.5"/>
{t(78,98,label,20,MUTED,600)}<path d="M80 122H132" stroke="{TEAL}" stroke-width="5"/>
{title_svg}{t(80,492,caption,17,MUTED)}{t(650,142,diagram_heading(kind),21,INK,650)}
{rule(650,162,1125,162,GRID,1.5)}{diagram_svg}</svg>'''



def make_thumbnail(title, top, sub):
    kind = select_variant(top, sub, title)
    diagram_svg = diagram_for(kind)
    diagram_svg = re.sub(r'<text x="650" y="205"[^>]*>.*?</text>', "", diagram_svg, count=1)
    diagram_svg = re.sub(r'<path d="M650 222L1125 222"[^>]*/>', "", diagram_svg, count=1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="360" viewBox="610 230 600 360" role="img" aria-labelledby="thumbnailTitle">
<title id="thumbnailTitle">{esc(diagram_heading(kind))}</title><defs>{defs()}</defs>
<rect x="610" y="230" width="600" height="360" fill="{BG}"/>{diagram_svg}</svg>'''


def get_meta(path):
    with open(path, encoding="utf-8", newline="") as post_file:
        source = post_file.read()
    parts=source.split("---")
    if len(parts)<3: raise ValueError(f"invalid front-matter: {path}")
    fm=parts[1]; match=re.search(r"^title:\s*(.+)$",fm,re.M)
    if not match: raise ValueError(f"missing title: {path}")
    title=match.group(1).strip().strip("'\"")
    end=fm.find("tags:") if "tags:" in fm else len(fm)
    block=fm[fm.find("categories:"):end]
    cats=re.findall(r"^\s+-\s*(.+)$",block,re.M)
    cover_match=re.search(r"^cover:\s*(.*)$",fm,re.M)
    return source,title,cats[0].strip() if cats else "",cats[-1].strip() if cats else "",cover_match.group(1).strip() if cover_match else ""


def slugify(title):
    return re.sub(r"[^\w一-鿿]+","-",title).strip("-")


def write_cover(path,source,title,top,sub):
    slug=slugify(title)
    with open(os.path.join(GEN,slug+".svg"),"w",encoding="utf-8",newline="\n") as f: f.write(make_svg(title,top,sub))
    with open(os.path.join(GEN,slug+"-thumb.svg"),"w",encoding="utf-8",newline="\n") as f: f.write(make_thumbnail(title,top,sub))
    cover_line=f"cover: {PREFIX}{slug}.png"
    if re.search(r"^cover:.*$",source,re.M): source=re.sub(r"^cover:[^\r\n]*",cover_line,source,count=1,flags=re.M)
    else: source=re.sub(r"^(date:.*)$",cover_line+r"\n\1",source,count=1,flags=re.M)
    with open(path,"w",encoding="utf-8",newline="") as f: f.write(source)


def main():
    os.makedirs(GEN,exist_ok=True); args=sys.argv[1:]
    keywords=[arg for arg in args if not arg.startswith("--")]; force="--all" in args; count=0; manual=0
    for path in glob.glob(os.path.join(POSTS,"*.md")):
        source,title,top,sub,cover=get_meta(path)
        if keywords and not any(word in title for word in keywords): continue
        if cover and not cover.startswith(PREFIX): manual+=1;continue
        if cover and not force: continue
        write_cover(path,source,title,top,sub);print(f"[{top}/{sub}] {title}");count+=1
    print(f"generated {count}, kept manual covers {manual}")

if __name__=="__main__": main()
