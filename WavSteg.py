import sys
import os.path
import wave
import argparse
import math
import hashlib
import zipfile
import lzma

class WavFileException(Exception):
    Wav_file_damaged = "Check arguments or your .wav file might be damaged, or doesn't exist"


class WavHeader:
    def __init__(self, wav_file):
            sound = wave.open(wav_file, 'r')
            self.bytes_per_sample = sound.getsampwidth()
            self.num_frames = sound.getnframes()
            self.num_channels = sound.getnchannels()
            sound.close()


class FileBuffer:
    def __init__(self, file, mode, size):
        self.file = open(file, mode)
        self.mode = mode
        self.size = size
        self.buffer = b''

    def __enter__(self):
        return self

    def read(self, bytes_count):
        if self.buffer == b'':
            self.buffer = self.file.read(self.size)
            if not self.buffer:
                return None

        if bytes_count > len(self.buffer):
            self.buffer += self.file.read(self.size - len(self.buffer))
        r = self.buffer[0:bytes_count]
        self.buffer = self.buffer[bytes_count:]
        return r

    def write(self, data):
        self.buffer += data
        if len(self.buffer) > self.size:
            self.file.write(self.buffer)
            self.buffer = b''

    def __exit__(self, exc_type, exc_value, traceback):
        if self.buffer != b'' and self.mode == 'ab':
            self.file.write(self.buffer)
        self.file.close()


class WavFile:
    def __init__(self, wav_file):
        self.file = wav_file
        self.header = WavHeader(wav_file)
        self.offset = 36
        try:
            wav = open(wav_file, 'rb')
            self.chunk_id = wav.read(4).decode('utf-8')
            wav.read(4)
            self.format = wav.read(4).decode('utf-8')
            if self.format != 'WAVE' or self.chunk_id != "RIFF":
                raise WavFileException

            data = b''
            while b'data' not in data:
                self.offset += 1
                data += wav.read(1)
            self.offset += 4
            self.data_size = int.from_bytes(wav.read(4), 'little')
        except:
            raise WavFileException


