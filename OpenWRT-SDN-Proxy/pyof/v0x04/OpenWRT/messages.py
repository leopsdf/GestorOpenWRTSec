from pyof.foundation.base import GenericStruct, GenericMessage
from pyof.foundation.basic_types import IPAddress, UBInt128, UBInt32
from pyof.v0x04.common.header import Header, Type

class QoS_Struct(GenericStruct):
    """ Struct that defines the OpenWRT Quality of Service setting, namely Download and Upload (bits/s)"""
    upload = UBInt32(0)
    download = UBInt32(0)
    
class QoS_Message(GenericMessage):
    """ OpenFlow OpenWRT QoS managament message - method set_metrics(download, upload) bits/s"""
    
    header = Header(message_type=65)
    qos = QoS_Struct()
    
    def __init__(self):
        super().__init__()
    
    def set_metrics(self, download, upload):
        
        self.qos.download = download
        self.qos.upload = upload
        
        
        
# if __name__ == "__main__":
    
#     qos_message = QoS_Message()
#     qos_message.set_metrics(20, 30)
#     binary_qos = qos_message.pack()
    
#     print(qos_message.qos_struct.download)    
    
    
#     # binary_packet = QoS_packet.pack()

#     # print(binary_packet)

#     QoS_recebido = QoS_Message()
#     QoS_recebido = binary_qos.unpack()
#     print(QoS_recebido.qos_struct.download)
    