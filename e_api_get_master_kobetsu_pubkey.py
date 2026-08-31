# -*- coding: utf-8 -*-
# Copyright (c) 2021 Tachibana Securities Co., Ltd. All rights reserved.

# 2021.07.09,   yo.
# 2023.04.14 reviced,   yo.
# 2025.07.27 reviced,   yo.
# 2026.08.14 reviced,   yo.
# 2026.08.28 reviced,   yo.
#
# 立花証券ｅ支店ＡＰＩ利用のサンプルコード
#
# 動作確認
# Python 3.13.5 / debian13
# API v4r10
#
# ------------------------------------------------------------------
#
# APIの基本設計について
# 
# 本APIは、プログラミング初心者や非ITエンジニアの方にも
# 利用しやすいよう、URLにJSON形式のパラメーターを付加して
# 送信する独自方式を採用しています。
# 
# 一般的なWeb APIとは異なる構成ですが、
# HTTPヘッダーやPOSTデータなどの知識を最小限に
# 抑えながら利用できることを重視しています。
# 
# このため、本APIは、URLとJSON文字列を組み立てて
# 送信するだけで利用でき、特別な知識を必要とせず、
# 各種スクリプト言語からも実装しやすいことを
# 優先した設計となっています。
#  
# ------------------------------------------------------------------
# 
# 固定IP指定の推奨
# 
# 秘密鍵、第2パスワードファイル、またはログインレスポンスファイルが
# 万が一流出した場合、第三者に不正ログインされるリスクがあります。
# 
# 安全のため、接続元を固定IPに限定する設定（IP制限）を
# 行っての利用を強く推奨いたします。
# 
# ------------------------------------------------------------------
#
# 利用方法: 
# 事前に「e_api_login_pubkey.py」を実行して、仮想URL等を取得しておいてください。
# 実行は「e_api_login_pubkey.py」と同じディレクトリで行ってください。
#
# ファイル構成：
# ~/e_api/                        ← API実行基盤（権限: 700 / 所有者のみアクセス可）
# ├── .auth/                      ← 鍵・暗号化データ格納（権限: 700）
# │   ├── file_pwd2.txt           ← 第2パスワード保存ファイル（手動作成。注文・訂正・取消以外は不要）
# │   └── file_login_response.txt ← ログイン応答出力先（自動生成）
# ├── file_url_info.txt           ← API接続情報ファイル（手動作成）
# ├── e_api_login_pubkey.py
# │
# └── [本実行プログラム]
# 
# 
# ~/e_api/file_url_info.txtの内容例：
# {
#     "sUrl": "https://demo-kabuka.e-shiten.jp/e_api_v4r10/",
#     "sJsonOfmt": "5"
# }
# 
#
# == ご注意: ========================================
#   本番環境にに接続した場合、実際に市場に注文が出ます。
#   市場で約定した場合取り消せません。
# ==================================================
#
# 機能: マスターを個別にダウンロードします。
#
# 必要な設定項目
# 取得するマスター項目:     S_CLMID  対象機能ＩＤ
# 出力ファイル名:   FNAME_OUTPUT  マスターデータの出力ファル名
# 
# ==================================================
# ----------------------
# ・株式銘柄市場マスタ問合取得・・・・・・・・CLMStkGetIssueSizyouMstKabu
# ・オプション銘柄マスタ問合取得・・・・・・・CLMStkGetIssueMstOp
# ・先物銘柄マスタ問合取得・・・・・・・・・・CLMStkGetIssueMstSak
# ・指数銘柄マスタ問合取得・・・・・・・・・・CLMStkGetIssueMstIndex
# ・為替銘柄マスタ問合取得・・・・・・・・・・CLMStkGetIssueMstFx
# ・取引所エラー等理由コード情報問合取得・・・CLMStkGetOrderErrReason
# ・日付情報問合取得・・・・・・・・・・・・・CLMStkGetDateZyouhou
# ・呼値情報問合取得・・・・・・・・・・・・・CLMStkGetYobine
# ・代用掛目情報問合取得・・・・・・・・・・・CLMStkGetDaiyouKakeme
# ・株式銘柄別・市場別規制情報問合取得・・・・CLMStkGetIssueSizyouKiseiKabu
# ・派生銘柄別・市場別規制情報問合取得・・・・CLMStkGetIssueSizyouKiseiHasei
# ・保証金マスタ問合取得・・・・・・・・・・・CLMStkGetHosyoukinMst
# ・ニュース問合取得・・・・・・・・・・・・・CLMMfdsGetNews
# ------------------------------
#

import urllib3
import datetime
import json
import os
import urllib.parse
from zoneinfo import ZoneInfo


# コマンド用パラメーター -------------------    
# 取得するマスター項目の選択（コメント'##'を外して指定。選択は1つのみ。）

# S_CLMID = 'CLMStkGetIssueMstKabu'      #・株式銘柄マスタ問合取得
# S_CLMID = 'CLMStkGetIssueSizyouMstKabu'     # 株式銘柄市場マスタ問合取得
# S_CLMID = 'CLMStkGetIssueMstOp'     # オプション銘柄マスタ問合取得
# S_CLMID = 'CLMStkGetIssueMstSak'     # 先物銘柄マスタ問合取得
# ###S_CLMID = 'CLMStkGetIssueMstIndex'     # 指数銘柄マスタ問合取得
# ###S_CLMID = 'CLMStkGetIssueMstFx'     # 為替銘柄マスタ問合取得
# S_CLMID = 'CLMStkGetOrderErrReason'     # 取引所エラー等理由コード情報問合取得
S_CLMID = 'CLMStkGetDateZyouhou'     # 日付情報問合取得
# S_CLMID = 'CLMStkGetYobine'     # 呼値情報問合取得
# S_CLMID = 'CLMStkGetDaiyouKakeme'     # 代用掛目情報問合取得
# ###S_CLMID = 'CLMStkGetIssueSizyouKiseiKabu'     # 株式銘柄別
# S_CLMID = 'CLMStkGetHosyoukinMst'     # 保証金マスタ問合取得

# 未対応 -----------------------
#### S_CLMID = 'CLMStkGetIssueSizyouKiseiHasei'     # 派生銘柄別
#### S_CLMID = 'CLMMfdsGetNews'     # ニュース問合取得


