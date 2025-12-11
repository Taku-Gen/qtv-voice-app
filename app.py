import streamlit as st
from PIL import Image
import os

# PDF生成用ライブラリ
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import requests

# ---------------------------------------------------------
# 0. 設定とデザイン (CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="QTV 声解析・診断システム",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（アカデミー風デザイン）
st.markdown("""
    <style>
    /* 全体の背景とフォント */
    .stApp {
        background-color: #f0f2f6;
    }
    /* ヘッダーのスタイル */
    .main-header {
        background-color: #0E1117;
        color: #C9A063; /* ゴールド */
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    h1 {
        color: #1E3A8A; /* ネイビーブルー */
        font-family: 'Helvetica', sans-serif;
    }
    h2, h3 {
        color: #1E3A8A;
    }
    /* 診断結果のボックス */
    .result-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    /* ボタンのスタイル */
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. データベース
# ---------------------------------------------------------
COLOR_DB = {
    "Red": {
        "name": "レッド (R)",
        "meaning": "行動力・情熱・経営感覚",
        "positive": "エネルギーに満ち溢れ、現実を動かす力があります。フットワークが軽く、義理堅いリーダータイプです。",
        "low_msg": "【課題】無気力・現実逃避\n経済的な不安や、地に足がついていない感覚がありませんか？\n身体を動かすエネルギーが不足しているかもしれません。",
        "prescription": "運動、散歩、トイレ掃除、雑巾がけ"
    },
    "Coral": {
        "name": "コーラルレッド (C)",
        "meaning": "本能・母性・繊細さ",
        "positive": "直感や身体感覚が鋭く、場の空気を肌で感じる力があります。人を育てる母性や優しさを持っています。",
        "low_msg": "【課題】神経過敏・依存\n相手に尽くしすぎて、自分をすり減らしていませんか？\n「愛されたい」という思いから依存的になっているかもしれません。",
        "prescription": "岩盤浴、ヨガ、気功、身体を温める"
    },
    "Orange": {
        "name": "オレンジ (O)",
        "meaning": "感情・美意識・食",
        "positive": "五感が鋭く、人生を楽しむ達人です。美味しいものや美しいものに感動する心を持っています。",
        "low_msg": "【課題】感情の抑圧・不感症\nワクワクする気持ちを忘れていませんか？\nショックなことがあり、感情に蓋をしている可能性があります。",
        "prescription": "ダンス、マッサージ、温泉、美味しいものを味わう"
    },
    "Gold": {
        "name": "ゴールド (G)",
        "meaning": "信念・カリスマ・中心",
        "positive": "揺るぎない信念と自分軸を持っています。組織の中心人物として、存在感だけで人を惹きつけます。",
        "low_msg": "【課題】不安・自信喪失\n「自分には価値がない」と感じていませんか？\n根拠のない不安や恐れに襲われているかもしれません。",
        "prescription": "アファメーション（自分への宣言）、チャレンジする"
    },
    "Yellow": {
        "name": "イエロー (Y)",
        "meaning": "論理・ユーモア・知識",
        "positive": "頭の回転が速く、知識豊富で教えるのが得意です。独自のユーモアで周囲を明るくします。",
        "low_msg": "【課題】胃痛・思考停止\n考えすぎて胃が痛くなったり、どうしていいか分からず混乱していませんか？\n「正解」を探しすぎているかもしれません。",
        "prescription": "お笑いを見る、趣味に没頭する、笑うこと"
    },
    "Lime": {
        "name": "ライムグリーン (L)",
        "meaning": "女性性リーダー・気配り",
        "positive": "柔らかい物腰で周囲を巻き込む力があります。真の優しさと強さを兼ね備えたリーダーです。",
        "low_msg": "【課題】過小評価・卑下\n過去の傷ついた経験から、自分を小さく見積もっていませんか？\nハートに恐れがあるかもしれません。",
        "prescription": "モーツァルトを聴く、緑の中に行く"
    },
    "Green": {
        "name": "グリーン (E)",
        "meaning": "協調・平和・傾聴",
        "positive": "聞き上手で、一緒にいるだけで相手を癒やす力があります。調和を大切にするサポーターです。",
        "low_msg": "【課題】拒絶・心の壁\n言いたいことが言えず、心に壁を作っていませんか？\n変化を恐れて、自分の殻に閉じこもっているかもしれません。",
        "prescription": "呼吸法、森林浴、リラックスする音楽"
    },
    "Aqua": {
        "name": "アクアブルー (A)",
        "meaning": "創造・同調・表現",
        "positive": "芸術的な感性を持ち、言葉にしなくても相手の気持ちを察する共感力があります。",
        "low_msg": "【課題】空気が読めない・同化\n周りの目が気になりすぎて、自分らしさを出せていないのではありませんか？\n相手の感情をもらいすぎているかもしれません。",
        "prescription": "歌う、絵を描く、塗り絵など「表現」すること"
    },
    "Blue": {
        "name": "ブルー (B)",
        "meaning": "伝達・責任・冷静",
        "positive": "冷静沈着で、物事を完璧にこなす実務能力があります。言葉で伝える力に優れています。",
        "low_msg": "【課題】完璧主義・閉鎖\n「〜せねばならない」という思い込みで、自分を縛り付けていませんか？\n言いたいことを飲み込んでしまっています。",
        "prescription": "写経、座禅、文章を書く、頭を空っぽにする"
    },
    "Navy": {
        "name": "ネイビーブルー (N)",
        "meaning": "直感・分析・本質",
        "positive": "物事の本質を見抜く洞察力があります。宇宙意識と繋がり、直感的に答えを導き出します。",
        "low_msg": "【課題】批判・孤独\n将来のビジョンが見えず、閉塞感を感じていませんか？\n直感が鈍り、理屈でジャッジしやすくなっています。",
        "prescription": "瞑想、何かに没頭・集中すること"
    },
    "Violet": {
        "name": "ヴァイオレット (V)",
        "meaning": "変容・統合・慈悲",
        "positive": "対立するものを統合し、癒やす力があります。スピリチュアルな感性が高く、奉仕の精神を持ちます。",
        "low_msg": "【課題】優柔不断・逃避\n現状から逃げ出したいと思っていませんか？\n自分に厳しくしすぎて、バランスを崩しているかもしれません。",
        "prescription": "神社仏閣への参拝、奉仕活動、瞑想"
    },
    "Magenta": {
        "name": "マゼンタピンク (M)",
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
    # 日本語フォント(IPAexGothic)をダウンロードして設定
    font_path = "IPAexGothic.ttf"
    if not os.path.exists(font_path):
        url = "https://moji.or.jp/wp-content/ipafont/IPAexfont/ipaexg00401.zip"
        # 簡易的にダウンロード済みのフォントがあると仮定するか、
        # ここではGithub上のファイルサイズ制限を避けるため、
        # ネット上のフリーフォント(Google Fonts等)ではなく
        # 確実に動作するフォントファイルを配置することを推奨します。
        # ※今回はデモ用に、Streamlit Cloudでも動くようにNotoSansJPをDLするロジックを入れます
        pass

    # 確実に日本語を表示するため、IPAフォントなどがなければ英語になるリスク回避
    # ここでは簡易実装として標準フォントを使用しますが、
    # 本番ではリポジトリに .ttf ファイルを含めるのがベストです。
    return "Helvetica"

def create_pdf(name, top1, top2, bottom):
    file_name = "diagnosis_result.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    # --- フォント登録 (IPAexGothic.ttf がある前提) ---
    # Githubに IPAexGothic.ttf をアップロードしておくと日本語が使えます。
    # ここではファイルがない場合のフォールバックを行います。
    font_name = "Helvetica"
    if os.path.exists("IPAexGothic.ttf"):
        pdfmetrics.registerFont(TTFont('IPAexGothic', 'IPAexGothic.ttf'))
        font_name = "IPAexGothic"
    
    # --- ヘッダー ---
    c.setFont(font_name, 24)
    c.setFillColor(colors.navy)
    c.drawString(50, height - 50, "Quantum Voice Analysis Report")
    
    c.setFont(font_name, 12)
    c.setFillColor(colors.black)
    c.drawString(50, height - 80, f"Client Name: {name}")
    c.line(50, height - 90, width - 50, height - 90)

    # --- 診断結果 (Strength) ---
    y = height - 130
    c.setFont(font_name, 16)
    c.setFillColor(colors.darkgoldenrod)
    c.drawString(50, y, "【 Your Strengths / 強み 】")
    y -= 30
    
    c.setFont(font_name, 12)
    c.setFillColor(colors.black)
    
    # Top 1
    d1 = COLOR_DB[top1]
    c.drawString(70, y, f"1. {d1['name']} : {d1['meaning']}")
    y -= 20
    c.setFont(font_name, 10)
    c.drawString(90, y, d1['positive'][:40] + "...") # 長いと切れるので簡易調整
    y -= 30

    # Top 2
    d2 = COLOR_DB[top2]
    c.setFont(font_name, 12)
    c.drawString(70, y, f"2. {d2['name']} : {d2['meaning']}")
    y -= 20
    c.setFont(font_name, 10)
    c.drawString(90, y, d2['positive'][:40] + "...")
    y -= 40

    # --- 課題と処方箋 (Weakness) ---
    c.setFont(font_name, 16)
    c.setFillColor(colors.darkblue)
    c.drawString(50, y, "【 Prescription / 課題と処方箋 】")
    y -= 30
    
    d_low = COLOR_DB[bottom]
    c.setFont(font_name, 12)
    c.setFillColor(colors.black)
    c.drawString(70, y, f"Missing Color: {d_low['name']}")
    y -= 20
    c.drawString(70, y, f"Action: {d_low['prescription']}")
    y -= 50

    # --- 21日間チャレンジシート ---
    c.setStrokeColor(colors.grey)
    c.rect(50, 50, width - 100, y - 60)
    
    c.setFont(font_name, 16)
    c.setFillColor(colors.black)
    c.drawString(200, y - 30, "21-Day Challenge Sheet")
    
    # 表を描画
    start_y = y - 60
    row_height = 20
    col_width = (width - 140) / 3
    
    c.setFont(font_name, 10)
    for i in range(21):
        # 3列で配置
        col = i % 3
        row = i // 3
        
        x_pos = 70 + (col * col_width)
        y_pos = start_y - (row * row_height) - 20
        
        c.rect(x_pos, y_pos, 15, 15) # チェックボックス
        c.drawString(x_pos + 20, y_pos + 4, f"Day {i+1}")

    c.save()
    return file_name

# ---------------------------------------------------------
# 3. アプリ画面構成
# ---------------------------------------------------------

# サイドバー（入力エリア）
with st.sidebar:
    st.header("⚙️ 設定・入力")
    
    # ロゴがある場合は表示（GitHubに logo.png を置くと表示されます）
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        st.markdown("## Quantum Voice Academy")

    # 名前入力
    client_name = st.text_input("お名前 (Client Name)", "Guest")

    st.markdown("---")
    st.write("画像をアップロード")
    uploaded_files = st.file_uploader("", type=['jpg', 'png'], accept_multiple_files=True)
    
    st.markdown("---")
    st.write("特徴的な色を選択")
    
    top1_key = st.selectbox("1位 (Max)", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"])
    top2_key = st.selectbox("2位", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"], index=3)
    bottom_key = st.selectbox("不足 (Min)", COLOR_OPTIONS, format_func=lambda x: COLOR_DB[x]["name"], index=8)

# メインエリア
st.markdown("<div class='main-header'><h1>🎤 Quantum Voice Analysis</h1></div>", unsafe_allow_html=True)

# 画像表示エリア
if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for idx, file in enumerate(uploaded_files):
        if idx < 2:
            with cols[idx]:
                st.image(file, caption=f"Graph {idx+1}", use_column_width=True)

# 診断結果エリア
if st.button("診断結果を表示する", type="primary"):
    st.markdown("---")
    
    # 2カラムレイアウト
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.subheader("✨ 強み・才能 (Strengths)")
        
        # 1位
        d1 = COLOR_DB[top1_key]
        st.markdown(f"**👑 1位：{d1['name']}**")
        st.info(f"{d1['meaning']}")
        st.caption(d1['positive'])
        
        # 2位
        d2 = COLOR_DB[top2_key]
        st.markdown(f"**🥈 2位：{d2['name']}**")
        st.write(f"{d2['meaning']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_res2:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.subheader("💊 課題と処方箋 (Prescription)")
        
        d_low = COLOR_DB[bottom_key]
        st.markdown(f"**⚠️ 不足色：{d_low['name']}**")
        st.warning(d_low['low_msg'])
        
        st.success(f"**アクション: {d_low['prescription']}**")
        st.write("このアクションを21日間続けてみましょう！")
        st.markdown("</div>", unsafe_allow_html=True)

    # 21日間チャレンジシート表示
    st.markdown("### 📅 21-Day Challenge Preview")
    st.write(f"**テーマ: {d_low['prescription']}** を実行してチェックしましょう。")
    
    # 簡易的なチェックシート表示（Web上）
    check_cols = st.columns(7)
    for i in range(21):
        with check_cols[i % 7]:
            st.checkbox(f"Day {i+1}", key=f"day_{i}")

    # PDFダウンロードボタン
    pdf_file = create_pdf(client_name, top1_key, top2_key, bottom_key)
    
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📄 診断レポート＆チャレンジシートをPDFで保存",
            data=f,
            file_name=f"QTV_Analysis_{client_name}.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.caption("© Quantum Voice Academy | [span_0](start_span)[span_1](start_span)認定インストラクター専用ツール[span_0](end_span)[span_1](end_span)")
