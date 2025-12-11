import streamlit as st
import numpy as np
from PIL import Image
import easyocr
import math

# ---------------------------------------------------------
# 1. データベース（テキストに基づく12色の定義）
# ---------------------------------------------------------
COLOR_DB = {
    "Red": {
        "name": "レッド (R)",
        "meaning": "行動力・情熱・経営感覚",
        "positive": "エネルギーに満ち溢れ、現実を動かす力があります。フットワークが軽く、義理堅いリーダータイプです。",
        "low_msg": "【課題】無気力・現実逃避\n経済的な不安や、地に足がついていない感覚がありませんか？身体を温めましょう。",
        "high_msg": "【注意】怒り・強引\nエネルギーが強すぎて、攻撃的になったりしていませんか？",
        "prescription": "運動、散歩、トイレ掃除"
    },
    "Coral": {
        "name": "コーラルレッド (C)",
        "meaning": "本能・母性・繊細さ",
        "positive": "直感や身体感覚が鋭く、場の空気を肌で感じる力があります。人を育てる母性や優しさを持っています。",
        "low_msg": "【課題】神経過敏・依存\n相手に尽くしすぎていませんか？報われない思いを抱えているかもしれません。",
        "high_msg": "【注意】アレルギー・自家中毒\n過敏になりすぎて、内側に毒を溜め込んでいませんか？",
        "prescription": "岩盤浴、ヨガ、気功"
    },
    "Orange": {
        "name": "オレンジ (O)",
        "meaning": "感情・美意識・食",
        "positive": "五感が鋭く、人生を楽しむ達人です。美味しいものや美しいものに感動する心を持っています。",
        "low_msg": "【課題】感情の抑圧・不感症\nワクワクする気持ちを忘れていませんか？",
        "high_msg": "【注意】感情的・刺激中毒\n買い物や食などの刺激で満たそうとしていませんか？",
        "prescription": "ダンス、温泉、美味しい食事"
    },
    "Gold": {
        "name": "ゴールド (G)",
        "meaning": "信念・カリスマ・中心",
        "positive": "揺るぎない信念と自分軸を持っています。組織の中心人物として、存在感だけで人を惹きつけます。",
        "low_msg": "【課題】不安・自信喪失\n「自分には価値がない」と感じていませんか？",
        "high_msg": "【注意】頑固・傲慢\n自分の考えに固執しすぎていませんか？",
        "prescription": "アファメーション、チャレンジ"
    },
    "Yellow": {
        "name": "イエロー (Y)",
        "meaning": "論理・ユーモア・知識",
        "positive": "頭の回転が速く、知識豊富で教えるのが得意です。独自のユーモアで周囲を明るくします。",
        "low_msg": "【課題】胃痛・思考停止\n考えすぎて胃が痛くなったりしていませんか？",
        "high_msg": "【注意】自己中心的・批判\n理屈っぽくなり、相手をコントロールしようとしていませんか？",
        "prescription": "お笑いを見る、趣味に没頭"
    },
    "Lime": {
        "name": "ライムグリーン (L)",
        "meaning": "女性性リーダー・気配り",
        "positive": "柔らかい物腰で周囲を巻き込む力があります。真の優しさと強さを兼ね備えたリーダーです。",
        "low_msg": "【課題】過小評価・卑下\n自分を小さく見積もっていませんか？",
        "high_msg": "【注意】比較・競争心\n人と自分を比べて落ち込んでいませんか？",
        "prescription": "モーツァルトを聴く、緑の中へ行く"
    },
    "Green": {
        "name": "グリーン (E)",
        "meaning": "協調・平和・傾聴",
        "positive": "聞き上手で、一緒にいるだけで相手を癒やす力があります。調和を大切にするサポーターです。",
        "low_msg": "【課題】拒絶・心の壁\n言いたいことが言えず、心に壁を作っていませんか？",
        "high_msg": "【注意】お節介・八方美人\n相手に合わせすぎて疲れていませんか？",
        "prescription": "呼吸法、森林浴"
    },
    "Aqua": {
        "name": "アクアブルー (A)",
        "meaning": "創造・同調・表現",
        "positive": "芸術的な感性を持ち、言葉にしなくても相手の気持ちを察する共感力があります。",
        "low_msg": "【課題】空気が読めない\n周りの目が気になりすぎていませんか？",
        "high_msg": "【注意】他人軸・同化\n相手の感情を自分のことのように感じすぎていませんか？",
        "prescription": "歌、絵画、塗り絵などの表現"
    },
    "Blue": {
        "name": "ブルー (B)",
        "meaning": "伝達・責任・冷静",
        "positive": "冷静沈着で、物事を完璧にこなす実務能力があります。言葉で伝える力に優れています。",
        "low_msg": "【課題】完璧主義・閉鎖\n「〜せねばならない」と思い込んでいませんか？",
        "high_msg": "【注意】決めつけ・固定観念\n自分の正しさを相手に押し付けていませんか？",
        "prescription": "写経、座禅、文章を書く"
    },
    "Navy": {
        "name": "ネイビーブルー (N)",
        "meaning": "直感・分析・本質",
        "positive": "物事の本質を見抜く洞察力があります。宇宙意識と繋がり、直感的に答えを導き出します。",
        "low_msg": "【課題】批判・孤独\n将来のビジョンが見えず、閉塞感を感じていませんか？",
        "high_msg": "【注意】権威主義・リスク回避\n失敗を恐れすぎて動けなくなっていませんか？",
        "prescription": "瞑想、何かに没頭・集中"
    },
    "Violet": {
        "name": "ヴァイオレット (V)",
        "meaning": "変容・統合・慈悲",
        "positive": "対立するものを統合し、癒やす力があります。スピリチュアルな感性が高く、奉仕の精神を持ちます。",
        "low_msg": "【課題】優柔不断・逃避\n現状から逃げ出したいと思っていませんか？",
        "high_msg": "【注意】選民意識・エゴ\n「自分は特別だ」という意識が強くなりすぎていませんか？",
        "prescription": "神社仏閣、奉仕活動、瞑想"
    },
    "Magenta": {
        "name": "マゼンタピンク (M)",
        "meaning": "無償の愛・博愛",
        "positive": "見返りを求めない大きな愛で、すべてを包み込む力があります。地球規模の視点を持っています。",
        "low_msg": "【課題】愛の枯渇・孤独\n「誰にも愛されていない」と感じていませんか？",
        "high_msg": "【注意】見返り欲求\n「してあげたのに」という気持ちが出ていませんか？",
        "prescription": "募金、ボランティア、感謝"
    }
}

