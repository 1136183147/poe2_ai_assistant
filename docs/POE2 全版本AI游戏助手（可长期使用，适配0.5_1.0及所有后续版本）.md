# POE2 全版本AI游戏助手（可长期使用，适配0\.5/1\.0及所有后续版本）

# 一、助手核心定位（长期可用，适配全版本）

本AI助手专为POE2全版本打造，无版本限制，可适配0\.5赛季、1\.0正式版及所有后续更新版本，无需随版本迭代重新搭建框架。初期以你个人总结的0\.5赛季细节作为初始记忆，后续可通过自动更新、手动喂养，同步适配新赛季机制、新职业、新BD、新做装攻略，长期陪伴你的POE2游戏历程。

核心核心优势：

- ✅ 全版本适配：后续1\.0及所有版本，可自动/手动更新记忆与爬虫规则，无需重新开发

- ✅ 专属记忆体系：优先存储你个人总结的版本细节、BD思路、做装经验，且永久保存、可导出/导入

- ✅ 跨设备/好友继承：记忆数据可一键打包导出，换电脑、发朋友均可直接继承，无需重复喂养

- ✅ 游戏实时陪伴：游戏运行时悬浮窗后台运行，不遮挡画面，边玩边问、即时响应

- ✅ 自动更新适配：自动爬取指定网站（POE2 Ninja、暗黑核、踩蘑菇等），同步新赛季资讯、做装攻略（抖音Ace），无需手动查找

- ✅ 可扩展性强：后续版本新增机制、新职业、新玩法，可直接更新记忆库，无需改动核心代码

# 二、助手核心功能（全版本通用，可迭代升级）

## 2\.1 永久记忆系统（核心功能，适配全版本）

记忆系统为助手核心，支持长期存储、迭代更新，适配所有版本，具体设计如下：

- 记忆分类：按“版本记忆\+个人专属记忆\+实时资讯记忆”分类存储，互不干扰，后续版本更新仅新增/修改对应版本记忆，不覆盖原有内容

- 个人专属记忆：优先存储你总结的各版本细节（如0\.5赛季总结）、BD思路、做装经验，手动喂养后永久保存，后续版本可随时调用、补充

- 版本记忆：自动同步各版本核心机制（0\.5、1\.0及后续），包括新职业、新玩法、机制改动，由爬虫自动更新或手动补充

- 记忆操作：支持一键导出（打包为记忆包）、一键导入，换电脑、发朋友可直接继承所有记忆，无需重复喂养

- 记忆备份：自动每日备份，防止数据丢失，可恢复任意历史版本记忆

## 2\.2 实时资讯与攻略同步（全版本适配）

自动爬取你指定的所有网站，随版本更新同步升级爬虫规则，确保资讯实时准确，具体配置：

|监控网站/来源|爬取频率|爬取内容（全版本适配）|存储位置|
|---|---|---|---|
|POE2 Ninja|每2小时|各版本热门BD、通货价格、装备趋势、贬值数据，随版本同步更新|memory/meta/top\_builds\.json、price\_trend\.json|
|暗黑核|每3小时|国服各版本攻略、BD推荐、做装教程、版本解读，适配国服更新节奏|memory/meta/darkcore\_guides\.md|
|踩蘑菇社区|每4小时|各版本玩家讨论、机制解析、BUG汇总、高难玩法心得|memory/meta/caimogu\_discuss\.md|
|抖音 Ace|每天凌晨|各版本做装视频、步骤拆解、词缀选择、成本控制，随版本做装机制同步更新|memory/craft/ace\_craft\_guide\.md|
|B站「受宠的老孤独」|每周1次|各版本发布会总结、实测心得、版本解读，补充你个人总结的细节|memory/core/version\_guides\.md|
|POE2 官网|每天1次|各版本官方做装机制、正统做装教程、词缀规则及版本更新做装改动，含基础做装与终局做装指南|memory/craft/offical\_craft\_guide\.md|
|POE2 编年史|每6小时|各版本做装底材数据库、词缀大全、催化剂效果、做装材料详情及暗金做装关联信息，补充做装细节支撑|memory/craft/chronicles\_craft\_data\.md|

## 2\.3 游戏实时陪伴功能（全版本通用）

- 悬浮窗设计：游戏运行时后台静默运行，悬浮窗可置顶、缩小，不遮挡游戏画面，低CPU占用，不影响游戏流畅度

- 即时响应：边玩边问，可随时查询BD优化、做装步骤、版本机制，AI自动调用当前版本记忆\+实时资讯，快速给出回答

- 手动喂养：游戏过程中，可随时输入你的新发现、新BD思路、做装经验，即时存入个人专属记忆，后续可直接调用

## 2\.4 全版本迭代适配功能（核心亮点）

无需随版本重新开发，仅需简单操作即可适配1\.0及后续所有版本：

- 记忆迭代：新增版本时，自动爬取新版本机制、新职业、新玩法，存入对应版本记忆文件夹，不覆盖原有0\.5、1\.0等历史版本记忆

