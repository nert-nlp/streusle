#!/usr/bin/env python3
import json
import os
from argparse import ArgumentParser


def sent2doc(sent_id):
    parts = sent_id.split("-")
    parts = parts[:-1]
    doc_id = "-".join(parts)
    assert doc_id and len(doc_id) > 0
    return doc_id


def process_json(json_file, output_dir):
    # read json
    with open(json_file, "r", encoding="utf-8") as f:
        sentences = json.load(f)

    base_dir = os.path.dirname(os.path.abspath(json_file))
    current_doc = []
    doc_count = 0

    os.makedirs(output_dir, exist_ok=True)
    for i, sentence in enumerate(sentences):
        sent_id = sentence["sent_id"]
        doc_id = sent2doc(sent_id)
        current_doc.append(sentence)

        if i == len(sentences) - 1 or sent2doc(sentences[i + 1]["sent_id"]) != doc_id:
            with open(
                os.path.join(output_dir, doc_id + ".json"), "w", encoding="utf-8"
            ) as f:
                json.dump(current_doc, f)
                current_doc = []
                doc_count += 1
    print("Wrote " + str(doc_count) + " docs to " + output_dir)


if __name__ == "__main__":
    argparser = ArgumentParser(
        description=(
            "Given a STREUSLE JSON, splits it into smaller JSONs corresponding to source documents."
        )
    )
    argparser.add_argument("json_file", type=str)
    argparser.add_argument("output_dir", type=str)
    process_json(**vars(argparser.parse_args()))
