`cawo_dump` is built from `cawo_dump.cpp` against the official CaWoSched library
(KIT-EAE/CaWoSched, commit dfc8e49c692bb6178bb88514a9f9e8fb8b1bdf7b, MIT licence):

    git clone https://github.com/KIT-EAE/CaWoSched && cd CaWoSched/CaWoSched
    mkdir build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make
    g++ -O2 -std=c++17 -I.. ../app/cawo_dump.cpp libMultiProcessor.a -o cawo_dump