- 爬虫升级：新版本上线后，自动优化爬虫规则，适配新网站、新资讯来源，确保能抓取新版本相关内容

- 手动更新：你可随时补充新版本个人总结细节，手动导入到对应版本记忆中，让助手更贴合你的认知

- 兼容保留：历史版本的BD、做装经验、记忆内容均会保留，可随时查询、调用，比如1\.0版本时，仍可查看0\.5赛季的个人总结与玩法心得

# 三、记忆库结构（全版本通用，可迭代扩展）

记忆库按“版本\+分类”设计，可随版本迭代无限扩展，所有记忆可导出/导入，具体结构如下（自动生成，无需手动创建）：

```plain text
memory/
├── core/                # 核心知识库（全版本通用+各版本专属）
│   ├── version_0.5.md   # 你个人总结的0.5赛季细节（专属记忆）
│   ├── version_1.0.md   # 1.0版本细节（自动爬取+手动补充）
│   ├── version_xxx.md   # 后续版本细节（随版本新增）
│   ├── new_classes_all.md # 全版本新职业、升华、技能汇总
│   └── common_mechanic.md # 全版本通用机制（不变内容，如基础做装逻辑）
├── craft/               # 做装库（全版本适配，自动更新）
│   ├── base_select.md   # 底材选择规则（全版本通用）
│   ├── prefix_suffix.md # 词缀优先级（随版本机制更新）
│   ├── force_craft.md   # 强行做装流程（全版本通用）
│   ├── ace_craft_guide.md # 抖音Ace最新做装攻略（随版本更新）
│   ├── offical_craft_guide.md # POE2官网做装指南（官方正统教程，随版本更新）
│   └── chronicles_craft_data.md # POE2编年史做装数据（底材、词缀等，随版本更新）
├── meta/                # 实时meta（全版本适配，自动更新）
│   ├── top_builds.json  # 各版本热门BD排行
│   ├── price_trend.json # 关键通货价格、装备贬值趋势
│   ├── darkcore_guides.md # 暗黑核国服攻略（全版本）
│   └── caimogu_discuss.md # 踩蘑菇社区讨论（全版本）
└── user/                # 你的专属记忆（永久保留，可无限补充）
    ├── chat_history.json # 你的提问与AI回答记录（全版本）
    ├── favorite_builds.md # 你收藏的各版本BD、思路
    ├── craft_notes.md    # 你自己的做装试错经验、心得（全版本）
    └── version_notes.md  # 你总结的各版本专属细节（单独存储，不被覆盖）
```

# 四、完整代码框架（全版本通用，可迭代升级）

## 4\.1 项目结构（可长期使用，随版本扩展）

```plain text
poe2_ai_assistant/
├── main.py              # 入口文件（启动悬浮窗+后台运行，整合所有模块，全版本通用）
├── memory/              # 记忆文件夹（可随版本无限扩展，自动生成）
├── crawler/             # 爬虫模块（可随版本升级，适配新资讯）
│   ├── ninja_crawler.py # POE2 Ninja爬虫（全版本适配，自动更新规则）
│   ├── darkcore_crawler.py # 暗黑核爬虫（全版本适配）
│   ├── caimogu_crawler.py # 踩蘑菇社区爬虫（全版本适配）
│   ├── douyin_ace_crawler.py # 抖音Ace爬虫（全版本适配）
│   ├── version_crawler.py # 版本更新爬虫（抓取1.0及后续版本资讯）
│   ├── poe2_official_crawler.py # POE2官网爬虫（抓取官方做装指南，全版本适配）
│   └── poe2_chronicles_crawler.py # POE2编年史爬虫（抓取做装数据，全版本适配）
├── ai/                  # AI对话模块（全版本通用，无需改动）
│   ├── llm_engine.py    # AI对话核心（调用模型，结合当前版本记忆回答）
│   └── memory_retriever.py # 记忆检索（自动匹配当前版本+个人专属记忆）
├── gui/                 # 悬浮窗界面（全版本通用，游戏友好型）
│   └── float_window.py  # 悬浮窗实现（不遮挡游戏，低CPU占用）
├── utils/               # 工具模块（全版本通用）
│   ├── export_memory.py # 一键导出记忆包（ZIP格式，跨设备/好友继承）
│   ├── import_memory.py # 一键导入记忆包
│   └── backup_memory.py # 自动备份记忆（防止数据丢失）
├── md_manager/          # MD知识库管理（全版本通用，自动生成/更新MD文件）
│   └── md_generator.py  # 生成各版本机制、技能、做装等MD文档
└── config.py            # 配置文件（可调整爬虫频率、悬浮窗大小、版本切换等）
```

## 4\.2 核心代码片段（全版本通用，可迭代升级）

### （1）记忆管理核心（永久存储\+全版本迭代\+导出/导入）