# 出力ファイル名の設定
# 書き込むファイル名。カレントディレクトリに上書きモードでファイルが作成される。
FNAME_OUTPUT = 'master_' + S_CLMID +'.csv'

# --- 共通設定項目 ------------------------------------------------------------
FNAME_URL_INFO = "file_url_info.txt"                # API接続情報ファイル
FNAME_PASSWD2 = "./.auth/file_pwd2.txt"              # 第二パスワード保存ファイル
FNAME_LOGIN_RESPONSE = "./.auth/file_login_response.txt"  # ログイン応答保存先
FNAME_INFO_P_NO = "file_info_p_no.txt"              # p_no保存ファイル

# --- 通信堅牢化のための設定項目 ---
API_TIMEOUT_SECONDS = 15.0  # タイムアウト時間（秒）: 応答がない場合15秒で切り上げる
MAX_RETRY_COUNT = 3         # 最大リトライ回数: 通信エラー時に自動再試行する回数
RETRY_INTERVAL_SECONDS = 5  # リトライ間隔（秒）: 再試行する前に待機する時間
# --- 以上設定項目 -------------------------------------------------------------------------




# --- 共通ユーティリティ関数 ----------------------------------------------

def func_p_sd_date():
    """
    機能: システム時刻を"p_sd_date"の書式の文字列で返す。
    返値: "p_sd_date"の書式の文字列。 API規定書式 "YYYY.MM.DD-hh:mm:ss.sss"
    引数1: なし
    備考: 
        日本標準時（Japan Standard Time、JST）を利用のこと。
    """
    dt_now = datetime.datetime.now(
        # 日本標準時（Japan Standard Time、JST）を利用
        ZoneInfo("Asia/Tokyo")
    )
    # 年.月.日-時:分:秒 の部分を作成
    str_date = dt_now.strftime("%Y.%m.%d-%H:%M:%S")
    
    # マイクロ秒（6桁ゼロ埋め）から先頭の3桁を切り出してミリ秒を作成
    str_micro = f"{dt_now.microsecond:06d}"
    str_ms = str_micro[0:3]
    
    # ドットで結合してAPI規定書式を完成
    return str_date + "." + str_ms


def func_replace_urlencode(str_input):
    """
    URLエンコードを行う。

    URLでは、スペースや「&」「+」「?」などの記号が
    特別な意味を持つため、そのまま送信できない場合がある。
    そのため、これらの文字を「%xx」形式へ変換する。

    例:
        "A B+C" → "A%20B%2BC"

    本サンプルでは Python標準ライブラリの
    urllib.parse.quote() を利用してURLエンコードを行う。

    他言語へ移植する場合も、自前で変換処理を作成するのではなく、
    各言語が提供する標準のURLエンコード関数を利用することを推奨する。

    主な対応例:
        Python      : urllib.parse.quote()
        Java        : java.net.URLEncoder.encode()
        C#          : Uri.EscapeDataString()
        JavaScript  : encodeURIComponent()
        Go          : url.QueryEscape()

    Parameters
    ----------
    str_input : str
        URLエンコード対象文字列

    Returns
    -------
    str
        URLエンコード後の文字列
    """
    return urllib.parse.quote(str_input, safe='')


def func_read_from_file(str_fname):
    """ファイルから文字情報を一括読み込み（BOMを排除）"""
    str_read = ''
    try:
        # utf-8-sig を指定してBOMを自動的に排除しファイルを開く
        with open(str_fname, 'r', encoding='utf-8-sig') as fin:
            while True:
                line = fin.readline()
                if not line:
                    break
                str_read = str_read + line
        return str_read
    except IOError as e:
        print(f"[エラー] ファイルを読み込めません: {str_fname}")
        raise e


def func_write_to_file(str_fname_output, str_data):
    """ファイルに書き込み、権限を所有者のみ(600)に制限"""
    try:
        # 出力先フォルダの存在を確認し、存在しない場合は自動作成
        str_dir = os.path.dirname(str_fname_output)
        if str_dir and not os.path.exists(str_dir):
            os.makedirs(str_dir, exist_ok=True)

        # データをファイルへ書き込み
        with open(str_fname_output, 'w', encoding='utf-8') as fout:
            fout.write(str_data)
        
        # パーミッションを600（所有者のみ読み書き可能）に制限
        os.chmod(str_fname_output, 0o600)
    except IOError as e:
        print(f"[エラー] ファイルに書き込めません: {str_fname_output}")
        raise e


def func_get_url_info(fname):
    """
    file_url_info.txt からAPI接続設定を取得

    機能: API接続情報をファイルから取得し辞書型で返す
    引数1: 接続先情報を保存したファイル名: fname_url_info

    サポートへの問い合わせは、sJsonOfmt:'5'でお願いします。
    """
    str_url_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    return  json.loads(str_url_info)    


def func_get_login_response(str_fname):
    '''
    ログインレスポンスを取得
    '''
    str_login_response = func_read_from_file(str_fname)
    dic_login_response = json.loads(str_login_response)
    return dic_login_response
    

def func_get_p_no(fname):
    """ 
    機能: p_noをファイルから取得する
    引数1: p_noを保存したファイル名（fname_info_p_no = "e_api_info_p_no.txt"）
    """
    str_p_no_info = func_read_from_file(fname)
    # JSON形式の文字列を辞書型で取り出す
    json_p_no_info = json.loads(str_p_no_info)
    int_p_no = int(json_p_no_info.get('p_no'))
    return int_p_no


def func_save_p_no(str_fname_output, int_p_no):
    """p_noを保存するためのJSONファイルを生成"""
    p_no_dict = {"p_no": str(int_p_no)}
    json_data = json.dumps(p_no_dict, indent=4)
    func_write_to_file(str_fname_output, json_data)
    print(f'現在の "p_no" を保存しました。 p_no = {int_p_no} -> {str_fname_output}')


