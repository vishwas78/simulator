"""
@package simulator
peer_core module
"""
from queue import Queue
from .common import Common
import time

class Peer_core():
    def __init__(self, id):
        self.id = id
        self.socket = Common.UDP_SOCKETS[self.id]
        self.played_chunk = 0
        self.prev_received_chunk = 0
        self.buffer_size = 64
        self.player_alive = True
        self.chunks = []

        #---Only for simulation purposes----
        self.losses = 0
        self.played = 0
        self.number_of_chunks_consumed = 0
        #----------------------------------
        
        print("Peer", self.id)
        print("Peer Core initialized")

    def set_splitter(self, splitter):
        self.splitter = {}
        self.splitter["id"] = splitter
        self.splitter["socketTCP"] = Common.TCP_SOCKETS[splitter]
        self.splitter["socketUDP"] = Common.UDP_SOCKETS[splitter]

    def connect_to_the_splitter(self):
        hello = (-1,"P")
        self.splitter["socketTCP"].put((self.id,hello))

    def send_ready_for_receiving_chunks(self):
        ready = (-1, "R")
        self.splitter["socketTCP"].put((self.id,ready))

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False
    
    def process_message(self, message, sender):
        # ----- Only for simulation purposes ------
        # ----- Check if new round for peer -------
        if not self.is_a_control_message(message) and sender == self.splitter["id"]:
            if self.played > 0 and self.played >= len(self.peer_list):
                clr = self.losses/self.played
                Common.SIMULATOR_FEEDBACK["DRAW"].put(("CLR",self.id,clr))
                self.losses = 0
                self.played = 0
        # ------------------------------------------

    def process_next_message(self):
        content = self.socket.get() #it replaces receive_next_message
        return self.process_message(content[1], content[0])

    def buffer_data(self):

        for i in range(self.buffer_size):
            self.chunks.append((i,"L"))
        
        chunk_number = self.process_next_message()
        
        while(chunk_number < 0):
            chunk_number = self.process_next_message()

        self.played_chunk = chunk_number

        print(self.id,"Position in the buffer of the first chunk to play", str(self.played_chunk))
        
        while (chunk_number < self.played_chunk or ((chunk_number - self.played_chunk) % self.buffer_size) < (self.buffer_size // 2)):
            chunk_number = self.process_next_message()
            #while (chunk_number < 0 or chunk_number < self.played_chunk):
            while (chunk_number < self.played_chunk):
                chunk_number = self.process_next_message()
                    
        self.prev_received_chunk = chunk_number

    def keep_the_buffer_full(self):
        last_received_chunk = self.process_next_message()
        while (last_received_chunk < 0):
            last_received_chunk = self.process_next_message()

        self.play_next_chunks(last_received_chunk)

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            self.player_alive = self.play_chunk(self.played_chunk)
            self.chunks[self.played_chunk % self.buffer_size] = (self.played_chunk,"L")
            self.played_chunk = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk
    
    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number%self.buffer_size][1] == "C":
            self.played +=1
        else:
            self.losses += 1            
        self.number_of_chunks_consumed += 1
        return self.player_alive

    def run(self):
        while(self.player_alive):
            keep_the_buffer_full()
