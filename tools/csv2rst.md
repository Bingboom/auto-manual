python tools/csv_to_rst.py --lang en
python tools/csv_to_rst.py --lang fr
python tools/csv_to_rst.py --lang es

rm -r docs\_build
python tools/build_multilang_bundle.py