def func_make_url_request_from_dic(
                                    auth_flg,       # ログインFlag。    login:true   login以外:false
                                    url_target,     # 接続先URL
                                    work_dic_req    # API要求項目
):
    '''
    API問合せ用完全URL（クエリパラメータ付）を作成
    
    ------------------------------------------------------------------

    APIの基本設計について

    本APIは、プログラミング初心者や非ITエンジニアの方にも
    利用しやすいよう、URLにJSON形式のパラメーターを付加して
    送信する独自方式を採用しています。

    一般的なWeb APIとは異なる構成ですが、
    HTTPヘッダーやPOSTデータなどの知識を最小限に
    抑えながら利用できることを重視しています。

    このため、本APIは、URLとJSON文字列を組み立てて
    送信するだけで利用でき、特別な知識を必要とせず、
    各種スクリプト言語からも実装しやすいことを
    優先した設計となっています。
    
    ------------------------------------------------------------------
    JSONをHTTPボディではなくURLに付加して送信します。
    詳細はAPIマニュアル参照。
    備考：
        サポートへの問い合わせを考慮し、項目ごとの改行とタブを入れてあります。
    '''
    str_url = url_target
    if auth_flg:
        str_url = urllib.parse.urljoin(str_url, 'auth/')
    json_param = json.dumps(work_dic_req, indent=4, ensure_ascii=False)
    return f"{str_url}?{json_param}"


def func_api_req(str_request_method, str_url): 
    """
    APIリクエストの送信と、Shift-JIS応答のデコード（リトライ・タイムアウト対応版）
    """
    # HTTP通信ライブラリ urllib3 を利用します。
    #
    # requests ライブラリでも同様の処理は可能ですが、
    # 本サンプルでは APIサーバーへの接続処理が分かりやすいよう、
    # より基本的な urllib3 を利用しています。
    #
    # 他言語へ移植する場合も、
    # 「HTTPクライアント生成 → リクエスト送信 → レスポンス受信」
    # の流れを対応するライブラリへ置き換えてください。

    # 接続および読み込みのタイムアウト時間を設定
    timeout_config = urllib3.Timeout(connect=API_TIMEOUT_SECONDS, read=API_TIMEOUT_SECONDS)
    http = urllib3.PoolManager()
    
    response_data = None
    status_code = None

    # 最大試行回数に達するまで通信をリトライ
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            # 2回目以降の試行（再接続）の前に、指定されたインターバル時間待機
            if attempt > 1:
                print(f"[{attempt}/{MAX_RETRY_COUNT} 回目] 再接続を試みます...（{RETRY_INTERVAL_SECONDS}秒待機）")
                time.sleep(RETRY_INTERVAL_SECONDS)

            req = http.request(str_request_method, str_url, timeout=timeout_config)
            status_code = req.status
            response_data = req.data
            break  # 正常に通信できた場合はループを抜ける

        except (TimeoutError, MaxRetryError) as ce:
            print(f"\n[警告] 通信エラーが発生しました (試行: {attempt}/{MAX_RETRY_COUNT})")
            print(f"エラー詳細: {ce}")
            
            # 最大リトライ回数を超えて失敗した場合はConnectionErrorを発生
            if attempt == MAX_RETRY_COUNT:
                raise ConnectionError(
                    f"APIサーバーへの接続に規定回数失敗しました。サーバーがメンテナンス中か、停止している可能性があります。\n"
                    f"設定されたタイムアウト時間: {API_TIMEOUT_SECONDS}秒"
                )
        except Exception as ex:
            print(f"\n[警告] 予期せぬネットワーク例外が発生しました: {ex}")
            if attempt == MAX_RETRY_COUNT:
                raise ex

    print(f"HTTP Status: {status_code}")

    # 受信した電文をShift-JISからUTF-8へデコード（不正なバイトは無視）
    str_response = response_data.decode("shift-jis", errors="ignore")
    return str_response


def func_print_sendding_url(str_sending_url):
    print('--- 送信電文 -------------------------------------------')
    print(str_sending_url)


def func_print_response(str_output, long_limit):
    print('--- 受信電文 -------------------------------------------')
    print(str_output[:long_limit])
    if len(str_output) < long_limit:
        print('--- 以上 受信電文 --------------------------------------')
    else:
        print('--- ', long_limit, '文字でカット -----------------------')



def func_api_request_from_dic(
                                flg_login,          # ログインFlag。    login:true   login以外:false
                                destination_url,    # 接続先URL。
                                                    #   ログイン時は、FNAME_URL_INFOから取得する接続先。
                                                    #   それ以外はログインレスポンスで指定される仮想URL。
                                dic_req_item        # API要求項目
                            ):
    '''
    APIへの問い合わせを実行する。
    '''
    # URL文字列の作成
    str_url = func_make_url_request_from_dic(
                                                flg_login,          # ログインFlag。    login:true   login以外:false
                                                destination_url,    # 接続先URL
                                                dic_req_item        # API要求項目
    )

    # 送信電文の出力
    func_print_sendding_url(str_url)

    # APIへの問い合わせ。
    # リクエストメソッドの指定('GET'、'POST'どちらでも動作します。)
    str_api_response = func_api_req('POST', str_url)

    # 受信電文の出力（文字数指定: 3,000）
    func_print_response(str_api_response, 3*10**3)

    # apiの返り値（JSON形式の文字列）を辞書型で取り出す
    dic_api_response = json.loads(str_api_response)
    
    return dic_api_response

# --- 共通ユーティリティ関数 ----------------------------------------------