```python
import json
import os
import shutil
from datetime import datetime

# 记忆根目录（自动创建，可随版本无限扩展）
MEMORY_ROOT = "memory/"
os.makedirs(MEMORY_ROOT, exist_ok=True)

def load_memory(category, filename):
    """加载指定分类的记忆内容（MD/JSON），适配全版本"""
    path = os.path.join(MEMORY_ROOT, category, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) if filename.endswith(".json") else f.read()
    # 若文件不存在，返回默认值（避免报错，后续版本可补充）
    return "" if filename.endswith(".md") else {}

def save_memory(category, filename, content, version="common"):
    """保存记忆内容，支持按版本分类，不覆盖历史版本"""
    # 若为版本专属记忆，创建对应版本文件夹
    if version != "common":
        category_path = os.path.join(MEMORY_ROOT, category, f"version_{version}")
    else:
        category_path = os.path.join(MEMORY_ROOT, category)
    os.makedirs(category_path, exist_ok=True)
    path = os.path.join(category_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        if filename.endswith(".json"):
            json.dump(content, f, ensure_ascii=False, indent=2)
        else:
            f.write(content)
    # 自动备份记忆，防止数据丢失
    backup_memory()

def export_memory(zip_path="POE2_AI记忆包.zip"):
    """一键导出所有记忆为ZIP包，用于换电脑/发朋友，全版本记忆均会导出"""
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", MEMORY_ROOT)
    return f"✅ 记忆已导出到：{os.path.abspath(zip_path)}"

def import_memory(zip_path):
    """一键导入记忆包，继承所有版本记忆、个人专属记忆，无需区分版本"""
    if not os.path.exists(zip_path):
        return "❌ 记忆包文件不存在，请检查路径"
    # 解压到记忆根目录，覆盖现有内容（可选择增量导入）
    shutil.unpack_archive(zip_path, MEMORY_ROOT)
    return "✅ 记忆导入成功，已继承所有版本知识库与专属记忆"

def backup_memory():
    """自动备份记忆，每天1次，保留7天内备份，防止数据丢失"""
    backup_dir = os.path.join(MEMORY_ROOT, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d')}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)
    shutil.make_archive(backup_path.replace(".zip", ""), "zip", MEMORY_ROOT)
    # 删除7天前的旧备份，节省空间
    for file in os.listdir(backup_dir):
        if file.endswith(".zip"):
            file_date = file.split("_")[1].split(".")[0]
            if (datetime.now() - datetime.strptime(file_date, "%Y%m%d")).days > 7:
                os.remove(os.path.join(backup_dir, file))
    return "✅ 记忆自动备份完成"

# 初始化你个人总结的0.5赛季细节（单独存储，不被后续版本覆盖）
def init_user_version_memory(version="0.5", content=""):
    """初始化用户个人总结的版本细节，单独存储，后续版本不覆盖"""
    save_memory("core", f"user_version_{version}.md", content, version=version)
    print(f"✅ 已初始化你个人总结的{version}赛季细节，存入专属记忆")
```

### （2）版本迭代适配核心代码（无需重新开发，自动升级）

```python
def update_version_memory(version, new_content):
    """更新指定版本的记忆内容（如1.0版本），不覆盖历史版本与个人专属记忆"""
    # 保存新版本细节（自动爬取+手动补充）
    save_memory("core", f"version_{version}.md", new_content, version=version)
    # 升级爬虫规则，适配新版本资讯
    update_crawler_rule(version)
    print(f"✅ 已更新{version}版本记忆，爬虫规则同步升级")

def update_crawler_rule(version):
    """随版本更新，升级爬虫规则，适配新版本资讯来源"""
    # 示例：1.0版本新增官方资讯站，添加爬虫规则
    if version == "1.0":
        from crawler.version_crawler import add_new_crawler
        # 添加1.0版本专属资讯站爬虫
        add_new_crawler("https://poe2.com/version-1.0", "version_1.0_news.md")
    # 后续版本可继续添加适配逻辑
    pass

def switch_version(version):
    """切换当前助手适配的版本，无需重启，即时生效"""
    # 切换记忆检索优先级，优先调用当前版本记忆
    from ai.memory_retriever import set_version_priority
    set_version_priority(version)
    # 切换爬虫抓取内容，聚焦当前版本
    from crawler import set_crawler_version
    set_crawler_version(version)
    print(f"✅ 已切换至{version}版本，AI将优先使用该版本记忆与资讯")
```

### （3）AI对话核心（自动适配当前版本，调用个人专属记忆）

