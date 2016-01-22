#!/usr/bin/env python
#-*-coding:utf-8-*-

import os
import sys
import getopt
import commands
import xml.dom.minidom
import urllib, urllib2
import json

class Translator():
    
    def __init__(self):
        self.fromLang = 'auto'
        self.toLang = ''
        self.inFile = ''
        self.outFile = ''
        
    def checkParams(self):
        if self.toLang == '' or self.inFile == '' or self.outFile == '':
            usage()
            
    def progress(self, pct):
        resize = commands.getoutput('resize')
        if resize == '':
            return
            
        columns = resize.split(';')[0]
        if columns.find('=') == -1:
            return
            
        width = int(columns.split('=')[1])
        count = width - 10
        pos = int(pct * count / 100)
        output = '\r['
        for i in range(count):
            if i < pos:
                output += '='
            elif i == pos:
                output += '>'
            else:
                output += ' '
        output += ']%3s%%' % str(pct)
        sys.stdout.write(output)
        sys.stdout.flush()
        
    def googleTranslate(self, text):
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=' \
                 + self.fromLang +'&tl=' + self.toLang + '&dt=t&q=' + urllib.quote(text)
        
        user_agent = 'Mozilla/5.0 (compatible; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        req = urllib2.Request(url, headers=headers)
        res_data = urllib2.urlopen(req)
        res = res_data.read()
        jdecode = json.loads(res.replace(',,', '," ",').replace(',,', '," ",'))
        tlist = []
        for l in jdecode[0]:
            tlist.append(l[0])
        return ''.join(tlist)
        
    def startTranslate(self):
        self.checkParams()
        
        print 'start translate...\n'
        hasError = False
        dom1 = xml.dom.minidom.parse(self.inFile)
        root = dom1.documentElement
        androidns = root.getAttribute('xmlns:android')
        xliffns = root.getAttribute('xmlns:xliff')
        doc = xml.dom.minidom.Document()
        resources = doc.createElement('resources')
        if androidns and androidns != '':
            resources.setAttribute('xmlns:android', androidns)
        if xliffns and xliffns != '':
            resources.setAttribute('xmlns:xliff', xliffns)
        doc.appendChild(resources)

        nodes = root.getElementsByTagName('string')
        nodeCount = len(nodes)
        self.progress(0)
        for i in range(nodeCount):
            node = nodes[i]
            name = node.getAttribute('name')
            value = node.childNodes[0].data
            
            if not value.startswith('@string/'):
                value = value.replace("\\'", "'")
                value = value.replace("\\n", " ")
                try:
                    value = self.googleTranslate(value)
                except Exception, err:
                    print str(err)
                    hasError = True
                
            stringNode = doc.createElement('string')
            stringNode.setAttribute('name', node.getAttribute('name'))
            textNode = doc.createTextNode(value)
            stringNode.appendChild(textNode)
            resources.appendChild(stringNode)
            
            self.progress(i * 100 / nodeCount)

        f = open(self.outFile,'w')
        f.write(doc.toprettyxml(indent = '    ', encoding='utf-8'))
        f.close()
        self.progress(100)
        print
        if hasError:
            print '\033[1;33;40mSome error occured in translating, please check the output file\033[0m'

def usage():
    print """Usage: %s [OPTION...] [FILE]
    Convert strings of given file from one language to another.
    
    Input/Output format specification:
     -f, --from-lang=NAME       language code of original text
     -t, --to-lang=NAME         language code for output
      
    Output control:
     -o, --output=FILE          output file
     
     -?, --help                 Show this help message
    """ % sys.argv[0]
    exit(1)


def checkParams():
    pass

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'f:t:o:?', ['from-lang=', 'to-lang=', 'output=', 'help'])
    except getopt.GetoptError, err:
        usage()
        print '**', str(err), '**'
        sys.exit(2)
        
    if len(args) == 0:
        usage()
        
    translator = Translator()
    translator.inFile = args[0]
    for o, a in opts:
        if o in ['-f', '--from-lang']:
            translator.fromLang = a
        elif o in ['-t', '--to-lang']:
            translator.toLang = a
        elif o in ['-o', '--output']:
            translator.outFile = a
        elif o == '-?':
            usage()
            
    translator.startTranslate()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        
    main(sys.argv[1:])