# 機能: 銘柄マスタ_株（CLMStkGetIssueMstKabu）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetIssueMstKabu(str_column_name):
    if str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sIssueName" : str_name_kanji = "銘柄名"
    elif str_column_name == "sIssueNameRyaku" : str_name_kanji = "銘柄名略称"
    elif str_column_name == "sIssueNameKana" : str_name_kanji = "銘柄名（カナ）"
    elif str_column_name == "sIssueNameEizi" : str_name_kanji = "銘柄名（英語表記）"
    elif str_column_name == "sTokuteiF" : str_name_kanji = "特定口座対象Ｃ"
    elif str_column_name == "sHikazeiC" : str_name_kanji = "非課税口座受付可否"
    elif str_column_name == "sZyouzyouHakkouKabusu" : str_name_kanji = "上場発行株数"
    elif str_column_name == "sKenriotiFlag" : str_name_kanji = "権利落ちフラグ"
    elif str_column_name == "sKenritukiSaisyuDay" : str_name_kanji = "権利付最終日"
    elif str_column_name == "sZyouzyouNyusatuC" : str_name_kanji = "上場・入札Ｃ"
    elif str_column_name == "sNyusatuKaizyoDay" : str_name_kanji = "入札解除日"
    elif str_column_name == "sNyusatuDay" : str_name_kanji = "入札日"
    elif str_column_name == "sBaibaiTani" : str_name_kanji = "売買単位"
    elif str_column_name == "sBaibaiTaniYoku" : str_name_kanji = "売買単位(翌営業日)"
    elif str_column_name == "sBaibaiTeisiC" : str_name_kanji = "売買停止Ｃ"
    elif str_column_name == "sHakkouKaisiDay" : str_name_kanji = "発行開始日"
    elif str_column_name == "sHakkouSaisyuDay" : str_name_kanji = "発行最終日"
    elif str_column_name == "sKessanC" : str_name_kanji = "決算Ｃ"
    elif str_column_name == "sKessanDay" : str_name_kanji = "決算日"
    elif str_column_name == "sZyouzyouOutouDay" : str_name_kanji = "上場応答日"
    elif str_column_name == "sNiruiKizituC" : str_name_kanji = "二類期日Ｃ"
    elif str_column_name == "sOogutiKabusu" : str_name_kanji = "大口株数"
    elif str_column_name == "sOogutiKingaku" : str_name_kanji = "大口金額"
    elif str_column_name == "sBadenpyouOutputYNC" : str_name_kanji = "場伝票出力有無Ｃ"
    elif str_column_name == "sHosyoukinDaiyouKakeme" : str_name_kanji = "保証金代用掛目"
    elif str_column_name == "sDaiyouHyoukaTanka" : str_name_kanji = "代用証券評価単価"
    elif str_column_name == "sKikoSankaC" : str_name_kanji = "機構参加Ｃ"
    elif str_column_name == "sKarikessaiC" : str_name_kanji = "仮決済Ｃ"
    elif str_column_name == "sYusenSizyou" : str_name_kanji = "優先市場"
    elif str_column_name == "sMukigenC" : str_name_kanji = "無期限対象Ｃ"
    elif str_column_name == "sGyousyuCode" : str_name_kanji = "業種コード"
    elif str_column_name == "sGyousyuName" : str_name_kanji = "業種コード名"
            # 0050:水産・農林業
            # 1050:鉱業
            # 2050:建設業
            # 3050:食料品
            # 3100:繊維製品
            # 3150:パルプ・紙
            # 3200:化学
            # 3250:医薬品
            # 3300:石油石炭製品
            # 3350:ゴム製品
            # 3400:ｶﾞﾗｽ土石製品
            # 3450:鉄鋼
            # 3500:非鉄金属
            # 3550:金属製品
            # 3600:機械
            # 3650:電気機器
            # 3700:輸送用機器
            # 3750:精密機器
            # 3800:その他製品
            # 4050:電気・ガス業
            # 5050:陸運業
            # 5100:海運業
            # 5150:空運業
            # 5200:倉庫運輸関連
            # 5250:情報・通信業
            # 6050:卸売業
            # 6100:小売業
            # 7050:銀行業
            # 7100:証券商品先物
            # 7150:保険業
            # 7200:その他金融業
            # 8050:不動産業
            # 9050:サービス業
            # 9999:その他
    elif str_column_name == "sSorC" : str_name_kanji = "ＳＯＲ対象銘柄Ｃ"
    elif str_column_name == "sCreateDate" : str_name_kanji = "新規作成日時"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "最終更新日時"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "最終更新通番"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji




# 機能: 銘柄市場マスタ_株（CLMStkGetIssueSizyouMstKabu）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetIssueSizyouMstKabu(str_column_name):
    if str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sZyouzyouSizyou" : str_name_kanji = "上場市場"
    elif str_column_name == "sSystemC" : str_name_kanji = "システムＣ"
    elif str_column_name == "sNehabaMin" : str_name_kanji = "値幅下限"
    elif str_column_name == "sNehabaMax" : str_name_kanji = "値幅上限"
    elif str_column_name == "sIssueKubunC" : str_name_kanji = "銘柄区分Ｃ"
    elif str_column_name == "sNehabaSizyouC" : str_name_kanji = "値幅市場Ｃ"
    elif str_column_name == "sSinyouC" : str_name_kanji = "信用Ｃ"
    elif str_column_name == "sSinkiZyouzyouDay" : str_name_kanji = "新規上場日"
    elif str_column_name == "sNehabaKigenDay" : str_name_kanji = "値幅期限日"
    elif str_column_name == "sNehabaKiseiC" : str_name_kanji = "値幅規制Ｃ"
    elif str_column_name == "sNehabaKiseiTi" : str_name_kanji = "値幅規制値"
    elif str_column_name == "sNehabaCheckKahiC" : str_name_kanji = "値幅チェック可否Ｃ"
    elif str_column_name == "sIssueBubetuC" : str_name_kanji = "銘柄部別Ｃ"
    elif str_column_name == "sZenzituOwarine" : str_name_kanji = "前日終値"
    elif str_column_name == "sNehabaSansyutuSizyouC" : str_name_kanji = "値幅算出市場Ｃ"
    elif str_column_name == "sIssueKisei1C" : str_name_kanji = "銘柄規制１Ｃ"
    elif str_column_name == "sIssueKisei2C" : str_name_kanji = "銘柄規制２Ｃ"
    elif str_column_name == "sZyouzyouKubun" : str_name_kanji = "上場区分"
    elif str_column_name == "sZyouzyouHaisiDay" : str_name_kanji = "上場廃止日"
    elif str_column_name == "sSizyoubetuBaibaiTani" : str_name_kanji = "市場別売買単位"
    elif str_column_name == "sSizyoubetuBaibaiTaniYoku" : str_name_kanji = "市場別売買単位(翌営業日)"
    elif str_column_name == "sYobineTaniNumber" : str_name_kanji = "呼値の単位番号"
    elif str_column_name == "sYobineTaniNumberYoku" : str_name_kanji = "呼値の単位番号(翌営業日)"
    elif str_column_name == "sZyouhouSource" : str_name_kanji = "情報系ソース"
    elif str_column_name == "sZyouhouCode" : str_name_kanji = "情報系コード"
    elif str_column_name == "sKouboPrice" : str_name_kanji = "公募価格"
    elif str_column_name == "sCreateDate" : str_name_kanji = "新規作成日時"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "最終更新日時"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "最終更新通番"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji





