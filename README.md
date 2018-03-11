Stenography
WavSteg.py is used to hide or recover files in file with extension .wav. WavSteg uses LSB(least significant bit) steganography.
For each sample in the audio file, we overwrite the least significant bits with
 the data from our file.


###How to use?### 

WavSteg.py requires Python 3

. Run program in terminal.
#For hiding file use these arguments:
-mode -h -- Specify that you want to perform hiding
-s PATh --  Path(absolute/relative) to sound with extension .wav
-f PATH --  Path(absolute/relative) to file you want to hide
-o PATH --  Path(absolute/relative) to output .wav file
-c COUNT -- Number of bits to change in LSB stenography

Example: #WavSteg.py -mode -h -f PATH -s PATH -o PATH -c COUNT

#For recover file use these arguments:
-mode -r -- Specify that you want to perform recover

Example: #WavSteg.py -mode -r -s PATH -o PATH 


