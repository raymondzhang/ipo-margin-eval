# -*- coding: utf-8 -*-
"""
港股IPO数据平台 V2 — 前端美化版

改进点:
1. 现代化卡片式首页
2. 侧边栏图标导航
3. 评分报告一键导出(DOCX/HTML)
4. 情绪数据手动录入
5. 响应式布局优化
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from ipo_platform.models.database import get_db
from ipo_platform.core.report_generator import IPOReportGenerator

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="港股IPO数据平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 自定义CSS
# ============================================================
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 主标题 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }
    .main-subtitle {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    
    /* 指标卡片 */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .kpi-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-top: 4px;
    }
    
    /* IPO卡片 */
    .ipo-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .ipo-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .ipo-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    .ipo-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    .ipo-code {
        color: #888;
        font-size: 0.85rem;
    }
    .ipo-meta {
        color: #666;
        font-size: 0.85rem;
        margin-bottom: 12px;
    }
    .ipo-score-row {
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .score-pill {
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        color: white;
    }
    .score-high { background: #28a745; }
    .score-mid { background: #ffc107; color: #333; }
    .score-low { background: #dc3545; }
    .category-pill {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .cat-whitelist { background: #d4edda; color: #155724; }
    .cat-greylist { background: #fff3cd; color: #856404; }
    .cat-blacklist { background: #f8d7da; color: #721c24; }
    
    /* 侧边栏 */
    .css-1d391kg { padding-top: 1rem; }
    
    /* 详情页 */
    .detail-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .detail-title {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .detail-subtitle {
        opacity: 0.8;
        margin-top: 4px;
    }
    
    /* 按钮 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 数据加载
# ============================================================

@st.cache_data(ttl=300)
def load_current_ipos():
    db = get_db()
    rows = db.fetchall("""
        SELECT b.*, s.total_score, s.base_score, s.category, s.leverage_advice, s.scored_at,
               MAX(mn.oversub_times) as oversub,
               MAX(mn.margin_amount) as margin
        FROM ipo_base b
        LEFT JOIN ipo_scores s ON b.stock_code = s.stock_code
        LEFT JOIN market_sentiment mn ON b.stock_code = mn.stock_code
        WHERE b.status IN ('prospectus', 'ipoing', 'listing_soon', 'listing_tomorrow')
        GROUP BY b.stock_code
        ORDER BY b.list_date ASC
    """)
    return pd.DataFrame([dict(r) for r in rows])

@st.cache_data(ttl=300)
def load_listed_ipos(start_date='20260401'):
    db = get_db()
    rows = db.fetchall("""
        SELECT b.*, s.total_score, s.category,
               p.d1_return, p.w1_return, p.m1_return
        FROM ipo_base b
        LEFT JOIN ipo_scores s ON b.stock_code = s.stock_code
        LEFT JOIN post_listing p ON b.stock_code = p.stock_code
        WHERE b.status = 'listed' AND b.list_date >= ?
        ORDER BY b.list_date DESC
    """, (start_date,))
    return pd.DataFrame([dict(r) for r in rows])

@st.cache_data(ttl=300)
def load_ipo_detail(stock_code):
    db = get_db()
    base = db.fetchone("SELECT * FROM ipo_base WHERE stock_code = ?", (stock_code,))
    score = db.fetchone(
        "SELECT * FROM ipo_scores WHERE stock_code = ? ORDER BY scored_at DESC LIMIT 1",
        (stock_code,)
    )
    financials = db.fetchone("SELECT * FROM ipo_financials WHERE stock_code = ?", (stock_code,))
    cs = db.fetchall("SELECT * FROM ipo_cornerstones WHERE stock_code = ?", (stock_code,))
    sentiment = db.fetchall(
        "SELECT * FROM market_sentiment WHERE stock_code = ? ORDER BY record_date DESC LIMIT 7",
        (stock_code,)
    )
    return {
        'base': dict(base) if base else {},
        'score': dict(score) if score else {},
        'financials': dict(financials) if financials else {},
        'cornerstones': [dict(c) for c in cs],
        'sentiment': [dict(s) for s in sentiment],
    }

@st.cache_data(ttl=300)
def load_market_stats():
    db = get_db()
    industry = db.fetchall("""
        SELECT industry_cat, COUNT(*) as count, AVG(raise_amount) as avg_raise
        FROM ipo_base WHERE list_date >= '20260401' GROUP BY industry_cat
    """)
    monthly = db.fetchall("""
        SELECT substr(list_date, 1, 6) as month, COUNT(*) as ipo_count,
               SUM(raise_amount) as total_raise, AVG(d1_return) as avg_return
        FROM ipo_base b LEFT JOIN post_listing p ON b.stock_code = p.stock_code
        WHERE b.list_date >= '20260401' GROUP BY month ORDER BY month
    """)
    return {
        'industry': pd.DataFrame([dict(r) for r in industry]),
        'monthly': pd.DataFrame([dict(r) for r in monthly]),
    }

# ============================================================
# 组件
# ============================================================

def render_radar(dimensions):
    if not dimensions:
        return None
    categories = list(dimensions.keys())
    scores = [dimensions[c]['score'] for c in categories]
    max_scores = [dimensions[c]['max'] for c in categories]
    labels = {
        'profitability': '盈利能力', 'allocation': '配售结构',
        'cornerstone': '基石投资', 'pricing': '估值定价',
        'stabilization': '稳价机制', 'q1_break_rate': 'Q1破发率',
        'hsi_monthly': 'HSI月度涨跌',
    }
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=[labels.get(c, c) for c in categories] + [labels.get(categories[0], categories[0])],
        fill='toself', name='得分', line_color='#1f77b4', fillcolor='rgba(31,119,180,0.3)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=max_scores + [max_scores[0]],
        theta=[labels.get(c, c) for c in categories] + [labels.get(categories[0], categories[0])],
        name='满分', line_color='rgba(200,200,200,0.5)', line_dash='dash', fill=None
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max_scores)])),
        showlegend=True, height=400, margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

# ============================================================
# 页面
# ============================================================

def page_home():
    st.markdown('<div class="main-title">📊 港股IPO数据平台</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="main-subtitle">数据更新: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 覆盖2026年Q2以来全部港股IPO</div>', unsafe_allow_html=True)
    
    df_current = load_current_ipos()
    df_listed = load_listed_ipos()
    
    # KPI卡片
    cols = st.columns(4)
    metrics = [
        ("当前招股中", len(df_current), "只"),
        ("Q2已上市", len(df_listed), "只"),
        ("Q2总募资", f"{df_listed['raise_amount'].sum():.1f}" if len(df_listed) > 0 else "0", "亿港元"),
        ("平均首日涨幅", f"{df_listed['d1_return'].mean():.1f}%" if len(df_listed) > 0 else "N/A", ""),
    ]
    for col, (label, value, unit) in zip(cols, metrics):
        with col:
            st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{value}<span style="font-size:1rem;font-weight:400;"> {unit}</span></div>
                <div class="kpi-label">{label}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # IPO卡片
    st.subheader("🔥 当前招股中的IPO")
    
    if df_current.empty:
        st.info("暂无正在招股中的IPO")
    else:
        for _, row in df_current.iterrows():
            score = row.get('total_score', 0)
            cat = row.get('category', 'unknown')
            cat_name = {'whitelist': '白名单', 'greylist': '灰list', 'blacklist': '黑名单'}.get(cat, cat)
            cat_cls = {'whitelist': 'cat-whitelist', 'greylist': 'cat-greylist', 'blacklist': 'cat-blacklist'}.get(cat, '')
            score_cls = 'score-high' if score >= 80 else 'score-mid' if score >= 60 else 'score-low'
            
            with st.container():
                st.markdown(f'''
                <div class="ipo-card">
                    <div class="ipo-header">
                        <div>
                            <div class="ipo-name">{row['stock_name']} <span class="ipo-code">{row['stock_code']}</span></div>
                            <div class="ipo-meta">{row.get('industry', '未知')} | 保荐: {row.get('sponsor_primary', 'N/A')} | 上市日: {row.get('list_date', 'N/A')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="score-pill {score_cls}">{score}/110</div>
                            <div style="margin-top:6px;"><span class="category-pill {cat_cls}">{cat_name}</span></div>
                        </div>
                    </div>
                    <div style="display:flex;gap:24px;font-size:0.85rem;color:#666;">
                        <div>📈 杠杆建议: <b>{row.get('leverage_advice', 'N/A')}</b></div>
                        <div>🔥 超购: <b>{row.get('oversub', 'N/A')}x</b></div>
                        <div>💰 募资: <b>{row.get('raise_amount', 'N/A')}亿</b></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button("查看详情 →", key=f"btn_{row['stock_code']}"):
                    st.session_state.page = 'detail'
                    st.session_state.selected_code = row['stock_code']
                    st.rerun()

def page_detail():
    code = st.session_state.get('selected_code', '07666.HK')
    data = load_ipo_detail(code)
    base = data['base']
    score = data['score']
    
    if st.button("← 返回首页"):
        st.session_state.page = 'home'
        st.rerun()
    
    # 头部
    cat = score.get('category', 'unknown')
    cat_name = {'whitelist': '白名单', 'greylist': '灰名单', 'blacklist': '黑名单'}.get(cat, cat)
    total = score.get('total_score', 0)
    
    # 检查招股书PDF是否存在
    pdf_path = Path(__file__).parent.parent / 'data' / 'prospectus' / f"{code.replace('.', '_')}_prospectus.pdf"
    pdf_exists = pdf_path.exists()
    pdf_size = f"({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)" if pdf_exists else ""
    
    st.markdown(f'''
    <div class="detail-header">
        <div class="detail-title">{base.get('stock_name', '')} ({code})</div>
        <div class="detail-subtitle">{base.get('industry', 'N/A')} | {cat_name} | 综合评分 {total}/110</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 招股书链接
    if pdf_exists:
        with open(pdf_path, 'rb') as f:
            st.download_button(
                label=f"📑 下载招股书 {pdf_size}",
                data=f,
                file_name=f"{code}_prospectus.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.info("📑 招股书PDF未下载，可在调度器自动扫描时获取")
    
    # 导出按钮
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("📄 导出DOCX报告", key="export_docx"):
            try:
                gen = IPOReportGenerator()
                path = gen.generate_docx(code)
                with open(path, 'rb') as f:
                    st.download_button("⬇️ 下载DOCX", f, file_name=f"{code}_report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                st.error(f"导出失败: {e}")
    with col2:
        if st.button("🌐 导出HTML报告", key="export_html"):
            try:
                gen = IPOReportGenerator()
                path = gen.generate_html(code)
                with open(path, 'r', encoding='utf-8') as f:
                    html = f.read()
                    st.download_button("⬇️ 下载HTML", html, file_name=f"{code}_report.html", mime="text/html")
            except Exception as e:
                st.error(f"导出失败: {e}")
    
    # 基础信息 + 评分
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📋 基本信息")
        info = {
            "股票代码": code, "行业": base.get('industry', 'N/A'),
            "上市类型": base.get('reg_type', 'N/A'), "保荐人": base.get('sponsor', 'N/A'),
            "招股期": f"{base.get('ipo_start_date', 'N/A')} ~ {base.get('ipo_end_date', 'N/A')}",
            "上市日期": base.get('list_date', 'N/A'),
            "招股价": f"{base.get('price_low', 'N/A')} ~ {base.get('price_high', 'N/A')} 港元",
            "募资额": f"{base.get('raise_amount', 'N/A')} 亿港元",
            "公开发售": f"{base.get('public_pct', 'N/A')}%", "国际配售": f"{base.get('intl_pct', 'N/A')}%",
            "稳价人": base.get('stabilizer', '无'), "绿鞋": '有' if base.get('has_greenshoe') else '无',
        }
        for k, v in info.items():
            st.markdown(f"**{k}**: {v}")
    
    with c2:
        st.subheader("📊 评分总览")
        if score:
            base_score = score.get('base_score', 0)
            st.markdown(f"### {total}/110")
            st.markdown(f"基础分: **{base_score}**/100")
            st.markdown(f"分类: **{cat_name}**")
            st.info(f"**杠杆建议**: {score.get('leverage_advice', 'N/A')}")
            st.warning(f"**风险提示**: {score.get('risk_warning', 'N/A')}")
    
    st.divider()
    
    # 维度拆解
    if score and score.get('evidence_json'):
        import json
        try:
            evidence = json.loads(score['evidence_json'])
            dims = evidence.get('dimensions', {})
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("📈 评分维度")
                dim_rows = []
                dim_names = {
                    'profitability': '盈利能力', 'allocation': '配售结构',
                    'cornerstone': '基石投资', 'pricing': '估值定价',
                    'stabilization': '稳价机制', 'q1_break_rate': 'Q1破发率',
                    'hsi_monthly': 'HSI月度涨跌',
                }
                for k, v in dims.items():
                    bar = '█' * int(v['score'] / v['max'] * 20)
                    dim_rows.append({
                        '维度': dim_names.get(k, k),
                        '得分': f"{v['score']}/{v['max']}",
                        '判定': v.get('desc', ''),
                        '可视化': bar,
                    })
                st.dataframe(pd.DataFrame(dim_rows), use_container_width=True, hide_index=True)
            
            with c2:
                st.subheader("🎯 雷达图")
                fig = render_radar(dims)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"解析评分数据失败: {e}")
    
    # 基石投资者
    if data['cornerstones']:
        st.subheader("🏛️ 基石投资者")
        cs_df = pd.DataFrame(data['cornerstones'])
        display_df = cs_df[['investor_name', 'amount_hkd', 'is_star']].copy()
        display_df.columns = ['投资者名称', '认购金额(亿港元)', '知名机构']
        display_df['知名机构'] = display_df['知名机构'].apply(lambda x: '⭐' if x else '')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # 情绪数据录入
    st.divider()
    st.subheader("🔥 市场情绪数据录入")
    
    db = get_db()
    latest = db.fetchone(
        "SELECT * FROM market_sentiment WHERE stock_code = ? ORDER BY record_date DESC, record_time DESC LIMIT 1",
        (code,)
    )
    if latest:
        latest = dict(latest)
        st.info(f"最新数据: {latest.get('record_date')} {latest.get('record_time')} | 超购 {latest.get('oversub_times')}x | 孖展 {latest.get('margin_amount')}亿港元 | 来源: {latest.get('source')}")
    else:
        st.info("暂无情绪数据")
    
    with st.form("sentiment_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            oversub = st.number_input("超购倍数", min_value=0.0, value=0.0, step=0.1)
        with col2:
            margin = st.number_input("孖展金额(亿港元)", min_value=0.0, value=0.0, step=0.1)
        with col3:
            source = st.selectbox("数据来源", ["手动录入", "etnet", "aastocks", "富途", "华盛"])
        submitted = st.form_submit_button("💾 保存情绪数据")
        if submitted:
            now = datetime.now()
            db.execute("""
                INSERT INTO market_sentiment (stock_code, record_date, record_time, source, margin_amount, oversub_times)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, now.strftime('%Y-%m-%d'), now.strftime('%H:%M'), source, margin, oversub))
            st.success("情绪数据已保存！重新评分后将纳入计算。")
            st.rerun()