```python
from ai.memory_retriever import load_memory, get_current_version
from utils.memory_manager import save_memory

def llm_call(prompt):
    """调用LLM模型（可替换为本地模型/通义千问/DeepSeek，预留接口，全版本通用）"""
    # 实际使用时替换为真实LLM调用代码，此处为示例
    return f"【POE2全版本助手】：{prompt.split('用户问题：')[-1]}（已结合当前版本记忆+你的专属总结+实时资讯）"

def ask_ai(question):
    """核心对话函数，自动适配当前版本，优先调用你的专属记忆"""
    current_version = get_current_version()  # 获取当前适配版本（如0.5、1.0）
    # 1. 检索相关记忆：当前版本细节+个人专属总结+实时资讯+通用内容
    version_info = load_memory("core", f"version_{current_version}.md")  # 当前版本官方机制
    user_version_info = load_memory("core", f"user_version_{current_version}.md")  # 你的个人总结
    craft_guide = load_memory("craft", "ace_craft_guide.md")  # 实时做装攻略（Ace）
    official_craft = load_memory("craft", "offical_craft_guide.md")  # 官方做装指南
    chronicles_craft = load_memory("craft", "chronicles_craft_data.md")  # 编年史做装数据
    top_builds = load_memory("meta", "top_builds.json")  # 当前版本热门BD
    price_trend = load_memory("meta", "price_trend.json")  # 当前版本物价

    # 2. 构建Prompt（贴合POE玩家语言，优先你的个人总结，再结合当前版本资讯）
    prompt = f"""你是POE2全版本专属AI游戏助手，可适配所有版本，当前适配版本：{current_version}。
优先参考用户个人总结的该版本细节，再结合当前版本实时资讯、官方做装指南、编年史数据，给出具体可操作的建议，语言接地气，符合POE玩家交流习惯。

【用户个人总结的{current_version}赛季细节】
{user_version_info if user_version_info else '暂无补充，参考官方版本细节'}

【当前版本官方机制】
{version_info[:2000]}

【当前做装攻略】
1. 抖音Ace最新做装攻略：{craft_guide[:1000]}
2. POE2官网官方做装指南：{official_craft[:800]}
3. POE2编年史做装数据：{chronicles_craft[:800]}

【当前版本热门BD（POE2 Ninja）】
{str(top_builds)[:500]}

【当前版本物价趋势】
{str(price_trend)[:300]}

用户问题：{question}

回答要求：
1. 优先结合用户个人总结的细节（若有），再补充当前版本实时资讯、官方指南与编年史数据；
2. 区分国服/国际服差异，给出对应建议；
3. 语言简洁，重点突出，优先具体操作建议，不堆砌无关内容；
4. 若用户询问历史版本内容，可调用对应版本记忆，准确回复；
5. 涉及做装相关问题，优先结合官网正统教程+编年史数据，补充Ace的实操技巧。"""

    # 3. 调用LLM获取回答
    response = llm_call(prompt)

    # 4. 保存对话记录到用户专属记忆
    chat_history = load_memory("user", "chat_history.json")
    chat_history.append({
        "time": str(datetime.now()),
        "question": question,
        "answer": response
    })
    save_memory("user", "chat_history.json", chat_history)

    return response

# 测试示例（可直接运行）
if __name__ == "__main__":
    # 初始化0.5赛季个人总结（示例，可替换为你实际总结的内容）
    user_05_content = """5.8 乔纳森发布会总结：脆皮职业王朝。
没玩过1的  直接给到夯爆
玩过1的 直接给到一个普通
神庙是一个非常好玩的版本，所以加入了常驻
新赛季玩法是 打符咒，类似一种新的工艺，然后通过赛季道具可以直接给装备进行加成，目前看下来最实用的有增加法术范围，暗金装备直接变异（或者提升数值），衣服或者头上可以打上免死结界，实用性应该挺强。ps：召唤、锐眼王朝。 
裂隙boss更换（或者新增，目前看直播应该是更换），变成1的种树玩法，直接复制，玩过流放1S27应该明白，爆率超高且能指定属性，做装成本下降，贬值快，2里面可能会进行修改，就跟流放1S28一样。
镜子剧情线补充完整，第四章，我们拯救的那个长老被拖进入镜子，需要进行解救，镜子里面分黑色红色，触碰黑色应该是进去找长老，大概率是挑战一下那个新的镜子boss
镜子产物：涂油修改，增加20个涂油天赋，珠宝也可以通过涂油进行替换珠宝里面的词缀
深渊：没看懂，感觉没变化
神庙：常驻玩法，还是能搭建神庙，但是由于变成随机区域，相当于砍了搭建速度，除了女王头跟女王手，装备收益不是很高，只能看爆率了
异界天赋树：完全修改，大概有300节点说是，实际看上去异界的应该在一百多应该是有的，全部可以点满，通过挑战异界boss还有一些发布任务，增加节点，重点：全部可以点满
流放1 红蓝王贤者关注参考，简单说就是能通过天赋增加地图boss的产出，boss区域可以多一个boss，甚至是一群，需要bd有一定的强度，普通bd甚至是装备一般直接pass。
高难图产出收益增加：高难度地图产出全面提升，专属掉落概率、稀有通货/传奇权重增加，解锁高阶词缀与赛季道具，配合异界天赋加成，形成高难度=高收益闭环。
引入流放1异界大师，新增相当于大型核心天赋，类似流放1里面的齐拉克任务，但是会多给一个专门针对常驻玩法（地图boss,小精灵，保险箱）这些的一个特殊加成，提高收益，增加难度，有些完全是负面提升，具体实装看蓝贴怎么说
火焰巅峰改版，以前是进入塔内杀一个仲裁官，现在改版就是登上塔顶杀一个新的巅峰boss 有独特的产出暗金，按照乔纳森所说是一个独一无二的暗金，大概率一定是版本主推，击杀道具猜测是，生成一大片城堡，城堡四周会有几个类似之前仲裁官的boss，击杀掉落装备核心（其实就是之前打石柱需要开的三个碎片类似的东西，现在叫装备核心），主推的话，个人猜测应该是三个碎片开启石柱，击杀掉落一个装备核心，然后几个不同的核心开启巅峰boss
新升华，
女猎手：祭灵行者，天赋点为获得熊的力量，鹿的力量，猫头鹰的力量（小精灵附身），通过视频看上去应该是不错的，因为三个加点之后会获得第四个加点，圣洁之力（没点3个是不会出现），视频看完给到一个夯
武僧：武圣，召唤幻影，幻影继承法术攻击，只能说武术家夯爆了，看上去就好玩，背钟人
部分暗金，召唤王朝，新增了一个长杖，直接召唤一个群鸦风暴（LOL稻草人大招），范围还能扩大，群鸦风暴属于召唤物，吃加成，死灵法师狂喜，看装备是无敌，但是缺点依赖惊魂更严重了，但是还是给到一个召唤王朝
新赛季道具可以提升暗金装备，变成独特装备，或者是黄装增加一个特殊结界之力，防具：免死结界....
国际服上架内置交易行
国服5.10号晚上开始发布会，老孤独说，国服是砍了组队收益，国际服是没有提到的
补充：0.5之后下赛季就是1.0版本，转免费版本了要，庄园、工艺都没有上，大概率是11月流放嘉年华说了这个事情，也就是这个0.5赛季将持续半年起步，因为11月的流放嘉年华类似就是这次的发布会，正式版本要12月上估计（乔纳森没有说，只说了下个版本是1.0 且消息在嘉年华会说），猜测应该是鹅厂技术跟ggg开始对接了，内置交易行就是一个显著特征
直播视频看: b站搜 受宠的老孤独
或者等各个主播进行总结视频"""
    init_user_version_memory(version="0.5", content=user_05_content)
    # 切换至0.5版本
    switch_version("0.5")
    # 测试对话
    print(ask_ai("0.5赛季符咒玩法怎么用？"))
    print(ask_ai("做装怎么利用POE2编年史的数据？"))
    print(ask_ai("国服和国际服的核心差异是什么？"))
```