# 機能: 先物（CLMStkGetIssueMstSak）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetIssueMstSak(str_column_name):
    if str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sIssueName" : str_name_kanji = "銘柄名"
    elif str_column_name == "sIssueNameEizi" : str_name_kanji = "銘柄名（英語表記）"
    elif str_column_name == "sSakOpSyouhin" : str_name_kanji = "先物OP商品"
    elif str_column_name == "sGensisanKubun" : str_name_kanji = "原資産区分"
    elif str_column_name == "sGensisanCode" : str_name_kanji = "原資産コード"
    elif str_column_name == "sGengetu" : str_name_kanji = "限月"
    elif str_column_name == "sZyouzyouSizyou" : str_name_kanji = "上場市場"
    elif str_column_name == "sTorihikiStartDay" : str_name_kanji = "取引開始日"
    elif str_column_name == "sLastBaibaiDay" : str_name_kanji = "最終売買日"
    elif str_column_name == "sTaniSuryou" : str_name_kanji = "単位数量"
    elif str_column_name == "sYobineTaniNumber" : str_name_kanji = "呼値の単位番号"
    elif str_column_name == "sZyouhouSource" : str_name_kanji = "情報系ソース"
    elif str_column_name == "sZyouhouCode" : str_name_kanji = "情報系コード"
    elif str_column_name == "sNehabaMin" : str_name_kanji = "値幅下限"
    elif str_column_name == "sNehabaMax" : str_name_kanji = "値幅上限"
    elif str_column_name == "sIssueKisei1C" : str_name_kanji = "銘柄規制１Ｃ"
    elif str_column_name == "sBaibaiTeisiC" : str_name_kanji = "売買停止Ｃ"
    elif str_column_name == "sZenzituOwarine" : str_name_kanji = "前日終値"
    elif str_column_name == "sBaDenpyouOutputUmuC" : str_name_kanji = "場伝票出力有無Ｃ"
    elif str_column_name == "sCreateDate" : str_name_kanji = "新規作成日時"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "最終更新日時"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "最終更新通番"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji





# 機能: OP（CLMStkGetIssueMstOp）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetIssueMstOp(str_column_name):
    if str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sIssueName" : str_name_kanji = "銘柄名"
    elif str_column_name == "sIssueNameEizi" : str_name_kanji = "銘柄名（英語表記）"
    elif str_column_name == "sSakOpSyouhin" : str_name_kanji = "先物OP商品"
    elif str_column_name == "sGensisanKubun" : str_name_kanji = "原資産区分"
    elif str_column_name == "sGensisanCode" : str_name_kanji = "原資産コード"
    elif str_column_name == "sGengetu" : str_name_kanji = "限月"
    elif str_column_name == "sZyouzyouSizyou" : str_name_kanji = "上場市場"
    elif str_column_name == "sKousiPrice" : str_name_kanji = "行使価格"
    elif str_column_name == "sPutCall" : str_name_kanji = "プット・コール"
    elif str_column_name == "sTorihikiStartDay" : str_name_kanji = "取引開始日"
    elif str_column_name == "sLastBaibaiDay" : str_name_kanji = "最終売買日"
    elif str_column_name == "sKenrikousiLastDay" : str_name_kanji = "権利行使最終日"
    elif str_column_name == "sTaniSuryou" : str_name_kanji = "単位数量"
    elif str_column_name == "sYobineTaniNumber" : str_name_kanji = "呼値の単位番号"
    elif str_column_name == "sZyouhouSource" : str_name_kanji = "情報系ソース"
    elif str_column_name == "sZyouhouCode" : str_name_kanji = "情報系コード"
    elif str_column_name == "sNehabaMin" : str_name_kanji = "値幅下限"
    elif str_column_name == "sNehabaMax" : str_name_kanji = "値幅上限"
    elif str_column_name == "sIssueKisei1C" : str_name_kanji = "銘柄規制１Ｃ"
    elif str_column_name == "sZenzituOwarine" : str_name_kanji = "前日終値"
    elif str_column_name == "sZenzituRironPrice" : str_name_kanji = "前日理論価格"
    elif str_column_name == "sBaDenpyouOutputUmuC" : str_name_kanji = "場伝票出力有無Ｃ"
    elif str_column_name == "sCreateDate" : str_name_kanji = "新規作成日時"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "最終更新日時"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "最終更新通番"
    elif str_column_name == "sATMFlag" : str_name_kanji = "アット・ザ・マネーF"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji







# 機能: 指数・為替（CLMIssueMstOther）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMIssueMstOther(str_column_name):
    if str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sIssueName" : str_name_kanji = "銘柄名"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji






# 機能: 代用掛目（CLMStkGetDaiyouKakeme）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetDaiyouKakeme(str_column_name):
    if str_column_name == "sSystemKouzaKubun" : str_name_kanji = "システム口座区分"
    elif str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sTekiyouDay" : str_name_kanji = "適用日"
    elif str_column_name == "sHosyokinDaiyoKakeme" : str_name_kanji = "保証金代用掛目"
    elif str_column_name == "sDeleteDay" : str_name_kanji = "削除日"
    elif str_column_name == "sCreateDate" : str_name_kanji = "作成日"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "更新番号"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "更新日"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji






# 機能: 保証金（CLMStkGetHosyoukinMst）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetHosyoukinMst(str_column_name):
    if str_column_name == "sSystemKouzaKubun" : str_name_kanji = "システム口座区分"
    elif str_column_name == "sIssueCode" : str_name_kanji = "銘柄コード"
    elif str_column_name == "sZyouzyouSizyou" : str_name_kanji = "上場市場"
    elif str_column_name == "sHenkouDay" : str_name_kanji = "変更日"
    elif str_column_name == "sDaiyoHosyokinRitu" : str_name_kanji = "代用保証金率"
    elif str_column_name == "sGenkinHosyokinRitu" : str_name_kanji = "現金保証金率"
    elif str_column_name == "sCreateDate" : str_name_kanji = "作成日"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "更新番号"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "更新日"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji




