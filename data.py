import json

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

    @staticmethod
    def hex2str(hex_string):
        return bytes.fromhex(hex_string).decode("utf-8")
    
    @staticmethod
    def obj2str(input_object):
        try:
            # Convert object (dict/list) to JSON string
            json_string = json.dumps(input_object, separators=(",",":"))
            return json_string
        except Exception as e:
            print(f"Error converting object to string: {e}")
            return None

    @staticmethod
    def obj2hex(input_object):
        try:
            # Convert object to string
            json_string = ConvertData.obj2str(input_object).encode()
            # Convert string to hex
            hex_string = ConvertData.hex2str(json_string)
            return hex_string
        except Exception as e:
            print(f"Error converting object to hex: {e}")
            return None