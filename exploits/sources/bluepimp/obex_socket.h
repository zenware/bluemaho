/*
 * UNrooted.net example code
 *
 * Prototypes for the functions in obex_socket.c
 *
 */

#ifndef OBEX_SOCKET_H_INCLUDED
#define OBEX_SOCKET_H_INCLUDED

#include <glib.h>
#include <openobex/obex.h>


struct cobex_context *cobex_open(const gchar *port);
struct cobex_context *cobex_setsocket(const int fd);
int cobex_getsocket(struct cobex_context *gt);
void cobex_close(struct cobex_context *gt);
gint cobex_connect(obex_t *handle, gpointer userdata);
gint cobex_disconnect(obex_t *handle, gpointer userdata);
gint cobex_write(obex_t *handle,gpointer userdata,guint8 *buffer, gint length);
gint cobex_handle_input(obex_t *handle, gpointer userdata, gint timeout);

#endif /* OBEX_SOCKET_H_INCLUDED */