# 12色の並び順リスト（ユーザー指定）
COLOR_ORDER = [
    "Red", "Coral", "Orange", "Gold", "Yellow", "Lime",
    "Green", "Aqua", "Blue", "Navy", "Violet", "Magenta"
]

# ---------------------------------------------------------
# 2. 文字認識ロジック (EasyOCR)
# ---------------------------------------------------------
@st.cache_resource
def load_reader():
    # 英語・数字モードで読み込み（GPUがあれば使う）
    return easyocr.Reader(['en'], gpu=False)

def extract_numbers_from_image(image):
    reader = load_reader()
    img_array = np.array(image)
    
    # OCR実行
    results = reader.readtext(img_array)
    
    numbers = []
    
    # 全テキストの中心座標を計算（円の中心を推定するため）
    all_centers = []
    
    for (bbox, text, prob) in results:
        # "%" を含んでいるか、数字だけのものを抽出
        clean_text = text.replace('%', '').strip()
        if clean_text.isdigit():
            val = int(clean_text)
            
            # バウンディングボックスの中心計算
            (tl, tr, br, bl) = bbox
            center_x = (tl[0] + br[0]) / 2
            center_y = (tl[1] + br[1]) / 2
            
            all_centers.append([center_x, center_y])
            numbers.append({
                "value": val,
                "x": center_x,
                "y": center_y,
                "angle": 0
            })
    
    # グラフの中心を推定（全数字の重心）
    if not all_centers:
        return {}
        
    chart_center = np.mean(all_centers, axis=0)
    
    # 角度を計算 (atan2)
    for num in numbers:
        dx = num["x"] - chart_center[0]
        dy = num["y"] - chart_center[1]
        # Y軸は下向き正なので反転させて計算
        angle = math.atan2(-dy, dx) # -PI to PI
        # 度数法に変換 (0~360)
        deg = math.degrees(angle)
        if deg < 0:
            deg += 360
        num["angle"] = deg
        
    # 角度でソート（反時計回りかどうかは画像の向きによるが、通常角度順で並ぶ）
    # ユーザー指定: Red(左=180度付近?)から反時計回り
    # OCRで取れた順序を角度順に並べる
    numbers.sort(key=lambda x: x["angle"], reverse=False) 
    
    # 検出された数字をリストで返す（最大12個）
    detected_values = [n["value"] for n in numbers]
    
    return detected_values

