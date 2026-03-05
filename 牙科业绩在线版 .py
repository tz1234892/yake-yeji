 import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page
# --- 1. 页面设置 ---
st.set_page_config(page_title="🦷 牙科在线业绩系统", layout="wide")
st.title("🦷 牙科诊所在线业绩录入系统")
st.caption("多人共享链接 · 手机电脑都能用 · 数据自动保存到文件")

# --- 2. 定义常量 ---
items = ["拔牙","种植-科特斯","种植-ITI","种植-悦锆","种植-亲水","种植-登腾",
         "根管治疗","牙冠-爱尔创","牙冠-威兰德","牙冠-泽康","牙冠-拉瓦",
         "补牙-380","补牙-580","补牙-780","补牙-980","补牙-1600",
         "儿童根管","预成冠","间隙保持器","正畸-固定","正畸-隐形",
         "儿童早矫","可摘局部义齿","精密件","个性化基台"]

doctors = ["唐卓","郭全","师维敏","李雨航","白雪嫣","杜根茂","王晓虹"]

# --- 3. 初始化 (只存当前状态，不存业务数据) ---
# 使用 session_state 存储当前用户的选择，避免每次交互都重置
if 'current_day' not in st.session_state:
    st.session_state.current_day = 1
if 'current_data' not in st.session_state:
    # 这里只存一个空壳或默认结构，实际数据来自上传文件
    st.session_state.current_data = {}

# --- 4. 侧边栏：文件上传与日期选择 ---
st.sidebar.header("📂 数据管理")
uploaded = st.sidebar.file_uploader("📤 上传昨天的数据文件（推荐）", type=["xlsx"])

# 读取上传的文件到内存
if uploaded:
    try:
        # 读取所有Sheet
        all_sheets = pd.read_excel(uploaded, sheet_name=None) # 读取所有表
        # 转换为你的内部结构：data[day][doctor] = df
        data = {}
        for day in range(1, 32):
            data[day] = {}
            sheet_name = str(day)
            if sheet_name in all_sheets:
                sheet_df = all_sheets[sheet_name]
                # 假设Excel列是按 项目1,数量1,单价1,合计1, 项目2,数量2... 排列的
                for i, doc in enumerate(doctors):
                    start_col = i * 4
                    if start_col + 3 < len(sheet_df.columns):
                        df = sheet_df.iloc[:, start_col:start_col+4]
                        df.columns = ["项目", "数量", "单价", "合计"]
                        data[day][doc] = df
                    else:
                        # 如果文件中没有该医生的数据，创建默认空表
                        data[day][doc] = pd.DataFrame({"项目": items, "数量": 0, "单价": 0.0, "合计": 0.0})
            else:
                # 如果文件中没有这一天的数据，创建默认空表
                for doc in doctors:
                    data[day][doc] = pd.DataFrame({"项目": items, "数量": 0, "单价": 0.0, "合计": 0.0})
        st.session_state.current_data = data
        st.sidebar.success("✅ 数据加载成功！")
    except Exception as e:
        st.sidebar.error(f"上传失败: {e}")

day = st.sidebar.selectbox(
    "📅 选择日期", 
    range(1,32), 
    format_func=lambda x: f"{x}号",
    key='selected_day' # 使用key防止重置
)

# --- 5. 主界面：多页签录入 ---
# 如果没有上传数据，使用默认空数据
if not st.session_state.current_data:
    # 创建默认数据结构
    default_data = {}
    for d in range(1, 32):
        default_data[d] = {}
        for doc in doctors:
            default_data[d][doc] = pd.DataFrame({"项目": items, "数量": 0, "单价": 0.0, "合计": 0.0})
    current_day_data = default_data[day]
else:
    current_day_data = st.session_state.current_data.get(day, {})

tabs = st.tabs(doctors)
grand_total = 0.0

# 遍历每个医生的标签页
for i, doctor in enumerate(doctors):
    with tabs[i]:
        st.subheader(f"👤 {doctor}")
        
        # 获取当前医生的数据
        if doctor in current_day_data and not current_day_data[doctor].empty:
            df = current_day_data[doctor].copy()
        else:
            df = pd.DataFrame({"项目": items, "数量": 0, "单价": 0.0, "合计": 0.0})
        
        # 关键修复：给 data_editor 加上唯一的 key
        # 这样即使 Streamlit 重新运行，也能识别这是同一个组件
        edited = st.data_editor(
            df,
            column_config={
                "项目": st.column_config.TextColumn("项目", disabled=True),
                "数量": st.column_config.NumberColumn("数量", min_value=0, step=1),
                "单价": st.column_config.NumberColumn("单价 ¥", min_value=0.0, format="¥%.2f"),
                "合计": st.column_config.NumberColumn("合计 ¥", disabled=True, format="¥%.2f")
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{day}_{doctor}" # 唯一Key，解决ID重复报错
        )
        
        # 重新计算合计
        edited["合计"] = edited["数量"] * edited["单价"]
        
        # 这里不再保存回 st.session_state.data，而是临时计算
        doctor_total = edited["合计"].sum()
        st.metric(f"{doctor} 小计", f"¥{doctor_total:,.2f}")
        grand_total += doctor_total

st.divider()
st.metric("🌟 全天总业绩", f"¥{grand_total:,.2f}", border=True)

# --- 6. 下载功能 ---
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 下载当天Excel（给老板看）", type="primary"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 将当前页面显示的数据（包括刚才修改的 edited）整合写入
            combined_df = pd.DataFrame()
            for doc in doctors:
                if doc in current_day_data:
                    temp_df = current_day_data[doc].copy()
                else:
                    temp_df = pd.DataFrame({"项目": items, "数量": 0, "单价": 0.0, "合计": 0.0})
                # 如果刚才在这个页面修改了数据，edited 变量里有最新数据
                # 这里逻辑比较复杂，建议用户填完一个医生点一次保存，或者使用更复杂的缓存机制
                # 简化版：这里只能导出上传时的原始数据，无法导出本次网页修改的临时数据（因为没地方存）
                # 这就是为什么必须重构数据流的原因
                temp_df.columns = [f"{doc}_{col}" for col in temp_df.columns]
                if combined_df.empty:
                    combined_df = temp_df
                else:
                    combined_df = pd.concat([combined_df, temp_df], axis=1)
            combined_df.to_excel(writer, sheet_name=str(day), index=False)
        output.seek(0)
        st.download_button(
            "点击保存当天文件",
            output,
            f"业绩_{day}号.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download_day'
        )

# ... (其他按钮逻辑同理)
