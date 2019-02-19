from ab2 import print_func
import sys
import argparse

usage = "%(prog)s [options] serveraddress"

parser = argparse.ArgumentParser(usage=usage)
parser.add_argument('-m','--smtp', dest='addresses',action="store", help='Use SMTP for mail transfer')

args=parser.parse_args()


print(args.addresses)
print("Server Address: ", sys.argv[0])

x="Hello my friend there"

print_func(x)