"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
from chat_group import *
import json
from googletrans import Translator
translator = Translator()
import googletrans as gt

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.languages = gt.LANGUAGES
        self.languages2 = dict([(value, key) for key, value in gt.LANGUAGES.items()])
        self.language = "en"

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def translate(self, text):
        if self.language == "default":
            return text

        else:
            try:
                translation = translator.translate(text, dest = self.language)
                return translation.text

            except:
                return text

    def detect(self, text):
        result = ''
        result = self.languages2[translator.detect(text).lang]
        return result

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            return (True)
        elif response["status"] == "busy":
            self.out_msg += '[SERVER] User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += '[SERVER] Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += '[SERVER] User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += "[SERVER] " + 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += '[SERVER] Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += "[SERVER]" + 'Connected to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += "[SERVER] Search results (time/person/chat) for keyword '" + term + "':\n"
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].strip().isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                elif my_msg[0] == "t":
                    language = my_msg[1:].strip().lower()
                    if language in self.languages.keys():
                        self.language = language
                        self.out_msg += ("Your default language is now: "+ self.languages[language])
                        self.out_msg += menu

                    elif language in self.languages2.keys():
                        self.language = self.languages2[language]
                        self.out_msg += ("Your default language is now: "+ language)
                        self.out_msg += menu

                    elif language == "chinese":
                        self.language = "zh-cn"
                        self.out_msg += ("Your default language is now: " + self.languages["zh-cn"])
                        self.out_msg += menu

                    else:
                        self.out_msg += "Invalid language code\n"
                        self.out_msg += menu

                elif my_msg[0] == "d":
                    word = my_msg[1:].strip()
                    return self.detect(word)

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err :
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg
            
                if peer_msg["action"] == "connect":

                    # ----------your code here------#
                    self.peer = peer_msg["from"]
                    self.out_msg += "[SERVER] "+ "You are connected with " + peer_msg["from"] + ". Chat away! \n"
                    self.state = S_CHATTING
                    # ----------end of your code----#
                    
#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                t_msg = translator.translate(my_msg, dest = 'en').text.lower()
                if t_msg == 'bye' or t_msg == 'goodbye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in

                # ----------your code here------#
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "[SERVER] " + peer_msg["from"] + " joined"

                elif peer_msg["action"] == "disconnect":
                    self.out_msg += "[SERVER] " + self.peer + " left\n"
                    self.out_msg += "[SERVER] " + peer_msg['msg']
                    self.state = S_LOGGEDIN

                elif peer_msg["action"] == "left":
                    self.out_msg += "[SERVER] " + peer_msg["msg"]

                else:
                    self.out_msg += peer_msg['msg']
                # ----------end of your code----#
                
            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        message = self.translate(self.out_msg)
        return message