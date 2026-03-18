# working file for repeated manual test commands


repository_dir="/Users/jim/p/donorpipe_data/primary_repository/oliveseed"
sanitized_dir="/Users/jim/p/donorpipe_data/primary_repository/test_org"

# Full download refresh
# echo 2023...
# uv run warehouse/downloads/runner.py  --output-dir $repository_dir --year 2023
# echo 2024...
# uv run warehouse/downloads/runner.py  --output-dir $repository_dir --year 2024
# echo 2025...
# uv run warehouse/downloads/runner.py  --output-dir $repository_dir --year 2025
# echo 2026...
# uv run warehouse/downloads/runner.py  --output-dir $repository_dir --year 2026

# create sanitized test data

#echo santize...
#python scripts/sanitize_csv.py  $repository_dir $sanitized_dir
#echo exiting

# build graphs for oliveseed and testdata
echo building graphs...
uv run scripts/generate_graph_json.py  --dir $repository_dir --output $repository_dir/graph.json
uv run scripts/generate_graph_json.py  --dir $sanitized_dir --output $sanitized_dir/graph.json
