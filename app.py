import streamlit as st
from PIL import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# ---------------------------------------------------------
# 0. 設定とデザイン (CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="QTV 声解析・診断システム",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カラーコード定義 (表示用)
HEX_COLORS = {
    "Red": "#FF0000", "Coral": "#FF7F50", "Orange": "#FFA500", 
    "Gold": "#FFD700", "Yellow": "#FFFF00", "Lime": "#BFFF00",
    "Green": "#008000", "Aqua": "#00FFFF", "Blue": "#0000FF", 
    "Navy": "#000080", "Violet": "#800080", "Magenta": "#FF00FF"
}

# カスタムCSS
st.markdown("""
    <style>
    /* アプリ全体の背景 */
    .stApp { background-color: #FAFAFA; }
    
    /* ヘッダーデザイン */
    .header-box {
        background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .header-title { font-size: 24px; font-weight: bold; letter-spacing: 2px; }
    
    /* カードデザイン */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
        border-left: 5px solid #1E3A8A;
    }
    
    /* 色表示用のバッジ */
    .color-badge {
        display: inline-block;
        width: 100%;
        height: 12px;
        border-radius: 6px;
        margin-top: 5px;
        margin-bottom: 10px;
    }
    
    /* 強調テキスト */
    .highlight { color: #1E3A8A; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. データベース
# ---------------------------------------------------------
COLOR_DB = {
    "Red": {
        "name": "レッド (R)", "hex": HEX_COLORS["Red"],
        "meaning": "行動力・情熱・経営感覚",
        "positive": "エネルギーに満ち溢れ、現実を動かす力があります。フットワークが軽く、義理堅いリーダータイプです。",
        "low_msg": "【課題】無気力・現実逃避\n経済的な不安や、地に足がついていない感覚がありませんか？\n身体を動かすエネルギーが不足しているかもしれません。",
        "prescription": "運動、散歩、トイレ掃除、雑巾がけ"
    },
    "Coral": {
        "name": "コーラル (C)", "hex": HEX_COLORS["Coral"],
        "meaning": "本能・母性・繊細さ",
        "positive": "直感や身体感覚が鋭く、場の空気を肌で感じる力があります。人を育てる母性や優しさを持っています。",
        "low_msg": "【課題】神経過敏・依存\n相手に尽くしすぎて、自分をすり減らしていませんか？\n「愛されたい」という思いから依存的になっているかもしれません。",
        "prescription": "岩盤浴、ヨガ、気功、身体を温める"
    },
    "Orange": {
        "name": "オレンジ (O)", "hex": HEX_COLORS["Orange"],
        "meaning": "感情・美意識・食",
        "positive": "五感が鋭く、人生を楽しむ達人です。美味しいものや美しいものに感動する心を持っています。",
        "low_msg": "【課題】感情の抑圧・不感症\nワクワクする気持ちを忘れていませんか？\nショックなことがあり、感情に蓋をしている可能性があります。",
        "prescription": "ダンス、マッサージ、温泉、美味しいものを味わう"
    },
    "Gold": {
        "name": "ゴールド (G)", "hex": HEX_COLORS["Gold"],
        "meaning": "信念・カリスマ・中心",
        "positive": "揺るぎない信念と自分軸を持っています。組織の中心人物として、存在感だけで人を惹きつけます。",
        "low_msg": "【課題】不安・自信喪失\n「自分には価値がない」と感じていませんか？\n根拠のない不安や恐れに襲われているかもしれません。",
        "prescription": "アファメーション（自分への宣言）、チャレンジする"
    },
    "Yellow": {
        "name": "イエロー (Y)", "hex": HEX_COLORS["Yellow"],
        "meaning": "論理・ユーモア・知識",
        "positive": "頭の回転が速く、知識豊富で教えるのが得意です。独自のユーモアで周囲を明るくします。",
        "low_msg": "【課題】胃痛・思考停止\n考えすぎて胃が痛くなったり、どうしていいか分からず混乱していませんか？\n「正解」を探しすぎているかもしれません。",
        "prescription": "お笑いを見る、趣味に没頭する、笑うこと"
    },
    "Lime": {
        "name": "ライム (L)", "hex": HEX_COLORS["Lime"],
        "meaning": "女性性リーダー・気配り",
        "positive": "柔らかい物腰で周囲を巻き込む力があります。真の優しさと強さを兼ね備えたリーダーです。",
        "low_msg": "【課題】過小評価・卑下\n過去の傷ついた経験から、自分を小さく見積もっていませんか？\nハートに恐れがあるかもしれません。",
        "prescription": "モーツァルトを聴く、緑の中に行く"
    },
    "Green": {
        "name": "グリーン (E)", "hex": HEX_COLORS["Green"],
        "meaning": "協調・平和・傾聴",
        "positive": "聞き上手で、一緒にいるだけで相手を癒やす力があります。調和を大切にするサポーターです。",
        "low_msg": "【課題】拒絶・心の壁\n言いたいことが言えず、心に壁を作っていませんか？\n変化を恐れて、自分の殻に閉じこもっているかもしれません。",
        "prescription": "呼吸法、森林浴、リラックスする音楽"
    },
    "Aqua": {
        "name": "アクア (A)", "hex": HEX_COLORS["Aqua"],
        "meaning": "創造・同調・表現",
        "positive": "芸術的な感性を持ち、言葉にしなくても相手の気持ちを察する共感力があります。",
        "low_msg": "【課題】空気が読めない・同化\n周りの目が気になりすぎて、自分らしさを出せていないのではありませんか？\n相手の感情をもらいすぎているかもしれません。",
        "prescription": "歌う、絵を描く、塗り絵など「表現」すること"
    },
    "Blue": {
        "name": "ブルー (B)", "hex": HEX_COLORS["Blue"],
        "meaning": "伝達・責任・冷静",
        "positive": "冷静沈着で、物事を完璧にこなす実務能力があります。言葉で伝える力に優れています。",
        "low_msg": "【課題】完璧主義・閉鎖\n「〜せねばならない」という思い込みで、自分を縛り付けていませんか？\n言いたいことを飲み込んでしまっています。",
        "prescription": "写経、座禅、文章を書く、頭を空っぽにする"
    },
    "Navy": {
        "name": "ネイビー (N)", "hex": HEX_COLORS["Navy"],
        "meaning": "直感・分析・本質",
        "positive": "物事の本質を見抜く洞察力があります。宇宙意識と繋がり、直感的に答えを導き出します。",
        "low_msg": "【課題】批判・孤独\n将来のビジョンが見えず、閉塞感を感じていませんか？\n直感が鈍り、理屈でジャッジしやすくなっています。",
        "prescription": "瞑想、何かに没頭・集中すること"
    },
    "Violet": {
        "name": "ヴァイオレット (V)", "hex": HEX_COLORS["Violet"],
        "meaning": "変容・統合・慈悲",
        "positive": "対立するものを統合し、癒やす力があります。スピリチュアルな感性が高く、奉仕の精神を持ちます。",
        "low_msg": "【課題】優柔不断・逃避\n現状から逃げ出したいと思っていませんか？\n自分に厳しくしすぎて、バランスを崩しているかもしれません。",
        "prescription": "神社仏閣への参拝、奉仕活動、瞑想"
    },
    "Magenta": {
        "name": "マゼンタ (M)", "hex": HEX_COLORS["Magenta"],
        "meaning": "無償の愛・博愛",
        "positive": "見返りを求めない大きな愛で、すべてを包み込む力があります。地球規模の視点を持っています。",
        "low_msg": "【課題】愛の枯渇・孤独\n「誰にも愛されていない」「認められていない」という孤独感を感じていませんか？\n自己否定の気持ちが強くなっています。",
        "prescription": "募金、ボランティア、感謝を伝える"
    }
}
COLOR_OPTIONS = list(COLOR_DB.keys())

# ---------------------------------------------------------
# 2. PDF生成機能
# ---------------------------------------------------------
@st.cache_resource
def setup_font():
    # 日本語フォントがなければHelvetica(英語)を使用
    return "Helvetica"

def create_pdf(name, top1, top2, bottom):
    file_name = f"QTV_{name}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4
    
    # フォント設定（IPAexGothicがあれば使用）
    font_name = "Helvetica"
    if os.path.exists("IPAexGothic.ttf"):
        pdfmetrics.registerFont(TTFont('IPAexGothic', 'IPAexGothic.ttf'))
        font_name = "IPAexGothic"
    
    # ヘッダー
    c.setFillColorRGB(0.05, 0.1, 0.3) # Navy
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 24)
    c.drawCentredString(width/2, height-60, "Quantum Voice Analysis Report")
    
    c.setFillColor(colors.black)
    c.setFont(font_name, 12)
    c.drawString(50, height-130, f"Name: {name}")
    c.line(50, height-140, width-50, height-140)

    # 強み
    y = height - 180
    c.setFont(font_name, 16)
    c.setFillColorRGB(0.8, 0.6, 0.2) # Gold
    c.drawString(50, y, "【 Strengths / 強み・才能 】")
    y -= 30
    
    c.setFillColor(colors.black)
    d1 = COLOR_DB[top1]
    d2 = COLOR_DB[top2]
    
    c.setFont(font_name, 14)
    c.drawString(60, y, f"1. {d1['name']}")
    c.setFont(font_name, 10)
    c.drawString(80, y-15, d1['meaning'])
    y -= 50
    
    c.setFont(font_name, 14)
    c.drawString(60, y, f"2. {d2['name']}")
    c.setFont(font_name, 10)
    c.drawString(80, y-15, d2['meaning'])
    y -= 60

    # 課題と処方箋
    c.setFont(font_name, 16)
    c.setFillColorRGB(0.05, 0.1, 0.3) # Navy
    c.drawString(50, y, "【 Prescription / 処方箋 】")
    y -= 30
    
    d_low = COLOR_DB[bottom]
    c.setFillColor(colors.black)
    c.setFont(font_name, 14)
    c.drawString(60, y, f"Missing: {d_low['name']}")
    c.setFont(font_name, 12)
    c.drawString(60, y-20, f"Action: {d_low['prescription']}")
    y -= 70

    # 21日間シート
    c.setStrokeColor(colors.grey)
    c.rect(50, 50, width-100, y-60)
    c.setFont(font_name, 14)
    c.drawString(width/2 - 80, y-30, "21-Day Challenge Sheet")
    
    # 簡易グリッド
    start_y = y - 60
    box_w = (width-140)/3
    box_h = 25
    
    c.setFont(font_name, 10)
    for i in range(21):
        col = i % 3
        row = i // 3
        x = 70 + col * box_w
        cur_y = start_y - row * box_h - 20
        c.rect(x, cur_y, 10, 10)
        c.drawString(x+15, cur_y+2, f"Day {i+1}")

    c.save()
    return file_name

# ---------------------------------------------------------
# 3. アプリ画面構成 (UI/UX)
# ---------------------------------------------------------

# サイドバー: 入力エリア
with st.sidebar:
    st.image("https://placehold.co/200x80/0e1117/c9a063?text=QTV+Academy", use_column_width=True)
    st.markdown("### ⚙️ 診断設定")
    
    client_name = st.text_input("お名前", "Guest")
    
    st.markdown("---")
    st.markdown("**1. 画像の参照**")
    uploaded_files = st.file_uploader("グラフ画像をアップロード", type=['jpg', 'png'], accept_multiple_files=True)
    
    st.markdown("---")
    st.markdown("**2. データの入力**")
    
    analysis_mode = st.radio("波形の種類", ("V1:顕在意識", "V2:下意識", "V3:潜在意識"))
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.caption("🟥 上位")
        top1 = st.selectbox("1位", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"])
        top2 = st.selectbox("2位", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"], index=3)
    with col_s2:
        st.caption("🟦 下位")
        bottom = st.selectbox("不足", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"], index=8)

# メインエリア
st.markdown("""
<div class="header-box">
    <div class="header-title">QTV QUANTUM VOICE ANALYSIS</div>
    <div>声解析・診断システム</div>
</div>
""", unsafe_allow_html=True)

# 画像表示 (横並び)
if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        if i < 2:
            cols[i].image(file, caption=f"Graph {i+1}", use_column_width=True)

# タブ機能
tab1, tab2, tab3 = st.tabs(["📊 診断結果", "📄 PDF発行", "ℹ️ 色の解説"])

# --- タブ1: 診断結果 ---
with tab1:
    if st.button("診断する", type="primary"):
        st.markdown("### ✨ あなたの才能と課題")
        
        # 強みエリア
        d1 = COLOR_DB[top1]
        d2 = COLOR_DB[top2]
        
        st.markdown(f"""
        <div class="card">
            <h3 style="color:#C9A063;">👑 1位：{d1['name']}</h3>
            <div class="color-badge" style="background-color:{d1['hex']};"></div>
            <p class="highlight">{d1['meaning']}</p>
            <p>{d1['positive']}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"🥈 2位：{d2['name']} の詳細"):
            st.markdown(f"""
            <div class="color-badge" style="background-color:{d2['hex']};"></div>
            <b>{d2['meaning']}</b><br>{d2['positive']}
            """, unsafe_allow_html=True)

        # 課題エリア
        d_low = COLOR_DB[bottom]
        st.markdown(f"""
        <div class="card" style="border-left: 5px solid {d_low['hex']};">
            <h3 style="color:#1E3A8A;">⚠️ 課題と処方箋 ({d_low['name']})</h3>
            <div class="color-badge" style="background-color:{d_low['hex']}; opacity: 0.3;"></div>
            <p><b>状態:</b> {d_low['low_msg']}</p>
            <hr>
            <p class="highlight">💊 アクション: {d_low['prescription']}</p>
        </div>
        """, unsafe_allow_html=True)

