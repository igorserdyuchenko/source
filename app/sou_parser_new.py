from app.modules.neo4j.models.symbol import SymbolType

import xml.etree.ElementTree as ET
import uuid

from lxml import etree as ET
import uuid


def parse(path):
    # Enable recovery from malformed XML
    context = ET.iterparse(path, events=("start", "end"), recover=True)
    pending_class = None

    for event, elem in context:
        if event == "start" and elem.tag in ["class", "comment", "methods"]:
            if elem.tag == "class":
                name = extract_class_name(elem.findtext("name"))
                inner_xml = "".join(
                    ET.tostring(e, encoding="unicode", method="xml") for e in elem
                ).strip()

                pending_class = {
                    "name": name,
                    "type": SymbolType.TYPE,
                    "body": inner_xml,
                    "comment": "",
                    "id": str(uuid.uuid4()),
                }

            elif elem.tag == "comment" and pending_class:
                comment_class_id = extract_class_name(elem.findtext("class-id", ""))
                if comment_class_id.endswith(pending_class["name"]):
                    pending_class["comment"] = elem.findtext("body", "").strip()

                yield pending_class
                pending_class = None
                elem.clear()

            elif elem.tag == "methods":
                class_name = extract_class_name(elem.findtext("class-id"))

                for body in elem.findall("body"):
                    yield {
                        "name": f"{class_name}.{body.get('selector')}",
                        "type": SymbolType.METHOD,
                        "comment": "",
                        "body": (body.text or "").strip(),
                        "id": str(uuid.uuid4()),
                    }
                elem.clear()

            elif pending_class:
                yield pending_class
                pending_class = None
                elem.clear()
            else:
                elem.clear()


def parse_metadata(path):
    fqdn_set = set()
    context = ET.iterparse(path, events=("end",))
    for event, elem in context:
        if elem.tag == "methods":
            class_name = elem.findtext("class-id")
            for body in elem.findall("body"):
                selector = body.get('selector')
                if class_name and selector:
                    fqdn_set.add(f"{class_name}.{selector}")

            elem.clear()
    return fqdn_set


def extract_class_name(full_name: str) -> str:
    return full_name.split(".")[-1]

# for m in parse("/Users/iserdyuc/sources/migrator/source/app/LibraryApp.sou"):
#     print(m)
#     # print(m["source"])
#     print("-----")

# metadata = parse_metadata("/Users/iserdyuc/sources/migrator/source/app/LibraryCore.sou")
# print(metadata)
