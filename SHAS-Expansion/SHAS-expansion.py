import serial
import time, datetime
from threading import Thread
import smtplib, imaplib
import email
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from matplotlib import pyplot as plt
import numpy as np
import requests
import urllib.request
import schedule
import warnings
warnings.filterwarnings("ignore")


email = ""
epass = ""
email_to = "danielthe@cyberdude.com"

ts_channel_id = '1906188'
ts_key_write = 'W9QUZYDDIK8XIO1E'
ts_key_read = 'R2S1BVEG9A23IE8D'

plots_dir = 'C:\\Users\\<username>\\Desktop\\plots\\'


class SHAS:
    """Final project for subject: IOT"""
    
    def __init__(self):
        """Class constructor"""

        self.printHeader()
        
        self.BAUD_RATE  = 115200;
        self.COM_PORT   = "COM5";
        
        self.EMAIL_SRV1 = "imap.gmail.com"
        self.EMAIL_SRV2 = "smtp.gmail.com"
        self.EMAIL_PORT = 587
        self.EMAIL_ADDR = email
        self.EMAIL_PASS = epass
        self.EMAIL_TO   = email_to

        self.CHANNEL_ID = ts_channel_id
        self.API_KEY_WRITE = ts_key_write
        self.API_KEY_READ = ts_key_read

        self.BASE_URL = 'https://api.thingspeak.com'

        self.WRITE_URL = '{}/update?api_key={}'.format(self.BASE_URL, self.API_KEY_WRITE)
        self.READ_CHANNEL_URL = '{}/channels/{}/feeds.json?api_key={}'.format(self.BASE_URL, self.CHANNEL_ID, self.API_KEY_READ)
        self.READ_FIELD1_URL = '{}/channels/{}/fields/{}.json?api_key={}&start={}%2000:00:00'.format(self.BASE_URL, self.CHANNEL_ID, 1, self.API_KEY_READ, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.READ_FIELD2_URL = '{}/channels/{}/fields/{}.json?api_key={}&start={}%2000:00:00'.format(self.BASE_URL, self.CHANNEL_ID, 2, self.API_KEY_READ, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.READ_FIELD3_URL = '{}/channels/{}/fields/{}.json?api_key={}&start={}%2000:00:00'.format(self.BASE_URL, self.CHANNEL_ID, 3, self.API_KEY_READ, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.timestamp = datetime.datetime.now()
        
        self.serial = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1);

        self.email = imaplib.IMAP4_SSL(self.EMAIL_SRV1)
        self.email.login(self.EMAIL_ADDR, self.EMAIL_PASS)

        serialCheckThread = Thread(target=self.serialCheck,daemon=True)
        serialCheckThread.start()
        mailCheckThread = Thread(target=self.mailCheck,daemon=True)
        mailCheckThread.start()
        mailDailyThread = Thread(target=self.mailDailyReport,daemon=True)
        mailDailyThread.start()
        
        thingspeakCheckThread = Thread(target=self.thingspeakUpdater,daemon=True)
        thingspeakCheckThread.start()#mailDailyReport
        print("[+] Innit done, you can now use the SERIAL metodes to call commands on SHAS")

    def printHeader(self):
        print("""
            ███████╗██╗  ██╗ █████╗ ███████╗
            ██╔════╝██║  ██║██╔══██╗██╔════╝
            ███████╗███████║███████║███████╗
            ╚════██║██╔══██║██╔══██║╚════██║
            ███████║██║  ██║██║  ██║███████║
            ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
                by Daniel Petrovich

COMMAND SYNTAX:
    GET <PARAMETER>
            PARAMETERS:
            TEMP = temperature (in °C)
            LUX  = luminosity (in lumens)
            MOVE = movement detected (1/0, and restarts it)
            ACM  = AC Mode active (1/0)
            LAM  = Light Auto Mode active (1/0)
            HSM  = Home Secure Mode active (1/0)
            EM   = Emergency Mode active (1/0)
            

    SET <PARAMETER> <VALUE>

            PARAMETERS:
            LIGHTS = relay to which lights are connected (1/0)
            RED    = red LED (1/0)
            GREEN  = green LED (1/0)
            ACM    = Air Condition Mode (1/0)
            AC     = AC control (0 OFF, 1 cooling, 2 heating)
            LAM    = Light Auto Mode (1/0)
            HSM    = Home Secure Mode (1/0)
            EM     = Emergency Mode (1/0)

VALUES:
    0 = OFF
    1 = ON (OR ACM: cooling)
    2 = ACM ONLY: heating

SERIAL:
    X.serialGET("<PARAMETER>")
    X.serialSET("<PARAMETER> <VALUE>")
    X.mailReport() 

""")

    def serialSET(self, x):
        """Sending the value x to the MCU for futher operation"""
        self.serial.write(("SET " + x.upper()).encode());

    def serialGET(self, x):
        """Fetching the value for x"""
        self.serial.write(("GET " + x.upper()).encode())
        return self.serial.readline().decode().replace('\r\n','')

    def serialCheck(self):
        """Periodically checking for serial feedback"""
        receivedMessage = "";
        while True:
            if self.serial.in_waiting > 0:
                x = self.serial.readline().decode().replace('\r\n','');
                if x == "[!] Motion detected!":
                    self.thingspeakReportMove("1");
                    self.mailAlert();
                print(x)
            time.sleep(0.1)

    def mailCheck(self):
        """Periodically checking for e-mail feedback"""
        while True:
            self.email.select('inbox')
            retcode, response_get = self.email.search(None, '(SUBJECT "GET " UNSEEN)')
            retcode, response_set = self.email.search(None, '(SUBJECT "SET " UNSEEN)')
            retcode, response_report = self.email.search(None, '(SUBJECT "REPORT" UNSEEN)') #TODO


            if len(response_report[0]) > 0:# MANUAL REPORT
                self.mailReport();
                    
                emailIds = response_report[0].split()
                for id in emailIds:
                    self.email.store(id, '+FLAGS', '\\Seen')

            if len(response_get[0]) > 0:# GET
                for num in response_get[0].split():
                    ok, fetched = self.email.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
                    msg = email.message_from_string(fetched[0][1].decode())
                    resp = self.serialGET(msg['subject'].upper().replace("GET ",""))
                    print("[*] EMAIL COMMAND: ", msg['subject'].upper().replace("GET ",""), "RESPONSE: ",resp)
                    self.mailSendResponse(msg['subject'].upper().split(" ")[1], resp)
                    
                emailIds = response_get[0].split()
                for id in emailIds:
                    self.email.store(id, '+FLAGS', '\\Seen')
                    
            if len(response_set[0]) > 0:# SET
                for num in response_set[0].split():
                    ok, fetched = self.email.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
                    msg = email.message_from_string(fetched[0][1].decode())
                    print("[*] EMAIL COMMAND: "+msg['subject'].upper())
                    self.serialSET(msg['subject'].upper().replace("SET ",""))
                    
                emailIds = response_set[0].split()
                for id in emailIds:
                    self.email.store(id, '+FLAGS', '\\Seen')

            time.sleep(1)

    def mailSendResponse(self, field, value):
        """Sends response for requested field"""
        message = MIMEMultipart()
        message['Subject'] = "Response for '"+field+"'"

        message.preamble = '=========================================='

        htmlText = """\
            <html>
                <head></head>
                <body>
                    <h1>Response for '"""+field+"""'</h1>
                    <p>
                        """+field+""" = <strong>"""+value+"""</strong>
                    </p>
                </body>
            </html>
        """

        mimeText = MIMEText(htmlText, 'html')
        message.attach(mimeText)

        server = smtplib.SMTP(self.EMAIL_SRV2, self.EMAIL_PORT)
        server.starttls()
        r = server.login(self.EMAIL_ADDR, self.EMAIL_PASS)
        r = server.sendmail(self.EMAIL_ADDR, self.EMAIL_TO, message.as_string())
        server.quit()
        print('[!] MailSendResponse done!')

    def mailReport(self):
        """Generating and sending the main report"""
        temp = requests.get(self.READ_FIELD1_URL)
        illum = requests.get(self.READ_FIELD2_URL)
        move = requests.get(self.READ_FIELD3_URL)

        dataJsonT = temp.json()
        dataJsonI = illum.json()
        dataJsonM = move.json()

        feeds = dataJsonT["feeds"]
        temperature = []
        for x in feeds:
            if x["field1"] != None:
                x =  float(x["field1"])
                temperature.append(x)

        feeds_illum = dataJsonI["feeds"]
        illumination = []
        for x in feeds_illum:
            if x["field2"] != None:
                x =  float(x["field2"])
                illumination.append(x)

        feeds_moving = dataJsonM["feeds"]
        moving = []
        m = 0
        for x in feeds_moving:
            #x =  float(x["field3"])
            if x["field3"] != None:
                m+=1
                x =  float(x["field3"])
                moving.append(x)

        message = MIMEMultipart()
        message['Subject'] = 'Report for {}'.format(datetime.date.today())

        plt.ioff()
        x=np.linspace(0,23,len(temperature))
        fig=plt.figure()
        plt.title("Daily temperature")
        plt.xlabel("Hours")
        plt.ylabel("Temperatrure (°C)")
        plt.plot(x, temperature)
        fileName = 'report-temperatrure-{}.png'.format(datetime.date.today())
        plt.savefig(plots_dir + fileName)

        tempGraph = open(plots_dir + fileName, 'rb')
        msgTempGraph = MIMEImage(tempGraph.read())
        tempGraph.close()
        message.attach(msgTempGraph)

        plt.ioff()
        x=np.linspace(0,23,len(illumination))
        fig=plt.figure()
        plt.title("Daily illumination")
        plt.xlabel("Hours")
        plt.ylabel("Illumination (%)")
        plt.plot(x, illumination)
        fileName = 'report-illumination-{}.png'.format(datetime.date.today())
        plt.savefig(plots_dir + fileName)

        illumGraph = open(plots_dir + fileName, 'rb')
        msgIllumGraph = MIMEImage(illumGraph.read())
        illumGraph.close()
        message.attach(msgIllumGraph)

        plt.ioff()
        x=np.linspace(0,23,len(moving))
        fig=plt.figure()
        plt.title("Daily move")
        plt.xlabel("Hours")
        plt.ylabel("Move")
        plt.plot(x, moving)
        fileName = 'report-move-{}.png'.format(datetime.date.today())
        plt.savefig(plots_dir + fileName)

        moveGraph = open(plots_dir + fileName, 'rb')
        msgmoveGraph = MIMEImage(moveGraph.read())
        moveGraph.close()
        message.attach(msgmoveGraph)

        t1 = datetime.datetime.now()
        t2 = self.timestamp
        diff = (t1-t2)
        

        message.preamble = '=========================================='

        htmlText = """\
            <html>
                <head></head>
                <body>
                    <h1>Daily report on {}</h1>
                    <p>
                        The minimum daily temperature was: <strong>{}</strong> C and the maximum was <strong>{}</strong> C and the average daily was <strong>{:.2f}</strong> C.
                    </p>
                    <p>
                        The minimum daily illumination was: <strong>{}</strong>  and the maximum was <strong>{}</strong> and the average daily was <strong>{:.2f}</strong> .
                    </p>
                    <p>
                        Moves detected today: <strong>{}</strong>, uptime duration: <strong>{}</strong>.
                    </p>
                </body>
            </html>
        
        """.format(datetime.date.today(),int(np.min(temperature)), int(np.max(temperature)), int(np.average(temperature)), int(np.min(illumination)), int(np.max(illumination)), int(np.average(illumination)), m, self.strfdelta(diff, "{days} days {hours}:{minutes}:{seconds}"))

        mimeText = MIMEText(htmlText, 'html')
        message.attach(mimeText)

        server = smtplib.SMTP(self.EMAIL_SRV2, self.EMAIL_PORT)
        server.starttls()
        r = server.login(self.EMAIL_ADDR, self.EMAIL_PASS)
        r = server.sendmail(self.EMAIL_ADDR, self.EMAIL_TO, message.as_string())
        server.quit()
        print('[!] MailSendReport done!')


    def strfdelta(self,tdelta, fmt):
        """Timedelta converter"""
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)

    def mailAlert(self):
        """Mail that is sent when the move is detected"""
        message = MIMEMultipart()
        message['Subject'] = "Motion Alert"

        message.preamble = '=========================================='

        htmlText = """\
            <html>
                <head></head>
                <body>
                    <h1>PIR Motion Alert</h1>
                </body>
            </html>
        """

        mimeText = MIMEText(htmlText, 'html')
        message.attach(mimeText)

        server = smtplib.SMTP(self.EMAIL_SRV2, self.EMAIL_PORT)
        server.starttls()
        r = server.login(self.EMAIL_ADDR, self.EMAIL_PASS)
        r = server.sendmail(self.EMAIL_ADDR, self.EMAIL_TO, message.as_string())
        server.quit()
        print('[!] MailAlert done!')

    def mailDailyReport(self):
        """Periodically sends daily report"""
        while True:
            if datetime.datetime.now().strftime("%H:%M") == "23:59":
                self.mailReport();
            time.sleep(1000)


    def thingspeakUpdater(self):
        """Periodically updates the thingspeak DB"""
        while True:
            x = self.serialGET("TEMP")
            y = self.serialGET("LUX")
            x = "1" if x=="" else x
            y = "1" if y=="" else y
            self.thingspeakReportLuxTemp(x,y)
            time.sleep(1000*60*10) # wait ten minutes


    def thingspeakReportLuxTemp(self,x,y):
        """Updating LUX and TEMP on thingspeak DB"""
        resp = urllib.request.urlopen("{}&field1={}&field2={}".format(self.WRITE_URL, x,y))

    def thingspeakReportMove(self,x):
        """Updating MOVE on thingspeak DB"""
        resp = urllib.request.urlopen("{}&field3={}".format(self.WRITE_URL, x))



if __name__ == "__main__":
    X = SHAS()

# delete me
test = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
test += "Mauris euismod arcu vitae molestie aliquet."
test += "Donec venenatis nisi ullamcorper, vulputate felis nec, mollis nulla."
test += "Maecenas sed nibh accumsan, vulputate lectus id, feugiat velit."
test += "Sed vel mi non ante elementum pellentesque id sit amet orci."
test += "Pellentesque eleifend risus a justo condimentum aliquam."
test += "Fusce et neque convallis, vestibulum ligula sed, ultrices risus."
test += "In ut enim lacinia, commodo nunc at, vehicula urna."
test += "Curabitur porttitor dolor convallis, luctus nisl eu, auctor lorem."
test += "Integer sagittis nulla vitae tortor maximus, vel tristique quam venenatis."
test += "Phasellus et diam mattis, semper justo sed, semper libero."
test += "Nullam scelerisque libero non ultrices egestas."
test += "Cras tempor purus eget auctor aliquet."
test += "Praesent sodales enim eu pellentesque luctus."
test += "Cras iaculis purus a odio dignissim condimentum."
test += "Sed eu est at est dapibus mattis."
test += "Donec egestas est in finibus mollis."
test += "Aenean id arcu porttitor, mollis metus at, aliquet elit."
test += "Donec ullamcorper justo in dictum rutrum."
test += "Pellentesque ut justo at tortor iaculis dignissim."
test += "Donec eget sem ut turpis sodales ultrices."
test += "Nulla vel erat a lectus consequat dictum dapibus id mauris."
test += "Phasellus id lorem nec dolor molestie efficitur nec in tortor."
test += "Sed imperdiet nulla ac magna imperdiet accumsan."
test += "Nullam sed lacus suscipit, commodo dolor ac, porttitor erat."
test += "Integer quis mi tincidunt, bibendum orci at, malesuada dolor."
test += "Aliquam quis tellus eu orci maximus lobortis ac in diam."
test += "Cras sit amet est feugiat, vulputate nisl id, sagittis dolor."
test += "Sed commodo nibh ac mi tincidunt venenatis."
test += "Duis fringilla augue porta nulla eleifend consectetur."
test += "Sed nec felis nec neque condimentum sodales."
test += "Mauris quis quam iaculis, fermentum felis sit amet, fermentum mauris."
test += "Sed sit amet mauris id enim scelerisque tristique."
test += "Mauris sed lectus et arcu faucibus iaculis et a ipsum."
test += "Sed posuere libero id vestibulum dignissim."
test += "Duis rhoncus velit id dignissim congue."
test += "Pellentesque lacinia purus sit amet mi facilisis, sit amet rutrum tortor euismod."
test += "Aenean egestas mauris in mi sollicitudin, vel volutpat ipsum dapibus."
test += "Sed cursus tortor eu iaculis sagittis."
test += "Phasellus vel massa at nunc posuere volutpat sed eget urna."
test += "Nullam tristique ante ac cursus tempus."
test += "Suspendisse vitae lacus porta, cursus eros ac, porttitor diam."
test += "Nulla tempus mi nec pellentesque tincidunt."
test += "Mauris euismod arcu vitae molestie aliquet."
test += "Donec venenatis nisi ullamcorper, vulputate felis nec, mollis nulla."
test += "Maecenas sed nibh accumsan, vulputate lectus id, feugiat velit."
test += "Sed vel mi non ante elementum pellentesque id sit amet orci."
test += "Pellentesque eleifend risus a justo condimentum aliquam."
test += "Fusce et neque convallis, vestibulum ligula sed, ultrices risus."
test += "In ut enim lacinia, commodo nunc at, vehicula urna."
test += "Curabitur porttitor dolor convallis, luctus nisl eu, auctor lorem."
test += "Integer sagittis nulla vitae tortor maximus, vel tristique quam venenatis."
test += "Phasellus et diam mattis, semper justo sed, semper libero."
test += "Nullam scelerisque libero non ultrices egestas."
test += "Cras tempor purus eget auctor aliquet."
test += "Praesent sodales enim eu pellentesque luctus."
test += "Cras iaculis purus a odio dignissim condimentum."
test += "Sed eu est at est dapibus mattis."
test += "Donec egestas est in finibus mollis."
test += "Aenean id arcu porttitor, mollis metus at, aliquet elit."
test += "Donec ullamcorper justo in dictum rutrum."
test += "Pellentesque ut justo at tortor iaculis dignissim."
test += "Donec eget sem ut turpis sodales ultrices."
test += "Nulla vel erat a lectus consequat dictum dapibus id mauris."
test += "Phasellus id lorem nec dolor molestie efficitur nec in tortor."
test += "Sed imperdiet nulla ac magna imperdiet accumsan."
test += "Nullam sed lacus suscipit, commodo dolor ac, porttitor erat."
test += "Integer quis mi tincidunt, bibendum orci at, malesuada dolor."
test += "Aliquam quis tellus eu orci maximus lobortis ac in diam."
test += "Cras sit amet est feugiat, vulputate nisl id, sagittis dolor."
test += "Sed commodo nibh ac mi tincidunt venenatis."
test += "Duis fringilla augue porta nulla eleifend consectetur."
test += "Sed nec felis nec neque condimentum sodales."
test += "Mauris quis quam iaculis, fermentum felis sit amet, fermentum mauris."
test += "Sed sit amet mauris id enim scelerisque tristique."
test += "Mauris sed lectus et arcu faucibus iaculis et a ipsum."
test += "Sed posuere libero id vestibulum dignissim."
test += "Duis rhoncus velit id dignissim congue."
test += "Pellentesque lacinia purus sit amet mi facilisis, sit amet rutrum tortor euismod."
test += "Aenean egestas mauris in mi sollicitudin, vel volutpat ipsum dapibus."
test += "Sed cursus tortor eu iaculis sagittis."
test += "Phasellus vel massa at nunc posuere volutpat sed eget urna."
test += "Nullam tristique ante ac cursus tempus."
test += "Suspendisse vitae lacus porta, cursus eros ac, porttitor diam."
test += "Nulla tempus mi nec pellentesque tincidunt."
test += "Mauris euismod arcu vitae molestie aliquet."
test += "Donec venenatis nisi ullamcorper, vulputate felis nec, mollis nulla."
test += "Maecenas sed nibh accumsan, vulputate lectus id, feugiat velit."
test += "Sed vel mi non ante elementum pellentesque id sit amet orci."
test += "Pellentesque eleifend risus a justo condimentum aliquam."
test += "Fusce et neque convallis, vestibulum ligula sed, ultrices risus."
test += "In ut enim lacinia, commodo nunc at, vehicula urna."
test += "Curabitur porttitor dolor convallis, luctus nisl eu, auctor lorem."
test += "Integer sagittis nulla vitae tortor maximus, vel tristique quam venenatis."
test += "Phasellus et diam mattis, semper justo sed, semper libero."
test += "Nullam scelerisque libero non ultrices egestas."
test += "Cras tempor purus eget auctor aliquet."
test += "Praesent sodales enim eu pellentesque luctus."
test += "Cras iaculis purus a odio dignissim condimentum."
test += "Sed eu est at est dapibus mattis."
test += "Donec egestas est in finibus mollis."
test += "Aenean id arcu porttitor, mollis metus at, aliquet elit."
test += "Donec ullamcorper justo in dictum rutrum."
test += "Pellentesque ut justo at tortor iaculis dignissim."
test += "Donec eget sem ut turpis sodales ultrices."
test += "Nulla vel erat a lectus consequat dictum dapibus id mauris."
test += "Phasellus id lorem nec dolor molestie efficitur nec in tortor."
test += "Sed imperdiet nulla ac magna imperdiet accumsan."
test += "Nullam sed lacus suscipit, commodo dolor ac, porttitor erat."
test += "Integer quis mi tincidunt, bibendum orci at, malesuada dolor."
test += "Aliquam quis tellus eu orci maximus lobortis ac in diam."
test += "Cras sit amet est feugiat, vulputate nisl id, sagittis dolor."
test += "Sed commodo nibh ac mi tincidunt venenatis."
test += "Duis fringilla augue porta nulla eleifend consectetur."
test += "Sed nec felis nec neque condimentum sodales."
test += "Mauris quis quam iaculis, fermentum felis sit amet, fermentum mauris."
test += "Sed sit amet mauris id enim scelerisque tristique."
test += "Mauris sed lectus et arcu faucibus iaculis et a ipsum."
test += "Sed posuere libero id vestibulum dignissim."
test += "Duis rhoncus velit id dignissim congue."
test += "Pellentesque lacinia purus sit amet mi facilisis, sit amet rutrum tortor euismod."
test += "Aenean egestas mauris in mi sollicitudin, vel volutpat ipsum dapibus."
test += "Sed cursus tortor eu iaculis sagittis."
test += "Phasellus vel massa at nunc posuere volutpat sed eget urna."
test += "Nullam tristique ante ac cursus tempus."
test += "Suspendisse vitae lacus porta, cursus eros ac, porttitor diam."
test += "Nulla tempus mi nec pellentesque tincidunt."