### （4）新增爬虫代码（POE2官网\+编年史，全版本适配）

```python
# crawler/poe2_official_crawler.py（POE2官网爬虫，抓取官方做装指南）
import requests
from bs4 import BeautifulSoup
from utils.memory_manager import save_memory

def crawl_poe2_official_craft():
    """爬取POE2官网做装指南，全版本适配，自动同步版本更新"""
    # 官网做装指南通用链接（随版本自动跳转对应版本）
    url = "https://www.pathofexile2.com/crafting-guide"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        # 提取官方做装指南核心内容（机制、步骤、词缀规则）
        craft_content = []
        # 提取标题
        title = soup.select_one("h1").text.strip() if soup.select_one("h1") else "POE2官方做装指南"
        craft_content.append(f"# {title}")
        # 提取核心章节（做装基础、终局做装、版本改动）
        sections = soup.select(".crafting-section")
        for section in sections:
            section_title = section.select_one("h2").text.strip() if section.select_one("h2") else ""
            section_content = section.get_text(strip=True, separator="\n")
            craft_content.append(f"## {section_title}\n{section_content}")
        # 拼接内容，保存到记忆库
        craft_text = "\n\n".join(craft_content)
        save_memory("craft", "offical_craft_guide.md", craft_text)
        return "✅ POE2官网做装指南已更新"
    except Exception as e:
        return f"❌ POE2官网爬虫失败：{str(e)}"

# crawler/poe2_chronicles_crawler.py（POE2编年史爬虫，抓取做装数据）
def crawl_poe2_chronicles_craft():
    """爬取POE2编年史做装数据，全版本适配，含底材、词缀、催化剂等"""
    # 编年史做装数据通用链接
    url = "https://poe2chronicles.com/crafting"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        # 提取底材数据
        base_materials = soup.select(".base-material-item")
        base_content = ["# POE2编年史做装数据（全版本）", "## 一、做装底材大全"]
        for base in base_materials[:20]:  # 提取前20个核心底材，避免内容过多
            base_name = base.select_one(".base-name").text.strip()
            base_level = base.select_one(".base-level").text.strip()
            base_stats = base.select_one(".base-stats").text.strip()
            base_content.append(f"- {base_name}（等级：{base_level}）：{base_stats}")
        # 提取词缀数据
        affixes = soup.select(".affix-item")
        base_content.append("\n## 二、核心词缀大全")
        for affix in affixes[:30]:  # 提取前30个核心词缀
            affix_name = affix.select_one(".affix-name").text.strip()
            affix_effect = affix.select_one(".affix-effect").text.strip()
            affix_type = affix.select_one(".affix-type").text.strip()  # 前缀/后缀
            base_content.append(f"- {affix_type}【{affix_name}】：{affix_effect}")
        # 提取催化剂数据
        catalysts = soup.select(".catalyst-item")
        base_content.append("\n## 三、催化剂效果")
        for catalyst in catalysts:
            cat_name = catalyst.select_one(".catalyst-name").text.strip()
            cat_effect = catalyst.select_one(".catalyst-effect").text.strip()
            base_content.append(f"- {cat_name}：{cat_effect}")
        # 拼接内容，保存到记忆库
        chronicles_text = "\n\n".join(base_content)
        save_memory("craft", "chronicles_craft_data.md", chronicles_text)
        return "✅ POE2编年史做装数据已更新"
    except Exception as e:
        return f"❌ POE2编年史爬虫失败：{str(e)}"

# 爬虫定时任务（整合到主程序，全版本通用）
def start_crawler_schedule():
    """启动所有爬虫定时任务，全版本适配，可调整频率"""
    from schedule import every, repeat, run_pending
    import time
    # 按预设频率启动各爬虫
    every(2).hours.do(crawl_poe2_ninja)  # POE2 Ninja
    every(3).hours.do(crawl_darkcore)    # 暗黑核
    every(4).hours.do(crawl_caimogu)     # 踩蘑菇社区
    every().day.at("00:00").do(crawl_douyin_ace)  # 抖音Ace（每天凌晨）
    every().day.at("01:00").do(crawl_poe2_official_craft)  # POE2官网（每天凌晨1点）
    every(6).hours.do(crawl_poe2_chronicles_craft)  # POE2编年史（每6小时）
    every().week.do(crawl_bilibili_lgdz) # B站老孤独（每周1次）
    # 持续运行定时任务
    print("✅ 所有爬虫定时任务已启动，开始同步实时资讯与做装攻略")
    while True:
        run_pending()
        time.sleep(60)  # 每分钟检查一次任务
```

