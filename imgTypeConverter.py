import argparse
import fnmatch
import os
import sys

from PIL import Image
from progress.bar import ChargingBar


suported_formats = ["png", "jpeg", "jpg", "jfif", "webp"]


arg_parser = argparse.ArgumentParser(
    prog='ImgTypeConverter',
    description='Converts image/images in directory given on input to specified file format',
    epilog='Supported formats are: ' + ', '.join(map(str, suported_formats)))

arg_parser.add_argument('input')
arg_parser.add_argument('-t', '--type', dest='type', type=str,
    help='specifies the destination file format (default png)')
arg_parser.add_argument('-f', '--filter', dest='filter', type=str,
    help='specifies the filter (fileformat which you want to be converted to destination file format)')
arg_parser.add_argument('-s', '--silent', action='store_true', help='disables all prints from the program')
arg_parser.add_argument('-r', '--recursive', action='store_true',
    help='enbales entering subdirectories if input given is directory. \
          Note this option will skip all paths that match this patern: *imgconv_backup*')
arg_parser.add_argument('--no-backup', action='store_false', dest='backup',
    help='disables creating backup of converted files (Warning may result in data loss)')


BACKUP = True
SILENT: bool = False
RECURSION: bool = False
TYPE: str = "png"
FILTER: str = None

COUNTER: int = 0
PROGRESS: int = 0
BACKUP_PATH = "imgconv_backup"

BAR = None


def log(msg: str, *args) -> None:
    if not SILENT: print(msg % (args))


def convert_image(path: str) -> None:
    global COUNTER
    COUNTER = COUNTER + 1
    img = Image.open(path).convert("RGB")
    head, tail = os.path.split(path)
    if BACKUP: os.replace(path, os.path.join(BACKUP_PATH, tail))
    else: os.remove(path)
    filename, _ = os.path.splitext(tail)
    img.save(os.path.join(head, filename) + "." + TYPE, TYPE)


def handle_file(filename: str, from_dir: bool = False) -> int:
    if not SILENT: BAR.next()
    _, type = os.path.splitext(filename)
    type = type.replace('.', '')
    if not from_dir and not type in suported_formats:
        log(".%s filetype not supported!\nSupported file types are %s or you can provide path to directory",
            type, ', '.join(map(str, suported_formats)))
        return 2

    if FILTER is not None and not FILTER == type:
        if not from_dir: log(".%s does not match given file type", type)
        return 3

    if TYPE != type:
        if not from_dir: log("%s is already of a target file type", TYPE)
        convert_image(filename)

    return 0


def handle_dir(dirname: str) -> None:

    for file in os.listdir(dirname):
        if os.path.isdir(os.path.join(dirname, file)):
            if RECURSION and not fnmatch.fnmatch(file, '*imgconv_backup*'):
                handle_dir(os.path.join(dirname, file))
        else:
            handle_file(os.path.join(dirname, file), from_dir=True)


def create_backup_dir() -> None:
    global BACKUP_PATH
    path = BACKUP_PATH
    counter = 1
    while os.path.exists(path):
        path = BACKUP_PATH + "_" + str(counter)
        counter = counter + 1
    os.mkdir(path)
    BACKUP_PATH = path


def count_files(path: str) -> int:
    total = 0

    if RECURSION:
        for _, _, files in os.walk(path):
            total = total + len(files)
    else:
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                total = total + 1

    return total


def main() -> int:
    args = arg_parser.parse_args()
    global SILENT, RECURSION, TYPE, FILTER, BACKUP
    SILENT = args.silent
    RECURSION = args.recursive
    BACKUP = args.backup
    TYPE = args.type if args.type else "png"
    FILTER = args.filter if args.filter else None

    if not os.path.exists(args.input):
        log('File %s does not exist', args.input)
        return 1

    if not (TYPE in suported_formats):
        log(".%s is not on a supported arg list!\nSupported file types are %s",
            TYPE, ', '.join(map(str, suported_formats)))
        return 2

    if FILTER is not None and not (FILTER in suported_formats):
        log(".%s is not on a supported arg list!\nSupported file types are %s",
            FILTER, ', '.join(map(str, suported_formats)))
        return 2

    if BACKUP:
        create_backup_dir()

    if os.path.isdir(args.input):
        if not SILENT:
            global BAR
            BAR = ChargingBar('Converting files', max=count_files(args.input))
        handle_dir(args.input)
        log('\n')
    else:
        return handle_file(args.input)

    log('Converted %i files', COUNTER)

    if BACKUP:
        log('Backup was written to ./%s', BACKUP_PATH)

    return 0


if __name__ == '__main__':
    sys.exit(main())