def page_history():
    st.markdown('<div class="main-title">📈 历史回测</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">2026年Q2已上市IPO表现跟踪</div>', unsafe_allow_html=True)
    
    df = load_listed_ipos()
    if df.empty:
        st.info("暂无已上市数据")
        return
    
    # 筛选器
    col1, col2 = st.columns([1, 3])
    with col1:
        category_filter = st.multiselect("分类", ['whitelist', 'greylist', 'blacklist'],
                                         default=['whitelist', 'greylist', 'blacklist'])
    df = df[df['category'].isin(category_filter)]
    
    # 汇总
    cols = st.columns(4)
    with cols[0]: st.metric("样本数", len(df))
    with cols[1]: st.metric("平均首日涨幅", f"{df['d1_return'].mean():.1f}%")
    with cols[2]: st.metric("上涨比例", f"{(df['d1_return'] > 0).mean() * 100:.0f}%")
    with cols[3]: st.metric("最大涨幅", f"{df['d1_return'].max():.1f}%")
    
    # 图表
    st.subheader("首日涨幅分布")
    fig = px.histogram(df, x='d1_return', nbins=20, color='category',
                       labels={'d1_return': '首日涨幅%'}, title='')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("评分 vs 实际表现")
    fig2 = px.scatter(df, x='total_score', y='d1_return', color='category',
                      size='raise_amount', hover_data=['stock_name', 'stock_code'],
                      labels={'total_score': '综合评分', 'd1_return': '首日涨幅%'})
    fig2.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("详细数据")
    display_cols = ['stock_code', 'stock_name', 'list_date', 'total_score', 'category', 'd1_return']
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