# --- タブ2: PDF発行 ---
with tab2:
    st.markdown("### 📄 診断レポート出力")
    st.write("診断結果と21日間チャレンジシートをまとめたPDFを発行します。")
    
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        st.info(f"対象者: **{client_name} 様**")
        st.write(f"処方箋テーマ: **{COLOR_DB[bottom]['prescription']}**")
    
    with col_p2:
        if st.button("PDFを作成"):
            pdf_path = create_pdf(client_name, top1, top2, bottom)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 ダウンロード",
                    data=f,
                    file_name=f"QTV_{client_name}.pdf",
                    mime="application/pdf"
                )
    
    st.markdown("#### 📅 21-Day Challenge Preview")
    # 簡易チェックシートUI
    cols = st.columns(7)
    for i in range(21):
        cols[i%7].checkbox(f"Day{i+1}", key=f"c_{i}")

# --- タブ3: 解説 ---
with tab3:
    st.markdown("### 🌈 12色の意味リスト")
    for key, val in COLOR_DB.items():
        st.markdown(f"""
        <div style="padding:10px; border-bottom:1px solid #eee; display:flex; align-items:center;">
            <div style="width:20px; height:20px; background-color:{val['hex']}; margin-right:15px; border-radius:50%;"></div>
            <div><b>{val['name']}</b> : {val['meaning']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("© Quantum Voice Academy | 認定インストラクター専用ツール")
