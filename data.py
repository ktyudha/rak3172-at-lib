class SaveData:
    def __init__(self):
        self.data_list = []
    
    def set_data(self,data):
        self.data_list.append(data)

    def to_csv(self,filename):
        if filename.split(".")[1] != "csv":
            raise Exception("Should be CSV file!")
        with open(filename,'w') as f:
            f.write("RSSI,SNR,Time,Message")
            f.write("\n")
            for r in self.data_list:
                f.write(r)
                f.write("\n")

class FormatData:
    @staticmethod
    def to_record(rssi,snr,time_received,message_sent):
        data = "{},{},{},{}".format(rssi,snr,time_received,message_sent)
        return data

    def get_value_return(data):
        try:
            data = data.split("=")
            data = data[1]
            return int(data)
        except:
            return -1

class ConvertData:
    @staticmethod
    def str2hex(input_string):
        hex_string = input_string.encode().hex().upper()
        return hex_string