# 機能: 日付情報（CLMStkGetDateZyouhou）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetDateZyouhou(str_column_name):
    if str_column_name == "sDayKey" : str_name_kanji = "日付ＫＥＹ"
    elif str_column_name == "sMaeEigyouDay_1" : str_name_kanji = "１営業日前"
    elif str_column_name == "sMaeEigyouDay_2" : str_name_kanji = "２営業日前"
    elif str_column_name == "sMaeEigyouDay_3" : str_name_kanji = "３営業日前"
    elif str_column_name == "sTheDay" : str_name_kanji = "当日日付"
    elif str_column_name == "sYokuEigyouDay_1" : str_name_kanji = "翌１営業日"
    elif str_column_name == "sYokuEigyouDay_2" : str_name_kanji = "翌２営業日"
    elif str_column_name == "sYokuEigyouDay_3" : str_name_kanji = "翌３営業日"
    elif str_column_name == "sYokuEigyouDay_4" : str_name_kanji = "翌４営業日"
    elif str_column_name == "sYokuEigyouDay_5" : str_name_kanji = "翌５営業日"
    elif str_column_name == "sYokuEigyouDay_6" : str_name_kanji = "翌６営業日"
    elif str_column_name == "sYokuEigyouDay_7" : str_name_kanji = "翌７営業日"
    elif str_column_name == "sYokuEigyouDay_8" : str_name_kanji = "翌８営業日"
    elif str_column_name == "sYokuEigyouDay_9" : str_name_kanji = "翌９営業日"
    elif str_column_name == "sYokuEigyouDay_10" : str_name_kanji = "翌１０営業日"
    elif str_column_name == "sKabuUkewatasiDay" : str_name_kanji = "株式受渡日"
    elif str_column_name == "sKabuKariUkewatasiDay" : str_name_kanji = "株式仮決受渡日"
    elif str_column_name == "sBondUkewatasiDay" : str_name_kanji = "債券受渡日"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji




# 機能: エラー理由（CLMStkGetOrderErrReason）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetOrderErrReason(str_column_name):
    if str_column_name == "sErrReasonCode" : str_name_kanji = "エラーコード"
    elif str_column_name == "sErrReasonText" : str_name_kanji = "エラーメッセージ"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji




# 機能: システムステイタス（CLMSystemStatus）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMSystemStatus(str_column_name):
    if str_column_name == "sSystemStatusKey" : str_name_kanji = "システムステイタスキー"
    elif str_column_name == "sLoginKyokaKubun" : str_name_kanji = "ログイン許可区分"
    elif str_column_name == "sSystemStatus" : str_name_kanji = "システムステイタスキー"
    elif str_column_name == "sCreateTime" : str_name_kanji = "作成日時"
    elif str_column_name == "sUpdateTime" : str_name_kanji = "更新日時"
    elif str_column_name == "sUpdateNumber" : str_name_kanji = "更新番号"
    elif str_column_name == "sDeleteFlag" : str_name_kanji = "削除フラグ"
    elif str_column_name == "sDeleteTime" : str_name_kanji = "削除日時"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji





# 機能: 呼値（CLMStkGetYobine）用 列名を漢字に変換 
# 引数: 列名
# 返値: 漢字名 string型
def func_column_kanji_CLMStkGetYobine(str_column_name):
    if str_column_name == "sYobineTaniNumber" : str_name_kanji = "呼値単位番号"
    elif str_column_name == "sTekiyouDay" : str_name_kanji = "適用日"
    elif str_column_name == "sKizunPrice_1" : str_name_kanji = "基準値段_1"
    elif str_column_name == "sKizunPrice_2" : str_name_kanji = "基準値段_2"
    elif str_column_name == "sKizunPrice_3" : str_name_kanji = "基準値段_3"
    elif str_column_name == "sKizunPrice_4" : str_name_kanji = "基準値段_4"
    elif str_column_name == "sKizunPrice_5" : str_name_kanji = "基準値段_5"
    elif str_column_name == "sKizunPrice_6" : str_name_kanji = "基準値段_6"
    elif str_column_name == "sKizunPrice_7" : str_name_kanji = "基準値段_7"
    elif str_column_name == "sKizunPrice_8" : str_name_kanji = "基準値段_8"
    elif str_column_name == "sKizunPrice_9" : str_name_kanji = "基準値段_9"
    elif str_column_name == "sKizunPrice_10" : str_name_kanji = "基準値段_10"
    elif str_column_name == "sKizunPrice_11" : str_name_kanji = "基準値段_11"
    elif str_column_name == "sKizunPrice_12" : str_name_kanji = "基準値段_12"
    elif str_column_name == "sKizunPrice_13" : str_name_kanji = "基準値段_13"
    elif str_column_name == "sKizunPrice_14" : str_name_kanji = "基準値段_14"
    elif str_column_name == "sKizunPrice_15" : str_name_kanji = "基準値段_15"
    elif str_column_name == "sKizunPrice_16" : str_name_kanji = "基準値段_16"
    elif str_column_name == "sKizunPrice_17" : str_name_kanji = "基準値段_17"
    elif str_column_name == "sKizunPrice_18" : str_name_kanji = "基準値段_18"
    elif str_column_name == "sKizunPrice_19" : str_name_kanji = "基準値段_19"
    elif str_column_name == "sKizunPrice_20" : str_name_kanji = "基準値段_20"
    elif str_column_name == "sYobineTanka_1" : str_name_kanji = "呼値単価_1"
    elif str_column_name == "sYobineTanka_2" : str_name_kanji = "呼値単価_2"
    elif str_column_name == "sYobineTanka_3" : str_name_kanji = "呼値単価_3"
    elif str_column_name == "sYobineTanka_4" : str_name_kanji = "呼値単価_4"
    elif str_column_name == "sYobineTanka_5" : str_name_kanji = "呼値単価_5"
    elif str_column_name == "sYobineTanka_6" : str_name_kanji = "呼値単価_6"
    elif str_column_name == "sYobineTanka_7" : str_name_kanji = "呼値単価_7"
    elif str_column_name == "sYobineTanka_8" : str_name_kanji = "呼値単価_8"
    elif str_column_name == "sYobineTanka_9" : str_name_kanji = "呼値単価_9"
    elif str_column_name == "sYobineTanka_10" : str_name_kanji = "呼値単価_10"
    elif str_column_name == "sYobineTanka_11" : str_name_kanji = "呼値単価_11"
    elif str_column_name == "sYobineTanka_12" : str_name_kanji = "呼値単価_12"
    elif str_column_name == "sYobineTanka_13" : str_name_kanji = "呼値単価_13"
    elif str_column_name == "sYobineTanka_14" : str_name_kanji = "呼値単価_14"
    elif str_column_name == "sYobineTanka_15" : str_name_kanji = "呼値単価_15"
    elif str_column_name == "sYobineTanka_16" : str_name_kanji = "呼値単価_16"
    elif str_column_name == "sYobineTanka_17" : str_name_kanji = "呼値単価_17"
    elif str_column_name == "sYobineTanka_18" : str_name_kanji = "呼値単価_18"
    elif str_column_name == "sYobineTanka_19" : str_name_kanji = "呼値単価_19"
    elif str_column_name == "sYobineTanka_20" : str_name_kanji = "呼値単価_20"
    elif str_column_name == "sDecimal_1" : str_name_kanji = "小数点以下桁数_1"
    elif str_column_name == "sDecimal_2" : str_name_kanji = "小数点以下桁数_2"
    elif str_column_name == "sDecimal_3" : str_name_kanji = "小数点以下桁数_3"
    elif str_column_name == "sDecimal_4" : str_name_kanji = "小数点以下桁数_4"
    elif str_column_name == "sDecimal_5" : str_name_kanji = "小数点以下桁数_5"
    elif str_column_name == "sDecimal_6" : str_name_kanji = "小数点以下桁数_6"
    elif str_column_name == "sDecimal_7" : str_name_kanji = "小数点以下桁数_7"
    elif str_column_name == "sDecimal_8" : str_name_kanji = "小数点以下桁数_8"
    elif str_column_name == "sDecimal_9" : str_name_kanji = "小数点以下桁数_9"
    elif str_column_name == "sDecimal_10" : str_name_kanji = "小数点以下桁数_10"
    elif str_column_name == "sDecimal_11" : str_name_kanji = "小数点以下桁数_11"
    elif str_column_name == "sDecimal_12" : str_name_kanji = "小数点以下桁数_12"
    elif str_column_name == "sDecimal_13" : str_name_kanji = "小数点以下桁数_13"
    elif str_column_name == "sDecimal_14" : str_name_kanji = "小数点以下桁数_14"
    elif str_column_name == "sDecimal_15" : str_name_kanji = "小数点以下桁数_15"
    elif str_column_name == "sDecimal_16" : str_name_kanji = "小数点以下桁数_16"
    elif str_column_name == "sDecimal_17" : str_name_kanji = "小数点以下桁数_17"
    elif str_column_name == "sDecimal_18" : str_name_kanji = "小数点以下桁数_18"
    elif str_column_name == "sDecimal_19" : str_name_kanji = "小数点以下桁数_19"
    elif str_column_name == "sDecimal_20" : str_name_kanji = "小数点以下桁数_20"
    elif str_column_name == "sCreateDate" : str_name_kanji = "作成日"
    elif str_column_name == "sUpdateDate" : str_name_kanji = "更新日"
    else :
        str_name_kanji = str_column_name
    return str_name_kanji










