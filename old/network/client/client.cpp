#include <iostream>
#include <enet/enet.h>
#include <stdio.h>
#include <cstring>
#include <string>
#include <pthread.h>
#include <map>

#include "chat_screen.hpp"

static ChatScreen chatScreen;
static int CLIENT_ID = -1;

class ClientData {
  private:
    int m_id;
    std::string m_username;

  public:
    ClientData(int id) : m_id(id) {}
    void SetUsername(std::string username) { m_username = username; }

    int GetID(){ return m_id; }
    std::string GetUsername() { return m_username; }
};

std::map<int, ClientData*> client_map;


void SendPacket(ENetPeer* peer,const char* data)
{
  ENetPacket* packet = enet_packet_create(data,strlen(data) + 1,ENET_PACKET_FLAG_RELIABLE);
  enet_peer_send(peer,0,packet);
  printf("packet sent");
}

void ParseData(char* data) {\
  int data_type;
  int id;
  sscanf(data, "%d|%d", &data_type, &id);

  switch (data_type) {
    case 1:
      if (id != CLIENT_ID) {
       char msg[80]; 
       sscanf(data, "%*d|%*d|%[^|]", &msg);
       chatScreen.PostMessage(client_map[id]->GetUsername().c_str(), msg); 
      }
      break;
    case 2:
      if (id != CLIENT_ID) {
       char username[80]; 
       sscanf(data, "%*d|%*d|%[^|]", &username);

       client_map[id] = new ClientData(id);
       client_map[id]->SetUsername(username);
      }
      break;
    case 3:
      CLIENT_ID = id;
      break;

    
  }
}

void* MsgLoop(ENetHost* client) { 
  while (true) {
   ENetEvent event; 
   while (enet_host_service(client, &event, 1000) > 0 ) {
    switch (event.type) {
      case ENET_EVENT_TYPE_RECEIVE:

        ParseData(event.packet->data);
        enet_packet_destroy(event.packet);

        break;
    }
   }
  }
}

int main(int argc, char ** argv){

  printf("Please Enter Your Username:\n");
  char username[80];
  scanf("%s", &username);

  if (enet_initialize() != 0){
    fprintf(stderr, "An error occurred while initializing ENet\n");
    return EXIT_FAILURE;
  }

  atexit(enet_deinitialize);

  ENetHost* client;
  client = enet_host_create(NULL, 1, 1, 0, 0);

  if (client == NULL) {
    fprintf(stderr, "An error occurred while tryign to create an ENet client host\n");
    return EXIT_FAILURE;
  }

  ENetAddress address;
  ENetEvent event;
  ENetPeer* peer;

  enet_address_set_host(&address, "cuppajoeman.com");
  address.port = 7777;

  peer = enet_host_connect(client, &address, 1, 0);
  if (peer == NULL) {
    fprintf(stderr, "No available peers for initiating an ENet connection\n");
    return EXIT_FAILURE;
  }

  if (enet_host_service(client, &event, 5000) > 0 && event.type == ENET_EVENT_TYPE_CONNECT) {
   puts("Connection to localhost:7777 succeeded"); 
  } else {
    enet_peer_reset(peer);
    puts("Connection to localhost:7777 failed"); 
    return EXIT_SUCCESS;
  }
  
  char str_data[80] = "2|";
  strcat(str_data, username);
  SendPacket(peer, str_data);

  chatScreen.Init();

  // Create thread for receiving data
  pthread_t thread;
  pthread_create(&thread, NULL, MsgLoop, client);

  bool running = true;

  // GAME LOOP START
  while (running) {

    std::string msg = chatScreen.CheckBoxInput();
    chatScreen.PostMessage(username,msg.c_str());

    char message_data[80] = "1|";
    strcat(message_data, msg.c_str());
    SendPacket(peer, message_data);

    if (msg == "/exit") {
     running = false; 
    }
    
  }
  // GAME LOOP END
  
  pthread_join(thread, NULL);
  
  enet_peer_disconnect(peer, 0);

  while (enet_host_service(client, &event, 3000) > 0) {
    switch(event.type) {
      case ENET_EVENT_TYPE_RECEIVE:
        enet_packet_destroy(event.packet);
        break;
      case ENET_EVENT_TYPE_DISCONNECT:
        puts("Disconnection succeeded."); 
        break;
    }
  }  


 return EXIT_SUCCESS; 
}

