import click
import os
import toml
import re
import pathlib
from parse_time_input import parse_time_input
from datetime import datetime, timedelta, time
from rich.console import Console


###
#可能的新功能
#1. win系统右下角定时提醒
#2. 更多‘趣味’，程序交互更人性化
#3. 记录时间功能是不会做的，完全没必要

# 使用 rich 来实现彩色输出
console = Console()

folder = pathlib.Path(__file__).parent.resolve()

today_date = datetime.today().strftime("%Y%m%d")
# 每日文件
TODO_FILE = f"{folder}/todo.norg"
TIME_FILE = f"{folder}/{today_date}_time.norg"
# 模板文件
TODO_TMPL_FILE = f"{folder}/config/todo_tmpl.norg"
TIME_TMPL_FILE = f"{folder}/config/time_tmpl.norg"
CONFIG_FILE = f"{folder}/config/config.toml"
ARCHIVE_FOLDER = f"{folder}/A"

# 配置文件读取
config = toml.load(CONFIG_FILE)
timestamp_format = config.get("timestamp_format", "%H:%M")

@click.group()
def cli():
    """正常生命体征维持工具"""
    pass

## debug
# @cli.command()
# def debug():
#     """debug"""
#     print(TIME_FILE)

###----------------------------------
### TODO逻辑
## od - tOdo eDit
# 
## ox - tOdo neXt
#
## oo - tOdo shOw
#
### TODO显示


### TIME逻辑
## igc - tIme Gen Config

## ig - tIme Gen

## id - tIme eDit
# 

## ia - tIme Add

## ii - tIme show

### whataday

### 解析和显示
###----------------------------------

### TODO逻辑
## od - tOdo eDit
@cli.command()
def od():
    """打开或编辑todo.norg"""
    # 检查 todo 文件是否存在
    if os.path.exists(TODO_FILE):
        console.print(f"[yellow]文件 {TODO_FILE} 已存在，打开文件进行编辑。[/yellow]")
    else:
        # 如果文件不存在，读取默认配置并创建新文件
        with open(TODO_TMPL_FILE, 'r', encoding='utf-8') as f:
            default_content = f.read()
        write_file(TODO_FILE, default_content)
        console.print(f"[green]文件 {TODO_FILE} 不存在，已创建并写入默认内容。[/green]")
    
    # 使用 nvim 打开文件
    console.print(f"打开文件: [cyan]{TODO_FILE}[/cyan]")
    os.system(f"nvim {TODO_FILE}")

# 
## ox - tOdo neXt
@cli.command()
def ox():
    """将当前任务状态更新为完成，并将下一任务设置为正在处理"""
    if not os.path.exists(TODO_FILE):
        console.print(f"[red]文件 {TODO_FILE} 不存在。[/red]")
        return

    with open(TODO_FILE, "r+", encoding="utf-8") as f:
        content = f.readlines()

        # 找到当前 processing 和 next 状态任务
        processing_idx = None
        next_indices = []
        for i, line in enumerate(content):
            if "(=)" in line:  # 正在处理
                processing_idx = i
            elif "(>)" in line:  # 下一步
                next_indices.append(i)

        # 准备更改内容
        current_task = None
        next_task = None
        if processing_idx is not None:
            current_task = content[processing_idx].strip().replace("(=)", "").strip()

        if next_indices:
            if len(next_indices) == 1:
                next_task = content[next_indices[0]].strip().replace("(>)", "").strip()
                next_idx = next_indices[0]
            else:
                # 列出所有 next 状态任务供用户选择
                console.print("[yellow]多项待处理任务，请选择：[/yellow]")
                for idx, next_idx in enumerate(next_indices, start=1):
                    task_text = content[next_idx].strip().replace("(>)", "").strip()
                    console.print(f"[cyan]{idx}. {task_text}[/cyan]")
                choice = click.prompt("请输入序号\n>", type=int)
                next_task = content[next_indices[choice - 1]].strip().replace("(>)", "").strip()
                next_idx = next_indices[choice - 1]

        # 确认更改内容
        changes = []
        if current_task:
            changes.append(f"[green]已完成任务：[/green] {current_task}")
        if next_task:
            changes.append(f"[blue]下一项任务：[/blue] {next_task}")
        if not changes:
            console.print("[red]没有可更改的任务状态！[/red]")
            return

        console.print("\n".join(changes))
        confirm = click.confirm("确认是否更改？\n>", default=True)

        if confirm:
            # 更新文件内容
            if processing_idx is not None:
                content[processing_idx] = content[processing_idx].replace("(=)", "(x)")  # 将当前任务标记为完成
            if next_task:
                content[next_idx] = content[next_idx].replace("(>)", "(=)")  # 将选择的 next 状态标记为 processing

            # 写回文件
            f.seek(0)
            f.writelines(content)
            f.truncate()

            # 显示更改的内容
            console.print("\n更改已完成：")
            if current_task:
                console.print(f"[green]已完成：[/green] {current_task}")
            if next_task:
                console.print(f"[blue]下一项：[/blue] {next_task}")
        else:
            console.print("[yellow]更改已取消。[/yellow]")

