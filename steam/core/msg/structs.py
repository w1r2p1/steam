"""Classes to (de)serialize various struct messages"""
import struct
import six
from steam.enums import EResult, EUniverse
from steam.enums.emsg import EMsg

_emsg_map = {}

def get_struct(emsg):
    return _emsg_map.get(emsg, None)

class StructMessageMeta(type):
    """Automatically adds subclasses of :class:`StructMessage` to the ``EMsg`` map"""

    def __new__(metacls, name, bases, classdict):
        cls = type.__new__(metacls, name, bases, classdict)

        if name != 'StructMessage':
            try:
                _emsg_map[EMsg[name]] = cls
            except KeyError:
                pass

        return cls

@six.add_metaclass(StructMessageMeta)
class StructMessage:
    def __init__(self, data=None):
        if data: self.load(data)

    def serialize(self):
        raise NotImplementedError

    def load(self, data):
        raise NotImplementedError


class ChannelEncryptRequest(StructMessage):
    protocolVersion = 1
    universe = EUniverse.Invalid
    challenge = b''

    def serialize(self):
        return struct.pack("<II", self.protocolVersion, self.universe) + self.challenge

    def load(self, data):
        (self.protocolVersion,
         universe,
         ) = struct.unpack_from("<II", data)

        self.universe = EUniverse(universe)

        if len(data) > 8:
            self.challenge = data[8:]

    def __str__(self):
        return '\n'.join(["protocolVersion: %s" % self.protocolVersion,
                          "universe: %s" % repr(self.universe),
                          "challenge: %s" % repr(self.challenge),
                          ])

class ChannelEncryptResponse(StructMessage):
    protocolVersion = 1
    keySize = 128
    key = ''
    crc = 0

    def serialize(self):
        return struct.pack("<II128sII",
                           self.protocolVersion,
                           self.keySize,
                           self.key,
                           self.crc,
                           0
                           )

    def load(self, data):
        (self.protocolVersion,
         self.keySize,
         self.key,
         self.crc,
         _,
         ) = struct.unpack_from("<II128sII", data)

    def __str__(self):
        return '\n'.join(["protocolVersion: %s" % self.protocolVersion,
                          "keySize: %s" % self.keySize,
                          "key: %s" % repr(self.key),
                          "crc: %s" % self.crc,
                          ])

class ChannelEncryptResult(StructMessage):
    eresult = EResult.Invalid

    def serialize(self):
        return struct.pack("<I", self.eresult)

    def load(self, data):
        (result,) = struct.unpack_from("<I", data)
        self.eresult = EResult(result)

    def __str__(self):
        return "result: %s" % repr(self.eresult)

class ClientLogOnResponse(StructMessage):
    eresult = EResult.Invalid

    def serialize(self):
        return struct.pack("<I", self.eresult)

    def load(self, data):
        (result,) = struct.unpack_from("<I", data)
        self.eresult = EResult(result)

    def __str__(self):
        return "eresult: %s" % repr(self.eresult)

class ClientVACBanStatus(StructMessage):
    numBans = 0

    def serialize(self):
        return struct.pack("<L", self.steamIdChat)

    def load(self, data):
        self.steamIdChat, = struct.unpack_from("<L", data)

    def __str__(self):
        return '\n'.join(["numBans: %d" % self.numBans,
                          ])

class ClientChatMsg(StructMessage):
    steamIdChatter = 0
    steamIdChatRoom = 0
    ChatMsgType = 0
    text = ""

    def serialize(self):
        rbytes = struct.pack("<QQI",
                             self.steamIdChatter,
                             self.steamIdChatRoom,
                             self.ChatMsgType,
                            )
        # utf-8 encode only when unicode in py2 and str in py3
        rbytes += (self.text.encode('utf-8')
                   if (not isinstance(self.text, str) and bytes is str)
                      or isinstance(self.text, str)
                   else self.text
                  ) + b'\x00'

        return rbytes

    def load(self, data):
        (self.steamIdChatter,
         self.steamIdChatRoom,
         self.ChatMsgType,
         ) = struct.unpack_from("<QQI", data)

        self.text = data[struct.calcsize("<QQI"):-1].decode('utf-8')

    def __str__(self):
        return '\n'.join(["steamIdChatter: %d" % self.steamIdChatter,
                          "steamIdChatRoom: %d" % self.steamIdChatRoom,
                          "ChatMsgType: %d" % self.ChatMsgType,
                          "text: %s" % repr(self.text),
                          ])

class ClientJoinChat(StructMessage):
    steamIdChat = 0
    isVoiceSpeaker = False

    def serialize(self):
        return struct.pack("<Q?",
                           self.steamIdChat,
                           self.isVoiceSpeaker
        )

    def load(self, data):
        (self.steamIdChat,
         self.isVoiceSpeaker
        ) = struct.unpack_from("<Q?", data)

    def __str__(self):
        return '\n'.join(["steamIdChat: %d" % self.steamIdChat,
                          "isVoiceSpeaker: %r" % self.isVoiceSpeaker,
                          ])

class ClientChatMemberInfo(StructMessage):
    steamIdChat = 0
    type = 0
    steamIdUserActedOn = 0
    chatAction = 0
    steamIdUserActedBy = 0

    def serialize(self):
        return struct.pack("<QIQIQ",
                           self.steamIdChat,
                           self.type,
                           self.steamIdUserActedOn,
                           self.chatAction,
                           self.steamIdUserActedBy
        )

    def load(self, data):
        (self.steamIdChat,
         self.type,
         self.steamIdUserActedOn,
         self.chatAction,
         self.steamIdUserActedBy
        ) = struct.unpack_from("<QIQIQ", data)

    def __str__(self):
        return '\n'.join(["steamIdChat: %d" % self.steamIdChat,
                          "type: %r" % self.type,
                          "steamIdUserActedOn: %d" % self.steamIdUserActedOn,
                          "chatAction: %d" % self.chatAction,
                          "steamIdUserActedBy: %d" % self.steamIdUserActedBy
                          ])

class ClientMarketingMessageUpdate2(StructMessage):
    class MarketingMessage(object):
        id = 0
        url = ''
        flags = 0

        def __str__(self):
            return '\n'.join(["{",
                              "id: %s" % self.id,
                              "url: %s" % self.url,
                              "flags: %d" % self.flags,
                              "}",
                              ])

    time = 0

    @property
    def count(self):
        return len(self.messages)

    messages = list()

    def load(self, data):
        (self.time, count), self.messages = struct.unpack_from("<II", data), list()
        offset = 4 + 4

        while offset < len(data):
            length, = struct.unpack_from("<I", data, offset)
            url_length = length-4-8-4
            offset += 4

            m = self.MarketingMessage()
            m.id, m.url, _, m.flags = struct.unpack_from("<Q%dssI" % (url_length - 1), data, offset)
            self.messages.append(m)

            offset += 8 + url_length + 4

    def __str__(self):
        text = ["time: %s" % self.time,
                "count: %d" % self.count,
                ]

        for m in self.messages:  # emulate Protobuf text format
            text.append("messages " + str(m).replace("\n", "\n    ", 3))

        return '\n'.join(text)