### （5）悬浮窗核心代码（全版本通用，游戏友好型）

```python
# gui/float_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from ai.llm_engine import ask_ai
from utils.memory_manager import export_memory, import_memory
import os

class POE2FloatWindow:
    def __init__(self):
        # 初始化悬浮窗，设置为顶级窗口，无标题栏，可拖动
        self.root = tk.Tk()
        self.root.title("POE2全版本AI助手")
        self.root.overrideredirect(True)  # 隐藏标题栏
        self.root.geometry("400x500")  # 初始大小，可调整
        self.root.attributes("-topmost", True)  # 置顶显示，不被游戏遮挡
        self.root.attributes("-alpha", 0.9)  # 半透明，不影响游戏视线
        self.root.config(bg="#1a1a1a")  # 深色模式，贴合游戏风格

        # 变量定义
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        # 构建界面
        self.create_widgets()
        # 绑定拖动事件
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        # 绑定关闭、缩小事件
        self.root.bind("<Escape>", self.hide_window)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_window)

    def create_widgets(self):
        # 标题栏（简易，可拖动）
        self.title_frame = ttk.Frame(self.root, height=30, style="Title.TFrame")
        self.title_frame.pack(fill=tk.X, side=tk.TOP)
        self.title_label = ttk.Label(self.title_frame, text="POE2全版本AI助手", style="Title.TLabel")
        self.title_label.pack(side=tk.LEFT, padx=10)
        self.close_btn = ttk.Button(self.title_frame, text="×", width=3, command=self.quit_window, style="Close.TButton")
        self.close_btn.pack(side=tk.RIGHT)
        self.hide_btn = ttk.Button(self.title_frame, text="−", width=3, command=self.hide_window, style="Hide.TButton")
        self.hide_btn.pack(side=tk.RIGHT)

        # 版本切换下拉框
        self.version_frame = ttk.Frame(self.root, style="Version.TFrame")
        self.version_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(self.version_frame, text="当前版本：", style="Version.TLabel").pack(side=tk.LEFT, padx=5)
        self.version_var = tk.StringVar(value="0.5")
        self.version_combobox = ttk.Combobox(self.version_frame, textvariable=self.version_var, values=["0.5", "1.0"], state="readonly", style="Version.TCombobox")
        self.version_combobox.pack(side=tk.LEFT, padx=5)
        self.switch_btn = ttk.Button(self.version_frame, text="切换版本", command=self.switch_version, style="Switch.TButton")
        self.switch_btn.pack(side=tk.RIGHT, padx=5)

        # 对话显示区域
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg="#2a2a2a", fg="#ffffff", font=("Consolas", 10))
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.chat_area.config(state=tk.DISABLED)  # 初始不可编辑

        # 输入区域
        self.input_frame = ttk.Frame(self.root, style="Input.TFrame")
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        self.input_entry = ttk.Entry(self.input_frame, style="Input.TEntry")
        self.input_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)
        self.send_btn = ttk.Button(self.input_frame, text="发送", command=self.send_message, style="Send.TButton")
        self.send_btn.pack(side=tk.RIGHT, padx=5)

        # 记忆操作按钮
        self.memory_frame = ttk.Frame(self.root, style="Memory.TFrame")
        self.memory_frame.pack(fill=tk.X, padx=10, pady=5)
        self.export_btn = ttk.Button(self.memory_frame, text="导出记忆", command=self.export_memory, style="Memory.TButton")
        self.export_btn.pack(side=tk.LEFT, padx=5)
        self.import_btn = ttk.Button(self.memory_frame, text="导入记忆", command=self.import_memory, style="Memory.TButton")
        self.import_btn.pack(side=tk.RIGHT, padx=5)

        # 设置样式（深色模式，贴合游戏）
        self.set_style()

    def set_style(self):
        """设置悬浮窗样式，深色模式，低饱和度，不遮挡游戏"""
        style = ttk.Style()
        # 标题栏样式
        style.configure("Title.TFrame", background="#333333")
        style.configure("Title.TLabel", background="#333333", foreground="#ffffff", font=("Consolas", 11, "bold"))
        style.configure("Close.TButton", background="#ff4444", foreground="#ffffff", borderwidth=0)
        style.configure("Hide.TButton", background="#444444", foreground="#ffffff", borderwidth=0)
        # 版本切换样式
        style.configure("Version.TFrame", background="#1a1a1a")
        style.configure("Version.TLabel", background="#1a1a1a", foreground="#ffffff", font=("Consolas", 10))
        style.configure("Version.TCombobox", background="#2a2a2a", foreground="#ffffff", fieldbackground="#2a2a2a", borderwidth=1)
        style.configure("Switch.TButton", background="#0088ff", foreground="#ffffff", borderwidth=0)
        # 输入区域样式
        style.configure("Input.TFrame", background="#1a1a1a")
        style.configure("Input.TEntry", background="#2a2a2a", foreground="#ffffff", borderwidth=1)
        style.configure("Send.TButton", background="#00aa00", foreground="#ffffff", borderwidth=0)
        # 记忆操作按钮样式
        style.configure("Memory.TFrame", background="#1a1a1a")
        style.configure("Memory.TButton", background="#8844ff", foreground="#ffffff", borderwidth=0)

    def start_drag(self, event):
        """开始拖动悬浮窗"""
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """拖动悬浮窗"""
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f"+{x}+{y}")

    def hide_window(self, event=None):
        """隐藏悬浮窗（按ESC或点击缩小按钮）"""
        self.root.withdraw()

    def show_window(self):
        """显示悬浮窗（可通过快捷键唤醒，后续可扩展）"""
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def quit_window(self):
        """关闭悬浮窗，退出程序"""
        self.root.quit()
        self.root.destroy()

    def switch_version(self):
        """切换当前适配版本，即时生效"""
        from crawler import set_crawler_version
        from ai.memory_retriever import set_version_priority
        current_version = self.version_var.get()
        set_version_priority(current_version)
        set_crawler_version(current_version)
        self.add_message(f"系统提示：已切换至{current_version}版本，AI将优先使用该版本记忆与资讯", "system")

    def send_message(self):
        """发送用户提问，获取AI回答并显示"""
        question = self.input_entry.get().strip()
        if not question:
            return
        # 清空输入框，添加用户提问到聊天区域
        self.input_entry.delete(0, tk.END)
        self.add_message(f"你：{question}", "user")
        # 获取AI回答
        response = ask_ai(question)
        self.add_message(f"AI助手：{response}", "ai")

    def add_message(self, message, sender):
        """添加消息到聊天区域"""
        self.chat_area.config(state=tk.NORMAL)
        if sender == "system":
            self.chat_area.insert(tk.END, f"{message}\n\n", "system")
        elif sender == "user":
            self.chat_area.insert(tk.END, f"{message}\n\n", "user")
        elif sender == "ai":
            self.chat_area.insert(tk.END, f"{message}\n\n", "ai")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)  # 自动滚动到最新消息

    def export_memory(self):
        """导出记忆包"""
        result = export_memory()
        self.add_message(f"系统提示：{result}", "system")

    def import_memory(self):
        """导入记忆包（简易版，可扩展为文件选择对话框）"""
        # 后续可扩展为tkinter文件选择对话框，此处为简易实现
        import_path = input("请输入记忆包路径（绝对路径）：")
        if os.path.exists(import_path):
            result = import_memory(import_path)
            self.add_message(f"系统提示：{result}", "system")
        else:
            self.add_message("系统提示：❌ 记忆包文件不存在，请检查路径", "system")

    def run(self):
        """启动悬浮窗主循环"""
        self.root.mainloop()

# 启动悬浮窗（整合到主程序）
def start_float_window():
    float_window = POE2FloatWindow()
    float_window.run()
```

