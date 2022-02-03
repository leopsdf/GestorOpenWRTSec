from pyof.v0x04.symmetric.hello import Hello
from pyof.utils import unpack

def prepare_Hello():
    """ Creates the Hello packet ready to be sent via socket """
    hello_packet = Hello()
    hello_binary = hello_packet.pack()
    
    return hello_binary

if __name__ == "__main__":
    
    print(prepare_Hello())