class WavSteganography:
    BUFFER_SIZE = 64 * 1024

    @staticmethod
    def set_bit(int_byte, bit, offset):
        return int_byte | (1 << offset) if bit else int_byte & ~(1 << offset)

    @staticmethod
    def get_bit(int_byte, offset):
        return int_byte & (1 << offset) != 0

    @staticmethod
    def rewrite_hiding_data(wav_block, bytes_per_sample, lsb_byte, lsb_count=2):
        injection_offset = 0
        injection_int = int.from_bytes(lsb_byte, 'big')
        stegano_block = b''
        for i in range(0, len(wav_block), bytes_per_sample):
            first_byte = bytes([wav_block[i]])
            int_byte = int.from_bytes(first_byte, 'big')
            for j in range(lsb_count):
                bit = WavSteganography.get_bit(injection_int, injection_offset)
                int_byte = WavSteganography.set_bit(int_byte, bit, j)
                injection_offset += 1
            first_byte = bytes([int_byte])
            stegano_block += first_byte + wav_block[i + 1: i + bytes_per_sample]
        return stegano_block

    @staticmethod
    def eject(wav_block, bytes_per_sample, lsb_count):
        injection_int = 0
        injection_offset = 0
        for i in range(0, len(wav_block), bytes_per_sample):
            stegano_int = wav_block[i]
            for offset in range(lsb_count):
                bit = WavSteganography.get_bit(stegano_int, offset)
                injection_int = WavSteganography.set_bit(injection_int, bit,
                                                         injection_offset)
                injection_offset += 1
        return bytes([injection_int])

    @staticmethod
    def hide_data(wav_path, file_to_hide, file_name, wav_stegano, lsb_number):
        buffer_size = WavSteganography.BUFFER_SIZE
        wav_file = WavFile(wav_path)
        with FileBuffer(wav_path, 'rb', buffer_size) as wav_file_buffer:
            with FileBuffer(file_to_hide, 'rb', buffer_size) as file_to_hide_buffer:
                with FileBuffer(wav_stegano, 'ab', buffer_size) as wav_stegano_buffer:

                    prefix = wav_file_buffer.read(wav_file.offset)
                    wav_stegano_buffer.write(prefix)

                    # injecting lsb
                    bytes_per_sample = wav_file.header.bytes_per_sample
                    wav_block = wav_file_buffer.read(bytes_per_sample * (8 // 2))
                    lsb_byte = bytes([lsb_number])
                    stegano_data = WavSteganography.rewrite_hiding_data(wav_block,
                                                                        bytes_per_sample, lsb_byte)
                    wav_stegano_buffer.write(stegano_data)

                    # injecting size of hiding file

                    file_to_hide_size = os.path.getsize(file_to_hide)
                    file_to_hide_buffer.write(file_to_hide_size.to_bytes(4, 'big'))

                    # injecting size of file name and file name
                    file_name_size_byte = len(file_name).to_bytes(1, 'big')
                    file_to_hide_name_bytes = file_name.encode('utf-8')
                    file_to_hide_buffer.write(file_name_size_byte)
                    file_to_hide_buffer.write(file_to_hide_name_bytes)

                    while True:
                        hiding_data = file_to_hide_buffer.read(1)
                        if not hiding_data:
                            break
                        block_size = bytes_per_sample * (8 // lsb_number)
                        wav_block = wav_file_buffer.read(block_size)
                        stegano_data = WavSteganography.rewrite_hiding_data(wav_block,
                                                                            bytes_per_sample,
                                                                            hiding_data,
                                                                            lsb_number)
                        wav_stegano_buffer.write(stegano_data)
                    while True:
                        rest = wav_file_buffer.read(buffer_size)
                        if not rest:
                            break
                        wav_stegano_buffer.write(rest)

    @staticmethod
    def recover_data(wav_file):
        buffer_size = WavSteganography.BUFFER_SIZE
        wav_stegano = WavFile(wav_file)
        with FileBuffer(wav_file, 'rb', buffer_size) as wav_buffer:
                wav_buffer.file.seek(wav_stegano.offset)

                # recover lsb count
                bytes_per_sample = wav_stegano.header.bytes_per_sample
                block_size = bytes_per_sample * (8 // 2)
                block_lsb = wav_buffer.read(block_size)
                lsb_count_byte = WavSteganography.eject(block_lsb,
                                                        bytes_per_sample, 2)

                lsb_count = int.from_bytes(lsb_count_byte, 'big')
                size_bytes = b''

                # recover size of hidden file
                block_size = bytes_per_sample * (8 // lsb_count)
                while len(size_bytes) != 4:
                    wav_block = wav_buffer.read(block_size)
                    size_bytes += WavSteganography.eject(wav_block,
                                                         bytes_per_sample,
                                                         lsb_count)
                size = int.from_bytes(size_bytes, 'big')

                name_size_byte = WavSteganography.eject(wav_buffer.read(block_size),
                                                        bytes_per_sample, lsb_count)
                # recover file name
                name_size = int.from_bytes(name_size_byte, 'big')
                name_buffer = b''
                while name_size > 0:
                    wav_block = wav_buffer.read(block_size)
                    name_buffer += WavSteganography.eject(wav_block, bytes_per_sample,
                                                          lsb_count)
                    name_size -= 1
                file_name = name_buffer.decode()

                zip_path = get_file_name('arch.zip')

                with FileBuffer(zip_path, 'ab', buffer_size) as file_to_recover_buffer:
                    for i in range(size):
                        wav_block = wav_buffer.read(block_size)
                        ejection_byte = WavSteganography.eject(wav_block,
                                                               bytes_per_sample,
                                                               lsb_count)
                        file_to_recover_buffer.write(ejection_byte)
        with zipfile.ZipFile(zip_path, 'r', compression=zipfile.ZIP_LZMA) as z:
            z.extract(file_name)
        os.remove(zip_path)
        print('File {} was recovered in this folder'.format(file_name))


def get_file_name(file_path):
    n = 1
    while os.path.exists(file_path):
        file_path = file_path.replace('.', '(' + str(n) + ').')
        n = n + 1
    return file_path


def create_zip_archive(file_to_hide):
    zip_path = 'arch.zip'
    zip_path = get_file_name(zip_path)
    zip_file = zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_LZMA)
    zip_file.write(file_to_hide)
    zip_file.close()
    return zip_path


def check_arguments(arguments):
    arguments_correct = True
    if arguments.mode is not None:
        if arguments.mode in 'h':
            if (arguments.file_to_hide is None or arguments.wav_path is None
                or arguments.output is None
                    or arguments.lsb_count is None):
                arguments_correct = False
        elif arguments.mode == 'r':
            if arguments.wav_path is None:
                arguments_correct = False
        else:
            arguments_correct = False
    else:
        arguments_correct = False

    if not arguments_correct:
        print('ERROR: Check arguments and their count')
        print(usage())
        sys.exit(1)


def blake2s_hash(wav_path):
    hash_blake = hashlib.blake2s()
    size = WavSteganography.BUFFER_SIZE
    with FileBuffer(file=wav_path, mode='rb', size=size) as wav_buffer:
        block = wav_buffer.read(size)
        hash_blake.update(block)
    return hash_blake.hexdigest()


def is_size_suitable(arguments):
    w = wave.open(arguments.wav_path, 'rb')
    num_samples = w.getnchannels() * w.getnframes()
    max_bytes_to_hide = (num_samples * arguments.lsb_count) // 8
    size_of_hiding_file = os.path.getsize(arguments.file_to_hide)
    print(max_bytes_to_hide)
    print(size_of_hiding_file)
    if size_of_hiding_file > max_bytes_to_hide:
        required_lsb = math.ceil(size_of_hiding_file * 8 / num_samples)
        raise ValueError("Input file too large to hide, "
                         "requires {} LSBs, using {}"
                         .format(required_lsb, arguments.lsb_count))
    if w.getsampwidth() < arguments.lsb_count // 8:
        raise ValueError("Lsb count too large and can't be used")
    if arguments.lsb_count < 0:
        raise ValueError("Lsb count can't be negative")
    return


def usage():
    print("\nCommand Line Arguments:\n",
          "-mode=   Specify what you want to perform hiding or recovering (h/r)\n",
          "-h=      To hide data in a sound file\n",
          "-r=      To recover data from a sound file\n",
          "-s=      Path(absolute/relative) to sound with extension .wav\n",
          "-f=      Path(absolute/relative) to file you want to hide\n",
          "-o=      Path(absolute/relative) to output .wav file\n",
          "-c=      Number of bits to change in LSB stenography\n",)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-mode', dest='mode', choices=['h', 'r'],
                        help='Mode: hide or recover (h/r)')
    parser.add_argument('-s', dest='wav_path',
                        help='Path of .wav sound')
    parser.add_argument('-f', dest='file_to_hide',
                        help='Path of file you want to hide into .wav file')
    parser.add_argument('-o', dest='output',
                        help='Path ot output file')
    parser.add_argument('-c', dest='lsb_count', type=int,
                        help='Lsb count')

    arguments = parser.parse_args(sys.argv[1:])
    print(arguments)
    check_arguments(arguments)

    if arguments.mode == 'h':
        hash_before = blake2s_hash(arguments.wav_path)
        zip_path = create_zip_archive(arguments.file_to_hide)
        file_name = arguments.file_to_hide
        arguments.file_to_hide = zip_path
        is_size_suitable(arguments)
        WavSteganography.hide_data(arguments.wav_path, zip_path, file_name,
                                   arguments.output, arguments.lsb_count)
        os.remove(zip_path)
        print('Blake2s hash of wav-file before hiding  \n{}'.format(hash_before))
        print('Blake2s hash of wav-file with hidden file \n{}'.format(blake2s_hash(arguments.output)))
    elif arguments.mode == 'r':
        WavSteganography.recover_data(arguments.wav_path)


if __name__ == "__main__":
    main()
