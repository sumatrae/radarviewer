import struct

HEADER_SIZE = 34
TLV_DESCRIPT_SIZE = 8

class Decoder():
    def search_magicword(self):
        pass

    def get_header(self, payload):
        self.magic_word, self.version, self.total_packet_lenght, self.platform, self.frame_number, self.time_cpucycle, self.num_detected_objection, \
        self.num_tlvs, self.sumframe_numbers = struct.unpack(">HIIIIIIII", payload[:HEADER_SIZE])

    def get_tlv(self,payload, offset):
        self.tlv_type, self.tlv_length = struct.unpack(">II", payload[offset:offset+TLV_DESCRIPT_SIZE])
