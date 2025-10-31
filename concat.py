import pandas as pd
from pathlib import Path

def main():
    """
    dataフォルダ内の全CSVファイルを縦結合し、重複を削除してconcat.csvとして保存する。
    """
    data_dir = Path("data")
    output_file = data_dir / "concat.csv"
    
    # dataフォルダ内の全CSVファイルを取得（concat.csvは除外）
    csv_files = [f for f in data_dir.glob("*.csv") if f.name != "concat.csv"]
    
    if not csv_files:
        print("CSVファイルが見つかりませんでした。")
        return
    
    # 各CSVファイルを読み込んでリストに格納
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
            print(f"読み込み: {csv_file.name} ({len(df)}行)")
        except Exception as e:
            print(f"スキップ: {csv_file.name} - {e}")
            continue
    
    if not dfs:
        print("読み込み可能なCSVファイルがありませんでした。")
        return
    
    # 全てのデータフレームを縦結合
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"\n結合後: {len(combined_df)}行")
    
    # 重複を削除
    duplicates_count = combined_df.duplicated().sum()
    combined_df = combined_df.drop_duplicates().reset_index(drop=True)
    print(f"重複削除: {duplicates_count}件")
    print(f"最終: {len(combined_df)}行")
    
    # concat.csvとして保存
    combined_df.to_csv(output_file, index=False)
    print(f"\n保存完了: {output_file}")

if __name__ == "__main__":
    main()