#
## oo - tOdo shOw
@cli.command()
def oo():
    """解析展示todo内容"""
    # 读取TODO文件内容并解析
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            todo_content = f.read()
            parse_and_display_norg("todo", todo_content)
    else:
        console.print(f"[red]文件 {TODO_FILE} 不存在。(先使用rv od创建)[/red]")

#
def extract_timestamp(todo_text):
    """
    提取任务中的时间戳，如 [15:30] 或 [2:00]
    返回时间戳字符串，或者 None 如果没有时间戳
    """
    match = re.search(r'\[(\d{1,2}:\d{2})\]', todo_text)
    if match:
        return match.group(1)  # 返回时间戳，例如 '15:30'
    return None

def get_timestamp_status(timestamp):
    """
    判断时间戳与当前时间的关系：
    - 如果时间戳在当前时间之前，返回 '❕'
    - 如果时间戳在当前时间之后，返回 '❗'
    - 如果时间戳等于当前时间，返回空字符串
    """
    current_time = datetime.now().replace(second=0, microsecond=0)
    timestamp_time = datetime.strptime(timestamp, "%H:%M").replace(year=current_time.year, month=current_time.month, day=current_time.day)

    if timestamp_time < current_time:
        return "❗"  # 时间戳在当前时间之前
    elif timestamp_time <= current_time + timedelta(minutes=15) :
        return "❕"  # 时间戳在当前时间之后15min内
    return ""  # 时间戳等于当前时间时不加任何符号

def parse_and_display_todo(content):
    """
    解析 TODO 文件内容并以颜色显示
    - ( ) 表示未完成 (白色)
    - (x) 表示已完成 (绿色)
    - (?) 表示待定 (黄色)
    - (=) 表示正在处理 (蓝色)
    - (_) 表示搁置 (灰色)
    - (+) 表示重要 (红色)
    - (>) 表示下一步 (紫色)
    """
    console.print("\n[bold underline]TODO:[/bold underline]")
    lines = content.splitlines()

    for line in lines:
        if line.strip().startswith("-"):
            todo_text = line.strip()
            timestamp = extract_timestamp(todo_text)

            # 判断时间戳状态
            if timestamp:
                timestamp_status = get_timestamp_status(timestamp)

                todo_text = todo_text.replace(
                    timestamp,
                    f"{timestamp_status}{timestamp}"   # 符号放在时间戳前
                )
            # 标记任务状态
            if "( )" in line:
                todo_text = todo_text.replace("( )", "").strip()
                console.print(f"⚪ {todo_text:<20}")
            elif "(x)" in line:
                todo_text = todo_text.replace("(x)", "").strip()
                console.print(f"🟢 {todo_text:<20} [green]---done[/green]")
            elif "(?)" in line:
                todo_text = todo_text.replace("(?)", "").strip()
                console.print(f"🔺 {todo_text:<20} [yellow]---pending[/yellow]")
            elif "(=)" in line:
                todo_text = todo_text.replace("(=)", "").strip()
                console.print(f"🟦 {todo_text:<20} [blue]---processing[/blue]")
            elif "(_)" in line:
                todo_text = todo_text.replace("(_)", "").strip()
                console.print(f"🔸 {todo_text:<20} [grey]---paused[/grey]")
            elif "(+)" in line:
                todo_text = todo_text.replace("(+)", "").strip()
                console.print(f"🔻 {todo_text:<20} [red]---important[/red]")
            elif "(>)" in line:
                todo_text = todo_text.replace("(>)", "").strip()
                console.print(f"🟪 {todo_text:<20} [magenta]---next[/magenta]")
            else:
                console.print(todo_text)
        elif "^EOP^" in line:
            break
        else:
            # 默认输出段落标题或其他文本
            console.print(line)
        


