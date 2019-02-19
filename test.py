'''
from optparse import OptionParser

parser=OptionParser()

parser.add_option("-f", "--file", action="store",type="string", dest="filename", help="setting a filename")
parser.add_option("-v", action="store_true", dest="verbose", default=False, help="Setting verbose")

parser.add_option("-l", "--lang", action="store", dest="language", default="English", help="Setting up the language")

parser.add_option("-d", "--direct", action="append", help="Supplying from_addr and to_addr", dest="addresses")


(options, args)=parser.parse_args()

'''

import argparse


usage = "%(prog)s [options] serveraddress"

parser = argparse.ArgumentParser(usage=usage)

parser.add_argument("server", help="Enter the server address")
parser.add_argument('-m','--smtp', nargs=2, dest='addresses',action="store", help='Use SMTP for mail transfer')
parser.add_argument('-e', '--exchange', action="store_true", dest="exc", default=False, help="Use Exchange for mail transfer")
parser.add_argument("-n", "--port", action="store", type=int, dest="serverport", help="SMTP server port",
                      metavar="nnn")

parser.add_argument("-l", "--lang", action="store", dest="language", default='english', help="language for generating body and subject of mail")
parser.add_argument("-f", "--addressesfile", action="store", type=str, dest="addresses_file",
                      help="Email addresses to use for generated emails", metavar="filepath")


args=parser.parse_args()

if args.addresses is None and args.exc is False:
    print("Select one of Mail Server or Exchange")

print(args.exc)




