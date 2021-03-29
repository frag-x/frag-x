#include <iostream>
#include <enet/enet.h>

void ParseData(ENetHost* server, int id, char* data) {
  std::cout << "Parsing: " << data << "\n";

  int data_type;
  sscanf(data, "%d|", &data_type);

  switch (data_type) {
    case 1:
      break;
    case 2:


      char username[80];
      sscanf(data, "2|%[^\n]", &username);

      char send_data[1024] = {'\0'};
      sprintf(send_data, "2|%d|%s", id, username);
      std::cout << "Send: " << send_data << "\n";
      break;
  }
}


int main(int argc, char ** argv){
  if (enet_initialize() != 0){
    fprintf(stderr, "An error occurred while initializing ENet\n");
    return EXIT_FAILURE;
  }
  atexit(enet_deinitialize);

  ENetAddress address;
  ENetHost* server;
  ENetEvent event;

  address.host = ENET_HOST_ANY;
  address.port = 7777;

  server = enet_host_create(&address, 32, 1, 0, 0);

  if (server == NULL) {
    fprintf(stderr, "An error occurred while tryign to create an ENet server host\n");
    return EXIT_FAILURE;
  }
  // GAME LOOP START
  while (true) {
    while (enet_host_service(server, &event, 1000) > 0) {
      switch(event.type) {
        case ENET_EVENT_TYPE_CONNECT:
          printf("A new client connected from %x:%u.\n", event.peer -> address.host, event.peer -> address.port);
          break;
        case ENET_EVENT_TYPE_RECEIVE:
          printf ("A packet of length %u containing %s was received from %x:%u on channel %u.\n",
                  event.packet -> dataLength,
                  event.packet -> data,
                  event.peer -> address.host,
                  event.peer -> address.port,
                  event.channelID);
          ParseData(server, -1, event.packet -> data); 
          enet_packet_destroy(event.packet); 
          break;
        case ENET_EVENT_TYPE_DISCONNECT:
          printf("%x:%u disconnected.\n", event.peer -> address.host, event.peer -> address.port); 
          break;
      }
    }
  }
  // GAME LOOP END
  enet_host_destroy(server);
 
 return EXIT_SUCCESS; 
}

