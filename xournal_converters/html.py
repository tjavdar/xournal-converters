#!/usr/bin/env python
from argparse import ArgumentParser
from xml.etree.cElementTree import ElementTree
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import gzip, cgi


def main():
    # fetch path
    parser = ArgumentParser()
    parser.add_argument('path')
    args = parser.parse_args()

    # extract xml in zip archive
    with gzip.open(args.path, 'rb') as fp:
        xml = ElementTree(file=fp)

    # convert to HTML
    def coords(stroke):
        coords = stroke.text.split()
        coords = ' '.join('L ' + coords[i] + ' ' + coords[i + 1]
                          for i in range(0, len(coords), 2))
        return 'M' + coords[1:]

    errors = []

    iostr = StringIO()
    for page in xml.getroot().iter('page'):
        # determine background info
        background = page.find('background')
        if background.attrib['type'] == 'solid':
            background_color = background.attrib['color']
            if background.attrib['style'] != 'plain':
                errors.append("Do not know how to handle background style '%s'"
                        .format( background.attrib['style']) )
        else:
            errors.append("Do not know how to handle background type '%s'"
                    .format( background.attrib['type']) )

        # start new page
        print('<p>',file=iostr)
        print('<svg width="%spt" height="%spt" style="border: 1px solid black; background-color: %s" viewBox="0 0 %s %s">'
                .format(
                page.attrib['width'], page.attrib['height'], background_color,
                page.attrib['width'], page.attrib['height']),file=iostr)
        for layer in page.iter('layer'):
            print('<g>',file=iostr)
            for item in layer:
                if item.tag == 'stroke':
                    if item.attrib["tool"] not in ["pen", "highlighter"]:
                        errors.append(
                            "Do not know how to handle stroke tool '%s'"
                            .format( item.attrib['tool']) )
                    print('<path d="%s" fill="none" stroke="%s" stroke-width="%s"'
                            .format(
                            coords(item), item.attrib["color"],
                            item.attrib["width"]), file=iostr)
                    if item.attrib["tool"] == "highlighter":
                        print('stroke-opacity="0.5"',file=iostr)
                    print('/>',file=iostr)
                elif item.tag == 'text':
                    dy = 0
                    font_size = float(item.attrib["size"])
                    for line in item.text.split("\n"):
                        print('<text font-family="%s" font-size="%s" x="%s" y="%s" fill="%s">%s</text>'
                                .format(
                                item.attrib["font"], font_size, item.attrib["x"],
                                dy + float(item.attrib["y"]) + font_size,
                                item.attrib["color"], cgi.escape(line)) ,file=iostr)

                        dy += float(item.attrib["size"])
                elif item.tag == 'image':
                    print('<image x="%s" y="%s" width="%s" height="%s" xlink:href="data:image/png;base64,%s" />'
                            .format(
                            item.attrib["left"], item.attrib["top"],
                            float(item.attrib["right"]) -
                            float(item.attrib["left"]),
                            float(item.attrib["bottom"]) -
                            float(item.attrib["top"]), cgi.escape(item.text)) ,file=iostr)
                else:
                    errors.append("Unknown item '%s'".format(item.tag))
            print('</g>',file=iostr)
        print('</svg>',file=iostr)
        print('</p>',file=iostr)

    # render document with errors prefixed
    print ('<html>')
    print ('<body>')

    if errors:
        print ('<p>')
        print ('<ul style="color: red">')
        for e in errors:
            print ('<li>', e, '</li>')
        print ('</ul>')
        print ('</p>')

    print (iostr.getvalue())

    print ('</body>')
    print ('</html>')


if __name__ == '__main__':
    main()
