# Stenography .wav file
WavSteg.py is used to hide or recover files in file with extension .wav. WavSteg uses LSB(least significant bit) steganography.
For each sample in the audio file, we overwrite the least significant bits with the data from our file.


## How to use? ##

WavSteg.py requires Python 3. Run program in terminal. The program needs only build in libraries.

## For hiding file use these arguments:

-mode -h -- Specify that you want to perform **hiding**

-s Wav_PATH --  Path(absolute/relative) to sound with extension **.wav**

-f File_PATH --  Path(absolute/relative) to **file** you want to hide

-o Out_PATH --  Path(absolute/relative) to output .wav file

-c COUNT -- Number of bits to change in LSB stenography

### Example: 
WavSteg.py -mode -h -f File_PATH -s WAV_PATH -o Out_PATH -c COUNT

## Recover
-mode -r -- Specify that you want to perform recover

## Example: 
WavSteg.py -mode -r -s WAV_PATH -o Out_PATH 


