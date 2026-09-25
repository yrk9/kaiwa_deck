import os

# app.core.config.settings はimport時に環境変数を読むため、appをimportする前に固定する
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
