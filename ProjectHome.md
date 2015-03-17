This project was made as part of university class named Informatica Electrónica in University Nacional de Rosario UNR.

We needed to read from several sensors on a microprocessing board, and needed to send that over a serial port. I went a bit further and made and application that's able to chart the sensors in "realtime".

The format for the sensors is: `<identifier>;<data><newline>` where data is in the units you want to display.

The program will automatic create a new chart for each new identifier.