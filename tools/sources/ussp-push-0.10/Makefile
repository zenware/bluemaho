#
# UNrooted.net example code
#
# Minimal Makefile used to build my Bluez OBEX example.  The generated 
# executable 'ussp-push' can be used to push files using OBEX over RFCOMM with
# the Bluez Linux Bluetooth stack.  You should be able to just 'make' directly
# without any setup.
#

OBEXINC=$(shell pkg-config --cflags openobex) $(shell pkg-config --cflags bluez)
OBEXLIB=$(shell pkg-config --libs openobex) $(shell pkg-config --libs bluez)

CFLAGS:=${CFLAGS} -Wall

OBEX_INCLUDES=obex_macros.h obex_main.h obex_socket.h obex_sdp.h
BINARY=ussp-push

#
# The make rules.. basically just two files here plus the openobex and glib
# libraries and we can make the executable.
#

all: $(BINARY)

$(BINARY): obex_main.o obex_socket.o obex_sdp.o
	$(CC) -o $@ $^ ${OBEXLIB}
 
%.o: %.c ${OBEX_INCLUDES}
	$(CC) ${CFLAGS} ${OBEXINC} -c -o $@ $<

clean:
	-rm -rf $(BINARY) *.o *~
