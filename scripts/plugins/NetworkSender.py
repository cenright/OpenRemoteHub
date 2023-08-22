# -*- coding: utf-8 -*-
#
# This file is a plugin for EventGhost.
# Copyright (C) 2005-2009 Lars-Peter Voss <bitmonster@eventghost.org>
#
# EventGhost is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation;
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.



import socket
from hashlib import md5


class Text:
    host = "Host:"
    port = "Port:"
    password = "Password:"
    tcpBox = "TCP/IP Settings"
    securityBox = "Security"
    class Map:
        parameterDescription = "Event name to send:"



class NetworkSender():
    text = Text

    #def __init__(self):


    def __start__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password

    def Setup(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password

    def Configure(self, host="127.0.0.1", port=1024, password=""):
        text = self.text
        panel = eg.ConfigPanel()
        hostCtrl = panel.TextCtrl(host)
        portCtrl = panel.SpinIntCtrl(port, max=65535)
        passwordCtrl = panel.TextCtrl(password, style=wx.TE_PASSWORD)

        st1 = panel.StaticText(text.host)
        st2 = panel.StaticText(text.port)
        st3 = panel.StaticText(text.password)
        eg.EqualizeWidths((st1, st2, st3))
        tcpBox = panel.BoxedGroup(
            text.tcpBox,
            (st1, hostCtrl),
            (st2, portCtrl),
        )
        securityBox = panel.BoxedGroup(
            text.securityBox,
            (st3, passwordCtrl),
        )

        panel.sizer.Add(tcpBox, 0, wx.EXPAND)
        panel.sizer.Add(securityBox, 0, wx.TOP|wx.EXPAND, 10)

        while panel.Affirmed():
            panel.SetResult(
                hostCtrl.GetValue(),
                portCtrl.GetValue(),
                passwordCtrl.GetValue()
            )


    def Send(self, eventString, payload=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket = sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(2.0)
        try:
        #if True:
        
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)
            # First wake up the server, for security reasons it does not
            # respond by it self it needs this string, why this odd word ?
            # well if someone is scanning ports "connect" would be very
            # obvious this one you'd never guess :-)

            sock.sendall(b"quintessence\n\r")

            # The server now returns a cookie, the protocol works like the
            # APOP protocol. The server gives you a cookie you add :<password>
            # calculate the md5 digest out of this and send it back
            # if the digests match you are in.
            # We do this so that no one can listen in on our password exchange
            # much safer then plain text.

            cookie = sock.recv(128)

            # Trim all enters and whitespaces off
            cookie = cookie.strip()

            # Combine the token <cookie>:<password>
            token = cookie + bytes(":" + self.password, 'utf-8')

            # Calculate the digest
            digest = md5(token).hexdigest()

            # add the enters
            digest = digest + "\n"

            print(digest)

            # Send it to the server
            sock.sendall(bytes(digest, 'utf-8'))

            # Get the answer
            answer = sock.recv(512)
            
            print(str(answer, 'utf-8'))

            # If the password was correct and you are allowed to connect
            # to the server, you'll get "accept"
            if (str(answer, 'utf-8').strip() != "accept"):
                print("Not Accepted")
                sock.close()
                return False

            # now just pipe those commands to the server
            if (payload is not None) and (len(payload) > 0):
                #for pld in payload:
                sock.sendall(
                        #("payload %s\n" % pld).encode('utf-8')
                        ("payload %s\n" % payload).encode('utf-8')
                    )
            else:
                sock.sendall(bytes("payload withoutRelease\n", 'utf-8'))
                #sock.sendall(eventString.encode(eg.systemEncoding) + "\n")
            
            sock.sendall(eventString.encode('utf-8') + b"\n")

            return sock

        except:
            sock.close()
            #self.PrintError("NetworkSender failed")
            print("NetworkSender failed")
            return None
        

    def MapUp(self, sock):
        # tell the server that we are done nicely.
        sock.sendall(b"close\n")
        sock.close()

if False:
    snd = NetworkSender()
    snd.Setup("192.168.0.125", 666, "Test")
    #sock = snd.Send("RubberMaster")
    sock = snd.Send("RubberMaster", '{ "name":"John", "age":30, "city":"New York"}')

    if sock:
        snd.MapUp(sock)

def run(code, event):
    """Send IR signal to device"""
    if "device" not in code:
        print("Missing 'device' key in IR plugin configuration")
        return

    if "code" not in code:
        print("Missing 'code' key in IR plugin configuration")
        return

    device = code["device"]
    
    prefix = None
    
    #if hasattr(code, "prefix"):
    if "prefix" in code:
        prefix = code["prefix"]
    
    code = code["code"]
    
    sendcode = event["keycode"]
    
    if code != "DEFAULT":
        print("mapping to " + code)
        sendcode = code    
    elif sendcode == "KEY_UNKNOWN":
        sendcode = sendcode + "_" + str(event["scancode"])
        
    if prefix != None:
        sendcode = prefix + sendcode
    
    #try:
    if True:
        #client.send_once(device, ir_code)
        #print(f"IR: Sent '{ir_code}' to '{device}'")
        print(event)
        
        if event["keystate"] == "up":
            snd = NetworkSender()
            snd.Setup("192.168.0.125", 666, "Test")
            #sock = snd.Send("Remote." + event["keycode"], event)
            sock = snd.Send(sendcode, event)

            if sock:
                snd.MapUp(sock)
        
    #except:
    #    print(f"IR: Unable to send '{ir_code}' to '{device}'")
        #print(error)