# 機能: 取得するマスターデータの種類により取得項目名の漢字名変換関数に分岐する。
# 引数1: マスターデータ種類
# 返値: 取得項目文字列
# 補足:  'CLMStkGetIssueMstKabu'         # 株式 銘柄マスタ
#       'CLMStkGetIssueSizyouMstKabu'   # 株式 銘柄市場マスタ
#       'CLMStkGetIssueMstSak'          # 先物
#       'CLMStkGetIssueMstOp'           # ＯＰ
#       'CLMIssueMstOther'        # 指数、為替、その他
#       'CLMStkGetOrderErrReason'       # 取引所エラー理由コード
#       'CLMStkGetDateZyouhou'          # 日付情報
#        呼び値は、個別ダウンロードでは指定不可
def func_column_kanji(str_sTargetCLMID, str_clumn_name):
    str_column_kanji = ''
    if str_sTargetCLMID == 'CLMStkGetIssueMstKabu' :
        str_column_kanji = func_column_kanji_CLMStkGetIssueMstKabu(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetIssueSizyouMstKabu' :
        str_column_kanji = func_column_kanji_CLMStkGetIssueSizyouMstKabu(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetIssueMstSak' :
        str_column_kanji = func_column_kanji_CLMStkGetIssueMstSak(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetIssueMstOp' :
        str_column_kanji = func_column_kanji_CLMStkGetIssueMstOp(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMIssueMstOther' :
        str_column_kanji = func_column_kanji_CLMIssueMstOther(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetDaiyouKakeme' :
        str_column_kanji = func_column_kanji_CLMStkGetDaiyouKakeme(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetHosyoukinMst' :
        str_column_kanji = func_column_kanji_CLMStkGetHosyoukinMst(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetDateZyouhou' :
        str_column_kanji = func_column_kanji_CLMStkGetDateZyouhou(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetOrderErrReason' :
        str_column_kanji = func_column_kanji_CLMStkGetOrderErrReason(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMSystemStatus' :
        str_column_kanji = func_column_kanji_CLMSystemStatus(str_clumn_name)
        
    elif str_sTargetCLMID == 'CLMStkGetYobine' :              # 呼び値は、個別ダウンロードでは指定不可。
        str_column_kanji = func_column_kanji_CLMStkGetYobine(str_clumn_name)
            
    return str_column_kanji




# 機能： 項目別マスターダウンロード
# 引数1：int_p_no
# 引数2：str_sTargetCLMID
# 引数3：str_sTargetColumn
# 引数4：class_login_property
# 返値: 辞書型データ（APIからのjson形式返信データをshift-jisのstring型に変換し、更に辞書型に変換）



# 機能: 限月が、当月以後（限月<=当月）ならば、True、当月より前（限月<当月）ならばFalseを返す。
# 
def func_judge_past_gengetsu(list_data):
    bool_judge = True
    
    # システム時刻の取得
    dt_systime = datetime.datetime.now()
    # 当月のyyyymmを取得
    str_tougetsu = str(dt_systime.year) + ('00' + str(dt_systime.month))[-2:]

    if int(list_data.get('sGengetu')) >= int(str_tougetsu) :
        bool_judge = True
    else :
        bool_judge = False

    return bool_judge


# 機能: csv形式でファイルに書き込む
# 返値: 
# 引数1:
# 引数2:
# 備考: 1行目は、タイトル行
#     2行目以降は、データ行 
def func_write_master_kobetsu(str_sTargetCLMID, \
                              json_return, \
                              str_master_filename):
##                              str_sTargetColumn, \
    
    str_a_clmid = 'a' + str_sTargetCLMID[:6] + str_sTargetCLMID[9:]
    print('str_a_clmid:', str_a_clmid)
    
    


    # 返り値からsTargetCLMID内のデータレコードのみ抜き出す
    list_return = json_return.get(str_a_clmid)
    
    if not list_return == None:
        try :
                
            with open(str_master_filename, 'w') as fout:
                int_num_of_articles = len(list_return[0].keys())
                iter_keys = iter(list_return[0].keys())
                    
                # タイトル行
                str_text = ''
                str_kanji = ''
                for i in range(int_num_of_articles) :
                    work_key = next(iter_keys)
                    work_kanji = func_column_kanji(str_sTargetCLMID, work_key)
                    
##                    str_text = str_text + next(iter_keys) + ','
                    str_text = str_text + work_key + ','
                    str_kanji = str_kanji + work_kanji + ','
                str_text = str_text[:-1] + '\n'
                fout.write(str_text)        # タイトル行をファイルに書き込む
                
                str_kanji = str_kanji[:-1] + '\n'
                fout.write(str_kanji)        # タイトル行をファイルに書き込む
                
                for i in range(len(list_return)):
                    # デフォルトでTrueをセット。
                    # 条件に合わない場合（非上場銘柄、過去の限月）は、以降でFalseをセット。
                    bool_judge = True


                    # 株式
                    # 銘柄マスタ_株       優先市場が 非上場:9 を除外
                    if str_sTargetCLMID == 'CLMStkGetIssueMstKabu' :
                        if list_return[i].get('sYusenSizyou') == '9' :
                            bool_judge = False

                    # 銘柄市場マスタ_株     上場市場が 非上場:9 を除外
                    if str_sTargetCLMID == 'CLMStkGetIssueSizyouMstKabu' :
                        if list_return[i].get('sZyouzyouSizyou') == '9' :
                            bool_judge = False
                    
                    # 先物、OP     過去の限月を削除する
                    if str_sTargetCLMID == 'CLMStkGetIssueMstSak' \
                       or str_sTargetCLMID == 'CLMStkGetIssueMstOp' :
                        bool_judge = func_judge_past_gengetsu(list_return[i])

                    if bool_judge :
                        iter_values = iter(list_return[i].values())
                    
                        str_text = ''
                        for n in range(int_num_of_articles) :
                            str_text = str_text +  next(iter_values) + ','
                        str_text = str_text[:-1] + '\n'
                        fout.write(str_text)        # データを1行ファイルに書き込む
                
        except IOError as e:
            print('File can not write!!!')
            print(type(e))
    else :
        str_txt = str_sTargetCLMID + ' は、取得できません。'
        print('エラー：')
        print(str_txt)



# ======================================================================================================
#      プログラム始点 
# ======================================================================================================

if __name__ == "__main__":
    
    # 表示形式を接続情報ファイルから読み込む。
    dic_url_info = func_get_url_info(FNAME_URL_INFO)
    str_sJsonOfmt = dic_url_info.get("sJsonOfmt")

    # ログイン応答を保存した「file_login_response.txt」から、仮想URLと口座情報を取得
    dic_login_property = func_get_login_response(FNAME_LOGIN_RESPONSE)

    # 現在（前回利用した）のp_noをファイルから取得する
    my_p_no = func_get_p_no(FNAME_INFO_P_NO)
    my_p_no = my_p_no + 1
    # 更新した"p_no"を保存する。
    func_save_p_no(FNAME_INFO_P_NO, my_p_no)

    print()
    print('-- マスター取得（個別） -------------------------------------------------------------')
    
    # 取得項目名を作成
    # my_sTargetColumn = func_make_sTargetColumn(S_TARGET_CLMID)
    
    # API要求項目のセット
    dic_req_item = {
        'p_no':             str(my_p_no),
        'p_sd_date':        func_p_sd_date(),

        'sCLMID':           S_CLMID,                    # 対象機能ＩＤ
        'sJsonOfmt':        str_sJsonOfmt               # 表示形式（サポートへの問い合わせでは'5'を指定指定した送信電文と受信電文で。）
    }

    # 'CLMMfdsGetMasterData'は、仮想URL:'sUrlMaster'
    str_connection_url = dic_login_property.get('sUrlMaster')

    # API問い合わせ実行
    #   項目別のマスターデータ取得は、通常のAPI呼び出し。
    #   マスターダウンロード専用（＝ストリーミング形式）の呼び出しは使わない。
    dic_return = func_api_request_from_dic(
                                                False,                  # ログインFlag。    login:true   login以外:false
                                                str_connection_url,     # 接続先URL。
                                                                        #    ログイン時は、FNAME_URL_INFOから取得する接続先。
                                                                        #   それ以外はログインレスポンスで指定される仮想URL。
                                                dic_req_item            # API要求項目
                                            )

    if dic_return is not None:
        if dic_return.get('p_errno') != '-2' and dic_return.get('p_errno') != '2':
            # csv形式でファイルへの書き出し
            func_write_master_kobetsu(
                                        S_CLMID, 
                                        dic_return, 
                                        FNAME_OUTPUT
                                    )

        elif dic_return.get('p_errno') == '-2' :
            print()
            print('p_errno', dic_return.get('p_errno'))
            print('p_err', dic_return.get('p_err'))
            print("パラメーターの設定に誤りが有ります。")

        # 仮想URLが無効になっている場合
        # if dic_return.get('p_errno') == '2':
        else:
            print()
            print('p_errno', dic_return.get('p_errno'))
            print('p_err', dic_return.get('p_err'))
            print("仮想URLが有効ではありません。")
            print("e_api_login_pubkey.py")
            print("の実行を再度行い、新しく仮想URL（1日券）を取得してください。")
    else:
        print('API接続自体の失敗')
        print('JSON形式の受信電文ではありません。接続先も含めて送信電文、受信電文を確認してください。')



    print()    
    print()
    # 最終の'p_no'を保存する。
    func_save_p_no(FNAME_INFO_P_NO, my_p_no)
