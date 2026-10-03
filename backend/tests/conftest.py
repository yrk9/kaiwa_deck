import os

# settingsは読み込み時に環境変数を使うので、appを読み込む前に決めておく
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
# テストが本物のDB(Supabase)に触れないよう、必ずメモリ上のSQLiteにする
os.environ["DATABASE_URL"] = "sqlite://"
