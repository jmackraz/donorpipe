# working file for repeated manual test commands


test_dir="/Users/jim/p/donorpipe_data/comparison_tests/"

#uv run warehouse/downloads/runner.py  --output-dir $test_dir/from_api --year 2025
#uv run scripts/generate_graph_json.py  --dir $test_dir/from_api/ --output $test_dir/from_api/graph.json
#uv run scripts/generate_graph_json.py  --dir $test_dir/web_download/ --output $test_dir/web_download/graph.json
diff $test_dir/web_download/graph.json $test_dir/from_api/graph.json