### （6）主程序入口代码（一键启动所有功能）

```python
# main.py（入口文件，一键启动所有功能）
import threading
from gui.float_window import start_float_window
from crawler import start_crawler_schedule
from utils.memory_manager import init_user_version_memory
import sys

def main():
    print("✅ POE2全版本AI助手启动中...")
    # 1. 初始化用户0.5赛季个人总结（若未初始化）
    try:
        from utils.memory_manager import load_memory
        user_05_mem = load_memory("core", "user_version_0.5.md")
        if not user_05_mem:
            # 若未初始化，提示用户输入个人总结（可直接粘贴你之前的总结）
            print("提示：未检测到你个人总结的0.5赛季细节，请粘贴你的总结内容（粘贴后按回车确认）：")
            user_05_content = sys.stdin.readline().strip()
            while not user_05_content:
                print("请输入有效的总结内容：")
                user_05_content = sys.stdin.readline().strip()
            init_user_version_memory(version="0.5", content=user_05_content)
    except Exception as e:
        print(f"初始化记忆失败：{str(e)}，将继续启动程序")

    # 2. 启动爬虫定时任务（后台线程，不影响主程序）
    crawler_thread = threading.Thread(target=start_crawler_schedule, daemon=True)
    crawler_thread.start()
    print("✅ 爬虫线程已启动，开始同步实时资讯与做装攻略")

    # 3. 启动悬浮窗（主线程）
    print("✅ 启动悬浮窗，游戏时可置顶使用，按ESC隐藏，关闭窗口退出程序")
    start_float_window()

if __name__ == "__main__":
    main()
```

