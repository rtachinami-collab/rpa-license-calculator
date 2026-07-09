import streamlit as st
import pandas as pd
import altair as alt
import time

# Page configuration
st.set_page_config(
    page_title="RPAライセンス料診断ツール",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Gradient headers */
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    /* Value Cards styling */
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4F46E5;
        margin-top: 0.5rem;
    }
    /* CTA Card Premium */
    .cta-card {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
        border: 2px solid #EC4899;
        border-radius: 16px;
        padding: 2.5rem;
        margin-top: 3rem;
        box-shadow: 0 10px 25px rgba(236, 72, 153, 0.1);
    }
    .cta-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .cta-subtitle {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    /* Large Diagnose Button styling */
    div.stButton > button.css-118g5e8, div.stButton > button:first-child {
        border-radius: 50px !important;
        font-size: 1.25rem !important;
        padding: 0.8rem 2.5rem !important;
        transition: all 0.3s ease !important;
    }
</style>
""", unsafe_allow_html=True)

# Title & Subtitle
st.markdown('<div class="main-title">RPAライセンス料診断 ➔ PAD移行シミュレーター</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">UiPathからPower Automate (PAD) へのライセンス移行によるコスト削減効果と、移行難易度を分析します。</div>', unsafe_allow_html=True)

# --- Sidebar Inputs ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-cards.png", width=80)
    
    st.markdown("### 📋 ① 現在のUiPath稼働規模")
    devs = st.number_input(
        "開発者ライセンス数 (Studio等)",
        min_value=0,
        max_value=100,
        value=1,
        step=1,
        help="シナリオを作成・開発するメンバーの人数です。"
    )
    
    attended = st.number_input(
        "有人ロボット実行数 (Attended)",
        min_value=0,
        max_value=500,
        value=0,
        step=1,
        help="ユーザーのPC上で、手動で起動して実行するロボットの数です。"
    )
    
    unattended = st.number_input(
        "無人ロボット実行数 (Unattended)",
        min_value=0,
        max_value=100,
        value=0,
        step=1,
        help="サーバーなどで人手を介さず、完全自動実行するロボットの数です。"
    )
    
    has_orchestrator = st.checkbox(
        "UiPath Orchestratorを導入している",
        value=False,
        help="UiPathロボットを集中管理・スケジュール配信するためのOrchestratorサーバー（年額250万円）を使用しているか設定します。"
    )
    
    st.markdown("---")
    
    st.markdown("### 🤖 ② 移行対象ロボットボリューム")
    st.caption("移行予定の業務シナリオ（ロボット）のボリュームを設定します。")
    
    high_complexity = st.number_input(
        "高難易度ロボットの数",
        min_value=0,
        max_value=100,
        value=1,
        step=1,
        help="複雑なシステム連携や多くの分岐、エラーリカバリを含む高難易度ロボット"
    )
    
    mid_complexity = st.number_input(
        "中難易度ロボットの数",
        min_value=0,
        max_value=100,
        value=2,
        step=1,
        help="一般的な社内システムやExcel操作を行う標準的な難易度のロボット"
    )
    
    low_complexity = st.number_input(
        "低難易度ロボットの数",
        min_value=0,
        max_value=100,
        value=3,
        step=1,
        help="単純なデータ転記や単一アプリのみを操作する簡易ロボット"
    )
    
    # ⑤ 全ロボット台数 (Calculated dynamic value)
    total_robots = high_complexity + mid_complexity + low_complexity
    st.markdown(f"**全ロボット（移行対象）台数**: `{total_robots}` 台")
    
    st.markdown("---")
    st.caption("※ 金額単価はデモ用の概算値です。実際のライセンス見積もりは、要件定義結果やボリュームディスカウントによって変動します。")

# --- State Machine to Prevent Auto-Reactive Update ---
if "diagnosed" not in st.session_state:
    st.session_state.diagnosed = False
if "prev_inputs" not in st.session_state:
    st.session_state.prev_inputs = None

# Bundle current input variables to check if anything changed
current_inputs = {
    "devs": devs,
    "attended": attended,
    "unattended": unattended,
    "has_orchestrator": has_orchestrator,
    "high_complexity": high_complexity,
    "mid_complexity": mid_complexity,
    "low_complexity": low_complexity
}

# If user changed any value in the sidebar, reset the diagnosis state
if st.session_state.prev_inputs is not None:
    changed = False
    for k, v in current_inputs.items():
        if st.session_state.prev_inputs.get(k) != v:
            changed = True
            break
    if changed:
        st.session_state.diagnosed = False
        st.session_state.prev_inputs = None

# --- License Cost Calculation Logic ---
# Unit Prices (in 万 Yen)
# UiPath
UIPATH_DEV = 40.0
UIPATH_ATTENDED = 15.0
UIPATH_UNATTENDED = 100.0
UIPATH_ORCHESTRATOR = 250.0 if has_orchestrator else 0.0

# Power Automate (Premium for devs/attended, Process for unattended)
PA_DEV = 2.4
PA_ATTENDED = 2.4
PA_UNATTENDED = 18.0

# Calculate Totals (Annual License)
uipath_annual_dev = devs * UIPATH_DEV
uipath_annual_attended = attended * UIPATH_ATTENDED
uipath_annual_unattended = unattended * UIPATH_UNATTENDED
uipath_annual_orchestrator = UIPATH_ORCHESTRATOR
uipath_annual = uipath_annual_dev + uipath_annual_attended + uipath_annual_unattended + uipath_annual_orchestrator

pa_annual_dev = devs * PA_DEV
extra_attended = max(0, attended - devs)
pa_annual_attended = extra_attended * PA_ATTENDED
pa_annual_unattended = unattended * PA_UNATTENDED
pa_annual = pa_annual_dev + pa_annual_attended + pa_annual_unattended

# 3-Year License Costs
uipath_total_3years = uipath_annual * 3
pa_total_3years = pa_annual * 3

# Calculate savings (3-Year difference)
diff_3years = abs(uipath_total_3years - pa_total_3years)
diff_3years_yen = diff_3years * 10000
diff_annual = abs(uipath_annual - pa_annual)

# --- UI Render Logic based on diagnosis state ---

if not st.session_state.diagnosed:
    # --- State A: Waiting for Diagnosis Button Click ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("💡 **使い方**: 左側のサイドバーで「UiPath稼働規模」および「移行対象ロボット数」を設定し、以下の「診断を実行」ボタンをクリックしてください。")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        # Styled primary button to trigger diagnosis
        diagnose_button = st.button(
            "🔍 RPAライセンス料金を診断する", 
            use_container_width=True, 
            type="primary"
        )
        
    if diagnose_button:
        # Interactive Loading Animation
        with st.spinner("🔮 RPA診断君が最適なライセンス構成を分析中..."):
            time.sleep(1.2) # 1.2 second think simulation
        
        # Change state and save inputs to freeze results
        st.session_state.diagnosed = True
        st.session_state.prev_inputs = current_inputs
        st.rerun()

else:
    # --- State B: Display Diagnosis Results ---
    st.caption("ℹ️ サイドバーの数値を変更すると、結果がリセットされます。")
    
    # 2-Column layout for 3-Year License Costs
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-weight: 600; color: #475569; font-size: 1.1rem;">UiPath 3年ライセンス費用合計</div>
            <div class="metric-val">{uipath_total_3years:,.1f} 万円</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-weight: 600; color: #475569; font-size: 1.1rem;">Power Automate 3年ライセンス費用合計</div>
            <div class="metric-val">{pa_total_3years:,.1f} 万円</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Display Savings Summary (Red highlights if > 500,000 Yen) ---
    font_color = "#EF4444" if diff_3years_yen > 500000 else "#4F46E5"
    bg_color = "#FEF2F2" if diff_3years_yen > 500000 else "#F8FAFC"
    border_color = "#FCA5A5" if diff_3years_yen > 500000 else "#E2E8F0"

    st.markdown(f"""
    <div style="background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 16px; padding: 1.8rem; text-align: center; margin-bottom: 2rem; box-shadow: 0 4px 10px rgba(0,0,0,0.04);">
        <span style="font-size: 1.1rem; font-weight: 700; color: #475569; letter-spacing: 0.05em;">💡 PAD移行によるライセンス削減効果</span>
        <div style="font-size: 2.4rem; font-weight: 850; color: {font_color}; margin: 0.6rem 0; font-family: 'Outfit', sans-serif;">
            3年間で {diff_3years_yen:,.0f}円 節約できます。
        </div>
        <span style="font-size: 1.1rem; font-weight: 600; color: #64748B;">（年間ライセンス費用において {diff_annual:.1f}万円 のランニング削減効果）</span>
    </div>
    """, unsafe_allow_html=True)

    # Create 2 Columns for Graph and Detailed Table
    graph_col, table_col = st.columns([3, 2])

    with graph_col:
        st.markdown("### 📊 3年間のライセンス費用比較（内訳別・積み上げ）")
        
        # Prepare Data for stacked bar chart based on 3-Year total License costs
        chart_data = pd.DataFrame([
            # UiPath
            {"製品名": "UiPath", "内訳": "A: 開発ライセンス(3年分)", "金額(万円)": uipath_annual_dev * 3},
            {"製品名": "UiPath", "内訳": "B: 有人ロボット(3年分)", "金額(万円)": uipath_annual_attended * 3},
            {"製品名": "UiPath", "内訳": "C: 無人ロボット(3年分)", "金額(万円)": uipath_annual_unattended * 3},
            {"製品名": "UiPath", "内訳": "D: Orchestrator(3年分)", "金額(万円)": uipath_annual_orchestrator * 3},
            
            # Power Automate
            {"製品名": "Power Automate", "内訳": "A: 開発ライセンス(3年分)", "金額(万円)": pa_annual_dev * 3},
            {"製品名": "Power Automate", "内訳": "B: 有人ロボット(3年分)", "金額(万円)": pa_annual_attended * 3},
            {"製品名": "Power Automate", "内訳": "C: 無人ロボット(3年分)", "金額(万円)": pa_annual_unattended * 3},
        ])
        
        # Altair chart definition
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('製品名:N', axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y('金額(万円):Q', title='3年間ライセンス合計 (万円)'),
            color=alt.Color('内訳:N', scale=alt.Scale(scheme='purples'), title="コスト内訳"),
            tooltip=['製品名', '内訳', '金額(万円)']
        ).properties(height=350)
        
        st.altair_chart(chart, use_container_width=True)

    with table_col:
        st.markdown("### 📋 ライセンスコスト明細 (万円)")
        
        detail_df = pd.DataFrame({
            "内訳項目": [
                "開発ライセンス (年間単価)",
                "有人ロボット (年間単価)",
                "無人ロボット (年間単価)",
                "Orchestrator (年間単価)",
                "3年ライセンス費用合計"
            ],
            "UiPath": [
                f"{uipath_annual_dev:,.1f} /年",
                f"{uipath_annual_attended:,.1f} /年",
                f"{uipath_annual_unattended:,.1f} /年",
                f"{uipath_annual_orchestrator:,.1f} /年",
                f"{uipath_total_3years:,.1f} 万円"
            ],
            "Power Automate": [
                f"{pa_annual_dev:,.1f} /年",
                f"{pa_annual_attended:,.1f} /年",
                f"{pa_annual_unattended:,.1f} /年",
                "-",
                f"{pa_total_3years:,.1f} 万円"
            ]
        })
        
        st.dataframe(
            detail_df,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # --- Recommendation Section (Consulting lead-in) ---
    st.markdown("### 🤖 RPA診断君の選定・推奨診断")

    col_rec1, col_rec2 = st.columns([1, 2])

    with col_rec1:
        st.markdown(f"""
        <div style="background-color: #8B5CF6; color: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 10px rgba(139, 92, 246, 0.2);">
            <span style="font-size: 0.9rem; font-weight: 500; text-transform: uppercase;">推奨アクション</span>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 1.6rem; font-weight: 700; color: white;">Power Automate (PAD) へのライセンス移行</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("✅ **年間ライセンス費の大幅削減ポテンシャル**")
        st.markdown("✅ **OS親和性による開発効率の向上**")
        st.markdown("✅ **Office365クラウド環境との即時連携**")

    with col_rec2:
        st.markdown("#### ⚠️ 移行性シミュレーションと専門家チェックの必要性")
        
        st.write(f"""
        現在稼働中のUiPathから **Power Automate (PAD) への移行** により、3年間で合計 **{diff_3years_yen:,.0f}円** （年間 {diff_annual:.1f}万円）ものライセンスコストを削減できる極めて高い経済効果が見込めます。
        
        しかし、UiPathのロボットプログラムは、単純にコピーするだけではPower Automateで正常動作しません。今回入力された要件においては、以下の**移行障壁（技術的課題）**が存在するため、安定した移行を実現するには**専門家による移行性診断（ソースコード解析）**が不可欠です。
        """)
        
        # Display warnings based on user inputs
        if has_orchestrator:
            st.warning("⚡ **Orchestrator（管理サーバー）の移行壁**\n\n現在Orchestratorでスケジュール配信やアセット（ID/Pass）管理を行っている場合、PAD単体では代替できません。Power AutomateクラウドフローやDataverse等を用いた、管理構造自体の再設計が必要です。")
        
        if high_complexity > 0 or mid_complexity > 0:
            st.warning(f"⚡ **ロボット難易度（高: {high_complexity}台、中: {mid_complexity}台）の移行壁**\n\n複雑な例外処理ロジックやUiPathの独自アクティビティは、PADへの単純置換が困難です。移行後にロボットがフリーズするなどの不具合を防ぐため、事前に専門アーキテクトによる『移行性診断（コードリファクタリング計画）』を推奨します。")
            
        st.info("💡 **アドバイス**: 削減される莫大なライセンスコストの一部を移行初期コストに充てることで、リスクを最小限に抑えた安全な移行プロジェクトを立ち上げることが可能です。")

    # --- Call To Action (Free Paper Download Form) ---
    st.markdown("<div class='cta-card'>", unsafe_allow_html=True)

    # Application Form
    if "download_ready" not in st.session_state:
        st.session_state.download_ready = False

    if not st.session_state.download_ready:
        st.markdown("<div class='cta-title'>📩 無料の『UiPath ➔ PAD 移行成功ガイドブック（フリーペーパー）』をダウンロード</div>", unsafe_allow_html=True)
        st.markdown("<div class='cta-subtitle'>UiPathからPower Automateへ安全に移行するためのステップや、失敗しやすいポイント、ライセンスコスト削減効果の実例をまとめた特別フリーペーパーをお届けします。</div>", unsafe_allow_html=True)
        
        with st.form("download_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                company_name = st.text_input("貴社名", placeholder="例：株式会社デモソリューションズ")
                contact_name = st.text_input("ご担当者名", placeholder="例：鈴木 太郎")
            with col_f2:
                email = st.text_input("メールアドレス", placeholder="例：contact@example.com")
                
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                submit_download = st.form_submit_button("📥 フリーペーパーを無料でダウンロードする", use_container_width=True)
                
        if submit_download:
            if not company_name or not contact_name or not email:
                st.error("「貴社名」「ご担当者名」「メールアドレス」は必須入力項目です。")
            else:
                st.session_state.download_ready = True
                st.rerun()
    else:
        # Success State with active download button
        st.balloons()
        st.markdown("<div class='cta-title'>✅ ご登録ありがとうございました！</div>", unsafe_allow_html=True)
        st.markdown("<div class='cta-subtitle'>以下ボタンをクリックして、移行成功ガイドブック（フリーペーパー）を保存してください。</div>", unsafe_allow_html=True)
        
        # Construct Guide content dynamically based on parameters
        guide_content = f"""# UiPath ➔ Power Automate 移行成功ガイドブック
RPA移行推進チーム 特別編集

---

## 📊 今回の試算結果サマリー
- **移行対象ロボット数**: {total_robots}台（高難易度: {high_complexity}台、中難易度: {mid_complexity}台、低難易度: {low_complexity}台）
- **Orchestrator利用**: {'あり' if has_orchestrator else 'なし'}
- **3年間でのライセンス削減効果額**: {diff_3years_yen:,.0f}円

---

## ⚡ 移行時の3大技術障壁と解決策

1. 【Orchestratorの移行壁】
   - スケジュール・トリガー・認証情報の管理をPower Automateクラウドフローへ移植するための再設計ガイド。
2. 【高難易度ロボットの移行壁】
   - UiPath独自のアクティビティをPADのネイティブアクションに効率的・安全にリファクタリングする移行パターン。
3. 【安定性テストの重要性】
   - セレクタ認識ズレを解消し、本番環境でエラーなく稼働させるためのステップテスト設計。

---
💡 個別の技術的相談・本格的な移行診断も無料で承っております。お気軽に contact@example.com までお問い合わせください。
"""
        
        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
        with col_d2:
            st.download_button(
                label="📥 ガイドブックをダウンロードする (PDF/TXT形式)",
                data=guide_content,
                file_name="RPA_Migration_Success_Guide.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # Reset button to allow testing again
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↩️ フォームに戻る", use_container_width=True):
                st.session_state.download_ready = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
