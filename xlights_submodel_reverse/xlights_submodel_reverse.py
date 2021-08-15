import xml.etree.ElementTree as ET
import argparse

ids = None

# we are reversing the string of pixels in xlights, remap pixels such that top index line is now bottom index line (ex below)
# top idx line: 1 2 3 4 5 6 7 8 9 
# bot idx line: 9 8 7 6 5 4 3 2 1
# so pixel 2, now becomes pixel 8, etc.
def remap_line(line):
    parts = line.split(",")
    new_line = ""
    for p in parts:
        if '-' in p:
            part_range = p.split('-')
            front = part_range[0]
            back = part_range[1]
            new_line = new_line + "," + str(ids[int(front)]) + "-" + str(ids[int(back)])
            pass
        else:
            new_line = new_line + "," + str(ids[int(p)])
    # strip leading comma
    new_line = new_line[1:]
    return str(new_line)


# take a single sub model line and reverse it
# eg line0: 10-6,5,2  -> 2,5,6-10
def reverse_line(line):
    parts = line.split(",")
    new_line = ""
    for p in reversed(parts):
        if '-' in p:
            part_range = p.split('-')
            front = part_range[0]
            back = part_range[1]
            new_line = new_line + "," + str(int(back)) + "-" + str(int(front))
        else:
            new_line = new_line + "," + str(int(p))
    # strip leading comma
    new_line = new_line[1:]
    return str(new_line)


# swap lines within a sub model
# line0, line1, line2 now becomes line2,line1,line0
def swap_lines(attribs):
    # terrible way to do this, but quick and dirty
    lines = []
    for k,v in attribs.items():
        if k.startswith('line'):
            lines.append(v)

    line_num = 0
    for l in reversed(lines):
        attribs['line'+ str(line_num)] = l
        line_num = line_num + 1
    
    return attribs

def find_max_pixel(model):
    max_pixel_num = 0
    lines = model.split(';')
    for l in lines:
        line_ids = l.split(',')
        for i in line_ids:
            if len(i) > 0:
                id = int(i)
                if id > max_pixel_num:
                    max_pixel_num = id

    return max_pixel_num


def main(args):
    # create xml tree of xml file
    tree = ET.parse(args.model_xml_file)
    root = tree.getroot()

    pixel_ct = find_max_pixel(root.attrib['CustomModel'])
    print("Input Model File:", args.model_xml_file)
    print("Model Name:", root.attrib['name'], "- %s Pixels" % (pixel_ct))

    global ids
    ids = list(range(pixel_ct,0,-1))
    ids.insert(0,99999999)  # xligts is 1 indexed not 0 index. throw trash out front

    submodels = {}
    non_submodels = []

    last_created_name = ""
    # iterate over child nodes
    for child in root:
        # only process submodels
        if child.tag == "subModel":
            print("- Processing tag - %s - %s" % (child.tag, child.attrib['name']))
            new_attribs = {}
            for k,v in child.attrib.items():
                # process all line values within the subModel
                if k.startswith('line'):
                    # print("appending to lines:", k)
                    remaped_line = remap_line(v)
                    reversed_line = reverse_line(remaped_line)
                    new_attribs[k]=reversed_line
                else:
                    # copy every other attrib
                    new_attribs[k] = v
            new_attribs = swap_lines(new_attribs)
            child.attrib = new_attribs

            # Strong assumption about ordering of the model
            if(not child.attrib["name"][-1].isdigit()):
                submodels[child.attrib["name"]] = []
                last_created_name = child.attrib["name"]
            
            submodels[last_created_name].append(child)

        else:
            print("- Skipping tag %s" % child.tag)
            non_submodels.append(child)
            pass

    # clear tree
    for k,v in submodels.items():
        for child in v:
            root.remove(child)
    for child in non_submodels:
        root.remove(child)

    # Had to rename the 'inner star' and 'middle star' from 'inner star 1' and 'middle star 1' for this parser to work
    # Reverse sub models.. strong assumption on xml format
    for k,v in submodels.items():
        if len(v) > 1:
            # reverse list (slicing trick)
            models = v[::-1]
            # take base group element (at end of list since reversed)
            base_model = models.pop()
            # append element to root
            root.append(base_model)
            next_num = 1
            for e in models:
                new_name = e.attrib['name'][:-1] + str(next_num)
                print("overwriting %s with %s" % (e.attrib['name'], new_name))
                e.attrib['name'] = new_name
                root.append(e)
                next_num = next_num + 1
        else:
            root.append(v[0])

    for element in non_submodels:
        root.append(element)

    print("Writing to XML file %s" % (args.model_xml_file_out))
    tree.write(args.model_xml_file_out, encoding='utf-8', xml_declaration=True)


if __name__=="__main__":
    # TODO Reverse custommodel['CustomModel']
    # TODO Calculate node count from custommodel['CustomModel']

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--input', dest='model_xml_file', help='xmodel file to process')
    parser.add_argument('--output', dest='model_xml_file_out', help='xmodel file to write')

    args = parser.parse_args()

    main(args)