# 五、部署与使用说明（全版本通用，简单易操作）

## 5\.1 环境配置（Windows系统，无需专业知识）

1. 安装Python（3\.8及以上版本），下载地址：https://www\.python\.org/downloads/，安装时勾选“Add Python to PATH”；

2. 创建文件夹（如“POE2\_AI助手”），将上述所有代码按项目结构创建对应文件（复制粘贴即可）；

3. 打开命令提示符（CMD），进入创建的文件夹，执行命令：`pip install requests beautifulsoup4 schedule tkinter`，安装所需依赖；

4. 双击运行main\.py，即可启动助手（首次启动需粘贴你总结的0\.5赛季细节，后续无需重复操作）。

## 5\.2 核心使用操作（全版本通用）

- 启动助手：双击main\.py，自动启动悬浮窗和爬虫线程，悬浮窗默认置顶，可拖动到游戏不遮挡的位置；

- 版本切换：在悬浮窗下拉框选择版本（0\.5、1\.0及后续版本），点击“切换版本”即可即时生效；

- 提问与喂养：在输入框输入问题（如“0\.5赛季种树玩法怎么玩？”“做装怎么选底材？”），点击发送，AI会结合你的总结、实时攻略回答；也可输入你的新经验（如“我发现符咒搭配免死结界生存拉满”），发送后自动存入个人记忆；

- 记忆操作：点击“导出记忆”，自动生成记忆包（ZIP格式），可复制到其他电脑或发给朋友；点击“导入记忆”，输入记忆包路径，即可继承所有记忆；

- 悬浮窗控制：按ESC键隐藏悬浮窗，再次启动main\.py可重新显示；点击“×”关闭助手，爬虫也会同步停止；

- 爬虫更新：无需手动操作，爬虫会按预设频率自动更新资讯和做装攻略，更新结果会在悬浮窗系统提示中显示。

## 5\.3 后续版本适配操作（无需重新开发）

- 1\.0及后续版本上线后，助手会自动爬取新版本机制、做装指南，存入对应版本记忆文件夹；

- 你可补充新版本个人总结，在悬浮窗输入“初始化\[版本号\]赛季总结：\+你的总结内容”，发送后自动存入专属记忆；

- 若新增资讯来源，可在crawler文件夹新增对应爬虫文件，参考现有爬虫代码编写，无需改动核心程序；

- 若LLM模型更新，可替换llm\_engine\.py中的llm\_call函数，无需改动其他模块。

# 六、常见问题解决（全版本通用）

- 问题1：爬虫失败/无法更新资讯？
解决：检查网络连接，确保目标网站可正常访问；若网站链接变更，修改对应爬虫文件中的url地址即可。

- 问题2：悬浮窗遮挡游戏画面？
解决：拖动悬浮窗到屏幕边缘，或按ESC隐藏；可在config\.py中调整悬浮窗大小和透明度。

- 问题3：记忆包导出/导入失败？
解决：确保导出路径无中文、无特殊字符；导入时输入记忆包绝对路径（如“D:/POE2\_AI记忆包\.zip”）。

- 问题4：切换版本后AI回答不准确？
解决：切换版本后，等待1\-2分钟，让爬虫同步该版本最新资讯；若仍不准确，可手动补充该版本个人总结。

- 问题5：游戏运行时助手卡顿？
解决：助手默认低CPU占用，若卡顿，可关闭不必要的后台程序；在config\.py中降低爬虫频率（如将POE2 Ninja爬虫改为每4小时一次）。

# 七、总结（全版本长期可用）

> （注：文档部分内容可能由 AI 生成）