def page_market():
    st.markdown('<div class="main-title">🌐 市场概览</div>', unsafe_allow_html=True)
    
    stats = load_market_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("行业分布")
        if not stats['industry'].empty:
            fig = px.pie(stats['industry'], values='count', names='industry_cat', title='')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("月度募资趋势")
        if not stats['monthly'].empty:
            fig = px.bar(stats['monthly'], x='month', y='total_raise',
                        labels={'month': '月份', 'total_raise': '募资额(亿港元)'}, title='')
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 导航
# ============================================================

def main():
    # 初始化session_state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    # 侧边栏导航（带图标）
    with st.sidebar:
        st.markdown("### 📊 IPO数据平台")
        st.markdown("---")
        
        nav_items = {
            'home': ('🏠 首页', '当前招股中的IPO'),
            'detail': ('📋 标的详情', '单只IPO完整画像'),
            'history': ('📈 历史回测', '已上市股票表现'),
            'market': ('🌐 市场概览', '行业分布与趋势'),
        }
        
        for key, (label, desc) in nav_items.items():
            active = st.session_state.page == key
            btn_type = "primary" if active else "secondary"
            if st.button(f"{label}\n\n{desc}", key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state.page = key
                st.rerun()
        
        st.markdown("---")
        st.caption("v2.0 | 自动评分引擎")
    
    # 路由
    if st.session_state.page == 'home':
        page_home()
    elif st.session_state.page == 'detail':
        page_detail()
    elif st.session_state.page == 'history':
        page_history()
    elif st.session_state.page == 'market':
        page_market()

if __name__ == '__main__':
    main()
