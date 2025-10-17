mapionからスクレイピングしてデータを取得するスクリプトの作成
BASE_URL = "https://www.mapion.co.jp/"

1. サイト構造の把握

1. 業種、地域の絞り方
1. 絞った時のURLのパターン
    例）運送業:https://www.mapion.co.jp/s/q=運送業/t=spot/ 57294件
    例）運送業 熊本: https://www.mapion.co.jp/s/q=運送業%20熊本/t=spot/

1. ページネーションの確認（総ページ数、urlなど）
https://www.mapion.co.jp/s/q=運送業/t=spot/p=280
max = 100

1. seleniumかrequestsを使うかの判断
requestsで対応可能

1. 必要なデータの特定（会社名、住所、電話番号）

1. データ抽出方法（正規表現は使用せず、html要素の順番だけで抽出）
