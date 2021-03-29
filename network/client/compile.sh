#!/bin/bash
g++ chat_screen.cpp client.cpp -o client.out -lpthread -lncurses -lenet -fpermissive