# ---------------------------------------------------------
# 3. アプリ画面構成
# ---------------------------------------------------------
st.title("🎤 QTV 声解析・診断アプリ (数値入力版)")
st.caption("円グラフの数値を読み取って診断します。画像が読み取れない場合は、手動で数値を入力してください。")

analysis_mode = st.radio(
    "どの波形を診断しますか？",
    ("V1 (顕在意識・外向きの自分)", "V2 (下意識・思考の癖)", "V3 (潜在意識・本質)")
)

target_file = st.file_uploader("グラフ画像をアップロード (自動読み取り)", type=['jpg', 'png', 'jpeg'])

# デフォルト値（全て0）
input_values = {color: 0 for color in COLOR_ORDER}

if target_file is not None:
    image = Image.open(target_file)
    st.image(image, caption='アップロード画像', use_column_width=True)
    
    if st.button("画像から数値を読み取る"):
        with st.spinner('文字を読み取っています...（初回は時間がかかります）'):
            try:
                detected_list = extract_numbers_from_image(image)
                st.success(f"{len(detected_list)}個の数値を検出しました！")
                
                # 検出された数値を順番に割り当て（仮）
                # ※完全な自動割り当ては難しいため、検出順に埋めてユーザーに修正させる
                for i, val in enumerate(detected_list):
                    if i < 12:
                        input_values[COLOR_ORDER[i]] = val
                        
            except Exception as e:
                st.error(f"読み取りエラー: {e}")

# ---------------------------------------------------------
# 入力フォーム（手動修正用）
# ---------------------------------------------------------
st.markdown("### 🔢 数値の確認・修正")
st.info("画像から読み取った数値が以下に入ります。間違っている箇所や空欄を修正してください。")

cols = st.columns(3) # 3列で表示
user_inputs = {}

# 12色の入力欄を作る
for i, color_key in enumerate(COLOR_ORDER):
    color_data = COLOR_DB[color_key]
    with cols[i % 3]:
        # セッションステートを使って値を保持・更新できるようにする
        # デフォルト値はOCRで取れた値、なければ0
        default_val = input_values[color_key]
        val = st.number_input(
            f"{color_data['name']}",
            min_value=0, 
            max_value=100,
            value=default_val,
            key=f"input_{color_key}"
        )
        user_inputs[color_key] = val

# ---------------------------------------------------------
# 診断ボタン
# ---------------------------------------------------------
if st.button("この数値で診断する"):
    # 値の大きい順にソート
    sorted_colors = sorted(user_inputs.items(), key=lambda x: x[1], reverse=True)
    
    st.markdown("---")
    st.markdown("## 📊 診断結果")
    
    # 上位3つを表示
    for rank, (color_key, score) in enumerate(sorted_colors[:3]):
        data = COLOR_DB[color_key]
        
        if rank == 0:
            st.markdown(f"## 👑 1位：{data['name']} ({score}%)")
            st.success(f"**キーワード: {data['meaning']}**")
            st.write(data['positive'])
            
            with st.expander(f"⚠️ {data['name']} の課題と処方箋", expanded=True):
                st.warning(data['low_msg'])
                st.markdown(f"**💊 おすすめアクション: {data['prescription']}**")
        else:
            st.markdown(f"**{rank+1}位：{data['name']} ({score}%)**")
            with st.expander(f"詳細を見る"):
                st.write(f"キーワード: {data['meaning']}")
                st.info(f"処方箋: {data['prescription']}")
    
    # グラフ表示（簡易バー）
    st.markdown("### 全体のバランス")
    for color_key in COLOR_ORDER:
        score = user_inputs[color_key]
        if score > 0:
            st.text(f"{COLOR_DB[color_key]['name']}")
            st.progress(score)

st.markdown("---")
st.caption("監修: クォンタムヴォイスアカデミー 認定インストラクター")
