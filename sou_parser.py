# from app.modules.neo4j.models.symbol import SymbolType

import uuid

from lxml import etree as ET
import uuid


def parse(path):
    # Enable recovery from malformed XML
    context = ET.iterparse(path, events=("start", "end"), recover=True)
    pending_class = None
    types_count = 0
    methods_count = 0   

    for event, elem in context:

        if event == "end" and elem.tag in ["class", "comment", "methods"]:
            if elem.tag == "class":
                name = extract_class_name(elem.findtext("name"))
                inner_xml = "".join(
                    ET.tostring(e, encoding="unicode", method="xml") for e in elem
                ).strip()

                pending_class = {
                    "name": name,
                    "type": "SymbolType.TYPE",
                    "body": inner_xml,
                    "comment": "",
                    "id": str(uuid.uuid4()),
                }

            elif elem.tag == "comment" and pending_class:
                comment_class_id = extract_class_name(elem.findtext("class-id", ""))
                if comment_class_id.endswith(pending_class["name"]):
                    pending_class["comment"] = elem.findtext("body", "").strip()

                types_count=types_count+1

                yield pending_class
                pending_class = None
                elem.clear()

            elif elem.tag == "methods":
                try:
                    class_name = extract_class_name(elem.findtext("class-id"))
                except Exception as e:
                    inner_xml = "".join(
                    ET.tostring(e, encoding="unicode", method="xml") for e in elem).strip()
                    print(e)

                for body in elem.findall("body"):
                    methods_count=  methods_count +1
                    yield {
                        "name": f"{class_name}.{body.get('selector')}",
                        "type": "SymbolType.METHOD",
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

count = 0
methods = 0
types = 0
body_len = []
for m in parse("C:\\Users\serdyig\\Downloads\\lamCTM_5000.sou"):
    count +=1
    if m["type"]=="SymbolType.TYPE":
        types += 1
    else:
        methods += 1
    
    body_len.append(len(m["body"].splitlines()))


print(f"total types {types}")
print(f"total methods {methods}")
print(f"total count {count}")

print(f"Min body lines {min(body_len)}")
print(f"Max body lines {max(body_len)}")
print(f"Avg body lines {sum(body_len)/ len(body_len)}")

data = sorted(body_len)
n= len(data)
if n % 2==1:
    median = data[n//2]
else:
    median = (data[n//2-1] + data[n//2])/2

print(f"Median body lines {median}")