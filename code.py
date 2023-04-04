import os
import ipaddress
import wifi
import socketpool
import time
import board
from analogio import AnalogIn

import microcontroller
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.mime_type import MIMEType

# 192.168.1.156

#  connect to SSID
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
                   os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

# for debugging:
#  prints MAC address to REPL
# print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

#  prints IP address to REPL
# print("My IP address is", wifi.radio.ipv4_address)

#  pings Google
# ipv4 = ipaddress.ip_address("8.8.4.4")
# print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))


#  get analog data from pin
# ADC2 / GP28 / pin34
analog_in = AnalogIn(board.GP28_A2)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def webpage(brightness):
    if (brightness < .035):
        conclusion = "dark"
    elif (brightness >= .035 and brightness <= .3):
        conclusion = "dim"
    else:
        conclusion = "bright"
    html = f"""
            <!DOCTYPE html>
            <html>
            <p>Sensor reports a normalized light value of {brightness}.</p>
            <p>This is {conclusion}.</p>
            </body>
            </html>
            """
    return str(html)


print("starting server..")
# startup the server
try:
    server.start(str(wifi.radio.ipv4_address))
    print("Listening on http://%s:80" % wifi.radio.ipv4_address)
#  if the server fails to begin, restart the pico w
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()

#  route default static IP
@server.route("/")
def base(request: HTTPRequest):  # pylint: disable=unused-argument
    #  serve the HTML f string
    #  with content type text/html
    brightness = get_voltage(analog_in)
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send(f"{webpage(brightness)}")

while True:
    try:
        #  poll the server for incoming/outgoing requests
        server.poll()
    except Exception as e:
        print(e)
        continue