### TODO显示


### TIME逻辑
## igc - tIme Gen Config
@cli.command()
def igc():
    """通过询问和编辑生成每日时间记录配置文件"""
    console.print("[cyan]Greetings, human! 🤖\n")

    # 获取基本信息
    wake_up_time = click.prompt("今天几点醒来？(支持任何时间输入格式)\n>")
    sleep_duration = click.prompt("昨晚睡眠时长？(支持任何时间输入格式)\n>")
    had_breakfast = click.confirm("是否吃早餐？\n>", default=False)
    lunch_time = click.prompt("计划午餐时间？(支持任何时间输入格式)\n>")

    # 计算推荐晚饭时间
    lunch_time_obj = datetime.strptime(parse_time_input(lunch_time), "%H:%M").time()
    if lunch_time_obj:
        suggested_dinner_times = [
            (datetime.combine(datetime.today(), lunch_time_obj) + timedelta(hours=5.5) + timedelta(minutes=-30)).strftime("%H:%M"),
            (datetime.combine(datetime.today(), lunch_time_obj) + timedelta(hours=5.5)).strftime("%H:%M"),
            (datetime.combine(datetime.today(), lunch_time_obj) + timedelta(hours=5.5) + timedelta(minutes=30)).strftime("%H:%M"),
        ]
        dinner_time = click.prompt(
            f"建议的晚餐时间: {', '.join(suggested_dinner_times)}，或选择其他时间\n>",
            default=suggested_dinner_times[1],
        )
    else:
        console.print("[yellow]无法解析午餐时间，晚餐时间将为默认时间(17:30)[/yellow]")
        dinner_time = "17:30"
    
    
    # 计算建议的睡眠时间
    wake_up_time = parse_time_input(wake_up_time)
    wake_up_time_obj = datetime.strptime(parse_time_input(wake_up_time), "%H:%M").time()
    sleep_time = (datetime.combine(datetime.today(), wake_up_time_obj) + timedelta(hours=16)).strftime("%H:%M")
    # 计算喝水时间
    Drinking_water_target1 = (datetime.combine(datetime.today(), wake_up_time_obj) + timedelta(hours=8)).strftime("%H:%M")
    Drinking_water_target2 = sleep_time
    # 格式化午餐时间
    lunch_time = lunch_time_obj.strftime("%H:%M")
    sleep_duration = parse_time_input(sleep_duration)
    # 获取时间戳
    # time_stamp = datetime.now().strftime('%Y-%m-%D %H:%M:%S')
    # 获取用户目标时长
    a_hours = click.prompt("目标 A (积累向) 预估时长（小时）\n>", type=int)
    b_hours = click.prompt("目标 B (消耗向) 预估时长（小时）\n>", type=int)

    # 保存到 config.toml
    config_data = {
        "timestamp_format": "%H:%M",
        "Drinking_water_target1": Drinking_water_target1,
        "Drinking_water_target2": Drinking_water_target2,
        "sleep_duration": sleep_duration,
        "wake_up_time": wake_up_time,
        "had_breakfast": had_breakfast,
        "lunch_time": lunch_time,
        "dinner_time": dinner_time,
        "sleep_time": sleep_time, 
        "a_hours": a_hours,
        "b_hours": b_hours,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        toml.dump(config_data, f)

    # 确保 time_conf.norg 存在并打开编辑
    if not os.path.exists(TIME_TMPL_FILE):
        default_content = """routine:
  - ( ) 跑步
  - ( ) 洗澡
habits:
  - ( ) 记得喝水
  - ( ) 坐姿端正
"""
        write_file(TIME_TMPL_FILE, default_content)
        console.print(f"[green]配置文件 {TIME_TMPL_FILE} 已创建。[/green]")

    console.print(f"[cyan]请编辑每日时间配置文件: {TIME_TMPL_FILE}[/cyan]")
    os.system(f"nvim {TIME_TMPL_FILE}")

    console.print("[green]每日时间配置已完成！rv ig将生成每日时间文件[/green]")

## ig - tIme Gen
@cli.command()
def ig():
    """生成今日的时间记录文件"""
    time_file = f"{folder}/{get_time_file_name()}"

    if os.path.exists(time_file):
        console.print(f"[yellow]今日的时间记录文件已存在: {time_file}[/yellow]")
        return

    if not os.path.exists(CONFIG_FILE):
        console.print(f"[red]配置文件 {CONFIG_FILE} 不存在，请先运行 igc！[/red]")
        return

    if not os.path.exists(TIME_TMPL_FILE):
        console.print(f"[red]时间配置文件 {TIME_TMPL_FILE} 不存在，请先运行 igc！[/red]")
        return

    # 读取 config.toml 配置
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = toml.load(f)

    # 解析 time_conf.norg
    with open(TIME_TMPL_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    routine = []
    habits = []
    section = None
    for line in lines:
        if line.strip().lower() == "* routine":
            section = "routine"
        elif line.strip().lower() == "* dev good habits":
            section = "habits"
        elif line.strip().startswith("- (") and section:
            if "(d)" not in line:  # 过滤禁用项
                if section == "routine":
                    routine.append(line.strip())
                elif section == "habits":
                    habits.append(line.strip())

    # 生成时间记录文件内容
    today = datetime.now().strftime("%Y%m%d")
    time_content = f"""[{today}]time.norg
routine:
{chr(10).join(routine)}
habits:
{chr(10).join(habits)}
schedule:
{chr(10)}午餐时间：{config.get('lunch_time')}
午休时间：建议在午餐半小时后午休15-25分钟
晚餐时间：{config.get('dinner_time')}
晚睡时间：{config.get('sleep_time')}
喝水目标：在{config.get('Drinking_water_target1')}前喝完600ml水，在{config.get('Drinking_water_target2')}前喝完另600ml水。
{chr(10)}
Asec({config.get('a_hours', 4)}h)
Bsec({config.get('b_hours', 4)}h)
Csec
"""

    # 写入文件
    write_file(time_file, time_content)
    console.print(f"[green]时间记录文件生成成功: {time_file}[/green]")

## id - tIme eDit
@cli.command()
def id():
    """打开或编辑time.norg """
    # 检查 time 文件是否存在
    if os.path.exists(TIME_FILE):
        console.print(f"[yellow]文件 {TIME_FILE} 已存在，打开文件进行编辑。[/yellow]")
        # 使用 nvim 打开文件
        console.print(f"打开文件: [cyan]{TIME_FILE}[/cyan]")
        os.system(f"nvim {TIME_FILE}")
    else:
        # 如果文件不存在，提示用户先运行ig命令
        console.print(f"[green]文件 {TIME_FILE} 不存在，先运行rv ig命令生成。[/green]")

## ia - tIme Add
@cli.command()
@click.argument("time_str")  # 接受时间字符串（+45m 或 -30m 等）
@click.argument("task_description")  # 接受任务描述
def ia(time_str, task_description):
    """
    添加时间记录到time.norg 文件 <str:时间+45m或_30m)> <str:任务描述>
    """
    today_date = datetime.now().strftime("%Y%m%d")
    time_file = f"{today_date}_time.norg"

    # 检查文件是否存在
    if not os.path.exists(time_file):
        console.print(f"[red]文件 {time_file} 不存在，请先运行 ig 生成文件。[/red]")
        return

    # 从 config.toml 中加载目标时间
    config = toml.load(CONFIG_FILE)
    asec_target_hours = config.get('a_hours', 4)
    bsec_target_hours = config.get('b_hours', 4)

    # 判断时间类型 (Asec 或 Bsec)
    # time_type = "Asec" if time_str.startswith("+") else "Bsec"
    
    if time_str.startswith("+"):
        time_type = "Asec"
    elif time_str.startswith("_"):
        time_type = "Bsec"
    elif time_str.startswith("."):
        time_type = "Csec"

    # 当前时间戳
    timestamp = datetime.now().strftime("%H:%M:%S")
    # 解析时间字符串
    try:
        time_minutes = parse_time_str(time_str)
        if isinstance(time_minutes, int):
            # 格式化新记录
            new_entry = f"^   \t{abs(time_minutes)}min\t{task_description}\t{timestamp}\n"
        else:
            new_entry = f"^   \t{time_minutes}\t{task_description}\t{timestamp}\n"
    except ValueError:
        console.print("[red]时间格式无效，请使用 +45m 或 _30m 或 .17:30 等格式。[/red]")
        return


    with open(time_file, "r+", encoding="utf-8") as f:
        lines = f.readlines()

        # 初始化时间统计变量
        asec_total = 0
        bsec_total = 0

        # 查找 Asec 和 Bsec 块和 Csec 块位置
        asec_start = lines.index(next(filter(lambda l: l.startswith("Asec("), lines))) + 1
        bsec_start = lines.index(next(filter(lambda l: l.startswith("Bsec("), lines))) + 1
        csec_start = lines.index(next(filter(lambda l: l.startswith("Csec"), lines))) + 1

        # 计算现有时间消耗
        for i in range(asec_start, len(lines)):
            if not lines[i].startswith("^   "):
                break
            asec_total += parse_existing_time(lines[i])
        for i in range(bsec_start, len(lines)):
            if not lines[i].startswith("^   "):
                break
            bsec_total += parse_existing_time(lines[i])

        # 添加新记录到正确的块
        if time_type == "Asec":
            lines.insert(asec_start, new_entry)
            asec_total += abs(time_minutes)
        elif time_type == "Bsec":
            lines.insert(bsec_start, new_entry)
            bsec_total += abs(time_minutes)
        else:
            lines.insert(csec_start, new_entry)

        # 更新统计信息
        update_asec_summary(lines, asec_total, asec_target_hours)
        update_bsec_summary(lines, bsec_total, bsec_target_hours)

        # 写回文件
        f.seek(0)
        f.writelines(lines)
        f.truncate()

        console.print(f"[green]已添加记录：[/green] {new_entry.strip()}")


def parse_time_str(time_str):
    """
    解析时间字符串 (+45m 或 _30m) 为分钟整数以及.17:30为 17:30
    """
    if not (time_str.startswith("+") or time_str.startswith("_") or time_str.startswith(".")):
        raise ValueError("时间字符串必须以 +, _ 或 . 开头。")
    
    if time_str.startswith("+") or time_str.startswith("_"):
        time_str = time_str[1:]  # 去掉前缀符号
        if not time_str.endswith("m"):
            raise ValueError("时间字符串必须以 'm' 结尾。")
        return int(time_str[:-1])
    else:
        time_str = time_str[1:]  # 去掉前缀符号
        if not re.match(r"^\d{1,2}:\d{2}$", time_str):
            raise ValueError("时间点字符串必须符合17:30的格式。")
        return time_str


def update_asec_summary(lines, asec_total, asec_target_hours):
    """
    更新 Asec 总计信息
    """
    remaining_minutes = asec_target_hours * 60 - asec_total
    percentage = (asec_total / (asec_target_hours * 60)) * 100 if asec_target_hours > 0 else 0
    summary = f"Asec[+{asec_total}m]:[剩余:{remaining_minutes}m]:({percentage:.1f}%)"

    for i, line in enumerate(lines):
        if line.startswith("Asec[+"):
            lines[i] = summary
            return
    lines.append(summary)


def update_bsec_summary(lines, bsec_total, bsec_target_hours):
    """
    更新 Bsec 总计信息
    """
    remaining_minutes = bsec_target_hours * 60 - bsec_total
    percentage = (bsec_total / (bsec_target_hours * 60)) * 100 if bsec_target_hours > 0 else 0
    summary = f"\nBsec[-{bsec_total}m]:[剩余:{remaining_minutes}m]:({percentage:.1f}%)"

    for i, line in enumerate(lines):
        if line.startswith("Bsec[-"):
            lines[i] = summary
            return
    lines.append(summary)

## ii - tIme show
@cli.command()
def ii():
    """
    解析并展示当日的 time.norg 文件内容
    """
    today_date = datetime.now().strftime("%Y%m%d")
    time_file = f"{folder}/{today_date}_time.norg"

    if not os.path.exists(time_file):
        console.print(f"[red]文件 {time_file} 不存在。请先运行 ig 生成文件。[/red]")
        return

    with open(time_file, "r", encoding="utf-8") as f:
        content = f.read()
        parse_and_display_norg("time",content)

def parse_task_line(line):
    """
    解析任务行，例如：
    - ( ) 计划的时间 跑步
    返回格式化后的任务字典或字符串
    """
    status = "未完成"
    if "(x)" in line:
        status = "完成"
    elif "(d)" in line:
        status = "搁置"

    task_text = line.split(")", 1)[1].strip() if ")" in line else line.strip()
    return {"status": status, "text": task_text}


def parse_existing_time(line):
    """
    从时间记录行解析时间分钟数，例如：
    '\t45min study 15:30:45' -> 返回 45
    """
    try:
        time_part = line.strip().split("\t")[1]
        return int(time_part.replace("min", "").strip())
    except (IndexError, ValueError):
        return 0


def parse_target_time(header):
    """
    解析 Asec 和 Bsec 的目标时间，例如：
    Asec(4h) -> 返回 4（小时）
    """
    try:
        start = header.index("(") + 1
        end = header.index("h")
        return int(header[start:end])
    except (ValueError, IndexError):
        return 0


def display_tasks(tasks):
    """
    使用 rich 显示任务列表，按状态显示不同颜色
    """
    for task in tasks:
        if task["status"] == "完成":
            console.print(f"[green]✓ {task['text']}[/green]")
        elif task["status"] == "搁置":
            console.print(f"[yellow]- {task['text']}[/yellow]")
        else:
            console.print(f"[white]⧗ {task['text']}[/white]")

def display_schedule(schedule):
    """
    使用 rich 显示时间安排
    """
    for schedule_ in schedule:
        console.print(schedule_)

def display_time_entries(entries):
    """
    使用 rich 显示时间记录
    """
    for entry in entries:
        parts = entry.strip().split("\t")
        time_spent = parts[1]
        task = parts[2] if len(parts) > 1 else ""
        timestamp = parts[3] if len(parts) > 2 else ""
        console.print(f"[cyan]{time_spent:<8}[/cyan] {task:<20} [dim]{timestamp}[/dim]")


def display_summary(total_minutes, target_hours, section_name):
    """
    显示时间段统计信息，包括总时间、目标时间和完成百分比
    """
    target_minutes = target_hours * 60
    remaining_minutes = target_minutes - total_minutes
    percentage = (total_minutes / target_minutes) * 100 if target_minutes > 0 else 0

    summary = f"{section_name}[+{total_minutes}m][剩余:{remaining_minutes}m]({percentage:.1f}%)"
    color = "green" if percentage >= 100 else "yellow" if percentage >= 50 else "red"
    console.print(f"[{color}]{summary}[/{color}]")

### whataday
## 将todo.norg和time.norg的内容格式化后复制到一个文件中，然后打印该文件，
# 并询问用户是否确认删除todo.norg和time.norg
@cli.command()
def whataday():
    """
    归档当日的todo.norg和time.norg
    """
    if not (os.path.exists(TIME_FILE) and os.path.exists(TODO_FILE)):
        console.print(f"[red]文件 {TIME_FILE} 或 {TODO_FILE}不存在。归档失败！[/red]")
        return
    today_date = datetime.now().strftime("%Y%m%d")
    archive_folder = "./A"
    archive_file = os.path.join(archive_folder, f"{today_date}.a.norg")

    # Ensure archive directory exists
    os.makedirs(archive_folder, exist_ok=True)
    file_paths = [TODO_FILE, TIME_FILE]
    # 创建一个新的文本文件
    combined_archive_file = open(archive_file, "w", encoding='utf-8')

    # 逐个将文本文件追加到新文件中
    combined_archive_file.write("TODO list:\n")
    file = open(TODO_FILE, "r", encoding='utf-8')
    content = file.readlines()
    for line in content:
        if line.startswith("^EOP^"):
            break
        combined_archive_file.writelines(line)
    file.close()

    combined_archive_file.write("^EOP^")

    combined_archive_file.write("\n\nTIME logs:\n")
    file = open(TIME_FILE, "r", encoding='utf-8')
    content = file.read()
    combined_archive_file.write(content)
    file.close()

    # 关闭新文件
    combined_archive_file.close()

    # Confirm deletion
    confirm_delete = click.confirm(f"是否删除每日临时文件？({today_date}_time.norg & todo.norg)请妥善处理todo.norg中的笔记内容", default=False)
    if confirm_delete:
        delete_file(TODO_FILE)
        delete_file(TIME_FILE)
        console.print("[yellow]每日临时文件已清理[/yellow]")
        console.print(f"每日总结已生成，保存于 {folder}/A (通过'rv archive'命令打开目录)")
    else:
        console.print("[yellow]每日临时文件保留[/yellow]")
        console.print(f"每日总结已生成，保存于 {folder}/A (通过'rv archive'命令打开目录)")

    with open(archive_file, "r", encoding="utf-8") as f:
        content = f.read()
        parse_and_display_norg("A",content)
    
@cli.command
def archive():
    """打开归档文件夹"""
    try:
        # 调用资源管理器打开文件夹
        os.system(f"nvim {ARCHIVE_FOLDER}")
    except Exception as e:
        click.echo(f"打开文件夹失败: {e}", err=True)

### 解析和显示

### 通用逻辑函数
def read_file(filepath):
    """Read the content of a file if it exists, otherwise return an empty string."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read().strip()
    return ""

def write_file(filepath, content):
    """Write content to a file."""
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

def delete_file(filepath):
    """Delete a file if it exists."""
    if os.path.exists(filepath):
        os.remove(filepath)

def get_time_file_name():
    """生成今日的时间记录文件名"""
    today = datetime.now().strftime("%Y%m%d")
    return f"{today}_time.norg"

def parse_and_display_time(content):
    routine = []
    habits = []
    schedule = []
    asec_entries = []
    bsec_entries = []
    csec_entries = []
    asec_target, bsec_target = 0, 0
    asec_total, bsec_total = 0, 0

    lines = content.splitlines()
    # 解析文件内容
    section = None
    for line in lines:
        stripped = line.strip()

        # 检测段落标题
        if stripped.startswith("routine"):
            section = "routine"
        elif stripped.startswith("habits"):
            section = "habit"
        elif stripped.startswith("schedule"):
            section = "schedule"
        elif stripped.startswith("Asec("):
            section = "asec"
            asec_target = parse_target_time(stripped)
        elif stripped.startswith("Bsec("):
            section = "bsec"
            bsec_target = parse_target_time(stripped)
        elif stripped.startswith("Csec"):
            section = "csec"
        elif stripped.startswith("- ("):
            # 常规任务
            if section == "routine":
                routine.append(parse_task_line(stripped))
            elif section == "habit":
                habits.append(parse_task_line(stripped))
        elif stripped.startswith("午") or stripped.startswith("晚") or stripped.startswith("喝"):
            if section == "schedule":
                schedule.append(stripped)
        elif section == "asec" and stripped.startswith("^   "):
            asec_entries.append(stripped)
            asec_total += parse_existing_time(stripped)
        elif section == "bsec" and stripped.startswith("^   "):
            bsec_entries.append(stripped)
            bsec_total += parse_existing_time(stripped)
        elif section == "csec" and stripped.startswith("^   "):
            csec_entries.append(stripped)


    # 显示结果
    console.print("[bold underline]TIME logs:[/bold underline]")

    console.print("\n[bold underline]Routine:[/bold underline]")
    display_tasks(routine)

    console.print("\n[bold underline]Habits:[/bold underline]")
    display_tasks(habits)

    console.print("\n[bold underline]Schedule:[/bold underline]")
    display_schedule(schedule)

    console.print("\n[bold underline]Asec:[/bold underline]")
    display_time_entries(asec_entries)
    display_summary(asec_total, asec_target, "Asec")

    console.print("\n[bold underline]Bsec:[/bold underline]")
    display_time_entries(bsec_entries)
    display_summary(bsec_total, bsec_target, "Bsec")

    console.print("\n[bold underline]Csec:[/bold underline]")
    display_time_entries(csec_entries)


def parse_and_display_norg(type, content):

    if type == "time":
        console.print("\n[bold underline]TIME logs:[/bold underline]")
        parse_and_display_time(content)
    elif type == "todo":
        console.print("\n[bold underline]TODO list:[/bold underline]")
        parse_and_display_todo(content)
    elif type == "A":
        console.print("\n[bold underline]ARCHIVE:[/bold underline]")
        parse_and_display_todo(content)
        parse_and_display_time(content)
if __name__ == "__main__":
    cli()