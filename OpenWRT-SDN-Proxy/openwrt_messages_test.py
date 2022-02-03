from pyof.utils import unpack
from pyof.v0x04.OpenWRT.messages import QoS_Message

if __name__ == "__main__":
    qos_message = QoS_Message()
    qos_message.set_metrics(20,30)
    binary_message = qos_message.pack()
    print(binary_message)
    QoS_recebido = QoS_Message()
    QoS_recebido = unpack(binary_message)
    print(QoS_recebido.header)